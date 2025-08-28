#!/usr/bin/env python3
"""
Test Parameter Saving API with Mock Data
Simulate the data that would come from the frontend
"""

import requests
import json
from datetime import datetime

# Test data that simulates what comes from the frontend
test_data = {
    "measurement": {
        "sample_id": "test_sample_debug",
        "instrument_type": "palmsens",
        "scan_rate": 100,
        "voltage_start": -0.4,
        "voltage_end": 0.6,
        "data_points": 220,
        "user_notes": "Debug test from API",
        "original_filename": "debug_test.csv"
    },
    "peaks": [
        {
            "type": "oxidation",
            "voltage": 0.2,
            "current": 15.5,
            "enabled": True,
            "baseline_current": 3.2
            # Note: no "height" field to test our fix
        },
        {
            "type": "reduction", 
            "voltage": -0.1,
            "current": -8.3,
            "height": 12.1,  # This one has height
            "enabled": True,
            "baseline_current": 2.1
        },
        {
            "type": "oxidation",
            "x": 0.35,  # Using "x" instead of "voltage"
            "y": 22.8,  # Using "y" instead of "current"
            "enabled": True
            # No height, no baseline_current
        }
    ]
}

def test_save_analysis():
    """Test the save_analysis API endpoint"""
    url = "http://127.0.0.1:8080/api/parameters/save_analysis"
    
    print("🧪 Testing parameter saving API...")
    print(f"📡 URL: {url}")
    print(f"📊 Test data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(url, json=test_data, timeout=10)
        
        print(f"\n📋 Response:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            print(f"   JSON Response: {json.dumps(result, indent=2)}")
        else:
            print(f"   Text Response: {response.text[:500]}")
        
        if response.status_code == 200:
            print("✅ API call successful!")
            return True
        else:
            print(f"❌ API call failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_get_measurements():
    """Test getting measurements back"""
    url = "http://127.0.0.1:8080/api/parameters/measurements"
    
    print(f"\n🔍 Testing measurements retrieval...")
    print(f"📡 URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            measurements = response.json()
            print(f"✅ Found {len(measurements)} measurements")
            
            # Look for our test measurement
            for m in measurements:
                if m.get('sample_id') == 'test_sample_debug':
                    print(f"   📝 Found our test measurement: ID {m['id']}")
                    return m['id']
                    
        return None
        
    except Exception as e:
        print(f"❌ Error getting measurements: {e}")
        return None

def test_get_peaks(measurement_id):
    """Test getting peak parameters"""
    url = f"http://127.0.0.1:8080/api/parameters/measurements/{measurement_id}/peaks"
    
    print(f"\n🔬 Testing peak retrieval for measurement {measurement_id}...")
    print(f"📡 URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            peaks = result.get('peaks', [])
            print(f"✅ Found {len(peaks)} peaks")
            
            for i, peak in enumerate(peaks):
                print(f"   Peak {i}: {peak.get('peak_type')} at {peak.get('peak_voltage')}V, height={peak.get('peak_height')}")
                
            return True
        else:
            print(f"❌ Failed to get peaks: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting peaks: {e}")
        return False

def main():
    """Run comprehensive API test"""
    print("🚀 PARAMETER SAVING API TEST")
    print("=" * 50)
    
    # Test saving
    save_success = test_save_analysis()
    
    if save_success:
        # Test retrieval
        measurement_id = test_get_measurements()
        
        if measurement_id:
            test_get_peaks(measurement_id)
    
    print(f"\n📊 Test Summary:")
    print(f"   Save API: {'✅ PASS' if save_success else '❌ FAIL'}")
    
if __name__ == '__main__':
    main()