#!/usr/bin/env python3
"""
Debug the algorithm directly to see what it's actually returning
"""

import numpy as np
from enhanced_detector_v4_improved import EnhancedDetectorV4Improved

def debug_algorithm_directly():
    """Test the algorithm directly without API"""
    
    # Load STM32 data
    filename = 'Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_100mVpS_E1_scan_08.csv'
    
    voltage = []
    current = []
    
    with open(filename, 'r') as f:
        lines = f.readlines()
        
        data_start = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('V,uA') or 'V,uA' in line:
                data_start = i + 1
                break
        
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
    
    voltage = np.array(voltage)
    current = np.array(current)
    
    print(f'🧪 Testing Enhanced V4 Improved Algorithm Directly')
    print(f'📊 Data: {len(voltage)} points, V:{np.min(voltage):.3f}-{np.max(voltage):.3f}V, I:{np.min(current):.3f}-{np.max(current):.3f}µA')
    
    # Test algorithm
    detector = EnhancedDetectorV4Improved(confidence_threshold=25.0)
    
    # Prepare data in correct format
    data = {
        'voltage': voltage.tolist(),
        'current': current.tolist()
    }
    
    results = detector.analyze_cv_data(data)
    
    print(f'\n🎯 Direct Algorithm Results:')
    peaks = results.get('peaks', [])
    print(f'Total peaks detected: {len(peaks)}')
    
    for i, peak in enumerate(peaks):
        peak_type = peak.get('type', 'unknown')
        peak_v = peak.get('voltage', 0)
        peak_i = peak.get('current', 0)
        peak_conf = peak.get('confidence', 0)
        peak_idx = peak.get('index', -1)
        
        print(f'Peak {i+1}: {peak_type}')
        print(f'   Voltage: {peak_v:.3f}V')
        print(f'   Current: {peak_i:.3f}µA')
        print(f'   Confidence: {peak_conf:.1f}%')
        print(f'   Index: {peak_idx}')
        
        # Check actual data at this index
        if 0 <= peak_idx < len(current):
            actual_v = voltage[peak_idx]
            actual_i = current[peak_idx]
            print(f'   Actual data at index {peak_idx}: V={actual_v:.3f}V, I={actual_i:.3f}µA')
            
            v_match = abs(peak_v - actual_v) < 0.001
            i_match = abs(peak_i - actual_i) < 0.001
            
            print(f'   Voltage match: {"✅" if v_match else "❌"} (Δ={abs(peak_v - actual_v):.6f}V)')
            print(f'   Current match: {"✅" if i_match else "❌"} (Δ={abs(peak_i - actual_i):.6f}µA)')
            
            if not i_match:
                print(f'   🚨 CURRENT MISMATCH: Algorithm={peak_i:.3f}µA vs Actual={actual_i:.3f}µA')
        else:
            print(f'   ❌ Invalid index: {peak_idx}')
        
        print()

if __name__ == "__main__":
    debug_algorithm_directly()
