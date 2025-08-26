#!/usr/bin/env python3
"""
Debug script to simulate the exact data flow from backend to frontend
and identify where the peak/baseline coordinate mapping is going wrong.
"""

import sys
sys.path.append('.')
from src.routes.peak_detection import detect_peaks_prominence
import pandas as pd
import json

def debug_data_mapping():
    """Debug the exact data flow that causes misaligned peaks and baselines"""
    
    # Load the test file
    file_path = "Test_data/Stm32/Pipot_Ferro_1_0mM/Pipot_Ferro-1_0mM_100mVpS_E1_scan_02.csv"
    print(f"🔍 Analyzing data mapping for: {file_path}")
    print("=" * 80)
    
    # Load data exactly like the API does
    df = pd.read_csv(file_path, skiprows=1)
    voltage = df['V'].values
    current = df['uA'].values
    
    print(f"📊 Raw data loaded:")
    print(f"   Voltage: {len(voltage)} points, range: {voltage.min():.3f} to {voltage.max():.3f}V")
    print(f"   Current: {len(current)} points, range: {current.min():.3f} to {current.max():.3f}μA")
    print()
    
    # Run peak detection exactly like the API
    result = detect_peaks_prominence(voltage, current)
    
    print(f"🎯 Backend peak detection results:")
    print(f"   Method: {result['method']}")
    print(f"   Total peaks found: {len(result['peaks'])}")
    print()
    
    # Show each peak with its coordinates
    for i, peak in enumerate(result['peaks']):
        print(f"   Peak {i+1} ({peak['type']}):")
        print(f"      Voltage: {peak['voltage']:.3f}V")
        print(f"      Current: {peak['current']:.3f}μA")
        print(f"      Height: {peak['height']:.3f}μA")
        print(f"      Baseline Current: {peak['baseline_current']:.3f}μA")
        print()
    
    # Check baseline info
    baseline = result.get('baseline', {})
    print(f"📈 Baseline information:")
    print(f"   Forward length: {len(baseline.get('forward', []))}")
    print(f"   Reverse length: {len(baseline.get('reverse', []))}")
    print(f"   Full length: {len(baseline.get('full', []))}")
    print()
    
    # Check baseline markers
    markers = baseline.get('markers', {})
    if markers:
        print(f"🎯 Baseline segment markers:")
        
        forward_seg = markers.get('forward_segment', {})
        if forward_seg:
            print(f"   Forward segment:")
            print(f"      Start index: {forward_seg.get('start_idx')}")
            print(f"      End index: {forward_seg.get('end_idx')}")
            print(f"      Voltage range: {forward_seg.get('voltage_start'):.3f} to {forward_seg.get('voltage_end'):.3f}V")
            print()
        
        reverse_seg = markers.get('reverse_segment', {})
        if reverse_seg:
            print(f"   Reverse segment:")
            print(f"      Start index: {reverse_seg.get('start_idx')}")
            print(f"      End index: {reverse_seg.get('end_idx')}")
            print(f"      Voltage range: {reverse_seg.get('voltage_start'):.3f} to {reverse_seg.get('voltage_end'):.3f}V")
            print()
    
    # Check debug info
    debug_info = baseline.get('debug', {})
    if debug_info:
        print(f"🐛 Debug information:")
        print(f"   Data length: {debug_info.get('data_length')}")
        print(f"   Sample voltage range: {debug_info.get('sample_voltage_range')}")
        print(f"   Sample current range: {debug_info.get('sample_current_range')}")
        
        peak_indices = debug_info.get('peak_indices_found', {})
        print(f"   Peak indices found:")
        print(f"      Positive (Ox): {peak_indices.get('positive', [])}")
        print(f"      Negative (Red): {peak_indices.get('negative', [])}")
        print()
    
    # Verify coordinate mapping by checking actual array values
    print(f"🔍 Coordinate verification:")
    for i, peak in enumerate(result['peaks']):
        peak_voltage = peak['voltage']
        peak_current = peak['current']
        
        # Find closest voltage in the original array
        voltage_diffs = abs(voltage - peak_voltage)
        closest_idx = voltage_diffs.argmin()
        actual_voltage = voltage[closest_idx]
        actual_current = current[closest_idx]
        
        print(f"   Peak {i+1}:")
        print(f"      Reported: V={peak_voltage:.3f}V, I={peak_current:.3f}μA")
        print(f"      Closest index: {closest_idx}")
        print(f"      Actual at index: V={actual_voltage:.3f}V, I={actual_current:.3f}μA")
        print(f"      Difference: ΔV={abs(peak_voltage-actual_voltage):.6f}, ΔI={abs(peak_current-actual_current):.6f}")
        print()
    
    # Output raw JSON that would be sent to frontend
    print(f"📤 JSON payload that frontend receives:")
    json_output = json.dumps(result, indent=2)
    print(json_output[:1000] + "..." if len(json_output) > 1000 else json_output)

if __name__ == "__main__":
    debug_data_mapping()