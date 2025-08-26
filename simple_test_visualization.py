#!/usr/bin/env python3
"""
Simple baseline visualization test - processes just 5 files for testing
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from matplotlib.patches import Rectangle
from scipy import stats
import sys

# Import baseline detection
from baseline_detector_v4 import cv_baseline_detector_v4

def load_csv_simple(file_path):
    """Simple CSV loader"""
    try:
        # Check if special format
        df_test = pd.read_csv(file_path, nrows=1)
        if len(df_test.columns) == 1 and 'FileName:' in df_test.columns[0]:
            df = pd.read_csv(file_path, skiprows=1)
        else:
            df = pd.read_csv(file_path)
        
        if len(df.columns) < 2:
            return None, "Not enough columns"
        
        # Assume first column is voltage, second is current
        voltage = df.iloc[:, 0].values
        current = df.iloc[:, 1].values
        
        # Convert current to µA if needed (assume already correct for now)
        
        # Clean data
        valid = ~(np.isnan(voltage) | np.isnan(current) | np.isinf(voltage) | np.isinf(current))
        voltage = voltage[valid]
        current = current[valid]
        
        if len(voltage) < 10:
            return None, "Not enough data points"
            
        return {'voltage': voltage, 'current': current}, None
        
    except Exception as e:
        return None, str(e)

def create_simple_plot(file_path, data, save_path):
    """Create a simple baseline plot"""
    try:
        voltage = data['voltage']
        current = data['current']
        
        # Run baseline detection
        forward_baseline, reverse_baseline, info = cv_baseline_detector_v4(voltage, current)
        
        # Create plot
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        
        # Plot data and baseline
        ax.plot(voltage, current, 'b-', linewidth=1.5, label='CV Data', alpha=0.8)
        
        full_baseline = np.concatenate([forward_baseline, reverse_baseline])
        ax.plot(voltage, full_baseline, 'g-', linewidth=2, label='Baseline')
        
        # Calculate R²
        mid = len(voltage) // 2
        forward_r2 = 0.0
        reverse_r2 = 0.0
        
        if len(forward_baseline) > 2:
            fwd_v = voltage[:len(forward_baseline)]
            try:
                _, _, r_val, _, _ = stats.linregress(fwd_v, forward_baseline)
                forward_r2 = r_val ** 2
            except:
                pass
        
        if len(reverse_baseline) > 2:
            rev_v = voltage[len(forward_baseline):]
            try:
                _, _, r_val, _, _ = stats.linregress(rev_v, reverse_baseline)
                reverse_r2 = r_val ** 2
            except:
                pass
        
        # Format plot
        ax.set_xlabel('Voltage (V)')
        ax.set_ylabel('Current (µA)')
        ax.set_title(f'{os.path.basename(file_path)}\\nForward R²: {forward_r2:.3f}, Reverse R²: {reverse_r2:.3f}')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return forward_r2, reverse_r2
        
    except Exception as e:
        print(f"Plot error: {e}")
        return 0.0, 0.0

def main():
    """Test with just a few files"""
    print("🧪 Simple Baseline Visualization Test")
    print("=" * 40)
    
    # Find test files
    test_files = []
    for root, dirs, files in os.walk('Test_data'):
        for file in files:
            if file.endswith('.csv') and not file.endswith('.backup'):
                test_files.append(os.path.join(root, file))
                if len(test_files) >= 5:  # Just test 5 files
                    break
        if len(test_files) >= 5:
            break
    
    print(f"📁 Found {len(test_files)} test files")
    
    success_count = 0
    for i, file_path in enumerate(test_files):
        print(f"\\n📄 Processing {i+1}/{len(test_files)}: {os.path.basename(file_path)}")
        
        # Load data
        data, error = load_csv_simple(file_path)
        if error:
            print(f"   ❌ Load error: {error}")
            continue
        
        print(f"   📊 Data: {len(data['voltage'])} points")
        
        # Create plot
        plot_path = file_path.replace('.csv', '_test_baseline.png')
        forward_r2, reverse_r2 = create_simple_plot(file_path, data, plot_path)
        
        if os.path.exists(plot_path):
            print(f"   ✅ Plot saved: {os.path.basename(plot_path)}")
            print(f"   📈 R² - Forward: {forward_r2:.3f}, Reverse: {reverse_r2:.3f}")
            success_count += 1
        else:
            print(f"   ❌ Plot failed")
    
    print(f"\\n✅ Test completed: {success_count}/{len(test_files)} successful")

if __name__ == "__main__":
    main()
