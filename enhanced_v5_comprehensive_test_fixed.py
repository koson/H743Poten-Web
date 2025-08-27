#!/usr/bin/env python3
"""
🎯 Enhanced V5 Comprehensive Testing Framework - FIXED VERSION
========================================================
ทดสอบ Enhanced V5 กับไฟล์ทั้งหมดในระบบ

📊 Features:
- ทดสอบข้อมูลจากหลายแหล่ง (STM32, PalmSens, raw data)
- จัดกลุ่มตามความเข้มข้น
- รายงานผลแบบครอบคลุม
- แก้ไขปัญหา list/dict return value

💾 Author: AI Assistant
🗓️ Created: 2025-08-27
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter
import json
import traceback
from datetime import datetime

# เพิ่ม path สำหรับ Enhanced V5
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Enhanced V5 detector
from enhanced_detector_v5 import EnhancedDetectorV5

def find_all_test_files():
    """🔍 ค้นหาไฟล์ทดสอบทั้งหมด"""
    print("🔍 Discovering all test files...")
    
    test_data_dir = Path("Test_data")
    
    file_groups = {
        'stm32': {
            'path': test_data_dir / "Stm32", 
            'files': [],
            'pattern': "*.csv"
        },
        'palmsens': {
            'path': test_data_dir / "PalmSens",
            'files': [], 
            'pattern': "*.csv"
        },
        'raw_stm32': {
            'path': test_data_dir / "raw_stm32",
            'files': [],
            'pattern': "*.csv"
        },
        'isolated': {
            'path': test_data_dir / "isolated-test",
            'files': [],
            'pattern': "*.csv"
        }
    }
    
    total_files = 0
    
    for group_name, group_info in file_groups.items():
        if group_info['path'].exists():
            files = list(group_info['path'].rglob(group_info['pattern']))
            group_info['files'] = [str(f) for f in files]
            total_files += len(files)
            print(f"📁 {group_name:12}: {len(files):4d} files")
        else:
            print(f"📁 {group_name:12}: Directory not found")
    
    print(f"📊 Total files found: {total_files}")
    return file_groups

def categorize_files_by_concentration(file_groups):
    """🧪 จัดกลุ่มไฟล์ตามความเข้มข้น"""
    concentrations = defaultdict(list)
    
    concentration_patterns = [
        'Pipot_Ferro_0_5mM', 'Pipot_Ferro-0_5mM',
        'Pipot_Ferro_1_0mM', 'Pipot_Ferro-1_0mM', 
        'Pipot_Ferro_5_0mM', 'Pipot_Ferro-5_0mM',
        'Pipot_Ferro_20mM', 'Pipot_Ferro-20mM',
        'Palmsens_5mM', 'Palmsens_10mM', 'Palmsens_20mM', 'Palmsens_50mM',
        'test_stm32', 'isolated'
    ]
    
    for group_name, group_info in file_groups.items():
        for file_path in group_info['files']:
            file_name = Path(file_path).name
            
            matched = False
            for pattern in concentration_patterns:
                if pattern in file_name:
                    concentrations[pattern].append(file_path)
                    matched = True
                    break
            
            if not matched:
                concentrations['others'].append(file_path)
    
    return concentrations

def test_single_file_fixed(detector, file_path):
    """✅ ทดสอบไฟล์เดียว - เวอร์ชันแก้ไขแล้ว"""
    try:
        # อ่านข้อมูล
        df = pd.read_csv(file_path)
        
        # จัดการ column names ที่แตกต่างกัน
        columns = df.columns.tolist()
        
        # หา voltage column
        voltage_col = None
        voltage_candidates = ['V', 'Voltage', 'voltage', 'Potential', 'potential', 'E', 'WE(1).Potential']
        for candidate in voltage_candidates:
            if candidate in columns:
                voltage_col = candidate
                break
        
        if voltage_col is None:
            # ใช้ column แรกถ้าไม่เจอ
            voltage_col = columns[0]
        
        # หา current column  
        current_col = None
        current_candidates = ['uA', 'µA', 'A', 'Current', 'current', 'I', 'WE(1).Current']
        for candidate in current_candidates:
            if candidate in columns:
                current_col = candidate
                break
                
        if current_col is None:
            # ใช้ column ที่สองถ้าไม่เจอ
            current_col = columns[1] if len(columns) > 1 else columns[0]
        
        # ข้ามแถวแรกถ้าเป็น header ซ้ำ
        if df.iloc[0, 0] == voltage_col or str(df.iloc[0, 0]).lower() in ['v', 'voltage']:
            df = df.iloc[1:].reset_index(drop=True)
        
        # แปลงเป็น numeric
        voltage = pd.to_numeric(df[voltage_col], errors='coerce').dropna().values
        current = pd.to_numeric(df[current_col], errors='coerce').dropna().values
        
        # ตรวจสอบข้อมูล
        if len(voltage) < 10 or len(current) < 10:
            return {
                'success': False,
                'error': 'Insufficient data points',
                'ox_peaks': 0,
                'red_peaks': 0,
                'total_peaks': 0,
                'baseline_quality': 0.0,
                'file_path': file_path,
                'voltage_col': voltage_col,
                'current_col': current_col
            }
        
        # Detect peaks with Enhanced V5
        result = detector.detect_peaks_enhanced_v5(voltage, current)
        
        # ✅ แก้ไขการประมวลผล result ที่เป็น tuple
        if isinstance(result, tuple) and len(result) >= 2:
            ox_peaks_list = result[0] if result[0] is not None else []
            red_peaks_list = result[1] if result[1] is not None else []
            baseline_info = result[2] if len(result) > 2 and result[2] is not None else {}
        elif isinstance(result, dict):
            ox_peaks_list = result.get('oxidation_peaks', [])
            red_peaks_list = result.get('reduction_peaks', [])
            baseline_info = result.get('baseline_info', {})
        else:
            ox_peaks_list = []
            red_peaks_list = []
            baseline_info = {}
        
        # นับจำนวน peaks
        ox_count = len(ox_peaks_list) if isinstance(ox_peaks_list, list) else 0
        red_count = len(red_peaks_list) if isinstance(red_peaks_list, list) else 0
        
        # เงื่อนไขความสำเร็จ: มี OX > 0 และ RED > 0
        success = ox_count > 0 and red_count > 0
        
        # คุณภาพ baseline
        baseline_quality = 0.0
        if isinstance(baseline_info, dict):
            baseline_quality = baseline_info.get('quality_score', 0.0)
        
        return {
            'success': success,
            'error': None,
            'ox_peaks': ox_count,
            'red_peaks': red_count,
            'total_peaks': ox_count + red_count,
            'baseline_quality': baseline_quality,
            'file_path': file_path,
            'voltage_col': voltage_col,
            'current_col': current_col
        }
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        return {
            'success': False,
            'error': error_msg,
            'ox_peaks': 0,
            'red_peaks': 0,
            'total_peaks': 0,
            'baseline_quality': 0.0,
            'file_path': file_path,
            'voltage_col': 'unknown',
            'current_col': 'unknown'
        }

def test_concentration_group(detector, concentration, files, max_files=15):
    """🧪 ทดสอบไฟล์ในกลุ่มความเข้มข้นเดียว"""
    print(f"\n📊 Testing {concentration} ({len(files)} files):")
    print("-" * 60)
    
    # จำกัดจำนวนไฟล์ถ้าจำเป็น
    test_files = files[:max_files] if len(files) > max_files else files
    
    results = []
    successful = 0
    
    for i, file_path in enumerate(test_files, 1):
        result = test_single_file_fixed(detector, file_path)
        results.append(result)
        
        file_name = Path(file_path).name
        status = "✅" if result['success'] else "❌"
        error_info = f" {result['error']}" if result['error'] else ""
        
        print(f"{i:5}. {file_name:50} {status}{error_info}")
        
        if result['success']:
            successful += 1
    
    success_rate = (successful / len(test_files)) * 100 if test_files else 0
    print(f"\n  📈 {concentration} Success Rate: {successful}/{len(test_files)} ({success_rate:.1f}%)")
    
    return {
        'concentration': concentration,
        'total_files': len(test_files),
        'successful_files': successful,
        'success_rate': success_rate,
        'results': results
    }

def run_comprehensive_test():
    """🎯 รันการทดสอบแบบครอบคลุม"""
    print("🎯 ENHANCED V5 COMPREHENSIVE TESTING FRAMEWORK")
    print("=" * 70)
    
    # สร้าง detector
    detector = EnhancedDetectorV5()
    
    # ค้นหาไฟล์ทั้งหมด
    file_groups = find_all_test_files()
    
    # จัดกลุ่มตามความเข้มข้น
    concentrations = categorize_files_by_concentration(file_groups)
    
    print(f"\n🧪 Found {len(concentrations)} concentration groups:")
    for conc, files in concentrations.items():
        print(f"   {conc:20}: {len(files):4d} files")
    
    # ทดสอบแต่ละกลุ่ม
    all_results = []
    total_files = 0
    total_successful = 0
    
    for concentration, files in concentrations.items():
        result = test_concentration_group(detector, concentration, files, max_files=15)
        all_results.append(result)
        total_files += result['total_files']
        total_successful += result['successful_files']
    
    # สรุปผล
    overall_success_rate = (total_successful / total_files) * 100 if total_files else 0
    
    print("\n" + "=" * 70)
    print("🎯 COMPREHENSIVE TEST RESULTS:")
    print("=" * 70)
    
    for result in all_results:
        status = "🟢" if result['success_rate'] >= 80 else "🟡" if result['success_rate'] >= 50 else "🔴"
        print(f"{status} {result['concentration']:20}: {result['successful_files']:3d}/{result['total_files']:3d} ({result['success_rate']:5.1f}%)")
    
    print(f"\n🏆 OVERALL SUCCESS RATE: {total_successful}/{total_files} ({overall_success_rate:.1f}%)")
    
    # Assessment
    if overall_success_rate >= 80:
        print("✅ EXCELLENT! Production ready")
    elif overall_success_rate >= 60:
        print("⚠️  GOOD! Minor improvements needed")
    else:
        print("❌ NEEDS IMPROVEMENT! Review failed cases")
    
    # สร้างรายงาน JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        'test_metadata': {
            'timestamp': datetime.now().isoformat(),
            'detector_version': 'Enhanced V5.0 Fixed',
            'test_parameters': {
                'max_files_per_group': 15,
                'success_criteria': 'OX peaks > 0 AND RED peaks > 0'
            }
        },
        'raw_results': {
            'overall_stats': {
                'total_files': total_files,
                'successful_files': total_successful,
                'failed_files': total_files - total_successful,
                'success_rate': overall_success_rate
            },
            'concentration_results': all_results
        },
        'summary': {
            'top_performing': sorted(all_results, key=lambda x: x['success_rate'], reverse=True)[:3],
            'needs_improvement': [r for r in all_results if r['success_rate'] < 50],
            'performance_assessment': (
                'excellent' if overall_success_rate >= 80 else
                'good' if overall_success_rate >= 60 else
                'needs_work'
            )
        }
    }
    
    # บันทึกรายงาน
    report_file = f"enhanced_v5_comprehensive_test_report_fixed_{timestamp}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 QUICK SUMMARY:")
    print(f"   💯 Overall Success Rate: {overall_success_rate:.1f}%")
    print(f"   📁 Total Files Tested: {total_files}")
    print(f"   ✅ Successful: {total_successful}")
    print(f"   ❌ Failed: {total_files - total_successful}")
    
    print(f"\n🏆 TOP PERFORMING CONCENTRATIONS:")
    top_3 = sorted(all_results, key=lambda x: x['success_rate'], reverse=True)[:3]
    for i, result in enumerate(top_3, 1):
        print(f"   {i}. {result['concentration']:15}: {result['success_rate']:5.1f}%")
    
    print(f"\n💾 Comprehensive report saved: {report_file}")
    
    # Final assessment
    print(f"\n🎯 FINAL ASSESSMENT:")
    if overall_success_rate >= 80:
        print("🚀 PRODUCTION READY! Excellent performance across datasets")
    elif overall_success_rate >= 60:
        print("⚡ GOOD PERFORMANCE! Minor tuning recommended")
    else:
        print("🔧 NEEDS WORK! Significant improvements required")
    
    print(f"\n✨ Testing complete! Report: {report_file}")
    return report

if __name__ == "__main__":
    report = run_comprehensive_test()
