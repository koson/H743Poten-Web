#!/usr/bin/env python3
"""
Improved 2-Step Baseline Detection Algorithm

Step 1: Find all linear segments that could be baseline candidates
Step 2: Select the best segments as forward/reverse baselines
"""
import numpy as np
from scipy import signal
from scipy.stats import linregress
import logging

logger = logging.getLogger(__name__)

def detect_linear_segments(voltage, current, min_length=5, r2_threshold=0.95):
    """
    Step 1: Find all linear segments in CV data
    
    Args:
        voltage: array of voltage values
        current: array of current values  
        min_length: minimum points for a segment to be considered
        r2_threshold: minimum R² for linearity
    
    Returns:
        List of segments: [{'start_idx', 'end_idx', 'slope', 'r2', 'voltage_range', 'current_range'}]
    """
    segments = []
    n = len(voltage)
    
    # Sliding window approach to find linear regions
    for start in range(n - min_length + 1):
        for length in range(min_length, min(50, n - start + 1)):  # Max segment length = 50
            end = start + length - 1
            
            if end >= n:
                break
                
            # Extract segment
            v_seg = voltage[start:end+1]
            i_seg = current[start:end+1]
            
            # Skip if segment has NaN or Inf
            if not (np.all(np.isfinite(v_seg)) and np.all(np.isfinite(i_seg))):
                continue
                
            # Check if voltage span is meaningful (at least 20mV)
            voltage_span = v_seg[-1] - v_seg[0]
            if abs(voltage_span) < 0.02:
                continue
            
            # Linear regression
            try:
                slope, intercept, r_value, p_value, std_err = linregress(v_seg, i_seg)
                r2 = r_value ** 2
                
                # Check linearity threshold
                if r2 >= r2_threshold:
                    segments.append({
                        'start_idx': start,
                        'end_idx': end,
                        'length': length,
                        'slope': slope,
                        'intercept': intercept,
                        'r2': r2,
                        'voltage_range': (v_seg[0], v_seg[-1]),
                        'current_range': (i_seg[0], i_seg[-1]),
                        'voltage_span': voltage_span,
                        'mean_current': np.mean(i_seg),
                        'std_current': np.std(i_seg)
                    })
            except Exception as e:
                logger.debug(f"Linear regression failed for segment {start}:{end}: {e}")
                continue
    
    # Remove overlapping segments (keep the longer/better ones)
    segments = remove_overlapping_segments(segments)
    
    logger.info(f"Found {len(segments)} linear segments")
    return segments

def remove_overlapping_segments(segments):
    """Remove significantly overlapping segments, keeping the better ones"""
    if not segments:
        return segments
    
    # Sort by R² descending (better fits first)
    segments = sorted(segments, key=lambda x: x['r2'], reverse=True)
    
    filtered = []
    for segment in segments:
        # Check if this segment significantly overlaps with any already selected
        is_overlapping = False
        for selected in filtered:
            overlap_start = max(segment['start_idx'], selected['start_idx'])
            overlap_end = min(segment['end_idx'], selected['end_idx'])
            overlap_length = max(0, overlap_end - overlap_start + 1)
            
            segment_length = segment['end_idx'] - segment['start_idx'] + 1
            overlap_ratio = overlap_length / segment_length
            
            # If more than 60% overlap, consider it overlapping
            if overlap_ratio > 0.6:
                is_overlapping = True
                break
        
        if not is_overlapping:
            filtered.append(segment)
    
    return filtered

