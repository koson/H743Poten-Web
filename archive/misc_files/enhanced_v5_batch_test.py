#!/usr/bin/env python3
"""
Enhanced V5 Batch Testing Script
ทดสอบ Enhanced V5 กับไฟล์หลายความเข้มข้นเพื่อดู success rate
"""

import os
import sys
import glob
import json
from pathlib import Path
from datetime import datetime
import logging

# Import Enhanced V5 detector
from enhanced_detector_v5 import EnhancedDetectorV5

# Setup logging
logging.basicConfig(level=logging.WARNING)  # ลด log เพื่อให้ดูผลได้ชัดเจน
logger = logging.getLogger(__name__)

def find_test_files_by_concentration():
    """
    หาไฟล์ทดสอบจากแต่ละความเข้มข้น
    """
    base_path = "Test_data/Stm32"
    concentrations = {}
    
    # หาโฟลเดอร์ที่มี concentration patterns
    concentration_patterns = [
        "Pipot_Ferro_0_5mM",
        "Pipot_Ferro_1_0mM", 
        "Pipot_Ferro_5_0mM",
        "Pipot_Ferro_20mM"
    ]
    
    for pattern in concentration_patterns:
        folder_path = Path(base_path) / pattern
        if folder_path.exists():
            # หาไฟล์ .csv ในโฟลเดอร์
            csv_files = list(folder_path.glob("*.csv"))
            if csv_files:
                concentrations[pattern] = [str(f) for f in csv_files[:5]]  # เอาแค่ 5 ไฟล์ต่อความเข้มข้น
                
    return concentrations

