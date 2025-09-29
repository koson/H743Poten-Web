"""
Voltage Window-Based Baseline Detector
=====================================

Algorithm:
1. Create voltage windows (e.g., 9 points, 50mV apart)
2. Scan each window for segments, record slope and R²
3. Sort by slope (prefer flat segments)
4. Score by slope flatness + R² quality + segment count bonus
5. Select best segments for forward/reverse baseline

Author: AI Assistant
Date: August 26, 2025
"""

import numpy as np
import logging
from scipy import stats
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

def voltage_window_baseline_detector(voltage: np.ndarray, current: np.ndarray, 
                                   peak_regions: List[Tuple[int, int]] = None) -> Tuple[np.ndarray, np.ndarray, Dict]:
    """
    Voltage window-based baseline detection
    
    Args:
        voltage: Voltage array
        current: Current array
        peak_regions: List of (start_idx, end_idx) for detected peaks
        
    Returns:
        forward_baseline, reverse_baseline, info_dict
    """
    try:
        logger.info("🔍 Starting Voltage Window-Based Baseline Detection")
        
        n = len(voltage)
        mid = n // 2
        
        if peak_regions is None:
            peak_regions = []
            
        # Parameters - Make adaptive to voltage range
        v_min, v_max = voltage.min(), voltage.max()
        v_range = v_max - v_min
        
        # Adaptive window sizing based on voltage range
        n_windows = 15  # Target number of windows
        window_voltage_span = v_range / n_windows  # Adaptive window size
        
        # Ensure reasonable window size limits
        min_window_span = 0.02  # 20mV minimum
        max_window_span = 0.15  # 150mV maximum  
        window_voltage_span = max(min_window_span, min(max_window_span, window_voltage_span))
        
        # Adjust parameters for smaller windows
        min_points_per_window = 5   # Reduced from 7
        max_points_per_window = 25  # Increased from 15
        
        logger.info(f"📊 Data: {n} points, voltage range: {v_min:.3f}V to {v_max:.3f}V ({v_range*1000:.0f}mV)")
        logger.info(f"🪟 Adaptive window: {window_voltage_span*1000:.1f}mV ({n_windows} target windows)")
        logger.info(f"🪟 Window points: {min_points_per_window}-{max_points_per_window}")
        
        # Step 1: Create voltage windows and scan for segments
        forward_segments = scan_voltage_windows(voltage[:mid], current[:mid], 0, 
                                              window_voltage_span, min_points_per_window, 
                                              max_points_per_window, peak_regions)
        
        reverse_segments = scan_voltage_windows(voltage[mid:], current[mid:], mid,
                                              window_voltage_span, min_points_per_window,
                                              max_points_per_window, peak_regions)
        
        logger.info(f"📋 Found {len(forward_segments)} forward segments, {len(reverse_segments)} reverse segments")
        
        # Debug segment quality distribution
        if forward_segments:
            forward_r2_dist = [s['r2'] for s in forward_segments]
            forward_slope_dist = [abs(s['slope']) for s in forward_segments]
            logger.info(f"📊 Forward segments - R² range: {min(forward_r2_dist):.3f}-{max(forward_r2_dist):.3f}, "
                       f"slope range: {min(forward_slope_dist):.2e}-{max(forward_slope_dist):.2e}")
        
        if reverse_segments:
            reverse_r2_dist = [s['r2'] for s in reverse_segments]
            reverse_slope_dist = [abs(s['slope']) for s in reverse_segments]
            logger.info(f"📊 Reverse segments - R² range: {min(reverse_r2_dist):.3f}-{max(reverse_r2_dist):.3f}, "
                       f"slope range: {min(reverse_slope_dist):.2e}-{max(reverse_slope_dist):.2e}")
        
        # Step 2: Score and select best segments
        best_forward = select_best_segments(forward_segments, "forward")
        best_reverse = select_best_segments(reverse_segments, "reverse")
        
        # Step 3: Generate baseline
        baseline_forward = np.zeros(mid)
        baseline_reverse = np.zeros(n - mid)
        
        forward_info = None
        reverse_info = None
        
        if best_forward:
            baseline_forward = generate_baseline_from_segments(voltage[:mid], best_forward)
            forward_info = combine_segment_info(best_forward, "forward")
            logger.info(f"✅ Forward baseline: {len(best_forward)} segments, avg R²={np.mean([s['r2'] for s in best_forward]):.3f}")
        else:
            logger.warning("⚠️ No suitable forward segments found")
            
        if best_reverse:
            baseline_reverse = generate_baseline_from_segments(voltage[mid:], best_reverse)
            reverse_info = combine_segment_info(best_reverse, "reverse")
            logger.info(f"✅ Reverse baseline: {len(best_reverse)} segments, avg R²={np.mean([s['r2'] for s in best_reverse]):.3f}")
        else:
            logger.warning("⚠️ No suitable reverse segments found")
            
        return baseline_forward, baseline_reverse, {
            'forward_segment': forward_info,
            'reverse_segment': reverse_info,
            'forward_segments_count': int(len(best_forward) if best_forward else 0),
            'reverse_segments_count': int(len(best_reverse) if best_reverse else 0),
            'excluded_peaks': int(len(peak_regions)),
            'peak_regions': [(int(start), int(end)) for start, end in peak_regions] if peak_regions else []
        }
        
    except Exception as e:
        logger.error(f"❌ Error in voltage window baseline detection: {e}")
        # Safe fallback
        n = len(voltage)
        mid = n // 2
        return np.zeros(mid), np.zeros(n - mid), {'error': str(e)}


