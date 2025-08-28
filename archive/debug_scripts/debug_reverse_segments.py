#!/usr/bin/env python3
"""
ตรวจสอบ reverse segments ของ PiPot data เพื่อหาสาเหตุที่ baseline เป็นเส้นตรง
"""

import numpy as np
from baseline_detector_voltage_windows import voltage_window_baseline_detector

# โหลดข้อมูล PiPot
def test_pipot_segments():
    file_path = "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_20mVpS_E1_scan_06.csv"
    
    try:
        data = np.loadtxt(file_path, delimiter=',', skiprows=2)
        voltage = data[:, 0]
        current = data[:, 1] * 1e6  # แปลง A เป็น µA
        
        print(f"🔍 ตรวจสอบ segments ของ PiPot data")
        print(f"📊 ข้อมูล: {len(voltage)} จุด")
        print(f"⚡ Voltage: {voltage.min():.3f} ถึง {voltage.max():.3f} V")
        print(f"🔌 Current: {current.min():.3f} ถึง {current.max():.3f} µA")
        
        # รัน baseline detector
        result = voltage_window_baseline_detector(voltage, current)
        
        if isinstance(result, tuple) and len(result) == 3:
            forward_baseline, reverse_baseline, metadata = result
            
            print(f"\n📈 Forward baseline variation: {forward_baseline.max() - forward_baseline.min():.6f} µA")
            print(f"📉 Reverse baseline variation: {reverse_baseline.max() - reverse_baseline.min():.6f} µA")
            
            print(f"\n🔧 Metadata keys: {list(metadata.keys())}")
            
            # ตรวจสอบ forward segments
            if 'forward_segments' in metadata:
                forward_segs = metadata['forward_segments']
                print(f"\n📈 Forward segments: {len(forward_segs)} segments")
                for i, seg in enumerate(forward_segs[:3]):  # แสดงแค่ 3 segments แรก
                    print(f"  Segment {i+1}: V=[{seg.get('voltage_start', 'N/A'):.3f}:{seg.get('voltage_end', 'N/A'):.3f}]V, "
                          f"current_mean={seg.get('current_mean', 'N/A'):.6f}µA, "
                          f"R²={seg.get('r2', 'N/A'):.3f}, "
                          f"length={seg.get('length', 'N/A')}")
            
            # ตรวจสอบ reverse segments
            if 'reverse_segments' in metadata:
                reverse_segs = metadata['reverse_segments']
                print(f"\n📉 Reverse segments: {len(reverse_segs)} segments")
                for i, seg in enumerate(reverse_segs):  # แสดงทุก reverse segments
                    print(f"  Segment {i+1}: V=[{seg.get('voltage_start', 'N/A'):.3f}:{seg.get('voltage_end', 'N/A'):.3f}]V, "
                          f"current_mean={seg.get('current_mean', 'N/A'):.6f}µA, "
                          f"R²={seg.get('r2', 'N/A'):.3f}, "
                          f"length={seg.get('length', 'N/A')}")
                
                if reverse_segs:
                    # ตรวจสอบ current_mean ของ reverse segments
                    reverse_currents = [seg.get('current_mean', 0) for seg in reverse_segs]
                    print(f"\n📊 Reverse segment current values: {reverse_currents}")
                    print(f"📊 Reverse current range: {min(reverse_currents):.6f} ถึง {max(reverse_currents):.6f} µA")
                    print(f"📊 Reverse current variation: {max(reverse_currents) - min(reverse_currents):.6f} µA")
                    
                    if max(reverse_currents) - min(reverse_currents) < 0.01:
                        print(f"⚠️ WARNING: Reverse segments มี current ใกล้เคียงกันมาก!")
                        print(f"   นี่อาจเป็นสาเหตุที่ reverse baseline เป็นเส้นตรง")
                else:
                    print(f"❌ ไม่มี reverse segments!")
            
        else:
            print(f"❌ Unexpected result format: {type(result)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_pipot_segments()