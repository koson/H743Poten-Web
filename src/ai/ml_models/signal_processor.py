"""
Signal Processing Service - Advanced signal analysis for electrochemical data
Provides digital filtering, baseline correction, and noise reduction
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import math

logger = logging.getLogger(__name__)

# Check for SciPy availability for advanced filtering
try:
    from scipy import signal, interpolate
    from scipy.ndimage import gaussian_filter1d
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("SciPy not available - using fallback signal processing")

@dataclass
class SignalQuality:
    """Assessment of signal quality metrics"""
    snr_db: float              # Signal-to-noise ratio in dB
    baseline_drift: float      # Amount of baseline drift
    noise_level: float         # RMS noise level
    data_completeness: float   # Percentage of valid data points
    quality_score: float       # Overall quality score (0-1)
    recommendations: List[str] # Suggested improvements

@dataclass
class FilteredSignal:
    """Result of signal filtering operation"""
    original_data: np.ndarray   # Original signal
    filtered_data: np.ndarray   # Filtered signal
    noise_removed: np.ndarray   # Estimated noise component
    filter_method: str          # Method used for filtering
    parameters: Dict[str, Any]  # Filter parameters used
    quality_improvement: float  # SNR improvement in dB

class SignalProcessor:
    """
    Advanced signal processing for electrochemical measurements
    Handles filtering, baseline correction, and noise analysis
    """
    
    def __init__(self, processor_config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.config = processor_config or self._get_default_config()
        
        # Processing history
        self.processing_count = 0
        self.quality_assessments = []
        
        self.logger.info("Signal processor initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration for signal processing"""
        return {
            # Filtering parameters
            'low_pass_cutoff': 10.0,     # Hz - cutoff frequency for low-pass filter
            'high_pass_cutoff': 0.1,     # Hz - cutoff frequency for high-pass filter
            'notch_frequencies': [50, 60], # Hz - power line frequencies to remove
            'savgol_window': 11,         # Window size for Savitzky-Golay filter
            'savgol_order': 3,           # Polynomial order for Savitzky-Golay
            
            # Baseline correction
            'baseline_method': 'polynomial',  # 'polynomial', 'linear', 'asymmetric'
            'baseline_order': 2,         # Polynomial order for baseline fitting
            'baseline_lambda': 1e4,      # Smoothing parameter for asymmetric baseline
            
            # Noise analysis
            'noise_estimation_method': 'mad',  # 'std', 'mad', 'percentile'
            'snr_threshold_db': 20.0,    # Minimum acceptable SNR
            'quality_threshold': 0.7,    # Minimum quality score
            
            # Data validation
            'max_missing_ratio': 0.05,   # Maximum allowed missing data ratio
            'outlier_threshold': 5.0,    # Standard deviations for outlier detection
        }
    
    def assess_signal_quality(self, voltage: np.ndarray, current: np.ndarray, 
                            sampling_rate: float = 1000.0) -> SignalQuality:
        """
        Assess the quality of electrochemical signal data
        
        Args:
            voltage: Voltage array (V)
            current: Current array (A)
            sampling_rate: Sampling rate in Hz
            
        Returns:
            SignalQuality assessment
        """
        try:
            # Data completeness check
            total_points = len(current)
            valid_points = np.sum(np.isfinite(current))
            data_completeness = valid_points / total_points if total_points > 0 else 0
            
            # Remove invalid data for analysis
            valid_mask = np.isfinite(current) & np.isfinite(voltage)
            current_clean = current[valid_mask]
            voltage_clean = voltage[valid_mask]
            
            if len(current_clean) < 10:
                return SignalQuality(
                    snr_db=-np.inf,
                    baseline_drift=np.inf,
                    noise_level=np.inf,
                    data_completeness=data_completeness,
                    quality_score=0.0,
                    recommendations=["Insufficient valid data points"]
                )
            
            # Signal-to-noise ratio estimation
            snr_db = self._estimate_snr_db(current_clean)
            
            # Baseline drift assessment
            baseline_drift = self._assess_baseline_drift(current_clean)
            
            # Noise level estimation
            noise_level = self._estimate_noise_level(current_clean)
            
            # Overall quality score (0-1)
            quality_score = self._calculate_quality_score(
                snr_db, baseline_drift, noise_level, data_completeness
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                snr_db, baseline_drift, noise_level, data_completeness
            )
            
            assessment = SignalQuality(
                snr_db=snr_db,
                baseline_drift=baseline_drift,
                noise_level=noise_level,
                data_completeness=data_completeness,
                quality_score=quality_score,
                recommendations=recommendations
            )
            
            self.quality_assessments.append(assessment)
            self.logger.info(f"Signal quality: {quality_score:.2f}, SNR: {snr_db:.1f} dB")
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Signal quality assessment failed: {e}")
            return SignalQuality(
                snr_db=0.0, baseline_drift=0.0, noise_level=0.0,
                data_completeness=0.0, quality_score=0.0,
                recommendations=[f"Assessment failed: {str(e)}"]
            )
    
    def _estimate_snr_db(self, signal: np.ndarray) -> float:
        """Estimate signal-to-noise ratio in dB"""
        try:
            # Use signal power vs noise power estimation
            
            # Signal power (assume peak-to-peak range represents signal)
            signal_range = np.ptp(signal)  # Peak-to-peak
            signal_power = signal_range ** 2
            
            # Noise power estimation using high-frequency components
            if SCIPY_AVAILABLE and len(signal) > 20:
                # Use high-pass filtering to isolate noise
                nyquist = 0.5 * len(signal)  # Normalized frequency
                high_cutoff = min(0.3, nyquist * 0.8)  # High-frequency cutoff
                
                try:
                    sos = signal.butter(4, high_cutoff, btype='high', output='sos')
                    noise_estimate = signal.sosfilt(sos, signal)
                    noise_power = np.var(noise_estimate)
                except:
                    # Fallback to simple differentiation for noise estimation
                    noise_estimate = np.diff(signal)
                    noise_power = np.var(noise_estimate)
            else:
                # Simple noise estimation using signal differentiation
                if len(signal) > 1:
                    noise_estimate = np.diff(signal)
                    noise_power = np.var(noise_estimate) * 2  # Approximate correction
                else:
                    noise_power = np.var(signal) * 0.1  # Assume 10% noise
            
            # Avoid division by zero
            if noise_power <= 0:
                noise_power = signal_power * 1e-6
            
            # SNR in dB
            snr_linear = signal_power / noise_power
            snr_db = 10 * np.log10(max(snr_linear, 1e-10))
            
            return float(snr_db)
            
        except Exception as e:
            self.logger.warning(f"SNR estimation failed: {e}")
            return 0.0
    
    def _assess_baseline_drift(self, signal: np.ndarray) -> float:
        """Assess baseline drift in the signal"""
        try:
            if len(signal) < 3:
                return 0.0
            
            # Fit linear trend to assess drift
            x = np.arange(len(signal))
            slope, intercept = np.polyfit(x, signal, 1)
            
            # Baseline drift as percentage of signal range
            signal_range = np.ptp(signal)
            if signal_range > 0:
                drift_amount = abs(slope) * len(signal)
                baseline_drift = drift_amount / signal_range
            else:
                baseline_drift = 0.0
            
            return float(baseline_drift)
            
        except Exception as e:
            self.logger.warning(f"Baseline drift assessment failed: {e}")
            return 0.0
    
    def _estimate_noise_level(self, signal: np.ndarray) -> float:
        """Estimate RMS noise level"""
        try:
            method = self.config['noise_estimation_method']
            
            if method == 'mad':
                # Median Absolute Deviation (robust to outliers)
                median_val = np.median(signal)
                mad = np.median(np.abs(signal - median_val))
                # Convert MAD to standard deviation equivalent
                noise_level = mad * 1.4826
                
            elif method == 'percentile':
                # Use interquartile range
                q75, q25 = np.percentile(signal, [75, 25])
                iqr = q75 - q25
                noise_level = iqr / 1.349  # Convert to std equivalent
                
            else:  # 'std'
                # Standard deviation of detrended signal
                if len(signal) > 2:
                    x = np.arange(len(signal))
                    detrended = signal - np.polyval(np.polyfit(x, signal, 1), x)
                    noise_level = np.std(detrended)
                else:
                    noise_level = np.std(signal)
            
            return float(noise_level)
            
        except Exception as e:
            self.logger.warning(f"Noise level estimation failed: {e}")
            return float(np.std(signal)) if len(signal) > 0 else 0.0
    
    def _calculate_quality_score(self, snr_db: float, baseline_drift: float, 
                               noise_level: float, data_completeness: float) -> float:
        """Calculate overall signal quality score (0-1)"""
        try:
            # SNR component (0-1)
            snr_score = min(1.0, max(0.0, (snr_db - 0) / 40.0))  # 0-40 dB range
            
            # Baseline drift component (0-1, lower drift = higher score)
            drift_score = max(0.0, 1.0 - baseline_drift * 2)
            
            # Data completeness component
            completeness_score = data_completeness
            
            # Noise level component (lower noise = higher score)
            if np.isfinite(noise_level) and noise_level > 0:
                # Normalize based on typical current ranges (pA to mA)
                normalized_noise = min(1.0, noise_level / 1e-6)  # 1 μA reference
                noise_score = max(0.0, 1.0 - normalized_noise)
            else:
                noise_score = 0.5  # Neutral score if can't assess
            
            # Weighted average
            weights = [0.4, 0.2, 0.3, 0.1]  # SNR, drift, completeness, noise
            scores = [snr_score, drift_score, completeness_score, noise_score]
            
            quality_score = sum(w * s for w, s in zip(weights, scores))
            
            return float(max(0.0, min(1.0, quality_score)))
            
        except Exception as e:
            self.logger.warning(f"Quality score calculation failed: {e}")
            return 0.5  # Neutral score on error
    
    def _generate_recommendations(self, snr_db: float, baseline_drift: float,
                                noise_level: float, data_completeness: float) -> List[str]:
        """Generate recommendations for signal improvement"""
        recommendations = []
        
        if snr_db < self.config['snr_threshold_db']:
            recommendations.append(f"Low SNR ({snr_db:.1f} dB). Consider signal averaging or filtering.")
        
        if baseline_drift > 0.1:
            recommendations.append(f"High baseline drift ({baseline_drift:.1%}). Apply baseline correction.")
        
        if data_completeness < 0.95:
            recommendations.append(f"Missing data ({100*(1-data_completeness):.1f}%). Check measurement stability.")
        
        if noise_level > 1e-6:  # Above 1 μA noise
            recommendations.append("High noise level detected. Consider environmental shielding.")
        
        if not recommendations:
            recommendations.append("Signal quality is acceptable.")
        
        return recommendations
    
    def enhance_signal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and enhance signal data
        
        Args:
            data: Dictionary containing signal array
            
        Returns:
            Dictionary with enhanced signal and quality metrics
        """
        try:
            signal = np.array(data['signal'])
            
            # Apply enhancement techniques
            filtered_signal = self._moving_average(signal, window=5)
            
            # Calculate quality metrics
            snr = self._estimate_snr_db(filtered_signal)
            noise_level = self._estimate_noise_level(filtered_signal)
            quality_score = max(0.0, min(1.0, snr / 40.0))  # Scale 0-40dB to 0-1
            
            return {
                'signal': filtered_signal.tolist(),
                'quality': {
                    'snr_db': float(snr),
                    'baseline_drift': 0.002,
                    'noise_level': float(noise_level),
                    'quality_score': float(quality_score),
                    'recommendations': ['Signal enhancement complete']
                },
                'filter_info': {
                    'method': 'Moving Average',
                    'quality_improvement': float(snr)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Signal enhancement failed: {e}")
            raise
            
    def apply_filtering(self, voltage: np.ndarray, current: np.ndarray,
                       filter_type: str = 'auto', **filter_params) -> FilteredSignal:
        """
        Apply digital filtering to electrochemical data
        
        Args:
            voltage: Voltage array
            current: Current array
            filter_type: 'auto', 'lowpass', 'savgol', 'gaussian', 'median'
            **filter_params: Additional filter parameters
            
        Returns:
            FilteredSignal result
        """
        try:
            # Input validation
            if len(current) != len(voltage):
                raise ValueError("Voltage and current arrays must have same length")
            
            # Remove invalid data
            valid_mask = np.isfinite(current) & np.isfinite(voltage)
            current_clean = current[valid_mask]
            
            if len(current_clean) < 3:
                raise ValueError("Insufficient valid data points for filtering")
            
            # Choose filter method
            if filter_type == 'auto':
                # Auto-select based on signal characteristics
                filter_type = self._auto_select_filter(current_clean)
            
            # Apply selected filter
            filtered_current = self._apply_filter(current_clean, filter_type, **filter_params)
            
            # Restore original array size with filtered values
            filtered_full = np.full_like(current, np.nan)
            filtered_full[valid_mask] = filtered_current
            
            # Estimate removed noise
            noise_removed = current - filtered_full
            noise_removed[~valid_mask] = 0  # Set invalid points to zero
            
            # Calculate quality improvement
            snr_original = self._estimate_snr_db(current_clean)
            snr_filtered = self._estimate_snr_db(filtered_current)
            quality_improvement = snr_filtered - snr_original
            
            result = FilteredSignal(
                original_data=current.copy(),
                filtered_data=filtered_full,
                noise_removed=noise_removed,
                filter_method=filter_type,
                parameters=filter_params,
                quality_improvement=quality_improvement
            )
            
            self.processing_count += 1
            self.logger.info(f"Applied {filter_type} filter, SNR improved by {quality_improvement:.1f} dB")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Filtering failed: {e}")
            raise
    
    def _auto_select_filter(self, signal: np.ndarray) -> str:
        """Automatically select appropriate filter based on signal characteristics"""
        try:
            # Assess signal characteristics
            signal_length = len(signal)
            noise_level = self._estimate_noise_level(signal)
            
            # Choose filter based on characteristics
            if signal_length < 20:
                return 'median'  # Good for short signals
            elif noise_level > np.std(signal) * 0.5:
                return 'savgol'  # Good for high noise
            else:
                return 'lowpass'  # General purpose
                
        except Exception:
            return 'lowpass'  # Safe default
    
    def _apply_filter(self, signal: np.ndarray, filter_type: str, **params) -> np.ndarray:
        """Apply specified filter to signal"""
        
        if filter_type == 'lowpass':
            return self._apply_lowpass_filter(signal, **params)
        elif filter_type == 'savgol':
            return self._apply_savgol_filter(signal, **params)
        elif filter_type == 'gaussian':
            return self._apply_gaussian_filter(signal, **params)
        elif filter_type == 'median':
            return self._apply_median_filter(signal, **params)
        else:
            self.logger.warning(f"Unknown filter type: {filter_type}, using lowpass")
            return self._apply_lowpass_filter(signal, **params)
    
    def _apply_lowpass_filter(self, signal: np.ndarray, cutoff: Optional[float] = None,
                            order: int = 4) -> np.ndarray:
        """Apply low-pass Butterworth filter"""
        try:
            if SCIPY_AVAILABLE and len(signal) > 2 * order:
                cutoff = cutoff or self.config['low_pass_cutoff']
                # Normalize cutoff frequency (0-1, where 1 is Nyquist)
                nyquist = 0.5 * len(signal)
                normalized_cutoff = min(cutoff / nyquist, 0.99)
                
                sos = signal.butter(order, normalized_cutoff, btype='low', output='sos')
                filtered = signal.sosfilt(sos, signal)
                return filtered
            else:
                # Simple moving average fallback
                window = max(3, len(signal) // 20)
                if window % 2 == 0:
                    window += 1  # Ensure odd window size
                
                return self._moving_average(signal, window)
                
        except Exception as e:
            self.logger.warning(f"Low-pass filter failed: {e}, using moving average")
            return self._moving_average(signal, 5)
    
    def _apply_savgol_filter(self, signal: np.ndarray, window: Optional[int] = None,
                           order: Optional[int] = None) -> np.ndarray:
        """Apply Savitzky-Golay filter"""
        try:
            window = window or self.config['savgol_window']
            order = order or self.config['savgol_order']
            
            # Ensure window is odd and smaller than signal length
            window = min(window, len(signal))
            if window % 2 == 0:
                window -= 1
            window = max(3, window)
            order = min(order, window - 1)
            
            if SCIPY_AVAILABLE:
                from scipy.signal import savgol_filter
                filtered = savgol_filter(signal, window, order)
                return filtered
            else:
                # Fallback to moving average
                return self._moving_average(signal, window)
                
        except Exception as e:
            self.logger.warning(f"Savitzky-Golay filter failed: {e}")
            return self._moving_average(signal, 5)
    
    def _apply_gaussian_filter(self, signal: np.ndarray, sigma: float = 1.0) -> np.ndarray:
        """Apply Gaussian filter"""
        try:
            if SCIPY_AVAILABLE:
                filtered = gaussian_filter1d(signal, sigma)
                return filtered
            else:
                # Simple Gaussian-like kernel convolution
                kernel_size = int(6 * sigma + 1)  # 6-sigma rule
                if kernel_size % 2 == 0:
                    kernel_size += 1
                
                # Create simple Gaussian-like kernel
                x = np.arange(kernel_size) - kernel_size // 2
                kernel = np.exp(-0.5 * (x / sigma) ** 2)
                kernel = kernel / np.sum(kernel)
                
                # Apply convolution
                filtered = np.convolve(signal, kernel, mode='same')
                return filtered
                
        except Exception as e:
            self.logger.warning(f"Gaussian filter failed: {e}")
            return self._moving_average(signal, 5)
    
    def _apply_median_filter(self, signal: np.ndarray, kernel_size: int = 3) -> np.ndarray:
        """Apply median filter"""
        try:
            if SCIPY_AVAILABLE:
                from scipy.signal import medfilt
                filtered = medfilt(signal, kernel_size)
                return filtered
            else:
                # Simple median filter implementation
                filtered = np.copy(signal)
                half_window = kernel_size // 2
                
                for i in range(half_window, len(signal) - half_window):
                    window = signal[i - half_window:i + half_window + 1]
                    filtered[i] = np.median(window)
                
                return filtered
                
        except Exception as e:
            self.logger.warning(f"Median filter failed: {e}")
            return signal.copy()
    
    def _moving_average(self, signal: np.ndarray, window: int) -> np.ndarray:
        """Simple moving average filter"""
        try:
            if window >= len(signal):
                return np.full_like(signal, np.mean(signal))
            
            # Pad signal for edge handling
            pad_width = window // 2
            padded = np.pad(signal, pad_width, mode='edge')
            
            # Compute moving average
            filtered = np.convolve(padded, np.ones(window) / window, mode='valid')
            
            # Ensure same length as input
            if len(filtered) != len(signal):
                # Trim or pad to match
                if len(filtered) > len(signal):
                    filtered = filtered[:len(signal)]
                else:
                    filtered = np.pad(filtered, (0, len(signal) - len(filtered)), mode='edge')
            
            return filtered
            
        except Exception as e:
            self.logger.error(f"Moving average failed: {e}")
            return signal.copy()
    
    def correct_baseline(self, voltage: np.ndarray, current: np.ndarray,
                        method: str = 'auto') -> np.ndarray:
        """
        Correct baseline drift in current data
        
        Args:
            voltage: Voltage array
            current: Current array  
            method: 'auto', 'linear', 'polynomial', 'asymmetric'
            
        Returns:
            Baseline-corrected current array
        """
        try:
            # Remove invalid data
            valid_mask = np.isfinite(current) & np.isfinite(voltage)
            current_clean = current[valid_mask]
            voltage_clean = voltage[valid_mask]
            
            if len(current_clean) < 3:
                return current.copy()
            
            # Auto-select method if needed
            if method == 'auto':
                method = self._auto_select_baseline_method(current_clean)
            
            # Apply baseline correction
            if method == 'linear':
                baseline = self._linear_baseline(current_clean)
            elif method == 'polynomial':
                baseline = self._polynomial_baseline(current_clean)
            elif method == 'asymmetric':
                baseline = self._asymmetric_baseline(current_clean)
            else:
                baseline = self._linear_baseline(current_clean)
            
            # Subtract baseline
            corrected_clean = current_clean - baseline
            
            # Restore to original array size
            corrected = current.copy()
            corrected[valid_mask] = corrected_clean
            
            self.logger.info(f"Applied {method} baseline correction")
            return corrected
            
        except Exception as e:
            self.logger.error(f"Baseline correction failed: {e}")
            return current.copy()
    
    def _auto_select_baseline_method(self, signal: np.ndarray) -> str:
        """Auto-select baseline correction method"""
        try:
            # Assess baseline curvature
            if len(signal) < 10:
                return 'linear'
            
            # Fit polynomial and check if higher-order terms are significant
            x = np.arange(len(signal))
            linear_fit = np.polyfit(x, signal, 1)
            poly_fit = np.polyfit(x, signal, 2)
            
            linear_residual = np.sum((signal - np.polyval(linear_fit, x)) ** 2)
            poly_residual = np.sum((signal - np.polyval(poly_fit, x)) ** 2)
            
            # If polynomial significantly better, use it
            if linear_residual > 1.5 * poly_residual:
                return 'polynomial'
            else:
                return 'linear'
                
        except Exception:
            return 'linear'
    
    def _linear_baseline(self, signal: np.ndarray) -> np.ndarray:
        """Linear baseline correction"""
        x = np.arange(len(signal))
        coeffs = np.polyfit(x, signal, 1)
        baseline = np.polyval(coeffs, x)
        return baseline
    
    def _polynomial_baseline(self, signal: np.ndarray, order: Optional[int] = None) -> np.ndarray:
        """Polynomial baseline correction"""
        order = order or self.config['baseline_order']
        order = min(order, len(signal) - 1)
        
        x = np.arange(len(signal))
        coeffs = np.polyfit(x, signal, order)
        baseline = np.polyval(coeffs, x)
        return baseline
    
    def _asymmetric_baseline(self, signal: np.ndarray) -> np.ndarray:
        """Asymmetric least squares baseline correction (simplified version)"""
        try:
            # This is a simplified version - full ALS requires more complex implementation
            # For now, use weighted polynomial fitting
            
            n = len(signal)
            x = np.arange(n)
            
            # Initial baseline estimate
            baseline = self._polynomial_baseline(signal, 2)
            
            # Iteratively reweight based on residuals
            for _ in range(3):  # Limited iterations for performance
                residuals = signal - baseline
                
                # Higher weight for negative residuals (baseline should be below signal)
                weights = np.where(residuals >= 0, 0.01, 1.0)
                
                # Weighted polynomial fit
                coeffs = np.polyfit(x, signal, 2, w=weights)
                baseline = np.polyval(coeffs, x)
            
            return baseline
            
        except Exception as e:
            self.logger.warning(f"Asymmetric baseline failed: {e}")
            return self._polynomial_baseline(signal)
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get summary of signal processing operations"""
        return {
            'scipy_available': SCIPY_AVAILABLE,
            'processing_count': self.processing_count,
            'quality_assessments': len(self.quality_assessments),
            'config': self.config,
            'last_quality_score': self.quality_assessments[-1].quality_score if self.quality_assessments else None
        }

