#!/usr/bin/env python3
"""
ทดสอบ cv_baseline_detector_v4 ด้วย peak_regions เหมือนกับที่ API ใช้
"""

import numpy as np
from baseline_detector_v4 import cv_baseline_detector_v4

# โหลดข้อมูล PiPot และทดสอบด้วย peak_regions เหมือน API
def test_with_peak_regions():
    file_path = "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_20mVpS_E1_scan_06.csv"
    
    try:
        data = np.loadtxt(file_path, delimiter=',', skiprows=2)
        voltage = data[:, 0]
        current = data[:, 1] * 1e6  # แปลง A เป็น µA
        
        print(f"🔍 ทดสอบ cv_baseline_detector_v4 ด้วย peak_regions เหมือน API")
        print(f"📊 ข้อมูล: {len(voltage)} จุด")
        
        # จำลอง peak_regions ที่ API ใช้ (จาก log: [(54, 64), (107, 117), (196, 206), (87, 97), (170, 180)])
        peak_regions = [(54, 64), (107, 117), (196, 206), (87, 97), (170, 180)]
        print(f"🎯 Peak regions: {peak_regions}")
        
        # ทดสอบแบบไม่มี peak_regions (ค่าเริ่มต้น)
        print(f"\n=== ทดสอบแบบไม่มี peak_regions ===")
        result1 = cv_baseline_detector_v4(voltage, current, None)
        forward1, reverse1, metadata1 = result1
        print(f"📉 Reverse variation (no peak_regions): {reverse1.max() - reverse1.min():.6f} µA")
        print(f"📉 Reverse unique values: {len(np.unique(reverse1))}/{len(reverse1)}")
        
        # ทดสอบแบบมี peak_regions (เหมือน API)
        print(f"\n=== ทดสอบแบบมี peak_regions ===")
        result2 = cv_baseline_detector_v4(voltage, current, peak_regions)
        forward2, reverse2, metadata2 = result2
        print(f"📉 Reverse variation (with peak_regions): {reverse2.max() - reverse2.min():.6f} µA")
        print(f"📉 Reverse unique values: {len(np.unique(reverse2))}/{len(reverse2)}")
        
        # เปรียบเทียบ
        print(f"\n=== เปรียบเทียบ ===")
        if reverse1.max() - reverse1.min() > 0.01:
            print(f"✅ ไม่มี peak_regions: Reverse มี variation")
        else:
            print(f"❌ ไม่มี peak_regions: Reverse เป็นเส้นตรง")
            
        if reverse2.max() - reverse2.min() > 0.01:
            print(f"✅ มี peak_regions: Reverse มี variation")
        else:
            print(f"❌ มี peak_regions: Reverse เป็นเส้นตรง")
            print(f"   🎯 นี่คือสาเหตุที่ API ได้ reverse เป็นเส้นตรง!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_with_peak_regions()