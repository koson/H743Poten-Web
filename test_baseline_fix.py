#!/usr/bin/env python3
"""
Test baseline detector with updated MAX_TOTAL_LENGTH
"""

import numpy as np
import pandas as pd
import sys
import os

# Add the current directory to the path
sys.path.append(os.getcwd())

from baseline_detector_voltage_windows import voltage_window_baseline_detector

def test_baseline_detector():
    """Test baseline detector with real converted data"""
    
    print("🔧 Testing baseline detector with updated MAX_TOTAL_LENGTH...")
    
    # Load a real converted file
    file_path = "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_100mVpS_E1_scan_06.csv"
    
    try:
        # Read the CSV file
        df = pd.read_csv(file_path, skiprows=1)  # Skip the filename header
        voltage = df.iloc[:, 0].values  # First column
        current = df.iloc[:, 1].values  # Second column (now in µA)
        
        print(f"📊 Loaded data: {len(voltage)} points")
        print(f"📊 Voltage range: {voltage.min():.3f}V to {voltage.max():.3f}V")
        print(f"📊 Current range: {current.min():.3f}µA to {current.max():.3f}µA")
        
        # Test baseline detection
        forward_baseline, reverse_baseline, info = voltage_window_baseline_detector(
            voltage, current, peak_regions=[]
        )
        
        print(f"\n✅ Baseline detection completed!")
        print(f"📈 Forward baseline range: {forward_baseline.min():.3f} to {forward_baseline.max():.3f} µA")
        print(f"📉 Reverse baseline range: {reverse_baseline.min():.3f} to {reverse_baseline.max():.3f} µA")
        
        # Check if baseline is flat (all zeros)
        forward_zero = np.all(forward_baseline == 0)
        reverse_zero = np.all(reverse_baseline == 0)
        
        if forward_zero and reverse_zero:
            print("❌ ISSUE: Both baselines are flat (all zeros)")
        else:
            print("✅ SUCCESS: Baselines are not flat")
            
        print(f"📊 Info: {info}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_baseline_detector()