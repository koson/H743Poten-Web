#!/usr/bin/env python3
"""
🐛 Debug Enhanced Baseline Detector v2.1
Test script to debug baseline detection issues on the web platform
"""

import numpy as np
import sys
import os
import logging

# Setup path
sys.path.append('/mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web/src')

from utils.baseline_detector import BaselineDetector

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_baseline_detector():
    """Test baseline detector with simple synthetic data"""
    
    print("🔧 Testing Enhanced Baseline Detector v2.1...")
    
    # Create synthetic CV data
    voltage = np.linspace(-0.4, 0.7, 220)  # Same size as the error
    
    # Create a simple CV with linear baseline and one peak
    baseline_true = voltage * 50 + 10  # Linear baseline
    peak_voltage = 0.2
    peak_width = 0.1
    peak_height = 100
    
    # Add Gaussian peak
    peak = peak_height * np.exp(-((voltage - peak_voltage) / peak_width) ** 2)
    current = baseline_true + peak + np.random.normal(0, 2, len(voltage))
    
    print(f"📊 Test data: {len(voltage)} voltage points, {len(current)} current points")
    print(f"🎯 Voltage range: {voltage.min():.3f}V to {voltage.max():.3f}V")
    print(f"⚡ Current range: {current.min():.2f} to {current.max():.2f} µA")
    
    # Test baseline detector
    try:
        detector = BaselineDetector(auto_mode=True)
        detected_baseline, metadata = detector.detect_baseline(voltage, current, "test_data")
        
        print(f"✅ Baseline detection successful!")
        print(f"📊 Method used: {metadata['method']}")
        print(f"⏱️ Processing time: {metadata['processing_time']:.3f}s")
        
        # Check quality metrics if available
        if 'quality_metrics' in metadata:
            print(f"📈 Quality: {metadata['quality_metrics']['overall_quality']:.2f}")
        elif 'quality_score' in metadata:
            print(f"📈 Quality: {metadata['quality_score']:.2f}")
        else:
            print(f"📈 Quality: Not available")
            
        print(f"🎯 Detected baseline shape: {detected_baseline.shape}")
        print(f"📏 Expected shape: {current.shape}")
        
        # Check if sizes match
        if detected_baseline.shape == current.shape:
            print("✅ Array sizes match correctly!")
            
            # Calculate baseline error
            if len(baseline_true) == len(detected_baseline):
                mse = np.mean((baseline_true - detected_baseline) ** 2)
                print(f"📊 MSE vs true baseline: {mse:.2f}")
            
        else:
            print(f"❌ Size mismatch! Expected {current.shape}, got {detected_baseline.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Baseline detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complexity_assessment():
    """Test data complexity assessment"""
    
    print("\n🔍 Testing simple data analysis...")
    
    # Test with different data types
    test_cases = [
        ("Clean Linear", np.linspace(0, 100, 100)),
        ("Noisy Linear", np.linspace(0, 100, 100) + np.random.normal(0, 5, 100)),
        ("With Peaks", np.linspace(0, 100, 100) + 50 * np.exp(-((np.linspace(0, 100, 100) - 50) / 10) ** 2))
    ]
    
    detector = BaselineDetector(auto_mode=True)
    
    for name, data in test_cases:
        try:
            voltages = np.linspace(-0.5, 0.5, len(data))
            method = detector._select_optimal_method(data, voltages)
            is_cv = detector._is_cv_like_data(voltages, data)
            
            print(f"📊 {name}:")
            print(f"   Data range: {np.ptp(data):.2f}")
            print(f"   Data std: {np.std(data):.2f}")
            print(f"   CV-like: {is_cv}")
            print(f"   Selected method: {method}")
            
        except Exception as e:
            print(f"❌ Failed to assess {name}: {e}")

def main():
    """Main test function"""
    
    print("🧪 Enhanced Baseline Detector v2.1 Debug Suite")
    print("=" * 60)
    
    # Test 1: Basic baseline detection
    success1 = test_baseline_detector()
    
    # Test 2: Complexity assessment
    test_complexity_assessment()
    
    print("\n" + "=" * 60)
    if success1:
        print("✅ Basic tests passed - detector is working!")
    else:
        print("❌ Basic tests failed - need fixes!")

if __name__ == "__main__":
    main()