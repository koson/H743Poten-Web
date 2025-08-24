#!/usr/bin/env python3
"""
Simple Advanced Calibration Demo
"""

import sqlite3
import json
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from datetime import datetime

def get_measurement_data(sample_id, instrument_type):
    """Get measurement data from database"""
    try:
        conn = sqlite3.connect('data_logs/parameter_log.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT raw_data_json FROM measurements 
            WHERE sample_id = ? AND instrument_type = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (sample_id, instrument_type))
        
        result = cursor.fetchone()
        if not result:
            return None
            
        raw_data = json.loads(result[0])
        cv_data = raw_data.get('cv_data', [])
        
        # Handle different cv_data formats
        if cv_data and isinstance(cv_data[0], dict):
            # Format: [{'voltage': x, 'current': y}, ...]
            voltages = [point['voltage'] for point in cv_data]
            currents = [point['current'] for point in cv_data]
        elif cv_data and isinstance(cv_data[0], (list, tuple)):
            # Format: [[voltage, current], ...]
            voltages = [point[0] for point in cv_data]
            currents = [point[1] for point in cv_data]
        else:
            voltages = []
            currents = []
        
        conn.close()
        
        return {
            'sample_id': f"{sample_id} ({instrument_type})",
            'voltage': np.array(voltages),
            'current': np.array(currents)
        }
        
    except Exception as e:
        print(f"Error loading data for sample {sample_id} ({instrument_type}): {e}")
        return None

def calibrate_technique1_voltage_current(stm32_v, stm32_i, palmsens_v, palmsens_i):
    """Technique 1: Calibrate both voltage and current"""
    # Voltage alignment
    voltage_offset = np.mean(palmsens_v) - np.mean(stm32_v)
    cal_voltage = stm32_v + voltage_offset
    
    # Current scaling
    stm32_std = np.std(stm32_i)
    palmsens_std = np.std(palmsens_i)
    current_gain = palmsens_std / stm32_std if stm32_std > 0 else 1.0
    cal_current = stm32_i * current_gain
    
    return cal_voltage, cal_current, voltage_offset, current_gain

def calibrate_technique2_current_only(stm32_v, stm32_i, palmsens_v, palmsens_i):
    """Technique 2: Preserve voltage, scale/offset current only"""
    cal_voltage = stm32_v.copy()  # Preserve original voltage
    
    # Current offset and scaling to match PalmSens peaks
    stm32_min, stm32_max = np.min(stm32_i), np.max(stm32_i)
    palmsens_min, palmsens_max = np.min(palmsens_i), np.max(palmsens_i)
    
    # Calculate scaling and offset
    stm32_range = stm32_max - stm32_min
    palmsens_range = palmsens_max - palmsens_min
    
    current_gain = palmsens_range / stm32_range if stm32_range > 0 else 1.0
    current_offset = palmsens_min - (stm32_min * current_gain)
    
    cal_current = stm32_i * current_gain + current_offset
    
    return cal_voltage, cal_current, current_offset, current_gain

def calculate_statistics(original, reference, calibrated):
    """Calculate correlation and RMSE statistics"""
    try:
        # Before calibration
        r2_before = stats.pearsonr(original, reference)[0]**2 if len(original) == len(reference) else 0
        rmse_before = np.sqrt(np.mean((original - reference)**2)) if len(original) == len(reference) else 0
        
        # After calibration
        r2_after = stats.pearsonr(calibrated, reference)[0]**2 if len(calibrated) == len(reference) else 0
        rmse_after = np.sqrt(np.mean((calibrated - reference)**2)) if len(calibrated) == len(reference) else 0
        
        return {
            'r2_before': r2_before,
            'r2_after': r2_after,
            'rmse_before': rmse_before,
            'rmse_after': rmse_after
        }
    except:
        return None

