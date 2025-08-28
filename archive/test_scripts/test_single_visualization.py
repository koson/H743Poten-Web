#!/usr/bin/env python3
"""
Test batch visualization with a single file first
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import logging
from sklearn.metrics import r2_score
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Import our existing baseline detector
import sys
sys.path.append('.')

try:
    from baseline_detector_voltage_windows import detect_baseline_voltage_windows
    print("✅ Successfully imported baseline detector")
except ImportError as e:
    print(f"❌ Failed to import baseline detector: {e}")
    sys.exit(1)

def test_single_file():
    """Test with a single file"""
    test_file = "Test_data/Stm32/Pipot_Ferro_1_0mM_20mVpS_E4_scan_05.csv"
    
    print(f"🧪 Testing with: {test_file}")
    
    if not os.path.exists(test_file):
        print(f"❌ File not found: {test_file}")
        return
    
    try:
        # Read CSV file
        df = pd.read_csv(test_file, encoding='utf-8')
        print(f"✅ Loaded CSV: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Find voltage and current columns
        headers = [h.strip().lower() for h in df.columns]
        voltage_idx = -1
        current_idx = -1
        
        for i, header in enumerate(headers):
            if any(keyword in header for keyword in ['voltage', 'potential', 'v']):
                voltage_idx = i
            elif any(keyword in header for keyword in ['current', 'i']):
                current_idx = i
        
        print(f"Voltage column index: {voltage_idx}")
        print(f"Current column index: {current_idx}")
        
        if voltage_idx == -1 or current_idx == -1:
            print("❌ Could not find voltage/current columns")
            return
        
        # Get data
        voltage_data = df.iloc[:, voltage_idx].values
        current_data = df.iloc[:, current_idx].values
        
        print(f"Data points: {len(voltage_data)}")
        print(f"Voltage range: {min(voltage_data):.3f} to {max(voltage_data):.3f} V")
        print(f"Current range: {min(current_data):.3e} to {max(current_data):.3e}")
        
        # Unit conversion
        current_unit = df.columns[current_idx].strip()
        current_unit_lower = current_unit.lower()
        print(f"Current unit: '{current_unit}' -> '{current_unit_lower}'")
        
        current_scale = 1.0
        if current_unit_lower == 'ma':
            current_scale = 1e3
        elif current_unit_lower == 'na':
            current_scale = 1e-3
        elif current_unit_lower == 'a':
            current_scale = 1e6
        elif current_unit_lower in ['ua', 'µa']:
            current_scale = 1.0
        
        print(f"Current scale factor: {current_scale}")
        current_data = current_data * current_scale
        print(f"After scaling - Current range: {min(current_data):.3f} to {max(current_data):.3f} µA")
        
        # Detect baseline
        print("🔍 Running baseline detection...")
        baseline_result = detect_baseline_voltage_windows(
            voltage_data, current_data,
            min_window_size=15,
            max_baseline_current_µA=50.0,
            min_baseline_points=10
        )
        
        print(f"Baseline detected: {baseline_result['baseline_detected']}")
        if baseline_result['baseline_detected']:
            print(f"Baseline points: {len(baseline_result['baseline_voltage'])}")
            
            # Create simple plot
            plt.figure(figsize=(10, 6))
            plt.plot(voltage_data, current_data, 'b-', label='CV Data', alpha=0.7)
            plt.plot(baseline_result['baseline_voltage'], baseline_result['baseline_current'], 
                    'g-', linewidth=3, label='Baseline')
            plt.xlabel('Voltage (V)')
            plt.ylabel('Current (µA)')
            plt.title(f'Test: {os.path.basename(test_file)}')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plot_path = "test_baseline_plot.png"
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Test plot saved: {plot_path}")
        else:
            print("❌ No baseline detected")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_file()