def select_baseline_segments(segments, voltage, current):
    """
    Step 2: Select the best segments for forward and reverse baselines
    
    Strategy:
    - Separate data into forward (decreasing voltage) and reverse (increasing voltage) scans
    - For each scan direction, find segments that are likely baseline (low slope, consistent current)
    - Prioritize segments that are longer and have better linearity
    """
    
    # Find the turning point (minimum voltage typically)
    min_voltage_idx = np.argmin(voltage)
    logger.info(f"[BASELINE] Turning point at index {min_voltage_idx}, voltage {voltage[min_voltage_idx]:.3f}V")
    
    # Split into forward and reverse scans
    forward_segments = [s for s in segments if s['end_idx'] <= min_voltage_idx + 5]  # Allow some overlap
    reverse_segments = [s for s in segments if s['start_idx'] >= min_voltage_idx - 5]  # Allow some overlap
    
    logger.info(f"[BASELINE] Forward segments: {len(forward_segments)}, Reverse segments: {len(reverse_segments)}")
    
    def score_baseline_segment(segment):
        """Score a segment for baseline suitability"""
        score = 0.0
        
        # Linearity (R²) - higher is better
        score += segment['r2'] * 50
        
        # Length - longer is better
        score += min(segment['length'] / 20, 1) * 30  # Cap at 20 points
        
        # Low slope - more horizontal is better for baseline
        slope_penalty = min(abs(segment['slope']) * 1e6, 10)  # Convert to µA/V, cap penalty
        score -= slope_penalty
        
        # Voltage span - reasonable span is better
        voltage_span = abs(segment['voltage_span'])
        if 0.05 <= voltage_span <= 0.3:  # 50mV to 300mV is good
            score += 10
        
        # Low current standard deviation - more stable is better
        if segment['std_current'] > 0:
            score += max(0, 10 - (segment['std_current'] * 1e6))  # Convert to µA
        
        return score
    
    # Score and select best segments
    def select_best_segment(segment_list, direction_name):
        if not segment_list:
            logger.info(f"[BASELINE] No {direction_name} segments to select from")
            return None
        
        scored_segments = [(score_baseline_segment(s), s) for s in segment_list]
        scored_segments.sort(key=lambda x: x[0], reverse=True)  # Best score first
        
        logger.info(f"[BASELINE] {direction_name} segment scores: {[f'{s[0]:.1f}' for s in scored_segments[:3]]}")
        
        best_segment = scored_segments[0][1]
        logger.info(f"[BASELINE] Best {direction_name} segment: idx {best_segment['start_idx']}-{best_segment['end_idx']}, score={scored_segments[0][0]:.1f}, R²={best_segment['r2']:.3f}")
        return best_segment  # Return best segment
    
    forward_baseline_segment = select_best_segment(forward_segments, "forward")
    reverse_baseline_segment = select_best_segment(reverse_segments, "reverse")
    
    return forward_baseline_segment, reverse_baseline_segment

