#!/usr/bin/env python3
"""
ตรวจสอบผลลัพธ์จาก voltage_window_baseline_detector โดยตรง
"""

import numpy as np
from baseline_detector_voltage_windows import voltage_window_baseline_detector

# โหลดข้อมูล PiPot และทดสอบ detector โดยตรง
def test_detector_direct():
    file_path = "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_20mVpS_E1_scan_06.csv"
    
    try:
        data = np.loadtxt(file_path, delimiter=',', skiprows=2)
        voltage = data[:, 0]
        current = data[:, 1] * 1e6  # แปลง A เป็น µA
        
        print(f"🔍 ทดสอบ voltage_window_baseline_detector โดยตรง")
        print(f"📊 ข้อมูล: {len(voltage)} จุด")
        print(f"⚡ Voltage: {voltage.min():.3f} ถึง {voltage.max():.3f} V")
        print(f"🔌 Current: {current.min():.3f} ถึง {current.max():.3f} µA")
        
        # รัน detector โดยตรง
        result = voltage_window_baseline_detector(voltage, current)
        
        if isinstance(result, tuple) and len(result) == 3:
            forward_baseline, reverse_baseline, metadata = result
            
            print(f"\n✅ Detector ส่งผลลัพธ์สำเร็จ!")
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
            
            # ตรวจสอบว่าข้อมูลเป็น numpy array หรือไม่
            print(f"\n🔧 Data types:")
            print(f"   Forward is numpy array: {isinstance(forward_baseline, np.ndarray)}")
            print(f"   Reverse is numpy array: {isinstance(reverse_baseline, np.ndarray)}")
            
            # ตรวจสอบว่าการต่อ array ทำงานถูกต้องหรือไม่
            baseline_full = np.concatenate([forward_baseline, reverse_baseline])
            print(f"\n📊 Full baseline (concatenated): {len(baseline_full)} จุด")
            print(f"   Range: {baseline_full.min():.6f} ถึง {baseline_full.max():.6f} µA")
            print(f"   Variation: {baseline_full.max() - baseline_full.min():.6f} µA")
            
            # ตรวจสอบ .tolist() conversion
            forward_list = forward_baseline.tolist()
            reverse_list = reverse_baseline.tolist()
            
            print(f"\n📋 After .tolist() conversion:")
            print(f"   Forward list range: {min(forward_list):.6f} ถึง {max(forward_list):.6f} µA")
            print(f"   Reverse list range: {min(reverse_list):.6f} ถึง {max(reverse_list):.6f} µA")
            print(f"   Forward variation: {max(forward_list) - min(forward_list):.6f} µA")
            print(f"   Reverse variation: {max(reverse_list) - min(reverse_list):.6f} µA")
            
            # ตรวจสอบ unique values
            unique_forward = len(set(forward_list))
            unique_reverse = len(set(reverse_list))
            print(f"\n🔢 Unique values:")
            print(f"   Forward unique values: {unique_forward}/{len(forward_list)}")
            print(f"   Reverse unique values: {unique_reverse}/{len(reverse_list)}")
            
            if unique_reverse == 1:
                print(f"❌ PROBLEM: Reverse baseline มีแค่ค่าเดียว!")
                print(f"   Value: {reverse_list[0]}")
            else:
                print(f"✅ Reverse baseline มีหลายค่า")
                
        else:
            print(f"❌ Unexpected result format: {type(result)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_detector_direct()