#!/usr/bin/env python3
"""
Limited batch baseline detection for testing - process just a few files
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
    
    # Calculate R² values for baseline
    baseline_r2 = 0.0
    if len(baseline_voltage) > 1 and len(baseline_current) > 1:
        try:
            slope, intercept, r_value, p_value, std_err = stats.linregress(baseline_voltage, baseline_current)
            baseline_r2 = r_value ** 2
        except:
            pass
    
    # Formatting
    ax.set_xlabel('Voltage (V)', fontsize=12)
    ax.set_ylabel('Current (µA)', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    
    # Quality assessment based on R² and baseline points
    baseline_points = len(baseline_voltage)
    if baseline_r2 > 0.8 and baseline_points > 50:
        quality = "EXCELLENT ✅"
        color = "lightgreen"
    elif baseline_r2 > 0.5 and baseline_points > 30:
        quality = "GOOD ✅"
        color = "lightblue" 
    elif baseline_r2 > 0.2 and baseline_points > 15:
        quality = "FAIR ⚠️"
        color = "lightyellow"
    else:
        quality = "POOR ❌"
        color = "lightcoral"
    
    # Title with filename and scan rate
    ax.set_title(f'{quality} Baseline Detection ({scan_rate})\n{filename}', 
                fontsize=14, fontweight='bold')
    
    # Add info box with background color
    info_text = f'Baseline R²: {baseline_r2:.3f}\nBaseline Points: {baseline_points}\nForward: {len(baseline_result["info"].get("forward_segment", []))} segments\nReverse: {len(baseline_result["info"].get("reverse_segment", []))} segments'
    
    ax.text(0.02, 0.98, info_text, 
            transform=ax.transAxes, fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor=color, alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return {"quality": quality, "r2": baseline_r2, "points": baseline_points}

def main():
    """Main function to process limited CSV files"""
    
    print("🎯 Limited Batch Baseline Detection Visualization")
    print("=" * 50)
    
    # Find CSV files from different directories (limit to a few samples)
    test_data_path = "Test_data"
    csv_files = []
    
    # Get samples from each subdirectory
    for root, dirs, files in os.walk(test_data_path):
        for file in files:
            if file.endswith('.csv') and not file.endswith('.backup'):
                csv_files.append(os.path.join(root, file))
    
    # Limit to first 10 files for testing
    csv_files = csv_files[:10]
    
    print(f"Found {len(csv_files)} CSV files to process (limited sample)")
    
    # Process each file
    successful_plots = 0
    failed_files = []
    results = []
    
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
            quality_info = create_baseline_plot(
                file_path, voltage_data, current_data, baseline_result, plot_path
            )
            
            print(f"   ✅ Plot saved: {plot_filename}")
            print(f"   📊 Quality: {quality_info['quality']}")
            print(f"   📈 R²: {quality_info['r2']:.3f}, Points: {quality_info['points']}")
            
            results.append({
                'file': os.path.basename(file_path),
                'quality': quality_info['quality'],
                'r2': quality_info['r2'],
                'points': quality_info['points']
            })
            
            successful_plots += 1
            
        except Exception as e:
            print(f"   ❌ Plot failed: {str(e)}")
            failed_files.append((file_path, f"Plot error: {str(e)}"))
    
    # Summary
    print("\n" + "=" * 50)
    print("📈 SUMMARY")
    print(f"✅ Successful plots: {successful_plots}")
    print(f"❌ Failed files: {len(failed_files)}")
    
    if results:
        print("\n🎯 QUALITY BREAKDOWN:")
        excellent = sum(1 for r in results if "EXCELLENT" in r['quality'])
        good = sum(1 for r in results if "GOOD" in r['quality']) 
        fair = sum(1 for r in results if "FAIR" in r['quality'])
        poor = sum(1 for r in results if "POOR" in r['quality'])
        
        print(f"   🟢 EXCELLENT: {excellent}")
        print(f"   ✅ GOOD: {good}")
        print(f"   ⚠️ FAIR: {fair}")
        print(f"   ❌ POOR: {poor}")
        
        avg_r2 = np.mean([r['r2'] for r in results])
        avg_points = np.mean([r['points'] for r in results])
        print(f"\n📊 Average R²: {avg_r2:.3f}")
        print(f"📊 Average baseline points: {avg_points:.1f}")
    
    if failed_files:
        print("\n❌ Failed files:")
        for file_path, error in failed_files[:5]:  # Show first 5 failures
            print(f"   {os.path.basename(file_path)}: {error}")
        if len(failed_files) > 5:
            print(f"   ... and {len(failed_files) - 5} more")
    
    print(f"\n🎯 All plots saved in their respective directories!")

if __name__ == "__main__":
    main()