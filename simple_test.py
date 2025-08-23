#!/usr/bin/env python3
"""
Ultra-quick baseline test for development
Usage: python simple_test.py [filename]
"""

import sys
import os
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_one_file(file_path):
    """Test baseline detection on one file"""
    from routes.peak_detection import detect_peaks_prominence, detect_improved_baseline_2step
    
    print(f"Testing: {os.path.basename(file_path)}")
    
    # Load
    df = pd.read_csv(file_path, skiprows=1)
    if 'uA' in df.columns:
        v, i = df['V'].values, df['uA'].values
    else:
        v, i = df['V'].values, df['A'].values * 1e6
    
    # Baseline
    result = detect_improved_baseline_2step(v, i)
    if result is None:
        print("❌ Baseline failed")
        return
    
    bf, br, _ = result
    print(f"✅ Baseline: F({len(bf)})=[{bf.min():.1f},{bf.max():.1f}] R({len(br)})=[{br.min():.1f},{br.max():.1f}]")
    
    # Peaks
    peaks_data = detect_peaks_prominence(v, i)
    if peaks_data and 'peaks' in peaks_data:
        peaks = peaks_data['peaks']
        print(f"🎯 {len(peaks)} peaks:")
        for p in peaks:
            print(f"   {p['type'][:3]}: {p['voltage']:.3f}V, h={p['height']:.1f}µA, bl={p['baseline_current']:.1f}µA")
    else:
        print("❌ No peaks")

def main():
    # Default test files - use Linux paths for WSL
    test_files = [
        "Test_data/Palmsens/Palmsens_5mM/Palmsens_5mM_CV_400mVpS_E3_scan_08.csv",
        "Test_data/Palmsens/Palmsens_5mM/Palmsens_5mM_CV_20mVpS_E1_scan_05.csv"
    ]
    
    if len(sys.argv) > 1:
        # Test specific file
        test_one_file(sys.argv[1])
    else:
        # Test default files
        for f in test_files:
            if os.path.exists(f):
                test_one_file(f)
                print()
            else:
                print(f"File not found: {f}")

if __name__ == "__main__":
    main()