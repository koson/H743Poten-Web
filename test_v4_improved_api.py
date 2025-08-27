#!/usr/bin/env python3
"""
Test Enhanced V4 Improved API endpoints
Verify web integration and compare with Enhanced V4
"""

import requests
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime

def load_test_file(filepath):
    """Load a single test file for API testing"""
    try:
        # Skip first line for Palmsens files
        df = pd.read_csv(filepath, skiprows=1)
        
        # Use first two columns
        voltage = df.iloc[:, 0].values
        current = df.iloc[:, 1].values
        
        # Remove NaN values
        valid_mask = ~(np.isnan(voltage) | np.isnan(current))
        voltage = voltage[valid_mask]
        current = current[valid_mask]
        
        return voltage.tolist(), current.tolist(), os.path.basename(filepath)
        
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return None, None, None

def test_enhanced_v4_improved_api():
    """Test Enhanced V4 Improved API endpoint"""
    
    print("🚀 Testing Enhanced V4 Improved API Integration")
    print("=" * 60)
    
    # Base URL (adjust if needed)
    base_url = "http://localhost:5000"
    
    # Test files
    test_files = [
        "Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv",
        "Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_100mVpS_E1_scan_02.csv",
        "Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_200mVpS_E5_scan_05.csv"
    ]
    
    # Test 1: Single file endpoint
    print("\\n📝 Test 1: Single file Enhanced V4 Improved API")
    
    for filepath in test_files[:1]:  # Test just first file
        voltage, current, filename = load_test_file(filepath)
        
        if voltage is None:
            continue
            
        print(f"\\n🔍 Testing {filename}")
        print(f"   Data points: {len(voltage)}")
        
        # Prepare data
        data = {
            'voltage': voltage,
            'current': current,
            'filename': filename
        }
        
        try:
            # Test Enhanced V4 Improved API
            response = requests.post(
                f"{base_url}/api/enhanced_v4_improved_analysis",
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result['success']:
                    print(f"   ✅ Enhanced V4 Improved API: {result['total_peaks']} peaks")
                    
                    # Show peak breakdown
                    breakdown = result.get('peak_breakdown', {})
                    ox_count = breakdown.get('oxidation', 0)
                    red_count = breakdown.get('reduction', 0)
                    print(f"      - Oxidation: {ox_count}")
                    print(f"      - Reduction: {red_count}")
                    
                    # Show improvements applied
                    if 'improvements_applied' in result:
                        print(f"      - Improvements: {len(result['improvements_applied'])} applied")
                    
                else:
                    print(f"   ❌ Enhanced V4 Improved failed: {result.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP Error {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Connection error: {e}")
    
    # Test 2: Multi-file endpoint
    print("\\n📝 Test 2: Multi-file Enhanced V4 Improved API")
    
    data_files = []
    for filepath in test_files:
        voltage, current, filename = load_test_file(filepath)
        
        if voltage is not None:
            data_files.append({
                'voltage': voltage,
                'current': current,
                'filename': filename
            })
    
    if data_files:
        print(f"\\n🔍 Testing {len(data_files)} files together")
        
        data = {'dataFiles': data_files}
        
        try:
            response = requests.post(
                f"{base_url}/api/enhanced_v4_improved_analysis",
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result['success']:
                    print(f"   ✅ Multi-file Enhanced V4 Improved: {result['total_files']} files processed")
                    print(f"      - Total peaks: {result['total_peaks']}")
                    
                    breakdown = result.get('peak_breakdown', {})
                    ox_count = breakdown.get('oxidation', 0)
                    red_count = breakdown.get('reduction', 0)
                    print(f"      - Oxidation: {ox_count}")
                    print(f"      - Reduction: {red_count}")
                    
                    # Show per-file results
                    for file_result in result['results']:
                        filename = file_result['filename']
                        peak_count = file_result['peak_count']
                        file_ox = len([p for p in file_result['peaks'] if p['type'] == 'oxidation'])
                        file_red = len([p for p in file_result['peaks'] if p['type'] == 'reduction'])
                        print(f"      - {filename}: {file_ox} ox + {file_red} red = {peak_count} total")
                    
                    # Check PLS export readiness
                    if result.get('export_ready'):
                        print(f"      - PLS export: ✅ Ready with {len(result.get('pls_ready_data', []))} feature sets")
                    
                else:
                    print(f"   ❌ Multi-file Enhanced V4 Improved failed: {result.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP Error {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Connection error: {e}")
    
    # Test 3: Compare Enhanced V4 vs V4 Improved endpoints
    print("\\n📝 Test 3: API Comparison - Enhanced V4 vs V4 Improved")
    
    test_file = test_files[0]
    voltage, current, filename = load_test_file(test_file)
    
    if voltage is not None:
        print(f"\\n🔍 Comparing APIs with {filename}")
        
        data = {
            'voltage': voltage,
            'current': current,
            'filename': filename
        }
        
        results = {}
        
        # Test Enhanced V4 (original)
        try:
            response = requests.post(
                f"{base_url}/api/enhanced_v4_analysis",
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    results['Enhanced_V4'] = result
                    print(f"   📊 Enhanced V4 (original): {result['total_peaks']} peaks")
                else:
                    print(f"   ❌ Enhanced V4 failed: {result.get('error')}")
            else:
                print(f"   ❌ Enhanced V4 HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Enhanced V4 connection error: {e}")
        
        # Test Enhanced V4 Improved
        try:
            response = requests.post(
                f"{base_url}/api/enhanced_v4_improved_analysis",
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    results['Enhanced_V4_Improved'] = result
                    print(f"   📊 Enhanced V4 Improved: {result['total_peaks']} peaks")
                else:
                    print(f"   ❌ Enhanced V4 Improved failed: {result.get('error')}")
            else:
                print(f"   ❌ Enhanced V4 Improved HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Enhanced V4 Improved connection error: {e}")
        
        # Compare results
        if len(results) == 2:
            print("\\n   📈 Comparison Summary:")
            
            v4_peaks = results['Enhanced_V4']['total_peaks']
            v4_improved_peaks = results['Enhanced_V4_Improved']['total_peaks']
            
            v4_breakdown = results['Enhanced_V4'].get('peak_breakdown', {})
            v4_improved_breakdown = results['Enhanced_V4_Improved'].get('peak_breakdown', {})
            
            print(f"      Enhanced V4:          {v4_peaks} total ({v4_breakdown.get('oxidation', 0)} ox + {v4_breakdown.get('reduction', 0)} red)")
            print(f"      Enhanced V4 Improved: {v4_improved_peaks} total ({v4_improved_breakdown.get('oxidation', 0)} ox + {v4_improved_breakdown.get('reduction', 0)} red)")
            
            if v4_improved_peaks > v4_peaks:
                improvement = v4_improved_peaks - v4_peaks
                print(f"      🎯 Improvement: +{improvement} more peaks detected")
            
            # Check reduction peak improvement
            v4_red = v4_breakdown.get('reduction', 0)
            v4_improved_red = v4_improved_breakdown.get('reduction', 0)
            
            if v4_improved_red > v4_red:
                red_improvement = v4_improved_red - v4_red
                print(f"      ⚡ Reduction peaks: +{red_improvement} more detected")
    
    # Test 4: Regular peak detection endpoint with Enhanced V4 Improved method
    print("\\n📝 Test 4: Regular /get-peaks/ endpoint with enhanced_v4_improved")
    
    if voltage is not None:
        data = {
            'voltage': voltage,
            'current': current
        }
        
        try:
            response = requests.post(
                f"{base_url}/get-peaks/enhanced_v4_improved",
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if 'peaks' in result:
                    peaks = result['peaks']
                    print(f"   ✅ Regular endpoint: {len(peaks)} peaks")
                    
                    # Count by type
                    ox_count = len([p for p in peaks if p.get('type') == 'oxidation'])
                    red_count = len([p for p in peaks if p.get('type') == 'reduction'])
                    print(f"      - Oxidation: {ox_count}")
                    print(f"      - Reduction: {red_count}")
                    
                    # Check method in response
                    method = result.get('method', 'unknown')
                    print(f"      - Method: {method}")
                    
                else:
                    print(f"   ❌ Regular endpoint failed: {result}")
            else:
                print(f"   ❌ Regular endpoint HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Regular endpoint connection error: {e}")
    
    print("\\n" + "=" * 60)
    print("🎯 API Testing Complete!")
    print("\\nNext steps:")
    print("1. Verify web interface integration")
    print("2. Test with production dataset")
    print("3. Export PLS data for analysis")

if __name__ == "__main__":
    test_enhanced_v4_improved_api()
