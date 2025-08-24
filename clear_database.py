#!/usr/bin/env python3
"""
ล้าง Database และเริ่มใหม่สำหรับแก้ปัญหาหน่วยกระแส
"""

import os
import sqlite3
from datetime import datetime

def backup_and_clear_database():
    """สำรองและล้าง database"""
    db_path = 'data_logs/parameter_log.db'
    
    if os.path.exists(db_path):
        # สำรองไฟล์เดิม
        backup_path = f'data_logs/parameter_log_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ สำรองฐานข้อมูลเป็น: {backup_path}")
        
        # ลบไฟล์เดิม
        os.remove(db_path)
        print(f"🗑️ ลบ database เดิม: {db_path}")
        
        return True
    else:
        print("❌ ไม่พบไฟล์ database")
        return False

def main():
    print("🚀 ล้าง Database เพื่อแก้ปัญหาหน่วยกระแส")
    print("="*50)
    print("⚠️  ข้อมูลทั้งหมดใน database จะถูกลบ!")
    print("📋 คุณจะต้อง:")
    print("   1. เรียกใช้ Peak Analysis ใหม่")
    print("   2. Save Analysis Parameters ใหม่")
    print("   3. ตรวจสอบหน่วยให้ถูกต้อง")
    print("="*50)
    
    response = input("❓ ยืนยันการล้าง database? (y/n): ").strip().lower()
    
    if response == 'y':
        if backup_and_clear_database():
            print("\n✅ ล้าง database เสร็จสิ้น")
            print("🔄 กรุณาทำตามขั้นตอนต่อไปนี้:")
            print("   1. เปิดหน้าเว็บ Peak Analysis")
            print("   2. อัปโหลดไฟล์ CSV ใหม่")
            print("   3. ตรวจสอบหน่วยให้ถูกต้อง:")
            print("      - STM32: แปลงจาก A เป็น µA")
            print("      - PalmSens: ใช้ µA ตามเดิม")
            print("   4. Save Analysis Parameters")
            print("   5. ทำการเปรียบเทียบ calibration ใหม่")
        else:
            print("❌ ไม่สามารถล้าง database ได้")
    else:
        print("❌ ยกเลิกการล้าง database")

if __name__ == "__main__":
    main()