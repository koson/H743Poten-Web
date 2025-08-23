#!/usr/bin/env python3
"""
Test script to verify that backend returns baseline data for all methods
"""
import json
import requests
import os

def test_baseline_backend():
    # Load sample data
    sample_file = "sample_data/cv_sample.csv"
    if not os.path.exists(sample_file):
        print(f"❌ Sample file not found: {sample_file}")
        return
    
    # Read sample CSV file
    with open(sample_file, 'r') as f:
        lines = f.readlines()
    
    # Simple CSV parsing (assuming voltage, current columns)
    headers = lines[0].strip().split(',')
    print(f"CSV Headers: {headers}")
    
    voltage = []
    current = []
    
    for line in lines[1:]:
        if line.strip():
            values = line.strip().split(',')
            if len(values) >= 2:
                try:
                    v = float(values[1])  # voltage column
                    c = float(values[2])  # current column
                    voltage.append(v)
                    current.append(c)
                except ValueError:
                    continue
    
    print(f"Data points: {len(voltage)}")
    
    # Test all methods
    methods = ['prominence', 'ml', 'derivative']
    
    for method in methods:
        print(f"\n🧪 Testing method: {method}")
        
        # Test endpoint - use correct route
        url = f"http://127.0.0.1:8080/peak_detection/get-peaks/{method}"
        
        data = {
            'voltage': voltage,
            'current': current
        }
        
        try:
            response = requests.post(url, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    peaks = result.get('peaks', [])
                    print(f"  ✅ {method}: {len(peaks)} peaks detected")
                    
                    # Check baseline in top level response (for single trace)
                    baseline = result.get('baseline', {})
                    if baseline:
                        print(f"  📊 Baseline found in response!")
                        if isinstance(baseline, dict):
                            if 'forward' in baseline and 'reverse' in baseline:
                                try:
                                    forward_len = len(baseline['forward']['current'])
                                    reverse_len = len(baseline['reverse']['current'])
                                    print(f"      Forward: {forward_len} points, Reverse: {reverse_len} points")
                                except Exception as e:
                                    print(f"      Error accessing baseline data: {str(e)}")
                                    print(f"      Baseline structure: {baseline}")
                            else:
                                print(f"      Baseline keys: {list(baseline.keys())}")
                        else:
                            print(f"      Baseline type: {type(baseline)}")
                    else:
                        print(f"  ❌ No baseline data found for {method}")
                        print(f"  🔍 Response keys: {list(result.keys())}")
                else:
                    print(f"  ❌ {method}: API error: {result.get('error', 'Unknown error')}")
            else:
                print(f"  ❌ {method}: HTTP {response.status_code}")
        except Exception as e:
            print(f"  ❌ {method}: Exception: {str(e)}")

if __name__ == "__main__":
    test_baseline_backend()