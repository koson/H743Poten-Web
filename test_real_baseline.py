#!/usr/bin/env python3
"""
Test specific PalmSens file baseline detection
"""

import subprocess
import time
import json
import os

def load_palmsens_file_data(file_path):
    """Load real PalmSens file data"""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            return None, None
        
        # Handle instrument file format
        header_line_idx = 0
        data_start_idx = 1
        
        if lines[0].strip().startswith('FileName:'):
            header_line_idx = 1
            data_start_idx = 2
        
        # Parse headers
        headers = [h.strip().lower() for h in lines[header_line_idx].strip().split(',')]
        
        # Find voltage and current columns
        voltage_idx = current_idx = -1
        for i, header in enumerate(headers):
            if header in ['v', 'voltage'] or 'volt' in header:
                voltage_idx = i
            elif header in ['ua', 'current'] or 'amp' in header:
                current_idx = i
        
        if voltage_idx == -1 or current_idx == -1:
            return None, None
        
        # Parse data
        voltage, current = [], []
        for i in range(data_start_idx, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
            values = line.split(',')
            if len(values) > max(voltage_idx, current_idx):
                try:
                    v = float(values[voltage_idx])
                    c = float(values[current_idx])  # Keep as µA
                    voltage.append(v)
                    current.append(c)
                except ValueError:
                    continue
        
        return voltage, current
        
    except Exception as e:
        print(f"Error loading file: {e}")
        return None, None

def test_real_palmsens_baseline():
    """Test baseline detection with real PalmSens data"""
    
    # Test with actual PalmSens file
    test_file = "./Test_data/Palmsens/Palmsens_1.0mM/Palmsens_1.0mM_CV_200mVpS_E3_scan_08.csv"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"🧪 Testing baseline detection with real PalmSens file:")
    print(f"📁 File: {os.path.basename(test_file)}")
    
    voltage, current = load_palmsens_file_data(test_file)
    if voltage is None:
        print("❌ Failed to load file data")
        return
    
    print(f"📊 Loaded {len(voltage)} data points")
    print(f"📊 Voltage range: {min(voltage):.3f}V to {max(voltage):.3f}V")
    print(f"📊 Current range: {min(current):.3f}µA to {max(current):.3f}µA")
    
    # Prepare API request
    test_data = {
        "voltage": voltage,
        "current": current,
        "filename": os.path.basename(test_file)
    }
    
    json_data = json.dumps(test_data)
    
    try:
        # Test ML method
        result = subprocess.run([
            'curl', '-s', '-X', 'POST',
            'http://127.0.0.1:8080/peak_detection/get-peaks/ml',
            '-H', 'Content-Type: application/json',
            '-d', json_data
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            try:
                response = json.loads(result.stdout)
                if response.get('success'):
                    peaks = response.get('peaks', [])
                    baseline = response.get('baseline', {})
                    
                    print(f"✅ API Success: Found {len(peaks)} peaks")
                    
                    # Show peak details
                    for i, peak in enumerate(peaks):
                        print(f"   Peak {i+1}: {peak.get('voltage', 0):.3f}V, {peak.get('current', 0):.1f}µA, type={peak.get('type', 'unknown')}")
                    
                    # Show baseline details
                    if baseline:
                        print(f"📊 Baseline info:")
                        metadata = baseline.get('metadata', {})
                        debug = baseline.get('debug', {})
                        
                        print(f"   Method: {metadata.get('method_used', 'unknown')}")
                        print(f"   Quality: {metadata.get('quality', 0):.2f}")
                        print(f"   Error: {metadata.get('error', 'None')}")
                        
                        if debug:
                            print(f"   Range: {debug.get('baseline_range', 'unknown')}")
                            print(f"   Std: {debug.get('baseline_std', 0):.2e}")
                            print(f"   Forward: {debug.get('forward_range', 'unknown')}")
                            print(f"   Reverse: {debug.get('reverse_range', 'unknown')}")
                    else:
                        print("⚠️ No baseline data returned")
                        
                else:
                    print(f"❌ API Error: {response.get('error', 'Unknown error')}")
                    
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {result.stdout[:300]}")
        else:
            print(f"❌ Curl failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    print("🔬 Testing Real PalmSens Baseline Detection...")
    time.sleep(1)  # Wait for server
    test_real_palmsens_baseline()