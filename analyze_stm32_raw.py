#!/usr/bin/env python3
"""
Analyze STM32 data to understand the peak detection issue
"""

import csv
import numpy as np
import matplotlib.pyplot as plt

def analyze_stm32_data():
    """Analyze STM32 data to understand where the true peaks are"""
    
    filename = 'Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_100mVpS_E1_scan_08.csv'
    
    voltage = []
    current = []
    
    # Load data
    with open(filename, 'r') as f:
        lines = f.readlines()
        
        # Skip header lines
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
    
    voltage = np.array(voltage)
    current = np.array(current)
    
    print(f'🔍 STM32 Data Analysis')
    print(f'📊 Data points: {len(voltage)}')
    print(f'📊 Voltage range: {np.min(voltage):.3f}V to {np.max(voltage):.3f}V')
    print(f'📊 Current range: {np.min(current):.3f}µA to {np.max(current):.3f}µA')
    
    # Find actual minimum (reduction peak)
    min_current_idx = np.argmin(current)
    min_voltage = voltage[min_current_idx]
    min_current_val = current[min_current_idx]
    
    print(f'\n🔵 Actual Reduction Peak (minimum current):')
    print(f'   Voltage: {min_voltage:.3f}V')
    print(f'   Current: {min_current_val:.3f}µA')
    print(f'   Index: {min_current_idx}')
    
    # Find actual maximum (oxidation peak)  
    max_current_idx = np.argmax(current)
    max_voltage = voltage[max_current_idx]
    max_current_val = current[max_current_idx]
    
    print(f'\n🔴 Actual Oxidation Peak (maximum current):')
    print(f'   Voltage: {max_voltage:.3f}V')
    print(f'   Current: {max_current_val:.3f}µA')
    print(f'   Index: {max_current_idx}')
    
    # Check what API detected
    print(f'\n⚠️  API Detection Analysis:')
    print(f'   API detected reduction at V=0.079V with I=-1.568µA')
    
    # Find closest point to API detection
    api_voltage = 0.079
    closest_idx = np.argmin(np.abs(voltage - api_voltage))
    closest_v = voltage[closest_idx]
    closest_i = current[closest_idx]
    
    print(f'   Closest actual data point to V=0.079V:')
    print(f'      Index: {closest_idx}')
    print(f'      Voltage: {closest_v:.3f}V')
    print(f'      Current: {closest_i:.3f}µA')
    
    # Check surrounding points
    print(f'\n📋 Surrounding data points:')
    for offset in [-2, -1, 0, 1, 2]:
        idx = closest_idx + offset
        if 0 <= idx < len(voltage):
            v = voltage[idx]
            i = current[idx]
            marker = " ← API detected here" if offset == 0 else ""
            print(f'   Index {idx}: V={v:.3f}V, I={i:.3f}µA{marker}')
    
    # Analysis of the discrepancy
    print(f'\n🧐 Analysis:')
    print(f'   - API says reduction current = -1.568µA')
    print(f'   - Actual current at V=0.079V = {closest_i:.3f}µA')
    print(f'   - True reduction peak at V={min_voltage:.3f}V, I={min_current_val:.3f}µA')
    
    if min_current_val < 0:
        print(f'   ✅ True reduction peak has negative current (correct)')
    else:
        print(f'   ⚠️  True reduction peak has positive current (unusual for reduction)')
    
    # Check for any negative currents
    negative_indices = np.where(current < 0)[0]
    print(f'\n📊 Negative current analysis:')
    print(f'   Found {len(negative_indices)} points with negative current')
    
    if len(negative_indices) > 0:
        print(f'   Negative current range: {np.min(current[negative_indices]):.3f}µA to {np.max(current[negative_indices]):.3f}µA')
        print(f'   Voltage range for negative currents: {np.min(voltage[negative_indices]):.3f}V to {np.max(voltage[negative_indices]):.3f}V')
        
        # Find the most negative point
        most_negative_idx = negative_indices[np.argmin(current[negative_indices])]
        print(f'   Most negative point: V={voltage[most_negative_idx]:.3f}V, I={current[most_negative_idx]:.3f}µA (index {most_negative_idx})')

if __name__ == "__main__":
    analyze_stm32_data()
