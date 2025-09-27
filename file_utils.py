#!/usr/bin/env python3
"""
ระบบจัดการไฟล์สำหรับ PyPiPo - แยกโฟลเดอร์สำหรับเก็บ data และ plots
"""

import os
import datetime
import platform

def get_data_root_folder():
    """กำหนดโฟลเดอร์หลักสำหรับเก็บข้อมูล - นอกโฟลเดอร์โค้ด"""
    # โฟลเดอร์หลัก - แยกตาม OS
    if platform.system() == 'Windows':
        # Windows: เก็บที่ Documents\PyPiPo_Data
        docs_folder = os.path.join(os.path.expanduser('~'), 'Documents')
        root_folder = os.path.join(docs_folder, 'PyPiPo_Data')
    else:
        # Linux/Mac: เก็บที่ ~/PyPiPo_Data
        root_folder = os.path.join(os.path.expanduser('~'), 'PyPiPo_Data')
    
    return root_folder

def ensure_directory_exists(directory):
    """สร้างโฟลเดอร์ถ้ายังไม่มี"""
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            print(f"Created directory: {directory}")
            return True
        except Exception as e:
            print(f"Error creating directory {directory}: {e}")
            return False
    return True

def get_technique_directory(technique, file_type='data'):
    """
    สร้างโครงสร้างโฟลเดอร์สำหรับแต่ละเทคนิค
    technique: 'CV', 'SWV', 'DPV', etc.
    file_type: 'data' (CSV) หรือ 'plots' (PNG)
    """
    # โฟลเดอร์หลัก
    root_folder = get_data_root_folder()
    
    # วันที่ปัจจุบัน
    today = datetime.datetime.now()
    date_string = today.strftime("%Y-%m-%d")
    
    # โครงสร้างโฟลเดอร์: PyPiPo_Data/{technique}/{file_type}/{YYYY-MM-DD}/
    technique_dir = os.path.join(root_folder, technique.upper(), file_type, date_string)
    
    # สร้างโฟลเดอร์ (รวมทั้ง parent directories)
    ensure_directory_exists(technique_dir)
    
    return technique_dir

def get_save_path_for_file(technique, filename, file_type='data', use_external=True):
    """
    สร้าง path สำหรับบันทึกไฟล์
    technique: 'CV', 'SWV', 'DPV', etc.
    filename: ชื่อไฟล์พร้อมนามสกุล
    file_type: 'data' (CSV) หรือ 'plots' (PNG)
    use_external: ถ้า False จะเก็บในโฟลเดอร์ปัจจุบัน
    """
    if not use_external:
        # เก็บในโฟลเดอร์ปัจจุบัน
        return filename
        
    # สร้างโฟลเดอร์และได้ path
    save_dir = get_technique_directory(technique, file_type)
    
    # สร้าง path เต็ม
    return os.path.join(save_dir, filename)
