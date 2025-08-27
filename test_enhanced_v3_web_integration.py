#!/usr/bin/env python3
"""
ทดสอบ Enhanced V3 integration ในระบบเว็บ
"""

import requests
import json
import numpy as np
import pandas as pd

def test_enhanced_v3_api():
    """ทดสอบ Enhanced V3 ผ่าน web API"""
    
    # โหลดข้อมูลทดสอบ
    test_file = "Test_data/Stm32/Pipot_Ferro_1_0mM_20mVpS_E4_scan_05.csv"
    
    print(f"🧪 Testing Enhanced V3 API Integration")
    print(f"📂 Loading test file: {test_file}")
    
    try:
        # โหลดข้อมูล
        df = pd.read_csv(test_file, skiprows=1)
        voltage = df['V'].values.tolist()
        current = df['uA'].values.tolist()
        
        print(f"📊 Data loaded: {len(voltage)} points")
        print(f"🔌 Voltage range: {min(voltage):.3f} to {max(voltage):.3f}V")
        print(f"⚡ Current range: {min(current):.3f} to {max(current):.3f}µA")
        
        # ทดสอบ Enhanced V3 method
        api_url = "http://localhost:8081/peak_detection/get-peaks/enhanced_v3"
        
        payload = {
            "voltage": voltage,
            "current": current,
            "filename": test_file
        }
        
        print(f"\n🚀 Testing Enhanced V3 method...")
        print(f"🌐 API endpoint: {api_url}")
        
        response = requests.post(api_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success', False):
                peaks = result.get('peaks', [])
                method = result.get('method', 'unknown')
                enhanced_results = result.get('enhanced_results', {})
                baseline = result.get('baseline', {})
                
                print(f"✅ Enhanced V3 API Test SUCCESSFUL!")
                print(f"📈 Method: {method}")
                print(f"🎯 Peaks found: {len(peaks)}")
                
                # แสดงรายละเอียด peaks
                ox_peaks = [p for p in peaks if p['type'] == 'oxidation']
                red_peaks = [p for p in peaks if p['type'] == 'reduction']
                
                print(f"   - Oxidation peaks: {len(ox_peaks)}")
                print(f"   - Reduction peaks: {len(red_peaks)}")
                
                # แสดง peak details
                for i, peak in enumerate(peaks):
                    print(f"   Peak {i+1}: {peak['type'][:3].upper()} at {peak['voltage']:.3f}V, {peak['current']:.1f}µA, conf={peak['confidence']:.0f}%")
                
                # แสดงข้อมูล Enhanced results
                if enhanced_results:
                    print(f"\n🔧 Enhanced V3 Features:")
                    scan_sections = enhanced_results.get('scan_sections', {})
                    if scan_sections:
                        print(f"   - Turning point: {scan_sections.get('turning_point', 'N/A')}")
                        print(f"   - Forward points: {scan_sections.get('forward', [0, 0])[1]}")
                        print(f"   - Reverse points: {scan_sections.get('reverse', [0, 0])[1] - scan_sections.get('reverse', [0, 0])[0]}")
                    
                    thresholds = enhanced_results.get('thresholds', {})
                    if thresholds:
                        print(f"   - SNR: {thresholds.get('snr', 'N/A')}")
                        print(f"   - Prominence threshold: {thresholds.get('prominence', 'N/A')}")
                    
                    baseline_info = enhanced_results.get('baseline_info', [])
                    print(f"   - Baseline regions: {len(baseline_info)}")
                    
                    conflicts = enhanced_results.get('conflicts', [])
                    print(f"   - Conflicts detected: {len(conflicts)}")
                
                # แสดงข้อมูล baseline
                baseline_metadata = baseline.get('metadata', {})
                if baseline_metadata:
                    print(f"\n📏 Baseline Information:")
                    print(f"   - Method: {baseline_metadata.get('method_used', 'N/A')}")
                    print(f"   - Quality: {baseline_metadata.get('quality', 'N/A')}")
                    print(f"   - Regions found: {baseline_metadata.get('regions_found', 'N/A')}")
                    print(f"   - Total baseline points: {baseline_metadata.get('total_baseline_points', 'N/A')}")
                
                return True
                
            else:
                print(f"❌ API returned error: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ API request failed: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except FileNotFoundError:
        print(f"❌ Test file not found: {test_file}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to web server. Make sure it's running on port 8081")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_multiple_methods():
    """ทดสอบหลาย methods เพื่อเปรียบเทียบ"""
    
    test_file = "Test_data/Stm32/Pipot_Ferro_1_0mM_20mVpS_E4_scan_05.csv"
    methods = ['prominence', 'derivative', 'ml', 'enhanced_v3']
    
    print(f"\n🔬 Comparing All Methods")
    print(f"=" * 50)
    
    try:
        # โหลดข้อมูล
        df = pd.read_csv(test_file, skiprows=1)
        voltage = df['V'].values.tolist()
        current = df['uA'].values.tolist()
        
        results = {}
        
        for method in methods:
            print(f"\n🧪 Testing {method} method...")
            
            api_url = f"http://localhost:8081/peak_detection/get-peaks/{method}"
            payload = {
                "voltage": voltage,
                "current": current,
                "filename": test_file
            }
            
            try:
                response = requests.post(api_url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get('success', False):
                        peaks = result.get('peaks', [])
                        ox_peaks = [p for p in peaks if p['type'] == 'oxidation']
                        red_peaks = [p for p in peaks if p['type'] == 'reduction']
                        
                        results[method] = {
                            'total_peaks': len(peaks),
                            'ox_peaks': len(ox_peaks),
                            'red_peaks': len(red_peaks),
                            'method_info': result.get('method', method),
                            'enhanced_features': bool(result.get('enhanced_results')),
                            'baseline_quality': result.get('baseline', {}).get('metadata', {}).get('quality', 'N/A')
                        }
                        
                        print(f"   ✅ {method}: {len(peaks)} peaks (OX:{len(ox_peaks)}, RED:{len(red_peaks)})")
                    else:
                        results[method] = {'error': result.get('error', 'Unknown error')}
                        print(f"   ❌ {method}: {result.get('error', 'Unknown error')}")
                else:
                    results[method] = {'error': f'HTTP {response.status_code}'}
                    print(f"   ❌ {method}: HTTP {response.status_code}")
                    
            except Exception as e:
                results[method] = {'error': str(e)}
                print(f"   ❌ {method}: {e}")
        
        # สรุปผลการเปรียบเทียบ
        print(f"\n📊 COMPARISON SUMMARY")
        print(f"=" * 50)
        
        for method, result in results.items():
            if 'error' not in result:
                print(f"{method:12} | Peaks: {result['total_peaks']:2d} | OX: {result['ox_peaks']:2d} | RED: {result['red_peaks']:2d} | Enhanced: {result['enhanced_features']}")
            else:
                print(f"{method:12} | ERROR: {result['error']}")
        
        # แสดง Enhanced V3 advantages
        if 'enhanced_v3' in results and 'error' not in results['enhanced_v3']:
            print(f"\n🚀 Enhanced V3 Advantages:")
            print(f"   ✅ Advanced scan direction detection")
            print(f"   ✅ Dynamic threshold calculation")  
            print(f"   ✅ Multi-criteria peak validation")
            print(f"   ✅ Baseline-peak conflict avoidance")
            print(f"   ✅ Confidence scoring system")
        
        return results
        
    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
        return {}

if __name__ == "__main__":
    print("🎯 Enhanced Detector V3.0 - Web Integration Test")
    print("=" * 60)
    
    # ทดสอบ Enhanced V3
    success = test_enhanced_v3_api()
    
    if success:
        # ทดสอบเปรียบเทียบ methods
        test_multiple_methods()
        
        print(f"\n🎉 Integration test completed successfully!")
        print(f"Enhanced V3 is now available in the web interface!")
    else:
        print(f"\n❌ Integration test failed!")
        print(f"Check web server and Enhanced V3 implementation.")
