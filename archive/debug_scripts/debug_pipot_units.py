#!/usr/bin/env python3
"""
Debug script to check PiPot current unit conversion and baseline detection
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from baseline_detector_voltage_windows import voltage_window_baseline_detector

def debug_pipot_units():
    """Debug PiPot unit conversion issue"""
    
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
    
    # Test baseline detection with both raw and converted currents
    print(f"\n🔧 Testing baseline detection:")
    
    # Test 1: With raw Ampere values
    print(f"📊 Test 1: Raw Ampere values")
    try:
        result_raw = voltage_window_baseline_detector(voltages, currents_raw)
        if result_raw:
            print(f"   ✅ Baseline detected!")
            print(f"   📈 Forward segments: {len(result_raw.get('forward_segments', []))}")
            print(f"   📉 Reverse segments: {len(result_raw.get('reverse_segments', []))}")
            print(f"   📊 Full baseline range: {np.min(result_raw['full']):.2e} to {np.max(result_raw['full']):.2e}")
        else:
            print(f"   ❌ No baseline detected with raw values")
    except Exception as e:
        print(f"   ❌ Error with raw values: {e}")
    
    # Test 2: With microamp values
    print(f"📊 Test 2: Microamp values")
    try:
        result_ua = voltage_window_baseline_detector(voltages, currents_ua)
        if result_ua:
            print(f"   ✅ Baseline detected!")
            print(f"   📈 Forward segments: {len(result_ua.get('forward_segments', []))}")
            print(f"   📉 Reverse segments: {len(result_ua.get('reverse_segments', []))}")
            print(f"   📊 Full baseline range: {np.min(result_ua['full']):.3f} to {np.max(result_ua['full']):.3f}")
        else:
            print(f"   ❌ No baseline detected with µA values")
    except Exception as e:
        print(f"   ❌ Error with µA values: {e}")
    
    # Plot comparison
    print(f"\n📈 Creating comparison plot...")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot raw Ampere data
    ax1.plot(voltages, currents_raw, 'b-', linewidth=1, label='Raw Current (A)')
    ax1.set_xlabel('Voltage (V)')
    ax1.set_ylabel('Current (A)')
    ax1.set_title('PiPot Raw Current Data (Amperes)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Plot microamp data
    ax2.plot(voltages, currents_ua, 'r-', linewidth=1, label='Current (µA)')
    ax2.set_xlabel('Voltage (V)')
    ax2.set_ylabel('Current (µA)')
    ax2.set_title('PiPot Current Data (Microamps)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    if result_ua:
        # Overlay baseline if detected
        ax2.plot(voltages, result_ua['full'], 'g--', linewidth=2, label='Baseline')
        ax2.legend()
    
    plt.tight_layout()
    output_file = 'pipot_units_debug.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"📊 Plot saved: {output_file}")
    plt.close()
    
    # Check what the web API scaling logic does
    print(f"\n🔍 Web API scaling logic:")
    header_parts = header_line.split(',')
    current_unit = header_parts[1].lower().strip() if len(header_parts) > 1 else 'unknown'
    print(f"   📋 Detected current unit: '{current_unit}'")
    
    # Simulate STM32 file detection
    is_stm32_file = 'pipot' in test_file.lower() or 'stm32' in test_file.lower()
    print(f"   🔧 Is STM32 file: {is_stm32_file}")
    
    if current_unit == 'a' and is_stm32_file:
        current_scale = 1e6  # STM32 'A' values are actually µA, so multiply by 1e6 to convert from A to µA
        print(f"   ⚖️ Applied scale factor: {current_scale} (STM32 A → µA)")
    elif current_unit == 'a' and not is_stm32_file:
        current_scale = 1e6  # True Amperes to microAmps
        print(f"   ⚖️ Applied scale factor: {current_scale} (True A → µA)")
    else:
        current_scale = 1.0
        print(f"   ⚖️ Applied scale factor: {current_scale}")
    
    final_currents = currents_raw * current_scale
    print(f"   ⚡ Final current range: {final_currents.min():.3f} to {final_currents.max():.3f} µA")
    
    return result_ua

if __name__ == "__main__":
    debug_pipot_units()