#!/usr/bin/env python3
"""
ทดสอบ Enhanced Detector V3.0 กับไฟล์ชุดใหม่แบบสุ่มตัวอย่าง
เพื่อหาปัจจัยที่ทำให้ผลไม่ดีเท่าที่ควร
"""

import sys
import os
import random
import glob
sys.path.append('.')

from enhanced_detector_v3 import EnhancedDetectorV3
import pandas as pd
import numpy as np
import json
from pathlib import Path

def analyze_diverse_samples():
    """ทดสอบตัวอย่างที่หลากหลายเพื่อหาปัจจัยที่มีปัญหา"""
    
    detector = EnhancedDetectorV3()
    
    # กำหนดกลุ่มไฟล์ที่น่าสนใจ
    test_categories = [
        {
            'name': 'Low Concentration (0.5mM)',
            'pattern': 'Test_data/Stm32/Pipot_Ferro_0_5mM/*.csv',
            'expected_issues': ['signal อ่อน', 'SNR ต่ำ', 'baseline ไม่เสถียร']
        },
        {
            'name': 'High Concentration (50mM)', 
            'pattern': 'Test_data/Stm32/Pipot_Ferro_50mM/*.csv',
            'expected_issues': ['peak สูงเกินไป', 'saturation', 'baseline drift']
        },
        {
            'name': 'Very High Scan Rate (400mVpS)',
            'pattern': 'Test_data/Stm32/*_400mVpS_*.csv',
            'expected_issues': ['capacitive current', 'peak บิดเบี้ยว', 'ไม่ equilibrium']
        },
        {
            'name': 'Very Low Scan Rate (20mVpS)',
            'pattern': 'Test_data/Stm32/*_20mVpS_*.csv', 
            'expected_issues': ['noise มาก', 'drift', 'ช้าเกินไป']
        },
        {
            'name': 'Palmsens Device',
            'pattern': 'Test_data/Palmsens/**/*.csv',
            'expected_issues': ['format ต่าง', 'unit ต่าง', 'voltage range ต่าง']
        }
    ]
    
    all_results = []
    category_summaries = []
    
    print("🔬 Analyzing Diverse Sample Categories for Potential Issues")
    print("=" * 80)
    
    for category in test_categories:
        print(f"\n📂 Category: {category['name']}")
        print(f"🔍 Pattern: {category['pattern']}")
        print(f"❓ Expected Issues: {', '.join(category['expected_issues'])}")
        print("-" * 60)
        
        # หาไฟล์ในกลุ่มนี้
        files = glob.glob(category['pattern'])
        if not files:
            print(f"❌ No files found for pattern: {category['pattern']}")
            continue
        
        # สุ่มเลือก 3-5 ไฟล์ต่อกลุ่ม
        sample_size = min(5, len(files))
        sample_files = random.sample(files, sample_size)
        
        category_results = []
        print(f"📊 Testing {sample_size} files from {len(files)} available...")
        
        for i, filepath in enumerate(sample_files, 1):
            filename = os.path.basename(filepath)
            print(f"\n  {i}/{sample_size}: {filename}")
            
            try:
                # โหลดและทดสอบ
                result = test_single_file(filepath, detector, verbose=False)
                result['category'] = category['name']
                result['expected_issues'] = category['expected_issues']
                
                category_results.append(result)
                all_results.append(result)
                
                # แสดงผลสั้นๆ
                print(f"    Peaks: {result['peaks_found']} (OX:{result['ox_peaks']}, RED:{result['red_peaks']})")
                print(f"    SNR: {result['snr']:.1f}, Score: {result['performance_score']:.1f}/10")
                if result['issues']:
                    print(f"    Issues: {', '.join(result['issues'][:2])}...")
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
                continue
        
        # สรุปผลตามกลุ่ม
        if category_results:
            summary = analyze_category_results(category, category_results)
            category_summaries.append(summary)
            
            print(f"\n  📋 Category Summary:")
            print(f"    Avg Score: {summary['avg_score']:.1f}/10")
            print(f"    Success Rate: {summary['success_rate']:.0f}%")
            print(f"    Main Issues: {', '.join(summary['main_issues'][:3])}")
    
    # วิเคราะห์ปัจจัยที่ทำให้ผลไม่ดี
    print(f"\n{'='*80}")
    print("🎯 COMPREHENSIVE ISSUE ANALYSIS")
    print(f"{'='*80}")
    
    if all_results:
        overall_analysis = analyze_overall_performance(all_results, category_summaries)
        
        # บันทึกผลลัพธ์
        report = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'total_files_tested': len(all_results),
            'categories_tested': len(category_summaries),
            'overall_analysis': overall_analysis,
            'category_summaries': category_summaries,
            'detailed_results': all_results
        }
        
        report_file = f"enhanced_detector_v3_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Full report saved to: {report_file}")
        
        return overall_analysis
    
    else:
        print("❌ No successful tests completed")
        return None

