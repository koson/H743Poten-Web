#!/usr/bin/env python3
"""
PLS Workflow Simple - ทดสอบการอ่านข้อมูลและแยก concentration/scan rate
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re

def extract_metadata_from_filename(filename):
    """แยก concentration และ scan rate จาก filename"""
    filename_lower = filename.lower()
    
    # Pattern สำหรับ concentration
    concentration = None
    
    # Palmsens format: Palmsens_0.5mM_...
    conc_match = re.search(r'palmsens[_\s]*(\d+\.?\d*)\s*mm', filename_lower)
    if conc_match:
        concentration = float(conc_match.group(1))
    
    # STM32 format: Pipot_Ferro_0_5mM_... หรือ Pipot_Ferro_1_0mM_...
    if concentration is None:
        conc_match = re.search(r'pipot[_\s]*ferro[_\s]*(\d+)[_\s]*(\d+)[_\s]*mm', filename_lower)
        if conc_match:
            major = int(conc_match.group(1))
            minor = int(conc_match.group(2))
            concentration = major + minor / 10.0
    
    # Pattern สำหรับ scan rate
    scan_rate = None
    scan_match = re.search(r'(\d+\.?\d*)\s*mv[\/\s]*p?s', filename_lower)
    if scan_match:
        scan_rate = float(scan_match.group(1))
    
    return concentration, scan_rate

def load_palmsens_csv(filepath):
    """โหลดไฟล์ CSV ของ Palmsens"""
    try:
        # อ่านไฟล์โดยข้าม 2 บรรทัดแรก (ชื่อไฟล์ + header)
        data = pd.read_csv(filepath, skiprows=2, names=['voltage', 'current'])
        
        # ตรวจสอบข้อมูล
        if len(data) == 0:
            print(f"❌ ไฟล์ว่าง: {filepath}")
            return None
            
        # ตรวจสอบว่าข้อมูลเป็นตัวเลข
        if not (pd.api.types.is_numeric_dtype(data['voltage']) and 
                pd.api.types.is_numeric_dtype(data['current'])):
            print(f"❌ ข้อมูลไม่ใช่ตัวเลข: {filepath}")
            return None
            
        return data
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return None

def scan_palmsens_data():
    """สแกนข้อมูล Palmsens"""
    palmsens_dir = Path("Test_data/Palmsens")
    
    if not palmsens_dir.exists():
        print("❌ ไม่พบโฟลเดอร์ Test_data/Palmsens")
        return
    
    # สร้างตารางสรุปข้อมูล
    concentrations = set()
    scan_rates = set()
    data_summary = []
    
    print("🔍 สแกนข้อมูล Palmsens...")
    
    # สแกนทุกโฟลเดอร์ความเข้มข้น
    for conc_folder in palmsens_dir.iterdir():
        if not conc_folder.is_dir():
            continue
            
        print(f"📂 {conc_folder.name}")
        
        # สแกนไฟล์ CSV ในโฟลเดอร์
        csv_files = list(conc_folder.glob("*.csv"))
        
        for csv_file in csv_files[:3]:  # ดูแค่ 3 ไฟล์แรกเพื่อประหยัดเวลา
            concentration, scan_rate = extract_metadata_from_filename(csv_file.name)
            
            if concentration is not None and scan_rate is not None:
                concentrations.add(concentration)
                scan_rates.add(scan_rate)
                
                # โหลดข้อมูล CV
                cv_data = load_palmsens_csv(csv_file)
                if cv_data is not None:
                    data_summary.append({
                        'filename': csv_file.name,
                        'concentration': concentration,
                        'scan_rate': scan_rate,
                        'voltage_range': f"{cv_data['voltage'].min():.2f} to {cv_data['voltage'].max():.2f}",
                        'current_range': f"{cv_data['current'].min():.2f} to {cv_data['current'].max():.2f}",
                        'data_points': len(cv_data)
                    })
                    
                    print(f"   ✅ {csv_file.name}: {concentration}mM @ {scan_rate}mV/s")
    
    # สร้างสรุปผล
    print(f"\n📊 สรุปข้อมูล Palmsens:")
    print(f"   🧪 Concentrations: {sorted(concentrations)} mM")
    print(f"   ⚡ Scan rates: {sorted(scan_rates)} mV/s")
    print(f"   📁 ไฟล์ที่อ่านได้: {len(data_summary)} ไฟล์")
    
    # สร้างตารางความเข้มข้น vs อัตราการสแกน
    print(f"\n📋 ตารางความพร้อมของข้อมูล:")
    print("Conc\\Scan", end="")
    for sr in sorted(scan_rates):
        print(f"\t{sr}", end="")
    print()
    
    for conc in sorted(concentrations):
        print(f"{conc}", end="")
        for sr in sorted(scan_rates):
            # นับว่ามีข้อมูลหรือไม่
            has_data = any(d['concentration'] == conc and d['scan_rate'] == sr 
                          for d in data_summary)
            print(f"\t{'✅' if has_data else '❌'}", end="")
        print()
    
    return data_summary, sorted(concentrations), sorted(scan_rates)

if __name__ == "__main__":
    print("🚀 PLS Workflow Simple - ทดสอบการอ่านข้อมูล")
    print("=" * 50)
    
    data_summary, concentrations, scan_rates = scan_palmsens_data()
    
    print(f"\n✅ เสร็จสิ้นการสแกน!")
    print(f"   พบความเข้มข้น: {len(concentrations)} ระดับ")
    print(f"   พบอัตราการสแกน: {len(scan_rates)} ระดับ")
    print(f"   ไฟล์ที่ประมวลผล: {len(data_summary)} ไฟล์")
