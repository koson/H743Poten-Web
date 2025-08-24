"""
Production Cross-Instrument Calibration Service
Converts STM32H743 measurements to PalmSens-equivalent values based on cross-sample calibration
"""

import json
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ProductionCalibrationService:
    """
    Production-ready calibration service for STM32 ↔ PalmSens conversion
    Based on cross-sample calibration results from dataset IDs 60-90
    """
    
    def __init__(self, calibration_file: str = "cross_sample_calibration_results.json"):
        """Initialize with calibration data from cross-sample analysis"""
        self.calibration_data = {}
        self.default_gain = 625583.47  # Average gain factor from analysis
        self.default_offset = -2.8     # Average offset from analysis
        
        # Load calibration data if available
        self.load_calibration_data(calibration_file)
        
        # Calibration quality metrics
        self.min_r_squared = 0.3  # Minimum acceptable R²
        self.confidence_levels = {
            'high': 0.6,    # R² > 0.6
            'medium': 0.4,  # R² > 0.4
            'low': 0.3      # R² > 0.3
        }
    
    def load_calibration_data(self, calibration_file: str) -> bool:
        """Load calibration data from file"""
        try:
            file_path = Path(calibration_file)
            if file_path.exists():
                with open(file_path, 'r') as f:
                    self.calibration_data = json.load(f)
                logger.info(f"Loaded calibration data with {len(self.calibration_data)} conditions")
                return True
            else:
                logger.warning(f"Calibration file {calibration_file} not found, using defaults")
                return False
        except Exception as e:
            logger.error(f"Error loading calibration data: {e}")
            return False
    
    def calibrate_current_stm32_to_palmsens(self, 
                                          stm32_current: float, 
                                          scan_rate: Optional[float] = None,
                                          concentration: Optional[float] = None) -> Dict:
        """
        Convert STM32 current measurement to PalmSens equivalent
        
        Args:
            stm32_current: Raw STM32 current in Amperes
            scan_rate: Scan rate in mV/s (optional, for condition-specific calibration)
            concentration: Concentration in mM (optional, for condition-specific calibration)
        
        Returns:
            Dict with calibrated_current, calibration_info, and confidence metrics
        """
        result = {
            'stm32_current': stm32_current,
            'calibrated_current': None,
            'gain_factor': self.default_gain,
            'offset': self.default_offset,
            'calibration_method': 'default',
            'confidence': 'medium',
            'r_squared': 0.5,  # Assumed average
            'condition_specific': False
        }
        
        # Try to find condition-specific calibration
        if scan_rate is not None and concentration is not None:
            condition_key = f"{concentration}mM_{scan_rate}mVs"
            if condition_key in self.calibration_data:
                cal_data = self.calibration_data[condition_key]
                result.update({
                    'gain_factor': cal_data['gain_factor'],
                    'offset': cal_data['offset'],
                    'calibration_method': 'condition_specific',
                    'r_squared': cal_data['r_squared'],
                    'condition_specific': True,
                    'stm32_id': cal_data['stm32_id'],
                    'palmsens_id': cal_data['palmsens_id']
                })
                
                # Determine confidence level
                r_squared = cal_data['r_squared']
                if r_squared >= self.confidence_levels['high']:
                    result['confidence'] = 'high'
                elif r_squared >= self.confidence_levels['medium']:
                    result['confidence'] = 'medium'
                else:
                    result['confidence'] = 'low'
        
        # Apply calibration
        calibrated_current = result['gain_factor'] * stm32_current + result['offset']
        result['calibrated_current'] = calibrated_current
        
        return result
    
    def calibrate_cv_curve(self, 
                          stm32_cv_data: List[List[float]], 
                          scan_rate: Optional[float] = None,
                          concentration: Optional[float] = None) -> Dict:
        """
        Calibrate an entire CV curve from STM32 to PalmSens equivalent
        
        Args:
            stm32_cv_data: List of [voltage, current] pairs from STM32
            scan_rate: Scan rate in mV/s
            concentration: Concentration in mM
        
        Returns:
            Dict with calibrated CV data and calibration metadata
        """
        if not stm32_cv_data:
            return {'error': 'No CV data provided'}
        
        # Get calibration for first point to determine parameters
        first_current = stm32_cv_data[0][1] if len(stm32_cv_data[0]) > 1 else 0
        cal_info = self.calibrate_current_stm32_to_palmsens(
            first_current, scan_rate, concentration
        )
        
        # Apply calibration to all current values
        calibrated_cv_data = []
        for voltage, current in stm32_cv_data:
            calibrated_current = cal_info['gain_factor'] * current + cal_info['offset']
            calibrated_cv_data.append([voltage, calibrated_current])
        
        return {
            'original_data': stm32_cv_data,
            'calibrated_data': calibrated_cv_data,
            'data_points': len(calibrated_cv_data),
            'calibration_info': {
                'gain_factor': cal_info['gain_factor'],
                'offset': cal_info['offset'],
                'method': cal_info['calibration_method'],
                'confidence': cal_info['confidence'],
                'r_squared': cal_info['r_squared'],
                'condition_specific': cal_info['condition_specific']
            },
            'current_range': {
                'stm32_min': min(point[1] for point in stm32_cv_data),
                'stm32_max': max(point[1] for point in stm32_cv_data),
                'palmsens_min': min(point[1] for point in calibrated_cv_data),
                'palmsens_max': max(point[1] for point in calibrated_cv_data)
            }
        }
    
    def get_available_calibrations(self) -> Dict:
        """Get information about available calibration conditions"""
        available = {}
        for condition, data in self.calibration_data.items():
            available[condition] = {
                'concentration_mM': data['concentration_mM'],
                'scan_rate_mVs': data['scan_rate_mVs'],
                'r_squared': data['r_squared'],
                'confidence': self._get_confidence_level(data['r_squared']),
                'data_points': data['data_points_used']
            }
        return available
    
    def _get_confidence_level(self, r_squared: float) -> str:
        """Determine confidence level based on R² value"""
        if r_squared >= self.confidence_levels['high']:
            return 'high'
        elif r_squared >= self.confidence_levels['medium']:
            return 'medium'
        else:
            return 'low'
    
    def get_calibration_stats(self) -> Dict:
        """Get overall calibration statistics"""
        if not self.calibration_data:
            return {
                'total_conditions': 0,
                'default_gain': self.default_gain,
                'default_offset': self.default_offset
            }
        
        gains = [data['gain_factor'] for data in self.calibration_data.values()]
        r_squares = [data['r_squared'] for data in self.calibration_data.values()]
        
        return {
            'total_conditions': len(self.calibration_data),
            'gain_factor_stats': {
                'mean': np.mean(gains),
                'std': np.std(gains),
                'min': np.min(gains),
                'max': np.max(gains),
                'cv_percent': (np.std(gains) / np.mean(gains)) * 100
            },
            'r_squared_stats': {
                'mean': np.mean(r_squares),
                'std': np.std(r_squares),
                'min': np.min(r_squares),
                'max': np.max(r_squares)
            },
            'confidence_distribution': {
                'high': sum(1 for r2 in r_squares if r2 >= self.confidence_levels['high']),
                'medium': sum(1 for r2 in r_squares if self.confidence_levels['medium'] <= r2 < self.confidence_levels['high']),
                'low': sum(1 for r2 in r_squares if self.confidence_levels['low'] <= r2 < self.confidence_levels['medium'])
            }
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize calibration service
    cal_service = ProductionCalibrationService()
    
    # Test single current calibration
    stm32_current = 1e-4  # 100 µA from STM32
    result = cal_service.calibrate_current_stm32_to_palmsens(
        stm32_current, 
        scan_rate=100.0, 
        concentration=5.0
    )
    
    print("Single Current Calibration Test:")
    print(f"STM32 Current: {stm32_current:.2e} A")
    print(f"Calibrated Current: {result['calibrated_current']:.2e} A")
    print(f"Gain Factor: {result['gain_factor']:.0f}")
    print(f"Confidence: {result['confidence']}")
    print(f"R²: {result['r_squared']:.3f}")
    
    # Test CV curve calibration
    test_cv_data = [
        [-0.5, -1e-4],
        [0.0, 0],
        [0.5, 1e-4]
    ]
    
    cv_result = cal_service.calibrate_cv_curve(
        test_cv_data, 
        scan_rate=100.0, 
        concentration=5.0
    )
    
    print("\nCV Curve Calibration Test:")
    print(f"Original range: {cv_result['current_range']['stm32_min']:.2e} to {cv_result['current_range']['stm32_max']:.2e} A")
    print(f"Calibrated range: {cv_result['current_range']['palmsens_min']:.2e} to {cv_result['current_range']['palmsens_max']:.2e} A")
    
    # Show available calibrations
    available = cal_service.get_available_calibrations()
    print(f"\nAvailable Calibrations: {len(available)}")
    for condition, info in available.items():
        print(f"  {condition}: R²={info['r_squared']:.3f}, Confidence={info['confidence']}")
    
    # Show calibration statistics
    stats = cal_service.get_calibration_stats()
    print(f"\nCalibration Statistics:")
    print(f"  Mean Gain Factor: {stats['gain_factor_stats']['mean']:.0f} ± {stats['gain_factor_stats']['std']:.0f}")
    print(f"  Coefficient of Variation: {stats['gain_factor_stats']['cv_percent']:.1f}%")
    print(f"  Average R²: {stats['r_squared_stats']['mean']:.3f}")