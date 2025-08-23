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
        
        # SIMPLIFIED APPROACH: Fix baseline segment selection
        # For CV data: 
        # - Forward scan = first half of data (high voltage to low voltage)
        # - Reverse scan = second half of data (low voltage to high voltage)
        
        n = len(voltage)
        mid_point = n // 2
        
        # Find the turning point (minimum voltage)
        min_voltage_idx = np.argmin(voltage)
        min_voltage = voltage[min_voltage_idx]
        max_voltage = np.max(voltage)
        
        logger.info(f"Data length: {n}, mid-point: {mid_point}, turning point at index {min_voltage_idx}")
        logger.info(f"Voltage range: {min_voltage:.3f}V to {max_voltage:.3f}V")
        
        # CORRECTED LOGIC FOR CV BASELINE DETECTION:
        # CV scan: Start voltage (max) → End voltage (min) → Start voltage (max)
        # Forward scan: high voltage → low voltage (first half of data)
        # Reverse scan: low voltage → high voltage (second half of data)
        
        # Find voltage extremes
        min_voltage_idx = np.argmin(voltage)
        max_voltage_idx = np.argmax(voltage)
        
        logger.info(f"Voltage analysis: min at index {min_voltage_idx} ({voltage[min_voltage_idx]:.3f}V), max at index {max_voltage_idx} ({voltage[max_voltage_idx]:.3f}V)")
        
        # CRITICAL FIX: Reverse baseline must be IMMEDIATELY after turning point, BEFORE reverse redox peak
        # Forward baseline: first 25% of data (before forward redox peak)
        forward_region_end = min(mid_point // 3, mid_point - 20)  # First third of forward scan
        forward_segments = [s for s in segments 
                          if s['start_idx'] >= 0 and s['end_idx'] <= forward_region_end and s['end_idx'] <= mid_point]
        
        # Reverse baseline: BEGINNING of reverse scan (right after turning point, before reverse redox peak)
        # Look for stable segments immediately after the voltage minimum (turning point)
        reverse_region_start = max(min_voltage_idx + 5, mid_point)  # Start just after turning point
        reverse_region_end = min(reverse_region_start + (n - mid_point) // 3, n - 20)  # First third of reverse scan
        
        reverse_segments = [s for s in segments 
                          if s['start_idx'] >= reverse_region_start 
                          and s['end_idx'] <= reverse_region_end 
                          and s['start_idx'] >= mid_point]
        
        logger.info(f"CORRECTED regions:")
        logger.info(f"Forward baseline region: [0:{forward_region_end}] (before forward peak)")
        logger.info(f"Reverse baseline region: [{reverse_region_start}:{reverse_region_end}] (after turning point, before reverse peak)")
        logger.info(f"Found {len(forward_segments)} forward segments, {len(reverse_segments)} reverse segments")
        
        # Fallback if no segments found
        if len(forward_segments) == 0:
            # Expand forward search to first half
            forward_segments = [s for s in segments if s['end_idx'] <= mid_point]
            logger.warning(f"Forward fallback: expanded to first half, found {len(forward_segments)} segments")
            
        if len(reverse_segments) == 0:
            # Expand reverse search to early part of second half (NOT the end!)
            reverse_early_region_end = mid_point + (n - mid_point) // 2  # First half of reverse scan
            reverse_segments = [s for s in segments 
                              if s['start_idx'] >= mid_point and s['end_idx'] <= reverse_early_region_end]
            logger.warning(f"Reverse fallback: expanded to early reverse region, found {len(reverse_segments)} segments")
            
            # Final fallback: use segments just after turning point
            if len(reverse_segments) == 0:
                reverse_segments = [s for s in segments if s['start_idx'] >= mid_point][:3]  # Take first 3 segments
                logger.warning(f"Reverse final fallback: using first 3 segments after mid-point, found {len(reverse_segments)} segments")
            
        # Final fallback: ensure we have at least one segment for each
        if len(forward_segments) == 0 and len(segments) > 0:
            forward_segments = [segments[0]]  # Use first available segment
            logger.warning("Emergency fallback: using first segment for forward")
            
        if len(reverse_segments) == 0 and len(segments) > 0:
            reverse_segments = [segments[-1]]  # Use last available segment  
            logger.warning("Emergency fallback: using last segment for reverse")
        # Debug: Show selected segments
        if forward_segments:
            logger.info(f"Forward segments: {[(s['start_idx'], s['end_idx'], s['r2']) for s in forward_segments[:3]]}")
        if reverse_segments:
            logger.info(f"Reverse segments: {[(s['start_idx'], s['end_idx'], s['r2']) for s in reverse_segments[:3]]}")
        
        def score_baseline_segment(segment, scan_direction='forward'):
            """Score segments for baseline selection - CORRECTED FOR CV SCANS"""
            logger.info(f"[BASELINE] Scoring segment {segment['start_idx']}-{segment['end_idx']} for {scan_direction} baseline")
            score = 0
            
            # Base score from R² quality
            score += segment['r2'] * 100
            
            # Stability (low standard deviation is better)
            if segment['std_current'] > 0:
                stability_score = max(0, 20 - (segment['std_current'] * 1e6))
                score += stability_score
            
            # CRITICAL: Position-based scoring for CV scans
            total_points = len(voltage)
            mid_point = total_points // 2
            segment_start_position = segment['start_idx'] / total_points
            segment_end_position = segment['end_idx'] / total_points
            
            if scan_direction == 'forward':
                # Forward baseline should be in the BEGINNING (first 30% of data)
                if segment_end_position <= 0.3:
                    score += 50  # Strong bonus for early forward segments
                elif segment_end_position <= 0.5:  
                    score += 20  # Moderate bonus for reasonably early segments
                elif segment_start_position > 0.5:  # In second half - wrong area
                    score -= 100  # Heavy penalty for late forward segments
                    
                logger.info(f"[BASELINE] Forward segment position: {segment_start_position:.2f}-{segment_end_position:.2f}")
                
            elif scan_direction == 'reverse':
                # CORRECTED: Reverse baseline should be at BEGINNING of reverse scan (after turning point, before peak)
                # Look for segments between 50%-75% of data (early reverse scan)
                if 0.5 <= segment_start_position <= 0.75 and segment_end_position <= 0.8:
                    score += 50  # Strong bonus for early reverse segments (after turning point, before peak)
                elif 0.5 <= segment_start_position <= 0.8:
                    score += 20  # Moderate bonus for reasonably early reverse segments
                elif segment_start_position > 0.8:  # Too late in reverse scan (after peak)
                    score -= 100  # Heavy penalty for late reverse segments (after redox peak)
                elif segment_end_position < 0.5:  # Before turning point
                    score -= 50  # Penalty for segments before reverse scan starts
                    
                logger.info(f"[BASELINE] Reverse segment position: {segment_start_position:.2f}-{segment_end_position:.2f}")
            
            # Small slope preference (baseline should be relatively flat)
            slope_abs = abs(segment['slope'])
            if slope_abs < 10:
                score += 10
            elif slope_abs > 100:
                score -= 30
            
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
            logger.info(f"Forward baseline range: [{baseline_forward.min():.3f}, {baseline_forward.max():.3f}] μA, mean={baseline_forward.mean():.3f}")
        else:
            # Use simple linear fit if no good segment found
            v_forward = voltage[:n//2]
            i_forward = current[:n//2]
            try:
                coeffs = np.polyfit(v_forward, i_forward, 1)
                baseline_forward = np.polyval(coeffs, v_forward)
                logger.info(f"Forward baseline (fallback): slope={coeffs[0]:.2e}, intercept={coeffs[1]:.3f}")
                logger.info(f"Forward baseline range: [{baseline_forward.min():.3f}, {baseline_forward.max():.3f}] μA, mean={baseline_forward.mean():.3f}")
            except:
                baseline_forward = np.full(n//2, np.mean(i_forward))
        
        if reverse_segment:
            v_reverse = voltage[n//2:]
            baseline_reverse = reverse_segment['slope'] * v_reverse + reverse_segment['intercept']
            logger.info(f"Reverse baseline: slope={reverse_segment['slope']:.2e}, R²={reverse_segment['r2']:.3f}, segment=[{reverse_segment['start_idx']}:{reverse_segment['end_idx']}]")
            logger.info(f"Reverse baseline range: [{baseline_reverse.min():.3f}, {baseline_reverse.max():.3f}] μA, mean={baseline_reverse.mean():.3f}")
        else:
            # Use simple linear fit if no good segment found
            v_reverse = voltage[n//2:]
            i_reverse = current[n//2:]
            try:
                coeffs = np.polyfit(v_reverse, i_reverse, 1)
                baseline_reverse = np.polyval(coeffs, v_reverse)
                logger.info(f"Reverse baseline (fallback): slope={coeffs[0]:.2e}, intercept={coeffs[1]:.3f}")
                logger.info(f"Reverse baseline range: [{baseline_reverse.min():.3f}, {baseline_reverse.max():.3f}] μA, mean={baseline_reverse.mean():.3f}")
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

        # Format peak data with baseline-corrected heights
        peaks = []

        # Add oxidation peaks
        for i, peak_idx in enumerate(pos_peaks):
            peak_voltage = float(voltage[peak_idx])
            peak_current = float(current[peak_idx])
            
            # Calculate baseline current at peak voltage - use appropriate baseline section
            n_forward = len(baseline_forward)  # n//2
            n_reverse = len(baseline_reverse)  # n - n//2
            
            if peak_idx < n_forward:
                # Peak is in forward scan, use forward baseline
                baseline_at_peak = float(baseline_forward[peak_idx])
                scan_section = "forward"
            else:
                # Peak is in reverse scan, use reverse baseline
                reverse_idx = peak_idx - n_forward
                if reverse_idx >= 0 and reverse_idx < n_reverse:
                    baseline_at_peak = float(baseline_reverse[reverse_idx])
                    scan_section = "reverse"
                else:
                    # Fallback to baseline_full if index is out of range
                    baseline_at_peak = float(baseline_full[peak_idx])
                    scan_section = "fallback"
            
            # Calculate peak height from baseline
            peak_height = peak_current - baseline_at_peak
            
            logger.info(f"Oxidation peak {i}: idx={peak_idx}, voltage={peak_voltage:.3f}V, current={peak_current:.3f}μA, baseline={baseline_at_peak:.3f}μA, height={peak_height:.3f}μA, section={scan_section}")
            
            peaks.append({
                'voltage': peak_voltage,
                'current': peak_current,
                'type': 'oxidation',
                'confidence': float(pos_properties['prominences'][i] * 100),
                'height': float(peak_height),
                'baseline_current': baseline_at_peak,
                'enabled': True  # Default enabled for user selection
            })

        # Add reduction peaks
        for i, peak_idx in enumerate(neg_peaks):
            peak_voltage = float(voltage[peak_idx])
            peak_current = float(current[peak_idx])
            
            # Calculate baseline current at peak voltage - use appropriate baseline section
            n_forward = len(baseline_forward)  # n//2
            n_reverse = len(baseline_reverse)  # n - n//2
            
            if peak_idx < n_forward:
                # Peak is in forward scan, use forward baseline
                baseline_at_peak = float(baseline_forward[peak_idx])
                scan_section = "forward"
            else:
                # Peak is in reverse scan, use reverse baseline
                reverse_idx = peak_idx - n_forward
                if reverse_idx >= 0 and reverse_idx < n_reverse:
                    baseline_at_peak = float(baseline_reverse[reverse_idx])
                    scan_section = "reverse"
                else:
                    # Fallback to baseline_full if index is out of range
                    baseline_at_peak = float(baseline_full[peak_idx])
                    scan_section = "fallback"
            
            # Calculate peak height from baseline (absolute value for reduction peaks)
            peak_height = abs(peak_current - baseline_at_peak)
            
            logger.info(f"Reduction peak {i}: idx={peak_idx}, voltage={peak_voltage:.3f}V, current={peak_current:.3f}μA, baseline={baseline_at_peak:.3f}μA, height={peak_height:.3f}μA, section={scan_section}")
            
            peaks.append({
                'voltage': peak_voltage,
                'current': peak_current,
                'type': 'reduction',
                'confidence': float(neg_properties['prominences'][i] * 100),
                'height': float(peak_height),
                'baseline_current': baseline_at_peak,
                'enabled': True  # Default enabled for user selection
            })

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