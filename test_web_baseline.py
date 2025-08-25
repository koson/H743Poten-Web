#!/usr/bin/env python3
"""
Test web API baseline detection after fixing unit conversion
"""

import requests
import json
import os

def test_web_baseline_detection():
    """Test baseline detection via web API"""
    print("🌐 Testing Web API Baseline Detection (Fixed Units)")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8080"
    
    # Test file upload and baseline detection
    csv_file = "test_cv_data_ua.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ Test CSV file not found: {csv_file}")
        return
    
    try:
        # Test load_saved_file endpoint with our test CSV
        print("📤 Testing CSV file loading via API...")
        
        # Copy test file to a location the API can access
        import shutil
        test_file_path = os.path.abspath(csv_file)
        
        response = requests.get(f"{base_url}/api/load_saved_file/{test_file_path}", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Upload failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        result = response.json()
        
        if not result.get('success'):
            print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
            return
        
        print("✅ File uploaded successfully")
        
        # Check if data loaded correctly
        data = result.get('data', {})
        voltage = data.get('voltage', [])
        current = data.get('current', [])
        
        if not voltage or not current:
            print("❌ No voltage/current data in response")
            return
        
        print(f"📊 Loaded {len(voltage)} data points")
        print(f"🔋 Voltage range: {min(voltage):.3f} to {max(voltage):.3f} V")
        print(f"⚡ Current range: {min(current):.3f} to {max(current):.3f} µA")
        
        # Check if current values are in correct µA range
        current_magnitude = max(abs(min(current)), abs(max(current)))
        if current_magnitude < 0.1:
            print("❌ CRITICAL: Current values still too small - unit conversion not fixed!")
            return
        elif current_magnitude >= 1.0:
            print("✅ Current values are in correct µA range - unit fix successful!")
        
        # Test baseline detection if available
        print("\n🔍 Testing baseline detection via API...")
        
        # Check if baseline detection endpoint exists
        try:
            baseline_response = requests.get(f"{base_url}/api/get_peaks/baseline", timeout=10)
            
            if baseline_response.status_code == 200:
                baseline_result = baseline_response.json()
                
                if baseline_result.get('success'):
                    print("✅ Baseline detection via API successful!")
                    
                    baseline_data = baseline_result.get('baseline', {})
                    if baseline_data:
                        print(f"   Algorithm: {baseline_data.get('algorithm', 'Unknown')}")
                        
                        baseline_points = baseline_data.get('points', [])
                        if baseline_points:
                            baseline_voltages = [p[0] for p in baseline_points]
                            baseline_currents = [p[1] for p in baseline_points]
                            print(f"   Baseline range: {min(baseline_voltages):.3f} to {max(baseline_voltages):.3f} V")
                            print(f"   Baseline current: {min(baseline_currents):.3f} to {max(baseline_currents):.3f} µA")
                else:
                    print("❌ Baseline detection failed via API")
                    print(f"   Error: {baseline_result.get('error', 'Unknown error')}")
            else:
                print(f"⚠️  Baseline detection endpoint returned status {baseline_response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Could not test baseline detection endpoint: {str(e)}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {str(e)}")
        print("   Make sure the server is running on http://127.0.0.1:8080")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🏁 Web API test completed")

if __name__ == "__main__":
    test_web_baseline_detection()