def test_single_file(filepath, detector, verbose=True):
    """ทดสอบไฟล์เดียวและวิเคราะห์ผล"""
    
    # โหลดข้อมูล
    try:
        df = pd.read_csv(filepath, skiprows=1)
        voltage = np.array(df['V'].values, dtype=float)
        current = np.array(df['uA'].values, dtype=float)
    except:
        # ลองแบบ Palmsens format
        try:
            df = pd.read_csv(filepath)
            if 'WE(1).Potential' in df.columns:
                voltage = np.array(df['WE(1).Potential'].values, dtype=float)
                current = np.array(df['WE(1).Current'].values, dtype=float) * 1e6  # A -> µA
            else:
                raise ValueError("Unknown format")
        except Exception as e:
            raise ValueError(f"Cannot read file: {e}")
    
    # รัน detector (ปิด logging)
    import logging
    old_level = logging.getLogger('enhanced_detector_v3').level
    logging.getLogger('enhanced_detector_v3').setLevel(logging.WARNING)
    
    try:
        results = detector.detect_peaks_enhanced(voltage, current)
    finally:
        logging.getLogger('enhanced_detector_v3').setLevel(old_level)
    
    # วิเคราะห์ผลลัพธ์
    analysis = analyze_single_result(filepath, voltage, current, results)
    
    return analysis

def analyze_single_result(filepath, voltage, current, results):
    """วิเคราะห์ผลลัพธ์จากไฟล์เดียว"""
    
    filename = os.path.basename(filepath)
    ox_peaks = [p for p in results['peaks'] if p['type'] == 'oxidation']
    red_peaks = [p for p in results['peaks'] if p['type'] == 'reduction']
    
    # คำนวณตัวชี้วัดต่างๆ
    data_range = voltage.max() - voltage.min()
    current_range = current.max() - current.min()
    scan_balance = calculate_scan_balance(results)
    
    # ตรวจสอบปัญหาต่างๆ
    issues = []
    warnings = []
    
    # 1. SNR issues
    if results['thresholds']['snr'] < 2.0:
        issues.append("Low SNR")
    elif results['thresholds']['snr'] < 3.0:
        warnings.append("Moderate SNR")
    
    # 2. Scan direction issues  
    if scan_balance < 0.2:
        issues.append("Unbalanced scan direction")
    elif scan_balance < 0.4:
        warnings.append("Slightly unbalanced scan")
    
    # 3. Peak detection issues
    if len(results['peaks']) == 0:
        issues.append("No peaks detected")
    elif len(ox_peaks) == 0:
        warnings.append("No oxidation peaks")
    elif len(red_peaks) == 0:
        warnings.append("No reduction peaks")
    
    # 4. Baseline issues
    if len(results['baseline_info']) == 0:
        issues.append("No baseline regions")
    elif len(results['baseline_indices']) < len(voltage) * 0.05:
        warnings.append("Insufficient baseline coverage")
    
    # 5. Voltage range issues
    if data_range < 0.8:
        warnings.append("Narrow voltage range")
    elif data_range > 1.2:
        warnings.append("Wide voltage range")
    
    # 6. Current magnitude issues
    if current_range < 1.0:
        warnings.append("Very low current range")
    elif current_range > 1000:
        warnings.append("Very high current range")
    
    # 7. Conflicts
    if len(results['conflicts']) > 0:
        issues.append(f"{len(results['conflicts'])} baseline-peak conflicts")
    
    # คำนวณคะแนนประสิทธิภาพ
    performance_score = calculate_performance_score(results, issues, warnings)
    
    return {
        'filename': filename,
        'filepath': filepath,
        'data_points': len(voltage),
        'voltage_range': [voltage.min(), voltage.max()],
        'current_range': [current.min(), current.max()],
        'peaks_found': len(results['peaks']),
        'ox_peaks': len(ox_peaks),
        'red_peaks': len(red_peaks),
        'baseline_regions': len(results['baseline_info']),
        'baseline_points': len(results['baseline_indices']),
        'snr': results['thresholds']['snr'],
        'scan_balance': scan_balance,
        'conflicts': len(results['conflicts']),
        'issues': issues,
        'warnings': warnings,
        'performance_score': performance_score,
        'raw_results': results
    }

