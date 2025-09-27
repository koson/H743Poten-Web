#!/usr/bin/env python3
"""
Test script to check CV scan rate setting capability
"""

import requests
import json

# Pi server URL
BASE_URL = "http://192.168.9.75:8080"

def test_cv_scan_rate():
    """Test CV measurement setup with different scan rates"""
    
    print("🧪 Testing CV Scan Rate Setting...")
    
    # Test different scan rates
    scan_rates = [0.01, 0.05, 0.1, 0.2, 0.5]
    
    for scan_rate in scan_rates:
        print(f"\n📏 Testing scan rate: {scan_rate} V/s")
        
        # CV parameters with specific scan rate
        params = {
            'mode': 'CV',
            'parameters': {
                'begin_voltage': 0.0,
                'upper_voltage': 1.0,
                'lower_voltage': -1.0,
                'scan_rate': scan_rate,  # Test this parameter
                'cycles': 1
            }
        }
        
        print(f"📡 Sending setup request: {json.dumps(params, indent=2)}")
        
        try:
            # Send setup request
            response = requests.post(f"{BASE_URL}/api/measurement/setup", 
                                   json=params, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            
            print(f"📥 Response status: {response.status_code}")
            print(f"📥 Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ Scan rate {scan_rate} V/s setup successful!")
                    
                    # Check if the scan rate was actually set by checking measurement service
                    status_response = requests.get(f"{BASE_URL}/api/cv/status", timeout=5)
                    if status_response.status_code == 200:
                        status = status_response.json()
                        if 'parameters' in status and 'scan_rate' in status['parameters']:
                            actual_rate = status['parameters']['scan_rate']
                            print(f"🔍 Confirmed scan rate in service: {actual_rate} V/s")
                            if abs(actual_rate - scan_rate) < 0.001:
                                print(f"✅ Scan rate correctly set!")
                            else:
                                print(f"❌ Scan rate mismatch! Set: {scan_rate}, Got: {actual_rate}")
                        else:
                            print(f"⚠️ No scan_rate in status response")
                else:
                    print(f"❌ Setup failed: {result.get('error', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🏁 CV Scan Rate Test Complete!")

if __name__ == "__main__":
    test_cv_scan_rate()