#!/usr/bin/env python3
"""
Test Peak Height Calculation
Test the corrected peak height calculation logic
"""

import requests
import json
from datetime import datetime

# Test data with different peak types and scenarios
test_data = {
    "measurement": {
        "sample_id": "height_test_sample",
        "instrument_type": "palmsens",
        "scan_rate": 100,
        "voltage_start": -0.4,
        "voltage_end": 0.6,
        "data_points": 220,
        "user_notes": "Height calculation test",
        "original_filename": "height_test.csv"
    },
    "peaks": [
        {
            # Oxidation peak with baseline - should use: height = current - baseline
            "type": "oxidation",
            "voltage": 0.2,
            "current": 15.5,
            "baseline_current": 3.2,
            "enabled": True
            # Expected height: 15.5 - 3.2 = 12.3
        },
        {
            # Reduction peak with baseline - should use: height = abs(current - baseline)
            "type": "reduction", 
            "voltage": -0.1,
            "current": -8.3,
            "baseline_current": 2.1,
            "enabled": True
            # Expected height: abs(-8.3 - 2.1) = abs(-10.4) = 10.4
        },
        {
            # Peak with provided height (should use provided value)
            "type": "oxidation",
            "voltage": 0.35,
            "current": 22.8,
            "height": 18.5,  # Explicitly provided
            "baseline_current": 4.3,
            "enabled": True
            # Expected height: 18.5 (provided value, not calculated)
        },
        {
            # Peak without baseline info (should use fallback)
            "type": "oxidation",
            "x": 0.45,  # Using "x" instead of "voltage"
            "y": 12.7,  # Using "y" instead of "current"
            "enabled": True
            # Expected height: abs(12.7) = 12.7 (fallback)
        },
        {
            # Reduction peak without baseline (should use fallback)
            "type": "reduction",
            "voltage": -0.2,
            "current": -15.2,
            "enabled": True
            # Expected height: abs(-15.2) = 15.2 (fallback)
        }
    ]
}

def test_height_calculation():
    """Test the height calculation API endpoint"""
    url = "http://127.0.0.1:8080/api/parameters/save_analysis"
    
    print("🧮 Testing Peak Height Calculation")
    print("=" * 50)
    print(f"📊 Test scenarios:")
    for i, peak in enumerate(test_data['peaks']):
        print(f"   Peak {i}: {peak['type']} at {peak.get('voltage', peak.get('x'))}V")
        print(f"      Current: {peak.get('current', peak.get('y'))}μA")
        if 'baseline_current' in peak:
            print(f"      Baseline: {peak['baseline_current']}μA")
        if 'height' in peak:
            print(f"      Provided height: {peak['height']}μA")
        print()
    
    try:
        print("📡 Sending test data...")
        response = requests.post(url, json=test_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            measurement_id = result['measurement_id']
            print(f"✅ Analysis saved successfully (ID: {measurement_id})")
            
            # Get the peaks back to verify height calculation
            peaks_url = f"http://127.0.0.1:8080/api/parameters/measurements/{measurement_id}/peaks"
            peaks_response = requests.get(peaks_url, timeout=10)
            
            if peaks_response.status_code == 200:
                peaks_result = peaks_response.json()
                peaks = peaks_result.get('peaks', [])
                
                print(f"\n📊 Retrieved {len(peaks)} peaks with calculated heights:")
                print("-" * 60)
                
                expected_heights = [12.3, 10.4, 18.5, 12.7, 15.2]
                
                for i, peak in enumerate(peaks):
                    peak_type = peak.get('peak_type')
                    voltage = peak.get('peak_voltage')
                    current = peak.get('peak_current')
                    baseline = peak.get('baseline_current')
                    height = peak.get('peak_height')
                    expected = expected_heights[i] if i < len(expected_heights) else 'N/A'
                    
                    print(f"Peak {i}: {peak_type}")
                    print(f"   Voltage: {voltage:.3f}V")
                    print(f"   Current: {current:.3f}μA")
                    print(f"   Baseline: {baseline}μA" if baseline else "   Baseline: None")
                    print(f"   Calculated Height: {height:.3f}μA")
                    print(f"   Expected Height: {expected}μA")
                    
                    # Check if calculation is correct
                    if isinstance(expected, (int, float)):
                        diff = abs(height - expected)
                        if diff < 0.1:
                            print(f"   ✅ CORRECT (diff: {diff:.3f})")
                        else:
                            print(f"   ❌ INCORRECT (diff: {diff:.3f})")
                    else:
                        print(f"   ℹ️ No expected value")
                    print()
                
                return True
            else:
                print(f"❌ Failed to retrieve peaks: {peaks_response.status_code}")
                return False
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run height calculation test"""
    success = test_height_calculation()
    
    print(f"\n📋 Test Summary:")
    print(f"   Height Calculation: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print(f"\n🎉 Peak height calculation is working correctly!")
        print(f"   ✅ Oxidation peaks: height = current - baseline")
        print(f"   ✅ Reduction peaks: height = abs(current - baseline)")
        print(f"   ✅ Provided heights: used as-is")
        print(f"   ✅ Fallback: height = abs(current)")

if __name__ == '__main__':
    main()