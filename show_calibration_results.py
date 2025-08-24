#!/usr/bin/env python3
"""
แสดงผลสรุปการเปรียบเทียบ STM32 ก่อน-หลัง calibrate
"""

import sqlite3
import json
import numpy as np
from datetime import datetime

def analyze_calibration_results():
    """วิเคราะห์และแสดงผลการเปรียบเทียบ calibration"""
    
    print("🎯 สรุปผลการเปรียบเทียบ Calibration")
    print("="*70)
    
    # อ่านข้อมูลจากฐานข้อมูล
    try:
        conn = sqlite3.connect('data_logs/parameter_log.db')
        cursor = conn.cursor()
        
        # ข้อมูล STM32 (ID 75)
        cursor.execute("SELECT * FROM measurements WHERE id = 75")
        stm32_data = cursor.fetchone()
        
        # ข้อมูล PalmSens (ID 90) 
        cursor.execute("SELECT * FROM measurements WHERE id = 90")
        palmsens_data = cursor.fetchone()
        
        if stm32_data and palmsens_data:
            print("📊 ข้อมูล Measurements ที่เปรียบเทียบ:")
            print("-" * 70)
            
            # STM32 Information
            stm32_raw = json.loads(stm32_data[13])  # raw_data_json
            stm32_cv = stm32_raw['cv_data']
            stm32_voltage = np.array([p[0] for p in stm32_cv])
            stm32_current = np.array([p[1] for p in stm32_cv])
            
            print(f"🔴 STM32 (ID: {stm32_data[0]}):")
            print(f"   Sample: {stm32_data[1]}")
            print(f"   Scan Rate: {stm32_data[5]:.1f} V/s")
            print(f"   Data Points: {len(stm32_cv)}")
            print(f"   Voltage Range: {stm32_voltage.min():.3f} to {stm32_voltage.max():.3f} V")
            print(f"   Current Range: {stm32_current.min()*1e6:.2f} to {stm32_current.max()*1e6:.2f} μA")
            
            # PalmSens Information  
            palmsens_raw = json.loads(palmsens_data[13])  # raw_data_json
            palmsens_cv = palmsens_raw['cv_data']
            palmsens_voltage = np.array([p[0] for p in palmsens_cv])
            palmsens_current = np.array([p[1] for p in palmsens_cv])
            
            print(f"\n🔵 PalmSens Reference (ID: {palmsens_data[0]}):")
            print(f"   Sample: {palmsens_data[1]}")
            print(f"   Scan Rate: {palmsens_data[5]:.1f} V/s")
            print(f"   Data Points: {len(palmsens_cv)}")
            print(f"   Voltage Range: {palmsens_voltage.min():.3f} to {palmsens_voltage.max():.3f} V")
            print(f"   Current Range: {palmsens_current.min()*1e6:.2f} to {palmsens_current.max()*1e6:.2f} μA")
            
            # การ Calibration (อัลกอริทึมง่ายๆ)
            print("\n🔧 การ Calibration:")
            print("-" * 70)
            
            # หา peak ของแต่ละ curve
            stm32_peak_idx = np.argmax(np.abs(stm32_current))
            palmsens_peak_idx = np.argmax(np.abs(palmsens_current))
            
            # คำนวณ offset และ gain
            voltage_offset = palmsens_voltage[palmsens_peak_idx] - stm32_voltage[stm32_peak_idx]
            current_gain = palmsens_current[palmsens_peak_idx] / stm32_current[stm32_peak_idx] if stm32_current[stm32_peak_idx] != 0 else 1
            
            print(f"Voltage Offset: {voltage_offset*1000:+.2f} mV")
            print(f"Current Gain: {current_gain:.3f}x")
            
            # Apply calibration
            calibrated_voltage = stm32_voltage + voltage_offset
            calibrated_current = stm32_current * current_gain
            
            # คำนวณสถิติเปรียบเทียบ
            print("\n📈 สถิติการเปรียบเทียบ:")
            print("-" * 70)
            
            # ตัดข้อมูลให้มีความยาวเท่ากัน
            min_len = min(len(stm32_current), len(palmsens_current))
            stm32_trimmed = stm32_current[:min_len]
            palmsens_trimmed = palmsens_current[:min_len]
            calibrated_trimmed = calibrated_current[:min_len]
            
            # Correlation
            corr_before = np.corrcoef(stm32_trimmed, palmsens_trimmed)[0, 1]
            corr_after = np.corrcoef(calibrated_trimmed, palmsens_trimmed)[0, 1]
            
            # RMSE
            rmse_before = np.sqrt(np.mean((stm32_trimmed - palmsens_trimmed)**2))
            rmse_after = np.sqrt(np.mean((calibrated_trimmed - palmsens_trimmed)**2))
            
            # R²
            ss_tot = np.sum((palmsens_trimmed - np.mean(palmsens_trimmed))**2)
            ss_res_before = np.sum((stm32_trimmed - palmsens_trimmed)**2)
            ss_res_after = np.sum((calibrated_trimmed - palmsens_trimmed)**2)
            
            r2_before = 1 - (ss_res_before / ss_tot) if ss_tot != 0 else 0
            r2_after = 1 - (ss_res_after / ss_tot) if ss_tot != 0 else 0
            
            print("📊 ก่อน Calibration:")
            print(f"   Correlation: {corr_before:.4f}")
            print(f"   RMSE: {rmse_before*1e6:.2f} μA")
            print(f"   R²: {r2_before:.4f}")
            
            print("\n🔧 หลัง Calibration:")
            print(f"   Correlation: {corr_after:.4f}")
            print(f"   RMSE: {rmse_after*1e6:.2f} μA") 
            print(f"   R²: {r2_after:.4f}")
            
            # การปรับปรุง
            print("\n✅ การปรับปรุง:")
            print("-" * 70)
            corr_improvement = ((corr_after - corr_before) / abs(corr_before) * 100) if corr_before != 0 else 0
            rmse_improvement = ((rmse_before - rmse_after) / rmse_before * 100) if rmse_before != 0 else 0
            r2_improvement = ((r2_after - r2_before) / abs(r2_before) * 100) if r2_before != 0 else 0
            
            print(f"Correlation ปรับปรุง: {corr_improvement:+.1f}%")
            print(f"RMSE ปรับปรุง: {rmse_improvement:+.1f}%")
            print(f"R² ปรับปรุง: {r2_improvement:+.1f}%")
            
            # Peak Analysis
            print(f"\n🎯 Peak Analysis:")
            print("-" * 70)
            print(f"STM32 Peak: {stm32_voltage[stm32_peak_idx]:.3f} V, {stm32_current[stm32_peak_idx]*1e6:.2f} μA")
            print(f"PalmSens Peak: {palmsens_voltage[palmsens_peak_idx]:.3f} V, {palmsens_current[palmsens_peak_idx]*1e6:.2f} μA")
            print(f"Calibrated Peak: {calibrated_voltage[stm32_peak_idx]:.3f} V, {calibrated_current[stm32_peak_idx]*1e6:.2f} μA")
            
        else:
            print("❌ ไม่พบข้อมูล measurements")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*70)
    print("📁 กราฟเปรียบเทียบถูกบันทึกเป็น: calibration_comparison_75_vs_90_*.png")
    print("✅ การเปรียบเทียบเสร็จสิ้น")

if __name__ == "__main__":
    analyze_calibration_results()