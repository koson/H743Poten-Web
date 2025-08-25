#!/usr/bin/env python3
"""
Test web API peak detection directly
"""

import requests
import json
import numpy as np
import sys
import os

def load_palmsens_file(file_path):
    """Load and parse PalmSens CSV file"""
    try:
        # Read CSV file
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            raise ValueError('File too short')
        
        # Handle instrument file format (FileName: header)
        header_line_idx = 0
        data_start_idx = 1
        
        if lines[0].strip().startswith('FileName:'):
            header_line_idx = 1
            data_start_idx = 2
        
        # Parse headers
        headers = [h.strip().lower() for h in lines[header_line_idx].strip().split(',')]
        
        # Find voltage and current columns
        voltage_idx = -1
        current_idx = -1
        
        for i, header in enumerate(headers):
            if header in ['v', 'voltage'] or 'volt' in header or 'potential' in header:
                voltage_idx = i
            elif header in ['a', 'ua', 'ma', 'na', 'current'] or 'amp' in header or 'curr' in header:
                current_idx = i
        
        if voltage_idx == -1 or current_idx == -1:
            raise ValueError(f'Could not find voltage or current columns in headers: {headers}')
        
        # Determine current scaling - keep in µA for baseline detection
        current_unit = headers[current_idx]
        current_scale = 1.0
        
        # Check if this is STM32/Pipot file (uses 'A' header but values are actually in µA)
        is_stm32_file = (
            'pipot' in file_path.lower() or 
            'stm32' in file_path.lower() or
            (current_unit == 'a' and lines[0].strip().startswith('FileName:'))
        )
        
        if current_unit == 'ma':
            current_scale = 1e3  # milliAmps to microAmps
        elif current_unit == 'na':
            current_scale = 1e-3  # nanoAmps to microAmps
        elif current_unit == 'a' and is_stm32_file:
            current_scale = 1e6  # STM32 'A' values are actually µA, so multiply by 1e6 to convert from A to µA
        elif current_unit == 'a' and not is_stm32_file:
            current_scale = 1e6  # True Amperes to microAmps
        # For 'ua' or 'uA' - keep as is (no scaling)
        
        # Parse data
        voltage = []
        current = []
        
        for i in range(data_start_idx, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
                
            values = line.split(',')
            if len(values) > max(voltage_idx, current_idx):
                try:
                    v = float(values[voltage_idx])
                    c = float(values[current_idx]) * current_scale
                    voltage.append(v)
                    current.append(c)
                except ValueError:
                    continue
        
        if len(voltage) == 0 or len(current) == 0:
            raise ValueError('No valid data points found')
        
        return voltage, current
        
    except Exception as e:
        print(f"Error loading CSV file: {str(e)}")
        raise

def test_web_api():
    """Test peak detection through web API with focus on voltage window baseline detector"""
    
    # Load a test file
    test_file = "./Test_data/Palmsens/Palmsens_1.0mM/Palmsens_1.0mM_CV_100mVpS_E1_scan_05.csv"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    try:
        voltage, current = load_palmsens_file(test_file)
        print(f"✅ Loaded {len(voltage)} data points")
        print(f"📊 Voltage range: {min(voltage):.3f}V to {max(voltage):.3f}V")
        print(f"⚡ Current range: {min(current):.3f}µA to {max(current):.3f}µA")
        
        # Prepare API request data
        api_data = {
            'voltage': voltage,
            'current': current,
            'filename': 'test_palmsens.csv'
        }
        
        # Test different methods with emphasis on voltage window baseline
        methods = ['prominence', 'ml', 'derivative']
        base_url = 'http://127.0.0.1:8080'
        
        for method in methods:
            print(f"\n🔬 Testing method: {method}")
            
            try:
                response = requests.post(
                    f"{base_url}/peak_detection/get-peaks/{method}",
                    json=api_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        peaks = result.get('peaks', [])
                        print(f"✅ {method}: Found {len(peaks)} peaks")
                        
                        # Show peak details
                        for i, peak in enumerate(peaks[:3]):  # Show first 3 peaks
                            print(f"   Peak {i+1}: {peak.get('voltage', 'N/A'):.3f}V, {peak.get('current', 'N/A'):.3f}µA, type={peak.get('type', 'N/A')}")
                        
                        # Check baseline data (focus on voltage window detector)
                        baseline = result.get('baseline', {})
                        if baseline:
                            # Check method in metadata first, then fall back to direct method
                            metadata = baseline.get('metadata', {})
                            method_used = metadata.get('method_used') or baseline.get('method', 'N/A')
                            print(f"   Baseline: method={method_used}")
                            
                            # Check if voltage window detector was used
                            if 'voltage_window' in method_used.lower():
                                print(f"   ✅ Using new voltage window baseline detector!")
                                
                                # Check baseline segments
                                full_baseline = baseline.get('full', [])
                                forward_baseline = baseline.get('forward', [])
                                reverse_baseline = baseline.get('reverse', [])
                                
                                print(f"   📈 Full baseline: {len(full_baseline)} points")
                                print(f"   ➡️ Forward baseline: {len(forward_baseline)} points")
                                print(f"   ⬅️ Reverse baseline: {len(reverse_baseline)} points")
                                
                                if len(full_baseline) > 0:
                                    # Baseline is a list of current values, not voltage-current pairs
                                    print(f"   🎯 Full baseline current range: {min(full_baseline):.3f}µA to {max(full_baseline):.3f}µA")
                                
                                # Check debug info if available
                                debug_info = baseline.get('debug', {})
                                if debug_info:
                                    print(f"   🔍 Debug: baseline_range={debug_info.get('baseline_range', 'N/A')}")
                                    
                                # Check metadata for processing info
                                if metadata:
                                    print(f"   ⚙️ Quality: {metadata.get('quality', 'N/A'):.2f}")
                                    processing_time = metadata.get('processing_time', 0)
                                    if processing_time > 0:
                                        print(f"   ⏱️ Processing time: {processing_time:.3f}ms")
                            else:
                                print(f"   ⚠️ Expected voltage window detector, got: {method_used}")
                        else:
                            print("   ❌ No baseline data returned")
                    else:
                        print(f"❌ {method}: API returned error: {result.get('error', 'Unknown error')}")
                else:
                    print(f"❌ {method}: HTTP {response.status_code}: {response.text[:200]}")
                    
            except requests.exceptions.ConnectionError:
                print(f"❌ {method}: Cannot connect to server - is it running?")
                print("   💡 Start the server with: python3 auto_dev.py start")
            except Exception as e:
                print(f"❌ {method}: Error - {e}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing Web API Peak Detection")
    test_web_api()