#!/usr/bin/env python3
"""
แก้ไขหน่วยกระแสของ STM32 ใน Database (Auto mode)
"""

import sqlite3
import json
import os
from datetime import datetime

def fix_current_units():
    """แก้ไขหน่วยกระแสของ STM32 โดยอัตโนมัติ"""
    db_path = 'data_logs/parameter_log.db'
    backup_path = f'data_logs/parameter_log_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    # สำรองฐานข้อมูล
    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ สำรองฐานข้อมูลเป็น: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 กำลังแก้ไขหน่วยกระแสของ STM32...")
    print("="*60)
    
    # ดึงข้อมูล STM32 ทั้งหมด
    cursor.execute("""
        SELECT id, raw_data_json 
        FROM measurements 
        WHERE instrument_type = 'stm32'
    """)
    stm32_measurements = cursor.fetchall()
    
    fixed_count = 0
    for measurement_id, raw_data_json in stm32_measurements:
        try:
            data = json.loads(raw_data_json)
            
            if 'cv_data' not in data:
                print(f"⚠️ ID {measurement_id}: ไม่มี cv_data, ข้าม")
                continue
                
            cv_data = data['cv_data']
            
            # แสดงข้อมูลก่อนแก้ไข
            old_current_range = [point[1] for point in cv_data]
            old_min = min(old_current_range)
            old_max = max(old_current_range)
            
            # แปลงหน่วยจาก A เป็น µA (คูณ 1,000,000)
            new_cv_data = []
            for voltage, current in cv_data:
                new_current = current * 1e6  # A → µA
                new_cv_data.append([voltage, new_current])
            
            data['cv_data'] = new_cv_data
            new_raw_data_json = json.dumps(data)
            
            new_current_range = [point[1] for point in new_cv_data]
            new_min = min(new_current_range)
            new_max = max(new_current_range)
            
            print(f"ID {measurement_id:3d}: {old_min:.2e} A → {new_min:.2e} µA")
            print(f"        : {old_max:.2e} A → {new_max:.2e} µA")
            
            # อัปเดตฐานข้อมูล
            cursor.execute("""
                UPDATE measurements 
                SET raw_data_json = ?, 
                    analysis_timestamp = ?
                WHERE id = ?
            """, (new_raw_data_json, datetime.now(), measurement_id))
            
            fixed_count += 1
            
        except Exception as e:
            print(f"❌ Error processing ID {measurement_id}: {e}")
    
    conn.commit()
    print(f"\n✅ แก้ไขเสร็จสิ้น: {fixed_count} measurements")
    
    # ตรวจสอบผลการแก้ไข
    print("\n🔍 ตรวจสอบผลการแก้ไข...")
    print("="*60)
    
    cursor.execute("""
        SELECT id, instrument_type, sample_id, raw_data_json 
        FROM measurements 
        WHERE id IN (75, 90)
        ORDER BY id
    """)
    
    for row in cursor.fetchall():
        data = json.loads(row[3])
        cv_data = data['cv_data']
        current_values = [point[1] for point in cv_data]
        min_current = min(current_values)
        max_current = max(current_values)
        
        print(f"{row[1]:8s} ID {row[0]:3d}: {min_current:.2e} to {max_current:.2e} µA")
    
    conn.close()
    
    print("\n🎉 แก้ไขเสร็จสิ้น! ตอนนี้หน่วยกระแสของ STM32 และ PalmSens สอดคล้องกันแล้ว")
    return fixed_count

if __name__ == "__main__":
    print("🚀 แก้ไขหน่วยกระแสของ STM32 (Auto Mode)")
    print("="*60)
    
    fixed_count = fix_current_units()
    
    if fixed_count > 0:
        print("\n💡 ขั้นตอนต่อไป:")
        print("   1. ทดสอบการเปรียบเทียบ calibration ใหม่")
        print("   2. ตรวจสอบผลลัพธ์ว่าสมเหตุสมผล")
        print("   3. หากผลลัพธ์ดี สามารถใช้งานต่อได้")
    else:
        print("❌ ไม่มีข้อมูลที่ต้องแก้ไข")