def calculate_baseline_from_segments(voltage, current, forward_segment, reverse_segment):
    """
    Generate baseline arrays from selected segments
    """
    n = len(voltage)
    baseline_forward = np.full(n//2, np.nan)
    baseline_reverse = np.full(n - n//2, np.nan)
    
    # Generate forward baseline
    if forward_segment:
        # Extract the linear fit from the segment
        slope = forward_segment['slope']
        intercept = forward_segment['intercept']
        
        # Apply to forward half
        v_forward = voltage[:n//2]
        baseline_forward = slope * v_forward + intercept
        
        logger.info(f"Forward baseline: slope={slope:.2e} A/V, R²={forward_segment['r2']:.3f}")
    
    # Generate reverse baseline  
    if reverse_segment:
        slope = reverse_segment['slope']
        intercept = reverse_segment['intercept']
        
        # Apply to reverse half
        v_reverse = voltage[n//2:]
        baseline_reverse = slope * v_reverse + intercept
        
        logger.info(f"Reverse baseline: slope={slope:.2e} A/V, R²={reverse_segment['r2']:.3f}")
    
    return baseline_forward, baseline_reverse

def detect_improved_baseline(voltage, current):
    """
    Main function: 2-step baseline detection
    """
    try:
        logger.info(f"[BASELINE] Starting improved baseline detection...")
        logger.info(f"[BASELINE] Data points: {len(voltage)}, V range: {min(voltage):.3f} to {max(voltage):.3f}")
        
        # Step 1: Find linear segments
        segments = detect_linear_segments(voltage, current)
        logger.info(f"[BASELINE] Step 1 complete: Found {len(segments)} linear segments")
        
        if not segments:
            logger.warning("No linear segments found for baseline")
            # Fallback to simple linear fit
            n = len(voltage)
            mid = n // 2
            
            def simple_fit(v, i):
                if len(v) < 2:
                    return np.full_like(v, np.nan)
                coeffs = np.polyfit(v, i, 1)
                return np.polyval(coeffs, v)
            
            baseline_forward = simple_fit(voltage[:mid], current[:mid])
            baseline_reverse = simple_fit(voltage[mid:], current[mid:])
            logger.info(f"[BASELINE] Using fallback simple fit")
            return baseline_forward, baseline_reverse
        
        # Step 2: Select best segments for baseline
        logger.info(f"[BASELINE] Step 2: Selecting best segments...")
        forward_segment, reverse_segment = select_baseline_segments(segments, voltage, current)
        
        if forward_segment:
            logger.info(f"[BASELINE] Forward segment selected: start_idx={forward_segment['start_idx']}, end_idx={forward_segment['end_idx']}, R²={forward_segment['r2']:.3f}")
        else:
            logger.warning(f"[BASELINE] No forward segment selected")
            
        if reverse_segment:
            logger.info(f"[BASELINE] Reverse segment selected: start_idx={reverse_segment['start_idx']}, end_idx={reverse_segment['end_idx']}, R²={reverse_segment['r2']:.3f}")
        else:
            logger.warning(f"[BASELINE] No reverse segment selected")
        
        # Step 3: Generate baseline arrays
        logger.info(f"[BASELINE] Step 3: Generating baseline arrays...")
        baseline_forward, baseline_reverse = calculate_baseline_from_segments(
            voltage, current, forward_segment, reverse_segment
        )
        
        logger.info(f"[BASELINE] Detection complete: forward={len(baseline_forward)} points, reverse={len(baseline_reverse)} points")
        return baseline_forward, baseline_reverse
        
    except Exception as e:
        logger.error(f"Error in improved baseline detection: {e}")
        # Fallback to simple method
        n = len(voltage)
        mid = n // 2
        
        def simple_fit(v, i):
            if len(v) < 2:
                return np.full_like(v, np.nan)
            coeffs = np.polyfit(v, i, 1)
            return np.polyval(coeffs, v)
        
        baseline_forward = simple_fit(voltage[:mid], current[:mid])
        baseline_reverse = simple_fit(voltage[mid:], current[mid:])
        return baseline_forward, baseline_reverse

if __name__ == "__main__":
    # Test with sample data
    logging.basicConfig(level=logging.INFO)
    
    # Generate test CV data
    v = np.linspace(-0.5, 0.5, 100)
    v = np.concatenate([v, v[::-1]])  # Forward + reverse scan
    
    # Simulate CV with baseline + peaks
    baseline = 1e-6 * (1 + 0.1 * v)  # Linear baseline with slight slope
    peaks = 5e-6 * np.exp(-50 * (v - 0.2)**2) - 3e-6 * np.exp(-50 * (v + 0.1)**2)  # Peaks
    noise = np.random.normal(0, 1e-7, len(v))
    
    current = baseline + peaks + noise
    
    # Test the algorithm
    forward_bl, reverse_bl = detect_improved_baseline(v, current)
    
    print(f"Forward baseline: {len(forward_bl)} points")
    print(f"Reverse baseline: {len(reverse_bl)} points")
    print(f"Forward range: {forward_bl[0]:.2e} to {forward_bl[-1]:.2e}")
    print(f"Reverse range: {reverse_bl[0]:.2e} to {reverse_bl[-1]:.2e}")