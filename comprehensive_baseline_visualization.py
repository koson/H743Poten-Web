#!/usr/bin/env python3
"""
Comprehensive Baseline Detection Visualization
==============================================

Creates plots for all CSV files in Test_data folder similar to the reference image:
- Shows CV data with baseline overlay
- Highlights forward and reverse segments
- Displays filename as title
- Shows R² values for both segments
- Saves plots in same directory as source files

Author: AI Assistant
Date: August 26, 2025
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
import re
import sys
from pathlib import Path

warnings.filterwarnings('ignore')

# Add current directory to path for imports
sys.path.append('.')

# Import our baseline detection algorithms
from baseline_detector_v4 import cv_baseline_detector_v4
from baseline_detector_voltage_windows import voltage_window_baseline_detector

# Configure matplotlib for better plots
plt.style.use('default')
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['legend.fontsize'] = 9

# Configure logging to reduce noise
logging.basicConfig(level=logging.ERROR)

def extract_scan_rate_from_filename(filename):
    """Extract scan rate from filename"""
    try:
        # Look for patterns like "20mVpS", "100mVpS", etc.
        match = re.search(r'(\d+)mVpS', filename, re.IGNORECASE)
        if match:
            return f"{match.group(1)}mVpS"
        
        # Alternative pattern
        match = re.search(r'(\d+)mvps', filename, re.IGNORECASE)
        if match:
            return f"{match.group(1)}mVpS"
            
        return "Unknown"
    except:
        return "Unknown"

def detect_unit_and_convert_current(current_data, current_column_name):
    """Detect current unit from column name and convert to µA"""
    current_unit_lower = current_column_name.lower().strip()
    
    # Determine scaling factor
    current_scale = 1.0
    unit_detected = "µA"
    
    if 'ma' in current_unit_lower or 'milliamp' in current_unit_lower:
        current_scale = 1e3  # mA to µA
        unit_detected = "mA"
    elif 'na' in current_unit_lower or 'nanoamp' in current_unit_lower:
        current_scale = 1e-3  # nA to µA  
        unit_detected = "nA"
    elif current_unit_lower == 'a' or 'ampere' in current_unit_lower:
        current_scale = 1e6  # A to µA
        unit_detected = "A"
    elif 'ua' in current_unit_lower or 'µa' in current_unit_lower or 'microamp' in current_unit_lower:
        current_scale = 1.0  # Already in µA
        unit_detected = "µA"
    
    return current_data * current_scale, unit_detected

def load_and_process_csv(file_path):
    """Load CSV file and detect baseline using our algorithm"""
    try:
        # Read CSV file with different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252']
        df = None
        
        for encoding in encodings:
            try:
                # Try reading normally first
                df = pd.read_csv(file_path, encoding=encoding)
                
                # Check if this is the special format with header line
                if len(df.columns) == 1 and 'FileName:' in df.columns[0]:
                    # Skip first row and re-read
                    df = pd.read_csv(file_path, encoding=encoding, skiprows=1)
                
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            return None, "Failed to read file with any encoding"
        
        # Find voltage and current columns (case-insensitive search)
        headers = [h.strip() for h in df.columns]
        headers_lower = [h.lower() for h in headers]
        
        voltage_idx = -1
        current_idx = -1
        
        # More comprehensive column detection
        for i, header in enumerate(headers_lower):
            if any(keyword in header for keyword in ['voltage', 'potential', 'v(v)', 'v [v]', 'volt']):
                if voltage_idx == -1:  # Take first match
                    voltage_idx = i
            elif any(keyword in header for keyword in ['current', 'i(a)', 'i [a]', 'i(ua)', 'i [ua]', 'i(µa)', 'amp']):
                if current_idx == -1:  # Take first match
                    current_idx = i
        
        if voltage_idx == -1 or current_idx == -1:
            return None, f"Could not find voltage/current columns. Found columns: {headers}"
        
        # Extract data
        voltage_data = df.iloc[:, voltage_idx].values
        current_data = df.iloc[:, current_idx].values
        
        # Convert current to µA
        current_column_name = headers[current_idx]
        current_data, detected_unit = detect_unit_and_convert_current(current_data, current_column_name)
        
        # Clean data - remove NaN, inf, and zero variance
        valid_mask = (
            ~np.isnan(voltage_data) & ~np.isnan(current_data) &
            ~np.isinf(voltage_data) & ~np.isinf(current_data) &
            np.isfinite(voltage_data) & np.isfinite(current_data)
        )
        
        voltage_data = voltage_data[valid_mask]
        current_data = current_data[valid_mask]
        
        if len(voltage_data) < 20:
            return None, f"Not enough valid data points ({len(voltage_data)})"
        
        # Check for reasonable voltage range (CV should span at least 0.3V)
        voltage_range = np.max(voltage_data) - np.min(voltage_data)
        if voltage_range < 0.1:
            return None, f"Voltage range too small ({voltage_range:.3f}V)"
        
        # Run baseline detection using our v4 algorithm
        try:
            forward_baseline, reverse_baseline, baseline_info = cv_baseline_detector_v4(
                voltage_data, current_data, peak_regions=None
            )
            
            if baseline_info.get('error'):
                return None, f"Baseline detection failed: {baseline_info['error']}"
            
            return {
                'voltage': voltage_data,
                'current': current_data,
                'forward_baseline': forward_baseline,
                'reverse_baseline': reverse_baseline,
                'baseline_info': baseline_info,
                'detected_unit': detected_unit,
                'voltage_column': headers[voltage_idx],
                'current_column': headers[current_idx]
            }, None
            
        except Exception as e:
            return None, f"Baseline detection error: {str(e)}"
        
    except Exception as e:
        return None, f"File processing error: {str(e)}"

def calculate_r2_for_segments(voltage_segment, current_segment):
    """Calculate R² for a baseline segment"""
    if len(voltage_segment) < 3:
        return 0.0
    
    try:
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(voltage_segment, current_segment)
        return r_value ** 2
    except:
        # Fallback: simple correlation coefficient squared
        try:
            correlation_matrix = np.corrcoef(voltage_segment, current_segment)
            correlation = correlation_matrix[0, 1]
            return correlation ** 2 if not np.isnan(correlation) else 0.0
        except:
            return 0.0

def create_baseline_visualization(file_path, data_dict, save_path):
    """Create a baseline detection visualization similar to reference image"""
    
    # Extract data
    voltage = data_dict['voltage']
    current = data_dict['current']
    forward_baseline = data_dict['forward_baseline']
    reverse_baseline = data_dict['reverse_baseline']
    baseline_info = data_dict['baseline_info']
    detected_unit = data_dict['detected_unit']
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Get filename and scan rate for title
    filename = os.path.basename(file_path)
    scan_rate = extract_scan_rate_from_filename(filename)
    
    # Plot CV data
    ax.plot(voltage, current, 'b-', linewidth=2, label='CV Data', alpha=0.7, zorder=1)
    
    # Create combined baseline for plotting
    full_baseline = np.concatenate([forward_baseline, reverse_baseline])
    ax.plot(voltage, full_baseline, 'g-', linewidth=3, label='Baseline', alpha=0.9, zorder=3)
    
    # Calculate R² values
    n_total = len(voltage)
    mid_point = n_total // 2
    
    # Forward segment R²
    forward_r2 = 0.0
    if len(forward_baseline) > 2:
        forward_voltage = voltage[:len(forward_baseline)]
        forward_r2 = calculate_r2_for_segments(forward_voltage, forward_baseline)
    
    # Reverse segment R²
    reverse_r2 = 0.0
    if len(reverse_baseline) > 2:
        reverse_voltage = voltage[len(forward_baseline):]
        reverse_r2 = calculate_r2_for_segments(reverse_voltage, reverse_baseline)
    
    # Add colored background regions
    v_min, v_max = voltage.min(), voltage.max()
    i_min, i_max = current.min(), current.max()
    i_range = i_max - i_min
    
    # Forward segment highlight (light green)
    if len(forward_baseline) > 0:
        forward_v_end = voltage[len(forward_baseline)-1] if len(forward_baseline) < len(voltage) else v_max
        rect_forward = Rectangle((v_min, i_min - 0.1*i_range), forward_v_end - v_min, i_range * 1.2, 
                               facecolor='lightgreen', alpha=0.3, 
                               label=f'Forward Seg ({len(forward_baseline)} pts)', zorder=0)
        ax.add_patch(rect_forward)
    
    # Reverse segment highlight (light orange)
    if len(reverse_baseline) > 0:
        reverse_v_start = voltage[len(forward_baseline)] if len(forward_baseline) < len(voltage) else v_min
        rect_reverse = Rectangle((reverse_v_start, i_min - 0.1*i_range), v_max - reverse_v_start, i_range * 1.2,
                               facecolor='orange', alpha=0.3,
                               label=f'Reverse Seg ({len(reverse_baseline)} pts)', zorder=0)
        ax.add_patch(rect_reverse)
    
    # Formatting
    ax.set_xlabel('Voltage (V)', fontsize=12, fontweight='bold')
    ax.set_ylabel(f'Current ({detected_unit})', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, linewidth=0.5)
    ax.legend(fontsize=10, loc='upper right')
    
    # Title with detection status and scan rate
    detection_status = "✅ Good Baseline Detection" if (forward_r2 > 0.7 or reverse_r2 > 0.7) else "⚠️ Baseline Detection"
    title = f'{detection_status} ({scan_rate})\n{filename}'
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
    
    # Add R² information as text box
    info_text = f'Forward R²: {forward_r2:.3f}\nReverse R²: {reverse_r2:.3f}'
    if baseline_info.get('forward_segments_count', 0) > 0:
        info_text += f'\nFwd segments: {baseline_info["forward_segments_count"]}'
    if baseline_info.get('reverse_segments_count', 0) > 0:
        info_text += f'\nRev segments: {baseline_info["reverse_segments_count"]}'
    
    ax.text(0.02, 0.98, info_text, 
            transform=ax.transAxes, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='gray'),
            zorder=5)
    
    # Add method info
    method_info = f'Method: {baseline_info.get("method", "v4")}'
    ax.text(0.98, 0.02, method_info, 
            transform=ax.transAxes, fontsize=9, verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7),
            zorder=5)
    
    # Optimize axis limits
    voltage_padding = (v_max - v_min) * 0.05
    current_padding = i_range * 0.1
    ax.set_xlim(v_min - voltage_padding, v_max + voltage_padding)
    ax.set_ylim(i_min - current_padding, i_max + current_padding)
    
    # Save plot
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return forward_r2, reverse_r2

def main():
    """Main function to process all CSV files in Test_data"""
    
    print("🎯 Comprehensive Baseline Detection Visualization")
    print("=" * 60)
    print("📁 Processing all CSV files in Test_data folder...")
    
    # Find all CSV files (excluding backups)
    test_data_path = Path("Test_data")
    if not test_data_path.exists():
        print(f"❌ Test_data directory not found: {test_data_path.absolute()}")
        return
    
    csv_files = []
    for csv_file in test_data_path.rglob("*.csv"):
        if not str(csv_file.name).endswith('.backup'):
            csv_files.append(csv_file)
    
    csv_files.sort()  # Sort for consistent processing order
    
    print(f"📊 Found {len(csv_files)} CSV files to process")
    if len(csv_files) == 0:
        print("❌ No CSV files found in Test_data directory")
        return
    
    # Process each file
    successful_plots = 0
    failed_files = []
    r2_stats = {'forward': [], 'reverse': []}
    
    for i, file_path in enumerate(csv_files):
        relative_path = file_path.relative_to(test_data_path)
        print(f"\n📄 Processing ({i+1}/{len(csv_files)}): {relative_path}")
        
        # Load and process data
        result, error = load_and_process_csv(str(file_path))
        
        if error:
            print(f"   ❌ Failed: {error}")
            failed_files.append((str(file_path), error))
            continue
        
        # Create plot filename
        base_name = file_path.stem  # filename without extension
        plot_filename = f"{base_name}_baseline_plot.png"
        plot_path = file_path.parent / plot_filename
        
        try:
            # Create and save plot
            forward_r2, reverse_r2 = create_baseline_visualization(
                str(file_path), result, str(plot_path)
            )
            
            print(f"   ✅ Plot saved: {plot_filename}")
            print(f"   📊 R² - Forward: {forward_r2:.3f}, Reverse: {reverse_r2:.3f}")
            
            # Collect statistics
            r2_stats['forward'].append(forward_r2)
            r2_stats['reverse'].append(reverse_r2)
            successful_plots += 1
            
        except Exception as e:
            print(f"   ❌ Plot creation failed: {str(e)}")
            failed_files.append((str(file_path), f"Plot error: {str(e)}"))
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("📈 PROCESSING SUMMARY")
    print(f"✅ Successful plots: {successful_plots}")
    print(f"❌ Failed files: {len(failed_files)}")
    
    if r2_stats['forward']:
        forward_r2_array = np.array(r2_stats['forward'])
        reverse_r2_array = np.array(r2_stats['reverse'])
        
        print(f"\n📊 R² STATISTICS:")
        print(f"Forward R² - Mean: {np.mean(forward_r2_array):.3f}, Std: {np.std(forward_r2_array):.3f}")
        print(f"             Min: {np.min(forward_r2_array):.3f}, Max: {np.max(forward_r2_array):.3f}")
        print(f"Reverse R² - Mean: {np.mean(reverse_r2_array):.3f}, Std: {np.std(reverse_r2_array):.3f}")
        print(f"             Min: {np.min(reverse_r2_array):.3f}, Max: {np.max(reverse_r2_array):.3f}")
        
        # Quality assessment
        good_forward = np.sum(forward_r2_array > 0.8)
        good_reverse = np.sum(reverse_r2_array > 0.8)
        
        print(f"\n🎯 QUALITY ASSESSMENT:")
        print(f"High quality forward baselines (R² > 0.8): {good_forward}/{len(forward_r2_array)} ({100*good_forward/len(forward_r2_array):.1f}%)")
        print(f"High quality reverse baselines (R² > 0.8): {good_reverse}/{len(reverse_r2_array)} ({100*good_reverse/len(reverse_r2_array):.1f}%)")
    
    if failed_files:
        print(f"\n❌ FAILED FILES ({len(failed_files)}):")
        for file_path, error in failed_files[:10]:  # Show first 10 failures
            relative_path = Path(file_path).relative_to(test_data_path)
            print(f"   {relative_path}: {error}")
        if len(failed_files) > 10:
            print(f"   ... and {len(failed_files) - 10} more failures")
    
    print(f"\n🎯 All plots saved in their respective directories!")
    print(f"📁 Look for '*_baseline_plot.png' files next to your CSV files")

if __name__ == "__main__":
    main()
