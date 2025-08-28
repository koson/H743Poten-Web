#!/usr/bin/env python3
"""
Batch baseline detection visualization for all CSV files in Test_data
Creates plots similar to the reference image with filename titles and R² values
"""

import os
import glob
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
        
        # Remove invalid data points
        valid_mask = ~(np.isnan(voltage_data) | np.isnan(current_data) | 
                      np.isinf(voltage_data) | np.isinf(current_data))
        
        voltage_data = voltage_data[valid_mask]
        current_data = current_data[valid_mask]
        
        if len(voltage_data) < 10:
            return None, None, None, "Not enough valid data points"
        
        # Detect baseline using our algorithm
        forward_baseline, reverse_baseline, baseline_info = voltage_window_baseline_detector(
            voltage_data, current_data
        )
        
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
        
        return voltage_data, current_data, baseline_result, None
        
    except Exception as e:
        return None, None, None, f"Error processing file: {str(e)}"

def create_baseline_plot(file_path, voltage_data, current_data, baseline_result, save_path):
    """Create a baseline detection plot similar to the reference image"""
    
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
    
    if 'forward_segments' in baseline_result and baseline_result['forward_segments']:
        forward_data = baseline_result['forward_segments']
        if len(forward_data) > 1:
            fwd_v = [seg['voltage'] for seg in forward_data]
            fwd_i = [seg['current'] for seg in forward_data]
            if len(fwd_v) > 1:
                forward_r2 = calculate_r2_for_baseline(fwd_v, fwd_i, "forward")
    
    if 'reverse_segments' in baseline_result and baseline_result['reverse_segments']:
        reverse_data = baseline_result['reverse_segments']
        if len(reverse_data) > 1:
            rev_v = [seg['voltage'] for seg in reverse_data]
            rev_i = [seg['current'] for seg in reverse_data]
            if len(rev_v) > 1:
                reverse_r2 = calculate_r2_for_baseline(rev_v, rev_i, "reverse")
    
    # Add voltage windows as colored backgrounds
    v_min, v_max = min(voltage_data), max(voltage_data)
    i_min, i_max = min(current_data), max(current_data)
    
    # Forward segment highlight (green)
    if 'forward_segments' in baseline_result and baseline_result['forward_segments']:
        forward_v_range = [seg['voltage'] for seg in baseline_result['forward_segments']]
        if forward_v_range:
            fw_min, fw_max = min(forward_v_range), max(forward_v_range)
            rect_forward = Rectangle((fw_min, i_min), fw_max - fw_min, i_max - i_min, 
                                   facecolor='lightgreen', alpha=0.3, 
                                   label=f'Forward Seg ({len(baseline_result["forward_segments"])} pts)')
            ax.add_patch(rect_forward)
    
    # Reverse segment highlight (orange)  
    if 'reverse_segments' in baseline_result and baseline_result['reverse_segments']:
        reverse_v_range = [seg['voltage'] for seg in baseline_result['reverse_segments']]
        if reverse_v_range:
            rv_min, rv_max = min(reverse_v_range), max(reverse_v_range)
            rect_reverse = Rectangle((rv_min, i_min), rv_max - rv_min, i_max - i_min,
                                   facecolor='orange', alpha=0.3,
                                   label=f'Reverse Seg ({len(baseline_result["reverse_segments"])} pts)')
            ax.add_patch(rect_reverse)
    
    # Formatting
    ax.set_xlabel('Voltage (V)', fontsize=12)
    ax.set_ylabel('Current (µA)', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    
    # Title with filename and scan rate
    ax.set_title(f'✅ Good Baseline Detection ({scan_rate})\n{filename}', 
                fontsize=14, fontweight='bold')
    
    # Add R² values as text
    ax.text(0.02, 0.98, f'Forward R²: {forward_r2:.3f}\nReverse R²: {reverse_r2:.3f}', 
            transform=ax.transAxes, fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return forward_r2, reverse_r2

def main():
    """Main function to process all CSV files"""
    
    print("🎯 Batch Baseline Detection Visualization")
    print("=" * 50)
    
    # Find all CSV files (excluding backups)
    test_data_path = "Test_data"
    csv_files = []
    
    for root, dirs, files in os.walk(test_data_path):
        for file in files:
            if file.endswith('.csv') and not file.endswith('.backup'):
                csv_files.append(os.path.join(root, file))
    
    print(f"Found {len(csv_files)} CSV files to process")
    
    # Process each file
    successful_plots = 0
    failed_files = []
    
    for i, file_path in enumerate(csv_files):
        print(f"\n📁 Processing ({i+1}/{len(csv_files)}): {os.path.basename(file_path)}")
        
        # Load and process data
        voltage_data, current_data, baseline_result, error = load_and_process_csv(file_path)
        
        if error:
            print(f"   ❌ Failed: {error}")
            failed_files.append((file_path, error))
            continue
        
        # Create plot filename
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        plot_filename = f"{base_name}_baseline_plot.png"
        plot_path = os.path.join(os.path.dirname(file_path), plot_filename)
        
        try:
            # Create and save plot
            forward_r2, reverse_r2 = create_baseline_plot(
                file_path, voltage_data, current_data, baseline_result, plot_path
            )
            
            print(f"   ✅ Plot saved: {plot_filename}")
            print(f"   📊 R² - Forward: {forward_r2:.3f}, Reverse: {reverse_r2:.3f}")
            successful_plots += 1
            
        except Exception as e:
            print(f"   ❌ Plot failed: {str(e)}")
            failed_files.append((file_path, f"Plot error: {str(e)}"))
    
    # Summary
    print("\n" + "=" * 50)
    print("📈 SUMMARY")
    print(f"✅ Successful plots: {successful_plots}")
    print(f"❌ Failed files: {len(failed_files)}")
    
    if failed_files:
        print("\n❌ Failed files:")
        for file_path, error in failed_files[:10]:  # Show first 10 failures
            print(f"   {os.path.basename(file_path)}: {error}")
        if len(failed_files) > 10:
            print(f"   ... and {len(failed_files) - 10} more")
    
    print(f"\n🎯 All plots saved in their respective directories!")

if __name__ == "__main__":
    main()