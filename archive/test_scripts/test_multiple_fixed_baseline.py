#!/usr/bin/env python3
"""
Test fixed baseline detection with multiple files
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import logging
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Import our existing baseline detector
import sys
sys.path.append('.')
from baseline_detector_voltage_windows import voltage_window_baseline_detector

# Import functions from fixed_baseline_test.py
from fixed_baseline_test import load_and_process_csv, create_proper_baseline_plot

def test_multiple_files():
    """Test with several different files to verify the fix"""
    
    print("🧪 Testing Fixed Baseline Detection - Multiple Files")
    print("=" * 60)
    
    # Test files from different categories
    test_files = [
        "Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_50mVpS_E3_scan_08.csv",
        "Test_data/Palmsens/Palmsens_1.0mM/Palmsens_1.0mM_CV_200mVpS_E1_scan_05.csv", 
        "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_100mVpS_E4_scan_05.csv",
        "Test_data/Stm32/Pipot_Ferro_1_0mM/Pipot_Ferro_1_0mM_20mVpS_E4_scan_05.csv"
    ]
    
    results = []
    
    for i, file_path in enumerate(test_files):
        print(f"\n📁 Test {i+1}/4: {os.path.basename(file_path)}")
        
        if not os.path.exists(file_path):
            print(f"   ❌ File not found, skipping...")
            continue
        
        # Process file
        voltage_data, current_data, baseline_result, error = load_and_process_csv(file_path)
        
        if error:
            print(f"   ❌ Error: {error}")
            continue
        
        print(f"   ✅ Data: {len(voltage_data)} points")
        print(f"   📊 V: [{voltage_data.min():.3f}, {voltage_data.max():.3f}] V")
        print(f"   📈 I: [{current_data.min():.1f}, {current_data.max():.1f}] µA")
        print(f"   🔍 Forward: {len(baseline_result['forward_baseline_v'])} pts")
        print(f"   🔄 Reverse: {len(baseline_result['reverse_baseline_v'])} pts")
        
        # Create plot
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        plot_filename = f"test_{i+1}_{base_name}_fixed.png"
        
        try:
            quality_info = create_proper_baseline_plot(
                file_path, voltage_data, current_data, baseline_result, plot_filename
            )
            
            print(f"   ✅ Plot: {plot_filename}")
            print(f"   📊 Quality: {quality_info['quality']}")
            print(f"   📈 Forward R²: {quality_info['forward_r2']:.3f}")
            print(f"   📈 Reverse R²: {quality_info['reverse_r2']:.3f}")
            print(f"   📊 Avg R²: {quality_info['avg_r2']:.3f}")
            
            results.append({
                'file': os.path.basename(file_path),
                'quality': quality_info['quality'],
                'forward_r2': quality_info['forward_r2'],
                'reverse_r2': quality_info['reverse_r2'],
                'avg_r2': quality_info['avg_r2'],
                'total_points': quality_info['total_points']
            })
            
        except Exception as e:
            print(f"   ❌ Plot failed: {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 SUMMARY OF FIXED BASELINE DETECTION")
    print(f"✅ Successful tests: {len(results)}")
    
    if results:
        print("\n🎯 QUALITY BREAKDOWN:")
        excellent = sum(1 for r in results if "EXCELLENT" in r['quality'])
        good = sum(1 for r in results if "GOOD" in r['quality'])
        fair = sum(1 for r in results if "FAIR" in r['quality'])
        poor = sum(1 for r in results if "POOR" in r['quality'])
        
        print(f"   🟢 EXCELLENT: {excellent}")
        print(f"   ✅ GOOD: {good}")
        print(f"   ⚠️ FAIR: {fair}")
        print(f"   ❌ POOR: {poor}")
        
        avg_r2 = np.mean([r['avg_r2'] for r in results])
        avg_points = np.mean([r['total_points'] for r in results])
        
        print(f"\n📊 Average R²: {avg_r2:.3f}")
        print(f"📊 Average baseline points: {avg_points:.1f}")
        
        print("\n📋 DETAILED RESULTS:")
        for r in results:
            print(f"   {r['file'][:40]:40} | {r['quality']:15} | R²: {r['avg_r2']:.3f} | Pts: {r['total_points']}")
    
    print(f"\n🎯 All test plots created successfully!")
    print("🔍 Compare with original problematic image to see improvements")

if __name__ == "__main__":
    test_multiple_files()