#!/usr/bin/env python3
"""
Test Enhanced V4 API Endpoint
"""

import requests
import json
import pandas as pd
import numpy as np

def test_enhanced_v4_api():
    """Test Enhanced V4 API endpoint directly"""
    print("🌐 Testing Enhanced V4 API Endpoint")
    print("=" * 50)
    
    # Load test data
    test_file = "Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv"
    
    try:
        # Read test data
        df = pd.read_csv(test_file, skiprows=1)
        voltage = df['V'].values
        current = df['uA'].values
        
        print(f"📊 Test data loaded:")
        print(f"   • Data points: {len(voltage)}")
        print(f"   • Voltage range: {voltage.min():.3f} to {voltage.max():.3f} V")
        print(f"   • Current range: {current.min():.3f} to {current.max():.3f} μA")
        
        # Prepare API request data
        api_data = {
            'voltage': voltage.tolist(),
            'current': current.tolist(),
            'filename': 'test_palmsens_0.5mM_100mVpS.csv'
        }
        
        print(f"\n📡 Testing Enhanced V4 API endpoint...")
        
        # Test Enhanced V4 analysis API
        # Test Enhanced V4 API endpoint
        url = "http://127.0.0.1:8080/peak_detection/api/enhanced_v4_analysis"
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(url, data=json.dumps(api_data), headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Enhanced V4 API test successful!")
            print(f"   • Success: {result['success']}")
            print(f"   • Method: {result['method']}")
            print(f"   • Total files: {result['total_files']}")
            print(f"   • Total peaks: {result['total_peaks']}")
            print(f"   • Export ready: {result['export_ready']}")
            
            # Show results details
            if result['results']:
                first_result = result['results'][0]
                print(f"\n🎯 Analysis Results:")
                print(f"   • Filename: {first_result['filename']}")
                print(f"   • Peak count: {first_result['peak_count']}")
                print(f"   • Success: {first_result['success']}")
                
                # Show peaks
                peaks = first_result['peaks']
                if peaks:
                    print(f"\n📍 Detected Peaks:")
                    for i, peak in enumerate(peaks):
                        print(f"   Peak {i+1}: {peak['type']} at {peak['voltage']:.3f}V, {peak['current']:.2f}μA")
                
                # Show PLS features
                pls_features = first_result['pls_features']
                if pls_features:
                    print(f"\n📊 PLS Features:")
                    print(f"   • Oxidation peaks: {len(pls_features['oxidation_peaks'])}")
                    print(f"   • Reduction peaks: {len(pls_features['reduction_peaks'])}")
                    
                    if pls_features['derived_features']:
                        derived = pls_features['derived_features']
                        print(f"   • Peak separation (V): {derived.get('peak_separation_voltage', 0):.3f}")
                        print(f"   • Current ratio: {derived.get('current_ratio', 0):.2f}")
                        print(f"   • Midpoint potential: {derived.get('midpoint_potential', 0):.3f}")
            
            return True
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_v4_regular_endpoint():
    """Test Enhanced V4 through regular peak detection endpoint"""
    print("\n🔬 Testing Enhanced V4 through regular endpoint")
    print("=" * 50)
    
    # Load test data
    test_file = "Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv"
    
    try:
        # Read test data
        df = pd.read_csv(test_file, skiprows=1)
        voltage = df['V'].values
        current = df['uA'].values
        
        # Prepare API request data
        api_data = {
            'voltage': voltage.tolist(),
            'current': current.tolist(),
            'filename': 'test_palmsens_0.5mM_100mVpS.csv'
        }
        
        print(f"📡 Testing regular peak detection with Enhanced V4...")
        
        # Test regular peak detection API with Enhanced V4
        url = "http://127.0.0.1:8080/peak_detection/get-peaks/enhanced_v4"
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(url, data=json.dumps(api_data), headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Regular endpoint test successful!")
            print(f"   • Success: {result['success']}")
            print(f"   • Method: {result.get('method', 'N/A')}")
            
            # Show peaks
            peaks = result.get('peaks', [])
            print(f"   • Peaks detected: {len(peaks)}")
            
            if peaks:
                print(f"\n📍 Detected Peaks:")
                for i, peak in enumerate(peaks):
                    print(f"   Peak {i+1}: {peak['type']} at {peak['voltage']:.3f}V, {peak['current']:.2f}μA")
            
            return True
        else:
            print(f"❌ Regular endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Regular endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test both API endpoints
    api_success = test_enhanced_v4_api()
    regular_success = test_enhanced_v4_regular_endpoint()
    
    if api_success and regular_success:
        print(f"\n🎉 All Enhanced V4 API tests PASSED!")
        print(f"✅ Production ready for integration!")
    else:
        print(f"\n💥 Some Enhanced V4 API tests FAILED!")
        print(f"❌ Needs debugging before production!")
