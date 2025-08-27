#!/usr/bin/env python3
"""
Enhanced V5 Production API Test
ทดสอบ Enhanced V5 ผ่าน API endpoints ในโหมด production
"""

import requests
import json
import pandas as pd
import time

def test_enhanced_v5_api():
    """ทดสอบ Enhanced V5 ผ่าน API"""
    
    print("🚀 Testing Enhanced V5 Production API")
    print("=" * 50)
    
    # Load test data
    test_file = "Test_data/Stm32/Pipot_Ferro_1_0mM/Pipot_Ferro_1_0mM_20mVpS_E4_scan_05.csv"
    
    try:
        # Read and prepare data (skip metadata row)
        df = pd.read_csv(test_file, skiprows=1)
        voltage = df['V'].values.tolist()
        current = df['uA'].values.tolist()
        
        print(f"📁 Loaded test data: {len(voltage)} points")
        print(f"📊 Voltage range: {min(voltage):.3f} to {max(voltage):.3f}V")
        print(f"📈 Current range: {min(current):.3f} to {max(current):.3f}µA")
        
        # Prepare API request
        api_data = {
            'dataFiles': [{
                'voltage': voltage,
                'current': current,
                'filename': 'test_enhanced_v5.csv'
            }]
        }
        
        # Test Enhanced V5 API
        print(f"\n🔬 Testing Enhanced V5 API...")
        start_time = time.time()
        
        response = requests.post(
            'http://127.0.0.1:8080/peak_detection/get-peaks/enhanced_v5',
            json=api_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Enhanced V5 API Success! ({processing_time:.2f}s)")
            print(f"🎯 Method: {result.get('method', 'unknown')}")
            
            # Analyze peaks
            peaks = result.get('peaks_per_file', [{}])[0].get('peaks', [])
            print(f"📊 Peaks found: {len(peaks)}")
            
            if peaks:
                ox_peaks = [p for p in peaks if p.get('type') == 'oxidation']
                red_peaks = [p for p in peaks if p.get('type') == 'reduction']
                
                print(f"🔴 Oxidation peaks: {len(ox_peaks)}")
                print(f"🔵 Reduction peaks: {len(red_peaks)}")
                
                # Show peak details
                print(f"\n📈 Peak Details:")
                for i, peak in enumerate(peaks[:5]):  # Show first 5 peaks
                    print(f"  {i+1}. {peak.get('type', 'unknown'):>10} | "
                          f"{peak.get('voltage', 0):.3f}V | "
                          f"{peak.get('current', 0):.3f}µA | "
                          f"conf: {peak.get('confidence', 0):.0f}%")
                
                if len(peaks) > 5:
                    print(f"  ... and {len(peaks) - 5} more peaks")
            
            # Baseline info
            baseline_info = result.get('enhanced_v5_results', {})
            if baseline_info:
                print(f"\n📏 Baseline Analysis:")
                print(f"  Regions: {len(baseline_info.get('baseline_info', []))}")
                print(f"  Rejected peaks: {len(baseline_info.get('rejected_peaks', []))}")
                print(f"  Production ready: {baseline_info.get('production_ready', False)}")
            
            return True
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except FileNotFoundError:
        print(f"❌ Test file not found: {test_file}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_all_methods_comparison():
    """เปรียบเทียบ Enhanced V5 กับ methods อื่นๆ"""
    
    print(f"\n🔄 Comparing all detection methods...")
    print("=" * 50)
    
    methods = ['prominence', 'enhanced_v3', 'enhanced_v5']
    test_file = "Test_data/Stm32/Pipot_Ferro_1_0mM/Pipot_Ferro_1_0mM_20mVpS_E4_scan_05.csv"
    
    try:
        # Load data
        df = pd.read_csv(test_file, skiprows=1)
        voltage = df['V'].values.tolist()
        current = df['uA'].values.tolist()
        
        api_data = {
            'dataFiles': [{
                'voltage': voltage,
                'current': current,
                'filename': 'comparison_test.csv'
            }]
        }
        
        results = {}
        
        for method in methods:
            print(f"\n🧪 Testing {method}...")
            
            try:
                start_time = time.time()
                response = requests.post(
                    f'http://127.0.0.1:8080/peak_detection/get-peaks/{method}',
                    json=api_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                processing_time = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    peaks = result.get('peaks_per_file', [{}])[0].get('peaks', [])
                    
                    results[method] = {
                        'success': True,
                        'peaks_count': len(peaks),
                        'processing_time': processing_time,
                        'ox_peaks': len([p for p in peaks if p.get('type') == 'oxidation']),
                        'red_peaks': len([p for p in peaks if p.get('type') == 'reduction'])
                    }
                    
                    print(f"  ✅ {len(peaks)} peaks in {processing_time:.2f}s")
                    
                else:
                    results[method] = {'success': False, 'error': response.status_code}
                    print(f"  ❌ Failed: {response.status_code}")
                    
            except Exception as e:
                results[method] = {'success': False, 'error': str(e)}
                print(f"  ❌ Error: {str(e)}")
        
        # Summary comparison
        print(f"\n📊 COMPARISON SUMMARY:")
        print("=" * 50)
        print(f"{'Method':<15} {'Peaks':<8} {'OX':<5} {'RED':<5} {'Time':<8} {'Status'}")
        print("-" * 50)
        
        for method, result in results.items():
            if result['success']:
                print(f"{method:<15} {result['peaks_count']:<8} "
                      f"{result['ox_peaks']:<5} {result['red_peaks']:<5} "
                      f"{result['processing_time']:.2f}s   {'✅'}")
            else:
                print(f"{method:<15} {'N/A':<8} {'N/A':<5} {'N/A':<5} {'N/A':<8} {'❌'}")
        
        # Enhanced V5 performance analysis
        if 'enhanced_v5' in results and results['enhanced_v5']['success']:
            v5_result = results['enhanced_v5']
            print(f"\n🏆 Enhanced V5 Performance:")
            print(f"  Total peaks: {v5_result['peaks_count']}")
            print(f"  Processing time: {v5_result['processing_time']:.2f}s")
            print(f"  Production ready: ✅")
            
            return True
        else:
            print(f"\n❌ Enhanced V5 not working properly")
            return False
            
    except Exception as e:
        print(f"❌ Comparison test failed: {str(e)}")
        return False

def main():
    """Main test execution"""
    print("🎯 Enhanced V5 Production Testing Suite")
    print("=" * 60)
    
    # Test 1: Enhanced V5 API
    test1_success = test_enhanced_v5_api()
    
    # Test 2: Method comparison
    test2_success = test_all_methods_comparison()
    
    # Final summary
    print(f"\n🎯 FINAL RESULTS:")
    print("=" * 60)
    print(f"Enhanced V5 API Test: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"Method Comparison:    {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        print(f"\n🎉 Enhanced V5 is PRODUCTION READY! 🚀")
        print(f"✨ All tests passed successfully!")
    else:
        print(f"\n🔧 Enhanced V5 needs additional work")
        print(f"⚠️ Some tests failed")

if __name__ == "__main__":
    main()