def calculate_scan_balance(results):
    """คำนวณความสมดุลของ scan direction"""
    forward_len = results['scan_sections']['forward'][1]
    reverse_len = results['scan_sections']['reverse'][1] - results['scan_sections']['reverse'][0]
    if forward_len == 0 or reverse_len == 0:
        return 0.0
    return min(forward_len, reverse_len) / max(forward_len, reverse_len)

def calculate_performance_score(results, issues, warnings):
    """คำนวณคะแนนประสิทธิภาพรวม"""
    score = 10.0
    
    # หักคะแนนตาม issues
    score -= len(issues) * 2.0
    score -= len(warnings) * 0.5
    
    # บวกคะแนนตามผลสำเร็จ
    if len(results['peaks']) > 0:
        score += 1.0
    
    if len(results['baseline_info']) > 0:
        score += 1.0
        
    if len(results['conflicts']) == 0:
        score += 0.5
    
    return max(0.0, min(10.0, score))

def analyze_category_results(category, results):
    """วิเคราะห์ผลลัพธ์ตามกลุ่ม"""
    
    if not results:
        return {'avg_score': 0, 'success_rate': 0, 'main_issues': []}
    
    avg_score = sum(r['performance_score'] for r in results) / len(results)
    success_rate = sum(1 for r in results if r['peaks_found'] > 0) / len(results) * 100
    
    # รวม issues ทั้งหมด
    all_issues = []
    for r in results:
        all_issues.extend(r['issues'] + r['warnings'])
    
    # นับความถี่ของ issues
    issue_counts = {}
    for issue in all_issues:
        issue_counts[issue] = issue_counts.get(issue, 0) + 1
    
    main_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
    main_issues = [f"{issue} ({count})" for issue, count in main_issues[:5]]
    
    return {
        'category_name': category['name'],
        'files_tested': len(results),
        'avg_score': avg_score,
        'success_rate': success_rate,
        'main_issues': main_issues,
        'avg_snr': sum(r['snr'] for r in results) / len(results),
        'avg_scan_balance': sum(r['scan_balance'] for r in results) / len(results)
    }

def analyze_overall_performance(all_results, category_summaries):
    """วิเคราะห์ประสิทธิภาพรวม และหาปัจจัยที่ทำให้ผลไม่ดี"""
    
    print(f"📊 Overall Performance Analysis ({len(all_results)} files tested)")
    print("-" * 50)
    
    # คะแนนรวม
    avg_score = sum(r['performance_score'] for r in all_results) / len(all_results)
    success_rate = sum(1 for r in all_results if r['peaks_found'] > 0) / len(all_results) * 100
    
    print(f"Average Score: {avg_score:.1f}/10")
    print(f"Success Rate: {success_rate:.0f}%")
    
    # แยกผลลัพธ์ตามระดับประสิทธิภาพ
    excellent = [r for r in all_results if r['performance_score'] >= 8.0]
    good = [r for r in all_results if 6.0 <= r['performance_score'] < 8.0]
    poor = [r for r in all_results if r['performance_score'] < 6.0]
    
    print(f"\nPerformance Distribution:")
    print(f"  Excellent (8-10): {len(excellent)} files ({len(excellent)/len(all_results)*100:.0f}%)")
    print(f"  Good (6-8): {len(good)} files ({len(good)/len(all_results)*100:.0f}%)")
    print(f"  Poor (<6): {len(poor)} files ({len(poor)/len(all_results)*100:.0f}%)")
    
    # วิเคราะห์ปัจจัยที่ทำให้ผลไม่ดี
    print(f"\n🚨 Top Issues Causing Poor Performance:")
    poor_issues = []
    for r in poor:
        poor_issues.extend(r['issues'] + r['warnings'])
    
    issue_counts = {}
    for issue in poor_issues:
        issue_counts[issue] = issue_counts.get(issue, 0) + 1
    
    top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (issue, count) in enumerate(top_issues, 1):
        percentage = count / len(poor) * 100 if poor else 0
        print(f"  {i}. {issue}: {count} files ({percentage:.0f}%)")
    
    # วิเคราะห์ correlation
    print(f"\n📈 Performance Correlations:")
    analyze_correlations(all_results)
    
    # แนะนำการปรับปรุง
    print(f"\n💡 Improvement Recommendations:")
    recommendations = generate_recommendations(all_results, poor, top_issues)
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")
    
    return {
        'avg_score': avg_score,
        'success_rate': success_rate,
        'performance_distribution': {
            'excellent': len(excellent),
            'good': len(good), 
            'poor': len(poor)
        },
        'top_issues': top_issues,
        'recommendations': recommendations
    }

