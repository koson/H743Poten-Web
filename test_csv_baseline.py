#!/usr/bin/env python3
"""
Test baseline detection after fixing unit conversion issue using CSV file
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
from utils.baseline_detector import BaselineDetector

def test_csv_loading_and_baseline():
    """Test CSV loading and baseline detection with fixed units"""
    print("🧪 Testing CSV Loading and Baseline Detection (Fixed Units)")
    print("=" * 60)
    
    # Test CSV file loading
    csv_file = "test_cv_data_ua.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ Test CSV file not found: {csv_file}")
        return
    
    # Read CSV file
    with open(csv_file, 'r') as f:
        lines = f.readlines()
    
    # Handle instrument file format (FileName: header)
    header_line_idx = 0
    data_start_idx = 1
    
    if lines[0].strip().startswith('FileName:'):
        header_line_idx = 1
        data_start_idx = 2
        print("✅ Detected instrument file format with FileName header")
    
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
    
    # Determine current scaling - NEW LOGIC: keep in µA
    current_unit = headers[current_idx]
    current_scale = 1.0
    if current_unit == 'ma':
        current_scale = 1e3  # milliAmps to microAmps
    elif current_unit == 'na':
        current_scale = 1e-3  # nanoAmps to microAmps
    # For 'ua' or 'uA' - keep as is (no scaling)
    
    print(f"⚡ Current unit: {current_unit}, scale: {current_scale} (keeping in µA)")
    
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
        print("⚠️  WARNING: Current values are very small (< 0.1 µA)")
    elif current_magnitude >= 1.0:
        print("✅ Current values are in normal µA range")
    
    # Test baseline detection
    print("\n🔍 Testing Baseline Detection...")
    detector = BaselineDetector()
    
    try:
        baseline_voltage, baseline_result = detector.detect_baseline(
            np.array(voltage), 
            np.array(current),
            filename="test_cv_data_ua.csv",
            force_method=None  # auto mode
        )
        
        if baseline_result and baseline_result.get('success', True):
            print("✅ Baseline detection successful!")
            print(f"   Algorithm: {baseline_result.get('algorithm', 'Unknown')}")
            print(f"   Confidence: {baseline_result.get('confidence', 1.0):.3f}")
            
            if baseline_voltage is not None and len(baseline_voltage) > 0:
                # baseline_voltage is just voltage array for baseline segment
                baseline_currents = np.array(current)[baseline_result.get('indices', [])]
                if len(baseline_currents) > 0:
                    print(f"   Baseline range: {min(baseline_voltage):.3f} to {max(baseline_voltage):.3f} V")
                    print(f"   Baseline current: {min(baseline_currents):.3f} to {max(baseline_currents):.3f} µA")
                    print(f"   Points in baseline: {len(baseline_voltage)}")
            
            # Check baseline quality
            quality = baseline_result.get('quality_metrics', {})
            if quality:
                print("📈 Quality metrics:")
                for metric, value in quality.items():
                    if isinstance(value, (int, float)):
                        print(f"   {metric}: {value:.4f}")
                    else:
                        print(f"   {metric}: {value}")
        else:
            print("❌ Baseline detection failed!")
            error_msg = baseline_result.get('error', 'Unknown error') if baseline_result else 'No result returned'
            print(f"   Error: {error_msg}")
            
    except Exception as e:
        print(f"❌ Exception during baseline detection: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🏁 Test completed")

if __name__ == "__main__":
    test_csv_loading_and_baseline()