def scan_voltage_windows(voltage: np.ndarray, current: np.ndarray, offset: int,
                        window_span: float, min_points: int, max_points: int,
                        peak_regions: List[Tuple[int, int]]) -> List[Dict]:
    """
    Scan voltage range with adaptive sliding windows to find stable segments
    """
    segments = []
    v_min, v_max = voltage.min(), voltage.max()
    
    # Create voltage windows with smaller steps for better coverage
    step_size = window_span * 0.3  # 30% step (more overlap)
    current_v = v_min
    window_count = 0
    
    logger.info(f"🔍 Scanning voltage range {v_min:.3f}V to {v_max:.3f}V")
    logger.info(f"🪟 Window: {window_span*1000:.1f}mV, step: {step_size*1000:.1f}mV")
    
    while current_v <= v_max - window_span:
        window_end = current_v + window_span
        
        # Find indices for this voltage window - more inclusive
        mask = (voltage >= current_v - 0.001) & (voltage <= window_end + 0.001)  # Small tolerance
        indices = np.where(mask)[0]
        
        if len(indices) >= min_points:
            # Trim to max_points if too many (take from middle for stability)
            if len(indices) > max_points:
                start_trim = (len(indices) - max_points) // 2
                indices = indices[start_trim:start_trim + max_points]
            
            # Check if window overlaps with peak regions
            global_start = indices[0] + offset
            global_end = indices[-1] + offset
            
            overlaps_peak = any(
                not (global_end < peak_start or global_start > peak_end)
                for peak_start, peak_end in peak_regions
            )
            
            if not overlaps_peak:
                # Analyze this window
                window_v = voltage[indices]
                window_i = current[indices]
                
                segment = analyze_window_segment(window_v, window_i, indices, offset, window_count)
                if segment:
                    segments.append(segment)
                    logger.debug(f"✅ Window {window_count}: Found segment at V=[{current_v:.3f}:{window_end:.3f}]")
                else:
                    logger.debug(f"❌ Window {window_count}: No valid segment at V=[{current_v:.3f}:{window_end:.3f}]")
            else:
                logger.debug(f"🚫 Window {window_count}: Overlaps peak region at V=[{current_v:.3f}:{window_end:.3f}]")
                    
        else:
            logger.debug(f"📊 Window {window_count}: Only {len(indices)} points (need {min_points}+)")
            
        current_v += step_size
        window_count += 1
        
    logger.info(f"🔍 Scanned {window_count} windows, found {len(segments)} valid segments")
    return segments


