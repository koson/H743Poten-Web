#!/usr/bin/env python3
"""
Test Cross-Instrument Calibration via API
"""

import requests
import json
import sys

def test_calibration_api():
    """Test the calibration API endpoints"""
    
    base_url = "http://localhost:5000"
    
    print("🔬 Testing Cross-Instrument Calibration API\n")
    
    # 1. Test measurement pairs
    print("1. Testing measurement pairs...")
    try:
        response = requests.get(f"{base_url}/api/calibration/measurement-pairs", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data.get('success')}")
            print(f"   📊 Pairs found: {data.get('count')}")
            
            if data.get('pairs'):
                pair = data['pairs'][0]
                stm32_id = pair['stm32_measurement']['id']
                palmsens_id = pair['palmsens_measurement']['id']
                print(f"   🎯 Testing pair: STM32 ID {stm32_id} vs PalmSens ID {palmsens_id}")
                
                # 2. Test actual calibration
                print("\n2. Testing calibration...")
                calibration_payload = {
                    "stm32_measurement_id": stm32_id,
                    "palmsens_measurement_id": palmsens_id
                }
                
                response = requests.post(
                    f"{base_url}/api/calibration/calibrate",
                    json=calibration_payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        cal_data = result['calibration_result']
                        print(f"   ✅ Calibration successful!")
                        print(f"   📈 R² Value: {cal_data['r_squared']:.4f}")
                        print(f"   🔧 Current Slope: {cal_data['current_slope']:.6f}")
                        print(f"   ⚡ Current Offset: {cal_data['current_offset']:.3e}")
                        print(f"   📊 Data Points: {cal_data['data_points']}")
                        
                        quality = ('excellent' if cal_data['r_squared'] > 0.95 else 
                                 'good' if cal_data['r_squared'] > 0.8 else 'fair')
                        print(f"   🏆 Quality: {quality.upper()}")
                        
                        # 3. Test calibration models
                        print("\n3. Testing calibration models...")
                        response = requests.get(f"{base_url}/api/calibration/models", timeout=10)
                        if response.status_code == 200:
                            models = response.json()
                            print(f"   ✅ Models available: {models.get('count')}")
                            if models.get('models'):
                                for key, model in models['models'].items():
                                    print(f"   📋 Model {key}: R²={model['r_squared']:.4f}, Quality={model['quality']}")
                        
                    else:
                        print(f"   ❌ Calibration failed: {result.get('error')}")
                else:
                    print(f"   ❌ HTTP Error: {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    
            else:
                print("   ⚠️  No measurement pairs available for testing")
                
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection Error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    print("\n🎯 Calibration API Test Complete!")
    return True

if __name__ == "__main__":
    success = test_calibration_api()
    sys.exit(0 if success else 1)