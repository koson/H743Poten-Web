#!/usr/bin/env python3
"""
Debug script for specific file frontend rendering issues
"""

import sys
import os
sys.path.append('.')

import pandas as pd
import numpy as np
import logging
import json

# Set logging level to reduce noise
logging.basicConfig(level=logging.ERROR)

def debug_file(file_path):
    """Debug specific file frontend rendering"""
    print(f"🔍 Debugging frontend rendering for: {file_path}")
    print("=" * 80)
    
    try:
        # Load and analyze the file
        df = pd.read_csv(file_path, skiprows=1)
        voltage = df['V'].values
        current = df['uA'].values
        
        print(f"📊 Raw data:")
        print(f"   Voltage: {len(voltage)} points, range: {voltage.min():.3f} to {voltage.max():.3f}V")
        print(f"   Current: {len(current)} points, range: {current.min():.3f} to {current.max():.3f}μA")
        print()
        
        # Run detection
        from src.routes.peak_detection import detect_peaks_prominence
        result = detect_peaks_prominence(voltage, current)
        
        peaks = result.get('peaks', [])
        rejected_peaks = result.get('rejected_peaks', [])
        baseline_info = result.get('baseline', {})
        
        print(f"🎯 Backend detection results:")
        print(f"   Method: {result.get('method', 'unknown')}")
        print(f"   Total peaks found: {len(peaks)}")
        print(f"   Rejected peaks: {len(rejected_peaks)}")
        print()
        
        # Show valid peaks
        if peaks:
            print("✅ Valid Peaks:")
            for i, peak in enumerate(peaks):
                print(f"   {i+1}. {peak['type'].title()}: V={peak['voltage']:.3f}V, I={peak['current']:.3f}μA")
                print(f"      Height: {peak['height']:.3f}μA, Baseline: {peak['baseline_current']:.3f}μA")
                print(f"      Confidence: {peak['confidence']:.1f}%, Enabled: {peak['enabled']}")
                print()
        
        # Show rejected peaks
        if rejected_peaks:
            print("❌ Rejected Peaks:")
            for i, peak in enumerate(rejected_peaks):
                print(f"   {i+1}. {peak['type'].title()}: V={peak['voltage']:.3f}V, I={peak['current']:.3f}μA")
                print(f"      Reason: {peak['reason']}")
                print()
        
        # Check baseline
        baseline_full = baseline_info.get('full', [])
        if baseline_full:
            print(f"📈 Baseline info:")
            print(f"   Length: {len(baseline_full)}")
            print(f"   Range: {min(baseline_full):.3f} to {max(baseline_full):.3f}μA")
            print(f"   Method: {baseline_info.get('params', {}).get('method', 'unknown')}")
            print()
        
        # Generate JSON payload as frontend would receive
        json_payload = {
            "success": True,
            "peaks": peaks,
            "rejected_peaks": rejected_peaks,
            "baseline": baseline_info,
            "previewData": {
                "voltage": voltage.tolist(),
                "current": current.tolist(),
                "peaks": peaks
            }
        }
        
        print(f"📤 JSON payload structure:")
        print(f"   success: {json_payload['success']}")
        print(f"   peaks: {len(json_payload['peaks'])} items")
        print(f"   rejected_peaks: {len(json_payload['rejected_peaks'])} items")
        print(f"   baseline.full: {len(json_payload['baseline'].get('full', []))} points")
        print(f"   previewData.voltage: {len(json_payload['previewData']['voltage'])} points")
        print(f"   previewData.current: {len(json_payload['previewData']['current'])} points")
        print()
        
        # Check for potential frontend issues
        print(f"🔍 Potential frontend issues:")
        
        # Check peak coordinates are within data range
        for i, peak in enumerate(peaks):
            v_min, v_max = voltage.min(), voltage.max()
            i_min, i_max = current.min(), current.max()
            
            if not (v_min <= peak['voltage'] <= v_max):
                print(f"   ⚠️  Peak {i+1} voltage {peak['voltage']:.3f}V outside data range [{v_min:.3f}, {v_max:.3f}]")
            
            if not (i_min <= peak['current'] <= i_max):
                print(f"   ⚠️  Peak {i+1} current {peak['current']:.3f}μA outside data range [{i_min:.3f}, {i_max:.3f}]")
        
        # Check for NaN or infinity values
        if any(np.isnan(voltage)) or any(np.isinf(voltage)):
            print(f"   ⚠️  Voltage data contains NaN or infinity values")
        
        if any(np.isnan(current)) or any(np.isinf(current)):
            print(f"   ⚠️  Current data contains NaN or infinity values")
        
        # Check peak data integrity
        for i, peak in enumerate(peaks):
            for key, value in peak.items():
                if isinstance(value, (int, float)) and (np.isnan(value) or np.isinf(value)):
                    print(f"   ⚠️  Peak {i+1} has invalid {key}: {value}")
        
        print(f"   ✅ No obvious data integrity issues found")
        print()
        
        return json_payload
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    file_path = "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_100mVpS_E1_scan_03.csv"
    debug_file(file_path)