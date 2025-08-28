#!/usr/bin/env python3
"""
Quick test to verify peak detection is working after fixes
"""

import subprocess
import time
import json

def test_peak_detection_api():
    """Test peak detection via curl"""
    
    # Test data - simplified PalmSens-like data
    test_data = {
        "voltage": [-0.4, -0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, -0.1, -0.2, -0.3, -0.4],
        "current": [-10, -8, -5, -2, 0, 5, 15, 25, 30, 25, 15, 10, 5, 0, -5, -15, -25, -30, -25, -15, -10, -8, -6],
        "filename": "test_data.csv"
    }
    
    # Convert to JSON string
    json_data = json.dumps(test_data)
    
    print("🧪 Testing ML Peak Detection API...")
    
    try:
        # Use curl to test the API
        result = subprocess.run([
            'curl', '-s', '-X', 'POST',
            'http://127.0.0.1:8080/peak_detection/get-peaks/ml',
            '-H', 'Content-Type: application/json',
            '-d', json_data
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            try:
                response = json.loads(result.stdout)
                if response.get('success'):
                    peaks = response.get('peaks', [])
                    print(f"✅ API Test Success: Found {len(peaks)} peaks")
                    for i, peak in enumerate(peaks[:3]):
                        print(f"   Peak {i+1}: {peak.get('voltage', 'N/A'):.3f}V, {peak.get('current', 'N/A'):.1f}µA, type={peak.get('type', 'N/A')}")
                    return True
                else:
                    print(f"❌ API Error: {response.get('error', 'Unknown error')}")
                    return False
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {result.stdout[:200]}")
                return False
        else:
            print(f"❌ Curl failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ API request timed out")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Peak Detection Fix...")
    
    # Wait a moment for server to be ready
    time.sleep(1)
    
    success = test_peak_detection_api()
    
    if success:
        print("🎉 Peak detection is working! You can now test on the web interface.")
    else:
        print("⚠️ Peak detection still has issues. Check server logs.")