#!/usr/bin/env python3
"""
Test Enhanced V4 Improved UI fixes
ทดสอบการแสดงผล OX/RED counts และปุ่ม action buttons
"""

import requests
import json
import time

def test_enhanced_v4_improved_ui():
    """Test Enhanced V4 Improved UI elements"""
    
    print("🧪 Testing Enhanced V4 Improved UI fixes...")
    print("=" * 50)
    
    # Multi-file test data (should detect peaks)
    multi_data = {
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
    
    url = "http://127.0.0.1:8080/get-peaks/enhanced_v4_improved"
    
    try:
        print("🌐 Testing Enhanced V4 Improved with multi-file data...")
        response = requests.post(url, json=multi_data, timeout=30)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            success = result.get('success', False)
            peaks = result.get('peaks', [])
            baseline = result.get('baseline', {})
            
            print(f"   ✅ Success: {success}")
            print(f"   📊 Total peaks: {len(peaks)}")
            
            if peaks:
                # Count peak types
                ox_count = len([p for p in peaks if p.get('type') == 'oxidation'])
                red_count = len([p for p in peaks if p.get('type') == 'reduction'])
                
                print(f"   🔴 Oxidation peaks: {ox_count}")
                print(f"   🔵 Reduction peaks: {red_count}")
                
                # Show sample peak
                sample_peak = peaks[0]
                print(f"   📋 Sample peak structure: {list(sample_peak.keys())}")
                print(f"   📋 Sample peak type: {sample_peak.get('type', 'unknown')}")
                print(f"   📋 Sample peak voltage: {sample_peak.get('voltage', 'N/A')}")
                print(f"   📋 Sample peak current: {sample_peak.get('current', 'N/A')}")
                
                # Check if this is flat structure
                if isinstance(peaks, list) and len(peaks) > 0 and isinstance(peaks[0], dict):
                    print("   ✅ FLAT STRUCTURE confirmed - ready for UI")
                else:
                    print("   ⚠️  NESTED STRUCTURE detected - UI may have issues")
            
            # Check baseline data
            if baseline:
                print(f"   📊 Baseline keys: {list(baseline.keys())}")
                
            print("\n🎯 Expected UI behavior:")
            print(f"   - Total peaks (P): {len(peaks)}")
            if peaks:
                ox_count = len([p for p in peaks if p.get('type') == 'oxidation'])
                red_count = len([p for p in peaks if p.get('type') == 'reduction'])
                print(f"   - Oxidation (OX): {ox_count}")
                print(f"   - Reduction (RED): {red_count}")
                print(f"   - Files (F): 2")
                print(f"   - View Analysis button: SHOULD BE VISIBLE")
                print(f"   - Export PLS button: SHOULD BE VISIBLE")
            else:
                print("   - OX/RED counts: 0")
                print("   - Action buttons: HIDDEN")
                
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            print(f"   📝 Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   💥 Error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 UI test completed!")
    print("\n💡 Next steps:")
    print("1. Refresh browser to clear cache")
    print("2. Test Enhanced V4+ method")
    print("3. Verify OX/RED counts display correctly")
    print("4. Check that View Analysis and Export buttons appear")

if __name__ == "__main__":
    test_enhanced_v4_improved_ui()
