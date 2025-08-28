#!/usr/bin/env python3
"""
Test Enhanced V4 with Palmsens 0.5mM Dataset
วิเคราะห์ปัญหาที่พบ:
1. ส่วนใหญ่เจอเฉพาะ Oxidation peaks
2. ส่วนน้อยที่มีครบสอง peak  
3. มีบางไฟล์เจอ Oxidation ที่ max voltage
"""

import requests
import json
import pandas as pd
import numpy as np
import os
from pathlib import Path
import time

def test_sample_files():
    """ทดสอบไฟล์ตัวอย่างจากหลายๆ condition"""
    
    base_path = "Test_data/Palmsens/Palmsens_0.5mM"
    
    # เลือกไฟล์ตัวอย่างจากหลายๆ scan rate และ electrode
    sample_files = [
        # Fast scan rate (400mV/s) - อาจมีปัญหา peak ที่ max voltage
        "Palmsens_0.5mM_CV_400mVpS_E1_scan_01.csv",
        "Palmsens_0.5mM_CV_400mVpS_E5_scan_05.csv", 
        
        # Medium scan rate (100mV/s) - ที่เราใช้ทดสอบมาแล้ว
        "Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv",
        "Palmsens_0.5mM_CV_100mVpS_E3_scan_05.csv",
        
        # Slow scan rate (20mV/s) - ควรเห็น peak ชัดที่สุด
        "Palmsens_0.5mM_CV_20mVpS_E1_scan_01.csv",
        "Palmsens_0.5mM_CV_20mVpS_E2_scan_04.csv",
        
        # Medium-slow (50mV/s)
        "Palmsens_0.5mM_CV_50mVpS_E4_scan_08.csv",
        
        # High speed (200mV/s)
        "Palmsens_0.5mM_CV_200mVpS_E5_scan_06.csv"
    ]
    
    print("🔬 Enhanced V4 Testing - Palmsens 0.5mM Dataset Analysis")
    print("=" * 70)
    print(f"📊 Testing {len(sample_files)} representative files")
    print(f"🎯 Focus: Peak detection patterns, missing reduction peaks, edge effects")
    print()
    
    results = []
    
    for i, filename in enumerate(sample_files):
        filepath = os.path.join(base_path, filename)
        
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filename}")
            continue
            
        print(f"[{i+1}/{len(sample_files)}] 📄 {filename}")
        
        try:
            # Read CV data
            df = pd.read_csv(filepath, skiprows=1)
            voltage = df['V'].values
            current = df['uA'].values
            
            # Extract scan rate from filename
            scan_rate = filename.split('_')[3]  # e.g., "100mVpS"
            electrode = filename.split('_')[4]  # e.g., "E1"
            
            print(f"   📊 Data: {len(voltage)} points, V: {voltage.min():.3f} to {voltage.max():.3f}V")
            print(f"   ⚡ Scan rate: {scan_rate}, Electrode: {electrode}")
            
            # Test Enhanced V4 API
            api_data = {
                'voltage': voltage.tolist(),
                'current': current.tolist(),
                'filename': filename
            }
            
            url = "http://127.0.0.1:8080/peak_detection/get-peaks/enhanced_v4"
            headers = {'Content-Type': 'application/json'}
            
            response = requests.post(url, data=json.dumps(api_data), headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success', False):
                    peaks = result.get('peaks', [])
                    
                    # วิเคราะห์ peaks
                    ox_peaks = [p for p in peaks if p.get('type') == 'oxidation']
                    red_peaks = [p for p in peaks if p.get('type') == 'reduction']
                    
                    # ตรวจสอบ edge effects (peaks ที่ max/min voltage)
                    edge_peaks = []
                    for peak in peaks:
                        pv = peak.get('voltage', 0)
                        if abs(pv - voltage.max()) < 0.05 or abs(pv - voltage.min()) < 0.05:
                            edge_peaks.append(peak)
                    
                    # สร้าง summary
                    file_result = {
                        'filename': filename,
                        'scan_rate': scan_rate,
                        'electrode': electrode,
                        'total_peaks': len(peaks),
                        'oxidation_peaks': len(ox_peaks),
                        'reduction_peaks': len(red_peaks),
                        'has_both_peaks': len(ox_peaks) > 0 and len(red_peaks) > 0,
                        'edge_peaks': len(edge_peaks),
                        'voltage_range': f"{voltage.min():.3f} to {voltage.max():.3f}V",
                        'peaks_detail': peaks,
                        'edge_detail': edge_peaks
                    }
                    
                    results.append(file_result)
                    
                    # แสดงผลลัพธ์
                    status = "✅" if len(peaks) > 0 else "❌"
                    both_peaks = "🎯" if file_result['has_both_peaks'] else "⚠️"
                    edge_warning = "🚨" if len(edge_peaks) > 0 else "✅"
                    
                    print(f"   {status} Peaks: {len(peaks)} total ({len(ox_peaks)} OX, {len(red_peaks)} RED) {both_peaks}")
                    
                    if len(peaks) > 0:
                        for peak in peaks:
                            conf = peak.get('confidence', 0)
                            print(f"      • {peak.get('type', 'unknown')[:3].upper()}: {peak.get('voltage', 0):.3f}V, {peak.get('current', 0):.1f}μA (conf: {conf:.0f}%)")
                    
                    if len(edge_peaks) > 0:
                        print(f"   {edge_warning} Edge effects: {len(edge_peaks)} peaks near voltage limits")
                        for edge in edge_peaks:
                            print(f"      ⚠️ {edge.get('type', 'unknown')}: {edge.get('voltage', 0):.3f}V (near edge)")
                    
                else:
                    print(f"   ❌ API Error: {result.get('error', 'Unknown')}")
                    
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"   💥 Error: {e}")
        
        print()
        time.sleep(0.5)  # หยุดเล็กน้อยเพื่อไม่ให้ server ติดขัด
    
    # สรุปผลการทดสอบ
    print("📈 SUMMARY ANALYSIS")
    print("=" * 50)
    
    if not results:
        print("❌ No successful tests!")
        return
    
    # สถิติ overall
    total_files = len(results)
    files_with_peaks = len([r for r in results if r['total_peaks'] > 0])
    files_with_both = len([r for r in results if r['has_both_peaks']])
    files_with_edges = len([r for r in results if r['edge_peaks'] > 0])
    
    ox_only_files = len([r for r in results if r['oxidation_peaks'] > 0 and r['reduction_peaks'] == 0])
    red_only_files = len([r for r in results if r['reduction_peaks'] > 0 and r['oxidation_peaks'] == 0])
    
    print(f"📊 Overall Statistics:")
    print(f"   • Total files tested: {total_files}")
    print(f"   • Files with any peaks: {files_with_peaks}/{total_files} ({files_with_peaks/total_files*100:.1f}%)")
    print(f"   • Files with both peaks: {files_with_both}/{total_files} ({files_with_both/total_files*100:.1f}%)")
    print(f"   • Files with only oxidation: {ox_only_files}/{total_files} ({ox_only_files/total_files*100:.1f}%)")
    print(f"   • Files with only reduction: {red_only_files}/{total_files} ({red_only_files/total_files*100:.1f}%)")
    print(f"   • Files with edge effects: {files_with_edges}/{total_files} ({files_with_edges/total_files*100:.1f}%)")
    
    # วิเคราะห์ตาม scan rate
    print(f"\n🔬 Analysis by Scan Rate:")
    scan_rates = {}
    for result in results:
        sr = result['scan_rate']
        if sr not in scan_rates:
            scan_rates[sr] = {'total': 0, 'both_peaks': 0, 'ox_only': 0, 'edge_effects': 0}
        
        scan_rates[sr]['total'] += 1
        if result['has_both_peaks']:
            scan_rates[sr]['both_peaks'] += 1
        elif result['oxidation_peaks'] > 0 and result['reduction_peaks'] == 0:
            scan_rates[sr]['ox_only'] += 1
        if result['edge_peaks'] > 0:
            scan_rates[sr]['edge_effects'] += 1
    
    for sr, stats in sorted(scan_rates.items()):
        both_pct = stats['both_peaks']/stats['total']*100 if stats['total'] > 0 else 0
        ox_pct = stats['ox_only']/stats['total']*100 if stats['total'] > 0 else 0
        edge_pct = stats['edge_effects']/stats['total']*100 if stats['total'] > 0 else 0
        
        print(f"   • {sr}: Both peaks {both_pct:.0f}%, OX-only {ox_pct:.0f}%, Edge effects {edge_pct:.0f}%")
    
    # แนะนำการแก้ไข
    print(f"\n💡 Recommendations:")
    
    if ox_only_files > files_with_both:
        print(f"   🔧 Reduction peak detection needs improvement:")
        print(f"      - Current algorithm may be too strict for reduction peaks")
        print(f"      - Consider lowering reduction peak thresholds")
        print(f"      - Check voltage range for reduction region (-0.4 to 0.4V)")
    
    if files_with_edges > 0:
        print(f"   ⚠️ Edge effect issues detected:")
        print(f"      - Some peaks detected at voltage limits")
        print(f"      - May need to exclude edge regions from detection")
        print(f"      - Consider expanding voltage scan range")
    
    if files_with_both < total_files * 0.8:  # Less than 80% have both peaks
        print(f"   📊 Overall detection rate could be improved:")
        print(f"      - For Ferrocyanide, should expect ~2 peaks per file")
        print(f"      - Current rate: {files_with_both/total_files*100:.1f}% have both peaks")
        print(f"      - Suggest algorithm tuning for this dataset")

if __name__ == "__main__":
    test_sample_files()
