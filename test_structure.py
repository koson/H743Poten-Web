#!/usr/bin/env python3

import requests
import json

# Test Enhanced V4 Improved API
url = "http://127.0.0.1:8080/get-peaks/enhanced_v4_improved"

# Test with multi-file data (real workflow)
data_multi = {
    "dataFiles": [
        {
            "voltage": [0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05, 0.0, -0.05, -0.1, -0.05, 0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4],
            "current": [1e-6, 2e-6, 5e-6, 8e-6, 12e-6, 15e-6, 18e-6, 20e-6, 22e-6, 23e-6, 24e-6, 20e-6, 18e-6, 15e-6, 12e-6, 8e-6, 5e-6, 2e-6, 1e-6, 1e-6, 1e-6]
        },
        {
            "voltage": [0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05, 0.0, -0.05, -0.1, -0.05, 0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4],
            "current": [2e-6, 4e-6, 10e-6, 16e-6, 24e-6, 30e-6, 36e-6, 40e-6, 44e-6, 46e-6, 48e-6, 40e-6, 36e-6, 30e-6, 24e-6, 16e-6, 10e-6, 4e-6, 2e-6, 2e-6, 2e-6]
        }
    ]
}

print("\n🧪 Testing multi-file data (workflow format)...")
try:
    response = requests.post(url, json=data_multi, timeout=10)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success', False)}")
        
        peaks = result.get('peaks', [])
        print(f"Peaks type: {type(peaks)}")
        print(f"Peaks length: {len(peaks)}")
        
        if peaks:
            print(f"First item type: {type(peaks[0])}")
            if isinstance(peaks[0], dict):
                print("✅ FLAT STRUCTURE - peaks are dict objects")
                print(f"First peak keys: {list(peaks[0].keys())}")
                print(f"Sample peak: voltage={peaks[0].get('voltage', 'N/A')}, current={peaks[0].get('current', 'N/A')}")
            elif isinstance(peaks[0], list):
                print("⚠️ NESTED STRUCTURE - peaks contains lists")
                print(f"First nested length: {len(peaks[0])}")
            else:
                print(f"Other type: {peaks[0]}")
        else:
            print("No peaks found in multi-file test")
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text[:500]}")

except Exception as e:
    print(f"Error: {e}")

try:
    print("🌐 Testing Enhanced V4 Improved API...")
    
    # Test single trace first
    single_data = {
        "voltage": [0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05, 0.0, -0.05, -0.1, -0.05, 0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4],
        "current": [1e-6, 2e-6, 5e-6, 8e-6, 12e-6, 15e-6, 18e-6, 20e-6, 22e-6, 23e-6, 24e-6, 20e-6, 18e-6, 15e-6, 12e-6, 8e-6, 5e-6, 2e-6, 1e-6, 1e-6, 1e-6]
    }
    
    response = requests.post(url, json=single_data, timeout=10)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success', False)}")
        
        peaks = result.get('peaks', [])
        print(f"Peaks type: {type(peaks)}")
        print(f"Peaks length: {len(peaks)}")
        
        if peaks:
            print(f"First item type: {type(peaks[0])}")
            if isinstance(peaks[0], dict):
                print("✅ FLAT STRUCTURE - peaks are dict objects")
                print(f"First peak keys: {list(peaks[0].keys())}")
            elif isinstance(peaks[0], list):
                print("⚠️ NESTED STRUCTURE - peaks contains lists")
                print(f"First nested length: {len(peaks[0])}")
            else:
                print(f"Other type: {peaks[0]}")
        else:
            print("No peaks found")
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text[:500]}")

except Exception as e:
    print(f"Error: {e}")
