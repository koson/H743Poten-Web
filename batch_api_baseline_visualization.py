#!/usr/bin/env python3
"""
Batch Baseline Visualization Using Existing Web API
===================================================

Uses the existing web API for baseline detection instead of local algorithms.
Creates plots with shaded regions like the reference image.

Author: AI Assistant  
Date: August 26, 2025
"""

import os
import requests
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from matplotlib.patches import Rectangle
import re
from pathlib import Path
import time

# Configure matplotlib
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['font.size'] = 10

# API Configuration
API_BASE_URL = "http://127.0.0.1:8084"  # ใช้ port จาก auto_dev.py
TIMEOUT = 30  # seconds

def extract_scan_rate_from_filename(filename):
    """Extract scan rate from filename"""
    try:
        match = re.search(r'(\d+)mVpS', filename, re.IGNORECASE)
        if match:
            return f"{match.group(1)}mVpS"
        return "Unknown"
    except:
        return "Unknown"

def call_web_api_baseline_detection(csv_file_path):
    """Call the existing web API for baseline detection"""
    try:
        print(f"   🌐 Calling web API for: {os.path.basename(csv_file_path)}")
        
        # Use the correct endpoint: /api/load_saved_file/<path:file_path>
        # Convert to absolute path
        abs_path = os.path.abspath(csv_file_path)
        
        response = requests.get(
            f"{API_BASE_URL}/api/load_saved_file/{abs_path}",
            timeout=TIMEOUT
        )
        
        if response.status_code != 200:
            return None, f"API returned status {response.status_code}: {response.text[:200]}"
        
        data = response.json()
        
        if not data.get('success', False):
            return None, f"API error: {data.get('error', 'Unknown error')}"
        
        # Extract data from API response
        result_data = data.get('data', {})
        
        return {
            'voltage': result_data.get('voltage', []),
            'current': result_data.get('current', []),
            'baseline_info': result_data.get('baseline_detection', {}),
            'api_response': data
        }, None
        
    except requests.exceptions.Timeout:
        return None, "API request timeout"
    except requests.exceptions.ConnectionError:
        return None, "Could not connect to API server"
    except Exception as e:
        return None, f"API call error: {str(e)}"

