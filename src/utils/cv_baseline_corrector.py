#!/usr/bin/env python3
"""
🔧 CV Baseline Correction for H743Poten Web
Improved baseline detection specifically for CV data on the web platform

This addresses the baseline detection issues seen in the web interface.
"""

import numpy as np
import time
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class CVBaselineCorrector:
    """🎯 CV-specific baseline correction optimized for web interface"""
    
    def __init__(self):
        """Initialize CV baseline corrector"""
        self.config = {
            'linear_fit_segments': 5,      # Number of segments for piecewise linear fit
            'edge_percentage': 0.15,       # Percentage of data at edges to use for baseline
            'smoothing_window': 10,        # Smoothing window size
            'peak_threshold': 0.3,         # Threshold for peak detection (relative to max)
            'baseline_points_min': 10,     # Minimum points needed for baseline estimation
        }
        
        logger.info("🎯 CV Baseline Corrector initialized")
    
    def detect_baseline_cv(self, voltages: np.ndarray, currents: np.ndarray, 
                          filename: str = "cv_data") -> Tuple[np.ndarray, Dict]:
        """
        🔍 Detect baseline for CV data using optimized method
        
        Args:
            voltages: Voltage array
            currents: Current array
            filename: Data identifier
            
        Returns:
            baseline: Detected baseline
            metadata: Detection metadata
        """
        start_time = time.time()
        
        logger.info(f"🔍 CV Baseline Detection: {filename}")
        logger.info(f"📊 Data: {len(voltages)} points, V-range: {voltages.min():.3f} to {voltages.max():.3f}V")
        logger.info(f"⚡ I-range: {currents.min():.2e} to {currents.max():.2e} µA")
        
        # Check for very small current values (potential unit conversion issue)
        current_magnitude = np.max(np.abs(currents))
        if current_magnitude < 1e-3:  # Less than 1 nA
            logger.warning(f"⚠️  Very small current magnitude: {current_magnitude:.2e} µA")
            logger.warning("⚠️  This might indicate a unit conversion issue")
            logger.warning("⚠️  Expected current should be in µA range (typically 1-1000 µA)")
        
        try:
            # Method 1: Try edge-based baseline
            baseline = self._edge_based_baseline(voltages, currents)
            quality_score = self._assess_baseline_quality(currents, baseline)
            
            # If edge-based fails, try piecewise linear
            if quality_score < 0.5:
                logger.info("📈 Edge-based baseline poor quality, trying piecewise linear")
                baseline = self._piecewise_linear_baseline(voltages, currents)
                quality_score = self._assess_baseline_quality(currents, baseline)
            
            # If still poor, use simple linear fit
            if quality_score < 0.3:
                logger.info("📉 Piecewise linear poor quality, using simple linear fit")
                baseline = self._simple_linear_baseline(voltages, currents)
                quality_score = self._assess_baseline_quality(currents, baseline)
            
            processing_time = time.time() - start_time
            
            metadata = {
                'method': 'cv_optimized',
                'quality_score': quality_score,
                'processing_time': processing_time,
                'data_points': len(voltages),
                'baseline_std': np.std(baseline),
                'current_std': np.std(currents)
            }
            
            logger.info(f"✅ CV baseline detection completed")
            logger.info(f"📊 Quality score: {quality_score:.2f}")
            logger.info(f"⏱️ Processing time: {processing_time:.3f}s")
            
            return baseline, metadata
            
        except Exception as e:
            logger.error(f"❌ CV baseline detection failed: {e}")
            import traceback
            logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
            
            # Emergency fallback - CV-appropriate baseline
            try:
                # Try simple linear baseline as emergency fallback
                baseline = self._emergency_cv_baseline(voltages, currents)
                metadata = {
                    'method': 'emergency_cv_fallback',
                    'quality_score': 0.3,
                    'processing_time': time.time() - start_time,
                    'error': str(e)
                }
                logger.info("🚨 Using emergency CV fallback baseline")
                return baseline, metadata
            except Exception as final_error:
                logger.error(f"🆘 Even emergency fallback failed: {final_error}")
                # Ultimate fallback - flat baseline at median
                baseline = np.full_like(currents, np.median(currents))
                metadata = {
                    'method': 'flat_median_fallback',
                    'quality_score': 0.1,
                    'processing_time': time.time() - start_time,
                    'error': f"Original: {str(e)}, Fallback: {str(final_error)}"
                }
                return baseline, metadata
    
    def _emergency_cv_baseline(self, voltages: np.ndarray, currents: np.ndarray) -> np.ndarray:
        """🚨 Emergency CV-appropriate baseline"""
        try:
            # Use first and last 10% of data for linear fit
            n = len(currents)
            edge_size = max(3, n // 10)
            
            start_current = np.mean(currents[:edge_size])
            end_current = np.mean(currents[-edge_size:])
            
            # Linear interpolation between start and end
            baseline = np.linspace(start_current, end_current, n)
            
            logger.info(f"🚨 Emergency baseline: {start_current:.2e} to {end_current:.2e} µA")
            return baseline
            
        except Exception:
            # Final fallback - constant baseline
            median_current = np.median(currents)
            logger.info(f"🆘 Constant baseline at median: {median_current:.2e} µA")
            return np.full_like(currents, median_current)
    
    def _edge_based_baseline(self, voltages: np.ndarray, currents: np.ndarray) -> np.ndarray:
        """🎯 Edge-based baseline detection for CV data"""
        
        n_points = len(voltages)
        edge_size = max(int(n_points * self.config['edge_percentage']), 
                       self.config['baseline_points_min'])
        
        # Get edge regions (beginning and end of CV scan)
        start_voltages = voltages[:edge_size]
        start_currents = currents[:edge_size]
        end_voltages = voltages[-edge_size:]
        end_currents = currents[-edge_size:]
        
        # Combine edge data
        edge_voltages = np.concatenate([start_voltages, end_voltages])
        edge_currents = np.concatenate([start_currents, end_currents])
        
        # Fit linear baseline through edge points
        try:
            coeffs = np.polyfit(edge_voltages, edge_currents, 1)
            baseline = np.polyval(coeffs, voltages)
            
            # Apply smoothing
            baseline = self._smooth_baseline(baseline)
            
            logger.info(f"📊 Edge-based baseline: slope={coeffs[0]:.2e}, intercept={coeffs[1]:.2e}")
            return baseline
            
        except Exception as e:
            logger.warning(f"Edge-based baseline failed: {e}")
            return np.full_like(currents, np.mean(edge_currents))
    
    def _piecewise_linear_baseline(self, voltages: np.ndarray, currents: np.ndarray) -> np.ndarray:
        """📈 Piecewise linear baseline for complex CV data"""
        
        n_segments = self.config['linear_fit_segments']
        n_points = len(voltages)
        segment_size = n_points // n_segments
        
        baseline_points_v = []
        baseline_points_i = []
        
        # Find baseline points in each segment
        for i in range(n_segments):
            start_idx = i * segment_size
            end_idx = min((i + 1) * segment_size, n_points)
            
            if end_idx <= start_idx:
                continue
            
            seg_voltages = voltages[start_idx:end_idx]
            seg_currents = currents[start_idx:end_idx]
            
            # Find minimum current region in this segment (likely baseline)
            min_idx = np.argmin(np.abs(seg_currents))
            baseline_points_v.append(seg_voltages[min_idx])
            baseline_points_i.append(seg_currents[min_idx])
        
        # Interpolate baseline through these points
        if len(baseline_points_v) >= 2:
            try:
                # Linear interpolation
                baseline = np.interp(voltages, baseline_points_v, baseline_points_i)
                baseline = self._smooth_baseline(baseline)
                
                logger.info(f"📈 Piecewise linear baseline with {len(baseline_points_v)} segments")
                return baseline
                
            except Exception as e:
                logger.warning(f"Piecewise linear interpolation failed: {e}")
        
        # Fallback to simple linear fit
        return self._simple_linear_baseline(voltages, currents)
    
    def _simple_linear_baseline(self, voltages: np.ndarray, currents: np.ndarray) -> np.ndarray:
        """📉 Simple linear baseline as fallback"""
        
        try:
            # Use least squares fit
            coeffs = np.polyfit(voltages, currents, 1)
            baseline = np.polyval(coeffs, voltages)
            
            logger.info(f"📉 Simple linear baseline: slope={coeffs[0]:.2e}")
            return baseline
            
        except Exception as e:
            logger.warning(f"Simple linear baseline failed: {e}")
            # Ultimate fallback - constant at mean
            return np.full_like(currents, np.mean(currents))
    
    def _smooth_baseline(self, baseline: np.ndarray) -> np.ndarray:
        """🎯 Smooth baseline to reduce noise"""
        
        window = min(self.config['smoothing_window'], len(baseline) // 5)
        if window < 3:
            return baseline
        
        # Simple moving average
        smoothed = np.copy(baseline)
        half_window = window // 2
        
        for i in range(len(baseline)):
            start = max(0, i - half_window)
            end = min(len(baseline), i + half_window + 1)
            smoothed[i] = np.mean(baseline[start:end])
        
        return smoothed
    
    def _assess_baseline_quality(self, currents: np.ndarray, baseline: np.ndarray) -> float:
        """📊 Assess baseline quality"""
        
        try:
            # Corrected current after baseline subtraction
            corrected = currents - baseline
            
            # Quality metrics
            baseline_smoothness = 1.0 / (1.0 + np.std(np.diff(baseline)))
            
            # Check if baseline correction improves signal
            original_range = np.ptp(currents)
            corrected_range = np.ptp(corrected)
            
            # Good baseline should not drastically change the signal range
            range_preservation = 1.0 - abs(original_range - corrected_range) / original_range
            range_preservation = max(0.0, min(1.0, range_preservation))
            
            # Check baseline magnitude compared to signal
            baseline_magnitude = np.std(baseline)
            signal_magnitude = np.std(currents)
            magnitude_ratio = min(1.0, baseline_magnitude / signal_magnitude) if signal_magnitude > 0 else 0.0
            
            # Combined quality score
            quality = (baseline_smoothness * 0.4 + 
                      range_preservation * 0.4 + 
                      (1.0 - magnitude_ratio) * 0.2)
            
            return max(0.0, min(1.0, quality))
            
        except Exception as e:
            logger.warning(f"Quality assessment failed: {e}")
            return 0.1