def main():
    print("🎯 Advanced Calibration Techniques Comparison")
    print("=" * 60)
    
    # Load data
    stm32_data = get_measurement_data("5mM E2S8", "stm32")
    palmsens_data = get_measurement_data("PS 5mM E2 S6", "palmsens")
    
    if not stm32_data or not palmsens_data:
        print("❌ Could not load data")
        return
    
    print(f"📊 Data loaded successfully:")
    print(f"  STM32: {stm32_data['sample_id']} - {len(stm32_data['current'])} points")
    print(f"  PalmSens: {palmsens_data['sample_id']} - {len(palmsens_data['current'])} points")
    
    # Get arrays
    stm32_voltage = stm32_data['voltage']
    stm32_current = stm32_data['current']
    palmsens_voltage = palmsens_data['voltage']
    palmsens_current = palmsens_data['current']
    
    print(f"\n🔧 Applying calibration techniques...")
    
    # Apply calibrations
    cal1_voltage, cal1_current, voltage_offset, current_gain1 = \
        calibrate_technique1_voltage_current(stm32_voltage, stm32_current, 
                                           palmsens_voltage, palmsens_current)
    
    cal2_voltage, cal2_current, current_offset, current_gain2 = \
        calibrate_technique2_current_only(stm32_voltage, stm32_current, 
                                        palmsens_voltage, palmsens_current)
    
    # Calculate statistics
    stats1 = calculate_statistics(stm32_current, palmsens_current, cal1_current)
    stats2 = calculate_statistics(stm32_current, palmsens_current, cal2_current)
    
    print(f"\n📈 RESULTS COMPARISON:")
    print("=" * 60)
    
    print(f"🔧 Technique 1 (Voltage + Current Calibration):")
    print(f"  Voltage Offset: {voltage_offset*1000:+.2f} mV")
    print(f"  Current Gain: {current_gain1:.3f}x")
    if stats1:
        print(f"  R² improvement: {stats1['r2_before']:.3f} → {stats1['r2_after']:.3f}")
        print(f"  RMSE: {stats1['rmse_before']*1e6:.0f} → {stats1['rmse_after']*1e6:.0f} μA")
    
    print(f"\n⚡ Technique 2 (Current-Only Calibration, Voltage Preserved):")
    print(f"  Voltage: UNCHANGED (preserved)")
    print(f"  Current Offset: {current_offset*1e6:+.2f} μA")
    print(f"  Current Gain: {current_gain2:.3f}x")
    if stats2:
        print(f"  R² improvement: {stats2['r2_before']:.3f} → {stats2['r2_after']:.3f}")
        print(f"  RMSE: {stats2['rmse_before']*1e6:.0f} → {stats2['rmse_after']*1e6:.0f} μA")
    
    # Create comparison plot
    plt.style.use('default')
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Advanced Calibration Techniques Comparison', fontsize=16, fontweight='bold')
    
    # Plot 1: Original data
    ax1.plot(stm32_voltage, stm32_current*1e6, 'b-', alpha=0.7, linewidth=2, label='STM32 Original')
    ax1.plot(palmsens_voltage, palmsens_current*1e6, 'r-', alpha=0.8, linewidth=2, label='PalmSens Reference')
    ax1.set_xlabel('Voltage (V)')
    ax1.set_ylabel('Current (μA)')
    ax1.set_title('Original Data Comparison')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Technique 1
    ax2.plot(cal1_voltage, cal1_current*1e6, 'g-', alpha=0.7, linewidth=2, label='STM32 Calibrated (Tech 1)')
    ax2.plot(palmsens_voltage, palmsens_current*1e6, 'r-', alpha=0.8, linewidth=2, label='PalmSens Reference')
    ax2.set_xlabel('Voltage (V)')
    ax2.set_ylabel('Current (μA)')
    ax2.set_title('Technique 1: Voltage + Current Calibration')
    if stats1:
        ax2.text(0.05, 0.95, f'R² = {stats1["r2_after"]:.3f}', transform=ax2.transAxes, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen"), fontsize=10)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Technique 2
    ax3.plot(cal2_voltage, cal2_current*1e6, 'm-', alpha=0.7, linewidth=2, label='STM32 Calibrated (Tech 2)')
    ax3.plot(palmsens_voltage, palmsens_current*1e6, 'r-', alpha=0.8, linewidth=2, label='PalmSens Reference')
    ax3.set_xlabel('Voltage (V)')
    ax3.set_ylabel('Current (μA)')
    ax3.set_title('Technique 2: Current-Only Calibration')
    if stats2:
        ax3.text(0.05, 0.95, f'R² = {stats2["r2_after"]:.3f}', transform=ax3.transAxes, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcyan"), fontsize=10)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Statistics comparison
    techniques = ['Original\nvs Reference', 'Technique 1\nvs Reference', 'Technique 2\nvs Reference']
    r2_values = []
    if stats1 and stats2:
        r2_values = [stats1['r2_before'], stats1['r2_after'], stats2['r2_after']]
        
        bars = ax4.bar(techniques, r2_values, color=['lightcoral', 'lightgreen', 'lightcyan'], alpha=0.7)
        ax4.set_ylabel('R² (Correlation Coefficient)')
        ax4.set_title('Calibration Performance Comparison')
        ax4.set_ylim(0, 1)
        
        # Add value labels on bars
        for bar, value in zip(bars, r2_values):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                    f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
        
        ax4.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # Save plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"advanced_calibration_simple_{timestamp}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\n📊 Graph saved as: {filename}")
    
    print("\n🎯 RECOMMENDATION:")
    print("-" * 40)
    if stats1 and stats2:
        if stats1['r2_after'] > stats2['r2_after']:
            diff = stats1['r2_after'] - stats2['r2_after']
            print(f"✅ Technique 1 performs better (R² difference: +{diff:.3f})")
        elif stats2['r2_after'] > stats1['r2_after']:
            diff = stats2['r2_after'] - stats1['r2_after']
            print(f"✅ Technique 2 performs better (R² difference: +{diff:.3f})")
        else:
            print(f"⚖️  Both techniques show similar performance")
    
    print("=" * 60)
    print("✅ Advanced calibration comparison completed!")

if __name__ == "__main__":
    main()