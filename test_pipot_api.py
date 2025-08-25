#!/usr/bin/env python3
"""
Test the full API with PiPot data to ensure baseline detection works in web interface
"""

import requests
import json

# Test the web API with PiPot data
def test_pipot_api():
    url = "http://localhost:5000/api/peak-detection"
    
    # PiPot test data
    test_data = {
        "file_path": "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_20mVpS_E1_scan_06.csv",
        "algorithm": "voltage_windows_v4"
    }
    
    try:
        print(f"🔍 Testing API with PiPot data...")
        print(f"📂 File: {test_data['file_path']}")
        
        response = requests.post(url, json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('status') == 'success':
                print("✅ API call successful!")
                
                # Check baseline data
                baseline_data = result.get('baseline', {})
                forward_baseline = baseline_data.get('forward_baseline', [])
                reverse_baseline = baseline_data.get('reverse_baseline', [])
                
                print(f"📈 Forward baseline: {len(forward_baseline)} points")
                if forward_baseline:
                    min_val = min(forward_baseline)
                    max_val = max(forward_baseline)
                    mean_val = sum(forward_baseline) / len(forward_baseline)
                    variation = max_val - min_val
                    print(f"   Range: {min_val:.6f} to {max_val:.6f} µA")
                    print(f"   Mean: {mean_val:.6f} µA")
                    print(f"   Variation: {variation:.6f} µA")
                
                print(f"📉 Reverse baseline: {len(reverse_baseline)} points")
                if reverse_baseline:
                    min_val = min(reverse_baseline)
                    max_val = max(reverse_baseline)
                    mean_val = sum(reverse_baseline) / len(reverse_baseline)
                    variation = max_val - min_val
                    print(f"   Range: {min_val:.6f} to {max_val:.6f} µA")
                    print(f"   Mean: {mean_val:.6f} µA")
                    print(f"   Variation: {variation:.6f} µA")
                
                # Check if baselines are meaningful
                forward_variation = max(forward_baseline) - min(forward_baseline) if forward_baseline else 0
                reverse_variation = max(reverse_baseline) - min(reverse_baseline) if reverse_baseline else 0
                
                if forward_variation > 0.001 or reverse_variation > 0.001:
                    print("✅ Baselines show meaningful variation!")
                    print("🎉 PiPot baseline detection is working correctly!")
                else:
                    print("⚠️ Baselines are still very flat")
                
                # Show metadata
                metadata = result.get('metadata', {})
                print(f"\n� Detection metadata:")
                print(f"   Forward segments: {metadata.get('forward_segments', 'N/A')}")
                print(f"   Reverse segments: {metadata.get('reverse_segments', 'N/A')}")
                print(f"   Forward R²: {metadata.get('forward_r2', 'N/A')}")
                print(f"   Reverse R²: {metadata.get('reverse_r2', 'N/A')}")
                
            else:
                print(f"❌ API returned error: {result.get('message', 'Unknown error')}")
                
        else:
            print(f"❌ HTTP error {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the development server is running.")
        print("💡 Run: python3 auto_dev.py start")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_pipot_api()