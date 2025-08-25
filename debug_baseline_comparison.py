#!/usr/bin/env python3
"""
Debug baseline detection differences between files
"""

import numpy as np
import matplotlib.pyplot as plt
import logging
import json
from baseline_detector_voltage_windows import voltage_window_baseline_detector
from baseline_detector_v4 import cv_baseline_detector_v4
from scipy.signal import find_peaks

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_palmsens_file(file_path):
    """Load and parse PalmSens CSV file"""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            raise ValueError('File too short')
        
        # Handle instrument file format (FileName: header)
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
            if header in ['v', 'voltage'] or 'volt' in header or 'potential' in header:
                voltage_idx = i
            elif header in ['a', 'ua', 'ma', 'na', 'current'] or 'amp' in header or 'curr' in header:
                current_idx = i
        
        if voltage_idx == -1 or current_idx == -1:
            raise ValueError(f'Could not find voltage or current columns')
        
        # Determine current scaling
        current_unit = headers[current_idx]
        current_scale = 1.0
        
        # Check if this is STM32/Pipot file
        is_stm32_file = (
            'pipot' in file_path.lower() or 
            'stm32' in file_path.lower() or
            (current_unit == 'a' and lines[0].strip().startswith('FileName:'))
        )
        
        if current_unit == 'ma':
            current_scale = 1e3
        elif current_unit == 'na':
            current_scale = 1e-3
        elif current_unit == 'a' and is_stm32_file:
            current_scale = 1e6
        elif current_unit == 'a' and not is_stm32_file:
            current_scale = 1e6
        
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
        
        return np.array(voltage), np.array(current)
        
    except Exception as e:
        logger.error(f"Error loading CSV file: {str(e)}")
        raise

def get_peak_regions(voltage, current):
    """Quick peak detection for baseline avoidance"""
    peak_regions = []
    try:
        # Normalize current for quick peak detection
        current_max = np.abs(current).max()
        if current_max > 0:
            current_norm = current / current_max
            
            # Quick peak detection with loose criteria
            pos_peaks, _ = find_peaks(current_norm, prominence=0.05, width=3)
            neg_peaks, _ = find_peaks(-current_norm, prominence=0.05, width=3)
            
            # Convert to peak regions (start_idx, end_idx)
            all_peak_indices = np.concatenate([pos_peaks, neg_peaks])
            for peak_idx in all_peak_indices:
                if 0 <= peak_idx < len(voltage):
                    # Create a small region around each peak (±5 points)
                    start_idx = max(0, peak_idx - 5)
                    end_idx = min(len(voltage) - 1, peak_idx + 5)
                    peak_regions.append((int(start_idx), int(end_idx)))
                    
    except Exception as e:
        logger.warning(f"Peak detection failed: {e}")
    
    return peak_regions

def analyze_baseline_detection(file_path, label):
    """Analyze baseline detection for a specific file"""
    print(f"\n🔍 Analyzing {label}: {file_path}")
    
    # Load data
    voltage, current = load_palmsens_file(file_path)
    print(f"📊 Data points: {len(voltage)}")
    print(f"🔌 Voltage range: {voltage.min():.3f}V to {voltage.max():.3f}V")
    print(f"⚡ Current range: {current.min():.3f}µA to {current.max():.3f}µA")
    
    # Get peak regions
    peak_regions = get_peak_regions(voltage, current)
    print(f"🎯 Peak regions detected: {len(peak_regions)}")
    for i, (start, end) in enumerate(peak_regions):
        print(f"   Peak {i+1}: [{start}:{end}] V={voltage[start]:.3f} to {voltage[end]:.3f}")
    
    # Run baseline detection
    forward_baseline, reverse_baseline, info = cv_baseline_detector_v4(voltage, current, peak_regions)
    
    print(f"\n📈 Baseline Results:")
    print(f"   Forward baseline: {len(forward_baseline)} points, range [{forward_baseline.min():.3f}, {forward_baseline.max():.3f}]µA")
    print(f"   Reverse baseline: {len(reverse_baseline)} points, range [{reverse_baseline.min():.3f}, {reverse_baseline.max():.3f}]µA")
    
    # Check segments
    forward_seg = info.get('forward_segment', {})
    reverse_seg = info.get('reverse_segment', {})
    
    if forward_seg:
        seg_length = forward_seg['end_idx'] - forward_seg['start_idx'] + 1
        print(f"   Forward segment: [{forward_seg['start_idx']}:{forward_seg['end_idx']}] = {seg_length} points")
        print(f"                   V=[{forward_seg['voltage_start']:.3f}:{forward_seg['voltage_end']:.3f}], R²={forward_seg['r2']:.3f}")
    
    if reverse_seg:
        seg_length = reverse_seg['end_idx'] - reverse_seg['start_idx'] + 1
        print(f"   Reverse segment: [{reverse_seg['start_idx']}:{reverse_seg['end_idx']}] = {seg_length} points")
        print(f"                   V=[{reverse_seg['voltage_start']:.3f}:{reverse_seg['voltage_end']:.3f}], R²={reverse_seg['r2']:.3f}")
    
    return {
        'voltage': voltage,
        'current': current,
        'forward_baseline': forward_baseline,
        'reverse_baseline': reverse_baseline,
        'peak_regions': peak_regions,
        'info': info
    }

