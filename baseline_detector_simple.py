#!/usr/bin/env python3
"""
Simple and robust baseline detector for CV data
Fixed version based on original working algorithm
"""

import numpy as np
from scipy import stats
import logging

def cv_baseline_detector_v3(voltage, current, logger=None, peaks=None):
    """
    Simple CV baseline detection using extended segment analysis
    This version prioritizes long, stable segments with consistent slope
    and avoids peak regions if peaks are provided
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        logger.info("[BASELINE] Starting simple CV baseline detection v3")
        
        n = len(voltage)
        mid = n // 2
        
        # Extract peak regions to avoid if peaks are provided
        peak_regions = []
        if peaks:
            logger.info(f"[BASELINE] Avoiding {len(peaks)} peak regions")
            for peak in peaks:
                if 'voltage' in peak:
                    peak_v = peak['voltage']
                    # Find closest index
                    peak_idx = np.argmin(np.abs(voltage - peak_v))
                    # Create smaller, more precise exclusion zone around peak (±5% of data range or ±10 points)
                    exclusion_width = max(10, int(n * 0.05))
                    start_exclude = max(0, peak_idx - exclusion_width)
                    end_exclude = min(n, peak_idx + exclusion_width)
                    peak_regions.append((start_exclude, end_exclude))
                    logger.info(f"[BASELINE] Excluding peak region [{start_exclude}:{end_exclude}] around V={peak_v:.3f}V (idx={peak_idx})")
        
        def is_in_peak_region(start_idx, end_idx):
            """Check if segment overlaps with any peak region"""
            for peak_start, peak_end in peak_regions:
                # Check for overlap - if any part of segment overlaps with peak region, reject it
                if not (end_idx <= peak_start or start_idx >= peak_end):
                    return True
            return False
        
        def find_stable_segments(v_data, i_data, start_offset=0, min_length=8):
            """Find segments with consistent slope (stable baseline regions), avoiding rapid initial changes"""
            segments = []
            
            # Skip initial rapid changes - start searching from 40% into the data
            skip_initial = max(12, int(len(v_data) * 0.4))  # Skip first 40% or at least 12 points
            logger.info(f"[BASELINE] Skipping first {skip_initial} points to avoid rapid initial changes")
            
            # Use a sliding window to find stable regions
            window_size = max(8, min_length)
            step_size = 3  # Larger steps to avoid similar segments
            
            # Calculate overall current statistics for stability checks
            overall_current_range = np.max(i_data) - np.min(i_data)
            
            for i in range(skip_initial, len(v_data) - window_size, step_size):
                end_idx = i + window_size
                
                # Check if this starting segment is in a peak region
                global_start = i + start_offset
                global_end = end_idx + start_offset
                if is_in_peak_region(global_start, global_end):
                    continue
                
                # Pre-check: ensure this is a VERY stable region 
                initial_segment_current = i_data[i:end_idx]
                current_std = np.std(initial_segment_current)
                current_range = np.max(initial_segment_current) - np.min(initial_segment_current)
                
                # Much stricter stability requirements
                if current_range > 0.02 * overall_current_range:  # > 2% of total range (was 5%)
                    continue
                if current_std > 0.008 * overall_current_range:  # > 0.8% of total range (was 2%)
                    continue
                
                # Additional check: slope of initial segment must be very small
                try:
                    initial_v = v_data[i:end_idx]
                    initial_slope = np.polyfit(initial_v, initial_segment_current, 1)[0]
                    if abs(initial_slope) > 2.0:  # Must be flatter than 2 µA/V
                        continue
                except:
                    continue
                
                # Extend window while slope remains consistent and not in peak regions
                while end_idx < len(v_data):
                    # Check if extending would enter peak region
                    global_end_extended = end_idx + 1 + start_offset
                    if global_end_extended < n and is_in_peak_region(global_start, global_end_extended):
                        break
                    
                    # Check if adding next point maintains slope consistency
                    v_seg = v_data[i:end_idx+1]
                    i_seg = i_data[i:end_idx+1]
                    
                    try:
                        slope, intercept, r_value, p_value, std_err = stats.linregress(v_seg, i_seg)
                        r2 = r_value ** 2
                        
                        # If R² drops significantly, stop extending
                        if r2 < 0.90:  # Even stricter R² requirement for extension
                            break
                            
                        # CRITICAL: Check if slope is too steep for baseline
                        # Good baseline should have very small slope (< 5 µA/V)
                        if abs(slope) > 5.0:  # Absolute slope limit in µA/V
                            break
                            
                        # Additional stability check: current should be relatively flat
                        segment_current_std = np.std(i_seg)
                        if segment_current_std > 0.02 * overall_current_range:  # > 2% variation
                            break
                            
                        # Check if slope is too steep relative to data characteristics
                        current_range = max(i_seg) - min(i_seg)
                        voltage_range = max(v_seg) - min(v_seg) 
                        if voltage_range > 0:
                            normalized_slope = abs(slope * voltage_range / current_range) if current_range > 0 else abs(slope)
                            if normalized_slope > 0.3:  # More strict: was 0.5, now 0.3
                                break
                            
                        # Check slope consistency with a smaller window
                        if len(v_seg) > window_size:
                            recent_v = v_seg[-window_size//2:]
                            recent_i = i_seg[-window_size//2:]
                            recent_slope, _, recent_r, _, _ = stats.linregress(recent_v, recent_i)
                            
                            # If recent slope differs significantly from overall slope, stop
                            if abs(recent_slope - slope) > abs(slope) * 0.2:  # Tighter tolerance (20%)
                                break
                        
                        end_idx += 1
                        
                    except:
                        break
                
                # If we found a good segment, record it
                if end_idx - i >= min_length:
                    v_seg = v_data[i:end_idx]
                    i_seg = i_data[i:end_idx]
                    
                    try:
                        slope, intercept, r_value, p_value, std_err = stats.linregress(v_seg, i_seg)
                        r2 = r_value ** 2
                        
                        # Much stricter requirements for baseline segments
                        baseline_slope_limit = 3.0  # µA/V - very conservative
                        segment_current_std = np.std(i_seg)
                        stability_metric = segment_current_std / overall_current_range
                        
                        # Multiple criteria for good baseline:
                        # 1. High R² (linearity)
                        # 2. Low absolute slope (flatness) 
                        # 3. Low current variation (stability)
                        if (r2 > 0.90 and 
                            abs(slope) < baseline_slope_limit and 
                            stability_metric < 0.015):  # < 1.5% current variation
                            
                            global_start = i + start_offset
                            global_end = end_idx + start_offset
                            
                            # Final check - make sure segment doesn't overlap with peaks
                            if not is_in_peak_region(global_start, global_end):
                                segments.append({
                                    'start_idx': global_start,
                                    'end_idx': global_end,
                                    'slope': slope,
                                    'intercept': intercept,
                                    'r2': r2,
                                    'p_value': p_value,
                                    'std_err': std_err,
                                    'length': end_idx - i,
                                    'voltage_start': v_data[i],
                                    'voltage_end': v_data[end_idx-1],
                                    'current_stability': stability_metric  # Lower is better
                                })
                                logger.info(f"[BASELINE] Found stable segment [{global_start}:{global_end}]: "
                                           f"length={end_idx - i}, R²={r2:.3f}, slope={slope:.2e}, "
                                           f"V=[{v_data[i]:.3f}:{v_data[end_idx-1]:.3f}], stability={stability_metric:.3f}")
                            else:
                                logger.debug(f"[BASELINE] Rejected segment [{global_start}:{global_end}] - overlaps peak region")
                        else:
                            logger.debug(f"[BASELINE] Rejected segment: R²={r2:.3f}, slope={slope:.2e}, stability={stability_metric:.3f}")
                            
                    except Exception as e:
                        logger.warning(f"Failed to analyze segment [{i}:{end_idx}]: {e}")
            
            return segments
        
        # Analyze forward and reverse sweeps
        logger.info(f"[BASELINE] Analyzing forward sweep (0:{mid})")
        forward_segments = find_stable_segments(voltage[:mid], current[:mid], start_offset=0)
        
        logger.info(f"[BASELINE] Analyzing reverse sweep ({mid}:{n})")
        reverse_segments = find_stable_segments(voltage[mid:], current[mid:], start_offset=mid)
        
        # Select best segments with voltage range preferences
        def select_best_segment(segments, name, preferred_voltage_range=None):
            if not segments:
                logger.warning(f"No {name} segments found")
                return None
            
            # Score based on: stability * R² * length_bonus * voltage_preference
            # Prioritize stability (low current variation) above all
            scored_segments = []
            for seg in segments:
                # Very strict R² requirement - must be extremely linear
                if seg['r2'] < 0.95:  # Increase from 0.90 to 0.95
                    continue
                
                # CRITICAL: Prevent segments that are too long (likely covering peaks)
                max_allowed_length = 50  # Maximum 50 points for any baseline segment
                if seg['length'] > max_allowed_length:
                    logger.warning(f"Rejecting {name} segment length {seg['length']} > {max_allowed_length}")
                    continue
                    
                # For forward segments, extra restriction: must be in first 40% of data
                if name == 'forward':
                    max_forward_end = mid * 0.4  # Only first 40% of forward sweep
                    if seg['end_idx'] > max_forward_end:
                        logger.warning(f"Rejecting forward segment ending at {seg['end_idx']} > {max_forward_end}")
                        continue
                
                # PRIORITY 1: Stability bonus - heavily prioritize stable current
                if 'current_stability' in seg:
                    stability_bonus = (1.0 / (1.0 + seg['current_stability'] * 100)) ** 3  # Lower stability = higher bonus
                else:
                    stability_bonus = 0.5  # Fallback for old segments without stability metric
                
                # PRIORITY 2: Flatness bonus - penalize steep slopes heavily
                slope_flatness = 1.0 / (1.0 + abs(seg['slope']) * 0.5)  # Reward very flat slopes
                
                # PRIORITY 3: R² quality
                r2_bonus = seg['r2'] ** 2  # Good but not dominant
                
                # PRIORITY 4: Length bonus - moderate, not dominant
                ideal_length = 20
                if seg['length'] <= ideal_length:
                    length_bonus = seg['length'] / ideal_length  # Linear bonus up to ideal
                else:
                    # Penalty for being too long
                    length_penalty = (seg['length'] - ideal_length) / (max_allowed_length - ideal_length)
                    length_bonus = max(0.1, 1.0 - length_penalty)  # Decreasing bonus for longer segments
                
                # PRIORITY 5: Voltage range preference
                voltage_bonus = 1.0
                if preferred_voltage_range:
                    v_start, v_end = preferred_voltage_range
                    seg_v_start = seg['voltage_start']
                    seg_v_end = seg['voltage_end']
                    
                    # Check how much overlap with preferred range
                    overlap_start = max(v_start, seg_v_start)
                    overlap_end = min(v_end, seg_v_end)
                    if overlap_end > overlap_start:
                        overlap_fraction = (overlap_end - overlap_start) / (seg_v_end - seg_v_start)
                        voltage_bonus = 1.0 + (overlap_fraction * 2.0)  # Reduced bonus: up to 3x
                    else:
                        voltage_bonus = 0.2  # Less harsh penalty for wrong voltage range
                
                # Final score: stability is king, then flatness, then R², then length, then voltage
                score = stability_bonus * slope_flatness * r2_bonus * length_bonus * voltage_bonus
                scored_segments.append((score, seg))
                
                logger.debug(f"[BASELINE] {name} segment score: stability={stability_bonus:.3f}, "
                           f"flatness={slope_flatness:.3f}, R²={r2_bonus:.3f}, "
                           f"length={length_bonus:.3f}, voltage={voltage_bonus:.3f}, "
                           f"total={score:.3f}")
            
            # Sort by score descending
            scored_segments.sort(key=lambda x: x[0], reverse=True)
            
            if not scored_segments:
                logger.warning(f"No high-quality {name} segments found (R² >= 0.95)")
                return None
            
            best_score, best_segment = scored_segments[0]
            logger.info(f"[BASELINE] Best {name} segment: [{best_segment['start_idx']}:{best_segment['end_idx']}] "
                       f"length={best_segment['length']}, R²={best_segment['r2']:.3f}, "
                       f"slope={best_segment['slope']:.2e}, score={best_score:.3f}, "
                       f"stability={best_segment.get('current_stability', 'N/A')}, "
                       f"V=[{best_segment['voltage_start']:.3f}:{best_segment['voltage_end']:.3f}]")
            return best_segment
            
            # Sort by score descending
            scored_segments.sort(key=lambda x: x[0], reverse=True)
            
            if not scored_segments:
                logger.warning(f"No high-quality {name} segments found (R² >= 0.95)")
                return None
            
            best_score, best_segment = scored_segments[0]
            logger.info(f"[BASELINE] Best {name} segment: [{best_segment['start_idx']}:{best_segment['end_idx']}] "
                       f"length={best_segment['length']}, R²={best_segment['r2']:.3f}, "
                       f"slope={best_segment['slope']:.2e}, score={best_score:.2f}, "
                       f"V=[{best_segment['voltage_start']:.3f}:{best_segment['voltage_end']:.3f}]")
            return best_segment
        
        # Define preferred voltage ranges for baseline - more restrictive
        v_min, v_max = voltage.min(), voltage.max()
        v_range = v_max - v_min
        
        # Forward baseline should be in EARLY voltage range (first 30% only)
        forward_preferred = (v_min, v_min + 0.3 * v_range)
        # Reverse baseline should be in LATE voltage range (last 30% only)  
        reverse_preferred = (v_max - 0.3 * v_range, v_max)
        
        logger.info(f"[BASELINE] Voltage ranges - Forward: {forward_preferred[0]:.3f} to {forward_preferred[1]:.3f}V")
        logger.info(f"[BASELINE] Voltage ranges - Reverse: {reverse_preferred[0]:.3f} to {reverse_preferred[1]:.3f}V")
        
        forward_segment = select_best_segment(forward_segments, 'forward', forward_preferred)
        
        # If no forward baseline found in preferred range, try without voltage restriction
        # but ensure it's in the first 40% of the data (before peak region)
        if forward_segment is None:
            logger.warning("No forward baseline in preferred voltage range, trying early segments only")
            # Filter segments to only first 40% of data points to avoid peaks
            # Also limit segment length to maximum 30 points
            early_forward_segments = [seg for seg in forward_segments 
                                    if seg['start_idx'] < mid * 0.4 and 
                                       seg['end_idx'] < mid * 0.4 and
                                       seg['length'] <= 30]  # Maximum 30 points
            forward_segment = select_best_segment(early_forward_segments, 'forward (early)', None)
            
        # Extra safety check for forward segment
        if forward_segment and forward_segment['end_idx'] > mid * 0.4:
            logger.warning(f"Forward segment extends too far ({forward_segment['end_idx']} > {mid * 0.4:.0f}), using fallback")
            forward_segment = None
        
        reverse_segment = select_best_segment(reverse_segments, 'reverse', reverse_preferred)
        
        # Extra safety check for reverse segment - ensure it doesn't cover peaks
        if reverse_segment is None:
            logger.warning("No reverse baseline in preferred voltage range, trying late segments only")
            # Filter segments to only last 40% of data points and short segments
            late_reverse_segments = [seg for seg in reverse_segments 
                                   if seg['start_idx'] > mid + (n - mid) * 0.6 and  # Last 40% of reverse sweep
                                      seg['length'] <= 25]  # Maximum 25 points
            reverse_segment = select_best_segment(late_reverse_segments, 'reverse (late)', None)
            
        # Extra safety check for reverse segment
        if reverse_segment and reverse_segment['start_idx'] < mid + (n - mid) * 0.6:
            logger.warning(f"Reverse segment starts too early ({reverse_segment['start_idx']} < {mid + (n - mid) * 0.6:.0f}), using fallback")
            reverse_segment = None
        
        # Generate baseline using the selected segments with clear separation
        baseline_forward = np.zeros(mid)
        baseline_reverse = np.zeros(n - mid)
        
        # Add buffer zone - don't extend baselines too close to the middle
        buffer_points = max(5, mid // 20)  # At least 5 points, or 5% of forward sweep
        forward_end_limit = mid - buffer_points
        reverse_start_limit = mid + buffer_points
        
        logger.info(f"[BASELINE] Buffer zone: forward ends at {forward_end_limit}, reverse starts at {reverse_start_limit}")
        
        if forward_segment:
            v_forward = voltage[:mid]
            baseline_forward = forward_segment['slope'] * v_forward + forward_segment['intercept']
            
            # Taper off the forward baseline near the middle to avoid overlap
            if forward_segment['end_idx'] > forward_end_limit:
                # Gradually fade out the baseline in the buffer zone
                fade_start = max(0, forward_end_limit - buffer_points)
                for i in range(fade_start, mid):
                    fade_factor = max(0, (forward_end_limit - i) / buffer_points)
                    if fade_factor < 1.0:
                        baseline_forward[i] *= fade_factor
                        
            logger.info(f"✓ Forward baseline generated: slope={forward_segment['slope']:.2e}, R²={forward_segment['r2']:.3f}")
        else:
            # Fallback: use ONLY the most stable part of forward sweep 
            # Start from 40% and use next 20% (40%-60% of forward sweep)
            fallback_start = max(8, int(mid * 0.4))  # Start from 40%
            fallback_end = min(mid - 5, int(mid * 0.6))  # End at 60%, leave buffer
            
            if fallback_end > fallback_start + 5:  # Need at least 5 points
                try:
                    coeffs = np.polyfit(voltage[fallback_start:fallback_end], current[fallback_start:fallback_end], 1)
                    
                    # Check if this fallback segment is actually stable
                    fallback_current = current[fallback_start:fallback_end]
                    fallback_std = np.std(fallback_current)
                    overall_range = np.max(current) - np.min(current)
                    
                    if fallback_std < 0.01 * overall_range and abs(coeffs[0]) < 5.0:  # Very strict
                        # Only apply to the stable region
                        baseline_forward[fallback_start:fallback_end] = np.polyval(coeffs, voltage[fallback_start:fallback_end])
                        logger.info(f"⚠ Forward baseline (stable middle region): slope={coeffs[0]:.2e}, points [{fallback_start}:{fallback_end}]")
                        forward_segment = {
                            'start_idx': fallback_start,
                            'end_idx': fallback_end,
                            'slope': coeffs[0],
                            'intercept': coeffs[1],
                            'r2': 0.85,
                            'p_value': 0.05,
                            'std_err': 0.0,
                            'length': fallback_end - fallback_start
                        }
                    else:
                        # Region not stable enough - no forward baseline
                        logger.warning("⚠ No stable forward region found - no forward baseline")
                        forward_segment = None
                except:
                    logger.warning("⚠ Forward fallback failed - no forward baseline")
                    forward_segment = None
            else:
                logger.warning("⚠ Insufficient data for forward fallback - no forward baseline")
                forward_segment = None
        
        if reverse_segment:
            v_reverse = voltage[mid:]
            baseline_reverse = reverse_segment['slope'] * v_reverse + reverse_segment['intercept']
            
            # Taper the reverse baseline to not start too early
            if reverse_segment['start_idx'] < reverse_start_limit:
                # Gradually fade in the baseline in the buffer zone  
                fade_end = min(n - mid, reverse_start_limit - mid + buffer_points)
                for i in range(0, fade_end):
                    fade_factor = max(0, (i - (reverse_start_limit - mid)) / buffer_points)
                    if fade_factor < 1.0:
                        baseline_reverse[i] *= fade_factor
                        
            logger.info(f"✓ Reverse baseline generated: slope={reverse_segment['slope']:.2e}, R²={reverse_segment['r2']:.3f}")
        else:
            # Fallback: use ONLY the most stable part of reverse sweep
            # Use last 30% but avoid very end (80%-90% of reverse sweep)
            reverse_length = n - mid
            fallback_start = mid + int(reverse_length * 0.8)  # Start from 80%
            fallback_end = mid + int(reverse_length * 0.95)   # End at 95%, avoid very end
            
            if fallback_end > fallback_start + 5:  # Need at least 5 points
                try:
                    coeffs = np.polyfit(voltage[fallback_start:fallback_end], current[fallback_start:fallback_end], 1)
                    
                    # Check if this fallback segment is actually stable
                    fallback_current = current[fallback_start:fallback_end]
                    fallback_std = np.std(fallback_current)
                    overall_range = np.max(current) - np.min(current)
                    
                    if fallback_std < 0.01 * overall_range and abs(coeffs[0]) < 5.0:  # Very strict
                        # Only apply to the stable region
                        baseline_reverse[fallback_start-mid:fallback_end-mid] = np.polyval(coeffs, voltage[fallback_start:fallback_end])
                        logger.info(f"⚠ Reverse baseline (stable late region): slope={coeffs[0]:.2e}, points [{fallback_start}:{fallback_end}]")
                        reverse_segment = {
                            'start_idx': fallback_start,
                            'end_idx': fallback_end,
                            'slope': coeffs[0],
                            'intercept': coeffs[1],
                            'r2': 0.85,
                            'p_value': 0.05,
                            'std_err': 0.0,
                            'length': fallback_end - fallback_start
                        }
                    else:
                        # Region not stable enough - no reverse baseline
                        logger.warning("⚠ No stable reverse region found - no reverse baseline")
                        reverse_segment = None
                except:
                    logger.warning("⚠ Reverse fallback failed - no reverse baseline")
                    reverse_segment = None
            else:
                logger.warning("⚠ Insufficient data for reverse fallback - no reverse baseline")
                reverse_segment = None
        
        # Log baseline statistics
        baseline_full = np.concatenate([baseline_forward, baseline_reverse])
        logger.info(f"📊 Baseline summary:")
        logger.info(f"   Forward range: [{baseline_forward.min():.3f}, {baseline_forward.max():.3f}] μA")
        logger.info(f"   Reverse range: [{baseline_reverse.min():.3f}, {baseline_reverse.max():.3f}] μA")
        logger.info(f"   Full range: [{baseline_full.min():.3f}, {baseline_full.max():.3f}] μA")
        logger.info(f"   CV data range: [{current.min():.3f}, {current.max():.3f}] μA")
        
        return baseline_forward, baseline_reverse, {
            'forward_segment': forward_segment,
            'reverse_segment': reverse_segment,
            'excluded_peaks': len(peak_regions),
            'peak_regions': peak_regions
        }
        
    except Exception as e:
        logger.error(f"❌ Error in CV baseline detection v3: {e}")
        # Safe fallback
        n = len(voltage)
        mid = n // 2
        
        def safe_linear_fit(v, i):
            try:
                if len(v) >= 2:
                    coeffs = np.polyfit(v, i, 1)
                    return np.polyval(coeffs, v)
                else:
                    return np.full_like(v, np.mean(i) if len(i) > 0 else 0.0)
            except:
                return np.full_like(v, np.mean(i) if len(i) > 0 else 0.0)
        
        return safe_linear_fit(voltage[:mid], current[:mid]), safe_linear_fit(voltage[mid:], current[mid:]), {
            'forward_segment': None,
            'reverse_segment': None
        }

if __name__ == "__main__":
    # Test the detector
    import matplotlib.pyplot as plt
    
    # Generate test CV data
    v = np.linspace(-0.5, 0.5, 200)
    # Simulate CV with oxidation peak at 0.2V and reduction peak at -0.2V
    i = -50 + 0.1 * v + 200 * np.exp(-((v - 0.2) / 0.05)**2) - 180 * np.exp(-((v + 0.2) / 0.05)**2)
    # Add some noise
    i += np.random.normal(0, 5, len(i))
    
    # Test the detector
    baseline_f, baseline_r, segments = cv_baseline_detector_v3(v, i)
    baseline_full = np.concatenate([baseline_f, baseline_r])
    
    # Plot results
    plt.figure(figsize=(10, 6))
    plt.plot(v, i, 'b-', label='CV Data', linewidth=2)
    plt.plot(v, baseline_full, 'r--', label='Baseline', linewidth=2)
    
    # Mark segments
    if segments['forward_segment']:
        fs = segments['forward_segment']
        plt.axvspan(v[fs['start_idx']], v[fs['end_idx']], alpha=0.2, color='green', label='Forward Segment')
    
    if segments['reverse_segment']:
        rs = segments['reverse_segment']
        plt.axvspan(v[rs['start_idx']], v[rs['end_idx']], alpha=0.2, color='orange', label='Reverse Segment')
    
    plt.xlabel('Voltage (V)')
    plt.ylabel('Current (μA)')
    plt.title('CV Baseline Detection Test')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()
    
    print("Test completed!")