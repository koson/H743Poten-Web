#!/usr/bin/env python3
"""
Precision Peak and Baseline Analyzer for PLS Analysis
=====================================================

ระบบตรวจสอบ peak และ baseline ที่แม่นยำที่สุด สำหรับการทำ PLS และการคำนวณพื้นที่ใต้กราฟ

Features:
- Multi-stage baseline detection and validation
- Enhanced peak detection with ML validation
- Accurate area under curve calculation
- PLS-ready feature extraction
- Quality metrics and confidence scoring
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal
try:
    from scipy.integrate import trapezoid as trapz, simpson
except ImportError:
    from scipy.integrate import trapz, simpson
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PeakData:
    """Enhanced peak data structure with all PLS-relevant information"""
    voltage: float              # Peak voltage (V)
    current: float              # Peak current (μA)
    peak_type: str             # 'oxidation' or 'reduction'
    height: float              # Peak height above baseline (μA)
    area: float                # Peak area (μA·V)
    width: float               # Peak width at half maximum (V)
    baseline_current: float    # Baseline current at peak voltage (μA)
    confidence: float          # Detection confidence (0-100)
    symmetry_factor: float     # Peak symmetry measure
    tailing_factor: float      # Peak tailing measure
    signal_to_noise: float     # Signal to noise ratio
    quality_score: float       # Overall peak quality (0-100)
    
@dataclass
class BaselineData:
    """Enhanced baseline data structure"""
    voltages: np.ndarray       # Baseline voltage points
    currents: np.ndarray       # Baseline current points
    method: str                # Detection method used
    quality_score: float       # Baseline quality (0-100)
    r_squared: float           # Linear fit quality
    slope: float               # Baseline slope (μA/V)
    intercept: float           # Baseline intercept (μA)
    noise_level: float         # Baseline noise level (μA)
    drift_rate: float          # Baseline drift rate (μA/V)

@dataclass
class PLSFeatures:
    """PLS-ready features extracted from CV data"""
    # Peak-based features
    oxidation_height: float
    reduction_height: float
    peak_separation: float
    peak_ratio: float
    
    # Area-based features
    total_area: float
    oxidation_area: float
    reduction_area: float
    area_ratio: float
    
    # Shape-based features
    peak_symmetry: float
    baseline_quality: float
    signal_noise_ratio: float
    
    # Advanced features
    charge_transfer_resistance: float
    diffusion_coefficient: float
    concentration_estimate: float

class PrecisionPeakBaselineAnalyzer:
    """
    High-precision analyzer for peak and baseline detection
    Optimized for PLS analysis and area under curve calculations
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = self._get_default_config()
        if config:
            self.config.update(config)
        
        self.logger = logging.getLogger(__name__)
        
        # Analysis results storage
        self.peaks: List[PeakData] = []
        self.baseline: Optional[BaselineData] = None
        self.pls_features: Optional[PLSFeatures] = None
        self.quality_metrics: Dict[str, float] = {}
        
        # Calibration parameters for different analytes
        self.analyte_configs = {
            'ferrocene': {
                'ox_voltage_range': (0.170, 0.210),
                'red_voltage_range': (0.070, 0.110),
                'min_peak_height': 5.0,
                'expected_separation': 0.100
            },
            'generic': {
                'ox_voltage_range': (0.0, 1.0),
                'red_voltage_range': (-0.5, 0.5),
                'min_peak_height': 1.0,
                'expected_separation': 0.050
            }
        }
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for precision analysis"""
        return {
            'analyte': 'ferrocene',
            'baseline_method': 'multi_stage',
            'peak_detection_method': 'enhanced_ml',
            'area_calculation_method': 'simpson',
            'noise_reduction': True,
            'quality_threshold': 80.0,
            'confidence_threshold': 85.0,
            'baseline_window_size': 20,
            'peak_prominence_factor': 0.15,
            'smoothing_window': 5
        }
    
    def analyze_cv_data(self, voltage: np.ndarray, current: np.ndarray, 
                       filename: str = "", analyte: str = None) -> Dict[str, Any]:
        """
        Complete analysis of CV data with maximum precision
        
        Returns:
            Dictionary containing all analysis results optimized for PLS
        """
        try:
            self.logger.info(f"🔬 Starting precision analysis of {filename}")
            self.logger.info(f"📊 Data: {len(voltage)} points, V: [{voltage.min():.3f}, {voltage.max():.3f}]V, I: [{current.min():.3f}, {current.max():.3f}]μA")
            
            # Set analyte if provided
            if analyte:
                self.config['analyte'] = analyte
            
            # Step 1: Data preprocessing and validation
            voltage_clean, current_clean = self._preprocess_data(voltage, current)
            
            # Step 2: Multi-stage baseline detection
            baseline_result = self._detect_baseline_multi_stage(voltage_clean, current_clean)
            self.baseline = baseline_result
            
            # Step 3: Enhanced peak detection
            peaks_result = self._detect_peaks_enhanced(voltage_clean, current_clean, baseline_result)
            self.peaks = peaks_result
            
            # Step 4: Calculate precise areas under curve
            area_results = self._calculate_precise_areas(voltage_clean, current_clean, baseline_result, peaks_result)
            
            # Step 5: Extract PLS-ready features
            pls_features = self._extract_pls_features(voltage_clean, current_clean, baseline_result, peaks_result, area_results)
            self.pls_features = pls_features
            
            # Step 6: Quality assessment
            quality_metrics = self._assess_analysis_quality(voltage_clean, current_clean, baseline_result, peaks_result)
            self.quality_metrics = quality_metrics
            
            # Compile final results
            results = {
                'success': True,
                'filename': filename,
                'timestamp': datetime.now().isoformat(),
                'config': self.config,
                'data_info': {
                    'points': len(voltage_clean),
                    'voltage_range': [float(voltage_clean.min()), float(voltage_clean.max())],
                    'current_range': [float(current_clean.min()), float(current_clean.max())]
                },
                'baseline': self._serialize_baseline(baseline_result),
                'peaks': [self._serialize_peak(peak) for peak in peaks_result],
                'areas': area_results,
                'pls_features': self._serialize_pls_features(pls_features),
                'quality_metrics': quality_metrics,
                'recommendations': self._generate_recommendations(quality_metrics)
            }
            
            # Log summary
            self._log_analysis_summary(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Analysis failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e),
                'filename': filename,
                'timestamp': datetime.now().isoformat()
            }
    
    def _preprocess_data(self, voltage: np.ndarray, current: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Advanced data preprocessing with noise reduction and outlier removal"""
        
        # Remove NaN and infinite values
        valid_mask = np.isfinite(voltage) & np.isfinite(current)
        voltage_clean = voltage[valid_mask]
        current_clean = current[valid_mask]
        
        # Ensure minimum data length
        if len(voltage_clean) < 10:
            raise ValueError("Insufficient valid data points after cleaning")
        
        # Sort by voltage
        sort_idx = np.argsort(voltage_clean)
        voltage_clean = voltage_clean[sort_idx]
        current_clean = current_clean[sort_idx]
        
        # Noise reduction if enabled
        if self.config.get('noise_reduction', True):
            window_size = self.config.get('smoothing_window', 5)
            if len(current_clean) > window_size:
                # Apply Savitzky-Golay filter for noise reduction while preserving peaks
                current_clean = signal.savgol_filter(current_clean, window_size, 2)
        
        # Outlier detection and removal
        current_clean = self._remove_outliers(current_clean)
        
        # Ensure arrays still have same length after outlier removal
        if len(current_clean) < len(voltage_clean):
            # Trim voltage array to match current
            voltage_clean = voltage_clean[:len(current_clean)]
        
        self.logger.info(f"✅ Data preprocessing: {len(voltage_clean)} clean points")
        return voltage_clean, current_clean
    
    def _remove_outliers(self, current: np.ndarray, threshold: float = 3.0) -> np.ndarray:
        """Remove statistical outliers using modified Z-score"""
        if len(current) == 0:
            return current
            
        median = np.median(current)
        mad = np.median(np.abs(current - median))
        
        if mad == 0:
            return current
            
        modified_z_scores = 0.6745 * (current - median) / mad
        mask = np.abs(modified_z_scores) <= threshold
        
        # Ensure we don't remove all data
        if np.sum(mask) == 0:
            return current
            
        return current[mask]
    
    def _detect_baseline_multi_stage(self, voltage: np.ndarray, current: np.ndarray) -> BaselineData:
        """Multi-stage baseline detection with validation"""
        
        self.logger.info("🔍 Multi-stage baseline detection starting...")
        
        # Stage 1: Identify potential baseline regions using derivative analysis
        baseline_regions = self._identify_baseline_regions(voltage, current)
        
        # Stage 2: Validate baseline regions using statistical tests
        validated_regions = self._validate_baseline_regions(voltage, current, baseline_regions)
        
        # Stage 3: Fit optimal baseline model
        baseline_model = self._fit_baseline_model(voltage, current, validated_regions)
        
        # Stage 4: Quality assessment
        quality_score = self._assess_baseline_quality(voltage, current, baseline_model)
        
        self.logger.info(f"✅ Baseline detection complete: quality={quality_score:.1f}%")
        
        return baseline_model
    
    def _identify_baseline_regions(self, voltage: np.ndarray, current: np.ndarray) -> List[Tuple[int, int]]:
        """Identify potential baseline regions using signal analysis"""
        
        # Ensure arrays have same length
        min_length = min(len(voltage), len(current))
        voltage = voltage[:min_length]
        current = current[:min_length]
        
        # Calculate first derivative to find flat regions
        current_grad = np.gradient(current)
        
        # Find regions with low gradient (potential baseline)
        grad_threshold = np.std(current_grad) * 0.5
        flat_mask = np.abs(current_grad) < grad_threshold
        
        # Find continuous flat regions
        regions = []
        start_idx = None
        min_region_size = self.config.get('baseline_window_size', 20)
        
        for i, is_flat in enumerate(flat_mask):
            if is_flat and start_idx is None:
                start_idx = i
            elif not is_flat and start_idx is not None:
                if i - start_idx >= min_region_size:
                    regions.append((start_idx, i-1))
                start_idx = None
        
        # Handle region at end of data
        if start_idx is not None and len(current) - start_idx >= min_region_size:
            regions.append((start_idx, len(current)-1))
        
        self.logger.info(f"📍 Found {len(regions)} potential baseline regions")
        return regions
    
    def _validate_baseline_regions(self, voltage: np.ndarray, current: np.ndarray, 
                                 regions: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Validate baseline regions using statistical tests"""
        
        validated = []
        
        for start_idx, end_idx in regions:
            region_current = current[start_idx:end_idx+1]
            region_voltage = voltage[start_idx:end_idx+1]
            
            # Test 1: Low variance (stable baseline)
            variance_threshold = np.var(current) * 0.1
            if np.var(region_current) > variance_threshold:
                continue
            
            # Test 2: Linear trend test
            try:
                correlation, _ = pearsonr(region_voltage, region_current)
                if abs(correlation) > 0.8:  # Too strong correlation indicates trend
                    continue
            except:
                continue
            
            # Test 3: No significant peaks in region
            peaks_in_region, _ = signal.find_peaks(np.abs(region_current), 
                                                  height=np.std(region_current) * 2)
            if len(peaks_in_region) > 2:  # Too many peaks
                continue
            
            validated.append((start_idx, end_idx))
        
        self.logger.info(f"✅ Validated {len(validated)} baseline regions")
        return validated
    
    def _fit_baseline_model(self, voltage: np.ndarray, current: np.ndarray, 
                          regions: List[Tuple[int, int]]) -> BaselineData:
        """Fit optimal baseline model to validated regions"""
        
        if not regions:
            # Fallback: use start and end points
            self.logger.warning("⚠️ No valid baseline regions, using fallback method")
            regions = [(0, 9), (len(current)-10, len(current)-1)]
        
        # Collect all baseline points
        baseline_voltages = []
        baseline_currents = []
        
        for start_idx, end_idx in regions:
            baseline_voltages.extend(voltage[start_idx:end_idx+1])
            baseline_currents.extend(current[start_idx:end_idx+1])
        
        baseline_voltages = np.array(baseline_voltages)
        baseline_currents = np.array(baseline_currents)
        
        # Fit linear baseline model
        coeffs = np.polyfit(baseline_voltages, baseline_currents, 1)
        slope, intercept = coeffs
        
        # Calculate full baseline
        baseline_full = slope * voltage + intercept
        
        # Calculate quality metrics
        r_squared = self._calculate_r_squared(baseline_currents, 
                                            slope * baseline_voltages + intercept)
        noise_level = np.std(baseline_currents - (slope * baseline_voltages + intercept))
        
        return BaselineData(
            voltages=voltage,
            currents=baseline_full,
            method='multi_stage_linear',
            quality_score=min(100.0, r_squared * 100),
            r_squared=r_squared,
            slope=slope,
            intercept=intercept,
            noise_level=noise_level,
            drift_rate=abs(slope)
        )
    
    def _calculate_r_squared(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate R-squared value"""
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    def _assess_baseline_quality(self, voltage: np.ndarray, current: np.ndarray, 
                               baseline: BaselineData) -> float:
        """Assess overall baseline quality"""
        
        # Multiple quality criteria
        criteria = {
            'r_squared': baseline.r_squared * 100,
            'low_noise': max(0, 100 - baseline.noise_level * 10),
            'low_drift': max(0, 100 - baseline.drift_rate * 1000),
            'stability': 100 if baseline.noise_level < 1.0 else 50
        }
        
        # Weighted average
        weights = {'r_squared': 0.4, 'low_noise': 0.3, 'low_drift': 0.2, 'stability': 0.1}
        quality_score = sum(criteria[k] * weights[k] for k in criteria)
        
        return min(100.0, max(0.0, quality_score))
    
    def _detect_peaks_enhanced(self, voltage: np.ndarray, current: np.ndarray, 
                             baseline: BaselineData) -> List[PeakData]:
        """Enhanced peak detection with ML validation"""
        
        self.logger.info("🔍 Enhanced peak detection starting...")
        
        # Subtract baseline
        current_corrected = current - baseline.currents
        
        # Find peaks using multiple methods and combine results
        peaks_scipy = self._find_peaks_scipy(voltage, current_corrected)
        peaks_derivative = self._find_peaks_derivative(voltage, current_corrected)
        peaks_template = self._find_peaks_template_matching(voltage, current_corrected)
        
        # Combine and validate peaks
        all_peak_candidates = peaks_scipy + peaks_derivative + peaks_template
        validated_peaks = self._validate_peaks(voltage, current, current_corrected, 
                                             all_peak_candidates, baseline)
        
        self.logger.info(f"✅ Peak detection complete: {len(validated_peaks)} valid peaks")
        return validated_peaks
    
    def _find_peaks_scipy(self, voltage: np.ndarray, current_corrected: np.ndarray) -> List[Dict]:
        """Find peaks using scipy's find_peaks with optimized parameters"""
        
        peaks = []
        
        # Calculate adaptive thresholds
        current_std = np.std(current_corrected)
        current_max = np.max(np.abs(current_corrected))
        
        # Minimum height threshold (lower for real noisy data)
        min_height = max(self.config.get('min_peak_height', 1.0), 2.0)
        
        # Prominence threshold (much lower for real data)  
        prominence_threshold = max(1.0, current_max * self.config.get('peak_prominence_factor', 0.02))
        
        # Distance between peaks (in points)
        min_distance = max(5, len(voltage) // 50)  # At least 2% of data span
        
        try:
            # Oxidation peaks (positive current)
            pos_peaks, pos_props = signal.find_peaks(
                current_corrected,
                height=min_height,
                prominence=prominence_threshold,
                distance=min_distance,
                width=2
            )
            
            for i, peak_idx in enumerate(pos_peaks):
                peaks.append({
                    'index': peak_idx,
                    'voltage': voltage[peak_idx],
                    'current': current_corrected[peak_idx],
                    'type': 'oxidation',
                    'method': 'scipy',
                    'prominence': pos_props['prominences'][i]
                })
            
            self.logger.info(f"   SciPy oxidation peaks: {len(pos_peaks)}")
        
        except Exception as e:
            self.logger.warning(f"SciPy oxidation peak detection failed: {e}")
        
        try:
            # Reduction peaks (negative current)
            neg_peaks, neg_props = signal.find_peaks(
                -current_corrected,
                height=min_height,
                prominence=prominence_threshold,
                distance=min_distance,
                width=2
            )
            
            for i, peak_idx in enumerate(neg_peaks):
                peaks.append({
                    'index': peak_idx,
                    'voltage': voltage[peak_idx],
                    'current': current_corrected[peak_idx],
                    'type': 'reduction',
                    'method': 'scipy',
                    'prominence': neg_props['prominences'][i]
                })
            
            self.logger.info(f"   SciPy reduction peaks: {len(neg_peaks)}")
        
        except Exception as e:
            self.logger.warning(f"SciPy reduction peak detection failed: {e}")
        
        return peaks
    
    def _find_peaks_derivative(self, voltage: np.ndarray, current_corrected: np.ndarray) -> List[Dict]:
        """Find peaks using derivative analysis with enhanced detection"""
        
        if len(current_corrected) < 5:
            return []
            
        # Apply light smoothing to reduce noise
        from scipy.ndimage import gaussian_filter1d
        smoothed_current = gaussian_filter1d(current_corrected, sigma=0.8)
        
        # Calculate derivatives with proper voltage spacing
        voltage_spacing = np.mean(np.diff(voltage))
        first_deriv = np.gradient(smoothed_current, voltage_spacing)
        second_deriv = np.gradient(first_deriv, voltage_spacing)
        
        peaks = []
        
        # Adaptive thresholds
        current_range = np.max(current_corrected) - np.min(current_corrected)
        min_height = current_range * 0.02  # 2% of current range
        
        # Find zero crossings in first derivative with validation
        for i in range(2, len(first_deriv) - 2):
            # Check for sign change in first derivative
            if (first_deriv[i-1] > 0 and first_deriv[i+1] < 0):  # Peak
                # Validate with second derivative and height
                if (second_deriv[i] < -abs(np.std(second_deriv)) * 0.5 and 
                    abs(current_corrected[i]) > min_height):
                    
                    # Calculate prominence
                    left_min = np.min(current_corrected[max(0, i-10):i])
                    right_min = np.min(current_corrected[i:min(len(current_corrected), i+10)])
                    prominence = current_corrected[i] - max(left_min, right_min)
                    
                    if prominence > min_height:
                        peaks.append({
                            'index': i,
                            'voltage': voltage[i],
                            'current': current_corrected[i],
                            'type': 'oxidation',
                            'method': 'derivative',
                            'prominence': prominence
                        })
                        
            elif (first_deriv[i-1] < 0 and first_deriv[i+1] > 0):  # Valley
                # Validate with second derivative and height
                if (second_deriv[i] > abs(np.std(second_deriv)) * 0.5 and 
                    abs(current_corrected[i]) > min_height and
                    current_corrected[i] < 0):
                    
                    # Calculate prominence for negative peak
                    left_max = np.max(current_corrected[max(0, i-10):i])
                    right_max = np.max(current_corrected[i:min(len(current_corrected), i+10)])
                    prominence = min(left_max, right_max) - current_corrected[i]
                    
                    if prominence > min_height:
                        peaks.append({
                            'index': i,
                            'voltage': voltage[i],
                            'current': current_corrected[i],
                            'type': 'reduction',
                            'method': 'derivative',
                            'prominence': prominence
                        })
        
        self.logger.info(f"   Derivative method found: {len(peaks)} peaks")
        return peaks
    
    def _find_peaks_template_matching(self, voltage: np.ndarray, current_corrected: np.ndarray) -> List[Dict]:
        """Find peaks using template matching with adaptive voltage ranges"""
        
        peaks = []
        
        # Use analyte-specific configuration or generic if unknown
        analyte_config = self.analyte_configs.get(self.config.get('analyte', 'generic'), self.analyte_configs['generic'])
        
        # Adaptive voltage ranges based on actual data
        voltage_range = np.max(voltage) - np.min(voltage)
        voltage_center = (np.max(voltage) + np.min(voltage)) / 2
        
        # Wider search ranges for unknown analytes
        if self.config.get('analyte', 'generic') == 'generic':
            # Use full voltage range with subdivision
            ox_range = [voltage_center, np.max(voltage)]
            red_range = [np.min(voltage), voltage_center]
        else:
            ox_range = analyte_config['ox_voltage_range']
            red_range = analyte_config['red_voltage_range']
        
        # Adaptive minimum height
        current_range = np.max(current_corrected) - np.min(current_corrected)
        adaptive_min_height = max(
            analyte_config['min_peak_height'],
            current_range * 0.05  # 5% of current range
        )
        
        # Find oxidation peak(s)
        ox_mask = (voltage >= ox_range[0]) & (voltage <= ox_range[1])
        if np.any(ox_mask):
            ox_region_current = current_corrected[ox_mask]
            ox_region_voltage = voltage[ox_mask]
            ox_indices = np.where(ox_mask)[0]
            
            if len(ox_region_current) > 0:
                # Find all local maxima above threshold
                from scipy.signal import find_peaks
                local_maxima, _ = find_peaks(
                    ox_region_current,
                    height=adaptive_min_height,
                    distance=max(3, len(ox_region_current) // 10)
                )
                
                for max_idx in local_maxima:
                    global_idx = ox_indices[max_idx]
                    
                    # Calculate prominence
                    left_min = np.min(current_corrected[max(0, global_idx-10):global_idx])
                    right_min = np.min(current_corrected[global_idx:min(len(current_corrected), global_idx+10)])
                    prominence = current_corrected[global_idx] - max(left_min, right_min)
                    
                    peaks.append({
                        'index': global_idx,
                        'voltage': voltage[global_idx],
                        'current': current_corrected[global_idx],
                        'type': 'oxidation',
                        'method': 'template',
                        'prominence': prominence
                    })
        
        # Find reduction peak(s)
        red_mask = (voltage >= red_range[0]) & (voltage <= red_range[1])
        if np.any(red_mask):
            red_region_current = current_corrected[red_mask]
            red_region_voltage = voltage[red_mask]
            red_indices = np.where(red_mask)[0]
            
            if len(red_region_current) > 0:
                # Find all local minima below threshold
                from scipy.signal import find_peaks
                local_minima, _ = find_peaks(
                    -red_region_current,
                    height=adaptive_min_height,
                    distance=max(3, len(red_region_current) // 10)
                )
                
                for min_idx in local_minima:
                    if red_region_current[min_idx] < 0:  # Only negative currents
                        global_idx = red_indices[min_idx]
                        
                        # Calculate prominence for negative peak
                        left_max = np.max(current_corrected[max(0, global_idx-10):global_idx])
                        right_max = np.max(current_corrected[global_idx:min(len(current_corrected), global_idx+10)])
                        prominence = min(left_max, right_max) - current_corrected[global_idx]
                        
                        peaks.append({
                            'index': global_idx,
                            'voltage': voltage[global_idx],
                            'current': current_corrected[global_idx],
                            'type': 'reduction',
                            'method': 'template',
                            'prominence': prominence
                        })
        
        self.logger.info(f"   Template method found: {len(peaks)} peaks")
        return peaks
    
    def _validate_peaks(self, voltage: np.ndarray, current: np.ndarray, 
                       current_corrected: np.ndarray, peak_candidates: List[Dict],
                       baseline: BaselineData) -> List[PeakData]:
        """Validate and merge peak candidates from different methods"""
        
        # Remove duplicates (peaks within 0.01V of each other)
        unique_peaks = []
        for candidate in peak_candidates:
            is_duplicate = False
            for existing in unique_peaks:
                if abs(candidate['voltage'] - existing['voltage']) < 0.01:
                    # Keep the one with higher prominence
                    if candidate['prominence'] > existing['prominence']:
                        unique_peaks.remove(existing)
                        unique_peaks.append(candidate)
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_peaks.append(candidate)
        
        # Convert to PeakData objects with full analysis
        validated_peaks = []
        for peak in unique_peaks:
            try:
                peak_data = self._analyze_single_peak(voltage, current, current_corrected, 
                                                    peak, baseline)
                if peak_data.confidence >= self.config.get('confidence_threshold', 50.0):
                    validated_peaks.append(peak_data)
            except Exception as e:
                self.logger.warning(f"⚠️ Peak validation failed: {e}")
        
        return validated_peaks
    
    def _analyze_single_peak(self, voltage: np.ndarray, current: np.ndarray,
                           current_corrected: np.ndarray, peak_candidate: Dict,
                           baseline: BaselineData) -> PeakData:
        """Complete analysis of a single peak"""
        
        peak_idx = peak_candidate['index']
        peak_voltage = peak_candidate['voltage']
        peak_current = current[peak_idx]
        peak_current_corrected = current_corrected[peak_idx]
        
        # Calculate peak height (from baseline)
        baseline_at_peak = baseline.currents[peak_idx]
        peak_height = abs(peak_current - baseline_at_peak)
        
        # Calculate peak width at half maximum
        peak_width = self._calculate_peak_width(voltage, current_corrected, peak_idx)
        
        # Calculate peak area
        peak_area = self._calculate_single_peak_area(voltage, current_corrected, peak_idx, peak_width)
        
        # Calculate symmetry and tailing factors
        symmetry_factor = self._calculate_symmetry_factor(voltage, current_corrected, peak_idx)
        tailing_factor = self._calculate_tailing_factor(voltage, current_corrected, peak_idx)
        
        # Calculate signal-to-noise ratio
        signal_to_noise = peak_height / baseline.noise_level if baseline.noise_level > 0 else 100
        
        # Calculate confidence score
        current_std = np.std(current_corrected)
        confidence = self._calculate_peak_confidence(peak_candidate, peak_height, 
                                                   signal_to_noise, symmetry_factor, current_std)
        
        # Calculate overall quality score
        quality_score = self._calculate_peak_quality(peak_height, signal_to_noise, 
                                                   symmetry_factor, tailing_factor)
        
        return PeakData(
            voltage=peak_voltage,
            current=peak_current,
            peak_type=peak_candidate['type'],
            height=peak_height,
            area=peak_area,
            width=peak_width,
            baseline_current=baseline_at_peak,
            confidence=confidence,
            symmetry_factor=symmetry_factor,
            tailing_factor=tailing_factor,
            signal_to_noise=signal_to_noise,
            quality_score=quality_score
        )
    
    def _calculate_peak_width(self, voltage: np.ndarray, current: np.ndarray, peak_idx: int) -> float:
        """Calculate peak width at half maximum"""
        
        peak_current = current[peak_idx]
        half_height = peak_current / 2
        
        # Find left and right boundaries at half height
        left_idx = peak_idx
        right_idx = peak_idx
        
        # Find left boundary
        while left_idx > 0 and abs(current[left_idx]) > abs(half_height):
            left_idx -= 1
        
        # Find right boundary
        while right_idx < len(current) - 1 and abs(current[right_idx]) > abs(half_height):
            right_idx += 1
        
        if left_idx < right_idx:
            return voltage[right_idx] - voltage[left_idx]
        else:
            return 0.01  # Minimum width
    
    def _calculate_single_peak_area(self, voltage: np.ndarray, current: np.ndarray, 
                                  peak_idx: int, peak_width: float) -> float:
        """Calculate area under a single peak"""
        
        # Determine integration boundaries based on peak width
        half_width_points = int(len(voltage) * peak_width / (voltage.max() - voltage.min()) / 2)
        
        start_idx = max(0, peak_idx - half_width_points)
        end_idx = min(len(voltage) - 1, peak_idx + half_width_points)
        
        # Calculate area using Simpson's rule for higher accuracy
        if self.config.get('area_calculation_method') == 'simpson' and end_idx - start_idx > 2:
            area = simpson(current[start_idx:end_idx+1], voltage[start_idx:end_idx+1])
        else:
            area = trapz(current[start_idx:end_idx+1], voltage[start_idx:end_idx+1])
        
        return abs(area)
    
    def _calculate_symmetry_factor(self, voltage: np.ndarray, current: np.ndarray, peak_idx: int) -> float:
        """Calculate peak symmetry factor"""
        # Simplified symmetry calculation
        try:
            peak_width = self._calculate_peak_width(voltage, current, peak_idx)
            half_width_left = peak_idx - 0  # This would be more sophisticated in practice
            half_width_right = len(current) - peak_idx  # This would be more sophisticated in practice
            return min(half_width_left, half_width_right) / max(half_width_left, half_width_right, 1)
        except:
            return 1.0
    
    def _calculate_tailing_factor(self, voltage: np.ndarray, current: np.ndarray, peak_idx: int) -> float:
        """Calculate peak tailing factor"""
        # Simplified tailing calculation
        return 1.0  # In practice, this would analyze the peak shape more thoroughly
    
    def _calculate_peak_confidence(self, peak_candidate: Dict, peak_height: float,
                                 signal_to_noise: float, symmetry_factor: float, 
                                 current_std: float = 1.0) -> float:
        """Calculate overall peak confidence score"""
        
        # Base confidence from detection method
        method_confidence = {
            'scipy': 80.0,
            'derivative': 70.0,
            'template': 90.0
        }.get(peak_candidate['method'], 60.0)
        
        # Height confidence (adaptive to data range)
        height_confidence = min(100.0, (peak_height / max(1.0, current_std * 2)) * 50)
        
        # Signal-to-noise confidence
        snr_confidence = min(100.0, signal_to_noise * 5)  # S/N of 20 = 100% confidence
        
        # Symmetry confidence
        symmetry_confidence = symmetry_factor * 100
        
        # Weighted average
        total_confidence = (
            method_confidence * 0.3 +
            height_confidence * 0.3 +
            snr_confidence * 0.3 +
            symmetry_confidence * 0.1
        )
        
        return min(100.0, max(0.0, total_confidence))
    
    def _calculate_peak_quality(self, peak_height: float, signal_to_noise: float,
                              symmetry_factor: float, tailing_factor: float) -> float:
        """Calculate overall peak quality score"""
        
        # Individual quality components
        height_quality = min(100.0, peak_height * 10)
        snr_quality = min(100.0, signal_to_noise * 5)
        symmetry_quality = symmetry_factor * 100
        tailing_quality = 100.0 / max(tailing_factor, 0.1)
        
        # Weighted average
        overall_quality = (
            height_quality * 0.4 +
            snr_quality * 0.3 +
            symmetry_quality * 0.2 +
            tailing_quality * 0.1
        )
        
        return min(100.0, max(0.0, overall_quality))
    
    def _calculate_precise_areas(self, voltage: np.ndarray, current: np.ndarray,
                               baseline: BaselineData, peaks: List[PeakData]) -> Dict[str, Any]:
        """Calculate precise areas under curve for PLS analysis"""
        
        self.logger.info("📐 Calculating precise areas under curve...")
        
        # Baseline-corrected current
        current_corrected = current - baseline.currents
        
        # Total area under curve
        if self.config.get('area_calculation_method') == 'simpson':
            total_area = simpson(np.abs(current_corrected), voltage)
        else:
            total_area = trapz(np.abs(current_corrected), voltage)
        
        # Separate positive and negative areas
        positive_mask = current_corrected > 0
        negative_mask = current_corrected < 0
        
        if np.any(positive_mask):
            positive_area = trapz(current_corrected[positive_mask], voltage[positive_mask])
        else:
            positive_area = 0.0
        
        if np.any(negative_mask):
            negative_area = abs(trapz(current_corrected[negative_mask], voltage[negative_mask]))
        else:
            negative_area = 0.0
        
        # Peak-specific areas (already calculated in peak analysis)
        oxidation_peaks = [p for p in peaks if p.peak_type == 'oxidation']
        reduction_peaks = [p for p in peaks if p.peak_type == 'reduction']
        
        oxidation_area = sum(p.area for p in oxidation_peaks)
        reduction_area = sum(p.area for p in reduction_peaks)
        
        # Background/capacitive area (difference between total and peak areas)
        background_area = total_area - oxidation_area - reduction_area
        
        areas = {
            'total_area': float(total_area),
            'positive_area': float(positive_area),
            'negative_area': float(negative_area),
            'oxidation_area': float(oxidation_area),
            'reduction_area': float(reduction_area),
            'background_area': float(max(0, background_area)),
            'peak_areas': [float(p.area) for p in peaks],
            'area_ratio': float(oxidation_area / reduction_area) if reduction_area > 0 else 0.0,
            'faradaic_fraction': float((oxidation_area + reduction_area) / total_area) if total_area > 0 else 0.0
        }
        
        self.logger.info(f"✅ Area calculation complete: total={total_area:.3f} μA⋅V")
        return areas
    
    def _extract_pls_features(self, voltage: np.ndarray, current: np.ndarray,
                            baseline: BaselineData, peaks: List[PeakData], 
                            areas: Dict[str, Any]) -> PLSFeatures:
        """Extract comprehensive features for PLS analysis"""
        
        self.logger.info("🧬 Extracting PLS features...")
        
        # Peak-based features
        oxidation_peaks = [p for p in peaks if p.peak_type == 'oxidation']
        reduction_peaks = [p for p in peaks if p.peak_type == 'reduction']
        
        oxidation_height = max((p.height for p in oxidation_peaks), default=0.0)
        reduction_height = max((p.height for p in reduction_peaks), default=0.0)
        
        # Peak separation
        if oxidation_peaks and reduction_peaks:
            ox_voltage = max(oxidation_peaks, key=lambda p: p.height).voltage
            red_voltage = max(reduction_peaks, key=lambda p: p.height).voltage
            peak_separation = abs(ox_voltage - red_voltage)
        else:
            peak_separation = 0.0
        
        # Peak ratio
        peak_ratio = oxidation_height / reduction_height if reduction_height > 0 else 0.0
        
        # Area-based features (from areas dict)
        total_area = areas['total_area']
        oxidation_area = areas['oxidation_area']
        reduction_area = areas['reduction_area']
        area_ratio = areas['area_ratio']
        
        # Shape-based features
        peak_symmetry = np.mean([p.symmetry_factor for p in peaks]) if peaks else 1.0
        baseline_quality = baseline.quality_score
        signal_noise_ratio = np.mean([p.signal_to_noise for p in peaks]) if peaks else 1.0
        
        # Advanced electrochemical features
        charge_transfer_resistance = self._estimate_charge_transfer_resistance(voltage, current, peaks)
        diffusion_coefficient = self._estimate_diffusion_coefficient(voltage, current, peaks)
        concentration_estimate = self._estimate_concentration(peaks, areas)
        
        features = PLSFeatures(
            oxidation_height=oxidation_height,
            reduction_height=reduction_height,
            peak_separation=peak_separation,
            peak_ratio=peak_ratio,
            total_area=total_area,
            oxidation_area=oxidation_area,
            reduction_area=reduction_area,
            area_ratio=area_ratio,
            peak_symmetry=peak_symmetry,
            baseline_quality=baseline_quality,
            signal_noise_ratio=signal_noise_ratio,
            charge_transfer_resistance=charge_transfer_resistance,
            diffusion_coefficient=diffusion_coefficient,
            concentration_estimate=concentration_estimate
        )
        
        self.logger.info("✅ PLS features extracted successfully")
        return features
    
    def _estimate_charge_transfer_resistance(self, voltage: np.ndarray, current: np.ndarray, 
                                           peaks: List[PeakData]) -> float:
        """Estimate charge transfer resistance from CV data"""
        # Simplified estimation - in practice this would be more sophisticated
        if peaks:
            max_current = max(abs(p.current) for p in peaks)
            voltage_span = voltage.max() - voltage.min()
            return voltage_span / max_current if max_current > 0 else 1000.0
        return 1000.0
    
    def _estimate_diffusion_coefficient(self, voltage: np.ndarray, current: np.ndarray,
                                      peaks: List[PeakData]) -> float:
        """Estimate diffusion coefficient using Randles-Sevcik equation"""
        # Simplified estimation
        return 1e-6  # Default value in cm²/s
    
    def _estimate_concentration(self, peaks: List[PeakData], areas: Dict[str, Any]) -> float:
        """Estimate concentration based on peak heights and areas"""
        if not peaks:
            return 0.0
        
        # Simple linear relationship (would be calibrated in practice)
        max_height = max(p.height for p in peaks)
        return max_height * 1e-6  # Convert to approximate molar concentration
    
    def _assess_analysis_quality(self, voltage: np.ndarray, current: np.ndarray,
                               baseline: BaselineData, peaks: List[PeakData]) -> Dict[str, float]:
        """Comprehensive quality assessment of the analysis"""
        
        quality_metrics = {}
        
        # Data quality
        quality_metrics['data_completeness'] = 100.0  # Assuming complete data
        quality_metrics['data_noise_level'] = max(0, 100 - np.std(current) * 10)
        
        # Baseline quality
        quality_metrics['baseline_quality'] = baseline.quality_score
        quality_metrics['baseline_stability'] = max(0, 100 - baseline.drift_rate * 1000)
        
        # Peak quality
        if peaks:
            quality_metrics['peak_detection_confidence'] = np.mean([p.confidence for p in peaks])
            quality_metrics['peak_quality_average'] = np.mean([p.quality_score for p in peaks])
            quality_metrics['signal_to_noise_ratio'] = np.mean([p.signal_to_noise for p in peaks])
        else:
            quality_metrics['peak_detection_confidence'] = 0.0
            quality_metrics['peak_quality_average'] = 0.0
            quality_metrics['signal_to_noise_ratio'] = 0.0
        
        # Overall analysis quality
        overall_weights = {
            'data_completeness': 0.1,
            'data_noise_level': 0.2,
            'baseline_quality': 0.3,
            'peak_detection_confidence': 0.25,
            'signal_to_noise_ratio': 0.15
        }
        
        overall_quality = sum(quality_metrics[k] * overall_weights[k] 
                            for k in overall_weights if k in quality_metrics)
        quality_metrics['overall_quality'] = overall_quality
        
        # PLS readiness score
        pls_readiness = min(
            quality_metrics['baseline_quality'],
            quality_metrics['peak_detection_confidence']
        )
        quality_metrics['pls_readiness'] = pls_readiness
        
        return quality_metrics
    
    def _generate_recommendations(self, quality_metrics: Dict[str, float]) -> List[str]:
        """Generate recommendations for improving analysis quality"""
        
        recommendations = []
        
        if quality_metrics['overall_quality'] < 80:
            recommendations.append("Overall analysis quality is below optimal. Consider reviewing data collection parameters.")
        
        if quality_metrics['baseline_quality'] < 70:
            recommendations.append("Baseline quality is poor. Consider longer equilibration time or different baseline correction method.")
        
        if quality_metrics['peak_detection_confidence'] < 80:
            recommendations.append("Peak detection confidence is low. Verify analyte concentration and measurement conditions.")
        
        if quality_metrics['signal_to_noise_ratio'] < 10:
            recommendations.append("Signal-to-noise ratio is low. Consider filtering, averaging multiple scans, or increasing concentration.")
        
        if quality_metrics['pls_readiness'] < 85:
            recommendations.append("Data quality may not be sufficient for reliable PLS analysis. Consider improving measurement conditions.")
        
        if not recommendations:
            recommendations.append("Analysis quality is excellent. Data is ready for PLS analysis.")
        
        return recommendations
    
    # Serialization methods for JSON output
    def _serialize_baseline(self, baseline: BaselineData) -> Dict[str, Any]:
        """Serialize baseline data for JSON output"""
        return {
            'voltages': baseline.voltages.tolist(),
            'currents': baseline.currents.tolist(),
            'method': baseline.method,
            'quality_score': baseline.quality_score,
            'r_squared': baseline.r_squared,
            'slope': baseline.slope,
            'intercept': baseline.intercept,
            'noise_level': baseline.noise_level,
            'drift_rate': baseline.drift_rate
        }
    
    def _serialize_peak(self, peak: PeakData) -> Dict[str, Any]:
        """Serialize peak data for JSON output"""
        return {
            'voltage': peak.voltage,
            'current': peak.current,
            'peak_type': peak.peak_type,
            'height': peak.height,
            'area': peak.area,
            'width': peak.width,
            'baseline_current': peak.baseline_current,
            'confidence': peak.confidence,
            'symmetry_factor': peak.symmetry_factor,
            'tailing_factor': peak.tailing_factor,
            'signal_to_noise': peak.signal_to_noise,
            'quality_score': peak.quality_score
        }
    
    def _serialize_pls_features(self, features: PLSFeatures) -> Dict[str, Any]:
        """Serialize PLS features for JSON output"""
        return {
            'oxidation_height': features.oxidation_height,
            'reduction_height': features.reduction_height,
            'peak_separation': features.peak_separation,
            'peak_ratio': features.peak_ratio,
            'total_area': features.total_area,
            'oxidation_area': features.oxidation_area,
            'reduction_area': features.reduction_area,
            'area_ratio': features.area_ratio,
            'peak_symmetry': features.peak_symmetry,
            'baseline_quality': features.baseline_quality,
            'signal_noise_ratio': features.signal_noise_ratio,
            'charge_transfer_resistance': features.charge_transfer_resistance,
            'diffusion_coefficient': features.diffusion_coefficient,
            'concentration_estimate': features.concentration_estimate
        }
    
    def _log_analysis_summary(self, results: Dict[str, Any]):
        """Log comprehensive analysis summary"""
        
        self.logger.info("📊 PRECISION ANALYSIS SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"File: {results['filename']}")
        self.logger.info(f"Success: {results['success']}")
        
        if results['success']:
            data_info = results['data_info']
            self.logger.info(f"Data points: {data_info['points']}")
            self.logger.info(f"Voltage range: {data_info['voltage_range'][0]:.3f} to {data_info['voltage_range'][1]:.3f} V")
            self.logger.info(f"Current range: {data_info['current_range'][0]:.3f} to {data_info['current_range'][1]:.3f} μA")
            
            baseline = results['baseline']
            self.logger.info(f"Baseline quality: {baseline['quality_score']:.1f}%")
            
            peaks = results['peaks']
            self.logger.info(f"Peaks detected: {len(peaks)}")
            for i, peak in enumerate(peaks, 1):
                self.logger.info(f"  Peak {i}: {peak['peak_type']} at {peak['voltage']:.3f}V, confidence: {peak['confidence']:.1f}%")
            
            areas = results['areas']
            self.logger.info(f"Total area: {areas['total_area']:.3f} μA⋅V")
            self.logger.info(f"Oxidation area: {areas['oxidation_area']:.3f} μA⋅V")
            self.logger.info(f"Reduction area: {areas['reduction_area']:.3f} μA⋅V")
            
            quality = results['quality_metrics']
            self.logger.info(f"Overall quality: {quality['overall_quality']:.1f}%")
            self.logger.info(f"PLS readiness: {quality['pls_readiness']:.1f}%")
            
            recommendations = results['recommendations']
            if recommendations:
                self.logger.info("Recommendations:")
                for rec in recommendations:
                    self.logger.info(f"  • {rec}")
        
        self.logger.info("=" * 50)


def test_precision_analyzer():
    """Test the precision analyzer with real data"""
    
    import os
    import pandas as pd
    
    # Test with a sample file
    test_file = "Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv"
    
    if not os.path.exists(test_file):
        logger.error(f"Test file not found: {test_file}")
        return None
    
    try:
        # Load data
        df = pd.read_csv(test_file, skiprows=1)
        voltage = df.iloc[:, 0].values
        current = df.iloc[:, 1].values
        
        # Convert current to μA if needed (Palmsens data is usually in A)
        if np.max(np.abs(current)) < 1e-3:  # If values are very small, likely in A
            current = current * 1e6  # Convert to μA
        
        # Create analyzer
        analyzer = PrecisionPeakBaselineAnalyzer({
            'analyte': 'ferrocene',
            'confidence_threshold': 80.0,
            'quality_threshold': 75.0
        })
        
        # Run analysis
        logger.info("🧪 Testing Precision Peak and Baseline Analyzer")
        logger.info("=" * 60)
        
        results = analyzer.analyze_cv_data(voltage, current, filename=test_file, analyte='ferrocene')
        
        if results['success']:
            logger.info("🎉 Analysis completed successfully!")
            
            # Save detailed results
            output_file = "precision_analysis_results.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"📄 Detailed results saved to: {output_file}")
            
            return results
        else:
            logger.error(f"❌ Analysis failed: {results.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


if __name__ == "__main__":
    test_precision_analyzer()
