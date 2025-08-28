#!/usr/bin/env python3
"""
Visual Test of Voltage Window Baseline Detector
===============================================
Test and visualize the voltage window baseline detector results
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging
from baseline_detector_voltage_windows import voltage_window_baseline_detector

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

def load_test_file(filepath):
    """Load CV data from CSV file"""
    try:
        df = pd.read_csv(filepath)
        
        # Handle different file formats
        if 'V' in df.columns and 'I' in df.columns:
            voltage = df['V'].values
            current = df['I'].values
        elif 'Voltage' in df.columns and 'Current' in df.columns:
            voltage = df['Voltage'].values
            current = df['Current'].values
        elif len(df.columns) >= 2:
            voltage = df.iloc[:, 0].values
            current = df.iloc[:, 1].values
        else:
            raise ValueError("Cannot identify voltage and current columns")
            
        return voltage, current
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return None, None

def plot_baseline_results(voltage, current, forward_baseline, reverse_baseline, title, info=None):
    """Plot CV data with detected baselines"""
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Top plot: Full CV with baselines
    n = len(voltage)
    mid = n // 2
    
    # Plot original data
    ax1.plot(voltage, current * 1e6, 'b-', linewidth=1, alpha=0.7, label='Original CV')
    
    # Plot baselines
    if np.any(forward_baseline):
        ax1.plot(voltage[:mid], forward_baseline * 1e6, 'r-', linewidth=2, label='Forward Baseline')
    if np.any(reverse_baseline):
        ax1.plot(voltage[mid:], reverse_baseline * 1e6, 'g-', linewidth=2, label='Reverse Baseline')
    
    ax1.set_xlabel('Voltage (V)')
    ax1.set_ylabel('Current (µA)')
    ax1.set_title(f'{title} - Voltage Window Baseline Detection')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Bottom plot: Baseline-corrected CV
    baseline_corrected = current.copy()
    if np.any(forward_baseline):
        baseline_corrected[:mid] = current[:mid] - forward_baseline
    if np.any(reverse_baseline):
        baseline_corrected[mid:] = current[mid:] - reverse_baseline
    
    ax2.plot(voltage, baseline_corrected * 1e6, 'purple', linewidth=1.5, label='Baseline Corrected')
    ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    ax2.set_xlabel('Voltage (V)')
    ax2.set_ylabel('Current (µA)')
    ax2.set_title('Baseline-Corrected CV')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Add info text
    if info:
        info_text = f"Forward: {info.get('forward_segments', 0)} segments, R²={info.get('forward_r2', 0):.3f}\n"
        info_text += f"Reverse: {info.get('reverse_segments', 0)} segments, R²={info.get('reverse_r2', 0):.3f}"
        ax1.text(0.02, 0.98, info_text, transform=ax1.transAxes, 
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    return fig

def test_and_visualize():
    """Test the voltage window detector and create visualizations"""
    
    print("🎨 VOLTAGE WINDOW BASELINE DETECTOR VISUALIZATION")
    print("=" * 60)
    
    # Test files
    test_files = [
        ("cv_data/measurement_93_100.0mVs_2025-08-25T06-39-11.686802.csv", "100mV/s"),
        ("cv_data/measurement_95_200.0mVs_2025-08-25T06-46-14.158045.csv", "200mV/s"), 
        ("cv_data/measurement_96_20.0mVs_2025-08-25T06-46-22.774810.csv", "20mV/s")
    ]
    
    for i, (filepath, scan_rate) in enumerate(test_files):
        print(f"\n📊 Processing {scan_rate}: {filepath}")
        
        voltage, current = load_test_file(filepath)
        if voltage is None:
            continue
            
        # Run voltage window detector
        forward_baseline, reverse_baseline, info = voltage_window_baseline_detector(
            voltage, current
        )
        
        # Extract info for display
        plot_info = {}
        if 'forward_info' in info and info['forward_info']:
            fwd_info = info['forward_info']
            plot_info['forward_segments'] = fwd_info.get('segment_count', 0)
            plot_info['forward_r2'] = fwd_info.get('avg_r2', 0)
        if 'reverse_info' in info and info['reverse_info']:
            rev_info = info['reverse_info']
            plot_info['reverse_segments'] = rev_info.get('segment_count', 0)
            plot_info['reverse_r2'] = rev_info.get('avg_r2', 0)
        
        # Create visualization
        fig = plot_baseline_results(voltage, current, forward_baseline, reverse_baseline, 
                                  scan_rate, plot_info)
        
        # Save plot
        filename = f"voltage_window_baseline_test_{scan_rate.replace('/', '')}_20250826.png"
        fig.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"💾 Saved plot: {filename}")
        
        plt.close(fig)
        
        # Print summary
        fwd_coverage = np.count_nonzero(forward_baseline) / len(forward_baseline) * 100
        rev_coverage = np.count_nonzero(reverse_baseline) / len(reverse_baseline) * 100
        print(f"📈 Forward coverage: {fwd_coverage:.1f}%")
        print(f"📉 Reverse coverage: {rev_coverage:.1f}%")
        
    print(f"\n✅ Visualization complete! Check PNG files for results.")

if __name__ == "__main__":
    test_and_visualize()