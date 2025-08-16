#!/usr/bin/env python3
"""
CSV Header Correction Tool
แก้ไข header จาก uA เป็น A สำหรับไฟล์ STM32H743 และวิเคราะห์ magnitude ใหม่
"""

import pandas as pd
import numpy as np
from pathlib import Path
import shutil
import os
from datetime import datetime

class CSVHeaderCorrector:
    """แก้ไข header ของไฟล์ CSV และวิเคราะห์ magnitude"""
    
    def __init__(self):
        self.base_path = Path("validation_data")
        self.stm32_path = self.base_path / "reference_cv_data" / "stm32h743"
        self.backup_path = self.base_path / "backup" / f"stm32h743_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def analyze_magnitude_before_correction(self):
        """วิเคราะห์ magnitude ก่อนแก้ไข"""
        print("🔍 การวิเคราะห์ magnitude ก่อนแก้ไข header")
        print("=" * 60)
        
        # อ่านไฟล์ตัวอย่างจาก STM32H743
        stm32_files = list(self.stm32_path.glob("*.csv"))[:5]  # ตัวอย่าง 5 ไฟล์
        
        print(f"📊 วิเคราะห์ไฟล์ STM32H743 ตัวอย่าง:")
        
        stm32_magnitudes = []
        for file_path in stm32_files:
            try:
                # อ่านข้อมูลโดยข้าม header บรรทัดแรก
                df = pd.read_csv(file_path, skiprows=1)
                if 'uA' in df.columns:
                    current_data = df['uA'].values
                    magnitude_range = [np.min(current_data), np.max(current_data)]
                    stm32_magnitudes.extend([abs(magnitude_range[0]), abs(magnitude_range[1])])
                    
                    print(f"   {file_path.name}:")
                    print(f"     Current range: {magnitude_range[0]:.2e} to {magnitude_range[1]:.2e} (labeled as uA)")
                    print(f"     Magnitude order: ~{np.log10(max(abs(magnitude_range[0]), abs(magnitude_range[1]))):.1f}")
                    
            except Exception as e:
                print(f"   ❌ Error reading {file_path.name}: {e}")
        
        # เปรียบเทียบกับ PalmSens
        palmsens_path = self.base_path / "reference_cv_data" / "palmsens"
        palmsens_files = list(palmsens_path.glob("*.csv"))[:3]
        
        print(f"\n📊 เปรียบเทียบกับ PalmSens:")
        palmsens_magnitudes = []
        
        for file_path in palmsens_files:
            try:
                df = pd.read_csv(file_path, skiprows=1)
                if 'uA' in df.columns:
                    current_data = df['uA'].values
                    magnitude_range = [np.min(current_data), np.max(current_data)]
                    palmsens_magnitudes.extend([abs(magnitude_range[0]), abs(magnitude_range[1])])
                    
                    print(f"   {file_path.name}:")
                    print(f"     Current range: {magnitude_range[0]:.2e} to {magnitude_range[1]:.2e} uA")
                    print(f"     Magnitude order: ~{np.log10(max(abs(magnitude_range[0]), abs(magnitude_range[1]))):.1f}")
                    
            except Exception as e:
                print(f"   ❌ Error reading {file_path.name}: {e}")
        
        # คำนวณอัตราส่วน
        if stm32_magnitudes and palmsens_magnitudes:
            avg_stm32 = np.mean(stm32_magnitudes)
            avg_palmsens = np.mean(palmsens_magnitudes)
            
            print(f"\n📈 การเปรียบเทียบ magnitude:")
            print(f"   STM32H743 average magnitude: {avg_stm32:.2e} (labeled as uA)")
            print(f"   PalmSens average magnitude: {avg_palmsens:.2e} uA")
            print(f"   Ratio (PalmSens/STM32): {avg_palmsens/avg_stm32:.2e}")
            
            # ถ้าแก้ไขจาก uA เป็น A สำหรับ STM32
            stm32_as_ampere = avg_stm32  # ถือว่าเป็น A
            stm32_as_microampere = avg_stm32 * 1e6  # แปลงเป็น uA
            
            print(f"\n🔄 ถ้าแก้ไขหน่วย STM32H743 จาก uA เป็น A:")
            print(f"   STM32H743 ในหน่วย A: {stm32_as_ampere:.2e} A")
            print(f"   STM32H743 แปลงเป็น uA: {stm32_as_microampere:.2e} uA")
            print(f"   อัตราส่วนใหม่ (PalmSens/STM32): {avg_palmsens/stm32_as_microampere:.2f}")
            
            if 0.1 <= avg_palmsens/stm32_as_microampere <= 10:
                print(f"   ✅ อัตราส่วนสมเหตุสมผล! STM32H743 น่าจะเป็นหน่วย A")
            else:
                print(f"   ⚠️  อัตราส่วนยังไม่สมเหตุสมผล")
    
    def backup_files(self):
        """สำรองไฟล์ก่อนแก้ไข"""
        print(f"\n💾 สำรองไฟล์ไปที่: {self.backup_path}")
        
        # สร้างโฟลเดอร์ backup
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        # Copy ไฟล์ทั้งหมด
        stm32_files = list(self.stm32_path.glob("*.csv"))
        for file_path in stm32_files:
            backup_file = self.backup_path / file_path.name
            shutil.copy2(file_path, backup_file)
        
        print(f"   ✅ สำรองไฟล์แล้ว {len(stm32_files)} ไฟล์")
        return len(stm32_files)
    
    def correct_headers(self, dry_run=True):
        """แก้ไข header จาก uA เป็น A"""
        print(f"\n🔧 {'[DRY RUN] ' if dry_run else ''}แก้ไข header ไฟล์ STM32H743")
        print("=" * 60)
        
        stm32_files = list(self.stm32_path.glob("*.csv"))
        corrected_count = 0
        error_count = 0
        
        for i, file_path in enumerate(stm32_files):
            try:
                # อ่านไฟล์
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                
                if len(lines) >= 2:
                    # ตรวจสอบ header บรรทัดที่ 2
                    header_line = lines[1].strip()
                    
                    if header_line == "V,uA":
                        # แก้ไข header
                        lines[1] = "V,A\n"
                        corrected_count += 1
                        
                        if not dry_run:
                            # เขียนไฟล์ใหม่
                            with open(file_path, 'w') as f:
                                f.writelines(lines)
                        
                        if i < 5:  # แสดงตัวอย่าง 5 ไฟล์แรก
                            print(f"   ✅ {file_path.name}: V,uA → V,A")
                    else:
                        if i < 5:
                            print(f"   ⏭️  {file_path.name}: header = '{header_line}' (ไม่ต้องแก้)")
                else:
                    print(f"   ❌ {file_path.name}: ไฟล์มีบรรทัดไม่เพียงพอ")
                    error_count += 1
                    
            except Exception as e:
                print(f"   ❌ {file_path.name}: Error - {e}")
                error_count += 1
        
        print(f"\n📊 สรุปผลการแก้ไข:")
        print(f"   ✅ แก้ไขแล้ว: {corrected_count} ไฟล์")
        print(f"   ⏭️  ไม่ต้องแก้: {len(stm32_files) - corrected_count - error_count} ไฟล์")
        print(f"   ❌ Error: {error_count} ไฟล์")
        
        return corrected_count, error_count
    
    def analyze_magnitude_after_correction(self):
        """วิเคราะห์ magnitude หลังแก้ไข"""
        print(f"\n🔍 การวิเคราะห์ magnitude หลังแก้ไข header")
        print("=" * 60)
        
        # อ่านไฟล์ตัวอย่างจาก STM32H743
        stm32_files = list(self.stm32_path.glob("*.csv"))[:5]
        
        print(f"📊 ข้อมูล STM32H743 หลังแก้ไข (หน่วย A):")
        stm32_magnitudes = []
        
        for file_path in stm32_files:
            try:
                df = pd.read_csv(file_path, skiprows=1)
                if 'A' in df.columns:
                    current_data = df['A'].values
                    magnitude_range = [np.min(current_data), np.max(current_data)]
                    stm32_magnitudes.extend([abs(magnitude_range[0]), abs(magnitude_range[1])])
                    
                    # แปลงเป็น µA เพื่อเปรียบเทียบ
                    magnitude_range_ua = [x * 1e6 for x in magnitude_range]
                    
                    print(f"   {file_path.name}:")
                    print(f"     Current (A): {magnitude_range[0]:.2e} to {magnitude_range[1]:.2e}")
                    print(f"     Current (µA): {magnitude_range_ua[0]:.2f} to {magnitude_range_ua[1]:.2f}")
                    
            except Exception as e:
                print(f"   ❌ Error reading {file_path.name}: {e}")
        
        # เปรียบเทียบกับ PalmSens
        palmsens_path = self.base_path / "reference_cv_data" / "palmsens"
        palmsens_files = list(palmsens_path.glob("*.csv"))[:3]
        
        print(f"\n📊 เปรียบเทียบกับ PalmSens:")
        palmsens_magnitudes = []
        
        for file_path in palmsens_files:
            try:
                df = pd.read_csv(file_path, skiprows=1)
                if 'uA' in df.columns:
                    current_data = df['uA'].values
                    magnitude_range = [np.min(current_data), np.max(current_data)]
                    palmsens_magnitudes.extend([abs(magnitude_range[0]), abs(magnitude_range[1])])
                    
                    print(f"   {file_path.name}:")
                    print(f"     Current (µA): {magnitude_range[0]:.2f} to {magnitude_range[1]:.2f}")
                    
            except Exception as e:
                print(f"   ❌ Error reading {file_path.name}: {e}")
        
        # คำนวณอัตราส่วนใหม่
        if stm32_magnitudes and palmsens_magnitudes:
            avg_stm32_ampere = np.mean(stm32_magnitudes)
            avg_stm32_microampere = avg_stm32_ampere * 1e6
            avg_palmsens = np.mean(palmsens_magnitudes)
            
            print(f"\n📈 การเปรียบเทียบ magnitude หลังแก้ไข:")
            print(f"   STM32H743: {avg_stm32_ampere:.2e} A = {avg_stm32_microampere:.2f} µA")
            print(f"   PalmSens: {avg_palmsens:.2f} µA")
            print(f"   อัตราส่วน (PalmSens/STM32): {avg_palmsens/avg_stm32_microampere:.2f}")
            
            if 0.1 <= avg_palmsens/avg_stm32_microampere <= 10:
                print(f"   ✅ อัตราส่วนสมเหตุสมผล! ข้อมูลใกล้เคียงกัน")
                print(f"   🎯 STM32H743 และ PalmSens ให้ผลที่เปรียบเทียบได้")
            else:
                print(f"   ⚠️  อัตราส่วนยังคงแปลก อาจต้องตรวจสอบเพิ่มเติม")

