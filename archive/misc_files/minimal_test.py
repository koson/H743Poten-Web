#!/usr/bin/env python3
"""
Minimal test - just plot CV data without baseline detection
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import os

def test_minimal():
    """Test minimal plotting"""
    print("🔬 Minimal CV Plotting Test")
    
    # Get a test file
    test_file = 'Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_100mVpS_E1_scan_05.csv'
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"📁 Loading: {os.path.basename(test_file)}")
    
    # Load data
    df = pd.read_csv(test_file, skiprows=1)  # Skip header
    voltage = df.iloc[:, 0].values
    current = df.iloc[:, 1].values
    
    print(f"📊 Data: {len(voltage)} points")
    print(f"⚡ Voltage: {voltage.min():.3f} to {voltage.max():.3f} V")
    print(f"🔌 Current: {current.min():.2e} to {current.max():.2e} µA")
    
    # Create simple plot
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.plot(voltage, current, 'b-', linewidth=2, label='CV Data')
    ax.set_xlabel('Voltage (V)')
    ax.set_ylabel('Current (µA)')
    ax.set_title(f'CV Plot: {os.path.basename(test_file)}')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Save plot
    plot_path = test_file.replace('.csv', '_minimal_plot.png')
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    if os.path.exists(plot_path):
        print(f"✅ Minimal plot saved: {os.path.basename(plot_path)}")
    else:
        print("❌ Plot save failed")

if __name__ == "__main__":
    test_minimal()
