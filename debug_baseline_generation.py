#!/usr/bin/env python3
"""
Debug and fix baseline generation for PiPot files
"""

import os
import sys
import numpy as np
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

def debug_baseline_generation():
    """Debug the baseline generation step specifically"""
    
    # Test with a specific PiPot file that's failing
    test_file = "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_20mVpS_E1_scan_06.csv"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"🔍 Debugging baseline generation: {test_file}")
    
    # Read the raw CSV data
    with open(test_file, 'r') as f:
        lines = f.readlines()
    
    # Parse data
    voltages = []
    currents_raw = []
    
    for line in lines[2:]:  # Skip header lines
        parts = line.strip().split(',')
        if len(parts) >= 2:
            try:
                voltage = float(parts[0])
                current = float(parts[1])
                voltages.append(voltage)
                currents_raw.append(current)
            except ValueError:
                continue
    
    voltages = np.array(voltages)
    currents_ua = np.array(currents_raw) * 1e6  # Convert A to µA
    
    print(f"📊 Data summary:")
    print(f"   📈 Voltage: {voltages.min():.3f} to {voltages.max():.3f} V")
    print(f"   ⚡ Current: {currents_ua.min():.3f} to {currents_ua.max():.3f} µA")
    
    # Simulate what the voltage window detector would do
    # Let's manually create some simple segments and see what happens
    mid = len(voltages) // 2
    
    # Example segment from the logs
    # This segment had slope=2.79e+01, but let's see what the current range was
    segment_voltage = voltages[:20]  # First 20 points
    segment_current = currents_ua[:20]
    
    print(f"\n🔍 Example segment analysis:")
    print(f"   📈 Segment voltage range: {segment_voltage.min():.3f} to {segment_voltage.max():.3f} V")
    print(f"   ⚡ Segment current range: {segment_current.min():.3f} to {segment_current.max():.3f} µA")
    print(f"   📊 Segment current mean: {segment_current.mean():.3f} µA")
    
    # Calculate slope and intercept for this segment
    from scipy import stats
    slope, intercept, r_value, p_value, std_err = stats.linregress(segment_voltage, segment_current)
    
    print(f"   📈 Linear fit: slope={slope:.2e}, intercept={intercept:.3f}")
    print(f"   📊 R² = {r_value**2:.3f}")
    
    # Now see what happens when we apply this to the full voltage range
    baseline_full = slope * voltages + intercept
    
    print(f"\n🔧 Baseline generation test:")
    print(f"   📈 Applied to full voltage range: {voltages.min():.3f} to {voltages.max():.3f} V")
    print(f"   ⚡ Resulting baseline range: {baseline_full.min():.3f} to {baseline_full.max():.3f} µA")
    print(f"   📊 Original current range: {currents_ua.min():.3f} to {currents_ua.max():.3f} µA")
    
    # Check if the baseline is reasonable
    current_range = currents_ua.max() - currents_ua.min()
    baseline_range = baseline_full.max() - baseline_full.min()
    
    print(f"\n📊 Range comparison:")
    print(f"   Current range: {current_range:.3f} µA")
    print(f"   Baseline range: {baseline_range:.3f} µA")
    print(f"   Ratio: {baseline_range/current_range:.3f}")
    
    if baseline_range < current_range * 0.1:
        print(f"   ⚠️ WARNING: Baseline range is much smaller than current range!")
        print(f"   ⚠️ This suggests extrapolation issues")
    
    # Test alternative approach: use segment current mean instead of linear extrapolation
    print(f"\n🔧 Alternative approach: Use segment mean")
    baseline_mean = np.full_like(voltages, segment_current.mean())
    print(f"   ⚡ Mean-based baseline: constant {segment_current.mean():.3f} µA")
    print(f"   📊 This would give a visible baseline!")
    
    # Test segment-based approach
    print(f"\n🔧 Segment-based approach:")
    forward_mean = np.mean(currents_ua[:mid])
    reverse_mean = np.mean(currents_ua[mid:])
    
    baseline_forward = np.full(mid, forward_mean)
    baseline_reverse = np.full(len(voltages) - mid, reverse_mean)
    baseline_segments = np.concatenate([baseline_forward, baseline_reverse])
    
    print(f"   📈 Forward mean: {forward_mean:.3f} µA")
    print(f"   📉 Reverse mean: {reverse_mean:.3f} µA")
    print(f"   📊 Segment baseline range: {baseline_segments.min():.3f} to {baseline_segments.max():.3f} µA")

if __name__ == "__main__":
    debug_baseline_generation()