def analyze_window_segment(voltage: np.ndarray, current: np.ndarray, 
                          local_indices: np.ndarray, offset: int, window_id: int) -> Optional[Dict]:
    """
    Analyze a voltage window to extract segment properties
    """
    try:
        if len(voltage) < 3:
            return None
            
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(voltage, current)
        r2 = r_value ** 2
        
        # Calculate stability metrics
        current_std = np.std(current)
        current_range = np.max(current) - np.min(current)
        
        # Quality thresholds - Very lenient for real CV data with strong electrochemical response
        min_r2 = 0.5            # Reduced from 0.6
        max_slope = 100.0       # Increased significantly from 25.0 µA/V  
        max_std_ratio = 0.5     # Very high tolerance from 0.08 (50% of local current range)
        
        if current_range > 0:
            std_ratio = current_std / current_range
        else:
            std_ratio = 0
            
        # Check quality with very lenient criteria
        quality_pass = r2 >= min_r2 and abs(slope) <= max_slope and std_ratio <= max_std_ratio
        
        logger.debug(f"🔍 Window {window_id}: V=[{voltage[0]:.3f}:{voltage[-1]:.3f}], "
                    f"points={len(voltage)}, slope={slope:.2e}, R²={r2:.3f}, "
                    f"stability={std_ratio:.3f}, pass={quality_pass}")
        
        if quality_pass:
            segment = {
                'start_idx': int(local_indices[0] + offset),
                'end_idx': int(local_indices[-1] + offset),
                'slope': float(slope),
                'intercept': float(intercept),
                'r2': float(r2),
                'p_value': float(p_value),
                'std_err': float(std_err),
                'length': int(len(voltage)),
                'voltage_start': float(voltage[0]),
                'voltage_end': float(voltage[-1]),
                'voltage_center': float(np.mean(voltage)),
                'current_mean': float(np.mean(current)),  # Add current mean
                'current_std': float(current_std),
                'current_range': float(current_range),
                'stability_ratio': float(std_ratio),
                'window_id': int(window_id),
                'local_indices': [int(idx) for idx in local_indices]
            }
            
            logger.info(f"✅ Window {window_id}: ACCEPTED V=[{voltage[0]:.3f}:{voltage[-1]:.3f}], "
                       f"slope={slope:.2e}, R²={r2:.3f}, stability={std_ratio:.3f}")
            return segment
        else:
            logger.debug(f"❌ Window {window_id} rejected: R²={r2:.3f} (need ≥{min_r2}), "
                        f"slope={slope:.2e} (need ≤{max_slope}), stability={std_ratio:.3f} (need ≤{max_std_ratio})")
            return None
            
    except Exception as e:
        logger.warning(f"Failed to analyze window {window_id}: {e}")
        return None


