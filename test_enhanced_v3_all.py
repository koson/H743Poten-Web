#!/usr/bin/env python3
"""
Test Enhanced Detector V3.0 กับไฟล์ทั้ง 5 ไฟล์ที่มีปัญหา
"""

import sys
import os
sys.path.append('.')

from enhanced_detector_v3 import EnhancedDetectorV3
import pandas as pd
import numpy as np

def test_all_problem_files():
    """ทดสอบ Enhanced Detector V3.0 กับไฟล์ที่มีปัญหาทั้ง 5 ไฟล์"""
    
    detector = EnhancedDetectorV3()
    
    problem_files = [
        {
            'file': 'Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_100mVpS_E1_scan_08.csv',
            'issue': 'baseline segment ไม่ถูก (ไม่อยู่ช่วงยาว)',
            'expected_improvement': 'ควรมี scan direction ที่ถูกต้องและ baseline ที่ดีขึ้น'
        },
        {
            'file': 'Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_200mVpS_E5_scan_05.csv', 
            'issue': 'มี OX 2 อัน แต่ไม่มี RED, OX ที่ +0.7V ไม่ถูก',
            'expected_improvement': 'ควรปฏิเสธ OX ที่ +0.7V และเจอ RED peaks'
        },
        {
            'file': 'Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_20mVpS_E1_scan_02.csv',
            'issue': 'ไม่เจอ peak และ baseline เลย (signal อ่อน)',
            'expected_improvement': 'ควรเจอ peaks แม้ signal อ่อน ด้วย dynamic threshold'
        },
        {
            'file': 'Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_20mVpS_E2_scan_04.csv',
            'issue': 'ไม่เจอ segment ใช้ baseline เป็นศูนย์',
            'expected_improvement': 'ควรเจอ baseline segment ที่ถูกต้อง'
        },
        {
            'file': 'Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_400mVpS_E5_scan_06.csv',
            'issue': 'baseline segment อยู่ตรงที่ควรเป็น peak',
            'expected_improvement': 'ควรหลีกเลี่ยง baseline ที่ทับกับ peak'
        }
    ]
    
    results_summary = []
    
    print("🚀 Testing Enhanced Detector V3.0 on All Problem Files")
    print("=" * 80)
    
    for i, file_info in enumerate(problem_files, 1):
        filename = file_info['file']
        issue = file_info['issue']
        expected = file_info['expected_improvement']
        
        print(f"\n📊 Test {i}/5: {filename.split('/')[-1]}")
        print(f"🚨 Known Issue: {issue}")
        print(f"💡 Expected Improvement: {expected}")
        print("-" * 60)
        
        try:
            # โหลดข้อมูล
            df = pd.read_csv(filename, skiprows=1)
            voltage = np.array(df['V'].values, dtype=float)
            current = np.array(df['uA'].values, dtype=float)
            
            print(f"📈 Data: {len(voltage)} points, V:[{voltage.min():.3f}, {voltage.max():.3f}], I:[{current.min():.1f}, {current.max():.1f}]µA")
            
            # รัน Enhanced Detector (ปิด logging เพื่อความกะทัดรัด)
            import logging
            logging.getLogger('__main__').setLevel(logging.WARNING)
            
            results = detector.detect_peaks_enhanced(voltage, current)
            
            # เปิด logging กลับ
            logging.getLogger('__main__').setLevel(logging.INFO)
            
            # วิเคราะห์ผลลัพธ์
            ox_peaks = [p for p in results['peaks'] if p['type'] == 'oxidation']
            red_peaks = [p for p in results['peaks'] if p['type'] == 'reduction']
            
            print(f"🎯 Results:")
            print(f"   Peaks: {len(results['peaks'])} total (OX:{len(ox_peaks)}, RED:{len(red_peaks)})")
            print(f"   Baseline: {len(results['baseline_indices'])} points in {len(results['baseline_info'])} regions")
            print(f"   Scan: Forward:{results['scan_sections']['forward'][1]}, Reverse:{results['scan_sections']['reverse'][1] - results['scan_sections']['reverse'][0]}")
            print(f"   SNR: {results['thresholds']['snr']:.1f}")
            print(f"   Conflicts: {len(results['conflicts'])}")
            
            # แสดงรายละเอียด peaks
            for peak in results['peaks']:
                print(f"      {peak['type'][:3].upper()}: {peak['voltage']:.3f}V, {peak['current']:.1f}µA, conf={peak['confidence']:.0f}%")
            
            # ประเมินการปรับปรุง
            improvement_score = evaluate_improvement(file_info, results, voltage, current)
            
            result_summary = {
                'filename': filename.split('/')[-1],
                'original_issue': issue,
                'peaks_found': len(results['peaks']),
                'ox_peaks': len(ox_peaks),
                'red_peaks': len(red_peaks),
                'baseline_regions': len(results['baseline_info']),
                'scan_balance': abs(results['scan_sections']['forward'][1] - (results['scan_sections']['reverse'][1] - results['scan_sections']['reverse'][0])) / len(voltage),
                'snr': results['thresholds']['snr'],
                'conflicts': len(results['conflicts']),
                'improvement_score': improvement_score['score'],
                'improvements': improvement_score['improvements']
            }
            
            results_summary.append(result_summary)
            
            print(f"✅ Improvement Score: {improvement_score['score']:.1f}/10")
            print(f"   {', '.join(improvement_score['improvements'])}")
            
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            continue
    
    # สรุปผลรวม
    print(f"\n{'='*80}")
    print("📋 OVERALL IMPROVEMENT SUMMARY")
    print(f"{'='*80}")
    
    if results_summary:
        avg_score = sum(r['improvement_score'] for r in results_summary) / len(results_summary)
        total_conflicts = sum(r['conflicts'] for r in results_summary)
        files_with_peaks = sum(1 for r in results_summary if r['peaks_found'] > 0)
        files_with_baseline = sum(1 for r in results_summary if r['baseline_regions'] > 0)
        avg_snr = sum(r['snr'] for r in results_summary) / len(results_summary)
        
        print(f"📊 Overall Performance:")
        print(f"   Average Improvement Score: {avg_score:.1f}/10")
        print(f"   Files with peaks detected: {files_with_peaks}/{len(results_summary)} ({files_with_peaks/len(results_summary)*100:.0f}%)")
        print(f"   Files with baseline regions: {files_with_baseline}/{len(results_summary)} ({files_with_baseline/len(results_summary)*100:.0f}%)")
        print(f"   Total conflicts: {total_conflicts}")
        print(f"   Average SNR: {avg_snr:.1f}")
        
        print(f"\n🎯 Key Improvements:")
        all_improvements = []
        for r in results_summary:
            all_improvements.extend(r['improvements'])
        
        improvement_counts = {}
        for imp in all_improvements:
            improvement_counts[imp] = improvement_counts.get(imp, 0) + 1
        
        for improvement, count in sorted(improvement_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   ✅ {improvement}: {count}/{len(results_summary)} files")
        
        print(f"\n📈 Detailed Results:")
        for r in results_summary:
            print(f"   {r['filename']}: {r['peaks_found']} peaks, {r['baseline_regions']} regions, score={r['improvement_score']:.1f}")

def evaluate_improvement(file_info, results, voltage, current):
    """ประเมินการปรับปรุงสำหรับแต่ละไฟล์"""
    
    score = 0.0
    improvements = []
    
    issue = file_info['issue']
    ox_peaks = [p for p in results['peaks'] if p['type'] == 'oxidation']
    red_peaks = [p for p in results['peaks'] if p['type'] == 'reduction']
    
    # 1. ประเมิน scan direction balance
    forward_len = results['scan_sections']['forward'][1]
    reverse_len = results['scan_sections']['reverse'][1] - results['scan_sections']['reverse'][0]
    balance_ratio = min(forward_len, reverse_len) / max(forward_len, reverse_len)
    
    if balance_ratio > 0.3:  # ไม่เอียงเกินไป
        score += 2.0
        improvements.append("Balanced scan direction")
    
    # 2. ประเมิน peak validation
    if 'OX ที่ +0.7V ไม่ถูก' in issue:
        # ตรวจสอบว่ามี peak ที่ +0.7V หรือไม่
        high_voltage_peaks = [p for p in results['peaks'] if p['voltage'] > 0.6]
        if len(high_voltage_peaks) == 0:
            score += 3.0
            improvements.append("Rejected invalid high-voltage peaks")
        else:
            score += 1.0  # บางส่วน
    
    # 3. ประเมิน baseline detection
    if len(results['baseline_info']) > 0:
        score += 2.0
        improvements.append("Found baseline regions")
        
        if len(results['baseline_indices']) > len(voltage) * 0.1:  # อย่างน้อย 10%
            score += 1.0
            improvements.append("Sufficient baseline coverage")
    
    # 4. ประเมิน conflict resolution
    if results['conflicts'] == 0:
        score += 1.0
        improvements.append("No baseline-peak conflicts")
    
    # 5. ประเมิน SNR-based detection
    if results['thresholds']['snr'] > 2.0:
        score += 1.0
        improvements.append("Good signal quality detected")
    
    # 6. ประเมิน peak diversity (ควรมีทั้ง OX และ RED)
    if len(ox_peaks) > 0 and len(red_peaks) > 0:
        score += 1.0
        improvements.append("Found both OX and RED peaks")
    elif len(results['peaks']) > 0:
        score += 0.5
        improvements.append("Found peaks")
    
    return {
        'score': min(10.0, score),  # สูงสุด 10
        'improvements': improvements
    }

if __name__ == "__main__":
    test_all_problem_files()