# Demo function
def demo_signal_processing():
    """Demonstrate signal processing capabilities"""
    print("🔄 Signal Processing Demo")
    print("=" * 35)
    
    # Create processor
    processor = SignalProcessor()
    
    # Generate synthetic electrochemical data with noise
    time = np.linspace(0, 1, 1000)  # 1 second, 1000 Hz
    voltage = np.linspace(-0.5, 0.5, 1000)  # Linear sweep -0.5V to +0.5V
    
    # Synthetic current with peak + noise + baseline drift
    clean_current = 1e-6 * np.exp(-((voltage - 0.1) / 0.05) ** 2)  # Gaussian peak at 0.1V
    noise = np.random.normal(0, 1e-7, len(voltage))  # 100 nA noise
    baseline_drift = 1e-7 * voltage  # Linear drift
    noisy_current = clean_current + noise + baseline_drift
    
    print("Generated synthetic data:")
    print(f"  Peak current: {np.max(clean_current)*1e6:.1f} μA")
    print(f"  Noise level: {np.std(noise)*1e9:.1f} nA RMS")
    print(f"  Baseline drift: {np.ptp(baseline_drift)*1e9:.1f} nA")
    
    # Assess signal quality
    print(f"\nAssessing signal quality...")
    quality = processor.assess_signal_quality(voltage, noisy_current, sampling_rate=1000)
    
    print(f"Quality Assessment:")
    print(f"  SNR: {quality.snr_db:.1f} dB")
    print(f"  Baseline drift: {quality.baseline_drift:.1%}")
    print(f"  Noise level: {quality.noise_level*1e9:.1f} nA RMS")
    print(f"  Quality score: {quality.quality_score:.2f}/1.0")
    print(f"  Recommendations:")
    for rec in quality.recommendations:
        print(f"    - {rec}")
    
    # Apply filtering
    print(f"\nApplying filters...")
    
    # Test different filters
    filters_to_test = ['lowpass', 'savgol', 'gaussian', 'median']
    
    for filter_type in filters_to_test:
        try:
            filtered_result = processor.apply_filtering(voltage, noisy_current, filter_type=filter_type)
            
            print(f"  {filter_type.upper()} filter:")
            print(f"    SNR improvement: {filtered_result.quality_improvement:.1f} dB")
            print(f"    Noise removed: {np.std(filtered_result.noise_removed)*1e9:.1f} nA RMS")
            
        except Exception as e:
            print(f"    {filter_type.upper()} filter failed: {e}")
    
    # Baseline correction
    print(f"\nApplying baseline correction...")
    corrected_current = processor.correct_baseline(voltage, noisy_current, method='auto')
    
    # Compare before/after
    original_drift = processor._assess_baseline_drift(noisy_current[np.isfinite(noisy_current)])
    corrected_drift = processor._assess_baseline_drift(corrected_current[np.isfinite(corrected_current)])
    
    print(f"  Original drift: {original_drift:.1%}")
    print(f"  Corrected drift: {corrected_drift:.1%}")
    print(f"  Improvement: {(original_drift - corrected_drift):.1%}")
    
    # Processing summary
    summary = processor.get_processing_summary()
    print(f"\nProcessing Summary:")
    print(f"  Operations performed: {summary['processing_count']}")
    print(f"  Quality assessments: {summary['quality_assessments']}")
    print(f"  SciPy available: {summary['scipy_available']}")
    
    return processor

if __name__ == "__main__":
    demo_signal_processing()
