#!/usr/bin/env python3
"""
Debug Enhanced Detector V4 Improved
ตรวจสอบว่าทำไม Enhanced Detector ไม่หา peaks เจอ
"""

import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import os
import sys

def debug_enhanced_detector():
    print("🔍 Debug Enhanced Detector V4 Improved")
    print("=" * 50)
    
    # อ่านไฟล์ตัวอย่าง
    test_file = 'Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv'
    
    if not os.path.exists(test_file):
        print(f"❌ ไม่พบไฟล์: {test_file}")
        return
        
    # โหลดข้อมูล
    data = pd.read_csv(test_file, skiprows=2, names=['voltage', 'current'])
    print(f"✅ โหลดไฟล์สำเร็จ: {len(data)} data points")
    print(f"Voltage range: {data['voltage'].min():.3f} to {data['voltage'].max():.3f} V")
    print(f"Current range: {data['current'].min():.6e} to {data['current'].max():.6e} A")
    print()
    
    # ทดสอบ Simple Peak Detection
    print("🔬 Simple Peak Detection:")
    current = data['current'].values
    peaks_pos, _ = find_peaks(current, height=np.max(current) * 0.1)
    peaks_neg, _ = find_peaks(-current, height=-np.min(current) * 0.1)
    print(f"  Anodic peaks: {len(peaks_pos)}")
    print(f"  Cathodic peaks: {len(peaks_neg)}")
    
    if len(peaks_pos) > 0:
        print(f"  Anodic peak voltages: {data['voltage'].iloc[peaks_pos].values}")
    if len(peaks_neg) > 0:
        print(f"  Cathodic peak voltages: {data['voltage'].iloc[peaks_neg].values}")
    print()
    
    # ทดสอบ Enhanced Detector
    print("🚀 Enhanced Detector V4 Improved:")
    try:
        from enhanced_detector_v4_improved import EnhancedDetectorV4Improved
        
        # ทดสอบหลาย threshold
        thresholds = [1.0, 5.0, 10.0, 15.0, 20.0]
        
        for threshold in thresholds:
            print(f"  Testing threshold: {threshold}%")
            detector = EnhancedDetectorV4Improved(confidence_threshold=threshold)
            
            # เตรียมข้อมูล
            cv_data = {
                'voltage': data['voltage'].values,
                'current': data['current'].values
            }
            
            try:
                results = detector.analyze_cv_data(cv_data)
                
                if results:
                    confidence = results.get('confidence', 0)
                    anodic_peaks = results.get('anodic_peaks', [])
                    cathodic_peaks = results.get('cathodic_peaks', [])
                    
                    print(f"    ✅ Confidence: {confidence:.1f}%")
                    print(f"    Anodic peaks: {len(anodic_peaks)}")
                    print(f"    Cathodic peaks: {len(cathodic_peaks)}")
                    
                    if len(anodic_peaks) > 0 or len(cathodic_peaks) > 0:
                        print(f"    🎯 พบ peaks ที่ threshold {threshold}%!")
                        break
                else:
                    print(f"    ❌ ไม่มีผลลัพธ์")
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
                
        print()
        
    except ImportError as e:
        print(f"❌ ไม่สามารถ import Enhanced Detector: {e}")
        return
    
    print("🎯 สรุป:")
    print("- Simple detector ทำงานได้")
    print("- Enhanced detector ต้องตรวจสอบเพิ่มเติม")

if __name__ == "__main__":
    debug_enhanced_detector()
