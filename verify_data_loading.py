#!/usr/bin/env python3
"""
Verify the data loading and indexing
"""

import numpy as np

def verify_data_loading():
    """Verify data loading and find exact match"""
    
    filename = 'Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_100mVpS_E1_scan_08.csv'
    
    voltage = []
    current = []
    
    with open(filename, 'r') as f:
        lines = f.readlines()
        
        print(f"📁 File: {filename}")
        print(f"📝 Total lines in file: {len(lines)}")
        print(f"📝 First 5 lines:")
        for i, line in enumerate(lines[:5]):
            print(f"   Line {i}: {line.strip()}")
        
        data_start = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('V,uA') or 'V,uA' in line:
                data_start = i + 1
                print(f"📝 Data starts at line {data_start}")
                break
        
        for line_num, line in enumerate(lines[data_start:], start=data_start):
            line = line.strip()
            if line and ',' in line:
                try:
                    parts = line.split(',')
                    v = float(parts[0])
                    i = float(parts[1])
                    voltage.append(v)
                    current.append(i)
                except (ValueError, IndexError):
                    print(f"⚠️  Skipped line {line_num}: {line}")
                    continue
    
    voltage = np.array(voltage)
    current = np.array(current)
    
    print(f"\n📊 Loaded data:")
    print(f"   Points: {len(voltage)}")
    print(f"   V range: {np.min(voltage):.3f} to {np.max(voltage):.3f}")
    print(f"   I range: {np.min(current):.3f} to {np.max(current):.3f}")
    
    # Search for V=0.079
    target_v = 0.079
    matches = []
    
    for idx, v in enumerate(voltage):
        if abs(v - target_v) < 0.001:
            matches.append((idx, v, current[idx]))
    
    print(f"\n🔍 Searching for V≈{target_v}V:")
    print(f"   Found {len(matches)} matches:")
    for idx, v, i in matches:
        print(f"      Index {idx}: V={v:.3f}V, I={i:.3f}µA")
    
    # Search for I=-1.568
    target_i = -1.568
    i_matches = []
    
    for idx, i in enumerate(current):
        if abs(i - target_i) < 0.001:
            i_matches.append((idx, voltage[idx], i))
    
    print(f"\n🔍 Searching for I≈{target_i}µA:")
    print(f"   Found {len(i_matches)} matches:")
    for idx, v, i in i_matches:
        print(f"      Index {idx}: V={v:.3f}V, I={i:.3f}µA")
    
    # Check index 174 specifically
    if len(voltage) > 174:
        print(f"\n📍 Checking index 174 specifically:")
        print(f"   V={voltage[174]:.3f}V, I={current[174]:.3f}µA")
    else:
        print(f"\n❌ Index 174 is out of range (max index: {len(voltage)-1})")
    
    # Show data around index 50 (from our previous analysis)
    print(f"\n📍 Data around index 50:")
    for idx in range(48, 53):
        if 0 <= idx < len(voltage):
            print(f"   Index {idx}: V={voltage[idx]:.3f}V, I={current[idx]:.3f}µA")

if __name__ == "__main__":
    verify_data_loading()
