#!/usr/bin/env python3
"""
Quick test for all peak detection methods
ทดสอบว่า method อื่น ๆ ทำงานปกติหรือไม่หลังจากแก้ไข Enhanced V4 Improved
"""

import requests
import json
import time

def test_all_methods():
    """Test all peak detection methods"""
    
    # Sample CV data
    sample_data = {
        "voltage": [0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05, 0.0, -0.05, -0.1, -0.05, 0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4],
        "current": [1e-6, 2e-6, 5e-6, 8e-6, 12e-6, 15e-6, 18e-6, 20e-6, 22e-6, 23e-6, 24e-6, 20e-6, 18e-6, 15e-6, 12e-6, 8e-6, 5e-6, 2e-6, 1e-6, 1e-6, 1e-6]
    }
    
    methods = ['ml', 'prominence', 'enhanced_v4', 'enhanced_v4_improved']
    
    print("🧪 Testing all peak detection methods...")
    print("=" * 50)
    
    for method in methods:
        print(f"\n🔍 Testing method: {method}")
        
        url = f"http://127.0.0.1:8080/get-peaks/{method}"
        
        try:
            response = requests.post(url, json=sample_data, timeout=15)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    success = result.get('success', False)
                    peaks = result.get('peaks', [])
                    
                    print(f"   ✅ Success: {success}")
                    print(f"   📊 Peaks: {len(peaks)}")
                    
                    if peaks:
                        print(f"   📊 First peak type: {type(peaks[0])}")
                        if isinstance(peaks[0], dict):
                            print(f"   📊 Peak structure: {list(peaks[0].keys())}")
                        
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON Error: {e}")
                    print(f"   📝 Raw response: {response.text[:200]}...")
                    
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   📝 Response: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout error")
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Connection error")
        except Exception as e:
            print(f"   💥 Unexpected error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Testing completed!")

if __name__ == "__main__":
    test_all_methods()