def test_single_file(detector, file_path):
    """
    ทดสอบไฟล์เดียว
    """
    try:
        import pandas as pd
        
        # โหลดข้อมูล
        df = pd.read_csv(file_path, skiprows=1)
        voltage = df['V'].values
        current = df['uA'].values
        
        # ทำการ detect
        results = detector.detect_peaks_enhanced_v5(voltage, current)
        
        # วิเคราะห์ผล
        valid_peaks = results['peaks']
        rejected_peaks = results['rejected_peaks']
        
        ox_count = len([p for p in valid_peaks if p['type'] == 'oxidation'])
        red_count = len([p for p in valid_peaks if p['type'] == 'reduction'])
        
        # คำนวณ success criteria
        # Success = มี peaks ทั้ง OX และ RED อย่างน้อยคนละ 1 peak
        has_both_peaks = ox_count > 0 and red_count > 0
        
        # คำนวณ baseline quality
        baseline_quality = results['enhanced_results']['baseline_quality']
        
        return {
            'success': has_both_peaks,
            'ox_peaks': ox_count,
            'red_peaks': red_count,
            'total_valid': len(valid_peaks),
            'total_rejected': len(rejected_peaks),
            'baseline_quality': baseline_quality,
            'data_points': len(voltage),
            'voltage_range': (float(voltage.min()), float(voltage.max())),
            'current_range': (float(current.min()), float(current.max())),
            'enhanced_results': results['enhanced_results']
        }
        
    except Exception as e:
        logger.error(f"Error testing {file_path}: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def run_batch_test():
    """
    รันการทดสอบ batch
    """
    print("🧪 Enhanced V5 Batch Testing")
    print("=" * 60)
    
    # หาไฟล์ทดสอบ
    concentrations = find_test_files_by_concentration()
    
    if not concentrations:
        print("❌ No test files found!")
        return
    
    # สร้าง detector
    detector = EnhancedDetectorV5()
    
    # เก็บผลลัพธ์
    all_results = {}
    overall_stats = {
        'total_files': 0,
        'successful_files': 0,
        'failed_files': 0,
        'success_rate': 0.0
    }
    
    # ทดสอบแต่ละความเข้มข้น
    for concentration, files in concentrations.items():
        print(f"\n📊 Testing {concentration}:")
        print("-" * 40)
        
        concentration_results = []
        successful_in_concentration = 0
        
        for i, file_path in enumerate(files):
            print(f"  {i+1:2d}. {Path(file_path).name[:50]}...", end=" ")
            
            result = test_single_file(detector, file_path)
            result['file_path'] = file_path
            concentration_results.append(result)
            
            if result['success']:
                successful_in_concentration += 1
                print(f"✅ OX:{result['ox_peaks']}, RED:{result['red_peaks']}")
            else:
                error_msg = result.get('error', 'No peaks detected')
                print(f"❌ {error_msg}")
            
            overall_stats['total_files'] += 1
            if result['success']:
                overall_stats['successful_files'] += 1
            else:
                overall_stats['failed_files'] += 1
        
        # สรุปผลของความเข้มข้นนี้
        concentration_success_rate = (successful_in_concentration / len(files)) * 100
        print(f"\n  📈 {concentration} Success Rate: {successful_in_concentration}/{len(files)} ({concentration_success_rate:.1f}%)")
        
        all_results[concentration] = {
            'files': concentration_results,
            'success_count': successful_in_concentration,
            'total_count': len(files),
            'success_rate': concentration_success_rate
        }
    
    # คำนวณ overall success rate
    overall_stats['success_rate'] = (overall_stats['successful_files'] / overall_stats['total_files']) * 100
    
    # สรุปผลรวม
    print("\n" + "=" * 60)
    print("🎯 OVERALL RESULTS:")
    print("=" * 60)
    
    for concentration, results in all_results.items():
        success_rate = results['success_rate']
        status = "🟢" if success_rate >= 80 else "🟡" if success_rate >= 60 else "🔴"
        print(f"{status} {concentration:20s}: {results['success_count']:2d}/{results['total_count']:2d} ({success_rate:5.1f}%)")
    
    print(f"\n🏆 OVERALL SUCCESS RATE: {overall_stats['successful_files']}/{overall_stats['total_files']} ({overall_stats['success_rate']:.1f}%)")
    
    # แสดงสถานะ
    if overall_stats['success_rate'] >= 80:
        print("🎉 SUCCESS! Ready to move to other concentrations!")
    elif overall_stats['success_rate'] >= 60:
        print("⚠️  Good progress, but needs some improvement")
    else:
        print("❌ Needs significant improvement")
    
    # บันทึกผลลัพธ์
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"v5_batch_test_report_{timestamp}.json"
    
    report_data = {
        'timestamp': timestamp,
        'overall_stats': overall_stats,
        'concentration_results': all_results,
        'detector_version': 'Enhanced V5.0',
        'test_criteria': 'Success = OX peaks > 0 AND RED peaks > 0'
    }
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Report saved: {report_file}")
    except Exception as e:
        print(f"⚠️  Could not save report: {e}")
    
    return overall_stats

def print_detailed_analysis(concentration_results):
    """
    แสดงการวิเคราะห์รายละเอียด
    """
    print("\n📋 DETAILED ANALYSIS:")
    print("-" * 40)
    
    for concentration, results in concentration_results.items():
        print(f"\n{concentration}:")
        
        successful_files = [r for r in results['files'] if r['success']]
        failed_files = [r for r in results['files'] if not r['success']]
        
        if successful_files:
            avg_ox = sum(r['ox_peaks'] for r in successful_files) / len(successful_files)
            avg_red = sum(r['red_peaks'] for r in successful_files) / len(successful_files)
            avg_baseline = sum(r['baseline_quality'] for r in successful_files) / len(successful_files)
            
            print(f"  ✅ Successful files: {len(successful_files)}")
            print(f"     Average OX peaks: {avg_ox:.1f}")
            print(f"     Average RED peaks: {avg_red:.1f}")
            print(f"     Average baseline quality: {avg_baseline:.1%}")
        
        if failed_files:
            print(f"  ❌ Failed files: {len(failed_files)}")
            for failed in failed_files[:3]:  # แสดงแค่ 3 ไฟล์แรก
                file_name = Path(failed['file_path']).name
                error = failed.get('error', 'No peaks detected')
                print(f"     - {file_name}: {error}")

if __name__ == "__main__":
    # รันการทดสอบ
    results = run_batch_test()
    
    # ถ้าต้องการดูรายละเอียดเพิ่มเติม
    print("\n" + "=" * 60)
    print("📊 RECOMMENDATION:")
    print("=" * 60)
    
    if results['success_rate'] >= 80:
        print("🚀 Enhanced V5 is ready for production!")
        print("   - Success rate > 80%")
        print("   - Can proceed to test other concentrations")
        print("   - Consider integration into web application")
    elif results['success_rate'] >= 60:
        print("⚙️  Enhanced V5 shows good potential:")
        print("   - Success rate 60-80%")
        print("   - May need minor tuning for edge cases")
        print("   - Consider testing with more files")
    else:
        print("🔧 Enhanced V5 needs improvement:")
        print("   - Success rate < 60%")
        print("   - Review failed cases for patterns")
        print("   - Consider algorithm refinement")
    
    print(f"\n✨ Total files tested: {results['total_files']}")
    print(f"🎯 Overall success rate: {results['success_rate']:.1f}%")
