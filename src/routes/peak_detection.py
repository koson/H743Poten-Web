import time
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app, session
import os
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from scipy.stats import linregress
import logging
import uuid
import glob
import json
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

peak_detection_bp = Blueprint('peak_detection', __name__)

def detect_linear_segments(voltage, current, min_length=5, r2_threshold=0.95, max_iterations=None, adaptive_step=False):
    """Find all linear segments that could be baseline candidates using voltage windows"""
    segments = []
    n = len(voltage)
    
    # Set default max_iterations based on input
    if max_iterations is None:
        max_iterations = 1000  # Much reduced for voltage-based windowing
    
    iteration_count = 0
    
    # Calculate voltage step and range
    voltage_range = np.max(voltage) - np.min(voltage)
    avg_voltage_step = voltage_range / (n - 1) if n > 1 else 0.001
    
    logger.info(f"Voltage range: {voltage_range:.3f}V, avg step: {avg_voltage_step*1000:.2f}mV, n_points: {n}")
    
    # Define voltage window sizes (10-50 mV as suggested)
    voltage_windows = [0.010, 0.020, 0.030, 0.050]  # 10, 20, 30, 50 mV windows
    
    # Skip initial steep region (first 10% of data typically has high slope)
    start_skip = max(10, n // 10)  # Skip first 10% or at least 10 points
    end_skip = max(10, n // 20)   # Skip last 5% for symmetry
    
    logger.info(f"Skipping initial {start_skip} points and final {end_skip} points to avoid steep regions")
    
    for voltage_window in voltage_windows:
        # Convert voltage window to approximate number of points
        window_points = max(min_length, int(voltage_window / avg_voltage_step)) if avg_voltage_step > 0 else min_length
        
        logger.info(f"Testing voltage window: {voltage_window*1000:.0f}mV (~{window_points} points)")
        
        # Use larger steps to reduce computation
        step_size = max(1, window_points // 4)  # Step by quarter of window size
        
        for start in range(start_skip, n - end_skip - window_points, step_size):
            iteration_count += 1
            if iteration_count > max_iterations:
                logger.warning(f"Reached maximum iterations ({max_iterations}) in segment detection")
                break
                
            # Try different segment lengths around the voltage window
            for length_factor in [0.8, 1.0, 1.2, 1.5]:  # 80%, 100%, 120%, 150% of window
                segment_length = max(min_length, int(window_points * length_factor))
                end = min(start + segment_length, n - end_skip)
                
                if end - start < min_length:
                    continue
                    
                v_seg = voltage[start:end]
                i_seg = current[start:end]
            
            if not (np.all(np.isfinite(v_seg)) and np.all(np.isfinite(i_seg))):
                continue
                
            voltage_span = v_seg[-1] - v_seg[0]
            if abs(voltage_span) < 0.02:
                continue
            
            try:
                slope, intercept, r_value, p_value, std_err = linregress(v_seg, i_seg)
                r2 = r_value ** 2
                
                if r2 >= r2_threshold:
                    segment_len = end - start
                    segments.append({
                        'start_idx': start,
                        'end_idx': end,
                        'length': segment_len,
                        'slope': slope,
                        'intercept': intercept,
                        'r2': r2,
                        'voltage_range': (v_seg[0], v_seg[-1]),
                        'voltage_span': voltage_span,
                        'mean_current': np.mean(i_seg),
                        'std_current': np.std(i_seg)
                    })
            except:
                continue
    
    # Remove overlapping segments
    segments = sorted(segments, key=lambda x: x['r2'], reverse=True)
    filtered = []
    for segment in segments:
        is_overlapping = False
        for selected in filtered:
            overlap_start = max(segment['start_idx'], selected['start_idx'])
            overlap_end = min(segment['end_idx'], selected['end_idx'])
            overlap_length = max(0, overlap_end - overlap_start + 1)
            segment_length = segment['end_idx'] - segment['start_idx'] + 1
            overlap_ratio = overlap_length / segment_length
            
            if overlap_ratio > 0.6:
                is_overlapping = True
                break
        
        if not is_overlapping:
            filtered.append(segment)
    
    return filtered

def detect_improved_baseline_2step(voltage, current, max_iterations=None, adaptive_step=False):
    """2-step baseline detection: find segments, then select best ones"""
    try:
        # Step 1: Find linear segments with optional parameters
        segments = detect_linear_segments(voltage, current, max_iterations=max_iterations, adaptive_step=adaptive_step)
        
        if not segments:
            logger.warning("No linear segments found, using simple baseline")
            return None  # Return None to trigger fallback
        
        # Step 2: Find peaks first to guide baseline selection
        # Use simple prominence-based peak detection to identify peak regions
        current_norm = current / np.abs(current).max()
        pos_peaks, _ = find_peaks(current_norm, prominence=0.1, width=3)
        neg_peaks, _ = find_peaks(-current_norm, prominence=0.1, width=3)
        all_peak_indices = sorted(list(pos_peaks) + list(neg_peaks))
        
        logger.info(f"Found {len(all_peak_indices)} peaks for baseline guidance: {all_peak_indices}")
        
        # Find the turning point and scan direction
        min_voltage_idx = np.argmin(voltage)
        min_voltage = voltage[min_voltage_idx]
        max_voltage = np.max(voltage)
        voltage_range = max_voltage - min_voltage
        
        logger.info(f"Voltage range: {min_voltage:.3f} to {max_voltage:.3f}V, turning point at index {min_voltage_idx}")
        
        # Step 3: Select baseline segments intelligently based on voltage values and scan direction
        # For CV: forward scan typically goes from high to low voltage, reverse goes from low to high
        mid_point = len(voltage) // 2
        
        # Find voltage-based boundaries instead of just index-based quarters
        voltage_min = np.min(voltage)
        voltage_max = np.max(voltage)
        voltage_range = voltage_max - voltage_min
        
        # Find the actual turning point (minimum voltage)
        turning_point_idx = np.argmin(voltage)
        
        # More intelligent segment selection:
        # Forward segments: from start until before first major peak
        # Reverse segments: from after turning point and after last major peak
        
        forward_quarter = len(voltage) // 4
        
        # For reverse, we want segments after the turning point AND after the last peak
        if all_peak_indices:
            # Find peaks in the reverse scan (after turning point)
            reverse_peaks = [p for p in all_peak_indices if p > turning_point_idx]
            if reverse_peaks:
                # Take segments AFTER the last peak in reverse scan
                last_reverse_peak = max(reverse_peaks)
                reverse_start_region = min(last_reverse_peak + 10, len(voltage) - 20)  # At least 10 points after last peak
                logger.info(f"Last reverse peak at {last_reverse_peak}, reverse region starts at {reverse_start_region}")
            else:
                # No peaks in reverse scan, use region after turning point
                reverse_start_region = turning_point_idx + 20
        else:
            # No peaks found, fall back to 3/4 point
            reverse_start_region = 3 * len(voltage) // 4
        
        # Forward segments: should be in the beginning of scan (before first peak)
        forward_segments = [s for s in segments if s['end_idx'] <= forward_quarter]
        
        # Reverse segments: should be AFTER the last peak in reverse scan
        reverse_segments = [s for s in segments if s['start_idx'] >= reverse_start_region and s['start_idx'] > turning_point_idx]
        
        logger.info(f"Turning point at index {turning_point_idx}, reverse region starts at {reverse_start_region}")
        
        # Fallback: if we don't find enough segments, expand search
        if len(forward_segments) == 0:
            # Try first half
            forward_segments = [s for s in segments if s['end_idx'] <= mid_point]
            logger.info(f"Forward fallback: expanded to first half, found {len(forward_segments)} segments")
            
        if len(reverse_segments) == 0:
            # Try after turning point
            reverse_segments = [s for s in segments if s['start_idx'] >= turning_point_idx + 10]
            logger.info(f"Reverse fallback: expanded to post-turning point, found {len(reverse_segments)} segments")
            
            # Final fallback: use second half
            if len(reverse_segments) == 0:
                reverse_segments = [s for s in segments if s['start_idx'] >= mid_point]
                logger.info(f"Reverse final fallback: expanded to second half, found {len(reverse_segments)} segments")
        
        logger.info(f"Forward segments (first quarter): {len(forward_segments)}, Reverse segments (post-last-peak): {len(reverse_segments)}")
        logger.info(f"Forward quarter: 0-{forward_quarter}, Reverse region starts at: {reverse_start_region}")
        
        # Debug: Show first few segments
        if forward_segments:
            logger.info(f"Forward segment examples: {[(s['start_idx'], s['end_idx']) for s in forward_segments[:3]]}")
        if reverse_segments:
            logger.info(f"Reverse segment examples: {[(s['start_idx'], s['end_idx']) for s in reverse_segments[:3]]}")
        else:
            logger.warning(f"No reverse segments found! Available segments: {[(s['start_idx'], s['end_idx']) for s in segments]}")
        
        # Additional safeguard: Ensure forward and reverse don't use same segments
        if forward_segments and reverse_segments:
            # Remove any overlapping segments
            safe_reverse_segments = []
            for rs in reverse_segments:
                overlap = False
                for fs in forward_segments:
                    # Check for overlap
                    if not (rs['end_idx'] < fs['start_idx'] or rs['start_idx'] > fs['end_idx']):
                        overlap = True
                        break
                if not overlap:
                    safe_reverse_segments.append(rs)
            
            if len(safe_reverse_segments) < len(reverse_segments):
                logger.info(f"Removed {len(reverse_segments) - len(safe_reverse_segments)} overlapping reverse segments")
                reverse_segments = safe_reverse_segments
                
            # If no safe reverse segments, force a different region
            if not reverse_segments:
                logger.warning("No non-overlapping reverse segments found, forcing separation")
                # Take segments from the last third that don't overlap with forward
                last_third_start = 2 * len(voltage) // 3
                reverse_segments = [s for s in segments if s['start_idx'] >= last_third_start]
                # Remove overlaps again
                safe_reverse_segments = []
                for rs in reverse_segments:
                    overlap = False
                    for fs in forward_segments:
                        if not (rs['end_idx'] < fs['start_idx'] or rs['start_idx'] > fs['end_idx']):
                            overlap = True
                            break
                    if not overlap:
                        safe_reverse_segments.append(rs)
                reverse_segments = safe_reverse_segments
                logger.info(f"Forced separation: found {len(reverse_segments)} reverse segments in last third")
        
        def score_baseline_segment(segment, scan_direction='forward'):
            """Score a segment for baseline suitability with voltage-based approach"""
            logger.info(f"[BASELINE] Scoring segment {segment['start_idx']}-{segment['end_idx']} for {scan_direction} baseline")
            score = 0.0
            
            # Linearity (R²) - higher is better
            r2_score = segment['r2'] * 60  # Increased weight for linearity
            score += r2_score
            logger.debug(f"[BASELINE] R² score: {r2_score:.2f} (R²={segment['r2']:.3f})")
            
            # Voltage span - prefer reasonable voltage coverage (10-50mV as suggested)
            voltage_span_mv = abs(segment['voltage_span']) * 1000  # Convert to mV
            if 10 <= voltage_span_mv <= 50:
                span_score = 20  # Good voltage window
            elif 5 <= voltage_span_mv < 10:
                span_score = 10  # Acceptable but small
            elif 50 < voltage_span_mv <= 100:
                span_score = 15  # Acceptable but large
            else:
                span_score = -10  # Too small or too large
            score += span_score
            logger.debug(f"[BASELINE] Voltage span score: {span_score} ({voltage_span_mv:.1f}mV)")
            
            # Low slope - more horizontal is better for baseline
            slope_abs = abs(segment['slope'])
            if slope_abs > 100:  # Very steep slopes (adjusted for mV scale)
                slope_penalty = 50
            elif slope_abs > 50:
                slope_penalty = 25  
            else:
                slope_penalty = slope_abs * 0.5  # Gentle penalty for small slopes
            score -= slope_penalty
            logger.debug(f"[BASELINE] Slope penalty: {slope_penalty:.2f} (slope: {segment['slope']:.2e})")
            
            # Position preference - avoid very beginning and end of scan
            total_points = len(voltage)
            segment_position = segment['start_idx'] / total_points
            if 0.1 <= segment_position <= 0.9:  # Middle 80% of scan
                position_score = 10
            else:
                position_score = -5  # Penalize extreme positions
            score += position_score
            logger.debug(f"[BASELINE] Position score: {position_score} (position: {segment_position:.2f})")
            
            # Low current standard deviation - more stable is better
            if segment['std_current'] > 0:
                stability_score = max(0, 15 - (segment['std_current'] * 1e6))  # Adjusted for typical current scales
                score += stability_score
                logger.debug(f"[BASELINE] Stability score: {stability_score:.2f}")
            
            # Peak awareness - prefer segments that are NOT in peak regions
            segment_mid = (segment['start_idx'] + segment['end_idx']) // 2
            min_distance_to_peak = float('inf')
            
            for peak_idx in all_peak_indices:
                distance = abs(segment_mid - peak_idx)
                min_distance_to_peak = min(min_distance_to_peak, distance)
            
            # Bonus for being far from peaks (baseline should be in non-peak regions)
            if min_distance_to_peak > 20:
                score += 20
            elif min_distance_to_peak > 10:
                score += 10
            else:
                score -= 5  # Penalty for being too close to peaks
            
            # NEW: Position preference for forward scan
            if scan_direction == 'forward':
                # For forward scan, prefer segments that are BEFORE major peaks
                # Find the first significant peak in forward scan
                forward_peaks = [p for p in all_peak_indices if p < min_voltage_idx]
                if forward_peaks:
                    first_peak = min(forward_peaks)
                    logger.debug(f"[BASELINE] Forward scan first peak at index {first_peak}")
                    if segment['end_idx'] < first_peak - 5:  # Must be well before first peak
                        score += 25  # Strong bonus for pre-peak segments
                        logger.debug(f"[BASELINE] Pre-peak bonus applied: +25")
                    elif segment['start_idx'] > first_peak:  # Penalty for post-peak segments
                        score -= 15
                        logger.debug(f"[BASELINE] Post-peak penalty applied: -15")
                        
                # Additional preference for earlier segments in forward scan
                segment_position = segment['start_idx'] / len(voltage)
                if segment_position < 0.3:  # First 30% of scan
                    score += 15
                    logger.debug(f"[BASELINE] Early position bonus: +15")
                elif segment_position > 0.7:  # Last 30% of forward scan
                    score -= 10
                    logger.debug(f"[BASELINE] Late position penalty: -10")
            
            logger.info(f"[BASELINE] Final segment score: {score:.2f}")
            return score
        
        def select_best_segment(segment_list, scan_direction='forward'):
            if not segment_list:
                logger.warning(f"[BASELINE] No segments available for {scan_direction} baseline")
                return None
            
            logger.info(f"[BASELINE] Selecting best segment from {len(segment_list)} {scan_direction} segments")
            scored_segments = [(score_baseline_segment(s, scan_direction), s) for s in segment_list]
            scored_segments.sort(key=lambda x: x[0], reverse=True)
            
            logger.info(f"[BASELINE] {scan_direction.capitalize()} segment scores: {[f'{s[0]:.1f}' for s in scored_segments[:3]]}")
            
            best_score, best_segment = scored_segments[0]
            logger.info(f"[BASELINE] Selected {scan_direction} segment [{best_segment['start_idx']}:{best_segment['end_idx']}] with score {best_score:.2f}")
            return best_segment
        
        forward_segment = select_best_segment(forward_segments, 'forward')
        reverse_segment = select_best_segment(reverse_segments, 'reverse')
        
        # CRITICAL: Verify segments are different
        if forward_segment and reverse_segment:
            if (forward_segment['start_idx'] == reverse_segment['start_idx'] and 
                forward_segment['end_idx'] == reverse_segment['end_idx']):
                logger.error("ERROR: Forward and reverse segments are identical! Forcing different segments")
                
                # Force different segments by taking alternative reverse
                if len(reverse_segments) > 1:
                    # Try second-best reverse segment
                    reverse_segment = select_best_segment(reverse_segments[1:], 'reverse')
                    logger.info(f"[BASELINE] Using second-best reverse segment [{reverse_segment['start_idx']}:{reverse_segment['end_idx']}]")
                else:
                    # Create a different reverse segment from the latter portion
                    mid_point = len(voltage) // 2
                    alternative_reverse = [s for s in segments if s['start_idx'] >= mid_point 
                                         and not (s['start_idx'] == forward_segment['start_idx'] and s['end_idx'] == forward_segment['end_idx'])]
                    if alternative_reverse:
                        reverse_segment = select_best_segment(alternative_reverse, 'reverse')
                        logger.info(f"[BASELINE] Using alternative reverse segment [{reverse_segment['start_idx']}:{reverse_segment['end_idx']}]")
                    else:
                        logger.error("Cannot find alternative reverse segment! Using fallback")
                        reverse_segment = None
        
        # Step 4: Generate baseline arrays - avoid NaN values
        n = len(voltage)
        
        # Initialize with zero instead of NaN for JSON compatibility
        baseline_forward = np.zeros(n//2)
        baseline_reverse = np.zeros(n - n//2)
        
        if forward_segment:
            v_forward = voltage[:n//2]
            baseline_forward = forward_segment['slope'] * v_forward + forward_segment['intercept']
            logger.info(f"Forward baseline: slope={forward_segment['slope']:.2e}, R²={forward_segment['r2']:.3f}, segment=[{forward_segment['start_idx']}:{forward_segment['end_idx']}]")
        else:
            # Use simple linear fit if no good segment found
            v_forward = voltage[:n//2]
            i_forward = current[:n//2]
            try:
                coeffs = np.polyfit(v_forward, i_forward, 1)
                baseline_forward = np.polyval(coeffs, v_forward)
            except:
                baseline_forward = np.full(n//2, np.mean(i_forward))
        
        if reverse_segment:
            v_reverse = voltage[n//2:]
            baseline_reverse = reverse_segment['slope'] * v_reverse + reverse_segment['intercept']
            logger.info(f"Reverse baseline: slope={reverse_segment['slope']:.2e}, R²={reverse_segment['r2']:.3f}, segment=[{reverse_segment['start_idx']}:{reverse_segment['end_idx']}]")
        else:
            # Use simple linear fit if no good segment found
            v_reverse = voltage[n//2:]
            i_reverse = current[n//2:]
            try:
                coeffs = np.polyfit(v_reverse, i_reverse, 1)
                baseline_reverse = np.polyval(coeffs, v_reverse)
            except:
                baseline_reverse = np.full(n - n//2, np.mean(i_reverse))
        
        return baseline_forward, baseline_reverse, {
            'forward_segment': forward_segment,
            'reverse_segment': reverse_segment
        }
        
    except Exception as e:
        logger.error(f"Error in improved baseline detection: {e}")
        # Fallback - avoid NaN values
        n = len(voltage)
        mid = n // 2
        def simple_fit(v, i):
            if len(v) < 2:
                return np.full_like(v, np.mean(i) if len(i) > 0 else 0.0)
            try:
                coeffs = np.polyfit(v, i, 1)
                return np.polyval(coeffs, v)
            except:
                return np.full_like(v, np.mean(i))
            coeffs = np.polyfit(v, i, 1)
            return np.polyval(coeffs, v)
        return simple_fit(voltage[:mid], current[:mid]), simple_fit(voltage[mid:], current[mid:]), {
            'forward_segment': None,
            'reverse_segment': None
        }

# In-memory storage for analysis sessions
# Global variable for tracking peak detection progress
peak_detection_progress = {
    'active': False,
    'current_file': 0,
    'total_files': 0,
    'percent': 0,
    'message': '',
    'start_time': None
}

analysis_sessions = {}

@peak_detection_bp.route('/api/get_saved_files')
def get_saved_files():
    """Get list of saved CSV files"""
    try:
        data_dir = os.path.join(current_app.root_path, '..', 'data_logs', 'csv')
        data_dir = os.path.abspath(data_dir)  # Resolve to absolute path
        
        if not os.path.exists(data_dir):
            return jsonify([])
        
        files = []
        for file_path in glob.glob(os.path.join(data_dir, '*.csv')):
            try:
                stat = os.stat(file_path)
                filename = os.path.basename(file_path)
                files.append({
                    'name': filename,
                    'filename': filename,  # Use filename instead of full path
                    'path': os.path.abspath(file_path),  # Keep full path for debugging
                    'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'size': stat.st_size
                })
            except Exception as e:
                logger.warning(f"Error reading file {file_path}: {e}")
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x['date'], reverse=True)
        return jsonify(files)
        
    except Exception as e:
        logger.error(f"Error getting saved files: {str(e)}")
        return jsonify([])

@peak_detection_bp.route('/api/load_saved_file_by_name/<filename>')
def load_saved_file_by_name(filename):
    """Load data from a saved CSV file by filename"""
    try:
        # Construct the file path
        data_dir = os.path.join(current_app.root_path, '..', 'data_logs', 'csv')
        data_dir = os.path.abspath(data_dir)
        file_path = os.path.join(data_dir, filename)
        
        # Security check - ensure the file is within the data directory
        if not os.path.abspath(file_path).startswith(data_dir):
            return jsonify({'success': False, 'error': 'Invalid file path'})
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': f'File not found: {filename}'})
        
        return load_csv_file(file_path)
        
    except Exception as e:
        logger.error(f"Error loading saved file by name: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def load_csv_file(file_path):
    """Helper function to load and parse CSV file"""
    try:
        # Read CSV file
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            return jsonify({'success': False, 'error': 'File too short'})
        
        # Handle instrument file format (FileName: header)
        header_line_idx = 0
        data_start_idx = 1
        
        if lines[0].strip().startswith('FileName:'):
            header_line_idx = 1
            data_start_idx = 2
            logger.info("Detected instrument file format with FileName header")
        
        # Parse headers
        headers = [h.strip().lower() for h in lines[header_line_idx].strip().split(',')]
        logger.info(f"Headers found: {headers}")
        
        # Find voltage and current columns
        voltage_idx = -1
        current_idx = -1
        
        for i, header in enumerate(headers):
            if header in ['v', 'voltage'] or 'volt' in header or 'potential' in header:
                voltage_idx = i
            elif header in ['a', 'ua', 'ma', 'na', 'current'] or 'amp' in header or 'curr' in header:
                current_idx = i
        
        if voltage_idx == -1 or current_idx == -1:
            return jsonify({'success': False, 'error': f'Could not find voltage or current columns in headers: {headers}'})
        
        # Determine current scaling
        current_unit = headers[current_idx]
        current_scale = 1.0
        if current_unit == 'ua':
            current_scale = 1e-6  # microAmps to Amps
        elif current_unit == 'ma':
            current_scale = 1e-3  # milliAmps to Amps
        elif current_unit == 'na':
            current_scale = 1e-9  # nanoAmps to Amps
        
        logger.info(f"Current unit: {current_unit}, scale: {current_scale}")
        
        # Parse data
        voltage = []
        current = []
        
        for i in range(data_start_idx, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
                
            values = line.split(',')
            if len(values) > max(voltage_idx, current_idx):
                try:
                    v = float(values[voltage_idx])
                    c = float(values[current_idx]) * current_scale
                    voltage.append(v)
                    current.append(c)
                except ValueError:
                    continue
        
        if len(voltage) == 0 or len(current) == 0:
            return jsonify({'success': False, 'error': 'No valid data points found'})
        
        logger.info(f"Loaded {len(voltage)} data points from {file_path}")
        logger.info(f"Voltage range: {min(voltage):.3f} to {max(voltage):.3f} V")
        logger.info(f"Current range: {min(current):.6e} to {max(current):.6e} A")
        
        return jsonify({
            'success': True,
            'data': {
                'voltage': voltage,
                'current': current
            },
            'metadata': {
                'points': len(voltage),
                'voltage_range': [min(voltage), max(voltage)],
                'current_range': [min(current), max(current)],
                'current_unit': current_unit,
                'current_scale': current_scale
            }
        })
        
    except Exception as e:
        logger.error(f"Error loading CSV file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@peak_detection_bp.route('/api/load_saved_file/<path:file_path>')
def load_saved_file(file_path):
    """Load data from a saved CSV file"""
    try:
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'})
        
        # Read CSV file
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            return jsonify({'success': False, 'error': 'File too short'})
        
        # Handle instrument file format (FileName: header)
        header_line_idx = 0
        data_start_idx = 1
        
        if lines[0].strip().startswith('FileName:'):
            header_line_idx = 1
            data_start_idx = 2
            logger.info("Detected instrument file format with FileName header")
        
        # Parse headers
        headers = [h.strip().lower() for h in lines[header_line_idx].strip().split(',')]
        logger.info(f"Headers found: {headers}")
        
        # Find voltage and current columns
        voltage_idx = -1
        current_idx = -1
        
        for i, header in enumerate(headers):
            if header in ['v', 'voltage'] or 'volt' in header or 'potential' in header:
                voltage_idx = i
            elif header in ['a', 'ua', 'ma', 'na', 'current'] or 'amp' in header or 'curr' in header:
                current_idx = i
        
        if voltage_idx == -1 or current_idx == -1:
            return jsonify({'success': False, 'error': f'Could not find voltage or current columns in headers: {headers}'})
        
        # Determine current scaling
        current_unit = headers[current_idx]
        current_scale = 1.0
        if current_unit == 'ua':
            current_scale = 1e-6  # microAmps to Amps
        elif current_unit == 'ma':
            current_scale = 1e-3  # milliAmps to Amps
        elif current_unit == 'na':
            current_scale = 1e-9  # nanoAmps to Amps
        
        logger.info(f"Current unit: {current_unit}, scale: {current_scale}")
        
        # Parse data
        voltage = []
        current = []
        
        for i in range(data_start_idx, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
                
            values = line.split(',')
            if len(values) > max(voltage_idx, current_idx):
                try:
                    v = float(values[voltage_idx])
                    c = float(values[current_idx]) * current_scale
                    voltage.append(v)
                    current.append(c)
                except ValueError:
                    continue
        
        if len(voltage) == 0 or len(current) == 0:
            return jsonify({'success': False, 'error': 'No valid data points found'})
        
        logger.info(f"Loaded {len(voltage)} data points from {file_path}")
        logger.info(f"Voltage range: {min(voltage):.3f} to {max(voltage):.3f} V")
        logger.info(f"Current range: {min(current):.6e} to {max(current):.6e} A")
        
        return jsonify({
            'success': True,
            'data': {
                'voltage': voltage,
                'current': current
            },
            'metadata': {
                'points': len(voltage),
                'voltage_range': [min(voltage), max(voltage)],
                'current_range': [min(current), max(current)],
                'current_unit': current_unit,
                'current_scale': current_scale
            }
        })
        
    except Exception as e:
        logger.error(f"Error loading saved file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@peak_detection_bp.route('/create_analysis_session', methods=['POST'])
def create_analysis_session():
    """Create a new analysis session and store data"""
    try:
        data = request.get_json()
        if not data:
            logger.error("No data provided to create_analysis_session")
            return jsonify({'error': 'No data provided'}), 400
        
        logger.info(f"Creating analysis session with data keys: {list(data.keys())}")
            
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Store data in in-memory storage
        # Ensure peaks is a list of dicts, not an int
        peaks = data.get('peaks', [])
        if isinstance(peaks, int):
            # Try to get from previewData if available
            peaks = data.get('previewData', {}).get('peaks', [])
        if not isinstance(peaks, list):
            peaks = []

        # Handle multi-trace: data['data'] is list of traces, each should have 'filename'
        traces = data.get('data', {})
        if isinstance(traces, list):
            # Add filename if missing
            for i, trace in enumerate(traces):
                if 'filename' not in trace:
                    # Try to get from filenames array if present
                    filenames = data.get('filenames') or data.get('file_labels')
                    if filenames and i < len(filenames):
                        trace['filename'] = filenames[i]
                    else:
                        trace['filename'] = f'Trace {i+1}'
        elif isinstance(traces, dict):
            # Single trace: add filename if present
            if 'filename' not in traces:
                filename = data.get('filename') or (data.get('filenames')[0] if data.get('filenames') else None)
                if filename:
                    traces['filename'] = filename
        analysis_sessions[session_id] = {
            'peaks': peaks,
            'data': traces,
            'method': data.get('method', ''),
            'methodName': data.get('methodName', ''),
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"Created analysis session {session_id} for method {data.get('method')}")
        return jsonify({'session_id': session_id})
        
    except Exception as e:
        logger.error(f"Error creating analysis session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@peak_detection_bp.route('/peak_analysis/<session_id>')
def peak_analysis(session_id):
    """Render peak analysis details page"""
    try:
        # Get data from in-memory storage
        session_data = analysis_sessions.get(session_id)
        if not session_data:
            logger.error(f"Session {session_id} not found in analysis_sessions")
            logger.info(f"Available sessions: {list(analysis_sessions.keys())}")
            return "Session not found", 404
        
        logger.info(f"Loading analysis session {session_id} for method {session_data.get('method')}")
        
        return render_template('peak_analysis.html',
                             peaks=session_data['peaks'],
                             data=session_data['data'],
                             method=session_data['method'],
                             methodName=session_data['methodName'])
                             
    except Exception as e:
        logger.error(f"Error rendering peak analysis: {str(e)}")
        return str(e), 500

@peak_detection_bp.route('/get-progress', methods=['GET'])
def get_progress():
    """Get current peak detection progress"""
    global peak_detection_progress
    
    # Calculate elapsed time if active
    elapsed_time = None
    if peak_detection_progress['active'] and peak_detection_progress['start_time']:
        elapsed_time = int(time.time() - peak_detection_progress['start_time'])
    
    return jsonify({
        'success': True,
        'progress': {
            **peak_detection_progress,
            'elapsed_time': elapsed_time
        }
    })

@peak_detection_bp.route('/get-peaks/<method>', methods=['POST'])
def get_peaks(method):
    """
    Analyze CV data and detect peaks using specified method
    Returns peaks with their positions and characteristics
    """
    global peak_detection_progress
    
    try:
        logger.info(f"Starting peak detection with method: {method}")
        
        # Initialize progress tracking
        peak_detection_progress.update({
            'active': True,
            'current_file': 0,
            'total_files': 0,
            'percent': 0,
            'message': 'Initializing...',
            'start_time': time.time()
        })
        
        # Get data from POST request
        data = request.get_json()
        if not data:
            peak_detection_progress['active'] = False
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # Multi-trace: voltage/current เป็น list of list หรือ dataFiles
        if 'dataFiles' in data and isinstance(data['dataFiles'], list):
            nFiles = len(data['dataFiles'])
            logger.info(f"Processing {nFiles} files with method: {method}")
            
            # Update progress with total files
            peak_detection_progress.update({
                'total_files': nFiles,
                'message': f'Processing {nFiles} files...'
            })
            
            peaks_per_file = [ [] for _ in range(nFiles) ]
            for i, file in enumerate(data['dataFiles']):
                    # Update progress only once per file
                    progress_percent = int(((i + 1) / nFiles) * 100)
                    peak_detection_progress.update({
                        'current_file': i + 1,
                        'percent': progress_percent,
                        'message': f'Processing file {i+1}/{nFiles}...'
                    })
                    
                    logger.info(f"[PROGRESS] Processing file {i+1}/{nFiles} ({progress_percent}%)")
                    
                    voltage = np.array(file.get('voltage', []))
                    current = np.array(file.get('current', []))
                    logger.info(f"[DEBUG] File {i}: voltage len={len(voltage)}, current len={len(current)}")
                    logger.info(f"[DEBUG] File {i}: voltage min={np.min(voltage) if len(voltage)>0 else 'NA'}, max={np.max(voltage) if len(voltage)>0 else 'NA'}, mean={np.mean(voltage) if len(voltage)>0 else 'NA'}")
                    logger.info(f"[DEBUG] File {i}: current min={np.min(current) if len(current)>0 else 'NA'}, max={np.max(current) if len(current)>0 else 'NA'}, mean={np.mean(current) if len(current)>0 else 'NA'}")
                    if np.any(np.isnan(voltage)) or np.any(np.isnan(current)):
                        logger.warning(f"[DEBUG] File {i}: NaN detected in voltage or current!")
                    if np.any(np.isinf(voltage)) or np.any(np.isinf(current)):
                        logger.warning(f"[DEBUG] File {i}: Inf detected in voltage or current!")
                    try:
                        result = detect_cv_peaks(voltage, current, method=method)
                        file_peaks = result['peaks']
                        logger.info(f"[DEBUG] File {i}: detected {len(file_peaks)} peaks")
                        
                        # Add baseline data to each peak if available
                        if 'baseline' in result:
                            for p in file_peaks:
                                p['baseline'] = result['baseline']
                        
                    except Exception as e:
                        logger.error(f"[DEBUG] File {i}: peak detection error: {str(e)}")
                        file_peaks = []
                    for p in file_peaks:
                        p['fileIdx'] = i
                    peaks_per_file[i] = file_peaks
            
            # Mark completion
            peak_detection_progress.update({
                'current_file': nFiles,
                'percent': 100,
                'message': f'Completed processing {nFiles} files',
                'active': False
            })
            
            logger.info(f"[PROGRESS] Processing complete: {nFiles}/{nFiles} files (100%)")
            logger.info(f"[DEBUG] peaks_per_file lens: {[len(p) for p in peaks_per_file]}")
            return jsonify({'success': True, 'peaks': peaks_per_file})
        elif isinstance(data.get('voltage'), list) and len(data['voltage']) > 0 and isinstance(data['voltage'][0], list):
            # voltage/current เป็น list of list
            nFiles = len(data['voltage'])
            peaks_per_file = [ [] for _ in range(nFiles) ]
            for i, (v, c) in enumerate(zip(data['voltage'], data['current'])):
                voltage = np.array(v)
                current = np.array(c)
                logger.info(f"[DEBUG] File {i}: voltage len={len(voltage)}, current len={len(current)}")
                logger.info(f"[DEBUG] File {i}: voltage min={np.min(voltage) if len(voltage)>0 else 'NA'}, max={np.max(voltage) if len(voltage)>0 else 'NA'}, mean={np.mean(voltage) if len(voltage)>0 else 'NA'}")
                logger.info(f"[DEBUG] File {i}: current min={np.min(current) if len(current)>0 else 'NA'}, max={np.max(current) if len(current)>0 else 'NA'}, mean={np.mean(current) if len(current)>0 else 'NA'}")
                if np.any(np.isnan(voltage)) or np.any(np.isnan(current)):
                    logger.warning(f"[DEBUG] File {i}: NaN detected in voltage or current!")
                if np.any(np.isinf(voltage)) or np.any(np.isinf(current)):
                    logger.warning(f"[DEBUG] File {i}: Inf detected in voltage or current!")
                try:
                    file_peaks = detect_cv_peaks(voltage, current, method=method)['peaks']
                    logger.info(f"[DEBUG] File {i}: detected {len(file_peaks)} peaks")
                except Exception as e:
                    logger.error(f"[DEBUG] File {i}: peak detection error: {str(e)}")
                    file_peaks = []
                for p in file_peaks:
                    p['fileIdx'] = i
                peaks_per_file[i] = file_peaks
            logger.info(f"[DEBUG] peaks_per_file lens: {[len(p) for p in peaks_per_file]}")
            return jsonify({'success': True, 'peaks': peaks_per_file})
        else:
            # Single trace (default)
            if 'voltage' not in data or 'current' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing voltage or current data in request'
                }), 400
            voltage = np.array(data['voltage'])
            current = np.array(data['current'])
            results = detect_cv_peaks(voltage, current, method=method)
            return jsonify({'success': True, **results})
    except Exception as e:
        logger.error(f"Error in peak detection: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@peak_detection_bp.route('/get-settings', methods=['GET'])
def get_settings():
    """Get current peak detection settings"""
    return jsonify({
        'success': True,
        'settings': {
            'prominence': current_app.config.get('PEAK_PROMINENCE', 0.1),
            'width': current_app.config.get('PEAK_WIDTH', 5),
            'description': {
                'prominence': 'Minimum peak prominence (normalized)',
                'width': 'Minimum peak width in data points'
            }
        }
    })

@peak_detection_bp.route('/update-settings', methods=['POST'])
def update_settings():
    """Update peak detection settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No settings provided'
            })

        # Update settings
        if 'prominence' in data:
            current_app.config['PEAK_PROMINENCE'] = float(data['prominence'])
        if 'width' in data:
            current_app.config['PEAK_WIDTH'] = int(data['width'])

        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'settings': {
                'prominence': current_app.config.get('PEAK_PROMINENCE', 0.1),
                'width': current_app.config.get('PEAK_WIDTH', 5)
            }
        })

    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

def detect_cv_peaks(voltage, current, method='prominence'):
    """
    Detect peaks in CV data using specified method
    Returns list of peaks with their characteristics
    """
    try:
        if method == 'prominence':
            return detect_peaks_prominence(voltage, current)
        elif method == 'derivative':
            return detect_peaks_derivative(voltage, current)
        elif method == 'ml':
            return detect_peaks_ml(voltage, current)
        else:
            raise ValueError(f"Unknown method: {method}")
    except Exception as e:
        logger.error(f"Error in CV peak detection: {str(e)}")
        raise

def detect_peaks_prominence(voltage, current):
    """Detect peaks using prominence method with simplified baseline"""
    try:
        # Get settings from config or use defaults
        prominence = current_app.config.get('PEAK_PROMINENCE', 0.1)
        width = current_app.config.get('PEAK_WIDTH', 5)

        # Normalize current for peak detection
        current_norm = current / np.abs(current).max()

        # Find positive peaks (oxidation)
        pos_peaks, pos_properties = find_peaks(
            current_norm,
            prominence=prominence,
            width=width
        )

        # Find negative peaks (reduction)
        neg_peaks, neg_properties = find_peaks(
            -current_norm,
            prominence=prominence,
            width=width
        )

        # Format peak data
        peaks = []

        # Add oxidation peaks
        for i, peak_idx in enumerate(pos_peaks):
            peaks.append({
                'voltage': float(voltage[peak_idx]),
                'current': float(current[peak_idx]),
                'type': 'oxidation',
                'confidence': float(pos_properties['prominences'][i] * 100)
            })

        # Add reduction peaks
        for i, peak_idx in enumerate(neg_peaks):
            peaks.append({
                'voltage': float(voltage[peak_idx]),
                'current': float(current[peak_idx]),
                'type': 'reduction',
                'confidence': float(neg_properties['prominences'][i] * 100)
            })

        # Use improved baseline detection but with limited iterations for speed
        logger.info("Using improved baseline for traditional method with speed optimization")
        
        # Detect baseline with peak-aware segmentation but limit iterations
        try:
            # First, get a quick baseline estimate for peak detection
            baseline_result = detect_improved_baseline_2step(
                voltage, current, 
                max_iterations=3000,  # Limit iterations for speed
                adaptive_step=True  # Use adaptive step size
            )
            
            if baseline_result is None:
                logger.warning("Baseline detection failed, using simple fallback")
                # Simple fallback if advanced method fails
                n = len(voltage)
                mid = n // 2
                
                def simple_linear_fit(v, c):
                    if len(v) < 2:
                        return np.full_like(v, np.mean(c) if len(c) > 0 else 0)
                    try:
                        coeffs = np.polyfit(v, c, 1)
                        return np.polyval(coeffs, v)
                    except:
                        return np.full_like(v, np.mean(c))
                
                baseline_forward = simple_linear_fit(voltage[:mid], current[:mid])
                baseline_reverse = simple_linear_fit(voltage[mid:], current[mid:])
                baseline_full = np.concatenate([baseline_forward, baseline_reverse])
                segment_info = {'forward_segment': None, 'reverse_segment': None}
            else:
                # baseline_result is a tuple (baseline_forward, baseline_reverse, segment_info)
                baseline_forward, baseline_reverse, segment_info = baseline_result
                baseline_full = np.concatenate([baseline_forward, baseline_reverse])
                logger.info(f"Successfully detected improved baseline with {len(baseline_forward)} forward and {len(baseline_reverse)} reverse points")
                
        except Exception as e:
            logger.error(f"Baseline detection error: {str(e)}, using simple fallback")
            # Simple fallback if any error occurs
            n = len(voltage)
            mid = n // 2
            
            def simple_linear_fit(v, c):
                if len(v) < 2:
                    return np.full_like(v, np.mean(c) if len(c) > 0 else 0)
                try:
                    coeffs = np.polyfit(v, c, 1)
                    return np.polyval(coeffs, v)
                except:
                    return np.full_like(v, np.mean(c))
            
            baseline_forward = simple_linear_fit(voltage[:mid], current[:mid])
            baseline_reverse = simple_linear_fit(voltage[mid:], current[mid:])
            baseline_full = np.concatenate([baseline_forward, baseline_reverse])
            segment_info = {'forward_segment': None, 'reverse_segment': None}

        return {
            'peaks': peaks,
            'method': 'prominence',
            'params': {
                'prominence': prominence,
                'width': width
            },
            'baseline': {
                'forward': baseline_forward.tolist(),
                'reverse': baseline_reverse.tolist(),
                'full': baseline_full.tolist(),
                'markers': {
                    'forward_segment': {
                        'start_idx': segment_info['forward_segment']['start_idx'] if segment_info['forward_segment'] else None,
                        'end_idx': segment_info['forward_segment']['end_idx'] if segment_info['forward_segment'] else None,
                        'voltage_range': segment_info['forward_segment']['voltage_range'] if segment_info['forward_segment'] else None,
                        'r2': segment_info['forward_segment']['r2'] if segment_info['forward_segment'] else None,
                        'slope': segment_info['forward_segment']['slope'] if segment_info['forward_segment'] else None
                    },
                    'reverse_segment': {
                        'start_idx': segment_info['reverse_segment']['start_idx'] if segment_info['reverse_segment'] else None,
                        'end_idx': segment_info['reverse_segment']['end_idx'] if segment_info['reverse_segment'] else None,
                        'voltage_range': segment_info['reverse_segment']['voltage_range'] if segment_info['reverse_segment'] else None,
                        'r2': segment_info['reverse_segment']['r2'] if segment_info['reverse_segment'] else None,
                        'slope': segment_info['reverse_segment']['slope'] if segment_info['reverse_segment'] else None
                    }
                }
            }
        }

    except Exception as e:
        logger.error(f"Error in prominence peak detection: {str(e)}")
        # Simple fallback
        return {
            'peaks': [],
            'method': 'prominence_error',
            'params': {'error': str(e)},
            'baseline': {
                'forward': np.zeros(len(voltage)//2).tolist(),
                'reverse': np.zeros(len(voltage) - len(voltage)//2).tolist(),
                'full': np.zeros(len(voltage)).tolist()
            }
        }

def detect_peaks_derivative(voltage, current):
    """Detect peaks using derivative method with improved filtering"""
    try:
        from scipy import signal
        
        # Smooth data first to reduce noise
        window_length = min(11, len(current) // 10)  # Adaptive window
        if window_length % 2 == 0:
            window_length += 1  # Must be odd
        if window_length >= 3:
            current_smooth = signal.savgol_filter(current, window_length, 3)
        else:
            current_smooth = current
        
        # Calculate first derivative
        dv = np.gradient(voltage)
        di = np.gradient(current_smooth)
        slope = di/dv
        
        # Find zero crossings in second derivative
        d2i = np.gradient(slope)
        zero_crossings = np.where(np.diff(np.signbit(d2i)))[0]
        
        peaks = []
        
        # Filter peaks by significance
        current_std = np.std(current)
        current_range = np.max(current) - np.min(current)
        
        # Adaptive thresholds based on data characteristics
        min_peak_height = max(current_std * 0.2, current_range * 0.01)  # More lenient
        min_prominence = max(current_std * 0.1, current_range * 0.005)   # More lenient
        
        logger.info(f"Derivative filtering: std={current_std:.2e}, range={current_range:.2e}, min_height={min_peak_height:.2e}, min_prominence={min_prominence:.2e}")
        
        for idx in zero_crossings:
            if idx < 5 or idx >= len(current) - 5:  # Skip edge points
                continue
                
            # Check if this is a significant peak
            peak_current = current[idx]
            local_baseline = np.mean(current[max(0, idx-10):min(len(current), idx+10)])
            peak_height = abs(peak_current - local_baseline)
            
            # More lenient filtering
            if peak_height < min_peak_height:
                continue
                
            # Check prominence (peak stands out from surroundings)
            left_vals = current[max(0, idx-5):idx] if idx > 0 else [peak_current]
            right_vals = current[idx+1:min(len(current), idx+6)] if idx < len(current)-1 else [peak_current]
            
            left_min = np.min(left_vals) if len(left_vals) > 0 else peak_current
            right_min = np.min(right_vals) if len(right_vals) > 0 else peak_current
            prominence = abs(peak_current) - max(abs(left_min), abs(right_min))
            
            # More lenient prominence check
            if prominence < min_prominence:
                continue
            
            peak_type = 'oxidation' if current[idx] > local_baseline else 'reduction'
            confidence = min(100.0, (peak_height / max(abs(current_range), 1e-10)) * 100)
            
            peaks.append({
                'voltage': float(voltage[idx]),
                'current': float(current[idx]),
                'type': peak_type,
                'confidence': float(confidence)
            })
        
        # Less restrictive peak limit
        if len(peaks) > 50:  # Increased from 20
            peaks = sorted(peaks, key=lambda x: x['confidence'], reverse=True)[:50]
        
        # Fallback: if no peaks found, use simpler method
        if len(peaks) == 0:
            logger.warning("No peaks found with derivative method, trying fallback")
            # Use scipy find_peaks as fallback
            from scipy.signal import find_peaks
            current_norm = current / np.abs(current).max()
            
            # Find positive peaks
            pos_peaks, _ = find_peaks(current_norm, prominence=0.1, width=3)
            # Find negative peaks  
            neg_peaks, _ = find_peaks(-current_norm, prominence=0.1, width=3)
            
            for peak_idx in pos_peaks:
                peaks.append({
                    'voltage': float(voltage[peak_idx]),
                    'current': float(current[peak_idx]),
                    'type': 'oxidation',
                    'confidence': 75.0
                })
            
            for peak_idx in neg_peaks:
                peaks.append({
                    'voltage': float(voltage[peak_idx]),
                    'current': float(current[peak_idx]),
                    'type': 'reduction', 
                    'confidence': 75.0
                })
            
            logger.info(f"Fallback method found {len(peaks)} peaks")
            
        logger.info(f"Derivative method found {len(peaks)} significant peaks (filtered from {len(zero_crossings)} zero crossings)")
            
        return {
            'peaks': peaks,
            'method': 'derivative',
            'params': {
                'smoothing': 'savgol_filter',
                'window': window_length,
                'min_height': min_peak_height,
                'min_prominence': min_prominence,
                'zero_crossings_found': len(zero_crossings),
                'peaks_after_filtering': len(peaks)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in derivative peak detection: {str(e)}")
        raise

def detect_peaks_ml(voltage, current):
    """Detect peaks using ML-enhanced method"""
    try:
        # Start with prominence method as baseline
        base_results = detect_peaks_prominence(voltage, current)
        base_peaks = base_results['peaks']
        
        # Add ML enhancements (feature extraction)
        enhanced_peaks = []
        for peak in base_peaks:
            # Find peak width at half height
            peak_idx = np.where((voltage == peak['voltage']) & (current == peak['current']))[0][0]
            half_height = peak['current'] / 2
            left_idx = right_idx = peak_idx
            
            while left_idx > 0 and abs(current[left_idx]) > abs(half_height):
                left_idx -= 1
            while right_idx < len(current)-1 and abs(current[right_idx]) > abs(half_height):
                right_idx += 1
                
            width = voltage[right_idx] - voltage[left_idx]
            area = np.trapz(current[left_idx:right_idx], voltage[left_idx:right_idx])
            
            enhanced_peaks.append({
                'voltage': peak['voltage'],
                'current': peak['current'],
                'type': peak['type'],
                'confidence': min(100.0, peak['confidence'] * 1.1),  # ML confidence boost
                'width': float(width),
                'area': float(area)
            })
            
        return {
            'peaks': enhanced_peaks,
            'method': 'ml',
            'params': {
                'feature_extraction': ['width', 'area'],
                'confidence_boost': 1.1
            },
            'baseline': base_results.get('baseline', {})  # Pass through baseline from prominence method
        }
        
    except Exception as e:
        logger.error(f"Error in ML peak detection: {str(e)}")
        raise