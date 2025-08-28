#!/usr/bin/env python3
"""
Test Enhanced V4 Improved API response structure with production data
"""

import requests
import json
import sys

def test_production_response():
    """Test API response structure with production data that has peaks"""
    
    url = "http://127.0.0.1:8080/get-peaks/enhanced_v4_improved"
    
    # Create sample data that should detect peaks (similar to production structure)
    test_data = {
        "voltage": [
            [-0.4, -0.35, -0.3, -0.25, -0.2, -0.15, -0.1, -0.05, 0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        ],
        "current": [
            [-1.2, -0.8, -0.5, -0.2, 2.5, 8.1, 15.2, 12.5, 8.7, 5.2, 3.1, 2.8, 3.5, 5.1, 8.9, 15.7, 22.3, 18.9, 12.1, 7.8, 4.2, 2.1, 1.1]
        ]
    }
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Keys: {list(data.keys())}")
            print(f"Success: {data.get('success')}")
            
            peaks = data.get('peaks', [])
            print(f"Peaks type: {type(peaks)}")
            print(f"Total peaks: {len(peaks)}")
            
            if len(peaks) > 0:
                print(f"First peak type: {type(peaks[0])}")
                print(f"First peak keys: {list(peaks[0].keys()) if isinstance(peaks[0], dict) else 'Not a dict'}")
                
                # Count peak types (check both 'type' and 'peak_type' keys)
                ox_count = sum(1 for p in peaks if isinstance(p, dict) and (p.get('type') == 'oxidation' or p.get('peak_type') == 'oxidation'))
                red_count = sum(1 for p in peaks if isinstance(p, dict) and (p.get('type') == 'reduction' or p.get('peak_type') == 'reduction'))
                
                print(f"Oxidation peaks: {ox_count}")
                print(f"Reduction peaks: {red_count}")
                
                # Debug peak keys and types
                for i, p in enumerate(peaks[:2]):  # Show first 2 peaks
                    print(f"Peak {i+1}: type='{p.get('type')}', peak_type='{p.get('peak_type')}', voltage={p.get('voltage'):.3f}V")
                
                return True
            else:
                print("⚠️  No peaks detected")
                return False
        else:
            print(f"❌ Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Enhanced V4 Improved API Response Structure...")
    success = test_production_response()
    sys.exit(0 if success else 1)
