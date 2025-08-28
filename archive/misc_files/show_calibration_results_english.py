#!/usr/bin/env python3
"""
English Calibration Results Display
Shows detailed calibration comparison in English
"""

import sqlite3
import json
import numpy as np
from datetime import datetime
from calibration_graph_comparison_fixed import CalibrationGraphComparison
import matplotlib
matplotlib.use('Agg')

def show_english_calibration_results():
    """Display calibration results in English"""
    
    print("=" * 70)
    print("🎯 CALIBRATION COMPARISON RESULTS")
    print("=" * 70)
    
    # Create visualizer
    visualizer = CalibrationGraphComparison()
    
    # Get measurement data
    stm32_data = visualizer.get_measurement_data(75)
    palmsens_data = visualizer.get_measurement_data(90)
    
    if not stm32_data or not palmsens_data:
        print("❌ Error: Could not load measurement data")
        return
    
    # Extract data for analysis
    stm32_voltage = stm32_data['voltage']
    stm32_current = stm32_data['current']
    palmsens_voltage = palmsens_data['voltage']
    palmsens_current = palmsens_data['current']
    
    # Perform calibration
    calibrated_voltage, calibrated_current, voltage_offset, current_gain = \
        visualizer.calibrate_stm32_data(stm32_voltage, stm32_current, 
                                      palmsens_voltage, palmsens_current)
    
    # Calculate statistics
    stats = visualizer.calculate_statistics(stm32_current, palmsens_current, calibrated_current)
    
    # Display results
    print("📊 MEASUREMENT DATA COMPARISON:")
    print("-" * 70)
    print(f"🔴 STM32 (ID: 75):")
    print(f"   Sample: {stm32_data['sample_id']}")
    print(f"   Scan Rate: {stm32_data['scan_rate']:.1f} V/s")
    print(f"   Data Points: {len(stm32_current)}")
    print(f"   Voltage Range: {min(stm32_voltage):.3f} to {max(stm32_voltage):.3f} V")
    print(f"   Current Range: {min(stm32_current)*1e6:.2f} to {max(stm32_current)*1e6:.2f} μA")
    
    print(f"\n🔵 PalmSens Reference (ID: 90):")
    print(f"   Sample: {palmsens_data['sample_id']}")
    print(f"   Scan Rate: {palmsens_data['scan_rate']:.1f} V/s")
    print(f"   Data Points: {len(palmsens_current)}")
    print(f"   Voltage Range: {min(palmsens_voltage):.3f} to {max(palmsens_voltage):.3f} V")
    print(f"   Current Range: {min(palmsens_current)*1e6:.2f} to {max(palmsens_current)*1e6:.2f} μA")
    
    print(f"\n🔧 CALIBRATION PARAMETERS:")
    print("-" * 70)
    print(f"Voltage Offset: {voltage_offset*1000:+.2f} mV")
    print(f"Current Gain: {current_gain:.3f}x")
    
    if stats:
        print(f"\n📈 STATISTICAL COMPARISON:")
        print("-" * 70)
        print(f"📊 Before Calibration:")
        print(f"   Correlation: {stats['correlation_before']:.3f}")
        print(f"   RMSE: {stats['rmse_before']*1e6:.2f} μA")
        print(f"   R²: {stats['r2_before']:.3f}")
        
        print(f"\n🔧 After Calibration:")
        print(f"   Correlation: {stats['correlation_after']:.3f}")
        print(f"   RMSE: {stats['rmse_after']*1e6:.2f} μA")
        print(f"   R²: {stats['r2_after']:.3f}")
        
        print(f"\n✅ IMPROVEMENTS:")
        print("-" * 70)
        corr_improvement = ((stats['correlation_after'] - stats['correlation_before']) / 
                          abs(stats['correlation_before']) * 100) if stats['correlation_before'] != 0 else 0
        rmse_improvement = ((stats['rmse_before'] - stats['rmse_after']) / 
                          stats['rmse_before'] * 100) if stats['rmse_before'] != 0 else 0
        r2_improvement = ((stats['r2_after'] - stats['r2_before']) / 
                         abs(stats['r2_before']) * 100) if stats['r2_before'] != 0 else 0
        
        print(f"Correlation improvement: {corr_improvement:+.1f}%")
        print(f"RMSE improvement: {rmse_improvement:+.1f}%")
        print(f"R² improvement: {r2_improvement:+.1f}%")
    
    # Find peaks
    stm32_peak_idx = np.argmax(np.abs(stm32_current))
    palmsens_peak_idx = np.argmax(np.abs(palmsens_current))
    cal_peak_idx = np.argmax(np.abs(calibrated_current))
    
    print(f"\n🎯 PEAK ANALYSIS:")
    print("-" * 70)
    print(f"STM32 Peak: {stm32_voltage[stm32_peak_idx]:.3f} V, {stm32_current[stm32_peak_idx]*1e6:.2f} μA")
    print(f"PalmSens Peak: {palmsens_voltage[palmsens_peak_idx]:.3f} V, {palmsens_current[palmsens_peak_idx]*1e6:.2f} μA")
    print(f"Calibrated Peak: {calibrated_voltage[cal_peak_idx]:.3f} V, {calibrated_current[cal_peak_idx]*1e6:.2f} μA")
    
    # Generate graph
    print("\n📁 GENERATING COMPARISON GRAPH...")
    print("-" * 70)
    visualizer.plot_comparison(75, 90)
    
    # Find the latest graph file
    import glob
    graph_files = glob.glob("calibration_comparison_75_vs_90_*.png")
    if graph_files:
        latest_file = max(graph_files)
        print(f"📊 Graph saved as: {latest_file}")
    
    print("\n" + "=" * 70)
    print("✅ CALIBRATION COMPARISON COMPLETED")
    print("=" * 70)

if __name__ == "__main__":
    show_english_calibration_results()