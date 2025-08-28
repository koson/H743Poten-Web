#!/usr/bin/env python3
"""
Test Enhanced V4 Regular Endpoint Only
"""

import requests
import json
import pandas as pd

def test_enhanced_v4_regular_only():
    """Test Enhanced V4 through regular peak detection endpoint only"""
    print("🔬 Testing Enhanced V4 Regular Endpoint")
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
        
        print(f"\n📡 Testing regular peak detection with Enhanced V4...")
        
        # Test regular peak detection API with Enhanced V4
        url = "http://127.0.0.1:8080/peak_detection/get-peaks/enhanced_v4"
        headers = {'Content-Type': 'application/json'}
        
        print(f"🔗 Request URL: {url}")
        print(f"📦 Data size: {len(json.dumps(api_data))} characters")
        
        response = requests.post(url, data=json.dumps(api_data), headers=headers, timeout=30)
        
        print(f"📈 Response status: {response.status_code}")
        print(f"📄 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Regular endpoint test successful!")
            print(f"   • Success: {result.get('success', False)}")
            print(f"   • Method: {result.get('method', 'N/A')}")
            
            # Show error if present
            if 'error' in result:
                print(f"   ❌ Error: {result['error']}")
            
            # Show all response keys
            print(f"   • Response keys: {list(result.keys())}")
            
            # Show peaks
            peaks = result.get('peaks', [])
            print(f"   • Peaks detected: {len(peaks)}")
            
            if peaks:
                print(f"\n📍 Detected Peaks:")
                for i, peak in enumerate(peaks):
                    print(f"   Peak {i+1}: {peak.get('type', 'unknown')} at {peak.get('voltage', 0):.3f}V, {peak.get('current', 0):.2f}μA")
                    print(f"      Confidence: {peak.get('confidence', 0):.1f}%")
                    print(f"      Height: {peak.get('height', 0):.2f}μA")
            
            # Show baseline info if available
            if 'baseline' in result:
                baseline = result['baseline']
                print(f"\n📊 Baseline Info:")
                print(f"   • Method: {baseline.get('metadata', {}).get('method_used', 'N/A')}")
                print(f"   • Quality: {baseline.get('metadata', {}).get('quality', 0):.2f}")
            
            # Show parameters
            if 'params' in result:
                params = result['params']
                print(f"\n⚙️ Parameters:")
                for key, value in params.items():
                    print(f"   • {key}: {value}")
            
            return True
        else:
            print(f"❌ Regular endpoint failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error data: {error_data}")
            except:
                print(f"   Response text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Regular endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_v4_regular_only()
    
    if success:
        print(f"\n🎉 Enhanced V4 regular endpoint test PASSED!")
    else:
        print(f"\n💥 Enhanced V4 regular endpoint test FAILED!")
