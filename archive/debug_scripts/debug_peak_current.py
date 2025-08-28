#!/usr/bin/env python3
"""
Debug peak current values - check if current values match peak positions
"""

import requests
import csv
import numpy as np
import matplotlib.pyplot as plt

def load_stm32_data(filename):
    """Load STM32 CSV data"""
    voltage = []
    current = []
    
    with open(filename, 'r') as f:
        lines = f.readlines()
        
        # Skip header lines (FileName: and V,uA)
        data_start = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('V,uA') or 'V,uA' in line:
                data_start = i + 1
                break
        
        # Read data
        for line in lines[data_start:]:
            line = line.strip()
            if line and ',' in line:
                try:
                    parts = line.split(',')
                    v = float(parts[0])
                    i = float(parts[1])
                    voltage.append(v)
                    current.append(i)
                except (ValueError, IndexError):
                    continue
    
    return voltage, current

def debug_peak_current():
    """Debug peak current values vs actual data"""
    
    filename = 'Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_100mVpS_E1_scan_08.csv'
    
    # Load actual data
    voltage, current = load_stm32_data(filename)
    
    print(f'🔍 Debugging Peak Current Values')
    print(f'📁 File: {filename}')
    print(f'📊 Data points: {len(voltage)}')
    
    # Get API results
    data = {
        'dataFiles': [{
            'voltage': voltage,
            'current': current
        }]
    }
    
    response = requests.post('http://127.0.0.1:8080/get-peaks/enhanced_v4_improved', 
                           json=data, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        peaks = result.get('peaks', [])
        
        if len(peaks) > 0 and len(peaks[0]) > 0:
            file_peaks = peaks[0]
            
            print(f'\n🎯 Detected Peaks vs Actual Data:')
            print(f'{"Type":<10} {"Detected V":<12} {"Detected I":<12} {"Actual I@V":<12} {"Match?":<8}')
            print("-" * 60)
            
            for peak in file_peaks:
                peak_v = peak.get('voltage', 0)
                peak_i = peak.get('current', 0)
                peak_type = peak.get('type', 'unknown')
                
                # Find closest voltage in actual data
                v_array = np.array(voltage)
                closest_idx = np.argmin(np.abs(v_array - peak_v))
                actual_i = current[closest_idx]
                actual_v = voltage[closest_idx]
                
                # Check if they match (within 5% tolerance)
                tolerance = 0.05
                match = abs(peak_i - actual_i) <= abs(actual_i) * tolerance if actual_i != 0 else abs(peak_i - actual_i) <= 0.1
                
                print(f'{peak_type:<10} {peak_v:<12.3f} {peak_i:<12.3f} {actual_i:<12.3f} {"✅ Yes" if match else "❌ No":<8}')
                
                if not match:
                    print(f'   ⚠️  Mismatch: API={peak_i:.3f}µA vs Actual={actual_i:.3f}µA at V={peak_v:.3f}V')
                    
                    # Find what current value corresponds to detected peak position
                    print(f'   📍 Actual voltage closest to detected: {actual_v:.3f}V')
                    print(f'   📊 Difference: ΔV={abs(peak_v-actual_v):.3f}V, ΔI={abs(peak_i-actual_i):.3f}µA')
        else:
            print("❌ No peaks detected")
    else:
        print(f"❌ API Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    debug_peak_current()
