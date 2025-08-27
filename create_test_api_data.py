#!/usr/bin/env python3
"""
ทดสอบ Enhanced V3 Web API Integration
"""

import json
import pandas as pd

def create_test_api_data():
    """สร้างข้อมูลทดสอบสำหรับ API"""
    
    # โหลดข้อมูลจริง
    test_file = "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_100mVpS_E1_scan_06.csv"
    
    try:
        df = pd.read_csv(test_file, skiprows=1)
        voltage = df['V'].values.tolist()
        current = df['uA'].values.tolist()
        
        api_data = {
            "voltage": voltage,
            "current": current,
            "filename": test_file
        }
        
        # บันทึกเป็นไฟล์ JSON สำหรับ curl
        with open('test_enhanced_v3_api_data.json', 'w') as f:
            json.dump(api_data, f, indent=2)
        
        print(f"✅ Created API test data with {len(voltage)} points")
        print(f"📊 Voltage range: {min(voltage):.3f} to {max(voltage):.3f}V")
        print(f"⚡ Current range: {min(current):.3f} to {max(current):.3f}µA")
        print(f"💾 Saved to: test_enhanced_v3_api_data.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        return False

if __name__ == "__main__":
    create_test_api_data()
