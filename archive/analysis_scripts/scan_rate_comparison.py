#!/usr/bin/env python3
"""
Scan Rate Comparison with Voltage Window Baseline Detection
==========================================================
Compare CV data at different scan rates using the new voltage window baseline detector
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging
from baseline_detector_voltage_windows import voltage_window_baseline_detector

# Set up logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s:%(name)s:%(message)s')

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

def extract_scan_rate(filename):
    """Extract scan rate from filename"""
    import re
    match = re.search(r'(\d+\.?\d*)mVs?', filename)
    if match:
        return float(match.group(1))
    return None

def create_scan_rate_comparison():
    """Create comprehensive scan rate comparison plots"""
    
    print("📊 SCAN RATE COMPARISON WITH VOLTAGE WINDOW BASELINE DETECTION")
    print("=" * 80)
    
    # Find all CV files and extract scan rates
    import glob
    cv_files = glob.glob("cv_data/*.csv")
    
    file_data = []
    for filepath in cv_files:
        scan_rate = extract_scan_rate(filepath)
        if scan_rate:
            voltage, current = load_test_file(filepath)
            if voltage is not None:
                file_data.append({
                    'filepath': filepath,
                    'scan_rate': scan_rate,
                    'voltage': voltage,
                    'current': current
                })
    
    # Sort by scan rate
    file_data.sort(key=lambda x: x['scan_rate'])
    
    print(f"📁 Found {len(file_data)} CV files with scan rates:")
    for data in file_data:
        print(f"   {data['scan_rate']:>6.1f} mV/s: {data['filepath']}")
    
    if len(file_data) < 2:
        print("❌ Need at least 2 files with different scan rates")
        return
    
    # Create comparison plots
    fig = plt.figure(figsize=(16, 12))
    
    # Define colors for different scan rates
    colors = plt.cm.viridis(np.linspace(0, 1, len(file_data)))
    
    # Plot 1: Original CV curves
    ax1 = plt.subplot(2, 3, 1)
    for i, data in enumerate(file_data):
        ax1.plot(data['voltage'], data['current'] * 1e6, 
                color=colors[i], linewidth=1.5, alpha=0.8,
                label=f"{data['scan_rate']:.0f} mV/s")
    ax1.set_xlabel('Voltage (V)')
    ax1.set_ylabel('Current (µA)')
    ax1.set_title('Original CV Curves')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Baseline-corrected CV curves
    ax2 = plt.subplot(2, 3, 2)
    baseline_results = []
    
    print("\n🔍 Processing baseline detection...")
    for i, data in enumerate(file_data):
        print(f"   Processing {data['scan_rate']:.0f} mV/s...")
        
        # Run voltage window baseline detection
        forward_baseline, reverse_baseline, info = voltage_window_baseline_detector(
            data['voltage'], data['current']
        )
        
        # Create baseline-corrected current
        corrected_current = data['current'].copy()
        n = len(data['voltage'])
        mid = n // 2
        
        if np.any(forward_baseline):
            corrected_current[:mid] = data['current'][:mid] - forward_baseline
        if np.any(reverse_baseline):
            corrected_current[mid:] = data['current'][mid:] - reverse_baseline
        
        baseline_results.append({
            'scan_rate': data['scan_rate'],
            'voltage': data['voltage'],
            'corrected_current': corrected_current,
            'forward_baseline': forward_baseline,
            'reverse_baseline': reverse_baseline,
            'info': info
        })
        
        # Plot baseline-corrected curve
        ax2.plot(data['voltage'], corrected_current * 1e6, 
                color=colors[i], linewidth=1.5, alpha=0.8,
                label=f"{data['scan_rate']:.0f} mV/s")
    
    ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    ax2.set_xlabel('Voltage (V)')
    ax2.set_ylabel('Current (µA)')
    ax2.set_title('Baseline-Corrected CV Curves')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Peak current vs scan rate
    ax3 = plt.subplot(2, 3, 3)
    scan_rates = []
    peak_currents = []
    
    for result in baseline_results:
        scan_rates.append(result['scan_rate'])
        # Find peak current (maximum absolute value)
        peak_current = np.max(np.abs(result['corrected_current'])) * 1e6
        peak_currents.append(peak_current)
    
    ax3.plot(scan_rates, peak_currents, 'ro-', linewidth=2, markersize=8)
    ax3.set_xlabel('Scan Rate (mV/s)')
    ax3.set_ylabel('Peak Current (µA)')
    ax3.set_title('Peak Current vs Scan Rate')
    ax3.grid(True, alpha=0.3)
    
    # Add trend line
    if len(scan_rates) > 2:
        z = np.polyfit(scan_rates, peak_currents, 1)
        p = np.poly1d(z)
        ax3.plot(scan_rates, p(scan_rates), 'r--', alpha=0.7, 
                label=f'Slope: {z[0]:.2f} µA/(mV/s)')
        ax3.legend()
    
    # Plot 4: Baseline quality comparison
    ax4 = plt.subplot(2, 3, 4)
    forward_r2 = []
    reverse_r2 = []
    
    for result in baseline_results:
        info = result['info']
        fwd_r2 = 0
        rev_r2 = 0
        
        if 'forward_info' in info and info['forward_info']:
            fwd_r2 = info['forward_info'].get('avg_r2', 0)
        if 'reverse_info' in info and info['reverse_info']:
            rev_r2 = info['reverse_info'].get('avg_r2', 0)
            
        forward_r2.append(fwd_r2)
        reverse_r2.append(rev_r2)
    
    x_pos = np.arange(len(scan_rates))
    width = 0.35
    
    ax4.bar(x_pos - width/2, forward_r2, width, label='Forward', alpha=0.8)
    ax4.bar(x_pos + width/2, reverse_r2, width, label='Reverse', alpha=0.8)
    ax4.set_xlabel('Scan Rate (mV/s)')
    ax4.set_ylabel('Average R²')
    ax4.set_title('Baseline Quality (R²)')
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels([f"{sr:.0f}" for sr in scan_rates])
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(0, 1.05)
    
    # Plot 5: Baseline segments count
    ax5 = plt.subplot(2, 3, 5)
    forward_segments = []
    reverse_segments = []
    
    for result in baseline_results:
        info = result['info']
        fwd_seg = 0
        rev_seg = 0
        
        if 'forward_info' in info and info['forward_info']:
            fwd_seg = info['forward_info'].get('segment_count', 0)
        if 'reverse_info' in info and info['reverse_info']:
            rev_seg = info['reverse_info'].get('segment_count', 0)
            
        forward_segments.append(fwd_seg)
        reverse_segments.append(rev_seg)
    
    ax5.bar(x_pos - width/2, forward_segments, width, label='Forward', alpha=0.8)
    ax5.bar(x_pos + width/2, reverse_segments, width, label='Reverse', alpha=0.8)
    ax5.set_xlabel('Scan Rate (mV/s)')
    ax5.set_ylabel('Number of Segments')
    ax5.set_title('Baseline Segments Count')
    ax5.set_xticks(x_pos)
    ax5.set_xticklabels([f"{sr:.0f}" for sr in scan_rates])
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # Plot 6: Current range comparison
    ax6 = plt.subplot(2, 3, 6)
    current_ranges = []
    
    for data in file_data:
        current_range = (np.max(data['current']) - np.min(data['current'])) * 1e6
        current_ranges.append(current_range)
    
    ax6.plot(scan_rates, current_ranges, 'bo-', linewidth=2, markersize=8)
    ax6.set_xlabel('Scan Rate (mV/s)')
    ax6.set_ylabel('Current Range (µA)')
    ax6.set_title('Current Range vs Scan Rate')
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save the plot
    timestamp = "20250826"
    filename = f"scan_rate_comparison_{timestamp}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\n💾 Saved comprehensive comparison: {filename}")
    
    # Print summary statistics
    print("\n📊 BASELINE DETECTION SUMMARY:")
    print("-" * 50)
    for i, result in enumerate(baseline_results):
        info = result['info']
        fwd_info = info.get('forward_info', {})
        rev_info = info.get('reverse_info', {})
        
        print(f"{result['scan_rate']:>6.0f} mV/s: "
              f"Forward({fwd_info.get('segment_count', 0)} seg, R²={fwd_info.get('avg_r2', 0):.3f}) "
              f"Reverse({rev_info.get('segment_count', 0)} seg, R²={rev_info.get('avg_r2', 0):.3f})")
    
    plt.show()
    return fig

if __name__ == "__main__":
    create_scan_rate_comparison()