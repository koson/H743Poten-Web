#!/usr/bin/env python3
"""
🚀 Enhanced Baseline Detection v2.1 for Web Application
Simplified and robust baseline detection system for H743Poten Web Interface
"""

# Import CV Baseline Corrector
try:
    from ..utils.cv_baseline_corrector import CVBaselineCorrector
except ImportError:
    try:
        from utils.cv_baseline_corrector import CVBaselineCorrector
    except ImportError:
        CVBaselineCorrector = None

import numpy as np
import time
from typing import Dict, Tuple
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
        self.traditional_window = 25
        
        # Initialize CV-specific corrector if available
        if CVBaselineCorrector:
            self.cv_corrector = CVBaselineCorrector()
        else:
            self.cv_corrector = None
            logger.warning("CVBaselineCorrector not available, using traditional methods only")
        
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
        
        # Validate input data
        if len(voltages) != len(currents):
            raise ValueError(f"Voltage and current arrays must have same length: {len(voltages)} vs {len(currents)}")
        
        if len(voltages) < 3:
            raise ValueError(f"Need at least 3 data points, got {len(voltages)}")
        
        # Method selection
        if force_method:
            selected_method = force_method
            logger.info(f"🔧 Forced method: {selected_method}")
        elif self.auto_mode:
            selected_method = self._select_optimal_method(currents, voltages)
            logger.info(f"🤖 Auto-selected method: {selected_method}")
        else:
            selected_method = 'cv_optimized' if self.cv_corrector else 'traditional'
            logger.info(f"📊 Default method: {selected_method}")
        
        # Apply selected method
        try:
            if selected_method == 'traditional' or not self.cv_corrector:
                baseline = self._traditional_baseline(currents)
                metadata = {
                    'method': 'traditional_optimized',
                    'window_size': self.traditional_window,
                    'processing_time': time.time() - start_time,
                    'quality_metrics': {'overall_quality': 0.7}
                }
                logger.info(f"✅ Traditional method completed in {metadata['processing_time']:.3f}s")
            else:
                # Use CV-optimized baseline corrector
                baseline, cv_metadata = self.cv_corrector.detect_baseline_cv(voltages, currents, filename)
                cv_metadata['auto_selected'] = self.auto_mode
                metadata = cv_metadata
            
            # Validate output
            if len(baseline) != len(currents):
                raise ValueError(f"Baseline length mismatch: expected {len(currents)}, got {len(baseline)}")
            
            logger.info(f"🎯 Selected method: {metadata['method']}")
            logger.info(f"⏱️ Processing time: {metadata['processing_time']:.3f}s")
            
            return baseline, metadata
            
        except Exception as e:
            logger.error(f"❌ Baseline detection failed: {e}")
            # Emergency fallback
            baseline = self._emergency_fallback(currents)
            metadata = {
                'method': 'emergency_fallback',
                'processing_time': time.time() - start_time,
                'quality_metrics': {'overall_quality': 0.1},
                'error': str(e)
            }
            return baseline, metadata
    
    def _select_optimal_method(self, currents: np.ndarray, voltages: np.ndarray) -> str:
        """🤖 Intelligent method selection based on data characteristics"""
        
        try:
            # Simple heuristics for method selection
            data_range = np.ptp(currents)  # Peak-to-peak range
            data_std = np.std(currents)
            
            # For CV data, check if it looks like a typical CV scan
            is_cv_like = self._is_cv_like_data(voltages, currents)
            
            if not self.cv_corrector:
                return 'traditional'
            elif is_cv_like:
                return 'cv_optimized'  # Use CV-specific method
            elif data_std < 0.1 * data_range:
                return 'traditional'   # Very clean data - use simple method
            else:
                return 'cv_optimized'  # Default to CV-optimized for robustness
                
        except Exception as e:
            logger.warning(f"Method selection failed: {e}, using traditional")
            return 'traditional'
    
    def _is_cv_like_data(self, voltages: np.ndarray, currents: np.ndarray) -> bool:
        """🔍 Check if data looks like CV scan"""
        
        try:
            # CV characteristics:
            # 1. Voltage should span reasonable range
            voltage_range = np.ptp(voltages)
            if voltage_range < 0.3:  # Less than 300mV range
                return False
            
            # 2. Current should have significant variation
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
        """📊 Traditional baseline using CV-optimized method"""
        
        try:
            # For CV data, use edge-based baseline instead of moving average
            n = len(currents)
            if n < 10:
                return np.full_like(currents, np.mean(currents))
            
            # CV-specific approach: use stable regions at edges
            edge_percent = 0.2  # Use 20% from each edge
            edge_points = max(5, int(n * edge_percent))
            
            # Get stable regions (beginning and end of CV scan)
            start_region = currents[:edge_points]
            end_region = currents[-edge_points:]
            
            # Calculate baseline using linear interpolation between edge regions
            start_baseline = np.mean(start_region)
            end_baseline = np.mean(end_region)
            
            # Create smooth transition between start and end baselines
            baseline = np.linspace(start_baseline, end_baseline, n)
            
            logger.info(f"📊 Traditional CV baseline: start={start_baseline:.2e}, end={end_baseline:.2e}")
            
            return baseline
            
        except Exception as e:
            logger.error(f"Traditional baseline failed: {e}")
            return self._emergency_fallback(currents)
    
    def _emergency_fallback(self, currents: np.ndarray) -> np.ndarray:
        """🚨 Emergency fallback baseline"""
        
        try:
            # Return constant baseline at median value
            return np.full_like(currents, np.median(currents))
        except Exception:
            # Ultimate fallback - zeros
            return np.zeros_like(currents)