def plot_comparison(good_result, bad_result):
    """Plot comparison between good and bad baseline detection"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot good case
    ax1.plot(good_result['voltage'], good_result['current'], 'b-', label='CV Data', alpha=0.7)
    baseline_full = np.concatenate([good_result['forward_baseline'], good_result['reverse_baseline']])
    ax1.plot(good_result['voltage'], baseline_full, 'g-', label='Baseline', linewidth=2)
    
    # Mark segments
    forward_seg = good_result['info'].get('forward_segment', {})
    if forward_seg:
        start_idx, end_idx = forward_seg['start_idx'], forward_seg['end_idx']
        ax1.axvspan(good_result['voltage'][start_idx], good_result['voltage'][end_idx], 
                   alpha=0.3, color='green', label=f"Forward Seg ({end_idx-start_idx+1} pts)")
    
    reverse_seg = good_result['info'].get('reverse_segment', {})
    if reverse_seg:
        start_idx, end_idx = reverse_seg['start_idx'], reverse_seg['end_idx']
        ax1.axvspan(good_result['voltage'][start_idx], good_result['voltage'][end_idx], 
                   alpha=0.3, color='orange', label=f"Reverse Seg ({end_idx-start_idx+1} pts)")
    
    ax1.set_title('✅ Good Baseline Detection (200mVpS)')
    ax1.set_xlabel('Voltage (V)')
    ax1.set_ylabel('Current (µA)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot bad case
    ax2.plot(bad_result['voltage'], bad_result['current'], 'b-', label='CV Data', alpha=0.7)
    baseline_full = np.concatenate([bad_result['forward_baseline'], bad_result['reverse_baseline']])
    ax2.plot(bad_result['voltage'], baseline_full, 'r-', label='Baseline', linewidth=2)
    
    # Mark segments
    forward_seg = bad_result['info'].get('forward_segment', {})
    if forward_seg:
        start_idx, end_idx = forward_seg['start_idx'], forward_seg['end_idx']
        ax2.axvspan(bad_result['voltage'][start_idx], bad_result['voltage'][end_idx], 
                   alpha=0.3, color='red', label=f"Forward Seg ({end_idx-start_idx+1} pts)")
    
    reverse_seg = bad_result['info'].get('reverse_segment', {})
    if reverse_seg:
        start_idx, end_idx = reverse_seg['start_idx'], reverse_seg['end_idx']
        ax2.axvspan(bad_result['voltage'][start_idx], bad_result['voltage'][end_idx], 
                   alpha=0.3, color='orange', label=f"Reverse Seg ({end_idx-start_idx+1} pts)")
    
    ax2.set_title('❌ Problematic Baseline Detection (100mVpS)')
    ax2.set_xlabel('Voltage (V)')
    ax2.set_ylabel('Current (µA)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('baseline_comparison_debug.png', dpi=150, bbox_inches='tight')
    plt.show()

def main():
    print("🔍 Debugging Baseline Detection Differences")
    
    # File paths
    good_file = "./Test_data/Palmsens/Palmsens_1.0mM/Palmsens_1.0mM_CV_200mVpS_E1_scan_05.csv"
    bad_file = "./Test_data/Palmsens/Palmsens_1.0mM/Palmsens_1.0mM_CV_100mVpS_E1_scan_05.csv"
    
    try:
        # Analyze both files
        good_result = analyze_baseline_detection(good_file, "GOOD (200mVpS)")
        bad_result = analyze_baseline_detection(bad_file, "PROBLEMATIC (100mVpS)")
        
        # Compare results
        print(f"\n📊 Comparison Summary:")
        
        # Forward segment comparison
        good_forward = good_result['info'].get('forward_segment', {})
        bad_forward = bad_result['info'].get('forward_segment', {})
        
        if good_forward and bad_forward:
            good_length = good_forward['end_idx'] - good_forward['start_idx'] + 1
            bad_length = bad_forward['end_idx'] - bad_forward['start_idx'] + 1
            
            print(f"🔍 Forward Segment Analysis:")
            print(f"   Good: {good_length} points, R²={good_forward['r2']:.3f}")
            print(f"   Bad:  {bad_length} points, R²={bad_forward['r2']:.3f}")
            print(f"   Length difference: {bad_length - good_length} points")
            
            if bad_length > good_length * 2:
                print(f"   ⚠️ Bad segment is {bad_length/good_length:.1f}x longer than good!")
        
        # Plot comparison
        plot_comparison(good_result, bad_result)
        
        # Save detailed info
        comparison_data = {
            'good_file': good_file,
            'bad_file': bad_file,
            'good_info': good_result['info'],
            'bad_info': bad_result['info']
        }
        
        with open('baseline_debug_comparison.json', 'w') as f:
            json.dump(comparison_data, f, indent=2, default=str)
        
        print(f"\n✅ Analysis complete. Check baseline_comparison_debug.png and baseline_debug_comparison.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()