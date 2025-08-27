#!/usr/bin/env python3
"""
Simple test for problematic files - ทดสอบง่ายๆ สำหรับไฟล์ที่มีปัญหา
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def test_file_loading():
    """ทดสอบการโหลดไฟล์"""
    print("🔍 Testing file loading...")
    
    base_path = Path("Test_data/Stm32/Pipot_Ferro_0_5mM")
    test_file = "Pipot_Ferro_0_5mM_100mVpS_E1_scan_08.csv"
    
    filepath = base_path / test_file
    print(f"📁 Testing file: {filepath}")
    
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        return None, None
    
    # โหลดข้อมูล
    try:
        # อ่านไฟล์โดยข้าม header แรก
        df = pd.read_csv(filepath, skiprows=1)
        print(f"✅ File loaded successfully")
        print(f"📊 Columns: {list(df.columns)}")
        print(f"📈 Shape: {df.shape}")
        print(f"🔢 First 5 rows:")
        print(df.head())
        
        # หาคอลัมน์ voltage และ current
        voltage_col = None
        current_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'volt' in col_lower or 'potential' in col_lower or col_lower == 'v':
                voltage_col = col
            elif 'current' in col_lower or 'amp' in col_lower or col_lower in ['i', 'ua']:
                current_col = col
        
        print(f"🔋 Voltage column: {voltage_col}")
        print(f"⚡ Current column: {current_col}")
        
        if voltage_col and current_col:
            voltage = df[voltage_col].values
            current = df[current_col].values
            
            # แปลงหน่วยถ้าจำเป็น
            if np.abs(current).max() < 1e-3:
                current = current * 1e6
                print(f"📊 Converted current from A to µA")
            
            print(f"📈 Data ranges:")
            print(f"   Voltage: {voltage.min():.3f} to {voltage.max():.3f} V")
            print(f"   Current: {current.min():.3f} to {current.max():.3f} µA")
            
            return voltage, current
        else:
            print("❌ Could not identify voltage/current columns")
            return None, None
            
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return None, None

def test_basic_analysis(voltage, current):
    """ทดสอบการวิเคราะห์พื้นฐาน"""
    if voltage is None or current is None:
        print("❌ No data to analyze")
        return
    
    print(f"\n🔍 Basic Analysis:")
    
    # สถิติพื้นฐาน
    print(f"📊 Statistics:")
    print(f"   Data points: {len(voltage)}")
    print(f"   Voltage std: {np.std(voltage):.6f} V")
    print(f"   Current std: {np.std(current):.3f} µA")
    print(f"   Current mean: {np.mean(current):.3f} µA")
    
    # ตรวจสอบ pattern
    current_variation = np.abs(np.gradient(current))
    high_variation_indices = np.where(current_variation > np.percentile(current_variation, 90))[0]
    
    print(f"🎯 High variation points: {len(high_variation_indices)}")
    if len(high_variation_indices) > 0:
        print(f"   At voltages: {voltage[high_variation_indices][:5]}")  # แสดง 5 อันแรก
    
    # สร้างกราฟง่ายๆ
    try:
        plt.figure(figsize=(10, 6))
        plt.plot(voltage, current, 'b-', linewidth=1, alpha=0.8)
        plt.xlabel('Voltage (V)')
        plt.ylabel('Current (µA)')
        plt.title('CV Data - Basic Plot')
        plt.grid(True, alpha=0.3)
        
        # Mark high variation points
        if len(high_variation_indices) > 0:
            plt.plot(voltage[high_variation_indices], current[high_variation_indices], 
                    'ro', markersize=3, alpha=0.6, label='High Variation')
            plt.legend()
        
        plot_filename = "basic_test_plot.png"
        plt.savefig(plot_filename, dpi=150, bbox_inches='tight')
        print(f"📊 Basic plot saved: {plot_filename}")
        plt.show()
        
    except Exception as e:
        print(f"❌ Plotting error: {e}")

def test_simple_peak_detection(voltage, current):
    """ทดสอบการตรวจจับ peak แบบง่าย"""
    if voltage is None or current is None:
        print("❌ No data for peak detection")
        return
    
    print(f"\n🎯 Simple Peak Detection:")
    
    try:
        from scipy.signal import find_peaks
        
        # Normalize current
        current_norm = current / np.abs(current).max()
        
        # Find positive peaks (oxidation)
        pos_peaks, pos_properties = find_peaks(current_norm, prominence=0.1, width=3)
        
        # Find negative peaks (reduction)
        neg_peaks, neg_properties = find_peaks(-current_norm, prominence=0.1, width=3)
        
        print(f"📈 Found {len(pos_peaks)} positive peaks (potential oxidation)")
        print(f"📉 Found {len(neg_peaks)} negative peaks (potential reduction)")
        
        # แสดงรายละเอียด peaks
        for i, peak_idx in enumerate(pos_peaks[:5]):  # แสดง 5 อันแรก
            print(f"   OX Peak {i+1}: V={voltage[peak_idx]:.3f}V, I={current[peak_idx]:.1f}µA")
        
        for i, peak_idx in enumerate(neg_peaks[:5]):  # แสดง 5 อันแรก
            print(f"   RED Peak {i+1}: V={voltage[peak_idx]:.3f}V, I={current[peak_idx]:.1f}µA")
        
        # สร้างกราฟ peaks
        plt.figure(figsize=(10, 6))
        plt.plot(voltage, current, 'b-', linewidth=1, alpha=0.8, label='CV Data')
        
        if len(pos_peaks) > 0:
            plt.plot(voltage[pos_peaks], current[pos_peaks], 'r*', markersize=10, label='Oxidation Peaks')
        
        if len(neg_peaks) > 0:
            plt.plot(voltage[neg_peaks], current[neg_peaks], 'gv', markersize=10, label='Reduction Peaks')
        
        plt.xlabel('Voltage (V)')
        plt.ylabel('Current (µA)')
        plt.title('Simple Peak Detection')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        peak_plot_filename = "simple_peaks_test.png"
        plt.savefig(peak_plot_filename, dpi=150, bbox_inches='tight')
        print(f"📊 Peak plot saved: {peak_plot_filename}")
        plt.show()
        
    except ImportError:
        print("❌ scipy not available for peak detection")
    except Exception as e:
        print(f"❌ Peak detection error: {e}")

def main():
    """Main function"""
    print("🚀 Starting Simple Problem File Test")
    
    # ทดสอบการโหลดไฟล์
    voltage, current = test_file_loading()
    
    # ทดสอบการวิเคราะห์พื้นฐาน
    test_basic_analysis(voltage, current)
    
    # ทดสอบการตรวจจับ peak แบบง่าย
    test_simple_peak_detection(voltage, current)
    
    print("\n✅ Simple test completed!")

if __name__ == "__main__":
    main()
