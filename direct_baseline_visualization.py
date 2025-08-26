#!/usr/bin/env python3
"""
Batch Baseline Visualization - Direct Algorithm Usage
====================================================

Uses the existing baseline detection algorithms directly (same as web) 
and creates plots with shaded regions like the reference image.

Author: AI Assistant  
Date: August 26, 2025
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from matplotlib.patches import Rectangle
import re
from pathlib import Path
import time
import warnings
warnings.filterwarnings('ignore')

# Import the baseline detection algorithms (same as web)
try:
    from baseline_detector_v4 import cv_baseline_detector_v4
    BASELINE_V4_AVAILABLE = True
    print("✅ Using baseline_detector_v4 (same as web)")
except ImportError:
    BASELINE_V4_AVAILABLE = False
    print("❌ baseline_detector_v4 not available")

# Configure matplotlib
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['font.size'] = 10

def extract_scan_rate_from_filename(filename):
    """Extract scan rate from filename"""
    try:
        match = re.search(r'(\d+)mVpS', filename, re.IGNORECASE)
        if match:
            return f"{match.group(1)}mVpS"
        return "Unknown"
    except:
        return "Unknown"

def load_csv_file_direct(file_path):
    """Load CSV file directly (same logic as web API)"""
    try:
        # Read file lines
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            return None, "File too short"
        
        # Handle instrument file format (same as web)
        header_line_idx = 0
        data_start_idx = 1
        
        if lines[0].strip().startswith('FileName:'):
            header_line_idx = 1
            data_start_idx = 2
        
        # Parse headers
        headers = [h.strip().lower() for h in lines[header_line_idx].strip().split(',')]
        
        # Find voltage and current columns (same logic as web)
        voltage_idx = -1
        current_idx = -1
        
        for i, header in enumerate(headers):
            if header in ['v', 'voltage'] or 'volt' in header or 'potential' in header:
                voltage_idx = i
            elif header in ['a', 'ua', 'ma', 'na', 'current'] or 'amp' in header or 'curr' in header:
                current_idx = i
        
        if voltage_idx == -1 or current_idx == -1:
            return None, f'Could not find voltage or current columns in headers: {headers}'
        
        # Determine current scaling (same logic as web)
        current_unit = headers[current_idx]
        current_scale = 1.0
        
        current_unit_lower = current_unit.lower()
        if current_unit_lower == 'ma':
            current_scale = 1e3  # milliAmps to microAmps
        elif current_unit_lower == 'na':
            current_scale = 1e-3  # nanoAmps to microAmps
        elif current_unit_lower == 'a':
            current_scale = 1e6  # Amperes to microAmps
        elif current_unit_lower in ['ua', 'µa']:
            current_scale = 1.0  # microAmps - keep as is
        
        # Parse data
        voltage = []
        current = []
        
        for i in range(data_start_idx, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
                
            values = line.split(',')
            if len(values) > max(voltage_idx, current_idx):
                try:
                    v = float(values[voltage_idx])
                    c = float(values[current_idx]) * current_scale
                    voltage.append(v)
                    current.append(c)
                except ValueError:
                    continue
        
        if len(voltage) == 0 or len(current) == 0:
            return None, "No valid data points found"
        
        return {
            'voltage': np.array(voltage),
            'current': np.array(current),
            'current_unit': current_unit,
            'current_scale': current_scale,
            'points': len(voltage)
        }, None
        
    except Exception as e:
        return None, f"Error loading file: {str(e)}"

def detect_baseline_direct(voltage, current):
    """Run baseline detection using the same algorithm as web"""
    try:
        if not BASELINE_V4_AVAILABLE:
            return None, "Baseline detector v4 not available"
        
        # Use cv_baseline_detector_v4 (same as web)
        forward_baseline, reverse_baseline, info = cv_baseline_detector_v4(voltage, current)
        
        return {
            'forward_baseline': forward_baseline,
            'reverse_baseline': reverse_baseline,
            'info': info,
            'detected': True
        }, None
        
    except Exception as e:
        return None, f"Baseline detection error: {str(e)}"

def create_baseline_plot_with_shading(csv_file_path, data_dict, baseline_result, save_path):
    """Create baseline plot with shaded regions like reference image"""
    try:
        voltage = data_dict['voltage']
        current = data_dict['current']
        
        # Create figure (same size as reference)
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Get filename and scan rate
        filename = os.path.basename(csv_file_path)
        scan_rate = extract_scan_rate_from_filename(filename)
        
        # Plot CV data (blue line like reference)
        ax.plot(voltage, current, 'b-', linewidth=2, label='CV Data', alpha=0.8, zorder=2)
        
        # Initialize R² values
        forward_r2 = 0.0
        reverse_r2 = 0.0
        
        if baseline_result and baseline_result.get('detected', False):
            forward_baseline = baseline_result['forward_baseline']
            reverse_baseline = baseline_result['reverse_baseline']
            info = baseline_result['info']
            
            # Create combined baseline
            full_baseline = np.concatenate([forward_baseline, reverse_baseline])
            
            # Plot baseline (green line like reference)
            ax.plot(voltage, full_baseline, 'g-', linewidth=3, label='Baseline', zorder=3)
            
            # Calculate R² values from baseline info
            forward_segment = info.get('forward_segment')
            reverse_segment = info.get('reverse_segment')
            
            if forward_segment and 'r2' in forward_segment:
                forward_r2 = forward_segment['r2']
            if reverse_segment and 'r2' in reverse_segment:
                reverse_r2 = reverse_segment['r2']
            
            # Add shaded regions (like reference image)
            v_min, v_max = voltage.min(), voltage.max()
            i_min, i_max = current.min(), current.max()
            i_range = i_max - i_min
            
            # Forward segment shading (light green like reference)
            if forward_segment and len(forward_baseline) > 0:
                mid_point = len(forward_baseline)
                forward_v_end = voltage[mid_point-1] if mid_point < len(voltage) else voltage[-1]
                
                rect_forward = Rectangle(
                    (v_min, i_min - 0.1*i_range), 
                    forward_v_end - v_min, 
                    i_range * 1.2,
                    facecolor='lightgreen', 
                    alpha=0.3, 
                    label=f'Forward Seg ({len(forward_baseline)} pts)',
                    zorder=1
                )
                ax.add_patch(rect_forward)
            
            # Reverse segment shading (light orange like reference)
            if reverse_segment and len(reverse_baseline) > 0:
                mid_point = len(forward_baseline)
                reverse_v_start = voltage[mid_point] if mid_point < len(voltage) else voltage[0]
                
                rect_reverse = Rectangle(
                    (reverse_v_start, i_min - 0.1*i_range),
                    v_max - reverse_v_start,
                    i_range * 1.2,
                    facecolor='orange',
                    alpha=0.3,
                    label=f'Reverse Seg ({len(reverse_baseline)} pts)',
                    zorder=1
                )
                ax.add_patch(rect_reverse)
        
        # Formatting (like reference image)
        ax.set_xlabel('Voltage (V)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Current (µA)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linewidth=0.5)
        ax.legend(fontsize=10, loc='upper right')
        
        # Title (like reference image)
        detection_status = "✅ Good Baseline Detection" if (forward_r2 > 0.7 or reverse_r2 > 0.7) else "⚠️ Baseline Detection"
        title = f'{detection_status} ({scan_rate})\\n{filename}'
        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
        
        # Add R² information below title (like reference image)
        r2_text = f'Forward R²: {forward_r2:.3f}\\nReverse R²: {reverse_r2:.3f}'
        
        # Position text box at bottom of plot (like reference)
        ax.text(0.5, 0.02, r2_text, 
                transform=ax.transAxes, fontsize=11, 
                verticalalignment='bottom', horizontalalignment='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9, edgecolor='gray'),
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
        
        return forward_r2, reverse_r2, None
        
    except Exception as e:
        return 0.0, 0.0, f"Plot creation error: {str(e)}"

def main():
    """Main function to process CSV files with direct algorithm usage"""
    
    print("🔬 Batch Baseline Visualization - Direct Algorithm Usage")
    print("=" * 60)
    
    if not BASELINE_V4_AVAILABLE:
        print("❌ Baseline detection algorithm not available")
        return
    
    # Find CSV files
    test_data_path = Path("Test_data")
    if not test_data_path.exists():
        print(f"❌ Test_data directory not found: {test_data_path.absolute()}")
        return
    
    csv_files = []
    for csv_file in test_data_path.rglob("*.csv"):
        if not str(csv_file.name).endswith('.backup'):
            csv_files.append(csv_file)
    
    csv_files.sort()
    
    print(f"📊 Found {len(csv_files)} CSV files to process")
    
    if len(csv_files) == 0:
        print("❌ No CSV files found")
        return
    
    # Process files (test with first 15)
    successful_plots = 0
    failed_files = []
    r2_stats = {'forward': [], 'reverse': []}
    
    test_files = csv_files[:15]  # Process 15 files for testing
    print(f"🧪 Processing {len(test_files)} files...")
    
    for i, file_path in enumerate(test_files):
        relative_path = file_path.relative_to(test_data_path)
        print(f"\\n📄 Processing ({i+1}/{len(test_files)}): {relative_path}")
        
        # Load CSV data directly
        data_dict, error = load_csv_file_direct(str(file_path))
        
        if error:
            print(f"   ❌ Load failed: {error}")
            failed_files.append((str(file_path), error))
            continue
        
        print(f"   ✅ Data loaded: {data_dict['points']} points")
        print(f"   📊 Voltage: {data_dict['voltage'].min():.3f} to {data_dict['voltage'].max():.3f} V")
        print(f"   ⚡ Current: {data_dict['current'].min():.3e} to {data_dict['current'].max():.3e} µA")
        
        # Run baseline detection
        baseline_result, baseline_error = detect_baseline_direct(
            data_dict['voltage'], data_dict['current']
        )
        
        if baseline_error:
            print(f"   ⚠️ Baseline detection issue: {baseline_error}")
            # Still create plot without baseline
            baseline_result = None
        
        # Create plot
        base_name = file_path.stem
        plot_filename = f"{base_name}_direct_baseline_plot.png"
        plot_path = file_path.parent / plot_filename
        
        forward_r2, reverse_r2, plot_error = create_baseline_plot_with_shading(
            str(file_path), data_dict, baseline_result, str(plot_path)
        )
        
        if plot_error:
            print(f"   ❌ Plot failed: {plot_error}")
            failed_files.append((str(file_path), plot_error))
        else:
            print(f"   ✅ Plot saved: {plot_filename}")
            print(f"   📊 R² - Forward: {forward_r2:.3f}, Reverse: {reverse_r2:.3f}")
            
            r2_stats['forward'].append(forward_r2)
            r2_stats['reverse'].append(reverse_r2)
            successful_plots += 1
    
    # Summary
    print("\\n" + "=" * 60)
    print("📈 PROCESSING SUMMARY")
    print(f"✅ Successful plots: {successful_plots}")
    print(f"❌ Failed files: {len(failed_files)}")
    
    if r2_stats['forward']:
        forward_r2_array = np.array(r2_stats['forward'])
        reverse_r2_array = np.array(r2_stats['reverse'])
        
        print(f"\\n📊 R² STATISTICS:")
        print(f"Forward R² - Mean: {np.mean(forward_r2_array):.3f}, Max: {np.max(forward_r2_array):.3f}")
        print(f"Reverse R² - Mean: {np.mean(reverse_r2_array):.3f}, Max: {np.max(reverse_r2_array):.3f}")
        
        good_forward = np.sum(forward_r2_array > 0.7)
        good_reverse = np.sum(reverse_r2_array > 0.7)
        
        print(f"\\n🎯 QUALITY ASSESSMENT:")
        print(f"Good forward baselines (R² > 0.7): {good_forward}/{len(forward_r2_array)} ({100*good_forward/len(forward_r2_array):.1f}%)")
        print(f"Good reverse baselines (R² > 0.7): {good_reverse}/{len(reverse_r2_array)} ({100*good_reverse/len(reverse_r2_array):.1f}%)")
    
    if failed_files:
        print(f"\\n❌ FAILED FILES:")
        for file_path, error in failed_files[:5]:
            print(f"   {Path(file_path).name}: {error}")
        if len(failed_files) > 5:
            print(f"   ... and {len(failed_files) - 5} more")
    
    print(f"\\n🎯 All plots saved as '*_direct_baseline_plot.png'")
    print(f"📁 Check the Test_data folders for the generated plots")
    print(f"🔬 Uses the same baseline detection algorithm as the web interface")

if __name__ == "__main__":
    main()