def main():
    corrector = CSVHeaderCorrector()
    
    print("🔧 CSV Header Correction Tool")
    print("แก้ไข header ไฟล์ STM32H743 จาก uA เป็น A")
    print("=" * 70)
    
    # วิเคราะห์ก่อนแก้ไข
    corrector.analyze_magnitude_before_correction()
    
    # ทำ Dry Run เพื่อดูผลลัพธ์
    print(f"\n🧪 ทำ Dry Run ก่อน...")
    corrected, errors = corrector.correct_headers(dry_run=True)
    
    if corrected > 0:
        print(f"\n❓ พบไฟล์ที่ต้องแก้ไข {corrected} ไฟล์")
        print(f"   ต้องการดำเนินการแก้ไขจริงหรือไม่? (y/n): ", end="")
        
        # สำหรับการใช้งานแบบ interactive
        import sys
        if sys.stdin.isatty():
            choice = input().strip().lower()
        else:
            choice = "y"  # Default ให้แก้ไขเมื่อไม่ใช่ interactive mode
        
        if choice in ['y', 'yes', '']:
            print(f"\n💾 สำรองไฟล์และแก้ไขจริง...")
            backup_count = corrector.backup_files()
            
            if backup_count > 0:
                corrected, errors = corrector.correct_headers(dry_run=False)
                if corrected > 0:
                    corrector.analyze_magnitude_after_correction()
                    
                    # อัพเดทเอกสาร
                    print(f"\n📝 ขั้นตอนต่อไป:")
                    print(f"   1. ✅ แก้ไข CSV headers เสร็จแล้ว")
                    print(f"   2. 📝 อัพเดทเอกสาร DATA_SPLITTING_STRATEGY.md")
                    print(f"   3. 🔄 รัน validation ใหม่เพื่อประเมิน magnitude ที่ถูกต้อง")
        else:
            print(f"\n❌ ยกเลิกการแก้ไข")
    else:
        print(f"\n✅ ไม่พบไฟล์ที่ต้องแก้ไข")

if __name__ == "__main__":
    main()
