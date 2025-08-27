#!/usr/bin/env python3
"""
Test Enhanced V4 Improved - Compare with Web API method
เปรียบเทียบวิธีเรียกใช้ในเว็บแอปกับ PLS workflow
"""

import pandas as pd
import numpy as np
import json

def test_enhanced_v4_improved_web_method():
    print("🔬 Test Enhanced V4 Improved - Web API Method")
    print("=" * 60)
    
    # อ่านไฟล์ตัวอย่าง
    test_file = 'Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv'
    data = pd.read_csv(test_file, skiprows=2, names=['voltage', 'current'])
    
    print(f"✅ โหลดไฟล์: {len(data)} data points")
    print(f"Voltage range: {data['voltage'].min():.3f} to {data['voltage'].max():.3f} V")
    print(f"Current range: {data['current'].min():.6e} to {data['current'].max():.6e} A")
    print()
    
    # ทดสอบ Enhanced V4 Improved แบบเว็บแอป
    try:
        from enhanced_detector_v4_improved import EnhancedDetectorV4Improved
        
        # 1. ทดสอบแบบที่เราใช้ใน PLS (ไม่เจอ peaks)
        print("🧪 Method 1: PLS Workflow style")
        detector1 = EnhancedDetectorV4Improved(confidence_threshold=25.0)
        cv_data = {
            'voltage': data['voltage'].values,
            'current': data['current'].values
        }
        
        result1 = detector1.analyze_cv_data(cv_data)
        print(f"  Result type: {type(result1)}")
        print(f"  Keys: {list(result1.keys()) if isinstance(result1, dict) else 'Not a dict'}")
        
        if isinstance(result1, dict):
            confidence = result1.get('confidence', 0)
            print(f"  Confidence: {confidence}%")
            
            # ตรวจสอบ peaks
            peaks = result1.get('peaks', [])
            anodic_peaks = result1.get('anodic_peaks', [])
            cathodic_peaks = result1.get('cathodic_peaks', [])
            
            print(f"  Peaks found: {len(peaks)}")
            print(f"  Anodic peaks: {len(anodic_peaks)}")
            print(f"  Cathodic peaks: {len(cathodic_peaks)}")
        print()
        
        # 2. ทดสอบแบบเว็บแอป (convert เป็น list ก่อน)
        print("🌐 Method 2: Web API style")
        detector2 = EnhancedDetectorV4Improved(confidence_threshold=25.0)
        data_dict = {
            'voltage': data['voltage'].tolist(),  # Convert to list like web API
            'current': data['current'].tolist()   # Convert to list like web API
        }
        
        result2 = detector2.analyze_cv_data(data_dict)
        print(f"  Result type: {type(result2)}")
        print(f"  Keys: {list(result2.keys()) if isinstance(result2, dict) else 'Not a dict'}")
        
        if isinstance(result2, dict):
            confidence = result2.get('confidence', 0)
            print(f"  Confidence: {confidence}%")
            
            # ตรวจสอบ peaks
            peaks = result2.get('peaks', [])
            anodic_peaks = result2.get('anodic_peaks', [])
            cathodic_peaks = result2.get('cathodic_peaks', [])
            
            print(f"  Peaks found: {len(peaks)}")
            print(f"  Anodic peaks: {len(anodic_peaks)}")
            print(f"  Cathodic peaks: {len(cathodic_peaks)}")
            
            # แสดงรายละเอียด peaks ถ้ามี
            if len(peaks) > 0:
                print(f"  Peak details:")
                for i, peak in enumerate(peaks[:3]):  # แสดงแค่ 3 peaks แรก
                    print(f"    Peak {i+1}: {peak}")
        print()
        
        # 3. ทดสอบด้วย threshold ต่ำลง
        print("🎯 Method 3: Lower threshold")
        detector3 = EnhancedDetectorV4Improved(confidence_threshold=5.0)
        result3 = detector3.analyze_cv_data(data_dict)
        
        if isinstance(result3, dict):
            confidence = result3.get('confidence', 0)
            peaks = result3.get('peaks', [])
            print(f"  Confidence: {confidence}%")
            print(f"  Peaks found: {len(peaks)}")
        
    except ImportError as e:
        print(f"❌ ไม่สามารถ import Enhanced V4 Improved: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_enhanced_v4_improved_web_method()
