#!/usr/bin/env python3
"""
Fixed batch baseline detection with proper visualization
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

def load_and_process_csv(file_path):
    """Load CSV file and process with our existing logic"""
    try:
        # Read CSV file - skip first row if it contains filename
        first_line = pd.read_csv(file_path, nrows=1, header=None, encoding='utf-8')
        if 'FileName:' in str(first_line.iloc[0, 0]):
            df = pd.read_csv(file_path, skiprows=1, encoding='utf-8')
        else:
            df = pd.read_csv(file_path, encoding='utf-8')
        
        # Find voltage and current columns
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
        
        # Get data
        voltage_data = df.iloc[:, voltage_idx].values
        current_data = df.iloc[:, current_idx].values
        
        # Unit conversion
        current_unit = df.columns[current_idx].strip().lower()
        current_scale = 1.0
        if current_unit == 'ma':
            current_scale = 1e3
        elif current_unit == 'na':
            current_scale = 1e-3
        elif current_unit == 'a':
            current_scale = 1e6
        elif current_unit in ['ua', 'µa']:
            current_scale = 1.0
        
        current_data = current_data * current_scale
        
        # Remove invalid data
        valid_mask = ~(np.isnan(voltage_data) | np.isnan(current_data) | 
                      np.isinf(voltage_data) | np.isinf(current_data))
        voltage_data = voltage_data[valid_mask]
        current_data = current_data[valid_mask]
        
        if len(voltage_data) < 10:
            return None, None, None, "Not enough valid data points"
        
        # Detect baseline
        forward_baseline_v, reverse_baseline_v, baseline_info = voltage_window_baseline_detector(
            voltage_data, current_data
        )
        
        if len(forward_baseline_v) == 0 and len(reverse_baseline_v) == 0:
            return None, None, None, "No baseline detected"
        
        # Create proper baseline result with interpolated currents
        baseline_result = {
            'forward_baseline_v': forward_baseline_v,
            'reverse_baseline_v': reverse_baseline_v,
            'forward_baseline_i': np.interp(forward_baseline_v, voltage_data, current_data) if len(forward_baseline_v) > 0 else np.array([]),
            'reverse_baseline_i': np.interp(reverse_baseline_v, voltage_data, current_data) if len(reverse_baseline_v) > 0 else np.array([]),
            'info': baseline_info
        }
        
        return voltage_data, current_data, baseline_result, None
        
    except Exception as e:
        return None, None, None, f"Error: {str(e)}"

def create_proper_baseline_plot(file_path, voltage_data, current_data, baseline_result, save_path):
    """Create a proper baseline detection plot"""
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    filename = os.path.basename(file_path)
    
    # Extract scan rate
    scan_rate = "Unknown"
    if "mVpS" in filename:
        try:
            import re
            match = re.search(r'(\d+)mVpS', filename, re.IGNORECASE)
            if match:
                scan_rate = f"{match.group(1)}mVpS"
        except:
            pass
    
    # Plot CV data
    ax.plot(voltage_data, current_data, 'b-', linewidth=2, label='CV Data', alpha=0.8)
    
    # Plot forward baseline
    if len(baseline_result['forward_baseline_v']) > 0:
        ax.plot(baseline_result['forward_baseline_v'], baseline_result['forward_baseline_i'], 
                'g-', linewidth=3, label=f'Forward Baseline ({len(baseline_result["forward_baseline_v"])} pts)', alpha=0.9)
    
    # Plot reverse baseline
    if len(baseline_result['reverse_baseline_v']) > 0:
        ax.plot(baseline_result['reverse_baseline_v'], baseline_result['reverse_baseline_i'], 
                'r-', linewidth=3, label=f'Reverse Baseline ({len(baseline_result["reverse_baseline_v"])} pts)', alpha=0.9)
    
    # Calculate R² values
    forward_r2 = 0.0
    reverse_r2 = 0.0
    
    if len(baseline_result['forward_baseline_v']) > 1:
        try:
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                baseline_result['forward_baseline_v'], baseline_result['forward_baseline_i']
            )
            forward_r2 = r_value ** 2
        except:
            pass
    
    if len(baseline_result['reverse_baseline_v']) > 1:
        try:
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                baseline_result['reverse_baseline_v'], baseline_result['reverse_baseline_i']
            )
            reverse_r2 = r_value ** 2
        except:
            pass
    
    # Add voltage windows as highlights
    v_min, v_max = voltage_data.min(), voltage_data.max()
    i_min, i_max = current_data.min(), current_data.max()
    
    # Forward region highlight
    if len(baseline_result['forward_baseline_v']) > 0:
        fw_min, fw_max = baseline_result['forward_baseline_v'].min(), baseline_result['forward_baseline_v'].max()
        rect_forward = Rectangle((fw_min, i_min), fw_max - fw_min, i_max - i_min, 
                               facecolor='lightgreen', alpha=0.2, 
                               label=f'Forward Region')
        ax.add_patch(rect_forward)
    
    # Reverse region highlight
    if len(baseline_result['reverse_baseline_v']) > 0:
        rv_min, rv_max = baseline_result['reverse_baseline_v'].min(), baseline_result['reverse_baseline_v'].max()
        rect_reverse = Rectangle((rv_min, i_min), rv_max - rv_min, i_max - i_min,
                               facecolor='orange', alpha=0.2,
                               label=f'Reverse Region')
        ax.add_patch(rect_reverse)
    
    # Quality assessment
    total_points = len(baseline_result['forward_baseline_v']) + len(baseline_result['reverse_baseline_v'])
    avg_r2 = (forward_r2 + reverse_r2) / 2 if forward_r2 > 0 or reverse_r2 > 0 else 0
    
    if avg_r2 > 0.7 and total_points > 50:
        quality = "EXCELLENT ✅"
        title_color = "green"
    elif avg_r2 > 0.5 and total_points > 30:
        quality = "GOOD ✅"
        title_color = "blue"
    elif avg_r2 > 0.2 and total_points > 15:
        quality = "FAIR ⚠️"
        title_color = "orange"
    else:
        quality = "POOR ❌"
        title_color = "red"
    
    # Formatting
    ax.set_xlabel('Voltage (V)', fontsize=12)
    ax.set_ylabel('Current (µA)', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    
    # Title
    ax.set_title(f'{quality} Baseline Detection ({scan_rate})\n{filename}', 
                fontsize=14, fontweight='bold', color=title_color)
    
    # Info box
    info_text = f'Forward R²: {forward_r2:.3f} ({len(baseline_result["forward_baseline_v"])} pts)\n'
    info_text += f'Reverse R²: {reverse_r2:.3f} ({len(baseline_result["reverse_baseline_v"])} pts)\n'
    info_text += f'Average R²: {avg_r2:.3f}'
    
    # Get baseline info
    if 'info' in baseline_result and baseline_result['info']:
        info = baseline_result['info']
        if 'forward_segments_count' in info:
            info_text += f'\nForward Segments: {info["forward_segments_count"]}'
        if 'reverse_segments_count' in info:
            info_text += f'\nReverse Segments: {info["reverse_segments_count"]}'
    
    ax.text(0.02, 0.98, info_text, 
            transform=ax.transAxes, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return {
        'quality': quality,
        'forward_r2': forward_r2,
        'reverse_r2': reverse_r2,
        'avg_r2': avg_r2,
        'total_points': total_points
    }

def test_single_file():
    """Test with the problematic file from the image"""
    
    print("🔧 Testing Fixed Baseline Detection")
    print("=" * 50)
    
    # Test with the file from the image
    file_path = "Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_50mVpS_E3_scan_08.csv"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        # Try to find similar file
        print("🔍 Looking for similar files...")
        import glob
        pattern = "Test_data/Palmsens/**/*50mVpS*E3*.csv"
        similar_files = glob.glob(pattern, recursive=True)
        if similar_files:
            file_path = similar_files[0]
            print(f"✅ Found: {file_path}")
        else:
            print("❌ No similar files found")
            return
    
    print(f"📁 Testing: {os.path.basename(file_path)}")
    
    # Process file
    voltage_data, current_data, baseline_result, error = load_and_process_csv(file_path)
    
    if error:
        print(f"❌ Error: {error}")
        return
    
    print(f"✅ Data loaded: {len(voltage_data)} points")
    print(f"📊 Voltage range: [{voltage_data.min():.3f}, {voltage_data.max():.3f}] V")
    print(f"📈 Current range: [{current_data.min():.1f}, {current_data.max():.1f}] µA")
    print(f"🔍 Forward baseline: {len(baseline_result['forward_baseline_v'])} points")
    print(f"🔄 Reverse baseline: {len(baseline_result['reverse_baseline_v'])} points")
    
    # Create plot
    plot_filename = "fixed_baseline_test.png"
    quality_info = create_proper_baseline_plot(
        file_path, voltage_data, current_data, baseline_result, plot_filename
    )
    
    print(f"✅ Fixed plot saved: {plot_filename}")
    print(f"📊 Quality: {quality_info['quality']}")
    print(f"📈 Forward R²: {quality_info['forward_r2']:.3f}")
    print(f"📈 Reverse R²: {quality_info['reverse_r2']:.3f}")
    print(f"📊 Average R²: {quality_info['avg_r2']:.3f}")

if __name__ == "__main__":
    test_single_file()