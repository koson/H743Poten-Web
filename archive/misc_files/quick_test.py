#!/usr/bin/env python3
"""
Quick baseline test - minimal version
"""

import sys
import os
import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from routes.peak_detection import detect_peaks_prominence, detect_improved_baseline

def quick_test(file_path):
    """Quick test function"""
    print(f"\n{'='*50}")
    print(f"Testing: {os.path.basename(file_path)}")
    print(f"{'='*50}")
    
    # Load data
    try:
        df = pd.read_csv(file_path, skiprows=1)
        if 'V' in df.columns and 'uA' in df.columns:
            voltage, current = df['V'].values, df['uA'].values
        elif 'V' in df.columns and 'A' in df.columns:
            voltage, current = df['V'].values, df['A'].values * 1e6
        else:
            print("❌ Unknown format")
            return False
    except Exception as e:
        print(f"❌ Load error: {e}")
        return False
    
    print(f"📊 Data: {len(voltage)} points, V:[{voltage.min():.3f}, {voltage.max():.3f}], I:[{current.min():.1f}, {current.max():.1f}]µA")
    
    # Test baseline
    try:
        baseline_result = detect_improved_baseline(voltage, current)
        if baseline_result is None:
            print("❌ Baseline detection failed")
            return False
            
        baseline_forward, baseline_reverse, _ = baseline_result
        print(f"✅ Baseline: Forward({len(baseline_forward)}) [{baseline_forward.min():.1f}, {baseline_forward.max():.1f}]µA")
        print(f"             Reverse({len(baseline_reverse)}) [{baseline_reverse.min():.1f}, {baseline_reverse.max():.1f}]µA")
        
    except Exception as e:
        print(f"❌ Baseline error: {e}")
        return False
    
    # Test peaks
    try:
        peaks_data = detect_peaks_prominence(voltage, current, prominence=50, width=3)
        if peaks_data and 'peaks' in peaks_data:
            peaks = peaks_data['peaks']
            ox_count = sum(1 for p in peaks if p['type'] == 'oxidation')
            red_count = sum(1 for p in peaks if p['type'] == 'reduction')
            print(f"🎯 Peaks: {len(peaks)} total (Ox:{ox_count}, Red:{red_count})")
            
            for i, peak in enumerate(peaks[:4]):  # Show first 4 peaks
                print(f"   {peak['type'][:3]}: {peak['voltage']:.3f}V, {peak['current']:.1f}µA, h:{peak['height']:.1f}µA, bl:{peak['baseline_current']:.1f}µA")
                
        else:
            print("❌ No peaks found")
            return False
            
    except Exception as e:
        print(f"❌ Peak error: {e}")
        return False
    
    return True

def run_quick_tests():
    """Run quick tests on sample files"""
    test_files = [
        r"D:\GitHubRepos\__Potentiostat\poten-2025\H743Poten\H743Poten-Web\Test_data\Palmsens\Palmsens_5mM\Palmsens_5mM_CV_400mVpS_E3_scan_08.csv",
        r"D:\GitHubRepos\__Potentiostat\poten-2025\H743Poten\H743Poten-Web\Test_data\Palmsens\Palmsens_5mM\Palmsens_5mM_CV_20mVpS_E1_scan_05.csv",
        r"D:\GitHubRepos\__Potentiostat\poten-2025\H743Poten\H743Poten-Web\Test_data\Stm32\Pipot_Ferro_5_0mM\Pipot_Ferro_5_0mM_50mVpS_E4_scan_05.csv"
    ]
    
    results = []
    for file_path in test_files:
        if os.path.exists(file_path):
            success = quick_test(file_path)
            results.append((os.path.basename(file_path), success))
        else:
            print(f"❌ File not found: {file_path}")
            results.append((os.path.basename(file_path), False))
    
    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    passed = sum(1 for _, success in results if success)
    print(f"Total: {len(results)}, Passed: {passed}, Failed: {len(results)-passed}")
    
    for filename, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {filename}")

if __name__ == "__main__":
    run_quick_tests()