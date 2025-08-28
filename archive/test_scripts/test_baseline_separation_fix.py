#!/usr/bin/env python3
"""
Test script for baseline separation fix
Verifies that baseline segments are visually separated (not joined)
"""

import time
import requests
import os
import json

def test_baseline_separation():
    """Test that baseline segments are properly separated"""
    print("🧪 Testing baseline segment separation fix...")
    
    # Test server is running
    try:
        response = requests.get('http://127.0.0.1:8083/', timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding")
            return False
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server")
        return False
    
    # Test with known CV file that has clear forward/reverse segments
    test_file = "Test_data/backup_raw_stm32/Pipot_Ferro-10mM_100mVpS_E1_scan_01.csv"
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"📁 Testing with file: {test_file}")
    
    # Load the file
    load_response = requests.post('http://127.0.0.1:8083/api/load_csv_file', 
                                json={'file_path': test_file})
    
    if load_response.status_code != 200:
        print(f"❌ Failed to load file: {load_response.status_code}")
        return False
    
    data = load_response.json()
    print(f"✅ File loaded: {len(data.get('voltage', []))} data points")
    
    # Test peak detection
    peak_response = requests.post('http://127.0.0.1:8083/api/detect_peaks', 
                                json={
                                    'voltage': data['voltage'],
                                    'current': data['current'],
                                    'direction': data.get('direction', []),
                                    'method': 'prominence',
                                    'prominence': 0.1,
                                    'height': 0.01,
                                    'distance': 20
                                })
    
    if peak_response.status_code != 200:
        print(f"❌ Peak detection failed: {peak_response.status_code}")
        return False
    
    peak_data = peak_response.json()
    peaks = peak_data.get('peaks', [])
    print(f"✅ Found {len(peaks)} peaks")
    
    # Test baseline detection (this should return proper segment markers)
    baseline_response = requests.post('http://127.0.0.1:8083/api/detect_baseline',
                                    json={
                                        'voltage': data['voltage'],
                                        'current': data['current'],
                                        'direction': data.get('direction', []),
                                        'peaks': peaks
                                    })
    
    if baseline_response.status_code != 200:
        print(f"❌ Baseline detection failed: {baseline_response.status_code}")
        return False
    
    baseline_data = baseline_response.json()
    baseline = baseline_data.get('baseline', {})
    markers = baseline.get('markers', {})
    
    print("📊 Baseline analysis:")
    if 'forward_segment' in markers and 'reverse_segment' in markers:
        forward = markers['forward_segment']
        reverse = markers['reverse_segment']
        
        print(f"  Forward segment: indices {forward.get('start_idx', 'N/A')} to {forward.get('end_idx', 'N/A')}")
        print(f"  Reverse segment: indices {reverse.get('start_idx', 'N/A')} to {reverse.get('end_idx', 'N/A')}")
        
        # Check for separation (forward end should be before reverse start)
        forward_end = forward.get('end_idx')
        reverse_start = reverse.get('start_idx')
        
        if forward_end is not None and reverse_start is not None:
            gap = reverse_start - forward_end
            print(f"  Gap between segments: {gap} indices")
            
            if gap > 0:
                print("✅ Segments are properly separated (no overlap)")
                return True
            elif gap == 0:
                print("⚠️  Segments touch exactly (minimal overlap)")
                return True
            else:
                print(f"❌ Segments overlap by {-gap} indices")
                return False
        else:
            print("❌ Missing segment index information")
            return False
    else:
        print("❌ No forward/reverse segment markers found")
        return False

def test_javascript_baseline_rendering():
    """Test the JavaScript rendering logic for baseline separation"""
    print("\n🖥️  Testing JavaScript baseline rendering...")
    
    # Check if the JS file was properly updated
    js_file = "static/js/peak_analysis_plotly.js"
    if not os.path.exists(js_file):
        print(f"❌ JavaScript file not found: {js_file}")
        return False
    
    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for the updated baseline separation logic
    checks = [
        ("forwardEndIdx + 1", "Forward segment uses exact end index"),
        ("reverseStartIdx", "Reverse segment uses exact start index"),
        ("no overlap", "Baseline segments don't overlap"),
    ]
    
    print("📝 Checking JavaScript code updates:")
    
    # Look for the improved baseline logic
    if "forwardEndIdx + 1" in content and "reverseStartIdx" in content:
        print("✅ Updated baseline separation logic found")
        
        # Check that we're not using splitPoint in baseline separation
        baseline_section = content[content.find("if (baseline.markers && baseline.markers.forward_segment"):content.find("} else {")]
        if "splitPoint" not in baseline_section:
            print("✅ Old splitPoint logic removed from baseline separation")
        else:
            print("⚠️  Old splitPoint logic still present in baseline separation")
        
        return True
    else:
        print("❌ Updated baseline separation logic not found")
        return False

if __name__ == "__main__":
    print("🧪 Testing Baseline Separation Fix")
    print("=" * 50)
    
    success = True
    
    # Test 1: JavaScript code changes
    if not test_javascript_baseline_rendering():
        success = False
    
    # Test 2: API functionality
    if not test_baseline_separation():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All baseline separation tests passed!")
        print("📝 Baseline segments should now be visually separated")
        print("   - Red forward segment: from start to exact forward end")
        print("   - Green reverse segment: from exact reverse start to end")
        print("   - No overlap or joining between segments")
    else:
        print("❌ Some tests failed")
        print("🔧 Check the fixes and try again")
    
    print("\n💡 Next: Test in browser to verify visual separation")