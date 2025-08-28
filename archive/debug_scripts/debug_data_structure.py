#!/usr/bin/env python3
"""
Debug data structure for Enhanced V4 Improved API
ตรวจสอบว่า flattening logic ทำงานหรือไม่
"""

import json
import requests
import time

def test_api_structure():
    """Test the API data structure"""
    
    # Wait for server to be ready
    print("⏳ Waiting for server...")
    time.sleep(3)
    
    url = "http://127.0.0.1:8080/get-peaks/enhanced_v4_improved"
    
    # Test with files array (wrong format - should cause 400)
    payload_files = {
        "files": ["Test_data/Palmsens/Palmsens_0.5mM/Pipot_Ferro_0_5mM_20mVpS_E1_scan_02.txt"]
    }
    
    # Test with single trace format
    sample_data = {
        "voltage": [0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05, 0.0, -0.05, -0.1, -0.05, 0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4],
        "current": [1e-6, 2e-6, 5e-6, 8e-6, 12e-6, 15e-6, 18e-6, 20e-6, 22e-6, 23e-6, 24e-6, 20e-6, 18e-6, 15e-6, 12e-6, 8e-6, 5e-6, 2e-6, 1e-6, 1e-6, 1e-6]
    }
    
    print("🧪 Testing files format (should fail)...")
    test_format(url, payload_files, "files")
    
    print("\n🧪 Testing single trace format...")
    test_format(url, sample_data, "single_trace")

def test_format(url, payload, test_name):
    """Test a specific payload format"""
    try:
        print(f"🌐 Testing {test_name}: {url}")
        print(f"📤 Payload keys: {list(payload.keys())}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Success: {data.get('success', False)}")
            
            peaks = data.get('peaks', [])
            print(f"📊 Peaks type: {type(peaks)}")
            print(f"📊 Peaks length: {len(peaks)}")
            
            if peaks:
                print(f"📊 First item type: {type(peaks[0])}")
                if isinstance(peaks[0], dict):
                    print(f"📊 First peak keys: {list(peaks[0].keys())}")
                elif isinstance(peaks[0], list):
                    print(f"⚠️  NESTED STRUCTURE DETECTED!")
                    print(f"📊 First item length: {len(peaks[0])}")
                    if peaks[0]:
                        print(f"📊 First nested peak type: {type(peaks[0][0])}")
                else:
                    print(f"📊 First item value: {peaks[0]}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📝 Response: {response.text[:500]}...")
    
    except Exception as e:
        print(f"💥 Exception: {e}")

if __name__ == "__main__":
    test_api_structure()
