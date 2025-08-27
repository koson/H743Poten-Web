#!/usr/bin/env python3
"""
Direct test of peak finding in high concentration data
"""

import numpy as np
from scipy.signal import find_peaks, savgol_filter
import matplotlib.pyplot as plt

def test_direct_peak_finding():
    """Test direct peak finding on high concentration data"""
    
    # High concentration data similar to the failing case
    voltage = np.array([
        -0.4, -0.35, -0.3, -0.25, -0.2, -0.15, -0.1, -0.05, 0.0, 
        0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6
    ])
    
    current = np.array([
        -200, -180, -400, -380, -150, -100, -50, 0, 50,
        100, 150, 200, 250, 350, 300, 250, 200, 150, 100, 80, 60
    ])
    
    print(f"🧪 Direct peak finding test")
    print(f"📊 Data points: {len(voltage)}")
    print(f"📊 Voltage range: {np.min(voltage):.2f}V to {np.max(voltage):.2f}V")
    print(f"📊 Current range: {np.min(current):.1f}µA to {np.max(current):.1f}µA")
    
    # Find negative minimum (reduction peak) in original signal
    min_idx = np.argmin(current)
    print(f"🔍 Global minimum: V={voltage[min_idx]:.3f}V, I={current[min_idx]:.1f}µA")
    
    # Smooth the signal
    smoothed = savgol_filter(current, window_length=5, polyorder=2)
    
    # Test various methods for finding reduction peaks
    print(f"\n🔬 Testing different peak finding methods:")
    
    # Method 1: Simple minimum finding
    negative_indices = np.where(current < -100)[0]  # Points below -100µA
    if len(negative_indices) > 0:
        min_in_negative = negative_indices[np.argmin(current[negative_indices])]
        print(f"   Method 1 (simple min): V={voltage[min_in_negative]:.3f}V, I={current[min_in_negative]:.1f}µA")
    
    # Method 2: Find peaks in inverted signal with very low thresholds
    inverted = -current
    low_threshold_peaks, _ = find_peaks(
        inverted,
        height=50,  # Very low threshold
        distance=1,
        prominence=10
    )
    print(f"   Method 2 (inverted, low thresh): {len(low_threshold_peaks)} peaks")
    for i, idx in enumerate(low_threshold_peaks):
        print(f"      Peak {i+1}: V={voltage[idx]:.3f}V, I={current[idx]:.1f}µA")
    
    # Method 3: Find peaks in inverted signal with adaptive threshold
    current_range = np.max(current) - np.min(current)
    adaptive_thresh = current_range * 0.1  # 10% of range
    adaptive_peaks, _ = find_peaks(
        inverted,
        height=adaptive_thresh,
        distance=1,
        prominence=adaptive_thresh * 0.5
    )
    print(f"   Method 3 (adaptive {adaptive_thresh:.1f}µA): {len(adaptive_peaks)} peaks")
    for i, idx in enumerate(adaptive_peaks):
        print(f"      Peak {i+1}: V={voltage[idx]:.3f}V, I={current[idx]:.1f}µA")
    
    # Method 4: Ultra-sensitive detection
    ultra_peaks, _ = find_peaks(
        inverted,
        height=20,  # Ultra low threshold
        distance=1
    )
    print(f"   Method 4 (ultra-sensitive 20µA): {len(ultra_peaks)} peaks")
    for i, idx in enumerate(ultra_peaks):
        if current[idx] < -50:  # Only show significant negative peaks
            print(f"      Peak {i+1}: V={voltage[idx]:.3f}V, I={current[idx]:.1f}µA")
    
    # Check if we found the expected peak at -0.25V
    expected_voltage = -0.25
    tolerance = 0.05
    
    for method_name, peaks in [
        ("Method 2", low_threshold_peaks),
        ("Method 3", adaptive_peaks), 
        ("Method 4", ultra_peaks)
    ]:
        found_expected = any(abs(voltage[idx] - expected_voltage) < tolerance for idx in peaks)
        if found_expected:
            print(f"✅ {method_name}: Found peak near {expected_voltage}V!")
            return True
    
    print(f"❌ No method found the expected peak at {expected_voltage}V")
    
    # Debug: Show all current values around expected voltage
    print(f"\n🔍 Debug: Current values around {expected_voltage}V:")
    for i, (v, c) in enumerate(zip(voltage, current)):
        if abs(v - expected_voltage) < 0.1:
            print(f"   idx={i}, V={v:.3f}V, I={c:.1f}µA")
    
    return False

if __name__ == "__main__":
    success = test_direct_peak_finding()
    if success:
        print(f"\n🎉 Direct peak finding test PASSED!")
    else:
        print(f"\n😞 Direct peak finding test FAILED")
