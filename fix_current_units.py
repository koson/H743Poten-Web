#!/usr/bin/env python3
"""
แก้ไขหน่วยกระแสของ STM32 ใน Database
แปลงจาก A เป็น µA เพื่อให้สอดคล้องกับ PalmSens
"""

import sqlite3
import json
import os
from datetime import datetime

class CurrentUnitFixer:
    def __init__(self):
        self.db_path = 'data_logs/parameter_log.db'
        self.backup_path = f'data_logs/parameter_log_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    def backup_database(self):
        """สำรองฐานข้อมูลก่อนแก้ไข"""
        if os.path.exists(self.db_path):
            import shutil
            shutil.copy2(self.db_path, self.backup_path)
            print(f"✅ สำรองฐานข้อมูลเป็น: {self.backup_path}")
            return True
        return False
    
    def analyze_measurements(self):
        """วิเคราะห์ข้อมูลใน database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("🔍 วิเคราะห์ข้อมูลใน Database...")
        print("="*60)
        
        # ดึงข้อมูล STM32
        cursor.execute("""
            SELECT id, sample_id, raw_data_json 
            FROM measurements 
            WHERE instrument_type = 'stm32' 
            ORDER BY id DESC 
            LIMIT 5
        """)
        stm32_data = cursor.fetchall()
        
        # ดึงข้อมูล PalmSens
        cursor.execute("""
            SELECT id, sample_id, raw_data_json 
            FROM measurements 
            WHERE instrument_type = 'palmsens' 
            ORDER BY id DESC 
            LIMIT 5
        """)
        palmsens_data = cursor.fetchall()
        
        print("🔴 STM32 Measurements (หน่วย A ที่ต้องแปลงเป็น µA):")
        for row in stm32_data:
            data = json.loads(row[2])
            cv_data = data['cv_data']
            current_sample = [point[1] for point in cv_data[:5]]
            print(f"  ID {row[0]:3d}: {min(current_sample):.2e} to {max(current_sample):.2e} A")
        
        print("\n🔵 PalmSens Measurements (หน่วย µA ที่ถูกต้องแล้ว):")
        for row in palmsens_data:
            data = json.loads(row[2])
            cv_data = data['cv_data']
            current_sample = [point[1] for point in cv_data[:5]]
            print(f"  ID {row[0]:3d}: {min(current_sample):.2e} to {max(current_sample):.2e} µA")
        
        conn.close()
        return len(stm32_data)
    
    def fix_stm32_units(self, dry_run=True):
        """แก้ไขหน่วยกระแสของ STM32"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print(f"\n{'🔧 ทดสอบ' if dry_run else '🔧 แก้ไข'} หน่วยกระแสของ STM32...")
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
                
                if not dry_run:
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
        
        if not dry_run:
            conn.commit()
            print(f"\n✅ แก้ไขเสร็จสิ้น: {fixed_count} measurements")
        else:
            print(f"\n📊 จะแก้ไข: {fixed_count} measurements")
        
        conn.close()
        return fixed_count
    
    def verify_fix(self):
        """ตรวจสอบผลการแก้ไข"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("\n🔍 ตรวจสอบผลการแก้ไข...")
        print("="*60)
        
        # ตรวจสอบ STM32 vs PalmSens
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

def main():
    print("🚀 เครื่องมือแก้ไขหน่วยกระแสของ STM32")
    print("="*60)
    
    fixer = CurrentUnitFixer()
    
    # 1. สำรองฐานข้อมูล
    if not fixer.backup_database():
        print("❌ ไม่สามารถสำรองฐานข้อมูลได้")
        return
    
    # 2. วิเคราะห์ข้อมูล
    count = fixer.analyze_measurements()
    if count == 0:
        print("❌ ไม่พบข้อมูล STM32 ในฐานข้อมูล")
        return
    
    # 3. ทดสอบการแก้ไข
    fixer.fix_stm32_units(dry_run=True)
    
    # 4. ขอยืนยันจากผู้ใช้
    response = input("\n❓ ต้องการแก้ไขข้อมูลจริงหรือไม่? (y/n): ").strip().lower()
    
    if response == 'y':
        # 5. แก้ไขจริง
        fixer.fix_stm32_units(dry_run=False)
        
        # 6. ตรวจสอบผล
        fixer.verify_fix()
        
        print("\n🎉 แก้ไขเสร็จสิ้น! ตอนนี้หน่วยกระแสของ STM32 และ PalmSens สอดคล้องกันแล้ว")
        print("💡 ลองรันการเปรียบเทียบ calibration ใหม่เพื่อดูผลลัพธ์ที่ถูกต้อง")
    else:
        print("❌ ยกเลิกการแก้ไข")

if __name__ == "__main__":
    main()