#!/usr/bin/env python3
"""
Web API Baseline Visualization
=============================

Uses the /get-peaks API endpoint to get baseline detection results 
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
import requests
import json
from pathlib import Path
import time
import warnings
warnings.filterwarnings('ignore')

# Configure matplotlib
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['font.size'] = 10

# Web API configuration
API_BASE_URL = "http://127.0.0.1:8084"

def extract_scan_rate_from_filename(filename):
    """Extract scan rate from filename"""
    try:
        match = re.search(r'(\d+)mVpS', filename, re.IGNORECASE)
        if match:
            return f"{match.group(1)}mVpS"
        return "Unknown"
    except:
        return "Unknown"

def load_csv_data(file_path):
    """Load CSV file data locally (same format as web)"""
    try:
        # Read file lines
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            return None, "File too short"
        
        # Handle FileName header
        header_line_idx = 0
        data_start_idx = 1
        
        if lines[0].strip().startswith('FileName:'):
            header_line_idx = 1
            data_start_idx = 2
        
        # Parse headers
        headers = [h.strip().lower() for h in lines[header_line_idx].strip().split(',')]
        
        # Find voltage and current columns
        voltage_idx = -1
        current_idx = -1
        
        for i, header in enumerate(headers):
            if header in ['v', 'voltage'] or 'volt' in header:
                voltage_idx = i
            elif header in ['a', 'ua', 'ma', 'na', 'current'] or 'amp' in header:
                current_idx = i
        
        if voltage_idx == -1 or current_idx == -1:
            return None, f'Could not find voltage/current columns: {headers}'
        
        # Current unit scaling
        current_unit = headers[current_idx]
        current_scale = 1.0
        
        current_unit_lower = current_unit.lower()
        if current_unit_lower == 'ma':
            current_scale = 1e3  # mA to µA
        elif current_unit_lower == 'na':
            current_scale = 1e-3  # nA to µA
        elif current_unit_lower == 'a':
            current_scale = 1e6  # A to µA
        elif current_unit_lower in ['ua', 'µa']:
            current_scale = 1.0  # µA - keep as is
        
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
        
        if len(voltage) == 0:
            return None, "No valid data points"
        
        return {
            'voltage': voltage,
            'current': current,
            'points': len(voltage)
        }, None
        
    except Exception as e:
        return None, f"CSV load error: {str(e)}"

def get_baseline_via_api(voltage, current, method='prominence'):
    """Get baseline detection via web API"""
    try:
        url = f"{API_BASE_URL}/get-peaks/{method}"
        
        payload = {
            'voltage': voltage,
            'current': current
        }
        
        print(f"   🧠 API: {url}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success', False):
                baseline_data = data.get('baseline', {})
                peaks = data.get('peaks', [])
                
                print(f"   ✅ API success: {len(peaks)} peaks, baseline keys: {list(baseline_data.keys())}")
                
                return {
                    'success': True,
                    'baseline': baseline_data,
                    'peaks': peaks
                }, None
            else:
                error_msg = data.get('error', 'API returned success=False')
                print(f"   ❌ API error: {error_msg}")
                return None, error_msg
        else:
            print(f"   ❌ API status: {response.status_code}")
            return None, f"API returned status {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        return None, f"API request failed: {str(e)}"
    except Exception as e:
        return None, f"API error: {str(e)}"

def create_api_baseline_plot(csv_file_path, data_dict, api_result, save_path):
    """Create baseline plot with API data and shaded regions"""
    try:
        voltage = np.array(data_dict['voltage'])
        current = np.array(data_dict['current'])
        
        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Get filename and scan rate
        filename = os.path.basename(csv_file_path)
        scan_rate = extract_scan_rate_from_filename(filename)
        
        # Plot CV data (blue line)
        ax.plot(voltage, current, 'b-', linewidth=2, label='CV Data', alpha=0.8, zorder=2)
        
        # Initialize values
        forward_r2 = 0.0
        reverse_r2 = 0.0
        
        # Add baseline if available
        if api_result and api_result.get('success', False):
            baseline_data = api_result.get('baseline', {})
            
            if baseline_data:
                print(f"   📊 Baseline data available: {list(baseline_data.keys())}")
                
                # Try to get baseline arrays
                forward_baseline = baseline_data.get('forward_baseline', [])
                reverse_baseline = baseline_data.get('reverse_baseline', [])
                
                if forward_baseline and reverse_baseline:
                    forward_baseline = np.array(forward_baseline)
                    reverse_baseline = np.array(reverse_baseline)
                    
                    # Combine baselines
                    full_baseline = np.concatenate([forward_baseline, reverse_baseline])
                    
                    if len(full_baseline) == len(voltage):
                        # Plot baseline (green line)
                        ax.plot(voltage, full_baseline, 'g-', linewidth=3, label='Baseline', zorder=3)
                        
                        # Get R² values
                        metadata = baseline_data.get('metadata', {})
                        forward_segment = metadata.get('forward_segment', {})
                        reverse_segment = metadata.get('reverse_segment', {})
                        
                        forward_r2 = forward_segment.get('r2', 0.0)
                        reverse_r2 = reverse_segment.get('r2', 0.0)
                        
                        print(f"   📈 R² values - Forward: {forward_r2:.3f}, Reverse: {reverse_r2:.3f}")
                        
                        # Add shaded regions
                        v_min, v_max = voltage.min(), voltage.max()
                        i_min, i_max = current.min(), current.max()
                        i_range = i_max - i_min
                        
                        # Forward segment (light green)
                        mid_point = len(forward_baseline)
                        if mid_point < len(voltage):
                            forward_v_end = voltage[mid_point-1]
                            rect_forward = Rectangle(
                                (v_min, i_min - 0.1*i_range), 
                                forward_v_end - v_min, 
                                i_range * 1.2,
                                facecolor='lightgreen', 
                                alpha=0.3, 
                                label=f'Forward ({len(forward_baseline)} pts)',
                                zorder=1
                            )
                            ax.add_patch(rect_forward)
                        
                        # Reverse segment (light orange)
                        if mid_point < len(voltage):
                            reverse_v_start = voltage[mid_point]
                            rect_reverse = Rectangle(
                                (reverse_v_start, i_min - 0.1*i_range),
                                v_max - reverse_v_start,
                                i_range * 1.2,
                                facecolor='orange',
                                alpha=0.3,
                                label=f'Reverse ({len(reverse_baseline)} pts)',
                                zorder=1
                            )
                            ax.add_patch(rect_reverse)
                    else:
                        print(f"   ⚠️ Baseline length mismatch: {len(full_baseline)} vs {len(voltage)}")
                else:
                    print(f"   ⚠️ No baseline arrays found")
            else:
                print(f"   ⚠️ No baseline data in API response")
        
        # Formatting
        ax.set_xlabel('Voltage (V)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Current (µA)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linewidth=0.5)
        ax.legend(fontsize=10, loc='upper right')
        
        # Title
        detection_status = "✅ Good Detection" if (forward_r2 > 0.7 or reverse_r2 > 0.7) else "⚠️ Detection"
        title = f'{detection_status} ({scan_rate})\\n{filename}'
        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
        
        # Add R² information
        r2_text = f'Forward R²: {forward_r2:.3f}\\nReverse R²: {reverse_r2:.3f}'
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
    """Main function"""
    print("🔬 Web API Baseline Visualization")
    print("=" * 40)
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        print(f"✅ Web server is running on {API_BASE_URL}")
    except:
        print(f"❌ Web server not accessible at {API_BASE_URL}")
        print("Please start with: python3 auto_dev.py start")
        return
    
    # Find CSV files
    test_data_path = Path("Test_data")
    if not test_data_path.exists():
        print(f"❌ Test_data directory not found")
        return
    
    csv_files = []
    for csv_file in test_data_path.rglob("*.csv"):
        if not str(csv_file.name).endswith('.backup'):
            csv_files.append(csv_file)
    
    csv_files.sort()
    print(f"📊 Found {len(csv_files)} CSV files")
    
    if len(csv_files) == 0:
        print("❌ No CSV files found")
        return
    
    # Process first 5 files for testing
    test_files = csv_files[:5]
    print(f"🧪 Testing with {len(test_files)} files...")
    
    successful_plots = 0
    failed_files = []
    r2_stats = {'forward': [], 'reverse': []}
    
    for i, file_path in enumerate(test_files):
        relative_path = file_path.relative_to(test_data_path)
        print(f"\\n📄 Processing ({i+1}/{len(test_files)}): {relative_path}")
        
        # Load CSV data locally
        data_dict, load_error = load_csv_data(str(file_path))
        
        if load_error:
            print(f"   ❌ Load failed: {load_error}")
            failed_files.append((str(file_path), load_error))
            continue
        
        print(f"   ✅ Data loaded: {data_dict['points']} points")
        
        # Get baseline via API
        api_result, api_error = get_baseline_via_api(
            data_dict['voltage'], 
            data_dict['current'], 
            method='prominence'
        )
        
        if api_error:
            print(f"   ⚠️ API baseline: {api_error}")
            # Continue without baseline
        
        # Create plot
        base_name = file_path.stem
        plot_filename = f"{base_name}_api_baseline_plot.png"
        plot_path = file_path.parent / plot_filename
        
        forward_r2, reverse_r2, plot_error = create_api_baseline_plot(
            str(file_path), data_dict, api_result, str(plot_path)
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
        
        # Brief pause between files
        time.sleep(0.5)
    
    # Summary
    print("\\n" + "=" * 40)
    print(f"✅ Successful plots: {successful_plots}")
    print(f"❌ Failed files: {len(failed_files)}")
    
    if r2_stats['forward']:
        forward_r2_array = np.array(r2_stats['forward'])
        reverse_r2_array = np.array(r2_stats['reverse'])
        
        print(f"\\n📊 R² STATISTICS:")
        print(f"Forward R² - Mean: {np.mean(forward_r2_array):.3f}")
        print(f"Reverse R² - Mean: {np.mean(reverse_r2_array):.3f}")
        
        good_forward = np.sum(forward_r2_array > 0.7)
        good_reverse = np.sum(reverse_r2_array > 0.7)
        
        print(f"\\n🎯 Good baselines (R² > 0.7):")
        print(f"Forward: {good_forward}/{len(forward_r2_array)}")
        print(f"Reverse: {good_reverse}/{len(reverse_r2_array)}")
    
    if failed_files:
        print(f"\\n❌ Failed files:")
        for file_path, error in failed_files[:3]:
            print(f"   {Path(file_path).name}: {error}")
    
    print(f"\\n🎯 All plots saved as '*_api_baseline_plot.png'")

if __name__ == "__main__":
    main()
