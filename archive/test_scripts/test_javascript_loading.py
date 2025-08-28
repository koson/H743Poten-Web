#!/usr/bin/env python3
"""
Test JavaScript loading and basic functionality
"""

import requests
import sys

def test_javascript_loading():
    """Test if JavaScript loads without errors"""
    
    try:
        # Test main page loads
        response = requests.get("http://127.0.0.1:8080/peak_detection", timeout=10)
        print(f"✅ Peak detection page status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Page failed to load: {response.status_code}")
            return False
            
        # Check if JavaScript is referenced
        content = response.text
        if "peak_detection.js?v=4004" in content:
            print("✅ JavaScript file reference found with correct version")
        else:
            print("❌ JavaScript file reference not found or wrong version")
            return False
            
        # Test JavaScript file loads
        js_response = requests.get("http://127.0.0.1:8080/static/js/peak_detection.js?v=4004", timeout=10)
        print(f"✅ JavaScript file status: {js_response.status_code}")
        
        if js_response.status_code != 200:
            print(f"❌ JavaScript file failed to load: {js_response.status_code}")
            return False
            
        # Check if PeakDetection object is defined
        js_content = js_response.text
        if "const PeakDetection = {" in js_content:
            print("✅ PeakDetection object found")
        else:
            print("❌ PeakDetection object not found")
            return False
            
        # Check if global exposure is fixed
        if "window.detectionManager = PeakDetection;" in js_content:
            print("✅ Global detectionManager exposure fixed")
        else:
            print("❌ Global detectionManager exposure not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing JavaScript Loading and Global Objects...")
    success = test_javascript_loading()
    sys.exit(0 if success else 1)
