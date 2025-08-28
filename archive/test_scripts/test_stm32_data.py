#!/usr/bin/env python3
"""
Test Enhanced V4 Improved with STM32 H743 data
"""

import requests
import time
import csv
import numpy as np

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

def test_stm32_data():
    """Test Enhanced V4 Improved with real STM32 data"""
    
    # Load real STM32 file
    filename = 'Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_100mVpS_E1_scan_08.csv'
    
    try:
        voltage, current = load_stm32_data(filename)
        
        print(f'🧪 Testing Enhanced V4 Improved with STM32 H743 data')
        print(f'📁 File: Pipot_Ferro_0_5mM_100mVpS_E1_scan_08.csv')
        print(f'📊 Data points: {len(voltage)}')
        print(f'📊 Voltage range: {min(voltage):.3f}V to {max(voltage):.3f}V')
        print(f'📊 Current range: {min(current):.3f}µA to {max(current):.3f}µA')
        
        # Check for typical ferrocyanide peaks
        expected_ox_range = (0.1, 0.6)  # Oxidation around 0.2-0.4V
        expected_red_range = (-0.2, 0.2)  # Reduction around 0.0V
        
        data = {
            'dataFiles': [{
                'voltage': voltage,
                'current': current
            }]
        }
        
        start = time.time()
        response = requests.post('http://127.0.0.1:8081/get-peaks/enhanced_v4_improved', 
                               json=data, timeout=30)
        end = time.time()
        
        print(f'⏱️  Processing time: {end-start:.2f}s')
        print(f'📡 Response status: {response.status_code}')
        
        if response.status_code == 200:
            result = response.json()
            peaks = result.get('peaks', [])
            
            if len(peaks) > 0 and len(peaks[0]) > 0:
                file_peaks = peaks[0]
                print(f'✅ Detected {len(file_peaks)} peaks:')
                
                ox_peaks = [p for p in file_peaks if p.get('type') == 'oxidation']
                red_peaks = [p for p in file_peaks if p.get('type') == 'reduction']
                
                print(f'   🔴 Oxidation peaks: {len(ox_peaks)}')
                for i, peak in enumerate(ox_peaks):
                    v = peak.get('voltage', 'N/A')
                    i_val = peak.get('current', 'N/A') 
                    conf = peak.get('confidence', 'N/A')
                    print(f'      Peak {i+1}: V={v:.3f}V, I={i_val:.3f}µA, Conf={conf:.1f}%')
                
                print(f'   🔵 Reduction peaks: {len(red_peaks)}')
                for i, peak in enumerate(red_peaks):
                    v = peak.get('voltage', 'N/A')
                    i_val = peak.get('current', 'N/A')
                    conf = peak.get('confidence', 'N/A')
                    print(f'      Peak {i+1}: V={v:.3f}V, I={i_val:.3f}µA, Conf={conf:.1f}%')
                
                # Analyze results
                if len(ox_peaks) > 0:
                    ox_in_range = any(expected_ox_range[0] <= p.get('voltage', -999) <= expected_ox_range[1] for p in ox_peaks)
                    print(f'   📍 Oxidation peak in expected range {expected_ox_range}: {"✅ Yes" if ox_in_range else "❌ No"}')
                
                if len(red_peaks) > 0:
                    red_in_range = any(expected_red_range[0] <= p.get('voltage', -999) <= expected_red_range[1] for p in red_peaks)
                    print(f'   📍 Reduction peak in expected range {expected_red_range}: {"✅ Yes" if red_in_range else "❌ No"}')
                
                total_peaks = len(ox_peaks) + len(red_peaks)
                if total_peaks >= 2:
                    print(f'✅ SUCCESS: Detected {total_peaks} peaks (likely ferrocyanide pair)')
                    return True
                elif total_peaks == 1:
                    print(f'⚠️  PARTIAL: Detected {total_peaks} peak (may need adjustment)')
                    return False
                else:
                    print(f'❌ FAILED: No peaks detected')
                    return False
            else:
                print(f'❌ No peaks detected')
                return False
                
        else:
            print(f'❌ Error: {response.text}')
            return False
            
    except FileNotFoundError:
        print(f'❌ File not found: {filename}')
        return False
    except Exception as e:
        print(f'❌ Test failed: {str(e)}')
        return False

if __name__ == "__main__":
    success = test_stm32_data()
    if success:
        print(f'\n🎉 STM32 H743 test PASSED!')
    else:
        print(f'\n😞 STM32 H743 test FAILED - may need algorithm adjustments')
