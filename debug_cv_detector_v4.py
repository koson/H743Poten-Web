#!/usr/bin/env python3
"""
ทดสอบ cv_baseline_detector_v4 โดยตรงเพื่อเปรียบเทียบกับ voltage_window_baseline_detector
"""

import numpy as np
from baseline_detector_v4 import cv_baseline_detector_v4

# โหลดข้อมูล PiPot และทดสอบ cv_baseline_detector_v4
def test_cv_detector_v4():
    file_path = "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_20mVpS_E1_scan_06.csv"
    
    try:
        data = np.loadtxt(file_path, delimiter=',', skiprows=2)
        voltage = data[:, 0]
        current = data[:, 1] * 1e6  # แปลง A เป็น µA
        
        print(f"🔍 ทดสอบ cv_baseline_detector_v4 โดยตรง")
        print(f"📊 ข้อมูล: {len(voltage)} จุด")
        print(f"⚡ Voltage: {voltage.min():.3f} ถึง {voltage.max():.3f} V")
        print(f"🔌 Current: {current.min():.3f} ถึง {current.max():.3f} µA")
        
        # รัน cv_baseline_detector_v4
        result = cv_baseline_detector_v4(voltage, current)
        
        if isinstance(result, tuple) and len(result) == 3:
            forward_baseline, reverse_baseline, metadata = result
            
            print(f"\n✅ cv_baseline_detector_v4 ส่งผลลัพธ์สำเร็จ!")
            print(f"📈 Forward baseline: {len(forward_baseline)} จุด")
            print(f"   Type: {type(forward_baseline)}")
            print(f"   Range: {forward_baseline.min():.6f} ถึง {forward_baseline.max():.6f} µA")
            print(f"   Variation: {forward_baseline.max() - forward_baseline.min():.6f} µA")
            print(f"   Sample values: {forward_baseline[:5]}")
            
            print(f"\n📉 Reverse baseline: {len(reverse_baseline)} จุด")
            print(f"   Type: {type(reverse_baseline)}")
            print(f"   Range: {reverse_baseline.min():.6f} ถึง {reverse_baseline.max():.6f} µA")
            print(f"   Variation: {reverse_baseline.max() - reverse_baseline.min():.6f} µA")
            print(f"   Sample values: {reverse_baseline[:5]}")
            
            # ตรวจสอบ unique values
            unique_forward = len(np.unique(forward_baseline))
            unique_reverse = len(np.unique(reverse_baseline))
            print(f"\n🔢 Unique values:")
            print(f"   Forward unique values: {unique_forward}/{len(forward_baseline)}")
            print(f"   Reverse unique values: {unique_reverse}/{len(reverse_baseline)}")
            
            if unique_reverse == 1:
                print(f"❌ PROBLEM: cv_baseline_detector_v4 ส่ง reverse baseline เป็นค่าเดียว!")
                print(f"   Value: {reverse_baseline[0]}")
            else:
                print(f"✅ cv_baseline_detector_v4 ส่ง reverse baseline มีหลายค่า")
                
            # ตรวจสอบ metadata
            print(f"\n🔧 Metadata keys: {list(metadata.keys())}")
            print(f"   method: {metadata.get('method', 'N/A')}")
            print(f"   error: {metadata.get('error', 'N/A')}")
                
        else:
            print(f"❌ Unexpected result format: {type(result)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cv_detector_v4()