def select_best_segments(segments: List[Dict], direction: str) -> List[Dict]:
    """
    Select best segments using slope sorting and multi-criteria scoring with position preference
    """
    if not segments:
        logger.warning(f"⚠️ No {direction} segments provided for selection")
        return []
        
    logger.info(f"🎯 Selecting best {direction} segments from {len(segments)} candidates")
    
    # Log input segment quality
    slopes = [abs(s['slope']) for s in segments]
    r2_values = [s['r2'] for s in segments]
    voltages = [s['voltage_start'] for s in segments]
    logger.info(f"📊 Input segments - slopes: {min(slopes):.2e} to {max(slopes):.2e}, "
               f"R²: {min(r2_values):.3f} to {max(r2_values):.3f}")
    logger.info(f"📊 Voltage range: {min(voltages):.3f}V to {max(voltages):.3f}V")

    # Filter segments based on position preference for CV baseline detection
    if direction == "forward":
        # For forward sweep, prefer segments in the initial flat region (before main peak)
        # Look for baseline in the early part of forward sweep
        preferred_segments = [s for s in segments if s['voltage_start'] <= 0.0]  # Before peaks start
        if preferred_segments:
            segments = preferred_segments
            logger.info(f"🎯 Forward position filter: {len(segments)} segments in preferred region (V ≤ 0.0V)")
        else:
            # Fallback: use segments in the first 30% of forward sweep
            forward_third = len(segments) // 3
            segments = segments[:forward_third] if len(segments) > 3 else segments
            logger.warning(f"⚠️ No forward segments in preferred region, using first {len(segments)} segments")
    
    elif direction == "reverse":
        # For reverse sweep, prefer segments in the final flat region (after peaks end)
        # But avoid segments that are clearly after peak regions
        # Look for baseline in the later part but avoid post-peak distortions
        preferred_segments = [s for s in segments if s['voltage_end'] >= 0.1 and s['voltage_start'] <= 0.5]  # Mid-to-late reverse
        if preferred_segments:
            segments = preferred_segments
            logger.info(f"🎯 Reverse position filter: {len(segments)} segments in preferred region (0.1V ≤ V ≤ 0.5V)")
        else:
            # Fallback: use segments in the last 30% of reverse sweep
            reverse_third = len(segments) // 3
            segments = segments[-reverse_third:] if len(segments) > 3 else segments
            logger.warning(f"⚠️ No reverse segments in preferred region, using last {len(segments)} segments")
    
    # Step 1: Sort by slope (prefer flat segments)
    segments_by_slope = sorted(segments, key=lambda x: abs(x['slope']))
    
    # Step 2: Group segments with similar slopes
    slope_tolerance = 2.0  # Increased tolerance (µA/V)
    slope_groups = []
    current_group = [segments_by_slope[0]]
    
    for seg in segments_by_slope[1:]:
        if abs(seg['slope'] - current_group[0]['slope']) <= slope_tolerance:
            current_group.append(seg)
        else:
            slope_groups.append(current_group)
            current_group = [seg]
    slope_groups.append(current_group)
    
    logger.info(f"📊 Grouped {len(segments)} segments into {len(slope_groups)} slope groups")
    
    # Step 3: Score each group with strict length filtering
    scored_groups = []
    MAX_TOTAL_LENGTH = 200  # Maximum total length allowed for any group
    
    for i, group in enumerate(slope_groups):
        total_length = sum([s['length'] for s in group])
        
        # Skip groups that are too long
        if total_length > MAX_TOTAL_LENGTH:
            avg_slope = np.mean([s['slope'] for s in group])
            logger.info(f"📊 Group {i+1}: REJECTED - too long ({total_length} > {MAX_TOTAL_LENGTH}), "
                       f"avg slope={avg_slope:.2e}")
            continue
            
        group_score = score_segment_group(group)
        scored_groups.append((group_score, group))
        
        avg_slope = np.mean([s['slope'] for s in group])
        avg_r2 = np.mean([s['r2'] for s in group])
        logger.info(f"📊 Group {i+1}: {len(group)} segments, total_length={total_length}, avg slope={avg_slope:.2e}, "
                   f"avg R²={avg_r2:.3f}, score={group_score:.3f}")
    
    # Sort by score (highest first)
    scored_groups.sort(key=lambda x: x[0], reverse=True)
    
    if scored_groups:
        best_score, best_group = scored_groups[0]
        logger.info(f"🏆 Selected {direction} group: {len(best_group)} segments, score={best_score:.3f}")
        return best_group
    else:
        logger.warning(f"⚠️ No suitable {direction} segment groups found")
        return []


def score_segment_group(segments: List[Dict]) -> float:
    """
    Score a group of segments with similar slopes - Improved scoring with length constraints
    """
    if not segments:
        return 0.0
        
    # Basic metrics
    avg_slope = np.mean([abs(s['slope']) for s in segments])
    avg_r2 = np.mean([s['r2'] for s in segments])
    avg_stability = np.mean([s['stability_ratio'] for s in segments])
    segment_count = len(segments)
    total_length = sum([s['length'] for s in segments])
    
    # Voltage span coverage
    voltage_span = 0
    if segments:
        voltages = []
        for s in segments:
            voltages.extend([s['voltage_start'], s['voltage_end']])
        voltage_span = max(voltages) - min(voltages)
    
    # Enhanced scoring components
    slope_score = 1.0 / (1.0 + avg_slope * 0.5)  # Prefer flatter slopes (less penalty)
    r2_score = (avg_r2 ** 1.5) * 2.0  # Strong preference for high R² 
    stability_score = 1.0 / (1.0 + avg_stability * 8)  # Prefer stable current (less penalty)
    
    # Strict length constraints - heavily penalize long segments
    MAX_REASONABLE_LENGTH = 25  # Reduced from 50 to 25 points
    length_penalty = 1.0
    if total_length > MAX_REASONABLE_LENGTH:
        # Apply severe exponential penalty for excessive length
        excess_factor = total_length / MAX_REASONABLE_LENGTH
        length_penalty = 1.0 / (excess_factor ** 3)  # Cubic penalty (more severe)
    
    # Further reduced bonuses to prioritize quality over quantity
    length_bonus = min(1.2, 1.0 + total_length / 100.0)  # Much smaller length bonus
    span_bonus = min(1.1, 1.0 + voltage_span / 1.0)  # Smaller span bonus
    count_bonus = min(1.2, 1.0 + segment_count * 0.1)  # Smaller count bonus
    
    # Quality threshold bonus - extra points for exceeding minimum requirements
    quality_bonus = 1.0
    if avg_r2 > 0.85:
        quality_bonus += 0.3  # Reduced from 0.5
    if avg_stability < 0.02:
        quality_bonus += 0.2  # Reduced from 0.3
    if avg_slope < 5.0:
        quality_bonus += 0.1  # Reduced from 0.2
    
    # Apply length penalty to final score
    final_score = slope_score * r2_score * stability_score * length_bonus * span_bonus * count_bonus * quality_bonus * length_penalty
    
    return final_score


