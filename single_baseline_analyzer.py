#!/usr/bin/env python3
"""
Single CSV File Baseline Analysis with R² Values
Usage: python3 single_baseline_analyzer.py <csv_file_path>
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import argparse
from scipy import stats
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

# Import baseline detector
sys.path.append('.')
from baseline_detector_v4 import cv_baseline_detector_v4

def load_csv_file(file_path):
    """Load CSV file with automatic format detection"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            raise ValueError('File too short')
        
        # Skip filename header if present
        data_start_idx = 1 if lines[0].strip().startswith('FileName:') else 0
        
        # Find header line
        header_line = None
        for i in range(data_start_idx, min(data_start_idx + 3, len(lines))):
            line = lines[i].strip().lower()
            if any(keyword in line for keyword in ['v,', 'voltage', 'potential']):
                header_line = i
                data_start_idx = i + 1
                break
        
        # Extract data
        voltages, currents = [], []
        for line in lines[data_start_idx:]:
            line = line.strip()
            if not line:
                continue
            try:
                parts = line.split(',')
                if len(parts) >= 2:
                    voltage = float(parts[0])
                    current = float(parts[1])
                    voltages.append(voltage)
                    currents.append(current)
            except (ValueError, IndexError):
                continue
        
        if len(voltages) == 0:
            raise ValueError("No valid data found")
        
        return np.array(voltages), np.array(currents)
    
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return None, None

def calculate_segment_r2(voltage_data, current_data, segment_info):
    """Calculate R² for a baseline segment"""
    if not segment_info or segment_info.get('start_idx') is None:
        return 0.0
    
    try:
        start_idx = segment_info['start_idx']
        end_idx = segment_info['end_idx']
        
        if start_idx >= len(voltage_data) or end_idx >= len(voltage_data):
            return 0.0
        
        v_seg = voltage_data[start_idx:end_idx+1]
        i_seg = current_data[start_idx:end_idx+1]
        
        if len(v_seg) < 2:
            return 0.0
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(v_seg, i_seg)
        return r_value ** 2
    
    except Exception:
        return 0.0

