#!/usr/bin/env python3

import requests
import json

url = "http://127.0.0.1:8080/get-peaks/enhanced_v4_improved"

multi_data = {
    "dataFiles": [
        {
            "voltage": [0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05, 0.0, -0.05, -0.1, -0.05, 0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4],
            "current": [1e-6, 2e-6, 5e-6, 8e-6, 12e-6, 15e-6, 18e-6, 20e-6, 22e-6, 23e-6, 24e-6, 20e-6, 18e-6, 15e-6, 12e-6, 8e-6, 5e-6, 2e-6, 1e-6, 1e-6, 1e-6]
        }
    ]
}

try:
    response = requests.post(url, json=multi_data, timeout=10)
    if response.status_code == 200:
        result = response.json()
        peaks = result.get('peaks', [])
        
        print(f"Total peaks: {len(peaks)}")
        print(f"Peaks type: {type(peaks)}")
        
        if peaks:
            print(f"First peak type: {type(peaks[0])}")
            print(f"First peak: {peaks[0]}")
            
            if len(peaks) > 1:
                print(f"Second peak: {peaks[1]}")
                
    else:
        print(f"Error: {response.status_code}")
        print(response.text[:500])

except Exception as e:
    print(f"Error: {e}")