def generate_baseline_from_segments(voltage: np.ndarray, segments: List[Dict]) -> np.ndarray:
    """
    Generate baseline from selected segments
    """
    baseline = np.zeros_like(voltage)
    
    if not segments:
        return baseline
        
    # Calculate representative current values from segments
    # Use the mean current from each segment, weighted by quality and length
    segment_currents = []
    weights = []
    
    for seg in segments:
        # Extract the current values from the segment's voltage range
        start_idx = seg['start_idx']
        end_idx = seg['end_idx']
        
        # Get the original current data for this segment if available
        if 'current_mean' in seg:
            current_mean = seg['current_mean']
        else:
            # Calculate from slope and intercept at segment center
            voltage_center = (seg['voltage_start'] + seg['voltage_end']) / 2
            current_mean = seg['slope'] * voltage_center + seg['intercept']
        
        segment_currents.append(current_mean)
        weights.append(seg['r2'] * seg['length'])  # Weight by quality and length
    
    if segment_currents:
        weights = np.array(weights)
        weights = weights / weights.sum()
        
        # Calculate weighted average current
        avg_current = sum(curr * w for curr, w in zip(segment_currents, weights))
        
        # For CV data, create a gentle slope across the voltage range
        # but constrain it to be close to the measured current values
        voltage_range = voltage.max() - voltage.min()
        current_variation = abs(max(segment_currents) - min(segment_currents))
        
        if len(segments) > 1 and current_variation > 0.1 and voltage_range > 0.1:
            # Create gentle slope between segment extremes
            min_current = min(segment_currents)
            max_current = max(segment_currents)
            
            # Normalize voltage to 0-1 range
            voltage_norm = (voltage - voltage.min()) / voltage_range
            
            # Create baseline with gentle variation
            baseline = min_current + (max_current - min_current) * voltage_norm
        else:
            # Use constant baseline at average current
            baseline = np.full_like(voltage, avg_current)
    
    return baseline


def combine_segment_info(segments: List[Dict], direction: str) -> Dict:
    """
    Combine multiple segments into single info for frontend
    """
    if not segments:
        return None
        
    # Use the best segment as representative
    best_seg = max(segments, key=lambda x: x['r2'])
    
    # Calculate combined metrics
    total_length = sum(s['length'] for s in segments)
    avg_r2 = np.mean([s['r2'] for s in segments])
    avg_slope = np.mean([s['slope'] for s in segments])
    min_start = min(s['start_idx'] for s in segments)
    max_end = max(s['end_idx'] for s in segments)
    
    return {
        'start_idx': min_start,
        'end_idx': max_end,
        'slope': avg_slope,
        'intercept': best_seg['intercept'],  # Use best segment's intercept
        'r2': avg_r2,
        'p_value': best_seg['p_value'],
        'std_err': best_seg['std_err'],
        'length': total_length,
        'voltage_start': best_seg['voltage_start'],
        'voltage_end': best_seg['voltage_end'],
        'segment_count': len(segments)
    }