def create_enhanced_baseline_plot(file_path, voltage_data, current_data, baseline_result, output_path=None):
    """Create enhanced baseline plot with R² values"""
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 9))
    
    filename = os.path.basename(file_path)
    
    # Extract scan rate from filename
    scan_rate = "Unknown"
    if "mVpS" in filename or "mvps" in filename.lower():
        try:
            import re
            match = re.search(r'(\d+)mVpS', filename, re.IGNORECASE)
            if match:
                scan_rate = f"{match.group(1)}mVpS"
        except:
            pass
    
    # Plot CV data
    ax.plot(voltage_data, current_data, 'b-', linewidth=2, label='CV Data', alpha=0.8)
    
    # Combine baseline points
    forward_baseline = baseline_result.get('forward_baseline', np.array([]))
    reverse_baseline = baseline_result.get('reverse_baseline', np.array([]))
    
    # Plot baselines with different colors
    if len(forward_baseline) > 0:
        forward_current = np.interp(forward_baseline, voltage_data, current_data)
        ax.plot(forward_baseline, forward_current, 'g-', linewidth=3, 
                label=f'Forward Baseline ({len(forward_baseline)} pts)', alpha=0.9)
    
    if len(reverse_baseline) > 0:
        reverse_current = np.interp(reverse_baseline, voltage_data, current_data)
        ax.plot(reverse_baseline, reverse_current, 'r-', linewidth=3, 
                label=f'Reverse Baseline ({len(reverse_baseline)} pts)', alpha=0.9)
    
    # Calculate R² values
    info = baseline_result.get('info', {})
    forward_r2 = calculate_segment_r2(voltage_data, current_data, info.get('forward_segment'))
    reverse_r2 = calculate_segment_r2(voltage_data, current_data, info.get('reverse_segment'))
    
    # Add voltage windows with R² labels
    v_min, v_max = voltage_data.min(), voltage_data.max()
    i_min, i_max = current_data.min(), current_data.max()
    i_range = i_max - i_min
    
    # Forward segment highlight
    forward_seg = info.get('forward_segment', {})
    if forward_seg and forward_seg.get('start_idx') is not None:
        start_idx, end_idx = forward_seg['start_idx'], forward_seg['end_idx']
        v_start, v_end = voltage_data[start_idx], voltage_data[end_idx]
        
        rect_forward = Rectangle((min(v_start, v_end), i_min), abs(v_end - v_start), i_range,
                               facecolor='lightgreen', alpha=0.3,
                               label=f'Forward Seg ({end_idx-start_idx+1} pts)')
        ax.add_patch(rect_forward)
        
        # Add R² text for forward segment
        mid_v = (v_start + v_end) / 2
        ax.text(mid_v, i_max - 0.1 * i_range, f'R²={forward_r2:.3f}', 
                ha='center', va='top', fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.8))
    
    # Reverse segment highlight
    reverse_seg = info.get('reverse_segment', {})
    if reverse_seg and reverse_seg.get('start_idx') is not None:
        start_idx, end_idx = reverse_seg['start_idx'], reverse_seg['end_idx']
        v_start, v_end = voltage_data[start_idx], voltage_data[end_idx]
        
        rect_reverse = Rectangle((min(v_start, v_end), i_min), abs(v_end - v_start), i_range,
                               facecolor='orange', alpha=0.3,
                               label=f'Reverse Seg ({end_idx-start_idx+1} pts)')
        ax.add_patch(rect_reverse)
        
        # Add R² text for reverse segment
        mid_v = (v_start + v_end) / 2
        ax.text(mid_v, i_max - 0.1 * i_range, f'R²={reverse_r2:.3f}', 
                ha='center', va='top', fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='orange', alpha=0.8))
    
    # Quality assessment
    avg_r2 = (forward_r2 + reverse_r2) / 2 if forward_r2 > 0 or reverse_r2 > 0 else 0
    total_baseline_points = len(forward_baseline) + len(reverse_baseline)
    
    if avg_r2 > 0.8 and total_baseline_points > 50:
        quality = "EXCELLENT ✅"
        title_color = "green"
    elif avg_r2 > 0.6 and total_baseline_points > 30:
        quality = "GOOD ✅"
        title_color = "blue"
    elif avg_r2 > 0.3 and total_baseline_points > 15:
        quality = "FAIR ⚠️"
        title_color = "orange"
    else:
        quality = "POOR ❌"
        title_color = "red"
    
    # Formatting
    ax.set_xlabel('Voltage (V)', fontsize=12)
    ax.set_ylabel('Current (µA)', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10, loc='upper right')
    
    # Enhanced title with quality and scan rate
    ax.set_title(f'{quality} Baseline Detection ({scan_rate})\n{filename}', 
                fontsize=14, fontweight='bold', color=title_color)
    
    # Enhanced info box
    info_text = f'Overall Quality: {quality}\n'
    info_text += f'Forward R²: {forward_r2:.3f} ({len(forward_baseline)} pts)\n'
    info_text += f'Reverse R²: {reverse_r2:.3f} ({len(reverse_baseline)} pts)\n'
    info_text += f'Average R²: {avg_r2:.3f}\n'
    info_text += f'Total baseline points: {total_baseline_points}'
    
    # Add additional segment info if available
    if forward_seg:
        info_text += f'\nForward: V=[{forward_seg.get("voltage_start", 0):.3f}:{forward_seg.get("voltage_end", 0):.3f}]V'
    if reverse_seg:
        info_text += f'\nReverse: V=[{reverse_seg.get("voltage_start", 0):.3f}:{reverse_seg.get("voltage_end", 0):.3f}]V'
    
    ax.text(0.02, 0.98, info_text, 
            transform=ax.transAxes, fontsize=9, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    plt.tight_layout()
    
    # Save plot
    if output_path is None:
        base_name = os.path.splitext(filename)[0]
        output_path = f"{base_name}_baseline_analysis.png"
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return {
        'output_path': output_path,
        'quality': quality,
        'forward_r2': forward_r2,
        'reverse_r2': reverse_r2,
        'avg_r2': avg_r2,
        'total_points': total_baseline_points,
        'scan_rate': scan_rate
    }

def analyze_single_file(file_path, output_dir=None):
    """Analyze a single CSV file and create baseline plot"""
    
    print(f"🔍 Analyzing: {os.path.basename(file_path)}")
    
    # Load data
    voltage_data, current_data = load_csv_file(file_path)
    if voltage_data is None:
        return None
    
    print(f"📊 Data loaded: {len(voltage_data)} points")
    print(f"📈 Voltage range: [{voltage_data.min():.3f}, {voltage_data.max():.3f}] V")
    print(f"📈 Current range: [{current_data.min():.1f}, {current_data.max():.1f}] µA")
    
    # Detect baseline
    try:
        baseline_result = cv_baseline_detector_v4(voltage_data, current_data)
        
        # Set output path
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}_baseline_analysis.png")
        else:
            output_path = None
        
        # Create plot
        result = create_enhanced_baseline_plot(file_path, voltage_data, current_data, 
                                             baseline_result, output_path)
        
        print(f"✅ Analysis complete!")
        print(f"📊 Quality: {result['quality']}")
        print(f"📈 Forward R²: {result['forward_r2']:.3f}")
        print(f"📈 Reverse R²: {result['reverse_r2']:.3f}")
        print(f"📊 Average R²: {result['avg_r2']:.3f}")
        print(f"🖼️ Plot saved: {result['output_path']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='Analyze baseline detection for a single CSV file')
    parser.add_argument('file_path', help='Path to the CSV file to analyze')
    parser.add_argument('-o', '--output', help='Output directory for the plot (default: same as input)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file_path):
        print(f"❌ File not found: {args.file_path}")
        sys.exit(1)
    
    print("🎯 Single File Baseline Analyzer")
    print("=" * 50)
    
    result = analyze_single_file(args.file_path, args.output)
    
    if result:
        print(f"\n🎉 Analysis successful!")
        print(f"📁 Output: {result['output_path']}")
    else:
        print(f"\n❌ Analysis failed!")
        sys.exit(1)

if __name__ == "__main__":
    # If run without arguments, show usage
    if len(sys.argv) == 1:
        print("🎯 Single File Baseline Analyzer")
        print("=" * 50)
        print("Usage: python3 single_baseline_analyzer.py <csv_file_path> [-o output_dir]")
        print("\nExample:")
        print("python3 single_baseline_analyzer.py Test_data/Palmsens/Palmsens_1.0mM/Palmsens_1.0mM_CV_200mVpS_E1_scan_05.csv")
        sys.exit(1)
    
    main()