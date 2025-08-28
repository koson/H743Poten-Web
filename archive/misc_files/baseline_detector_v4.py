"""
CV Baseline Detector v4 - Voltage Window Based
============================================
Enhanced baseline detection using voltage windows approach
"""

import numpy as np
import logging
from scipy import stats
from typing import List, Dict, Tuple, Optional

# Import the new voltage window algorithm
from baseline_detector_voltage_windows import voltage_window_baseline_detector

logger = logging.getLogger(__name__)

def cv_baseline_detector_v4(voltage: np.ndarray, current: np.ndarray, 
                           peak_regions: List[Tuple[int, int]] = None) -> Tuple[np.ndarray, np.ndarray, Dict]:
    """
    CV Baseline Detection v4 - Voltage Window Based
    
    Uses adaptive voltage windows to find stable baseline segments,
    avoiding hard-coded position assumptions.
    
    Args:
        voltage: Voltage array (V)
        current: Current array (µA)  
        peak_regions: List of (start_idx, end_idx) for detected peaks
        
    Returns:
        forward_baseline, reverse_baseline, info_dict
    """
    try:
        logger.info("🚀 CV Baseline Detector v4 - Voltage Window Based")
        logger.info(f"📊 Data: {len(voltage)} points, V-range: {voltage.min():.3f} to {voltage.max():.3f}V")
        logger.info(f"⚡ I-range: {current.min():.2e} to {current.max():.2e} µA")
        
        if peak_regions:
            logger.info(f"🎯 Excluding {len(peak_regions)} peak regions from baseline search")
        
        # Use the new voltage window algorithm
        forward_baseline, reverse_baseline, info = voltage_window_baseline_detector(
            voltage, current, peak_regions
        )
        
        # Log results
        baseline_full = np.concatenate([forward_baseline, reverse_baseline])
        logger.info(f"📊 Baseline summary:")
        logger.info(f"   Forward range: [{forward_baseline.min():.3f}, {forward_baseline.max():.3f}] μA")
        logger.info(f"   Reverse range: [{reverse_baseline.min():.3f}, {reverse_baseline.max():.3f}] μA")
        logger.info(f"   Full range: [{baseline_full.min():.3f}, {baseline_full.max():.3f}] μA")
        logger.info(f"   CV data range: [{current.min():.3f}, {current.max():.3f}] μA")
        
        # Add processing time and method info
        info.update({
            'method': 'voltage_window_v4',
            'voltage_range': (voltage.min(), voltage.max()),
            'current_range': (current.min(), current.max()),
            'baseline_range': (baseline_full.min(), baseline_full.max())
        })
        
        return forward_baseline, reverse_baseline, info
        
    except Exception as e:
        logger.error(f"❌ Error in CV baseline detection v4: {e}")
        # Safe fallback
        n = len(voltage)
        mid = n // 2
        
        # Simple fallback baseline
        forward_mean = np.mean(current[:mid//2])  # Use early portion only
        reverse_mean = np.mean(current[-mid//2:])  # Use late portion only
        
        forward_baseline = np.full(mid, forward_mean)
        reverse_baseline = np.full(n - mid, reverse_mean)
        
        return forward_baseline, reverse_baseline, {
            'method': 'fallback_v4',
            'error': str(e),
            'forward_segment': None,
            'reverse_segment': None
        }

# Keep v3 as backup
def cv_baseline_detector_v3(voltage: np.ndarray, current: np.ndarray, 
                           peak_regions: List[Tuple[int, int]] = None) -> Tuple[np.ndarray, np.ndarray, Dict]:
    """
    Fallback to v3 if needed
    """
    # Import and use the original v3 logic would go here
    # For now, just call v4
    return cv_baseline_detector_v4(voltage, current, peak_regions)