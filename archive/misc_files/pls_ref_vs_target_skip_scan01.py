#!/usr/bin/env python3
"""
PLS Analysis: Palmsens (Reference) vs STM32 (Target)
ข้าม scan_01 เพราะระบบยังไม่เสถียร (ใช้ scan_02 เป็นต้นไป)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cross_decomposition import PLSRegression
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import os
import glob
import re
from pathlib import Path
import time
from datetime import datetime
import json

def should_skip_file(filename):
    """Check if file should be skipped (scan_01 files)"""
    return 'scan_01' in filename.lower()

def filter_valid_files(file_list):
    """Filter out scan_01 files and keep only stable measurements"""
    valid_files = [f for f in file_list if not should_skip_file(str(f))]
    skipped_count = len(file_list) - len(valid_files)
    
    if skipped_count > 0:
        print(f"⚠️ ข้าม scan_01: {skipped_count} ไฟล์ (ระบบยังไม่เสถียร)")
        
    return valid_files

def extract_metadata_from_filename(filename):
    """แยกข้อมูล metadata จากชื่อไฟล์"""
    filename_only = Path(filename).stem
    
    # Example: "Palmsens_0.5mM_CV_100mVpS_E1_scan_02.csv"
    patterns = [
        r'(\w+)_([0-9.]+mM)_CV_([0-9.]+mVpS)_(\w+)_scan_(\d+)',
        r'(\w+)_([0-9.]+)mM_CV_([0-9.]+)mVs_(\w+)_scan_(\d+)',
        r'(\w+)_([0-9.]+mM)_([0-9.]+mVpS)_(\w+)_scan_(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename_only)
        if match:
            groups = match.groups()
            device = groups[0]
            concentration_str = groups[1]
            scan_rate_str = groups[2]
            electrode = groups[3]
            scan_number = groups[4]
            
            # Extract numeric values
            conc_match = re.search(r'([0-9.]+)', concentration_str)
            concentration = float(conc_match.group(1)) if conc_match else 0.0
            
            rate_match = re.search(r'([0-9.]+)', scan_rate_str)
            scan_rate = float(rate_match.group(1)) if rate_match else 0.0
            
            return {
                'device': device,
                'concentration': concentration,
                'scan_rate': scan_rate,
                'electrode': electrode,
                'scan_number': int(scan_number),
                'filename': filename_only
            }
    
    return {
        'device': 'unknown',
        'concentration': 0.0,
        'scan_rate': 0.0,
        'electrode': 'unknown',
        'scan_number': 1,
        'filename': filename_only
    }

def analyze_cv_file_enhanced_v4(filepath, detector):
    """วิเคราะห์ไฟล์ CV ด้วย Enhanced V4 Improved"""
    try:
        # โหลดไฟล์ (skip 2 header rows)
        data = pd.read_csv(filepath, skiprows=2, names=['voltage', 'current'])
        
        if data.empty or len(data) < 10:
            return None
        
        # เตรียมข้อมูลสำหรับ Enhanced V4 Improved
        cv_data = {
            'voltage': data['voltage'].tolist(),
            'current': data['current'].tolist()
        }
        
        # วิเคราะห์ด้วย Enhanced V4 Improved
        results = detector.analyze_cv_data(cv_data)
        
        if not results or not isinstance(results, dict):
            return None
        
        # แยก peaks
        all_peaks = results.get('peaks', [])
        if not all_peaks:
            return None
        
        anodic_peaks = [p for p in all_peaks if p.get('type') == 'oxidation']
        cathodic_peaks = [p for p in all_peaks if p.get('type') == 'reduction']
        
        # ตรวจสอบว่ามี peak ครบทั้ง 2 ด้าน
        has_both_peaks = len(anodic_peaks) > 0 and len(cathodic_peaks) > 0
        
        if not has_both_peaks:
            return None
        
        # Extract metadata
        metadata = extract_metadata_from_filename(filepath.name)
        
        # Extract peak features
        ox_peak = anodic_peaks[0]  # ใช้ peak แรก
        red_peak = cathodic_peaks[0]  # ใช้ peak แรก
        
        peak_features = {
            'ox_voltage': ox_peak.get('voltage', 0),
            'ox_current': ox_peak.get('current', 0),
            'ox_confidence': ox_peak.get('confidence', 0),
            'red_voltage': red_peak.get('voltage', 0),
            'red_current': red_peak.get('current', 0),
            'red_confidence': red_peak.get('confidence', 0),
            
            # Derived features
            'peak_separation_voltage': abs(ox_peak.get('voltage', 0) - red_peak.get('voltage', 0)),
            'peak_separation_current': abs(ox_peak.get('current', 0) - red_peak.get('current', 0)),
            'current_ratio': ox_peak.get('current', 0) / red_peak.get('current', 0) if red_peak.get('current', 0) != 0 else 0,
            'midpoint_potential': (ox_peak.get('voltage', 0) + red_peak.get('voltage', 0)) / 2
        }
        
        return {
            'filename': filepath.name,
            'metadata': metadata,
            'peak_features': peak_features,
            'has_both_peaks': has_both_peaks,
            'peak_count': len(all_peaks)
        }
        
    except Exception as e:
        print(f"❌ Error analyzing {filepath.name}: {e}")
        return None

def collect_data_from_directory(data_dir, detector, device_name):
    """รวบรวมข้อมูลจากไดเรกทอรี (ข้าม scan_01)"""
    print(f"📁 สแกนข้อมูลใน {data_dir} ({device_name})...")
    
    if not os.path.exists(data_dir):
        print(f"❌ ไม่พบไดเรกทอรี: {data_dir}")
        return []
    
    # หาไฟล์ทั้งหมด
    pattern = os.path.join(data_dir, "**", "*.csv")
    all_files = [Path(f) for f in glob.glob(pattern, recursive=True)]
    
    # กรองไฟล์ (ข้าม scan_01)
    valid_files = filter_valid_files(all_files)
    
    print(f"📊 ไฟล์ทั้งหมด: {len(all_files)}, ใช้ได้: {len(valid_files)} (ข้าม scan_01: {len(all_files) - len(valid_files)})")
    
    # วิเคราะห์ไฟล์
    valid_data = []
    stats = {'total': 0, 'success': 0, 'failed': 0, 'both_peaks': 0}
    
    for i, filepath in enumerate(valid_files):
        print(f"[{i+1:2d}/{len(valid_files)}] {filepath.name}...", end=" ")
        
        stats['total'] += 1
        result = analyze_cv_file_enhanced_v4(filepath, detector)
        
        if result and result['has_both_peaks']:
            valid_data.append(result)
            stats['success'] += 1
            stats['both_peaks'] += 1
            
            pf = result['peak_features']
            print(f"✅ ox:{pf['ox_voltage']:.3f}V, red:{pf['red_voltage']:.3f}V, sep:{pf['peak_separation_voltage']:.3f}V")
        else:
            stats['failed'] += 1
            print("❌ no valid peaks")
    
    print(f"📈 {device_name} สรุป: {stats['success']}/{stats['total']} ไฟล์ใช้ได้ ({stats['success']/stats['total']*100:.1f}%)")
    
    return valid_data

def run_pls_analysis_ref_vs_target():
    """รัน PLS Analysis: Palmsens (ref) vs STM32 (target) - ข้าม scan_01"""
    print("🎯 PLS Analysis: Palmsens (REF) vs STM32 (TARGET)")
    print("⚠️ ข้าม scan_01 เพราะระบบยังไม่เสถียร")
    print("=" * 60)
    
    try:
        from enhanced_detector_v4_improved import EnhancedDetectorV4Improved
        print("✅ Enhanced V4 Improved พร้อมใช้งาน")
    except ImportError:
        print("❌ Enhanced V4 Improved ไม่พร้อมใช้งาน")
        return
    
    # สร้าง detector
    detector = EnhancedDetectorV4Improved(confidence_threshold=25.0)
    
    # กำหนด directories
    ref_dir = "Test_data/Palmsens"
    target_dir = "Test_data/Stm32"
    
    start_time = time.time()
    
    # รวบรวมข้อมูล Reference (Palmsens)
    print("\n🔬 รวบรวมข้อมูล Reference (Palmsens)...")
    ref_data = collect_data_from_directory(ref_dir, detector, "Palmsens")
    
    # รวบรวมข้อมูล Target (STM32)
    print("\n🎯 รวบรวมข้อมูล Target (STM32)...")
    target_data = collect_data_from_directory(target_dir, detector, "STM32")
    
    collection_time = time.time() - start_time
    print(f"\n⏱️ รวบรวมข้อมูลเสร็จใน {collection_time:.2f} วินาที")
    
    if not ref_data:
        print("❌ ไม่มีข้อมูล Reference (Palmsens)")
        return
    
    if not target_data:
        print("❌ ไม่มีข้อมูล Target (STM32)")
        return
    
    # สร้างรายงานสรุป
    print(f"\n📊 สรุปข้อมูลที่รวบรวมได้:")
    print(f"  Reference (Palmsens): {len(ref_data)} ไฟล์")
    print(f"  Target (STM32): {len(target_data)} ไฟล์")
    
    # แสดงการกระจายของความเข้มข้น
    ref_concentrations = [d['metadata']['concentration'] for d in ref_data]
    target_concentrations = [d['metadata']['concentration'] for d in target_data]
    
    print(f"  Palmsens ความเข้มข้น: {sorted(set(ref_concentrations))} mM")
    print(f"  STM32 ความเข้มข้น: {sorted(set(target_concentrations))} mM")
    
    # สร้าง DataFrame สำหรับ analysis
    create_pls_dataframes_and_analysis(ref_data, target_data)
    
    # Export ข้อมูล
    export_pls_data_with_labplot2(ref_data, target_data)
    
    print(f"\n🎉 PLS Analysis เสร็จสิ้น!")

def create_pls_dataframes_and_analysis(ref_data, target_data):
    """สร้าง DataFrame และวิเคราะห์ PLS"""
    print("\n📈 สร้าง PLS DataFrames และวิเคราะห์...")
    
    # สร้าง DataFrame สำหรับ Reference
    ref_rows = []
    for data in ref_data:
        row = data['metadata'].copy()
        row.update(data['peak_features'])
        row['device'] = 'Palmsens'
        ref_rows.append(row)
    
    ref_df = pd.DataFrame(ref_rows)
    
    # สร้าง DataFrame สำหรับ Target
    target_rows = []
    for data in target_data:
        row = data['metadata'].copy()
        row.update(data['peak_features'])
        row['device'] = 'STM32'
        target_rows.append(row)
    
    target_df = pd.DataFrame(target_rows)
    
    print(f"✅ Reference DataFrame: {len(ref_df)} samples")
    print(f"✅ Target DataFrame: {len(target_df)} samples")
    
    # แสดงสถิติพื้นฐาน
    print(f"\n📊 สถิติพื้นฐาน:")
    print(f"Palmsens - ความเข้มข้นเฉลี่ย: {ref_df['concentration'].mean():.2f}±{ref_df['concentration'].std():.2f} mM")
    print(f"STM32 - ความเข้มข้นเฉลี่ย: {target_df['concentration'].mean():.2f}±{target_df['concentration'].std():.2f} mM")
    
    # บันทึก DataFrames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    ref_path = f"pls_reference_palmsens_{timestamp}.csv"
    target_path = f"pls_target_stm32_{timestamp}.csv"
    
    ref_df.to_csv(ref_path, index=False)
    target_df.to_csv(target_path, index=False)
    
    print(f"📄 บันทึก Reference data: {ref_path}")
    print(f"📄 บันทึก Target data: {target_path}")
    
    return ref_df, target_df

def export_pls_data_with_labplot2(ref_data, target_data):
    """Export ข้อมูลในรูปแบบที่ LabPlot2 ใช้ได้"""
    print("\n📊 Export ข้อมูลสำหรับ LabPlot2...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Combined data for PLS analysis
    combined_data = []
    
    # Add reference data
    for data in ref_data:
        row = {
            'device': 'Palmsens',
            'device_code': 0,  # Numeric code for LabPlot2
            **data['metadata'],
            **data['peak_features']
        }
        combined_data.append(row)
    
    # Add target data  
    for data in target_data:
        row = {
            'device': 'STM32',
            'device_code': 1,  # Numeric code for LabPlot2
            **data['metadata'],
            **data['peak_features']
        }
        combined_data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(combined_data)
    
    # LabPlot2 compatible CSV with metadata
    labplot_filename = f"pls_data_labplot2_compatible_{timestamp}.csv"
    
    # Write with LabPlot2 metadata header
    with open(labplot_filename, 'w', encoding='utf-8') as f:
        # LabPlot2 metadata comments
        f.write("# LabPlot2 Data File\n")
        f.write("# PLS Analysis: Palmsens (Reference) vs STM32 (Target)\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n")
        f.write("# Method: Enhanced Detector V4 Improved\n")
        f.write("# Note: scan_01 files excluded (system not stable)\n")
        f.write("#\n")
        f.write("# Column descriptions:\n")
        f.write("# device: Device name (Palmsens/STM32)\n")
        f.write("# device_code: Numeric device code (0=Palmsens, 1=STM32)\n")
        f.write("# concentration: Ferrocyanide concentration (mM)\n")
        f.write("# scan_rate: CV scan rate (mV/s)\n")
        f.write("# ox_voltage: Oxidation peak voltage (V)\n")
        f.write("# ox_current: Oxidation peak current (µA)\n")
        f.write("# red_voltage: Reduction peak voltage (V)\n")
        f.write("# red_current: Reduction peak current (µA)\n")
        f.write("# peak_separation_voltage: |ox_voltage - red_voltage| (V)\n")
        f.write("# current_ratio: ox_current / red_current\n")
        f.write("# midpoint_potential: (ox_voltage + red_voltage) / 2 (V)\n")
        f.write("#\n")
        
        # Write CSV data
        df.to_csv(f, index=False)
    
    print(f"📊 LabPlot2 compatible file: {labplot_filename}")
    print(f"📈 Total samples: {len(df)} ({len(ref_data)} Palmsens + {len(target_data)} STM32)")
    print(f"🔍 Columns: {list(df.columns)}")
    
    # Summary statistics for report
    summary = {
        'timestamp': timestamp,
        'ref_samples': len(ref_data),
        'target_samples': len(target_data),
        'total_samples': len(df),
        'scan_01_skipped': True,
        'ref_concentrations': sorted(df[df['device'] == 'Palmsens']['concentration'].unique()),
        'target_concentrations': sorted(df[df['device'] == 'STM32']['concentration'].unique()),
        'method': 'Enhanced Detector V4 Improved',
        'files': {
            'labplot2_csv': labplot_filename,
            'ref_csv': f"pls_reference_palmsens_{timestamp}.csv",
            'target_csv': f"pls_target_stm32_{timestamp}.csv"
        }
    }
    
    # Save summary
    summary_file = f"pls_analysis_summary_{timestamp}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"📋 Analysis summary: {summary_file}")

if __name__ == "__main__":
    run_pls_analysis_ref_vs_target()
