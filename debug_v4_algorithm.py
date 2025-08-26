#!/usr/bin/env python3
"""
Debug V4 Algorithm with Single File
==================================
"""

import numpy as np
import pandas as pd
from baseline_detector_v4 import cv_baseline_detector_v4

def test_v4_with_palmsens():
    """Test v4 algorithm with Palmsens data"""
    
    file_path = "Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_100mVpS_E1_scan_05.csv"
    
    print("🧪 Testing V4 Algorithm with Palmsens Data")
    print("=" * 50)
    
    # Load data in original format (µA)
    df = pd.read_csv(file_path, skiprows=1)  # Skip the filename line
    print(f"📋 Columns: {list(df.columns)}")
    
    voltage = pd.to_numeric(df['V'], errors='coerce').dropna().values
    current_ua = pd.to_numeric(df['uA'], errors='coerce').dropna().values  # Keep in µA
    
    print(f"📈 Data points: {len(voltage)}")
    print(f"⚡ Voltage range: [{voltage.min():.3f}, {voltage.max():.3f}] V")
    print(f"⚡ Current range: [{current_ua.min():.2f}, {current_ua.max():.2f}] µA")
    
    # Test with µA (original units)
    print("\n🔬 Testing with µA units (original):")
    try:
        forward_baseline, reverse_baseline, info = cv_baseline_detector_v4(voltage, current_ua)
        print(f"✅ V4 Success!")
        print(f"📊 Forward baseline range: [{forward_baseline.min():.2f}, {forward_baseline.max():.2f}] µA")
        print(f"📊 Reverse baseline range: [{reverse_baseline.min():.2f}, {reverse_baseline.max():.2f}] µA")
        print(f"📄 Info: {info}")
    except Exception as e:
        print(f"❌ V4 Failed: {e}")
    
    # Test with A (converted units)
    print("\n🔬 Testing with A units (converted):")
    current_a = current_ua * 1e-6  # Convert to A
    print(f"⚡ Current range (A): [{current_a.min():.2e}, {current_a.max():.2e}] A")
    
    try:
        forward_baseline, reverse_baseline, info = cv_baseline_detector_v4(voltage, current_a)
        print(f"✅ V4 Success!")
        print(f"📊 Forward baseline range: [{forward_baseline.min():.2e}, {forward_baseline.max():.2e}] A")
        print(f"📊 Reverse baseline range: [{reverse_baseline.min():.2e}, {reverse_baseline.max():.2e}] A")
        print(f"📄 Info: {info}")
    except Exception as e:
        print(f"❌ V4 Failed: {e}")

if __name__ == "__main__":
    test_v4_with_palmsens()