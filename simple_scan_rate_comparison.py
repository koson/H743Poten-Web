#!/usr/bin/env python3
"""
Simple Scan Rate Comparison
==========================
Create visual comparison of CV data at different scan rates
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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

def create_simple_scan_rate_comparison():
    """Create simple scan rate comparison plots"""
    
    print("📊 SIMPLE SCAN RATE COMPARISON")
    print("=" * 50)
    
    # Test files with known scan rates
    test_files = [
        ("cv_data/measurement_96_20.0mVs_2025-08-25T06-46-22.774810.csv", 20.0, "20 mV/s"),
        ("cv_data/measurement_98_50.0mVs_2025-08-25T06-46-44.165711.csv", 50.0, "50 mV/s"), 
        ("cv_data/measurement_93_100.0mVs_2025-08-25T06-39-11.686802.csv", 100.0, "100 mV/s"),
        ("cv_data/measurement_95_200.0mVs_2025-08-25T06-46-14.158045.csv", 200.0, "200 mV/s"),
        ("cv_data/measurement_97_400.0mVs_2025-08-25T06-46-33.785412.csv", 400.0, "400 mV/s")
    ]
    
    valid_files = []
    print("📁 Loading CV files...")
    
    for filepath, scan_rate, label in test_files:
        voltage, current = load_test_file(filepath)
        if voltage is not None:
            valid_files.append({
                'scan_rate': scan_rate,
                'voltage': voltage,
                'current': current,
                'label': label,
                'filepath': filepath
            })
            print(f"   ✅ {label}: {len(voltage)} points, I range: {current.min():.1f} to {current.max():.1f} µA")
        else:
            print(f"   ❌ Failed to load: {filepath}")
    
    if len(valid_files) < 2:
        print("❌ Need at least 2 valid files")
        return
    
    # Create comparison plots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    colors = plt.cm.viridis(np.linspace(0, 1, len(valid_files)))
    
    # Plot 1: All CV curves overlaid
    ax = axes[0, 0]
    for i, data in enumerate(valid_files):
        ax.plot(data['voltage'], data['current'], 
                color=colors[i], linewidth=2, alpha=0.8,
                label=data['label'])
    ax.set_xlabel('Voltage (V)')
    ax.set_ylabel('Current (µA)')
    ax.set_title('CV Curves at Different Scan Rates')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 2: Forward sweeps only
    ax = axes[0, 1]
    for i, data in enumerate(valid_files):
        n = len(data['voltage'])
        mid = n // 2
        # Forward sweep (first half)
        ax.plot(data['voltage'][:mid], data['current'][:mid], 
                color=colors[i], linewidth=2, alpha=0.8,
                label=data['label'])
    ax.set_xlabel('Voltage (V)')
    ax.set_ylabel('Current (µA)')
    ax.set_title('Forward Sweeps Only')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 3: Peak current vs scan rate
    ax = axes[1, 0]
    scan_rates = []
    peak_currents = []
    
    for data in valid_files:
        scan_rates.append(data['scan_rate'])
        # Find peak current (maximum absolute value) - data already in µA
        peak_current = np.max(np.abs(data['current']))
        peak_currents.append(peak_current)
    
    ax.plot(scan_rates, peak_currents, 'ro-', linewidth=3, markersize=10)
    
    # Add trend lines
    if len(scan_rates) > 2:
        # Linear fit
        z_linear = np.polyfit(scan_rates, peak_currents, 1)
        fit_linear = np.poly1d(z_linear)
        ax.plot(scan_rates, fit_linear(scan_rates), 'b--', alpha=0.7, 
                label=f'Linear: R²={np.corrcoef(scan_rates, peak_currents)[0,1]**2:.3f}')
        
        # Square root fit (theoretical for diffusion-controlled processes)
        sqrt_rates = np.sqrt(scan_rates)
        z_sqrt = np.polyfit(sqrt_rates, peak_currents, 1)
        fit_sqrt_rates = np.linspace(min(scan_rates), max(scan_rates), 100)
        fit_sqrt_currents = z_sqrt[0] * np.sqrt(fit_sqrt_rates) + z_sqrt[1]
        ax.plot(fit_sqrt_rates, fit_sqrt_currents, 'g--', alpha=0.7,
                label=f'√v fit: R²={np.corrcoef(sqrt_rates, peak_currents)[0,1]**2:.3f}')
        
        ax.legend()
    
    ax.set_xlabel('Scan Rate (mV/s)')
    ax.set_ylabel('Peak Current (µA)')
    ax.set_title('Peak Current vs Scan Rate')
    ax.grid(True, alpha=0.3)
    
    # Plot 4: Current range analysis
    ax = axes[1, 1]
    current_ranges = []
    noise_levels = []
    
    for data in valid_files:
        current_range = (np.max(data['current']) - np.min(data['current']))
        current_ranges.append(current_range)
        
        # Estimate noise from derivative
        current_diff = np.diff(data['current'])
        noise_level = np.std(current_diff)
        noise_levels.append(noise_level)
    
    x_pos = np.arange(len(scan_rates))
    width = 0.35
    
    ax.bar(x_pos - width/2, current_ranges, width, label='Current Range', alpha=0.8, color='blue')
    ax2 = ax.twinx()
    ax2.bar(x_pos + width/2, noise_levels, width, label='Noise Level', alpha=0.8, color='red')
    
    ax.set_xlabel('Scan Rate (mV/s)')
    ax.set_ylabel('Current Range (µA)', color='blue')
    ax2.set_ylabel('Noise Level (µA)', color='red')
    ax.set_title('Signal Quality Analysis')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"{sr:.0f}" for sr in scan_rates])
    
    # Add legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save the plot
    filename = "simple_scan_rate_comparison_20250826.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\n💾 Saved comparison plot: {filename}")
    
    # Print summary table
    print("\n📊 SCAN RATE ANALYSIS SUMMARY:")
    print("-" * 70)
    print(f"{'Rate (mV/s)':<12} {'Peak (µA)':<12} {'Range (µA)':<12} {'Noise (µA)':<12} {'S/N Ratio':<10}")
    print("-" * 70)
    
    for i, data in enumerate(valid_files):
        snr = current_ranges[i] / noise_levels[i] if noise_levels[i] > 0 else 0
        print(f"{data['scan_rate']:>8.0f}     {peak_currents[i]:>10.2f}   {current_ranges[i]:>10.2f}   "
              f"{noise_levels[i]:>10.3f}   {snr:>8.1f}")
    
    # Analyze scan rate dependency
    print("\n🔬 ELECTROCHEMICAL ANALYSIS:")
    print("-" * 40)
    
    if len(scan_rates) > 2:
        # Check if peak current follows Randles-Sevcik equation (I ∝ √v)
        sqrt_correlation = np.corrcoef(sqrt_rates, peak_currents)[0,1]**2
        linear_correlation = np.corrcoef(scan_rates, peak_currents)[0,1]**2
        
        print(f"Peak current vs scan rate (linear): R² = {linear_correlation:.3f}")
        print(f"Peak current vs √(scan rate): R² = {sqrt_correlation:.3f}")
        
        if sqrt_correlation > linear_correlation and sqrt_correlation > 0.9:
            print("✅ Strong √v dependency → Likely diffusion-controlled process")
        elif linear_correlation > sqrt_correlation and linear_correlation > 0.9:
            print("⚠️ Linear dependency → Possible adsorption or kinetic control")
        else:
            print("❓ Mixed behavior → Complex electrochemical mechanism")
    
    plt.show()
    return fig

if __name__ == "__main__":
    create_simple_scan_rate_comparison()