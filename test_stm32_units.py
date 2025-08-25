#!/usr/bin/env python3
"""
Test STM32 file loading with fixed unit conversion
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
from utils.baseline_detector import BaselineDetector

def test_stm32_file_loading():
    """Test STM32 CSV loading and baseline detection with fixed units"""
    print("🧪 Testing STM32 File Loading and Baseline Detection (Fixed Units)")
    print("=" * 65)
    
    # Test STM32 CSV file
    stm32_file = "Test_data/Stm32/Pipot_Ferro_1_0mM/Pipot_Ferro-1_0mM_50mVpS_E1_scan_06.csv"
    
    if not os.path.exists(stm32_file):
        print(f"❌ STM32 test file not found: {stm32_file}")
        return
    
    # Read CSV file using the same logic as the backend
    with open(stm32_file, 'r') as f:
        lines = f.readlines()
    
    # Handle instrument file format (FileName: header)
    header_line_idx = 0
    data_start_idx = 1
    
    if lines[0].strip().startswith('FileName:'):
        header_line_idx = 1
        data_start_idx = 2
        print("✅ Detected STM32 instrument file format with FileName header")
    
    # Parse headers
    headers = [h.strip().lower() for h in lines[header_line_idx].strip().split(',')]
    print(f"📂 Headers found: {headers}")
    
    # Find voltage and current columns
    voltage_idx = -1
    current_idx = -1
    
    for i, header in enumerate(headers):
        if header in ['v', 'voltage'] or 'volt' in header or 'potential' in header:
            voltage_idx = i
        elif header in ['a', 'ua', 'ma', 'na', 'current'] or 'amp' in header or 'curr' in header:
            current_idx = i
    
    if voltage_idx == -1 or current_idx == -1:
        print(f"❌ Could not find voltage or current columns in headers: {headers}")
        return
    
    # NEW STM32 DETECTION LOGIC
    current_unit = headers[current_idx]
    current_scale = 1.0
    
    # Check if this is STM32/Pipot file (uses 'A' header but values are actually in µA)
    is_stm32_file = (
        'pipot' in stm32_file.lower() or 
        'stm32' in stm32_file.lower() or
        (current_unit == 'a' and lines[0].strip().startswith('FileName:'))
    )
    
    if current_unit == 'ma':
        current_scale = 1e3  # milliAmps to microAmps
    elif current_unit == 'na':
        current_scale = 1e-3  # nanoAmps to microAmps
    elif current_unit == 'a' and is_stm32_file:
        current_scale = 1e6  # STM32 'A' values are actually µA, so multiply by 1e6 to convert from A to µA
        print("🎯 Detected STM32/Pipot file - treating 'A' column as µA values")
    elif current_unit == 'a' and not is_stm32_file:
        current_scale = 1e6  # True Amperes to microAmps
    # For 'ua' or 'uA' - keep as is (no scaling)
    
    print(f"⚡ Current unit: {current_unit}, scale: {current_scale} (keeping in µA), STM32: {is_stm32_file}")
    
    # Parse data
    voltage = []
    current = []
    
    for i in range(data_start_idx, len(lines)):
        line = lines[i].strip()
        if not line:
            continue
            
        values = line.split(',')
        if len(values) > max(voltage_idx, current_idx):
            try:
                v = float(values[voltage_idx])
                c = float(values[current_idx]) * current_scale
                voltage.append(v)
                current.append(c)
            except ValueError:
                continue
    
    if len(voltage) == 0 or len(current) == 0:
        print("❌ No valid data points found")
        return
    
    print(f"📊 Loaded {len(voltage)} data points")
    print(f"🔋 Voltage range: {min(voltage):.3f} to {max(voltage):.3f} V")
    print(f"⚡ Current range: {min(current):.3f} to {max(current):.3f} µA")
    print(f"📏 Current magnitude: {max(abs(min(current)), abs(max(current))):.3f} µA")
    
    # Check if current values are in reasonable µA range
    current_magnitude = max(abs(min(current)), abs(max(current)))
    if current_magnitude < 0.1:
        print("❌ CRITICAL: Current values still too small (< 0.1 µA)")
        print("    Unit conversion not working properly!")
        return
    elif current_magnitude >= 1.0:
        print("✅ Current values are in correct µA range - STM32 unit fix successful!")
    
    # Show before/after comparison
    raw_value = float(lines[data_start_idx].split(',')[current_idx])
    converted_value = raw_value * current_scale
    print(f"📈 Example conversion: {raw_value:.2e} A → {converted_value:.3f} µA")
    
    # Test baseline detection
    print("\n🔍 Testing Baseline Detection with STM32 data...")
    detector = BaselineDetector()
    
    try:
        baseline_voltage, baseline_result = detector.detect_baseline(
            np.array(voltage), 
            np.array(current),
            filename=stm32_file,
            force_method=None  # auto mode
        )
        
        if baseline_result and baseline_result.get('success', True):
            print("✅ Baseline detection successful with STM32 data!")
            print(f"   Algorithm: {baseline_result.get('algorithm', 'Unknown')}")
            print(f"   Confidence: {baseline_result.get('confidence', 1.0):.3f}")
            
            if baseline_voltage is not None and len(baseline_voltage) > 0:
                baseline_currents = np.array(current)[baseline_result.get('indices', [])]
                if len(baseline_currents) > 0:
                    print(f"   Baseline range: {min(baseline_voltage):.3f} to {max(baseline_voltage):.3f} V")
                    print(f"   Baseline current: {min(baseline_currents):.3f} to {max(baseline_currents):.3f} µA")
                    print(f"   Points in baseline: {len(baseline_voltage)}")
        else:
            print("❌ Baseline detection failed with STM32 data")
            error_msg = baseline_result.get('error', 'Unknown error') if baseline_result else 'No result returned'
            print(f"   Error: {error_msg}")
            
    except Exception as e:
        print(f"❌ Exception during baseline detection: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 65)
    print("🏁 STM32 test completed")

if __name__ == "__main__":
    test_stm32_file_loading()