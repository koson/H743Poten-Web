#!/usr/bin/env python3
"""
Simple Baseline Visualization using Web API
==========================================

Uses web API to get baseline detection results and creates plots 
with shaded regions like the reference image.

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

def load_csv_via_api(file_path):
    """Load CSV file via web API"""
    try:
        # Convert to relative path from Test_data
        relative_path = str(file_path).replace('Test_data/', '').replace('Test_data\\', '')
        
        # Try different API endpoints
        endpoints_to_try = [
            f"/api/load_saved_file/{relative_path}",
            f"/api/load_saved_file_by_name/{os.path.basename(file_path)}"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                url = f"{API_BASE_URL}{endpoint}"
                print(f"   🔗 Trying API: {url}")
                
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success', False):
                        print(f"   ✅ API success: {len(data.get('voltage', []))} points")
                        return data, None
                    else:
                        print(f"   ⚠️ API returned: {data.get('error', 'Unknown error')}")
                else:
                    print(f"   ❌ API status: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"   ❌ API request failed: {str(e)}")
                continue
        
        return None, "All API endpoints failed"
        
    except Exception as e:
        return None, f"API call error: {str(e)}"

def detect_baseline_via_api(file_path):
    """Get baseline detection via web API"""
    try:
        # Convert to relative path from Test_data
        relative_path = str(file_path).replace('Test_data/', '').replace('Test_data\\', '')
        
        # Try baseline detection endpoint
        url = f"{API_BASE_URL}/api/cv_baseline_detection"
        
        payload = {
            'file_path': relative_path,
            'detector_type': 'v4'
        }
        
        print(f"   🧠 Baseline API: {url}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success', False):
                print(f"   ✅ Baseline detected")
                return data, None
            else:
                print(f"   ⚠️ Baseline API: {data.get('error', 'Unknown error')}")
                return None, data.get('error', 'Baseline detection failed')
        else:
            print(f"   ❌ Baseline API status: {response.status_code}")
            return None, f"API returned status {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        return None, f"Baseline API request failed: {str(e)}"
    except Exception as e:
        return None, f"Baseline API error: {str(e)}"

def create_simple_plot(csv_file_path, data_dict, baseline_result, save_path):
    """Create simple plot with shaded regions"""
    try:
        if not data_dict:
            return 0.0, 0.0, "No data available"
        
        voltage = np.array(data_dict.get('voltage', []))
        current = np.array(data_dict.get('current', []))
        
        if len(voltage) == 0 or len(current) == 0:
            return 0.0, 0.0, "Empty voltage or current data"
        
        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Get filename and scan rate
        filename = os.path.basename(csv_file_path)
        scan_rate = extract_scan_rate_from_filename(filename)
        
        # Plot CV data (blue line)
        ax.plot(voltage, current, 'b-', linewidth=2, label='CV Data', alpha=0.8, zorder=2)
        
        # Initialize R² values
        forward_r2 = 0.0
        reverse_r2 = 0.0
        
        # Add baseline if available
        if baseline_result and baseline_result.get('success', False):
            try:
                baseline_data = baseline_result.get('baseline_data', {})
                forward_baseline = np.array(baseline_data.get('forward_baseline', []))
                reverse_baseline = np.array(baseline_data.get('reverse_baseline', []))
                
                if len(forward_baseline) > 0 and len(reverse_baseline) > 0:
                    # Combine baselines
                    full_baseline = np.concatenate([forward_baseline, reverse_baseline])
                    
                    if len(full_baseline) == len(voltage):
                        # Plot baseline (green line)
                        ax.plot(voltage, full_baseline, 'g-', linewidth=3, label='Baseline', zorder=3)
                        
                        # Get R² values
                        stats_data = baseline_result.get('statistics', {})
                        forward_stats = stats_data.get('forward_segment', {})
                        reverse_stats = stats_data.get('reverse_segment', {})
                        
                        forward_r2 = forward_stats.get('r2', 0.0)
                        reverse_r2 = reverse_stats.get('r2', 0.0)
                        
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
                
            except Exception as e:
                print(f"   ⚠️ Baseline plotting issue: {str(e)}")
        
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
        if len(voltage) > 0 and len(current) > 0:
            v_min, v_max = voltage.min(), voltage.max()
            i_min, i_max = current.min(), current.max()
            voltage_padding = (v_max - v_min) * 0.05
            current_padding = (i_max - i_min) * 0.1
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
    print("🔬 Simple Baseline Visualization via Web API")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        print(f"✅ Web server is running on {API_BASE_URL}")
    except:
        print(f"❌ Web server not accessible at {API_BASE_URL}")
        print("Please start the server with: python3 auto_dev.py start")
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
    
    # Process first 3 files for testing
    test_files = csv_files[:3]
    print(f"🧪 Testing with {len(test_files)} files...")
    
    successful_plots = 0
    failed_files = []
    
    for i, file_path in enumerate(test_files):
        relative_path = file_path.relative_to(test_data_path)
        print(f"\\n📄 Processing ({i+1}/{len(test_files)}): {relative_path}")
        
        # Load data via API
        data_dict, load_error = load_csv_via_api(str(relative_path))
        
        if load_error:
            print(f"   ❌ Load failed: {load_error}")
            failed_files.append((str(file_path), load_error))
            continue
        
        # Try baseline detection
        baseline_result, baseline_error = detect_baseline_via_api(str(relative_path))
        
        if baseline_error:
            print(f"   ⚠️ Baseline detection: {baseline_error}")
            # Continue without baseline
        
        # Create plot
        base_name = file_path.stem
        plot_filename = f"{base_name}_simple_baseline_plot.png"
        plot_path = file_path.parent / plot_filename
        
        forward_r2, reverse_r2, plot_error = create_simple_plot(
            str(file_path), data_dict, baseline_result, str(plot_path)
        )
        
        if plot_error:
            print(f"   ❌ Plot failed: {plot_error}")
            failed_files.append((str(file_path), plot_error))
        else:
            print(f"   ✅ Plot saved: {plot_filename}")
            print(f"   📊 R² - Forward: {forward_r2:.3f}, Reverse: {reverse_r2:.3f}")
            successful_plots += 1
    
    # Summary
    print("\\n" + "=" * 50)
    print(f"✅ Successful plots: {successful_plots}")
    print(f"❌ Failed files: {len(failed_files)}")
    
    if failed_files:
        print("\\n❌ Failed files:")
        for file_path, error in failed_files:
            print(f"   {Path(file_path).name}: {error}")
    
    print(f"\\n🎯 Check Test_data folders for '*_simple_baseline_plot.png' files")

if __name__ == "__main__":
    main()
