#!/usr/bin/env python3
"""
Simple debug script to check PiPot current processing
"""

import os
import sys
import pandas as pd
import numpy as np

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

def debug_pipot_simple():
    """Simple debug of PiPot current units"""
    
    # Test with a specific PiPot file that's failing
    test_file = "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_20mVpS_E1_scan_06.csv"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"🔍 Debugging PiPot units: {test_file}")
    
    # Read the raw CSV data
    with open(test_file, 'r') as f:
        lines = f.readlines()
    
    # Check headers
    header_line = lines[1].strip()  # Second line contains headers
    data_lines = lines[2:]  # Data starts from third line
    
    print(f"📄 Header line: {header_line}")
    
    # Parse data
    voltages = []
    currents_raw = []
    
    for line in data_lines:
        parts = line.strip().split(',')
        if len(parts) >= 2:
            try:
                voltage = float(parts[0])
                current = float(parts[1])
                voltages.append(voltage)
                currents_raw.append(current)
            except ValueError:
                continue
    
    voltages = np.array(voltages)
    currents_raw = np.array(currents_raw)
    
    print(f"📊 Raw data stats:")
    print(f"   📈 Voltage range: {voltages.min():.3f} to {voltages.max():.3f} V")
    print(f"   ⚡ Current range (raw): {currents_raw.min():.2e} to {currents_raw.max():.2e} A")
    print(f"   📏 Data points: {len(voltages)}")
    
    # Convert to microamps (like the web API does)
    currents_ua = currents_raw * 1e6  # Convert A to µA
    print(f"   ⚡ Current range (µA): {currents_ua.min():.3f} to {currents_ua.max():.3f} µA")
    
    # Check what magnitude we're dealing with
    current_std = np.std(currents_ua)
    current_mean = np.mean(np.abs(currents_ua))
    current_range = np.max(currents_ua) - np.min(currents_ua)
    
    print(f"   📊 Current statistics (µA):")
    print(f"      🎯 Mean absolute: {current_mean:.3f}")
    print(f"      📏 Standard deviation: {current_std:.3f}")
    print(f"      📈 Range: {current_range:.3f}")
    
    # Check if the magnitude is too small for the baseline detector
    print(f"\n🔧 Baseline detector thresholds:")
    print(f"   📏 Current magnitude: {current_mean:.3f} µA")
    
    if current_mean < 0.1:
        print(f"   ⚠️ WARNING: Current magnitude very low (<0.1 µA)")
        print(f"   ⚠️ This might cause baseline detection issues")
    
    if current_std < 0.01:
        print(f"   ⚠️ WARNING: Current variation very low (<0.01 µA)")
        print(f"   ⚠️ Signal might be too flat for meaningful baseline")
    
    # Test different scaling scenarios
    print(f"\n🔍 Testing different scaling scenarios:")
    
    # Scenario 1: Raw values (what we have)
    print(f"📊 Scenario 1: Raw conversion (A × 1e6 → µA)")
    print(f"   ⚡ Range: {currents_ua.min():.3f} to {currents_ua.max():.3f} µA")
    
    # Scenario 2: If the data was already in µA (no conversion)
    print(f"📊 Scenario 2: If data was already µA (no scaling)")
    print(f"   ⚡ Range: {currents_raw.min():.2e} to {currents_raw.max():.2e} µA")
    
    # Scenario 3: If we scale by smaller factor
    currents_alt = currents_raw * 1e3  # Convert A to mA, then treat as µA
    print(f"📊 Scenario 3: Alternative scaling (A × 1e3)")
    print(f"   ⚡ Range: {currents_alt.min():.6f} to {currents_alt.max():.6f} µA")
    
    return currents_ua

if __name__ == "__main__":
    debug_pipot_simple()