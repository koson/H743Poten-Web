#!/usr/bin/env python3
"""
Comprehensive Problem File Analysis - วิเคราะห์ไฟล์ที่มีปัญหาทั้ง 5 ไฟล์
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import json
import time

def load_csv_data(filepath):
    """โหลดข้อมูลจากไฟล์ CSV"""
    try:
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return None, None
            
        # อ่านไฟล์โดยข้าม header แรก
        df = pd.read_csv(filepath, skiprows=1)
        
        # หาคอลัมน์ voltage และ current
        voltage_col = None
        current_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'volt' in col_lower or 'potential' in col_lower or col_lower == 'v':
                voltage_col = col
            elif 'current' in col_lower or 'amp' in col_lower or col_lower in ['i', 'ua']:
                current_col = col
        
        if voltage_col is None or current_col is None:
            print(f"❌ Could not find voltage/current columns in {filepath}")
            print(f"Available columns: {list(df.columns)}")
            return None, None
            
        voltage = df[voltage_col].values
        current = df[current_col].values
        
        # แปลงเป็น numpy arrays
        voltage = np.array(voltage, dtype=float)
        current = np.array(current, dtype=float)
        
        # แปลงหน่วยถ้าจำเป็น (ข้อมูลนี้อยู่ในหน่วย µA แล้ว)
        print(f"📈 Data loaded: {len(voltage)} points")
        print(f"   Voltage range: {voltage.min():.3f} to {voltage.max():.3f} V")
        print(f"   Current range: {current.min():.3f} to {current.max():.3f} µA")
        
        return voltage, current
        
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return None, None

def analyze_cv_characteristics(voltage, current, filename):
    """วิเคราะห์ลักษณะเฉพาะของ CV"""
    print(f"\n🔬 CV Characteristics Analysis: {filename}")
    
    # หาจุดที่แรงดันเปลี่ยนทิศทาง (turning points)
    voltage_diff = np.diff(voltage)
    direction_changes = np.where(np.diff(np.sign(voltage_diff)) != 0)[0]
    
    if len(direction_changes) > 0:
        turning_point = direction_changes[0] + 1  # +1 เพราะ diff ลดมิติไป 1
        print(f"   🔄 Scan direction change at index: {turning_point}")
        print(f"      Forward scan: 0 to {turning_point} ({turning_point} points)")
        print(f"      Reverse scan: {turning_point} to {len(voltage)} ({len(voltage)-turning_point} points)")
        
        # แยกส่วน forward และ reverse
        forward_v = voltage[:turning_point]
        forward_i = current[:turning_point]
        reverse_v = voltage[turning_point:]
        reverse_i = current[turning_point:]
        
        return forward_v, forward_i, reverse_v, reverse_i, turning_point
    else:
        print(f"   ❌ Could not find scan direction change")
        return voltage, current, np.array([]), np.array([]), len(voltage)

def simple_baseline_estimation(voltage, current, window_size=20):
    """ประมาณการ baseline แบบง่าย"""
    print(f"\n📏 Simple Baseline Estimation:")
    
    # หา regions ที่มี current variation น้อย
    current_variation = np.abs(np.gradient(current))
    smooth_variation = np.convolve(current_variation, np.ones(window_size)/window_size, mode='same')
    
    # หา percentile ต่ำสุดของ variation
    low_variation_threshold = np.percentile(smooth_variation, 20)
    stable_regions = smooth_variation < low_variation_threshold
    
    stable_indices = np.where(stable_regions)[0]
    print(f"   📊 Found {len(stable_indices)} stable points (low variation)")
    
    if len(stable_indices) > 10:
        # แยก stable regions ตาม voltage
        stable_voltages = voltage[stable_indices]
        stable_currents = current[stable_indices]
        
        # หา baseline สำหรับแต่ละช่วง voltage
        v_min, v_max = voltage.min(), voltage.max()
        v_range = v_max - v_min
        
        # แบ่งเป็น 3 ช่วง: low, mid, high voltage
        low_v_mask = stable_voltages < (v_min + v_range * 0.3)
        mid_v_mask = (stable_voltages >= (v_min + v_range * 0.3)) & (stable_voltages <= (v_min + v_range * 0.7))
        high_v_mask = stable_voltages > (v_min + v_range * 0.7)
        
        baseline_info = {}
        
        if np.sum(low_v_mask) > 3:
            baseline_info['low_voltage'] = {
                'voltage_range': (stable_voltages[low_v_mask].min(), stable_voltages[low_v_mask].max()),
                'current_mean': stable_currents[low_v_mask].mean(),
                'current_std': stable_currents[low_v_mask].std(),
                'point_count': np.sum(low_v_mask)
            }
            print(f"   🔵 Low voltage baseline: {baseline_info['low_voltage']['current_mean']:.3f} ± {baseline_info['low_voltage']['current_std']:.3f} µA")
        
        if np.sum(mid_v_mask) > 3:
            baseline_info['mid_voltage'] = {
                'voltage_range': (stable_voltages[mid_v_mask].min(), stable_voltages[mid_v_mask].max()),
                'current_mean': stable_currents[mid_v_mask].mean(),
                'current_std': stable_currents[mid_v_mask].std(),
                'point_count': np.sum(mid_v_mask)
            }
            print(f"   🟡 Mid voltage baseline: {baseline_info['mid_voltage']['current_mean']:.3f} ± {baseline_info['mid_voltage']['current_std']:.3f} µA")
        
        if np.sum(high_v_mask) > 3:
            baseline_info['high_voltage'] = {
                'voltage_range': (stable_voltages[high_v_mask].min(), stable_voltages[high_v_mask].max()),
                'current_mean': stable_currents[high_v_mask].mean(),
                'current_std': stable_currents[high_v_mask].std(),
                'point_count': np.sum(high_v_mask)
            }
            print(f"   🔴 High voltage baseline: {baseline_info['high_voltage']['current_mean']:.3f} ± {baseline_info['high_voltage']['current_std']:.3f} µA")
        
        return stable_indices, baseline_info
    else:
        print(f"   ❌ Not enough stable regions found")
        return np.array([]), {}

def detect_peaks_simple(voltage, current):
    """ตรวจจับ peaks แบบง่าย"""
    print(f"\n🎯 Simple Peak Detection:")
    
    try:
        from scipy.signal import find_peaks
        
        # Normalize current สำหรับ peak detection
        current_norm = current / np.abs(current).max()
        
        # Parameters for peak detection
        min_prominence = 0.1
        min_width = 3
        min_distance = 5
        
        # Find positive peaks (oxidation)
        pos_peaks, pos_props = find_peaks(current_norm, 
                                         prominence=min_prominence, 
                                         width=min_width,
                                         distance=min_distance)
        
        # Find negative peaks (reduction) 
        neg_peaks, neg_props = find_peaks(-current_norm, 
                                         prominence=min_prominence,
                                         width=min_width,
                                         distance=min_distance)
        
        peaks_info = {
            'oxidation_peaks': [],
            'reduction_peaks': []
        }
        
        # Process oxidation peaks
        for i, peak_idx in enumerate(pos_peaks):
            peak_info = {
                'index': int(peak_idx),
                'voltage': float(voltage[peak_idx]),
                'current': float(current[peak_idx]),
                'prominence': float(pos_props['prominences'][i]),
                'width': float(pos_props['widths'][i]) if 'widths' in pos_props else 0.0
            }
            peaks_info['oxidation_peaks'].append(peak_info)
            print(f"   🔴 OX Peak: V={peak_info['voltage']:.3f}V, I={peak_info['current']:.1f}µA, prom={peak_info['prominence']:.2f}")
        
        # Process reduction peaks
        for i, peak_idx in enumerate(neg_peaks):
            peak_info = {
                'index': int(peak_idx),
                'voltage': float(voltage[peak_idx]),
                'current': float(current[peak_idx]),
                'prominence': float(neg_props['prominences'][i]),
                'width': float(neg_props['widths'][i]) if 'widths' in neg_props else 0.0
            }
            peaks_info['reduction_peaks'].append(peak_info)
            print(f"   🔵 RED Peak: V={peak_info['voltage']:.3f}V, I={peak_info['current']:.1f}µA, prom={peak_info['prominence']:.2f}")
        
        print(f"   📊 Total: {len(pos_peaks)} oxidation, {len(neg_peaks)} reduction peaks")
        
        return peaks_info
        
    except ImportError:
        print("   ❌ scipy not available")
        return {'oxidation_peaks': [], 'reduction_peaks': []}
    except Exception as e:
        print(f"   ❌ Peak detection error: {e}")
        return {'oxidation_peaks': [], 'reduction_peaks': []}

def create_analysis_plot(voltage, current, stable_indices, baseline_info, peaks_info, filename, issue):
    """สร้างกราฟวิเคราะห์"""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: CV พร้อม baseline regions
    ax1.plot(voltage, current, 'b-', linewidth=1, alpha=0.8, label='CV Data')
    
    if len(stable_indices) > 0:
        ax1.plot(voltage[stable_indices], current[stable_indices], 'ro', 
                markersize=2, alpha=0.6, label='Stable Regions')
    
    # แสดง baseline levels
    if baseline_info:
        y_positions = []
        labels = []
        colors = ['blue', 'orange', 'red']
        
        for i, (region, info) in enumerate(baseline_info.items()):
            y_pos = info['current_mean']
            y_positions.append(y_pos)
            labels.append(f"{region}: {y_pos:.2f}µA")
            ax1.axhline(y=y_pos, color=colors[i % len(colors)], 
                       linestyle='--', alpha=0.7, label=f"{region} baseline")
    
    ax1.set_xlabel('Voltage (V)')
    ax1.set_ylabel('Current (µA)')
    ax1.set_title(f'CV Data with Baseline Analysis\n{filename}')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Peak detection
    ax2.plot(voltage, current, 'b-', linewidth=1, alpha=0.8, label='CV Data')
    
    # แสดง oxidation peaks
    for peak in peaks_info['oxidation_peaks']:
        ax2.plot(peak['voltage'], peak['current'], 'r*', markersize=10, 
                label='Oxidation Peak' if peak == peaks_info['oxidation_peaks'][0] else "")
    
    # แสดง reduction peaks
    for peak in peaks_info['reduction_peaks']:
        ax2.plot(peak['voltage'], peak['current'], 'gv', markersize=10,
                label='Reduction Peak' if peak == peaks_info['reduction_peaks'][0] else "")
    
    ax2.set_xlabel('Voltage (V)')
    ax2.set_ylabel('Current (µA)')
    ax2.set_title('Peak Detection Results')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Current variation analysis
    current_variation = np.abs(np.gradient(current))
    ax3.plot(voltage, current_variation, 'g-', linewidth=1, alpha=0.8, label='Current Variation')
    
    # Mark high variation points
    high_var_threshold = np.percentile(current_variation, 80)
    high_var_mask = current_variation > high_var_threshold
    ax3.plot(voltage[high_var_mask], current_variation[high_var_mask], 'ro', 
            markersize=3, alpha=0.6, label='High Variation')
    
    ax3.axhline(y=high_var_threshold, color='red', linestyle='--', alpha=0.7, 
                label=f'80th percentile: {high_var_threshold:.3f}')
    
    ax3.set_xlabel('Voltage (V)')
    ax3.set_ylabel('|dI/dV| (µA/V)')
    ax3.set_title('Current Variation Analysis')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Forward vs Reverse scan comparison
    forward_v, forward_i, reverse_v, reverse_i, turning_point = analyze_cv_characteristics(voltage, current, filename)
    
    ax4.plot(forward_v, forward_i, 'b-', linewidth=2, alpha=0.8, label='Forward Scan')
    if len(reverse_v) > 0:
        ax4.plot(reverse_v, reverse_i, 'r-', linewidth=2, alpha=0.8, label='Reverse Scan')
    
    # Mark turning point
    if turning_point < len(voltage):
        ax4.plot(voltage[turning_point], current[turning_point], 'ko', 
                markersize=8, label='Turning Point')
    
    ax4.set_xlabel('Voltage (V)')
    ax4.set_ylabel('Current (µA)')
    ax4.set_title('Forward vs Reverse Scan')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.suptitle(f'Comprehensive Analysis: {filename}\nIssue: {issue}', fontsize=14)
    plt.tight_layout()
    
    # บันทึกกราฟ
    plot_filename = f"analysis_{filename.replace('.csv', '')}.png"
    plt.savefig(plot_filename, dpi=150, bbox_inches='tight')
    print(f"📊 Analysis plot saved: {plot_filename}")
    
    try:
        plt.show()
    except:
        pass  # ไม่ให้ error ถ้า GUI ไม่พร้อม

def analyze_single_file(filepath, issue, expected):
    """วิเคราะห์ไฟล์เดียว"""
    filename = os.path.basename(filepath)
    
    print(f"\n{'='*80}")
    print(f"🔍 ANALYZING: {filename}")
    print(f"🚨 Known Issue: {issue}")
    print(f"💡 Expected: {expected}")
    print(f"{'='*80}")
    
    # โหลดข้อมูล
    voltage, current = load_csv_data(filepath)
    
    if voltage is None or current is None:
        print(f"❌ Failed to load data from {filename}")
        return None
    
    # วิเคราะห์ลักษณะเฉพาะ CV
    forward_v, forward_i, reverse_v, reverse_i, turning_point = analyze_cv_characteristics(voltage, current, filename)
    
    # ประมาณการ baseline
    stable_indices, baseline_info = simple_baseline_estimation(voltage, current)
    
    # ตรวจจับ peaks
    peaks_info = detect_peaks_simple(voltage, current)
    
    # สร้างกราฟวิเคราะห์
    create_analysis_plot(voltage, current, stable_indices, baseline_info, peaks_info, filename, issue)
    
    # สรุปผลการวิเคราะห์
    analysis_result = {
        'filename': filename,
        'issue': issue,
        'expected': expected,
        'data_info': {
            'voltage_range': (float(voltage.min()), float(voltage.max())),
            'current_range': (float(current.min()), float(current.max())),
            'data_points': len(voltage),
            'turning_point': int(turning_point)
        },
        'baseline_analysis': baseline_info,
        'peak_analysis': {
            'oxidation_count': len(peaks_info['oxidation_peaks']),
            'reduction_count': len(peaks_info['reduction_peaks']),
            'peaks': peaks_info
        },
        'stable_regions': {
            'count': len(stable_indices),
            'percentage': len(stable_indices) / len(voltage) * 100
        }
    }
    
    return analysis_result

def main():
    """Main analysis function"""
    print("🚀 Starting Comprehensive Problem File Analysis")
    
    # ไฟล์ที่มีปัญหาทั้ง 5 ไฟล์
    problem_files = [
        {
            'file': 'Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_100mVpS_E1_scan_08.csv',
            'issue': 'baseline segment ไม่ถูก (ไม่อยู่ช่วงยาว)',
            'expected': 'ควรมี baseline segment ที่ยาวกว่า'
        },
        {
            'file': 'Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_200mVpS_E5_scan_05.csv', 
            'issue': 'มี OX 2 อัน แต่ไม่มี RED, OX ที่ +0.7V ไม่ถูก',
            'expected': 'ควรเจอ RED peak และ OX ที่ +0.7V ไม่ควรถูกตรวจจับ'
        },
        {
            'file': 'Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_20mVpS_E1_scan_02.csv',
            'issue': 'ไม่เจอ peak และ baseline เลย',
            'expected': 'ควรเจอ peak และ baseline แม้สัญญาณอ่อน'
        },
        {
            'file': 'Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_20mVpS_E2_scan_04.csv',
            'issue': 'ไม่เจอ segment ใช้ baseline เป็นศูนย์',
            'expected': 'ควรเจอ baseline segment ที่ถูกต้อง'
        },
        {
            'file': 'Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_400mVpS_E5_scan_06.csv',
            'issue': 'baseline segment อยู่ตรงที่ควรเป็น peak',
            'expected': 'baseline ไม่ควรทับกับ peak'
        }
    ]
    
    results = []
    
    for i, file_info in enumerate(problem_files, 1):
        print(f"\n📊 Progress: {i}/{len(problem_files)}")
        
        try:
            result = analyze_single_file(file_info['file'], file_info['issue'], file_info['expected'])
            if result:
                results.append(result)
        except Exception as e:
            print(f"❌ Error analyzing {file_info['file']}: {e}")
            continue
    
    # สรุปผลรวม
    print(f"\n{'='*80}")
    print("📋 COMPREHENSIVE ANALYSIS SUMMARY")
    print(f"{'='*80}")
    
    total_files = len(results)
    files_with_peaks = 0
    files_with_baseline = 0
    
    for result in results:
        filename = result['filename']
        print(f"\n📄 {filename}")
        print(f"   🚨 Issue: {result['issue']}")
        
        # Peak analysis
        ox_count = result['peak_analysis']['oxidation_count']
        red_count = result['peak_analysis']['reduction_count']
        total_peaks = ox_count + red_count
        
        if total_peaks > 0:
            files_with_peaks += 1
            print(f"   ✅ Peaks: {total_peaks} total (OX:{ox_count}, RED:{red_count})")
        else:
            print(f"   ❌ Peaks: None detected")
        
        # Baseline analysis
        baseline_regions = len(result['baseline_analysis'])
        if baseline_regions > 0:
            files_with_baseline += 1
            print(f"   ✅ Baseline: {baseline_regions} regions found")
        else:
            print(f"   ❌ Baseline: No stable regions")
        
        # Stable regions
        stable_percentage = result['stable_regions']['percentage']
        print(f"   📊 Stable regions: {stable_percentage:.1f}% of data")
    
    print(f"\n📊 Overall Summary:")
    print(f"   Files analyzed: {total_files}")
    print(f"   Files with peaks detected: {files_with_peaks}/{total_files} ({files_with_peaks/total_files*100:.1f}%)")
    print(f"   Files with baseline regions: {files_with_baseline}/{total_files} ({files_with_baseline/total_files*100:.1f}%)")
    
    # บันทึกผลลัพธ์
    report_filename = f"comprehensive_analysis_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Comprehensive report saved: {report_filename}")
    print("✅ Analysis completed!")

if __name__ == "__main__":
    main()
