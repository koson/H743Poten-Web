#!/usr/bin/env python3
"""
Clean Scan Rate Comparison
=========================
Compare CV data at different scan rates with good baseline detection
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging
from baseline_detector_voltage_windows import voltage_window_baseline_detector

# Set up logging - allow some info
logging.basicConfig(level=logging.WARNING)

def load_test_file(filepath):
    """Load CV data from CSV file"""
    try:
        df = pd.read_csv(filepath)
        
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
        return None, None

def test_baseline_quality(voltage, current):
    """Test if baseline detection works well for this file"""
    try:
        forward_baseline, reverse_baseline, info = voltage_window_baseline_detector(
            voltage, current
        )
        
        # Check if we got good baselines
        fwd_segments = 0
        rev_segments = 0
        fwd_r2 = 0
        rev_r2 = 0
        
        if 'forward_info' in info and info['forward_info']:
            fwd_info = info['forward_info']
            fwd_segments = fwd_info.get('segment_count', 0)
            fwd_r2 = fwd_info.get('avg_r2', 0)
            
        if 'reverse_info' in info and info['reverse_info']:
            rev_info = info['reverse_info']
            rev_segments = rev_info.get('segment_count', 0)
            rev_r2 = rev_info.get('avg_r2', 0)
        
        # Good baseline if we have segments (relaxed criteria)
        is_good = (fwd_segments > 0 and fwd_r2 > 0.5) or (rev_segments > 0 and rev_r2 > 0.5)
        
        # Debug print
        print(f"        Fwd: {fwd_segments} seg, R²={fwd_r2:.3f}, Rev: {rev_segments} seg, R²={rev_r2:.3f}, Good: {is_good}")
        
        return is_good, (forward_baseline, reverse_baseline, info)
    except:
        return False, None

def create_clean_scan_rate_comparison():
    """Create clean scan rate comparison with working files only"""
    
    print("📊 CLEAN SCAN RATE COMPARISON")
    print("=" * 50)
    
    # Test specific files that we know work well
    test_files = [
        ("cv_data/measurement_96_20.0mVs_2025-08-25T06-46-22.774810.csv", 20.0),
        ("cv_data/measurement_98_50.0mVs_2025-08-25T06-46-44.165711.csv", 50.0), 
        ("cv_data/measurement_93_100.0mVs_2025-08-25T06-39-11.686802.csv", 100.0),
        ("cv_data/measurement_95_200.0mVs_2025-08-25T06-46-14.158045.csv", 200.0),
        ("cv_data/measurement_97_400.0mVs_2025-08-25T06-46-33.785412.csv", 400.0)
    ]
    
    good_files = []
    print("🔍 Testing files for baseline quality...")
    
    for filepath, scan_rate in test_files:
        print(f"   Testing {scan_rate:>6.0f} mV/s: {filepath}")
        voltage, current = load_test_file(filepath)
        if voltage is not None:
            is_good, result = test_baseline_quality(voltage, current)
            if is_good:
                good_files.append({
                    'scan_rate': scan_rate,
                    'voltage': voltage,
                    'current': current,
                    'filepath': filepath,
                    'baseline_result': result
                })
                print(f"      ✅ Good baseline detected")
            else:
                print(f"      ❌ Poor baseline quality")
        else:
            print(f"      ❌ Failed to load file")
    
    if len(good_files) < 2:
        print("❌ Need at least 2 files with good baselines")
        return
    
    print(f"\n📁 Using {len(good_files)} files with good baselines:")
    for data in good_files:
        print(f"   {data['scan_rate']:>6.0f} mV/s: {data['filepath']}")
    
    # Create the comparison plot
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    colors = plt.cm.Set1(np.linspace(0, 1, len(good_files)))
    
    # Plot 1: Original CV curves
    ax = axes[0, 0]
    for i, data in enumerate(good_files):
        ax.plot(data['voltage'], data['current'] * 1e6, 
                color=colors[i], linewidth=2, alpha=0.8,
                label=f"{data['scan_rate']:.0f} mV/s")
    ax.set_xlabel('Voltage (V)')
    ax.set_ylabel('Current (µA)')
    ax.set_title('Original CV Curves')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 2: Baseline-corrected CV curves
    ax = axes[0, 1]
    corrected_data = []
    
    for i, data in enumerate(good_files):
        forward_baseline, reverse_baseline, info = data['baseline_result']
        
        # Create baseline-corrected current
        corrected_current = data['current'].copy()
        n = len(data['voltage'])
        mid = n // 2
        
        if np.any(forward_baseline):
            corrected_current[:mid] = data['current'][:mid] - forward_baseline
        if np.any(reverse_baseline):
            corrected_current[mid:] = data['current'][mid:] - reverse_baseline
        
        corrected_data.append(corrected_current)
        
        ax.plot(data['voltage'], corrected_current * 1e6, 
                color=colors[i], linewidth=2, alpha=0.8,
                label=f"{data['scan_rate']:.0f} mV/s")
    
    ax.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    ax.set_xlabel('Voltage (V)')
    ax.set_ylabel('Current (µA)')
    ax.set_title('Baseline-Corrected CV')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 3: Peak current vs scan rate
    ax = axes[0, 2]
    scan_rates = [data['scan_rate'] for data in good_files]
    peak_currents = []
    
    for corrected_current in corrected_data:
        peak_current = np.max(np.abs(corrected_current)) * 1e6
        peak_currents.append(peak_current)
    
    ax.plot(scan_rates, peak_currents, 'ro-', linewidth=3, markersize=10)
    ax.set_xlabel('Scan Rate (mV/s)')
    ax.set_ylabel('Peak Current (µA)')
    ax.set_title('Peak Current vs Scan Rate')
    ax.grid(True, alpha=0.3)
    
    # Add theoretical sqrt relationship
    if len(scan_rates) > 2:
        # Fit to I = k * sqrt(v)
        sqrt_rates = np.sqrt(scan_rates)
        z = np.polyfit(sqrt_rates, peak_currents, 1)
        fit_rates = np.linspace(min(scan_rates), max(scan_rates), 100)
        fit_currents = z[0] * np.sqrt(fit_rates) + z[1]
        ax.plot(fit_rates, fit_currents, 'b--', alpha=0.7, 
                label=f'√v fit: R²={np.corrcoef(sqrt_rates, peak_currents)[0,1]**2:.3f}')
        ax.legend()
    
    # Plot 4: Baseline segments quality
    ax = axes[1, 0]
    forward_segments = []
    reverse_segments = []
    forward_r2 = []
    reverse_r2 = []
    
    for data in good_files:
        info = data['baseline_result'][2]
        
        fwd_seg = 0
        rev_seg = 0
        fwd_r2 = 0
        rev_r2 = 0
        
        if 'forward_info' in info and info['forward_info']:
            fwd_info = info['forward_info']
            fwd_seg = fwd_info.get('segment_count', 0)
            fwd_r2 = fwd_info.get('avg_r2', 0)
            
        if 'reverse_info' in info and info['reverse_info']:
            rev_info = info['reverse_info']
            rev_seg = rev_info.get('segment_count', 0)
            rev_r2 = rev_info.get('avg_r2', 0)
        
        forward_segments.append(fwd_seg)
        reverse_segments.append(rev_seg)
        forward_r2.append(fwd_r2)
        reverse_r2.append(rev_r2)
    
    x_pos = np.arange(len(scan_rates))
    width = 0.35
    
    ax.bar(x_pos - width/2, forward_segments, width, label='Forward', alpha=0.8, color='blue')
    ax.bar(x_pos + width/2, reverse_segments, width, label='Reverse', alpha=0.8, color='red')
    ax.set_xlabel('Scan Rate (mV/s)')
    ax.set_ylabel('Number of Segments')
    ax.set_title('Baseline Segments Count')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"{sr:.0f}" for sr in scan_rates])
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 5: R² quality
    ax = axes[1, 1]
    ax.bar(x_pos - width/2, forward_r2, width, label='Forward R²', alpha=0.8, color='blue')
    ax.bar(x_pos + width/2, reverse_r2, width, label='Reverse R²', alpha=0.8, color='red')
    ax.set_xlabel('Scan Rate (mV/s)')
    ax.set_ylabel('Average R²')
    ax.set_title('Baseline Quality (R²)')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"{sr:.0f}" for sr in scan_rates])
    ax.set_ylim(0, 1.05)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 6: Current density comparison (normalized by area)
    ax = axes[1, 2]
    # Assume electrode area = 1 cm² for this comparison
    current_densities = [pc for pc in peak_currents]  # µA/cm²
    
    ax.bar(range(len(scan_rates)), current_densities, alpha=0.8, color=colors)
    ax.set_xlabel('Scan Rate (mV/s)')
    ax.set_ylabel('Peak Current Density (µA/cm²)')
    ax.set_title('Current Density Comparison')
    ax.set_xticks(range(len(scan_rates)))
    ax.set_xticklabels([f"{sr:.0f}" for sr in scan_rates])
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save the plot
    filename = "clean_scan_rate_comparison_20250826.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\n💾 Saved comparison plot: {filename}")
    
    # Print detailed summary
    print("\n📊 DETAILED BASELINE SUMMARY:")
    print("-" * 60)
    print(f"{'Scan Rate':<12} {'Fwd Seg':<8} {'Fwd R²':<8} {'Rev Seg':<8} {'Rev R²':<8} {'Peak µA':<10}")
    print("-" * 60)
    
    for i, data in enumerate(good_files):
        print(f"{data['scan_rate']:>8.0f} mV/s {forward_segments[i]:>6d} {forward_r2[i]:>10.3f} "
              f"{reverse_segments[i]:>6d} {reverse_r2[i]:>10.3f} {peak_currents[i]:>10.2f}")
    
    plt.show()
    return fig, good_files

if __name__ == "__main__":
    create_clean_scan_rate_comparison()