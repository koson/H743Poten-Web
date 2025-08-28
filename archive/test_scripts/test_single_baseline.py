#!/usr/bin/env python3
"""
Test single file baseline detection
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import logging
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Import our existing baseline detector
import sys
sys.path.append('.')
from baseline_detector_voltage_windows import voltage_window_baseline_detector

# Configure logging
logging.basicConfig(level=logging.WARNING)

def calculate_r2_for_baseline(voltage_data, baseline_data, segment_type=""):
    """Calculate R² for baseline fit"""
    if len(baseline_data) < 2:
        return 0.0
    
    try:
        # Simple linear regression for R²
        slope, intercept, r_value, p_value, std_err = stats.linregress(voltage_data, baseline_data)
        return r_value ** 2
    except:
        return 0.0

def load_and_process_csv(file_path):
    """Load CSV file and process with our existing logic"""
    try:
        # Read CSV file - skip first row if it contains filename
        first_line = pd.read_csv(file_path, nrows=1, header=None, encoding='utf-8')
        if 'FileName:' in str(first_line.iloc[0, 0]):
            # Skip first row with filename
            df = pd.read_csv(file_path, skiprows=1, encoding='utf-8')
        else:
            df = pd.read_csv(file_path, encoding='utf-8')
        
        # Find voltage and current columns (case-insensitive)
        headers = [h.strip().lower() for h in df.columns]
        voltage_idx = -1
        current_idx = -1
        
        for i, header in enumerate(headers):
            if any(keyword in header for keyword in ['voltage', 'potential', 'v', 'volt']):
                voltage_idx = i
            elif any(keyword in header for keyword in ['current', 'i', 'ua', 'µa', 'ma', 'na', 'a']):
                current_idx = i
        
        if voltage_idx == -1 or current_idx == -1:
            return None, None, None, "Could not find voltage/current columns"
        
        print(f"   📊 Found columns: {df.columns[voltage_idx]} (V), {df.columns[current_idx]} (I)")
        
        # Get data using original column names
        voltage_data = df.iloc[:, voltage_idx].values
        current_data = df.iloc[:, current_idx].values
        
        # Unit conversion logic (same as backend)
        current_unit = df.columns[current_idx].strip()
        current_unit_lower = current_unit.lower()
        
        current_scale = 1.0
        if current_unit_lower == 'ma':
            current_scale = 1e3  # milliAmps to microAmps
        elif current_unit_lower == 'na':
            current_scale = 1e-3  # nanoAmps to microAmps
        elif current_unit_lower == 'a':
            current_scale = 1e6  # Amperes to microAmps
        elif current_unit_lower in ['ua', 'µa']:
            current_scale = 1.0  # microAmps - keep as is
        
        # Apply scaling
        current_data = current_data * current_scale
        
        print(f"   🔢 Current unit: {current_unit} -> scale: {current_scale}")
        print(f"   📈 Data range: V=[{voltage_data.min():.3f}, {voltage_data.max():.3f}], I=[{current_data.min():.1f}, {current_data.max():.1f}] µA")
        
        # Remove invalid data points
        valid_mask = ~(np.isnan(voltage_data) | np.isnan(current_data) | 
                      np.isinf(voltage_data) | np.isinf(current_data))
        
        voltage_data = voltage_data[valid_mask]
        current_data = current_data[valid_mask]
        
        if len(voltage_data) < 10:
            return None, None, None, "Not enough valid data points"
        
        print(f"   ✅ Valid data points: {len(voltage_data)}")
        
        # Detect baseline using our algorithm
        forward_baseline, reverse_baseline, baseline_info = voltage_window_baseline_detector(
            voltage_data, current_data
        )
        
        print(f"   🔍 Baseline detection results:")
        print(f"      Forward baseline: {len(forward_baseline)} points")
        print(f"      Reverse baseline: {len(reverse_baseline)} points")
        print(f"      Info keys: {list(baseline_info.keys())}")
        
        # Convert to our expected format
        if len(forward_baseline) == 0 and len(reverse_baseline) == 0:
            return None, None, None, "No baseline detected"
        
        # Combine baseline voltage points
        all_baseline_voltage = np.concatenate([forward_baseline, reverse_baseline]) if len(forward_baseline) > 0 and len(reverse_baseline) > 0 else (forward_baseline if len(forward_baseline) > 0 else reverse_baseline)
        
        # Calculate corresponding current values by interpolating from original data
        all_baseline_current = np.interp(all_baseline_voltage, voltage_data, current_data)
        
        # Create baseline_result dict for compatibility
        baseline_result = {
            'baseline_detected': True,
            'baseline_voltage': all_baseline_voltage,
            'baseline_current': all_baseline_current,
            'forward_segments': [],
            'reverse_segments': [],
            'info': baseline_info
        }
        
        print(f"   📊 Final baseline: {len(baseline_result['baseline_voltage'])} voltage points, {len(baseline_result['baseline_current'])} current points")
        
        return voltage_data, current_data, baseline_result, None
        
    except Exception as e:
        return None, None, None, f"Error processing file: {str(e)}"

def create_baseline_plot(file_path, voltage_data, current_data, baseline_result, save_path):
    """Create a baseline detection plot"""
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Get filename for title
    filename = os.path.basename(file_path)
    
    # Extract scan rate from filename if possible
    scan_rate = "Unknown"
    if "mVpS" in filename or "mvps" in filename.lower():
        try:
            # Find scan rate pattern
            import re
            match = re.search(r'(\d+)mVpS', filename, re.IGNORECASE)
            if match:
                scan_rate = f"{match.group(1)}mVpS"
        except:
            pass
    
    # Plot CV data
    ax.plot(voltage_data, current_data, 'b-', linewidth=2, label='CV Data', alpha=0.8)
    
    # Plot baseline
    baseline_voltage = baseline_result['baseline_voltage']
    baseline_current = baseline_result['baseline_current']
    ax.plot(baseline_voltage, baseline_current, 'g-', linewidth=3, label='Baseline')
    
    # Calculate R² values for forward and reverse segments
    forward_r2 = 0.0
    reverse_r2 = 0.0
    
    # Estimate R² from baseline segments
    if len(baseline_voltage) > 1 and len(baseline_current) > 1:
        try:
            # Simple R² for the entire baseline
            slope, intercept, r_value, p_value, std_err = stats.linregress(baseline_voltage, baseline_current)
            baseline_r2 = r_value ** 2
        except:
            baseline_r2 = 0.0
    else:
        baseline_r2 = 0.0
    
    # Formatting
    ax.set_xlabel('Voltage (V)', fontsize=12)
    ax.set_ylabel('Current (µA)', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    
    # Title with filename and scan rate
    ax.set_title(f'✅ Baseline Detection Test ({scan_rate})\n{filename}', 
                fontsize=14, fontweight='bold')
    
    # Add R² values as text
    ax.text(0.02, 0.98, f'Baseline R²: {baseline_r2:.3f}\nBaseline Points: {len(baseline_voltage)}', 
            transform=ax.transAxes, fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return baseline_r2

def main():
    """Test single file"""
    
    print("🧪 Single File Baseline Detection Test")
    print("=" * 50)
    
    # Test with a single file
    file_path = "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_100mVpS_E4_scan_05.csv"
    
    print(f"📁 Testing file: {os.path.basename(file_path)}")
    
    # Load and process data
    voltage_data, current_data, baseline_result, error = load_and_process_csv(file_path)
    
    if error:
        print(f"   ❌ Failed: {error}")
        return
    
    # Create plot filename
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    plot_filename = f"{base_name}_test_baseline.png"
    plot_path = plot_filename
    
    try:
        # Create and save plot
        baseline_r2 = create_baseline_plot(
            file_path, voltage_data, current_data, baseline_result, plot_path
        )
        
        print(f"   ✅ Plot saved: {plot_filename}")
        print(f"   📊 Baseline R²: {baseline_r2:.3f}")
        
    except Exception as e:
        print(f"   ❌ Plot failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()