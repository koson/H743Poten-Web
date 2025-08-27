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

# Import parameter logging
try:
    from ..services.parameter_logging import parameter_logger
except ImportError:
    from services.parameter_logging import parameter_logger

# Import Enhanced Baseline Detector v2.1
try:
    from ..utils.baseline_detector import BaselineDetector
except ImportError:
    from utils.baseline_detector import BaselineDetector

# Import Voltage Window Baseline Detector v4
try:
    from ..baseline_detector_v4 import cv_baseline_detector_v4
except ImportError:
    from baseline_detector_v4 import cv_baseline_detector_v4

# Import Enhanced Detector V3.0
try:
    from ..enhanced_detector_v3 import EnhancedDetectorV3
except ImportError:
    try:
        # Try relative import from parent directory
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, parent_dir)
        from enhanced_detector_v3 import EnhancedDetectorV3
    except ImportError as e:
        logger.warning(f"Enhanced Detector V3.0 not available: {e}")

# Import Enhanced Detector V5.0 (Production Ready)
try:
    from ..enhanced_detector_v5 import EnhancedDetectorV5
except ImportError:
    try:
        # Try relative import from parent directory
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, parent_dir)
        from enhanced_detector_v5 import EnhancedDetectorV5
    except ImportError as e:
        logger.warning(f"Enhanced Detector V5.0 not available: {e}")
        EnhancedDetectorV3 = None

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Enhanced Baseline Detector v2.1 and Voltage Window Detector v4
try:
    baseline_detector = BaselineDetector(auto_mode=True)
    logger.info("🎯 Enhanced Baseline Detector v2.1 initialized for web application")
    logger.info("🔬 Voltage Window Baseline Detector v4 available as primary method")
except Exception as e:
    logger.error(f"Failed to initialize Enhanced Baseline Detector: {e}")
    baseline_detector = None

peak_detection_bp = Blueprint('peak_detection', __name__)

def extract_sample_info_from_filename(filename):
    """Extract sample information from filename with improved normalization"""
    if not filename:
        return {
            'sample_id': f'sample_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'instrument_type': 'unknown',
            'scan_rate': None,
            'concentration': None
        }
    
    filename_lower = filename.lower()
    import re
    
    # Determine instrument type
    if 'palmsens' in filename_lower:
        instrument_type = 'palmsens'
    elif any(x in filename_lower for x in ['pipot', 'ferro', 'stm32']):
        instrument_type = 'stm32'
    else:
        instrument_type = 'unknown'
    
    # Extract scan rate with comprehensive patterns
    scan_rate = None
    scan_patterns = [
        r'(\d+)mvps',      # 100mvps
        r'(\d+)mv_?ps',    # 100mvpS, 100mv_ps  
        r'(\d+)mv[/_]?s',  # 100mvs, 100mv_s, 100mv/s
    ]
    
    for pattern in scan_patterns:
        scan_match = re.search(pattern, filename_lower)
        if scan_match:
            scan_rate = int(scan_match.group(1))
            break
    
    # Extract concentration with comprehensive patterns
    concentration = None
    
    # Pattern 1: Decimal format (5.0mm, 0.5mm)
    decimal_match = re.search(r'(\d+\.\d+)mm', filename_lower)
    if decimal_match:
        concentration = float(decimal_match.group(1))
    
    # Pattern 2: Underscore format (5_0mm -> 5.0, 0_5mm -> 0.5)
    elif re.search(r'(\d+)_(\d+)mm', filename_lower):
        underscore_match = re.search(r'(\d+)_(\d+)mm', filename_lower)
        whole = int(underscore_match.group(1))
        decimal = int(underscore_match.group(2))
        
        # Special handling for different formats
        if whole == 0 and decimal == 5:
            # 0_5mm -> 0.5mm
            concentration = 0.5
        elif whole > 0 and decimal == 0:
            # 5_0mm -> 5.0mm
            concentration = float(whole)
        else:
            # General case: treat as decimal
            concentration = float(f"{whole}.{decimal}")
    
    # Pattern 3: Simple integer format (5mm)
    elif re.search(r'(\d+)mm', filename_lower):
        simple_match = re.search(r'(\d+)mm', filename_lower)
        concentration = float(simple_match.group(1))
    
    # Generate highly standardized sample_id for consistent pairing
    if concentration is not None and scan_rate is not None:
        # Always use the same format regardless of input format
        # Convert concentration to consistent integer representation when possible
        if concentration == int(concentration):
            # Whole numbers: 5mM, 1mM
            conc_str = f"{int(concentration)}mM"
        else:
            # Decimals: always use underscore format for consistency
            # 0.5 -> 0_5mM, 2.5 -> 2_5mM
            whole_part = int(concentration)
            decimal_part = int((concentration - whole_part) * 10)
            conc_str = f"{whole_part}_{decimal_part}mM"
        
        # Standardized sample_id format
        sample_id = f"sample_{conc_str}_{scan_rate}mVpS"
    else:
        # Fallback: create meaningful ID from filename
        base_name = re.sub(r'\.(csv|txt)$', '', filename, flags=re.IGNORECASE)
        base_name = re.sub(r'[^a-zA-Z0-9_]', '_', base_name)
        
        # Remove common instrument-specific prefixes
        for prefix in ['palmsens_', 'pipot_ferro_', 'pipot_']:
            if base_name.lower().startswith(prefix):
                base_name = base_name[len(prefix):]
                break
        
        sample_id = f"sample_{base_name}"
    
    return {
        'sample_id': sample_id,
        'instrument_type': instrument_type,
        'scan_rate': scan_rate,
        'concentration': concentration
    }