def analyze_correlations(results):
    """วิเคราะห์ความสัมพันธ์ระหว่างตัวแปรต่างๆ กับประสิทธิภาพ"""
    
    if len(results) < 5:
        print("  Insufficient data for correlation analysis")
        return
    
    scores = [r['performance_score'] for r in results]
    snrs = [r['snr'] for r in results]
    balances = [r['scan_balance'] for r in results]
    
    # SNR correlation
    snr_corr = np.corrcoef(scores, snrs)[0,1] if len(set(snrs)) > 1 else 0
    balance_corr = np.corrcoef(scores, balances)[0,1] if len(set(balances)) > 1 else 0
    
    print(f"  SNR vs Performance: {snr_corr:.2f} correlation")
    print(f"  Scan Balance vs Performance: {balance_corr:.2f} correlation")
    
    # วิเคราะห์ตาม scan rate (ถ้าสามารถดึงได้จากชื่อไฟล์)
    scan_rates = []
    for r in results:
        filename = r['filename']
        if 'mVpS' in filename:
            try:
                rate = filename.split('mVpS')[0].split('_')[-1]
                scan_rates.append(int(rate))
            except:
                scan_rates.append(None)
        else:
            scan_rates.append(None)
    
    if scan_rates and any(rate is not None for rate in scan_rates):
        valid_indices = [i for i, rate in enumerate(scan_rates) if rate is not None]
        if len(valid_indices) > 3:
            valid_scores = [scores[i] for i in valid_indices]
            valid_rates = [scan_rates[i] for i in valid_indices]
            rate_corr = np.corrcoef(valid_scores, valid_rates)[0,1]
            print(f"  Scan Rate vs Performance: {rate_corr:.2f} correlation")

def generate_recommendations(all_results, poor_results, top_issues):
    """สร้างคำแนะนำการปรับปรุง"""
    
    recommendations = []
    
    # ตาม top issues
    if top_issues:
        top_issue = top_issues[0][0]
        
        if 'Low SNR' in top_issue:
            recommendations.append("Improve SNR calculation algorithm - consider alternative noise estimation methods")
        
        if 'No peaks detected' in top_issue:
            recommendations.append("Lower peak detection threshold for weak signals - implement adaptive sensitivity")
        
        if 'Unbalanced scan' in top_issue:
            recommendations.append("Enhance scan direction detection - use smoothed derivative with larger window")
        
        if 'No baseline regions' in top_issue:
            recommendations.append("Relax baseline detection criteria - allow smaller voltage windows")
        
        if 'conflicts' in top_issue:
            recommendations.append("Increase exclusion zone around peaks for baseline detection")
    
    # ตามประสิทธิภาพรวม
    avg_score = sum(r['performance_score'] for r in all_results) / len(all_results)
    if avg_score < 7.0:
        recommendations.append("Overall performance needs improvement - consider ensemble methods")
    
    # ตาม scan rate analysis
    high_rate_poor = [r for r in poor_results if '400mVpS' in r['filename']]
    if len(high_rate_poor) > len(poor_results) * 0.3:
        recommendations.append("High scan rate performance poor - implement capacitive current compensation")
    
    low_rate_poor = [r for r in poor_results if '20mVpS' in r['filename']]
    if len(low_rate_poor) > len(poor_results) * 0.3:
        recommendations.append("Low scan rate performance poor - implement drift correction algorithm")
    
    return recommendations[:8]  # จำกัดไว้ 8 ข้อ

if __name__ == "__main__":
    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    
    analyze_diverse_samples()
