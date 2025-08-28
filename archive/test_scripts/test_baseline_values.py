#!/usr/bin/env python3
"""
Test script to check the actual baseline values from the detector
"""

import numpy as np
import matplotlib.pyplot as plt
from baseline_detector_voltage_windows import voltage_window_baseline_detector

# Load test data
def load_csv_data(file_path):
    """Load CSV data with error handling"""
    try:
        data = np.loadtxt(file_path, delimiter=',', skiprows=2)  # Skip 2 header lines
        voltage = data[:, 0]
        current = data[:, 1] * 1e6  # Convert A to µA
        return voltage, current
    except Exception as e:
        print(f"Error loading data: {e}")
        return None, None

# Load PiPot test file
file_path = "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_20mVpS_E1_scan_06.csv"
voltage, current = load_csv_data(file_path)

if voltage is not None:
    print(f"🔍 Testing baseline detector with PiPot data")
    print(f"📊 Data: {len(voltage)} points, V: {voltage.min():.3f} to {voltage.max():.3f} V")
    print(f"⚡ Current: {current.min():.3f} to {current.max():.3f} µA")
    
    # Run baseline detector
    result = voltage_window_baseline_detector(voltage, current)
    
    if isinstance(result, tuple) and len(result) == 3:
        forward_baseline, reverse_baseline, metadata = result
        
        print(f"\n✅ Baseline detection successful!")
        print(f"📈 Forward baseline: {len(forward_baseline)} points")
        print(f"   Range: {forward_baseline.min():.6f} to {forward_baseline.max():.6f} µA")
        print(f"   Mean: {forward_baseline.mean():.6f} µA")
        print(f"   Std: {forward_baseline.std():.6f} µA")
        
        print(f"📉 Reverse baseline: {len(reverse_baseline)} points")
        print(f"   Range: {reverse_baseline.min():.6f} to {reverse_baseline.max():.6f} µA")
        print(f"   Mean: {reverse_baseline.mean():.6f} µA")
        print(f"   Std: {reverse_baseline.std():.6f} µA")
        
        # Check if baselines are meaningful (not all zeros or flat)
        forward_variation = forward_baseline.max() - forward_baseline.min()
        reverse_variation = reverse_baseline.max() - reverse_baseline.min()
        
        print(f"\n📊 Baseline variation analysis:")
        print(f"   Forward variation: {forward_variation:.6f} µA")
        print(f"   Reverse variation: {reverse_variation:.6f} µA")
        
        if forward_variation > 0.001 or reverse_variation > 0.001:
            print("✅ Baselines show meaningful variation!")
        else:
            print("⚠️ Baselines are very flat - might need adjustment")
        
        # Plot for visual inspection
        plt.figure(figsize=(12, 8))
        
        plt.subplot(2, 1, 1)
        plt.plot(voltage, current, 'b-', alpha=0.7, label='Original Data')
        
        # Create voltage arrays for baselines (assuming they cover same range)
        half_len = len(voltage) // 2
        forward_voltage = voltage[:len(forward_baseline)]
        reverse_voltage = voltage[len(voltage)-len(reverse_baseline):]
        
        plt.plot(forward_voltage, forward_baseline, 'r-', linewidth=2, label='Forward Baseline')
        plt.plot(reverse_voltage, reverse_baseline, 'g-', linewidth=2, label='Reverse Baseline')
        plt.xlabel('Voltage (V)')
        plt.ylabel('Current (µA)')
        plt.title('PiPot Data with Baselines')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Zoom in on baseline details
        plt.subplot(2, 1, 2)
        plt.plot(forward_voltage, forward_baseline, 'r-', linewidth=2, label='Forward Baseline')
        plt.plot(reverse_voltage, reverse_baseline, 'g-', linewidth=2, label='Reverse Baseline')
        plt.xlabel('Voltage (V)')
        plt.ylabel('Current (µA)')
        plt.title('Baseline Details (Zoomed)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('baseline_test_values.png', dpi=150, bbox_inches='tight')
        print(f"\n📊 Plot saved as baseline_test_values.png")
        
    else:
        print(f"❌ Unexpected result format: {type(result)}")
        if hasattr(result, '__len__'):
            print(f"   Length: {len(result)}")
        print(f"   Value: {result}")

else:
    print("❌ Failed to load test data")