def create_baseline_plot_with_api_data(csv_file_path, api_data, save_path):
    """Create baseline plot using data from web API"""
    try:
        voltage = np.array(api_data['voltage'])
        current = np.array(api_data['current'])
        baseline_info = api_data['baseline_info']
        
        if len(voltage) == 0 or len(current) == 0:
            return 0.0, 0.0, "No data received from API"
        
        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Get filename and scan rate
        filename = os.path.basename(csv_file_path)
        scan_rate = extract_scan_rate_from_filename(filename)
        
        # Plot CV data
        ax.plot(voltage, current, 'b-', linewidth=2, label='CV Data', alpha=0.8, zorder=2)
        
        # Extract baseline data from API response
        forward_baseline = []
        reverse_baseline = []
        forward_r2 = 0.0
        reverse_r2 = 0.0
        
        # Check if baseline detection was successful
        if baseline_info and baseline_info.get('detected', False):
            # Get baseline segments
            forward_segment = baseline_info.get('forward_segment', {})
            reverse_segment = baseline_info.get('reverse_segment', {})
            
            # Plot baseline if available
            if 'baseline_voltage' in baseline_info and 'baseline_current' in baseline_info:
                baseline_v = np.array(baseline_info['baseline_voltage'])
                baseline_i = np.array(baseline_info['baseline_current'])
                ax.plot(baseline_v, baseline_i, 'g-', linewidth=3, label='Baseline', zorder=3)
            
            # Get R² values
            forward_r2 = forward_segment.get('r2', 0.0) if forward_segment else 0.0
            reverse_r2 = reverse_segment.get('r2', 0.0) if reverse_segment else 0.0
            
            # Add shaded regions for baseline segments (like reference image)
            v_min, v_max = voltage.min(), voltage.max()
            i_min, i_max = current.min(), current.max()
            i_range = i_max - i_min
            
            # Forward segment (green shade)
            if forward_segment and 'voltage_start' in forward_segment and 'voltage_end' in forward_segment:
                fwd_start = forward_segment['voltage_start']
                fwd_end = forward_segment['voltage_end']
                fwd_length = forward_segment.get('length', 0)
                
                rect_forward = Rectangle(
                    (fwd_start, i_min - 0.1*i_range), 
                    fwd_end - fwd_start, 
                    i_range * 1.2,
                    facecolor='lightgreen', 
                    alpha=0.3, 
                    label=f'Forward Seg ({fwd_length} pts)',
                    zorder=1
                )
                ax.add_patch(rect_forward)
            
            # Reverse segment (orange shade)  
            if reverse_segment and 'voltage_start' in reverse_segment and 'voltage_end' in reverse_segment:
                rev_start = reverse_segment['voltage_start']
                rev_end = reverse_segment['voltage_end']
                rev_length = reverse_segment.get('length', 0)
                
                rect_reverse = Rectangle(
                    (rev_start, i_min - 0.1*i_range),
                    rev_end - rev_start,
                    i_range * 1.2,
                    facecolor='orange',
                    alpha=0.3,
                    label=f'Reverse Seg ({rev_length} pts)',
                    zorder=1
                )
                ax.add_patch(rect_reverse)
        
        else:
            # No baseline detected - still plot the data
            ax.text(0.5, 0.5, 'No Baseline Detected', 
                   transform=ax.transAxes, fontsize=14, ha='center',
                   bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        # Formatting
        ax.set_xlabel('Voltage (V)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Current (µA)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linewidth=0.5)
        ax.legend(fontsize=10, loc='upper right')
        
        # Title
        detection_status = "✅ Good Baseline Detection" if (forward_r2 > 0.7 or reverse_r2 > 0.7) else "⚠️ Baseline Detection"
        title = f'{detection_status} ({scan_rate})\\n{filename}'
        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
        
        # Add R² information
        info_text = f'Forward R²: {forward_r2:.3f}\\nReverse R²: {reverse_r2:.3f}'
        
        # Add API method info
        method = baseline_info.get('method', 'Web API') if baseline_info else 'Web API'
        info_text += f'\\nMethod: {method}'
        
        ax.text(0.02, 0.98, info_text, 
                transform=ax.transAxes, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='gray'),
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

def check_server_status():
    """Check if the web server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return True, response.status_code
    except:
        return False, None

def main():
    """Main function to process all CSV files using web API"""
    
    print("🌐 Batch Baseline Visualization Using Web API")
    print("=" * 60)
    
    # Check server status first
    print(f"🔍 Checking server status at {API_BASE_URL}...")
    server_ok, status_code = check_server_status()
    
    if not server_ok:
        print(f"❌ Cannot connect to web server at {API_BASE_URL}")
        print("   Please make sure the web server is running")
        print("   You can start it with: python3 auto_dev.py start")
        return
    
    print(f"✅ Server is running (status: {status_code})")
    
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
    
    # Process each file
    successful_plots = 0
    failed_files = []
    r2_stats = {'forward': [], 'reverse': []}
    
    # Limit to first 10 files for testing
    test_files = csv_files[:10]
    print(f"🧪 Testing with first {len(test_files)} files...")
    
    for i, file_path in enumerate(test_files):
        relative_path = file_path.relative_to(test_data_path)
        print(f"\\n📄 Processing ({i+1}/{len(test_files)}): {relative_path}")
        
        # Call web API for baseline detection
        api_data, error = call_web_api_baseline_detection(str(file_path))
        
        if error:
            print(f"   ❌ API call failed: {error}")
            failed_files.append((str(file_path), error))
            continue
        
        print(f"   ✅ API call successful")
        print(f"   📊 Data points: {len(api_data['voltage'])}")
        
        # Create plot
        base_name = file_path.stem
        plot_filename = f"{base_name}_api_baseline_plot.png"
        plot_path = file_path.parent / plot_filename
        
        forward_r2, reverse_r2, plot_error = create_baseline_plot_with_api_data(
            str(file_path), api_data, str(plot_path)
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
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.5)
    
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
        print(f"Good forward baselines (R² > 0.7): {good_forward}/{len(forward_r2_array)}")
        print(f"Good reverse baselines (R² > 0.7): {good_reverse}/{len(reverse_r2_array)}")
    
    if failed_files:
        print(f"\\n❌ FAILED FILES:")
        for file_path, error in failed_files[:5]:
            print(f"   {Path(file_path).name}: {error}")
        if len(failed_files) > 5:
            print(f"   ... and {len(failed_files) - 5} more")
    
    print(f"\\n🎯 All plots saved as '*_api_baseline_plot.png'")
    print(f"📁 Check the Test_data folders for the generated plots")

if __name__ == "__main__":
    main()
