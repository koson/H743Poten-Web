#!/usr/bin/env python3
"""
Test the updated API with case-insensitive unit headers
"""

import requests
import json

def test_api():
    print("🧪 Testing API after unit header fix...")
    
    # Test with a PiPot file that should have 'uA' header
    test_file = "Test_data/Stm32/Pipot_Ferro_1_0mM_20mVpS_E4_scan_05.csv"
    
    try:
        # Test load_csv_file endpoint
        response = requests.post(
            'http://localhost:5000/api/load_csv_file',
            json={'file_path': test_file},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ API responded successfully")
                print(f"Data points: {len(data.get('data', []))}")
                
                # Check current values
                current_data = data.get('data', [])
                if current_data:
                    sample_currents = [abs(float(point['current'])) for point in current_data[:5]]
                    print(f"Sample current values: {sample_currents}")
                    
                    # Check if values are in reasonable µA range (not 1e-7)
                    if any(curr > 1e-3 for curr in sample_currents):
                        print("✅ Current values appear to be in µA range")
                    else:
                        print("❌ Current values still very low")
                
                # Check baseline
                baseline_data = data.get('baseline_data', [])
                if baseline_data:
                    baseline_currents = [abs(float(point['current'])) for point in baseline_data[:5]]
                    print(f"Sample baseline values: {baseline_currents}")
                    
                    # Check if baseline is not flat
                    if len(set([round(curr, 6) for curr in baseline_currents[:10]])) > 1:
                        print("✅ Baseline appears to have variation (not flat)")
                    else:
                        print("❌ Baseline appears flat")
                else:
                    print("❌ No baseline data found")
                    
            else:
                print(f"❌ API error: {data.get('error')}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_api()