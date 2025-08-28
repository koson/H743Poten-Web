#!/usr/bin/env python3
"""
ทดสอบ API จริงด้วยไฟล์ PiPot เพื่อตรวจสอบ baseline
"""

import requests
import json
import numpy as np

# ทดสอบ API โดยการส่งข้อมูลจริงจากไฟล์ PiPot
def test_api_with_pipot_data():
    # อ่านข้อมูลจากไฟล์ PiPot
    file_path = "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_20mVpS_E1_scan_06.csv"
    
    try:
        # โหลดข้อมูล
        data = np.loadtxt(file_path, delimiter=',', skiprows=2)
        voltage = data[:, 0].tolist()
        current = (data[:, 1] * 1e6).tolist()  # แปลง A เป็น µA
        
        print(f"📂 โหลดไฟล์: {file_path}")
        print(f"📊 ข้อมูล: {len(voltage)} จุด")
        print(f"⚡ Voltage: {min(voltage):.3f} ถึง {max(voltage):.3f} V")
        print(f"🔌 Current: {min(current):.3f} ถึง {max(current):.3f} µA")
        
        # ทดสอบ API endpoint
        url = "http://127.0.0.1:8080/peak_detection/get-peaks/prominence"
        
        payload = {
            "voltage": voltage,
            "current": current
        }
        
        print(f"\n🔍 ส่งข้อมูลไป API: {url}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ API ตอบกลับสำเร็จ!")
            print(f"📊 Keys ใน response: {list(result.keys())}")
            
            # ตรวจสอบ baseline
            baseline_data = result.get('baseline', {})
            print(f"\n📈 Baseline data:")
            print(f"  Keys: {list(baseline_data.keys())}")
            
            if 'forward' in baseline_data:
                forward = baseline_data['forward']
                print(f"  📈 Forward baseline: {len(forward)} จุด")
                if forward:
                    print(f"     ช่วง: {min(forward):.6f} ถึง {max(forward):.6f} µA")
                    print(f"     ค่าเฉลี่ย: {sum(forward)/len(forward):.6f} µA")
                    print(f"     ตัวอย่าง 5 จุดแรก: {forward[:5]}")
            
            if 'reverse' in baseline_data:
                reverse = baseline_data['reverse']
                print(f"  📉 Reverse baseline: {len(reverse)} จุด")
                if reverse:
                    print(f"     ช่วง: {min(reverse):.6f} ถึง {max(reverse):.6f} µA")
                    print(f"     ค่าเฉลี่ย: {sum(reverse)/len(reverse):.6f} µA")
                    print(f"     ตัวอย่าง 5 จุดแรก: {reverse[:5]}")
            
            if 'full' in baseline_data:
                full = baseline_data['full']
                print(f"  📊 Full baseline: {len(full)} จุด")
                if full:
                    print(f"     ช่วง: {min(full):.6f} ถึง {max(full):.6f} µA")
                    print(f"     ค่าเฉลี่ย: {sum(full)/len(full):.6f} µA")
                    print(f"     ความแปรปรวน: {max(full) - min(full):.6f} µA")
                    
                    # ตรวจสอบว่า baseline เป็น 0 หรือไม่
                    non_zero_count = sum(1 for x in full if abs(x) > 1e-10)
                    print(f"     จุดที่ไม่ใช่ศูนย์: {non_zero_count}/{len(full)}")
                    
                    if all(abs(x) < 1e-6 for x in full):
                        print(f"     ⚠️ WARNING: Baseline ยังเป็นศูนย์อยู่!")
                    else:
                        print(f"     ✅ Baseline มีค่าที่เหมาะสม!")
            
            # ตรวจสอบ metadata
            metadata = baseline_data.get('metadata', {})
            print(f"\n🔧 Metadata:")
            for key, value in metadata.items():
                print(f"  {key}: {value}")
            
            # ตรวจสอบ debug info
            debug = baseline_data.get('debug', {})
            print(f"\n🐛 Debug info:")
            for key, value in debug.items():
                print(f"  {key}: {value}")
            
            # ตรวจสอบ peaks
            peaks = result.get('peaks', [])
            print(f"\n🔺 Peaks ที่พบ: {len(peaks)} peak(s)")
            for i, peak in enumerate(peaks[:3]):  # แสดงแค่ 3 peaks แรก
                print(f"  Peak {i+1}: V={peak.get('voltage', 'N/A'):.3f}V, I={peak.get('current', 'N/A'):.3f}µA, type={peak.get('type', 'N/A')}")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except FileNotFoundError:
        print(f"❌ ไม่พบไฟล์: {file_path}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_with_pipot_data()