#!/usr/bin/env python3
"""
Simple test to recreate the comparison image
"""

import numpy as np
import matplotlib.pyplot as plt
from baseline_detector_voltage_windows import voltage_window_baseline_detector
from baseline_detector_v4 import cv_baseline_detector_v4
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

def load_palmsens_file(file_path):
    """Load and parse PalmSens CSV file"""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            raise ValueError('File too short')
        
        # Handle instrument file format (FileName: header)
        data_start_idx = 1
        if lines[0].strip().startswith('FileName:'):
            data_start_idx = 1
        else:
            data_start_idx = 0
        
        # Extract voltage and current data
        voltages, currents = [], []
        for line in lines[data_start_idx:]:
            line = line.strip()
            if not line or line.startswith('V,'):
                continue
            try:
                parts = line.split(',')
                if len(parts) >= 2:
                    voltage = float(parts[0])
                    current = float(parts[1])
                    voltages.append(voltage)
                    currents.append(current)
            except ValueError:
                continue
        
        return np.array(voltages), np.array(currents)
    
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None, None

def analyze_baseline_detection(file_path, label):
    """Analyze baseline detection for a file"""
    print(f"\n🔍 Analyzing {label}: {file_path}")
    
    voltage, current = load_palmsens_file(file_path)
    if voltage is None:
        return None
    
    print(f"📊 Data points: {len(voltage)}")
    print(f"🔌 Voltage range: {voltage.min():.3f}V to {voltage.max():.3f}V")
    print(f"⚡ Current range: {current.min():.3f}µA to {current.max():.3f}µA")
    
    # Detect baseline using v4 detector
    result = cv_baseline_detector_v4(voltage, current)
    
    print(f"📈 Baseline Results:")
    print(f"   Forward baseline: {len(result['forward_baseline'])} points")
    print(f"   Reverse baseline: {len(result['reverse_baseline'])} points")
    
    # Get segment info
    forward_seg = result['info'].get('forward_segment', {})
    reverse_seg = result['info'].get('reverse_segment', {})
    
    if forward_seg:
        print(f"   Forward segment: [{forward_seg['start_idx']}:{forward_seg['end_idx']}] = {forward_seg['end_idx'] - forward_seg['start_idx'] + 1} points")
        print(f"                   V=[{forward_seg['voltage_start']:.3f}:{forward_seg['voltage_end']:.3f}], R²={forward_seg['r2']:.3f}")
    
    if reverse_seg:
        print(f"   Reverse segment: [{reverse_seg['start_idx']}:{reverse_seg['end_idx']}] = {reverse_seg['end_idx'] - reverse_seg['start_idx'] + 1} points")
        print(f"                   V=[{reverse_seg['voltage_start']:.3f}:{reverse_seg['voltage_end']:.3f}], R²={reverse_seg['r2']:.3f}")
    
    return {
        'voltage': voltage,
        'current': current,
        'forward_baseline': result['forward_baseline'],
        'reverse_baseline': result['reverse_baseline'],
        'info': result['info']
    }

def create_comparison_plot(good_result, bad_result):
    """Create comparison plot similar to the reference image"""
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot 1: Good baseline detection (200mVpS)
    ax1.plot(good_result['voltage'], good_result['current'], 'b-', linewidth=2, label='CV Data')
    
    # Combine baselines
    good_baseline_v = np.concatenate([good_result['forward_baseline'], good_result['reverse_baseline']])
    good_baseline_i = np.interp(good_baseline_v, good_result['voltage'], good_result['current'])
    ax1.plot(good_baseline_v, good_baseline_i, 'g-', linewidth=3, label='Baseline')
    
    # Add voltage windows
    forward_seg = good_result['info'].get('forward_segment', {})
    if forward_seg:
        start_idx, end_idx = forward_seg['start_idx'], forward_seg['end_idx']
        ax1.axvspan(good_result['voltage'][start_idx], good_result['voltage'][end_idx], 
                   alpha=0.3, color='lightgreen', label=f"Forward Seg ({end_idx-start_idx+1} pts)")
    
    reverse_seg = good_result['info'].get('reverse_segment', {})
    if reverse_seg:
        start_idx, end_idx = reverse_seg['start_idx'], reverse_seg['end_idx']
        ax1.axvspan(good_result['voltage'][start_idx], good_result['voltage'][end_idx], 
                   alpha=0.3, color='orange', label=f"Reverse Seg ({end_idx-start_idx+1} pts)")
    
    ax1.set_title('✅ Good Baseline Detection (200mVpS)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Current (µA)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Problematic baseline detection (100mVpS)
    ax2.plot(bad_result['voltage'], bad_result['current'], 'b-', linewidth=2, label='CV Data')
    
    # Combine baselines
    bad_baseline_v = np.concatenate([bad_result['forward_baseline'], bad_result['reverse_baseline']])
    bad_baseline_i = np.interp(bad_baseline_v, bad_result['voltage'], bad_result['current'])
    ax2.plot(bad_baseline_v, bad_baseline_i, 'r-', linewidth=3, label='Baseline')
    
    # Add voltage windows
    forward_seg = bad_result['info'].get('forward_segment', {})
    if forward_seg:
        start_idx, end_idx = forward_seg['start_idx'], forward_seg['end_idx']
        ax2.axvspan(bad_result['voltage'][start_idx], bad_result['voltage'][end_idx], 
                   alpha=0.3, color='lightcoral', label=f"Forward Seg ({end_idx-start_idx+1} pts)")
    
    reverse_seg = bad_result['info'].get('reverse_segment', {})
    if reverse_seg:
        start_idx, end_idx = reverse_seg['start_idx'], reverse_seg['end_idx']
        ax2.axvspan(bad_result['voltage'][start_idx], bad_result['voltage'][end_idx], 
                   alpha=0.3, color='orange', label=f"Reverse Seg ({end_idx-start_idx+1} pts)")
    
    ax2.set_title('❌ Problematic Baseline Detection (100mVpS)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Voltage (V)')
    ax2.set_ylabel('Current (µA)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save the plot
    output_file = 'recreated_baseline_comparison.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n✅ Comparison plot saved as: {output_file}")
    
    return output_file

def main():
    """Main function to recreate the comparison"""
    print("🎯 Recreating Baseline Detection Comparison")
    print("=" * 50)
    
    # File paths (same as original script)
    good_file = "./Test_data/Palmsens/Palmsens_1.0mM/Palmsens_1.0mM_CV_200mVpS_E1_scan_05.csv"
    bad_file = "./Test_data/Palmsens/Palmsens_1.0mM/Palmsens_1.0mM_CV_100mVpS_E1_scan_05.csv"
    
    try:
        # Analyze both files
        good_result = analyze_baseline_detection(good_file, "GOOD (200mVpS)")
        bad_result = analyze_baseline_detection(bad_file, "PROBLEMATIC (100mVpS)")
        
        if good_result and bad_result:
            # Create comparison plot
            output_file = create_comparison_plot(good_result, bad_result)
            print(f"\n🎉 Successfully recreated the comparison image!")
            print(f"📁 Output file: {output_file}")
        else:
            print("❌ Failed to analyze one or both files")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()