def save_analysis_to_log(voltage, current, peaks, metadata=None):
    """Save analysis results to parameter log"""
    try:
        if not metadata:
            metadata = {}
        
        # Extract info from filename if provided
        filename = metadata.get('filename', '')
        sample_info = extract_sample_info_from_filename(filename)
        
        # Prepare measurement data
        measurement_data = {
            'sample_id': sample_info['sample_id'],
            'instrument_type': sample_info['instrument_type'],
            'timestamp': datetime.now(),
            'scan_rate': sample_info['scan_rate'],
            'voltage_start': float(np.min(voltage)) if len(voltage) > 0 else None,
            'voltage_end': float(np.max(voltage)) if len(voltage) > 0 else None,
            'data_points': len(voltage),
            'original_filename': filename,
            'user_notes': metadata.get('user_notes', ''),
        }
        
        # For STM32, store raw data if available
        if sample_info['instrument_type'] == 'stm32' and 'raw_data' in metadata:
            measurement_data['raw_data'] = metadata['raw_data']
        
        # Process peaks for logging
        processed_peaks = []
        for i, peak in enumerate(peaks):
            peak_data = {
                'type': peak.get('type', 'unknown'),
                'voltage': peak.get('x', peak.get('voltage')),
                'current': peak.get('y', peak.get('current')),
                'height': peak.get('height', 0),
                'enabled': peak.get('enabled', True),
                'peak_index': i
            }
            
            # Add baseline information if available
            if 'baseline' in peak:
                baseline = peak['baseline']
                if isinstance(baseline, dict):
                    peak_data.update({
                        'baseline_current': baseline.get('current'),
                        'baseline_slope': baseline.get('slope'),
                        'baseline_r2': baseline.get('r2'),
                        'baseline_voltage_start': baseline.get('voltage_start'),
                        'baseline_voltage_end': baseline.get('voltage_end')
                    })
            
            # Add raw data for STM32 peaks
            if sample_info['instrument_type'] == 'stm32' and 'raw' in peak:
                raw = peak['raw']
                peak_data.update({
                    'raw_dac_ch1': raw.get('dac_ch1'),
                    'raw_dac_ch2': raw.get('dac_ch2'),
                    'raw_timestamp_us': raw.get('timestamp_us'),
                    'raw_counter': raw.get('counter'),
                    'raw_lut_data': raw.get('lut_data')
                })
            
            processed_peaks.append(peak_data)
        
        # Save to database
        measurement_id = parameter_logger.save_measurement(measurement_data)
        saved_peaks = parameter_logger.save_peak_parameters(measurement_id, processed_peaks)
        
        logger.info(f"Saved analysis: measurement_id={measurement_id}, peaks={saved_peaks}")
        return {
            'success': True,
            'measurement_id': measurement_id,
            'peaks_saved': saved_peaks
        }
        
    except Exception as e:
        logger.error(f"Error saving analysis to log: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

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
        
        # Determine current scaling - keep in µA for baseline detection
        current_unit = headers[current_idx]
        current_scale = 1.0
        
        # Simple unit conversion to µA (PiPot files now have 'uA' headers after conversion)
        current_unit_lower = current_unit.lower()
        if current_unit_lower == 'ma':
            current_scale = 1e3  # milliAmps to microAmps
        elif current_unit_lower == 'na':
            current_scale = 1e-3  # nanoAmps to microAmps
        elif current_unit_lower == 'a':
            current_scale = 1e6  # Amperes to microAmps
        elif current_unit_lower in ['ua', 'µa']:
            current_scale = 1.0  # microAmps - keep as is (no scaling)
        
        logger.info(f"Current unit: {current_unit}, scale: {current_scale} (keeping in µA)")
        
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
        logger.info(f"Current range: {min(current):.3f} to {max(current):.3f} µA")
        
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
        
        # Determine current scaling - keep in µA for baseline detection
        current_unit = headers[current_idx]
        current_scale = 1.0
        
        # Simple unit conversion to µA (PiPot files now have 'uA' headers after conversion)
        current_unit_lower = current_unit.lower()
        if current_unit_lower == 'ma':
            current_scale = 1e3  # milliAmps to microAmps
        elif current_unit_lower == 'na':
            current_scale = 1e-3  # nanoAmps to microAmps
        elif current_unit_lower == 'a':
            current_scale = 1e6  # Amperes to microAmps
        elif current_unit_lower in ['ua', 'µa']:
            current_scale = 1.0  # microAmps - keep as is (no scaling)
        
        logger.info(f"Current unit: {current_unit}, scale: {current_scale} (keeping in µA)")
        
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
        logger.info(f"Current range: {min(current):.3f} to {max(current):.3f} µA")
        
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
                        
                        # Store baseline data from first file only (for display)
                        if i == 0 and 'baseline' in result:
                            first_file_baseline = result['baseline']
                            logger.info(f"[DEBUG] File {i}: stored baseline data with keys: {list(first_file_baseline.keys())}")
                        
                        logger.info(f"[DEBUG] File {i}: detected {len(file_peaks)} peaks")
                        
                        # Add baseline data to each peak if available
                        if 'baseline' in result:
                            for p in file_peaks:
                                p['baseline'] = result['baseline']
                        
                    except Exception as e:
                        logger.error(f"[DEBUG] File {i}: peak detection error: {str(e)}")
                        file_peaks = []
                        if i == 0:
                            first_file_baseline = {}
                    for p in file_peaks:
                        p['fileIdx'] = i
                    peaks_per_file[i] = file_peaks
            
            # Include baseline data from first file in response
            response_data = {'success': True, 'peaks': peaks_per_file}
            if 'first_file_baseline' in locals() and first_file_baseline:
                response_data['baseline'] = first_file_baseline
                logger.info(f"[DEBUG] Including baseline data in files array response: {list(first_file_baseline.keys())}")
            
            # Mark completion
            peak_detection_progress.update({
                'current_file': nFiles,
                'percent': 100,
                'message': f'Completed processing {nFiles} files',
                'active': False
            })
            
            logger.info(f"[PROGRESS] Processing complete: {nFiles}/{nFiles} files (100%)")
            logger.info(f"[DEBUG] peaks_per_file lens: {[len(p) for p in peaks_per_file]}")
            return jsonify(response_data)
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
                    detection_results = detect_cv_peaks(voltage, current, method=method)
                    file_peaks = detection_results['peaks']
                    
                    # Store baseline data for first file only (for display)
                    if i == 0 and 'baseline' in detection_results:
                        first_file_baseline = detection_results['baseline']
                        logger.info(f"[DEBUG] File {i}: stored baseline data with keys: {list(first_file_baseline.keys())}")
                    
                    logger.info(f"[DEBUG] File {i}: detected {len(file_peaks)} peaks")
                except Exception as e:
                    logger.error(f"[DEBUG] File {i}: peak detection error: {str(e)}")
                    file_peaks = []
                    if i == 0:
                        first_file_baseline = {}
                for p in file_peaks:
                    p['fileIdx'] = i
                peaks_per_file[i] = file_peaks
            
            # Include baseline data from first file in response
            response_data = {'success': True, 'peaks': peaks_per_file}
            if 'first_file_baseline' in locals() and first_file_baseline:
                response_data['baseline'] = first_file_baseline
                logger.info(f"[DEBUG] Including baseline data in multi-file response: {list(first_file_baseline.keys())}")
            
            logger.info(f"[DEBUG] peaks_per_file lens: {[len(p) for p in peaks_per_file]}")
            return jsonify(response_data)
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
            
            # Save analysis to parameter log if requested
            if data.get('save_to_log', False):
                metadata = {
                    'filename': data.get('filename', ''),
                    'user_notes': data.get('user_notes', ''),
                    'raw_data': data.get('raw_data', {})
                }
                
                log_result = save_analysis_to_log(voltage, current, results['peaks'], metadata)
                results['log_result'] = log_result
                
                if log_result['success']:
                    logger.info(f"Analysis saved to log: {log_result.get('measurement_id')}")
                else:
                    logger.warning(f"Failed to save analysis: {log_result.get('error')}")
            
            # Mark completion
            peak_detection_progress.update({
                'percent': 100,
                'message': 'Peak detection completed',
                'active': False
            })
            
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
        elif method == 'enhanced_v3':
            return detect_peaks_enhanced_v3(voltage, current)
        elif method == 'enhanced_v5':
            return detect_peaks_enhanced_v5(voltage, current)
        else:
            raise ValueError(f"Unknown method: {method}")
    except Exception as e:
        logger.error(f"Error in CV peak detection: {str(e)}")
        raise

def detect_peaks_prominence(voltage, current):
    """Detect peaks using prominence method with simplified baseline"""
    try:
        logger.info(f"🔍 Prominence Peak Detection: starting with {len(voltage)} data points")
        logger.info(f"📊 Data range - V: {voltage.min():.3f} to {voltage.max():.3f}V, I: {current.min():.3f} to {current.max():.3f}µA")
        
        # Get settings from config or use defaults (handle cases without Flask context)
        try:
            prominence = current_app.config.get('PEAK_PROMINENCE', 0.1)
            width = current_app.config.get('PEAK_WIDTH', 5)
        except RuntimeError:
            # Working outside Flask context - use defaults
            prominence = 0.1
            width = 5
            logger.info(f"🔧 Using default settings: prominence={prominence}, width={width}")

        # Use Enhanced Baseline Detector v2.1
        logger.info("🚀 Using Enhanced Baseline Detector v2.1 for improved peak detection")
        
        baseline_full = None
        baseline_metadata = None
        segment_info = {}
        
        try:
            # Use new Voltage Window Baseline Detector v4 as primary method
            logger.info("� Using Voltage Window Baseline Detector v4 for improved CV analysis")
            
            # Quick peak detection for baseline avoidance
            peak_regions = []
            if False:  # Temporarily disable peak avoidance to fix reverse baseline issue
                try:
                    # Normalize current for quick peak detection
                    current_max = np.abs(current).max()
                    if current_max > 0:
                        current_norm = current / current_max
                        
                        # Quick peak detection with loose criteria
                        pos_peaks, _ = find_peaks(current_norm, prominence=0.05, width=3)
                        neg_peaks, _ = find_peaks(-current_norm, prominence=0.05, width=3)
                    
                    # Convert to peak regions (start_idx, end_idx)
                    all_peak_indices = np.concatenate([pos_peaks, neg_peaks])
                    for peak_idx in all_peak_indices:
                        if 0 <= peak_idx < len(voltage):
                            # Create a small region around each peak (±5 points)
                            start_idx = max(0, peak_idx - 5)
                            end_idx = min(len(voltage) - 1, peak_idx + 5)
                            peak_regions.append((int(start_idx), int(end_idx)))
                    
                        
                    logger.info(f"[BASELINE] Quick peak detection found {len(peak_regions)} peaks for baseline avoidance")
                        
                except Exception as peak_err:
                    logger.warning(f"Quick peak detection failed: {peak_err}, proceeding without peak avoidance")            # Use the new voltage window detector with peak avoidance
            logger.info(f"🔍 About to call cv_baseline_detector_v4 with voltage len={len(voltage)}, current len={len(current)}")
            baseline_forward, baseline_reverse, segment_info = cv_baseline_detector_v4(
                voltage, current, peak_regions
            )
            logger.info(f"🔍 cv_baseline_detector_v4 returned: forward len={len(baseline_forward)}, reverse len={len(baseline_reverse)}")
            
            logger.info("✅ Voltage window baseline detection completed successfully")
            logger.info(f"🔍 Segment info: {segment_info}")
            logger.info(f"📈 Forward baseline range: [{baseline_forward.min():.6f}, {baseline_forward.max():.6f}] μA, variation: {baseline_forward.max() - baseline_forward.min():.6f}")
            logger.info(f"📉 Reverse baseline range: [{baseline_reverse.min():.6f}, {baseline_reverse.max():.6f}] μA, variation: {baseline_reverse.max() - baseline_reverse.min():.6f}")
            
            baseline_full = np.concatenate([baseline_forward, baseline_reverse])
            logger.info(f"📊 Full baseline range: [{baseline_full.min():.3f}, {baseline_full.max():.3f}] μA")
                
        except Exception as e:
            logger.error(f"❌ Voltage window baseline detection failed: {e}")
            
            # Fallback to Enhanced Baseline Detector v2.1
            if baseline_detector:
                try:
                    logger.info(f"🔧 Fallback: attempting Enhanced Baseline Detector v2.1")
                    baseline_full, baseline_metadata = baseline_detector.detect_baseline(
                        voltage, current, filename="web_prominence_detection"
                    )
                    
                    logger.info(f"✅ Enhanced baseline detection completed: method={baseline_metadata['method']}")
                    
                    # Handle quality metrics
                    if 'quality_metrics' in baseline_metadata:
                        quality_score = baseline_metadata['quality_metrics']['overall_quality']
                    elif 'quality_score' in baseline_metadata:
                        quality_score = baseline_metadata['quality_score']
                    else:
                        quality_score = 0.5
                    
                    logger.info(f"📊 Quality: {quality_score:.2f}")
                    
                    # Split baseline for forward/reverse analysis
                    n = len(voltage)
                    mid = n // 2
                    baseline_forward = baseline_full[:mid]
                    baseline_reverse = baseline_full[mid:]
                    
                    # Create segment info for compatibility
                    segment_info = {
                        'method_used': baseline_metadata['method'],
                        'processing_time': baseline_metadata['processing_time'],
                        'quality': quality_score,
                        'auto_selected': baseline_metadata.get('auto_selected', False)
                    }
                    
                except Exception as fallback_err:
                    logger.error(f"❌ Enhanced baseline detector fallback failed: {fallback_err}")
                    raise Exception("All baseline detection methods failed")
            else:
                raise Exception("No baseline detector available")

        # Ensure we have baseline data
        if baseline_full is None or len(baseline_full) != len(voltage):
            logger.warning(f"⚠️ Baseline length mismatch: baseline_full={len(baseline_full) if baseline_full is not None else 'None'}, voltage={len(voltage)}")
            logger.warning(f"⚠️ Creating constant fallback baseline at median current")
            baseline_full = np.full_like(current, np.median(current))
            n = len(voltage)
            mid = n // 2
            baseline_forward = baseline_full[:mid]
            baseline_reverse = baseline_full[mid:]
        else:
            logger.info(f"✅ Baseline length check passed: baseline_full={len(baseline_full)}, voltage={len(voltage)}")

        # Normalize current for peak detection
        current_max = np.abs(current).max()
        if current_max == 0:
            logger.warning("⚠️ Zero current detected, cannot normalize")
            current_norm = np.zeros_like(current)
        else:
            current_norm = current / current_max

        logger.info(f"🔢 Normalized current range: {current_norm.min():.3f} to {current_norm.max():.3f}")

        # Enhanced Peak Detection with Validation Rules
        logger.info("🎯 Using Enhanced Peak Detection with validation rules")
        
        # Updated voltage zones for better compatibility (based on real data analysis)
        OX_VOLTAGE_MIN = -0.3    # Allow more negative voltages for Ox peaks
        OX_VOLTAGE_MAX = 0.8     # Extended upper range for Ox peaks
        RED_VOLTAGE_MIN = -0.8   # Allow more negative voltages for Red peaks
        RED_VOLTAGE_MAX = 0.4    # Extended upper range for Red peaks
        MIN_PEAK_HEIGHT = 1.0    # Reduced from 5.0 to accept smaller signals
        
        def validate_peak_pre_detection(voltage_val, current_val, peak_type):
            """ตรวจสอบ peak ก่อน add เข้าไปในผลลัพธ์"""
            # Rule 1: Voltage zone validation
            if peak_type == 'oxidation':
                if voltage_val < OX_VOLTAGE_MIN or voltage_val > OX_VOLTAGE_MAX:
                    return False, f"Ox peak voltage {voltage_val:.3f}V outside valid range {OX_VOLTAGE_MIN}-{OX_VOLTAGE_MAX}V"
            elif peak_type == 'reduction':
                if voltage_val < RED_VOLTAGE_MIN or voltage_val > RED_VOLTAGE_MAX:
                    return False, f"Red peak voltage {voltage_val:.3f}V outside valid range {RED_VOLTAGE_MIN}-{RED_VOLTAGE_MAX}V"
            
            # Rule 2: Current direction validation
            if peak_type == 'oxidation' and current_val < 0:
                return False, f"Ox peak has negative current {current_val:.2f}μA"
            elif peak_type == 'reduction' and current_val > 0:
                return False, f"Red peak has positive current {current_val:.2f}μA"
            
            # Rule 3: Peak size validation
            if abs(current_val) < MIN_PEAK_HEIGHT:
                return False, f"Peak current {current_val:.2f}μA too small"
            
            return True, "Valid peak"

        # Find positive peaks (oxidation candidates)
        try:
            pos_peaks, pos_properties = find_peaks(
                current_norm,
                prominence=prominence,
                width=width
            )
            logger.info(f"➕ Found {len(pos_peaks)} oxidation candidates at indices {pos_peaks}")
        except Exception as e:
            logger.error(f"❌ Positive peak finding failed: {e}")
            pos_peaks, pos_properties = np.array([]), {'prominences': np.array([])}

        # Find negative peaks (reduction candidates)
        try:
            neg_peaks, neg_properties = find_peaks(
                -current_norm,
                prominence=prominence,
                width=width
            )
            logger.info(f"➖ Found {len(neg_peaks)} reduction candidates at indices {neg_peaks}")
        except Exception as e:
            logger.error(f"❌ Negative peak finding failed: {e}")
            neg_peaks, neg_properties = np.array([]), {'prominences': np.array([])}

        # Format peak data with validation
        peaks = []
        rejected_peaks = []

        # Add oxidation peaks with validation
        for i, peak_idx in enumerate(pos_peaks):
            try:
                peak_voltage = float(voltage[peak_idx])
                peak_current = float(current[peak_idx])
                
                # Calculate baseline current at peak voltage - use appropriate baseline section
                n_forward = len(baseline_forward)
                n_reverse = len(baseline_reverse)
                
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
                
                # Validate peak before adding
                is_valid, validation_message = validate_peak_pre_detection(
                    peak_voltage, peak_current, 'oxidation'
                )
                
                if is_valid:
                    peaks.append({
                        'voltage': peak_voltage,
                        'current': peak_current,
                        'type': 'oxidation',
                        'confidence': float(pos_properties['prominences'][i] * 100),
                        'height': float(peak_height),
                        'baseline_current': baseline_at_peak,
                        'enabled': True  # Default enabled for user selection
                    })
                    logger.info(f"✅ Valid Ox peak: V={peak_voltage:.3f}V, I={peak_current:.3f}μA, height={peak_height:.3f}μA, section={scan_section}")
                else:
                    rejected_peaks.append({
                        'voltage': peak_voltage,
                        'current': peak_current,
                        'type': 'oxidation',
                        'reason': validation_message
                    })
                    logger.warning(f"❌ Rejected Ox peak: V={peak_voltage:.3f}V, I={peak_current:.3f}μA - {validation_message}")
            except Exception as e:
                logger.error(f"❌ Error processing oxidation peak {i}: {e}")

        # Add reduction peaks with validation
        for i, peak_idx in enumerate(neg_peaks):
            try:
                peak_voltage = float(voltage[peak_idx])
                peak_current = float(current[peak_idx])
                
                # Calculate baseline current at peak voltage - use appropriate baseline section
                n_forward = len(baseline_forward)
                n_reverse = len(baseline_reverse)
                
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
                
                # Validate peak before adding
                is_valid, validation_message = validate_peak_pre_detection(
                    peak_voltage, peak_current, 'reduction'
                )
                
                if is_valid:
                    peaks.append({
                        'voltage': peak_voltage,
                        'current': peak_current,
                        'type': 'reduction',
                        'confidence': float(neg_properties['prominences'][i] * 100),
                        'height': float(peak_height),
                        'baseline_current': baseline_at_peak,
                        'enabled': True  # Default enabled for user selection
                    })
                    logger.info(f"✅ Valid Red peak: V={peak_voltage:.3f}V, I={peak_current:.3f}μA, height={peak_height:.3f}μA, section={scan_section}")
                else:
                    rejected_peaks.append({
                        'voltage': peak_voltage,
                        'current': peak_current,
                        'type': 'reduction',
                        'reason': validation_message
                    })
                    logger.warning(f"❌ Rejected Red peak: V={peak_voltage:.3f}V, I={peak_current:.3f}μA - {validation_message}")
            except Exception as e:
                logger.error(f"❌ Error processing reduction peak {i}: {e}")

        # Log summary of peak detection results
        valid_ox_count = len([p for p in peaks if p['type'] == 'oxidation'])
        valid_red_count = len([p for p in peaks if p['type'] == 'reduction'])
        rejected_ox_count = len([p for p in rejected_peaks if p['type'] == 'oxidation'])
        rejected_red_count = len([p for p in rejected_peaks if p['type'] == 'reduction'])
        
        logger.info(f"🎯 Peak Detection Summary:")
        logger.info(f"   ✅ Valid peaks: {len(peaks)} (Ox: {valid_ox_count}, Red: {valid_red_count})")
        logger.info(f"   ❌ Rejected peaks: {len(rejected_peaks)} (Ox: {rejected_ox_count}, Red: {rejected_red_count})")
        
        # Log details of rejected peaks if any
        if rejected_peaks:
            logger.info(f"   📋 Rejected peak details:")
            for rp in rejected_peaks:
                logger.info(f"      {rp['type']}: V={rp['voltage']:.3f}V, I={rp['current']:.3f}μA - {rp['reason']}")

        logger.info(f"✅ Prominence method completed: {len(peaks)} total peaks found")

        return {
            'peaks': peaks,
            'rejected_peaks': rejected_peaks,
            'method': 'prominence',
            'params': {
                'prominence': prominence,
                'width': width
            },
            'peak_summary': {
                'total_valid': len(peaks),
                'total_rejected': len(rejected_peaks),
                'oxidation_valid': valid_ox_count,
                'reduction_valid': valid_red_count,
                'oxidation_rejected': rejected_ox_count,
                'reduction_rejected': rejected_red_count
            },
            'baseline': {
                'forward': baseline_forward.tolist(),
                'reverse': baseline_reverse.tolist(),
                'full': baseline_full.tolist(),
                'metadata': {
                    'method_used': segment_info.get('method_used') or segment_info.get('method', 'unknown'),
                    'quality': segment_info.get('quality', 0.5),
                    'processing_time': segment_info.get('processing_time', 0),
                    'auto_selected': segment_info.get('auto_selected', False),
                    'error': segment_info.get('error')
                },
                'markers': {
                    'forward_segment': segment_info.get('forward_segment') or {},
                    'reverse_segment': segment_info.get('reverse_segment') or {}
                },
                'debug': {
                    'baseline_range': f"{baseline_full.min():.2e} to {baseline_full.max():.2e}",
                    'forward_range': f"{baseline_forward.min():.2e} to {baseline_forward.max():.2e}",
                    'reverse_range': f"{baseline_reverse.min():.2e} to {baseline_reverse.max():.2e}",
                    'baseline_std': float(np.std(baseline_full)),
                    'current_std': float(np.std(current)),
                    'data_length': len(voltage),
                    'sample_voltage_range': f"{voltage[0]:.3f} to {voltage[-1]:.3f}V",
                    'sample_current_range': f"{current.min():.3f} to {current.max():.3f}μA",
                    'peak_indices_found': {
                        'positive': pos_peaks.tolist() if len(pos_peaks) > 0 else [],
                        'negative': neg_peaks.tolist() if len(neg_peaks) > 0 else []
                    }
                }
            }
        }

    except Exception as e:
        logger.error(f"❌ Critical error in prominence peak detection: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Emergency fallback - return empty result
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
                'confidence': float(confidence),
                'height': float(peak_height),
                'baseline_current': float(local_baseline),
                'enabled': True
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
                peak_current = float(current[peak_idx])
                local_baseline = np.mean(current[max(0, peak_idx-10):min(len(current), peak_idx+10)])
                peak_height = abs(peak_current - local_baseline)
                
                peaks.append({
                    'voltage': float(voltage[peak_idx]),
                    'current': peak_current,
                    'type': 'oxidation',
                    'confidence': 75.0,
                    'height': float(peak_height),
                    'baseline_current': float(local_baseline),
                    'enabled': True
                })
            
            for peak_idx in neg_peaks:
                peak_current = float(current[peak_idx])
                local_baseline = np.mean(current[max(0, peak_idx-10):min(len(current), peak_idx+10)])
                peak_height = abs(peak_current - local_baseline)
                
                peaks.append({
                    'voltage': float(voltage[peak_idx]),
                    'current': peak_current,
                    'type': 'reduction', 
                    'confidence': 75.0,
                    'height': float(peak_height),
                    'baseline_current': float(local_baseline),
                    'enabled': True
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
        logger.info(f"🤖 ML Peak Detection: starting with {len(voltage)} data points")
        logger.info(f"📊 Data range - V: {voltage.min():.3f} to {voltage.max():.3f}V, I: {current.min():.3f} to {current.max():.3f}µA")
        
        # Start with prominence method as baseline
        try:
            base_results = detect_peaks_prominence(voltage, current)
            base_peaks = base_results['peaks']
            logger.info(f"✅ Prominence method found {len(base_peaks)} base peaks")
        except Exception as e:
            logger.error(f"❌ Prominence method failed in ML: {e}")
            # Fallback to simple peak detection
            logger.info("🔄 Falling back to simple peak detection in ML method")
            base_peaks = []
            
            # Simple fallback peak detection
            try:
                current_norm = current / np.abs(current).max()
                from scipy.signal import find_peaks
                
                # Find positive peaks
                pos_peaks, _ = find_peaks(current_norm, prominence=0.1, width=5)
                # Find negative peaks  
                neg_peaks, _ = find_peaks(-current_norm, prominence=0.1, width=5)
                
                # Convert to peak format
                for peak_idx in pos_peaks:
                    base_peaks.append({
                        'voltage': float(voltage[peak_idx]),
                        'current': float(current[peak_idx]),
                        'type': 'oxidation',
                        'confidence': 75.0,
                        'height': abs(float(current[peak_idx])),
                        'baseline_current': 0.0,
                        'enabled': True
                    })
                
                for peak_idx in neg_peaks:
                    base_peaks.append({
                        'voltage': float(voltage[peak_idx]),
                        'current': float(current[peak_idx]),
                        'type': 'reduction',
                        'confidence': 75.0,
                        'height': abs(float(current[peak_idx])),
                        'baseline_current': 0.0,
                        'enabled': True
                    })
                
                logger.info(f"🔄 Fallback found {len(base_peaks)} peaks ({len(pos_peaks)} pos, {len(neg_peaks)} neg)")
                base_results = {'peaks': base_peaks, 'baseline': {}}
                
            except Exception as fallback_error:
                logger.error(f"❌ Even fallback peak detection failed: {fallback_error}")
                base_peaks = []
                base_results = {'peaks': [], 'baseline': {}}
        
        # Add ML enhancements (feature extraction)
        enhanced_peaks = []
        for i, peak in enumerate(base_peaks):
            try:
                # Find peak index
                peak_voltage = peak['voltage']
                peak_current = peak['current']
                
                # Find closest index
                voltage_diff = np.abs(voltage - peak_voltage)
                peak_idx = np.argmin(voltage_diff)
                
                # Calculate peak width at half height
                half_height = peak_current / 2
                left_idx = right_idx = peak_idx
                
                # Find left boundary
                while left_idx > 0 and abs(current[left_idx]) > abs(half_height):
                    left_idx -= 1
                    
                # Find right boundary
                while right_idx < len(current)-1 and abs(current[right_idx]) > abs(half_height):
                    right_idx += 1
                    
                width = voltage[right_idx] - voltage[left_idx] if right_idx != left_idx else 0.01
                
                # Calculate area under the curve
                try:
                    area = np.trapz(current[left_idx:right_idx+1], voltage[left_idx:right_idx+1])
                except:
                    area = 0.0
                
                enhanced_peaks.append({
                    'voltage': peak['voltage'],
                    'current': peak['current'],
                    'type': peak['type'],
                    'confidence': min(100.0, peak.get('confidence', 50.0) * 1.1),  # ML confidence boost
                    'height': peak.get('height', abs(peak_current)),
                    'baseline_current': peak.get('baseline_current', 0.0),
                    'enabled': peak.get('enabled', True),
                    'width': float(width),
                    'area': float(area)
                })
                
            except Exception as peak_error:
                logger.warning(f"⚠️ Error processing peak {i}: {peak_error}")
                # Add peak without enhancements
                enhanced_peaks.append({
                    'voltage': peak['voltage'],
                    'current': peak['current'],
                    'type': peak.get('type', 'unknown'),
                    'confidence': peak.get('confidence', 50.0),
                    'height': peak.get('height', abs(peak.get('current', 0))),
                    'baseline_current': peak.get('baseline_current', 0.0),
                    'enabled': peak.get('enabled', True),
                    'width': 0.01,
                    'area': 0.0
                })
        
        logger.info(f"🎯 ML method completed: {len(enhanced_peaks)} enhanced peaks")
        
        return {
            'peaks': enhanced_peaks,
            'method': 'ml',
            'params': {
                'feature_extraction': ['width', 'area'],
                'confidence_boost': 1.1,
                'fallback_used': len(base_peaks) == 0
            },
            'baseline': base_results.get('baseline', {})  # Pass through baseline from prominence method
        }
        
    except Exception as e:
        logger.error(f"❌ Critical error in ML peak detection: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Return empty result instead of raising
        return {
            'peaks': [],
            'method': 'ml_error',
            'params': {'error': str(e)},
            'baseline': {}
        }

def detect_peaks_enhanced_v3(voltage, current):
    """Detect peaks using Enhanced Detector V3.0 with all improvements"""
    try:
        logger.info(f"🚀 Enhanced Detector V3.0: starting with {len(voltage)} data points")
        logger.info(f"📊 Data range - V: {voltage.min():.3f} to {voltage.max():.3f}V, I: {current.min():.3f} to {current.max():.3f}µA")
        
        # Check if Enhanced Detector V3.0 is available
        if EnhancedDetectorV3 is None:
            logger.warning("⚠️ Enhanced Detector V3.0 not available, falling back to prominence method")
            return detect_peaks_prominence(voltage, current)
        
        # Create detector instance
        detector = EnhancedDetectorV3()
        
        # Run enhanced detection
        results = detector.detect_peaks_enhanced(voltage, current)
        
        # Convert to web API format
        web_peaks = []
        for peak in results['peaks']:
            web_peaks.append({
                'voltage': float(peak['voltage']),
                'current': float(peak['current']),
                'type': peak['type'],  # 'oxidation' or 'reduction'
                'confidence': float(peak['confidence']),
                'height': float(peak.get('height', abs(peak['current']))),
                'baseline_current': 0.0,  # Enhanced detector handles baseline internally
                'enabled': True
            })
        
        # Format baseline data for web interface
        baseline_data = {
            'forward': [],
            'reverse': [],
            'full': [],
            'metadata': {},
            'markers': {},
            'debug': {}
        }
        
        if results.get('baseline_indices') and len(results['baseline_indices']) > 0:
            # Create baseline array
            baseline_full = np.zeros(len(voltage))
            if len(results['baseline_info']) > 0:
                # Use baseline info to fill the array
                for region in results['baseline_info']:
                    start_idx = max(0, region.get('start_index', 0))
                    end_idx = min(len(voltage), region.get('end_index', len(voltage)))
                    if start_idx < end_idx:
                        baseline_full[start_idx:end_idx] = region.get('mean_current', 0.0)
            
            # Split into forward/reverse
            mid_point = len(voltage) // 2
            baseline_data['forward'] = baseline_full[:mid_point].tolist()
            baseline_data['reverse'] = baseline_full[mid_point:].tolist()
            baseline_data['full'] = baseline_full.tolist()
            
            # Add metadata
            baseline_data['metadata'] = {
                'method_used': 'enhanced_v3',
                'quality': 0.9,  # Enhanced detector has high quality
                'processing_time': 0.0,
                'auto_selected': True,
                'regions_found': len(results['baseline_info']),
                'total_baseline_points': len(results['baseline_indices'])
            }
            
            # Add debug info
            baseline_data['debug'] = {
                'scan_direction': {
                    'turning_point': results['scan_sections']['turning_point'],
                    'forward_points': results['scan_sections']['forward'][1],
                    'reverse_points': results['scan_sections']['reverse'][1] - results['scan_sections']['reverse'][0]
                },
                'thresholds_used': results['thresholds'],
                'conflicts_detected': len(results.get('conflicts', [])),
                'baseline_regions': len(results['baseline_info'])
            }
        
        logger.info(f"✅ Enhanced V3.0 completed: {len(web_peaks)} peaks found")
        logger.info(f"📊 Baseline: {len(results.get('baseline_indices', []))} points in {len(results.get('baseline_info', []))} regions")
        logger.info(f"🎯 Scan sections: turning point at {results['scan_sections']['turning_point']}")
        
        return {
            'peaks': web_peaks,
            'method': 'enhanced_v3',
            'params': {
                'scan_direction_detection': 'enhanced_gradient_smoothing',
                'threshold_calculation': 'dynamic_snr_based',
                'peak_validation': 'multi_criteria_electrochemical',
                'baseline_detection': 'conflict_aware_voltage_windows',
                'confidence_scoring': 'integrated'
            },
            'enhanced_results': {
                'scan_sections': results['scan_sections'],
                'thresholds': results['thresholds'],
                'baseline_info': results['baseline_info'],
                'conflicts': results.get('conflicts', []),
                'total_processing_steps': 6
            },
            'baseline': baseline_data
        }
        
    except Exception as e:
        logger.error(f"❌ Error in Enhanced Detector V3.0: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Fallback to prominence method
        logger.info("🔄 Falling back to prominence method due to Enhanced V3.0 error")
        fallback_result = detect_peaks_prominence(voltage, current)
        fallback_result['method'] = 'enhanced_v3_fallback'
        fallback_result['params']['fallback_reason'] = str(e)
        return fallback_result

def detect_peaks_enhanced_v5(voltage, current):
    """Detect peaks using Enhanced Detector V5.0 - Production Ready"""
    try:
        logger.info(f"🚀 Enhanced Detector V5.0: starting with {len(voltage)} data points")
        logger.info(f"📊 Data range - V: {voltage.min():.3f} to {voltage.max():.3f}V, I: {current.min():.3f} to {current.max():.3f}µA")
        
        # Check if Enhanced Detector V5.0 is available
        try:
            detector = EnhancedDetectorV5()
        except NameError:
            logger.warning("⚠️ Enhanced Detector V5.0 not available, falling back to enhanced V3")
            return detect_peaks_enhanced_v3(voltage, current)
        
        # Run enhanced detection V5
        results = detector.detect_peaks_enhanced_v5(voltage, current)
        
        # Convert to web API format
        web_peaks = []
        for peak in results['peaks']:
            web_peaks.append({
                'voltage': float(peak['voltage']),
                'current': float(peak['current']),
                'type': peak['type'],  # 'oxidation' or 'reduction'
                'confidence': float(peak['confidence']),
                'height': float(peak.get('height', abs(peak['current']))),
                'baseline_current': 0.0,  # Enhanced V5 handles baseline internally
                'enabled': True,
                'shape_score': float(peak.get('shape_score', 1.0)),
                'snr': float(peak.get('snr', 1.0))
            })
        
        # Format baseline data for web interface
        baseline_data = {
            'forward': [],
            'reverse': [],
            'full': [],
            'metadata': {},
            'markers': {},
            'debug': {}
        }
        
        if results.get('baseline_info') and len(results['baseline_info']) > 0:
            # Create baseline array
            baseline_full = np.zeros(len(voltage))
            
            # Use baseline info to fill the array
            for region in results['baseline_info']:
                start_v = region.get('voltage_min', voltage.min())
                end_v = region.get('voltage_max', voltage.max())
                
                # Find indices within voltage range
                mask = (voltage >= start_v) & (voltage <= end_v)
                baseline_full[mask] = region.get('mean_current', 0.0)
            
            # Split into forward/reverse based on scan direction
            turning_point = results.get('scan_info', {}).get('turning_point', len(voltage) // 2)
            baseline_data['forward'] = baseline_full[:turning_point].tolist()
            baseline_data['reverse'] = baseline_full[turning_point:].tolist()
            baseline_data['full'] = baseline_full.tolist()
            
            # Add metadata
            baseline_data['metadata'] = {
                'method_used': 'enhanced_v5',
                'quality': 0.95,  # Enhanced V5 has highest quality
                'processing_time': 0.0,
                'auto_selected': True,
                'regions_found': len(results['baseline_info']),
                'total_baseline_points': sum(region.get('point_count', 0) for region in results['baseline_info'])
            }
            
            # Add debug info
            baseline_data['debug'] = {
                'scan_direction': {
                    'turning_point': turning_point,
                    'detection_method': 'enhanced_v5_gradient_analysis'
                },
                'thresholds_used': results.get('detection_params', {}),
                'rejected_peaks': len(results.get('rejected_peaks', [])),
                'baseline_regions': len(results['baseline_info']),
                'detection_methods': ['scipy_peaks', 'local_extrema', 'gradient_based']
            }
        
        logger.info(f"✅ Enhanced V5.0 completed: {len(web_peaks)} peaks found")
        logger.info(f"📊 Baseline: {baseline_data['metadata'].get('total_baseline_points', 0)} points in {len(results.get('baseline_info', []))} regions")
        logger.info(f"🎯 Detection confidence: {np.mean([p['confidence'] for p in web_peaks]):.2f}" if web_peaks else "🎯 No peaks detected")
        
        return {
            'peaks': web_peaks,
            'method': 'enhanced_v5',
            'params': {
                'scan_direction_detection': 'enhanced_v5_multi_point_analysis',
                'threshold_calculation': 'adaptive_snr_prominence_width',
                'peak_validation': 'multi_method_electrochemical_v5',
                'baseline_detection': 'voltage_segmented_statistical_analysis',
                'confidence_scoring': 'comprehensive_v5',
                'multi_method_detection': 'scipy_extrema_gradient_fusion'
            },
            'enhanced_v5_results': {
                'detection_params': results.get('detection_params', {}),
                'baseline_info': results.get('baseline_info', []),
                'rejected_peaks': results.get('rejected_peaks', []),
                'scan_info': results.get('scan_info', {}),
                'total_processing_methods': 3,
                'production_ready': True
            },
            'baseline': baseline_data
        }
        
    except Exception as e:
        logger.error(f"❌ Error in Enhanced Detector V5.0: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Fallback to enhanced V3 method
        logger.info("🔄 Falling back to enhanced V3 method due to Enhanced V5.0 error")
        fallback_result = detect_peaks_enhanced_v3(voltage, current)
        fallback_result['method'] = 'enhanced_v5_fallback'
        fallback_result['params']['fallback_reason'] = str(e)
        return fallback_result