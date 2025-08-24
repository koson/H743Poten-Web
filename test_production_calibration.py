#!/usr/bin/env python3
"""
Test the Production Calibration API Directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_calibration_service():
    """Test the calibration service directly"""
    
    from src.services.production_calibration_service import ProductionCalibrationService
    
    print("🧪 Testing Production Calibration Service")
    print("=" * 50)
    
    # Initialize service
    cal_service = ProductionCalibrationService()
    
    # Test 1: Service Info
    print("\n1. Service Information:")
    stats = cal_service.get_calibration_stats()
    print(f"   📊 Total Calibration Conditions: {stats['total_conditions']}")
    print(f"   📊 Average Gain Factor: {stats['gain_factor_stats']['mean']:.0f} ± {stats['gain_factor_stats']['std']:.0f}")
    print(f"   📊 Coefficient of Variation: {stats['gain_factor_stats']['cv_percent']:.1f}%")
    print(f"   📊 Average R²: {stats['r_squared_stats']['mean']:.3f}")
    
    # Test 2: Available Calibrations
    print("\n2. Available Calibrations:")
    available = cal_service.get_available_calibrations()
    for condition, info in available.items():
        print(f"   {condition}: R²={info['r_squared']:.3f}, Confidence={info['confidence']}, Points={info['data_points']}")
    
    # Test 3: Single Current Calibration
    print("\n3. Single Current Calibration:")
    test_current = 1e-4  # 100 µA
    
    # Default calibration
    result = cal_service.calibrate_current_stm32_to_palmsens(test_current)
    print(f"   Default: {test_current:.2e} A → {result['calibrated_current']:.2e} A (gain={result['gain_factor']:.0f})")
    
    # Condition-specific calibration
    result = cal_service.calibrate_current_stm32_to_palmsens(test_current, 100.0, 5.0)
    print(f"   100mV/s, 5mM: {test_current:.2e} A → {result['calibrated_current']:.2e} A (confidence={result['confidence']})")
    
    result = cal_service.calibrate_current_stm32_to_palmsens(test_current, 400.0, 5.0)
    print(f"   400mV/s, 5mM: {test_current:.2e} A → {result['calibrated_current']:.2e} A (confidence={result['confidence']})")
    
    # Test 4: CV Curve Calibration
    print("\n4. CV Curve Calibration:")
    test_cv_data = [
        [-0.5, -1e-4],
        [-0.25, -5e-5],
        [0.0, 0],
        [0.25, 5e-5],
        [0.5, 1e-4]
    ]
    
    cv_result = cal_service.calibrate_cv_curve(test_cv_data, 200.0, 5.0)
    print(f"   Original Range: {cv_result['current_range']['stm32_min']:.2e} to {cv_result['current_range']['stm32_max']:.2e} A")
    print(f"   Calibrated Range: {cv_result['current_range']['palmsens_min']:.2e} to {cv_result['current_range']['palmsens_max']:.2e} A")
    print(f"   Calibration: {cv_result['calibration_info']['method']} (confidence={cv_result['calibration_info']['confidence']})")
    
    # Test 5: Real Data Calibration
    print("\n5. Real Data Calibration:")
    try:
        from src.services.hybrid_data_manager import HybridDataManager
        hybrid_manager = HybridDataManager()
        
        # Test with measurement ID 67 (STM32)
        cv_data = hybrid_manager.get_cv_data(67)
        if cv_data:
            cv_result = cal_service.calibrate_cv_curve(cv_data, 100.0, 5.0)
            print(f"   ✅ Measurement 67: {cv_result['data_points']} points calibrated")
            print(f"   Original: {cv_result['current_range']['stm32_min']:.2e} to {cv_result['current_range']['stm32_max']:.2e} A")
            print(f"   Calibrated: {cv_result['current_range']['palmsens_min']:.2e} to {cv_result['current_range']['palmsens_max']:.2e} A")
            print(f"   Method: {cv_result['calibration_info']['method']} (R²={cv_result['calibration_info']['r_squared']:.3f})")
        else:
            print("   ❌ No CV data found for measurement 67")
    except Exception as e:
        print(f"   ❌ Error accessing real data: {e}")
    
    print(f"\n🎯 Service Testing Complete!")

if __name__ == "__main__":
    test_calibration_service()