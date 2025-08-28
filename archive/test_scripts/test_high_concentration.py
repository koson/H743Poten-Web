#!/usr/bin/env python3
"""
Test Enhanced V4 Improved with high concentration CV data
"""

import requests
import time
import json

def test_high_concentration():
    """Test Enhanced V4 Improved with high concentration data"""
    
    # Test with simulated high concentration data (20mM)
    # Based on the screenshot showing reduction peak around -0.25V
    voltage_data = [
        -0.4, -0.35, -0.3, -0.25, -0.2, -0.15, -0.1, -0.05, 0.0, 
        0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6
    ]
    
    # High concentration CV profile with strong reduction at -0.25V and oxidation at 0.25V
    current_data = [
        -200, -180, -400, -380, -150, -100, -50, 0, 50,  # Strong reduction around -0.25V
        100, 150, 200, 250, 350, 300, 250, 200, 150, 100, 80, 60  # Strong oxidation around 0.25V
    ]
    
    data = {
        'dataFiles': [{
            'voltage': voltage_data,
            'current': current_data
        }]
    }
    
    print('🧪 Testing Enhanced V4 Improved with high concentration data...')
    print(f'📊 Voltage range: {min(voltage_data):.2f}V to {max(voltage_data):.2f}V')
    print(f'📊 Current range: {min(current_data):.1f}µA to {max(current_data):.1f}µA')
    print(f'🔍 Expected reduction peak around: -0.25V')
    print(f'🔍 Expected oxidation peak around: 0.25V')
    
    try:
        start = time.time()
        response = requests.post('http://127.0.0.1:8080/get-peaks/enhanced_v4_improved', 
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
                    print(f'      Peak {i+1}: V={v:.3f}V, I={i_val:.1f}µA, Conf={conf:.1f}%')
                
                print(f'   🔵 Reduction peaks: {len(red_peaks)}')
                for i, peak in enumerate(red_peaks):
                    v = peak.get('voltage', 'N/A')
                    i_val = peak.get('current', 'N/A')
                    conf = peak.get('confidence', 'N/A')
                    print(f'      Peak {i+1}: V={v:.3f}V, I={i_val:.1f}µA, Conf={conf:.1f}%')
                
                # Check if reduction peak at -0.25V is detected
                red_at_expected = any(abs(p.get('voltage', 0) - (-0.25)) < 0.05 for p in red_peaks)
                if red_at_expected:
                    print('✅ SUCCESS: Reduction peak detected near -0.25V!')
                else:
                    print('❌ ISSUE: No reduction peak detected near -0.25V')
                    
                return len(red_peaks) > 0 and red_at_expected
            else:
                print('❌ No peaks detected')
                return False
                
        else:
            print(f'❌ Error: {response.text}')
            return False
            
    except Exception as e:
        print(f'❌ Test failed: {str(e)}')
        return False

if __name__ == "__main__":
    success = test_high_concentration()
    if success:
        print('\n🎉 High concentration test PASSED!')
    else:
        print('\n😞 High concentration test FAILED - need further adjustments')
