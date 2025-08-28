#!/usr/bin/env python3
"""
Convert PiPot CSV files from Amperes (A) to microAmps (µA)
แปลงไฟล์ CSV ของ PiPot จากหน่วย A เป็น µA โดยคูณด้วย 1e6
"""

import os
import glob
import shutil
from pathlib import Path

def convert_pipot_file(file_path):
    """Convert single PiPot file from A to µA"""
    try:
        print(f"Converting: {file_path}")
        
        # อ่านไฟล์ต้นฉบับ
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # ตรวจสอบว่าเป็นไฟล์ PiPot (มี FileName: header และ V,A)
        if len(lines) < 2:
            print(f"  ⚠️  Skipped: File too short")
            return False
            
        if not lines[0].strip().startswith('FileName:'):
            print(f"  ⚠️  Skipped: Not PiPot format (no FileName header)")
            return False
            
        if lines[1].strip().lower() != 'v,a':
            print(f"  ⚠️  Skipped: Not A units (header: {lines[1].strip()})")
            return False
        
        # สำรองไฟล์เดิม
        backup_path = file_path + '.backup'
        if not os.path.exists(backup_path):
            shutil.copy2(file_path, backup_path)
            print(f"  📁 Backup created: {backup_path}")
        
        # แปลงข้อมูล
        converted_lines = []
        converted_lines.append(lines[0])  # FileName line
        converted_lines.append('V,uA\n')  # เปลี่ยน header จาก V,A เป็น V,uA
        
        data_converted = 0
        for i, line in enumerate(lines[2:], start=2):
            line = line.strip()
            if not line:
                converted_lines.append('\n')
                continue
                
            try:
                parts = line.split(',')
                if len(parts) >= 2:
                    voltage = float(parts[0])
                    current_A = float(parts[1])
                    current_uA = current_A * 1e6  # Convert A to µA
                    
                    # เขียนข้อมูลใหม่
                    converted_lines.append(f'{voltage},{current_uA}\n')
                    data_converted += 1
                else:
                    converted_lines.append(line + '\n')
                    
            except ValueError as e:
                print(f"  ⚠️  Line {i}: Could not convert '{line}' - {e}")
                converted_lines.append(line + '\n')
        
        # เขียนไฟล์ใหม่
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(converted_lines)
        
        print(f"  ✅ Converted {data_converted} data points")
        print(f"  📝 Header changed: V,A → V,uA")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Convert all PiPot files in Test_data/Stm32"""
    
    print("🔄 PiPot Unit Converter: A → µA")
    print("=" * 50)
    
    # หาไฟล์ PiPot ทั้งหมด
    pipot_pattern = "Test_data/Stm32/**/*.csv"
    all_csv_files = glob.glob(pipot_pattern, recursive=True)
    
    # กรองไฟล์ backup ออก (ไฟล์ที่ลงท้ายด้วย .backup)
    pipot_files = [f for f in all_csv_files if not f.endswith('.backup')]
    
    if not pipot_files:
        print("❌ No PiPot files found!")
        return
    
    print(f"📁 Found {len(pipot_files)} potential PiPot files (excluding .backup files)")
    if len(all_csv_files) > len(pipot_files):
        print(f"📁 Filtered out {len(all_csv_files) - len(pipot_files)} backup files")
    print()
    
    # สถิติ
    converted_count = 0
    skipped_count = 0
    error_count = 0
    
    # แปลงทีละไฟล์
    for file_path in pipot_files:
        try:
            result = convert_pipot_file(file_path)
            if result:
                converted_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            print(f"❌ Fatal error with {file_path}: {e}")
            error_count += 1
        print()
    
    # สรุปผล
    print("=" * 50)
    print("📊 CONVERSION SUMMARY")
    print(f"✅ Converted: {converted_count} files")
    print(f"⚠️  Skipped: {skipped_count} files")
    print(f"❌ Errors: {error_count} files")
    print(f"📁 Total processed: {len(pipot_files)} files")
    
    if converted_count > 0:
        print("\n🎉 SUCCESS! PiPot files converted from A to µA")
        print("💾 Original files backed up with .backup extension")
        print("⚠️  Remember to update any hardcoded unit conversions in code!")
    
    print("\n🔍 Next steps:")
    print("1. Test a few converted files to ensure they look correct")
    print("2. Update backend code to treat PiPot files as µA units")
    print("3. Remove the 1e6 multiplication for PiPot files in peak_detection.py")

if __name__ == "__main__":
    main()