#!/usr/bin/env python3
"""
Debug baseline detector with verbose logging for PiPot files
"""

import os
import sys
import pandas as pd
import numpy as np
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from baseline_detector_voltage_windows import voltage_window_baseline_detector

def debug_baseline_verbose():
    """Debug baseline detector with verbose output"""
    
    # Test with a specific PiPot file that's failing
    test_file = "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_20mVpS_E1_scan_06.csv"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"🔍 Debugging baseline detector: {test_file}")
    
    # Read the raw CSV data
    with open(test_file, 'r') as f:
        lines = f.readlines()
    
    # Parse data
    voltages = []
    currents_raw = []
    
    for line in lines[2:]:  # Skip header lines
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
    currents_ua = np.array(currents_raw) * 1e6  # Convert A to µA
    
    print(f"📊 Data summary:")
    print(f"   📈 Voltage: {voltages.min():.3f} to {voltages.max():.3f} V")
    print(f"   ⚡ Current: {currents_ua.min():.3f} to {currents_ua.max():.3f} µA")
    print(f"   📏 Points: {len(voltages)}")
    
    # Run baseline detector with detailed logging
    print(f"\n🔧 Running baseline detector with verbose logging...")
    print(f"=" * 80)
    
    try:
        result = voltage_window_baseline_detector(voltages, currents_ua)
        
        print(f"=" * 80)
        print(f"🎯 Baseline detection result:")
        
        if isinstance(result, dict):
            print(f"   ✅ Success! Type: dict")
            print(f"   📊 Keys: {list(result.keys())}")
            if 'full' in result:
                baseline = result['full']
                print(f"   📈 Baseline range: {np.min(baseline):.3f} to {np.max(baseline):.3f} µA")
            if 'metadata' in result:
                metadata = result['metadata']
                print(f"   📋 Metadata: {metadata}")
        elif isinstance(result, tuple):
            print(f"   ⚠️ Tuple result (fallback): {len(result)} elements")
            if len(result) >= 2:
                forward, reverse = result[:2]
                print(f"   📈 Forward baseline: {len(forward)} points")
                print(f"   📉 Reverse baseline: {len(reverse)} points")
        else:
            print(f"   ❌ Unexpected result type: {type(result)}")
            
    except Exception as e:
        print(f"❌ Error in baseline detection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_baseline_verbose()