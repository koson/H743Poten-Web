# Import Enhanced Baseline Detector v2.1 for Web Application
try:
    from ..utils.cv_baseline_corrector import CVBaselineCorrector
except ImportError:
    from utils.cv_baseline_corrector import CVBaselineCorrector

import numpy as np
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class BaselineDetector:
    """🚀 Production Baseline Detector with Smart Method Selection"""
    
    def __init__(self, auto_mode: bool = True):
        """
        Initialize baseline detector for web application
        auto_mode: If True, automatically choose best method based on data
        """
        self.auto_mode = auto_mode
        
        # Initialize CV-specific corrector
        self.cv_corrector = CVBaselineCorrector()
        
        # Optimized configuration for fallback methods
        self.traditional_window = 25  # Optimized traditional window size
        
        logger.info("🎯 Baseline Detector v2.1 Initialized for Web Application")
        logger.info(f"🤖 Auto-mode: {'ON' if auto_mode else 'OFF'}")
    
    def detect_baseline(self, voltages: np.ndarray, currents: np.ndarray, 
                       filename: str = "web_data", force_method: str = None) -> Tuple[np.ndarray, Dict]:
        """
        🎯 Smart baseline detection with automatic method selection
        
        Args:
            voltages: Voltage array
            currents: Current array  
            filename: Data identifier for logging
            force_method: Force specific method ('traditional', 'cv_optimized', None for auto)
        
        Returns:
            baseline: Detected baseline
            metadata: Detection metadata
        """
        start_time = time.time()
        
        logger.info(f"🔍 Baseline Detection: {filename}")
        logger.info(f"📊 Data: {len(voltages)} points, Range: {voltages.min():.3f}V to {voltages.max():.3f}V")
        logger.info(f"⚡ Current range: {currents.min():.2e} to {currents.max():.2e} µA")
        
        # Method selection
        if force_method:
            selected_method = force_method
            logger.info(f"🔧 Forced method: {selected_method}")
        elif self.auto_mode:
            selected_method = self._select_optimal_method(currents, voltages)
            logger.info(f"🤖 Auto-selected method: {selected_method}")
        else:
            selected_method = 'cv_optimized'  # Default to CV optimized
            logger.info(f"📊 Default method: {selected_method}")
        
        # Apply selected method
        if selected_method == 'traditional':
            baseline = self._traditional_baseline(currents)
            metadata = {
                'method': 'traditional_optimized',
                'window_size': self.traditional_window,
                'processing_time': time.time() - start_time,
                'quality_metrics': {'overall_quality': 0.7}  # Estimated quality
            }
            logger.info(f"✅ Traditional method completed in {metadata['processing_time']:.3f}s")
        else:
            # Use CV-optimized baseline corrector
            baseline, cv_metadata = self.cv_corrector.detect_baseline_cv(voltages, currents, filename)
            cv_metadata['auto_selected'] = self.auto_mode
            metadata = cv_metadata
        
        logger.info(f"🎯 Selected method: {metadata['method']}")
        logger.info(f"⏱️ Processing time: {metadata['processing_time']:.3f}s")
        
        return baseline, metadata
    
    def _select_optimal_method(self, currents: np.ndarray, voltages: np.ndarray) -> str:
        """🤖 Intelligent method selection based on data characteristics"""
        
        # Simple heuristics for method selection
        data_range = np.ptp(currents)  # Peak-to-peak range
        data_std = np.std(currents)
        
        # For CV data, check if it looks like a typical CV scan
        is_cv_like = self._is_cv_like_data(voltages, currents)
        
        if is_cv_like:
            return 'cv_optimized'  # Use CV-specific method
        elif data_std < 0.1 * data_range:
            return 'traditional'   # Very clean data - use simple method
        else:
            return 'cv_optimized'  # Default to CV-optimized for robustness
    
    def _is_cv_like_data(self, voltages: np.ndarray, currents: np.ndarray) -> bool:
        """🔍 Check if data looks like CV scan"""
        
        try:
            # CV characteristics:
            # 1. Voltage should span reasonable range
            voltage_range = np.ptp(voltages)
            if voltage_range < 0.3:  # Less than 300mV range
                return False
            
            # 2. Current should have both positive and negative values (or significant variation)
            current_range = np.ptp(currents)
            current_mean = np.abs(np.mean(currents))
            
            if current_range > 5 * current_mean:  # Significant variation
                return True
            
            # 3. Check for potential peak-like behavior
            current_abs = np.abs(currents)
            max_current = np.max(current_abs)
            median_current = np.median(current_abs)
            
            if max_current > 3 * median_current:  # Has peak-like features
                return True
            
            return True  # Default to CV-like for safety
            
        except Exception:
            return True  # Default to CV-like on error
    
    def _traditional_baseline(self, currents: np.ndarray) -> np.ndarray:
        """📊 Optimized traditional baseline using moving average"""
        
        window = min(self.traditional_window, len(currents) // 4)
        if window < 3:
            return np.zeros_like(currents)
        
        # Simple moving average baseline
        baseline = np.copy(currents)
        half_window = window // 2
        
        for i in range(len(currents)):
            start = max(0, i - half_window)
            end = min(len(currents), i + half_window + 1)
            baseline[i] = np.mean(currents[start:end])
        
        return baseline
    
    def _assess_data_complexity(self, currents: np.ndarray) -> Dict:
        """📊 Assess data complexity metrics"""
        
        # Compute various complexity metrics safely
        if len(currents) < 2:
            return {
                'peak_count': 0,
                'noise_ratio': 0.0,
                'stability_metric': 1.0,
                'dynamic_range': 0.0
            }
        
        current_diff = np.diff(currents)
        current_max = np.abs(currents).max()
        current_normalized = currents / current_max if current_max > 0 else currents
        
        # Peak count estimation
        try:
            from scipy.signal import find_peaks
            peaks, _ = find_peaks(np.abs(current_normalized), prominence=0.1, width=3)
            peak_count = len(peaks)
        except ImportError:
            # Fallback without scipy
            peak_count = self._simple_peak_count(current_normalized)
        
        # Noise estimation - handle the diff size difference
        current_std = np.std(currents)
        noise_ratio = np.std(current_diff) / current_std if current_std > 0 else 0
        
        # Stability metric
        stability_metric = 1.0 / (1.0 + np.std(current_diff)) if len(current_diff) > 0 else 1.0
        
        return {
            'peak_count': peak_count,
            'noise_ratio': noise_ratio,
            'stability_metric': stability_metric,
            'dynamic_range': np.ptp(currents) / np.abs(currents).max() if np.abs(currents).max() > 0 else 0
        }
    
    def _estimate_noise_level(self, currents: np.ndarray) -> float:
        """🔊 Estimate noise level in the data"""
        
        # High-frequency noise estimation
        current_smooth = self._moving_average(currents, window=5)
        noise = currents - current_smooth
        noise_level = np.std(noise) / np.std(currents) if np.std(currents) > 0 else 0
        
        return min(noise_level, 1.0)  # Cap at 1.0
    
    def _simple_peak_count(self, data: np.ndarray) -> int:
        """Simple peak counting without scipy"""
        
        peaks = 0
        for i in range(1, len(data) - 1):
            if (data[i] > data[i-1] and data[i] > data[i+1] and 
                abs(data[i]) > 0.1):  # Simple peak detection
                peaks += 1
        return peaks
    
    def _traditional_baseline(self, currents: np.ndarray) -> np.ndarray:
        """📊 Optimized traditional baseline using moving average"""
        
        window = min(self.traditional_window, len(currents) // 4)
        if window < 3:
            return np.zeros_like(currents)
        
        # Apply smoothed moving average
        baseline = self._moving_average(currents, window)
        
        # Additional smoothing for stability
        baseline = self._moving_average(baseline, window // 2)
        
        return baseline
    
    def _enhanced_baseline(self, voltages: np.ndarray, currents: np.ndarray, 
                          filename: str) -> Tuple[np.ndarray, Dict]:
        """🚀 Enhanced baseline detection with feature engineering"""
        
        start_time = time.time()
        
        # Enhanced baseline detection logic
        try:
            # Find linear segments
            segments = self._detect_linear_segments(voltages, currents)
            
            if not segments:
                logger.warning("No linear segments found, using fallback")
                baseline = self._traditional_baseline(currents)
                metadata = {
                    'processing_time': time.time() - start_time,
                    'fallback_used': True,
                    'quality_metrics': {'overall_quality': 0.6}
                }
                return baseline, metadata
            
            # Select best segments for baseline
            baseline_segments = self._select_baseline_segments(segments, voltages, currents)
            
            # Interpolate baseline
            baseline = self._interpolate_baseline(baseline_segments, len(currents))
            
            # Smooth the result
            baseline = self._moving_average(baseline, self.enhanced_config['baseline_smoothing'])
            
            # Quality assessment
            quality = self._assess_baseline_quality(currents, baseline)
            
            metadata = {
                'processing_time': time.time() - start_time,
                'segments_found': len(segments),
                'baseline_segments_used': len(baseline_segments),
                'quality_metrics': quality,
                'fallback_used': False
            }
            
            logger.info(f"✅ Enhanced baseline: {len(segments)} segments, quality: {quality['overall_quality']:.2f}")
            
            return baseline, metadata
            
        except Exception as e:
            logger.error(f"Enhanced baseline failed: {e}, using traditional fallback")
            baseline = self._traditional_baseline(currents)
            metadata = {
                'processing_time': time.time() - start_time,
                'fallback_used': True,
                'error': str(e),
                'quality_metrics': {'overall_quality': 0.5}
            }
            return baseline, metadata
    
    def _detect_linear_segments(self, voltages: np.ndarray, currents: np.ndarray) -> List[Dict]:
        """🔍 Detect linear segments in the data"""
        
        segments = []
        window = self.enhanced_config['base_window']
        min_length = self.enhanced_config['segment_min_length']
        
        for i in range(0, len(currents) - window, window // 2):
            end_idx = min(i + window, len(currents))
            
            if end_idx - i < min_length:
                continue
            
            segment_voltages = voltages[i:end_idx]
            segment_currents = currents[i:end_idx]
            
            # Linear fit quality
            try:
                coeffs = np.polyfit(segment_voltages, segment_currents, 1)
                fit_currents = np.polyval(coeffs, segment_voltages)
                r_squared = 1 - (np.sum((segment_currents - fit_currents) ** 2) / 
                                np.sum((segment_currents - np.mean(segment_currents)) ** 2))
                
                if r_squared > 0.7:  # Good linear fit
                    segments.append({
                        'start_idx': i,
                        'end_idx': end_idx,
                        'coeffs': coeffs,
                        'r_squared': r_squared,
                        'stability': 1.0 / (1.0 + np.std(segment_currents)),
                        'mean_current': np.mean(segment_currents)
                    })
            except:
                continue
        
        return segments
    
    def _select_baseline_segments(self, segments: List[Dict], voltages: np.ndarray, 
                                currents: np.ndarray) -> List[Dict]:
        """🎯 Select best segments for baseline construction"""
        
        if not segments:
            return []
        
        # Score segments based on multiple criteria
        for segment in segments:
            score = 0.0
            
            # R-squared contribution
            score += segment['r_squared'] * 0.4
            
            # Stability contribution
            score += segment['stability'] * 0.3
            
            # Distance from peaks (prefer segments away from peaks)
            segment_center = (segment['start_idx'] + segment['end_idx']) // 2
            peak_distance = self._distance_from_nearest_peak(segment_center, currents)
            score += min(peak_distance / 50.0, 1.0) * 0.3
            
            segment['score'] = score
        
        # Sort by score and select top segments
        segments_sorted = sorted(segments, key=lambda s: s['score'], reverse=True)
        
        # Select top segments covering different regions
        selected = []
        coverage = np.zeros(len(currents), dtype=bool)
        
        for segment in segments_sorted:
            start, end = segment['start_idx'], segment['end_idx']
            
            # Check if this segment adds new coverage
            if np.sum(coverage[start:end]) < 0.5 * (end - start):
                selected.append(segment)
                coverage[start:end] = True
                
                if len(selected) >= 5:  # Limit number of segments
                    break
        
        return selected
    
    def _distance_from_nearest_peak(self, index: int, currents: np.ndarray) -> float:
        """📏 Calculate distance from nearest peak"""
        
        # Simple peak detection
        current_abs = np.abs(currents)
        local_max = np.max(current_abs)
        
        # Find points with high current (potential peaks)
        peak_threshold = 0.3 * local_max
        peak_candidates = np.where(current_abs > peak_threshold)[0]
        
        if len(peak_candidates) == 0:
            return 100.0  # No peaks, large distance
        
        # Find minimum distance to any peak candidate
        distances = np.abs(peak_candidates - index)
        return np.min(distances)
    
    def _interpolate_baseline(self, baseline_segments: List[Dict], data_length: int) -> np.ndarray:
        """🎯 Interpolate baseline from selected segments"""
        
        if not baseline_segments:
            return np.zeros(data_length)
        
        baseline = np.zeros(data_length)
        weights = np.zeros(data_length)
        
        # Fill baseline using segment information
        for segment in baseline_segments:
            start, end = segment['start_idx'], segment['end_idx']
            mean_current = segment['mean_current']
            weight = segment['score']
            
            baseline[start:end] += mean_current * weight
            weights[start:end] += weight
        
        # Normalize by weights
        mask = weights > 0
        baseline[mask] /= weights[mask]
        
        # Interpolate gaps
        if np.sum(mask) > 1:
            from scipy import interpolate
            try:
                indices = np.arange(data_length)
                f = interpolate.interp1d(indices[mask], baseline[mask], 
                                       kind='linear', fill_value='extrapolate')
                baseline = f(indices)
            except ImportError:
                # Fallback linear interpolation
                baseline = self._simple_interpolate(baseline, mask)
        
        return baseline
    
    def _simple_interpolate(self, baseline: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Simple linear interpolation fallback"""
        
        result = baseline.copy()
        indices = np.arange(len(baseline))
        
        if np.sum(mask) < 2:
            return result
        
        # Simple linear interpolation
        valid_indices = indices[mask]
        valid_values = baseline[mask]
        
        for i in range(len(result)):
            if not mask[i]:
                # Find nearest valid points
                left_idx = valid_indices[valid_indices <= i]
                right_idx = valid_indices[valid_indices > i]
                
                if len(left_idx) > 0 and len(right_idx) > 0:
                    # Interpolate between nearest points
                    left_i = left_idx[-1]
                    right_i = right_idx[0]
                    left_val = baseline[left_i]
                    right_val = baseline[right_i]
                    
                    # Linear interpolation
                    ratio = (i - left_i) / (right_i - left_i)
                    result[i] = left_val + ratio * (right_val - left_val)
                elif len(left_idx) > 0:
                    result[i] = baseline[left_idx[-1]]
                elif len(right_idx) > 0:
                    result[i] = baseline[right_idx[0]]
        
        return result
    
    def _assess_baseline_quality(self, currents: np.ndarray, baseline: np.ndarray) -> Dict:
        """📊 Assess baseline quality metrics"""
        
        # Calculate corrected current
        corrected = currents - baseline
        
        # Quality metrics
        baseline_smoothness = 1.0 / (1.0 + np.std(np.diff(baseline)))
        signal_improvement = np.std(currents) / np.std(corrected) if np.std(corrected) > 0 else 1.0
        
        # Overall quality score
        overall_quality = min((baseline_smoothness * 0.5 + 
                             min(signal_improvement / 2.0, 1.0) * 0.5), 1.0)
        
        return {
            'overall_quality': overall_quality,
            'baseline_smoothness': baseline_smoothness,
            'signal_improvement': signal_improvement,
            'baseline_std': np.std(baseline),
            'corrected_std': np.std(corrected)
        }
    
    def _moving_average(self, data: np.ndarray, window: int) -> np.ndarray:
        """📈 Compute moving average with consistent output size"""
        
        if window >= len(data):
            return np.full_like(data, np.mean(data))
        
        if window < 3:
            return data.copy()
        
        # Ensure window is odd for symmetric padding
        if window % 2 == 0:
            window += 1
        
        # Simple moving average without changing array size
        result = np.copy(data)
        half_window = window // 2
        
        for i in range(len(data)):
            start = max(0, i - half_window)
            end = min(len(data), i + half_window + 1)
            result[i] = np.mean(data[start:end])
        
        return result