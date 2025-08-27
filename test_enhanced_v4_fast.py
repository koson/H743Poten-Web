#!/usr/bin/env python3
"""
Fast Test Enhanced V4 Improved - Web API Compatible
ทดสอบ Enhanced V4 Improved แบบเร็วตามเว็บแอป
"""

import pandas as pd
import numpy as np
import time
import json

def test_enhanced_v4_fast():
    print("⚡ Fast Test Enhanced V4 Improved")
    print("=" * 40)
    
    try:
        from enhanced_detector_v4_improved import EnhancedDetectorV4Improved
        
        # โหลดไฟล์
        test_file = 'Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv'
        data = pd.read_csv(test_file, skiprows=2, names=['voltage', 'current'])
        
        print(f"✅ โหลดไฟล์: {len(data)} points")
        
        # สร้าง detector
        start_time = time.time()
        detector = EnhancedDetectorV4Improved(confidence_threshold=25.0)
        print(f"✅ สร้าง detector: {time.time() - start_time:.3f}s")
        
        # เตรียมข้อมูล (แบบเว็บแอป)
        cv_data = {
            'voltage': data['voltage'].tolist(),
            'current': data['current'].tolist()
        }
        
        print("🔬 เริ่มวิเคราะห์...")
        analysis_start = time.time()
        
        # วิเคราะห์
        results = detector.analyze_cv_data(cv_data)
        
        analysis_time = time.time() - analysis_start
        print(f"✅ วิเคราะห์เสร็จ: {analysis_time:.3f}s")
        
        # แสดงผล
        if results and isinstance(results, dict):
            peaks = results.get('peaks', [])
            print(f"\\n🎯 ผลลัพธ์:")
            print(f"  Total peaks: {len(peaks)}")
            
            ox_peaks = [p for p in peaks if p.get('type') == 'oxidation']
            red_peaks = [p for p in peaks if p.get('type') == 'reduction']
            
            print(f"  Oxidation peaks: {len(ox_peaks)}")
            print(f"  Reduction peaks: {len(red_peaks)}")
            
            if peaks:
                print(f"\\n📋 Peak details:")
                for i, peak in enumerate(peaks[:3]):  # แสดงแค่ 3 peaks แรก
                    voltage = peak.get('voltage', 0)
                    current = peak.get('current', 0)
                    peak_type = peak.get('type', 'unknown')
                    confidence = peak.get('confidence', 0)
                    
                    print(f"    Peak {i+1}: {peak_type} @ {voltage:.3f}V, {current:.1f}µA (conf: {confidence:.1f}%)")
            
            # ตรวจสอบข้อมูลอื่นๆ
            print(f"\\n🔍 Additional info:")
            print(f"  Method: {results.get('method', 'unknown')}")
            print(f"  Confidence threshold: {results.get('confidence_threshold', 0)}%")
            print(f"  Processing time: {results.get('processing_time', 0):.3f}s")
            
            return True
        else:
            print("❌ ไม่มีผลลัพธ์หรือรูปแบบไม่ถูกต้อง")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_v4_fast()
    if success:
        print("\\n🎉 ทดสอบสำเร็จ!")
    else:
        print("\\n💥 ทดสอบล้มเหลว!")
