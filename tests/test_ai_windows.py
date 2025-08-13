#!/usr/bin/env python3
"""
Complete AI Analysis Test for Windows (No Hardware Required)
Tests all AI endpoints with simulated DPV data
"""

import sys
import os
import time
import threading
import requests
import numpy as np
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

def create_simulated_dpv_data():
    """Create realistic DPV measurement data"""
    # Simulate DPV scan from -0.7V to +0.7V
    voltages = np.linspace(-0.7, 0.7, 120)
    
    # Create baseline current with noise
    baseline = 1e-6  # 1 µA baseline
    noise = np.random.normal(0, 5e-8, len(voltages))  # 50 nA noise
    currents = np.full(len(voltages), baseline) + noise
    
    # Add realistic DPV peaks
    peaks = [
        {'voltage': -0.2, 'height': 2e-6, 'width': 0.05},  # Peak 1
        {'voltage': 0.1, 'height': 4e-6, 'width': 0.04},   # Peak 2 (main)
        {'voltage': 0.4, 'height': 1.5e-6, 'width': 0.06}, # Peak 3
    ]
    
    # Add Gaussian peaks
    for peak in peaks:
        peak_currents = peak['height'] * np.exp(
            -((voltages - peak['voltage']) / peak['width'])**2
        )
        currents += peak_currents
    
    return voltages.tolist(), currents.tolist()

def test_ai_endpoints():
    """Test all AI analysis endpoints with simulated data"""
    print("🧪 Testing AI Analysis Endpoints on Windows")
    print("=" * 50)
    
    # Create simulated data
    voltages, currents = create_simulated_dpv_data()
    measurement_data = [
        {'voltage': v, 'current': c} 
        for v, c in zip(voltages, currents)
    ]
    
    print(f"📊 Generated simulated DPV data:")
    print(f"   Points: {len(measurement_data)}")
    print(f"   Voltage range: {min(voltages):.3f}V to {max(voltages):.3f}V")
    print(f"   Current range: {min(currents):.2e}A to {max(currents):.2e}A")
    print()
    
    base_url = "http://localhost:5000/api/analysis"
    endpoints_to_test = [
        {
            'name': 'Status Check',
            'method': 'GET',
            'url': f'{base_url}/status',
            'data': None
        },
        {
            'name': 'Peak Detection',
            'method': 'POST',
            'url': f'{base_url}/peak-detection',
            'data': {'measurement_data': measurement_data}
        },
        {
            'name': 'Quality Assessment',
            'method': 'POST',
            'url': f'{base_url}/quality-assessment',
            'data': {'measurement_data': measurement_data}
        },
        {
            'name': 'Full Analysis',
            'method': 'POST',
            'url': f'{base_url}/analyze',
            'data': {
                'measurement_type': 'DPV',
                'measurement_data': measurement_data
            }
        }
    ]
    
    results = {}
    
    for endpoint in endpoints_to_test:
        print(f"🔍 Testing {endpoint['name']}...")
        
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(endpoint['url'], timeout=10)
            else:
                response = requests.post(
                    endpoint['url'], 
                    json=endpoint['data'], 
                    timeout=15
                )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    print(f"   ✅ SUCCESS")
                    
                    # Show specific results
                    if 'peaks_detected' in result.get('data', {}):
                        peaks = result['data']['peaks_detected']
                        print(f"   📈 Peaks detected: {peaks}")
                        
                        if peaks > 0:
                            peak_info = result['data']['peaks'][0]
                            print(f"   🎯 First peak: {peak_info['potential']:.3f}V, {peak_info['current']:.2e}A")
                    
                    if 'quality_metrics' in result.get('data', {}):
                        metrics = result['data']['quality_metrics']
                        print(f"   📊 Signal-to-Noise: {metrics.get('signal_to_noise_ratio', 'N/A')}")
                        print(f"   🏆 Overall Score: {result['data'].get('overall_score', 'N/A')}")
                    
                    if 'confidence_score' in result.get('data', {}):
                        conf = result['data']['confidence_score']
                        peaks_count = len(result['data'].get('peaks', []))
                        print(f"   🎯 Confidence: {conf:.3f}")
                        print(f"   📈 Total peaks: {peaks_count}")
                        
                        if 'electrochemical_parameters' in result['data']:
                            params = result['data']['electrochemical_parameters']
                            if 'peak_current' in params:
                                print(f"   ⚡ Peak current: {params['peak_current']:.2e}A")
                    
                    if 'capabilities' in result:
                        caps = result['capabilities']
                        print(f"   🔧 SciPy: {'✅' if caps.get('scipy_available') else '❌'}")
                        print(f"   🤖 Sklearn: {'✅' if caps.get('sklearn_available') else '❌'}")
                    
                    results[endpoint['name']] = 'PASS'
                else:
                    print(f"   ❌ API returned success=false: {result.get('error', 'Unknown error')}")
                    results[endpoint['name']] = 'FAIL'
            else:
                print(f"   ❌ HTTP Error {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"   Error: {response.text[:200]}")
                results[endpoint['name']] = 'FAIL'
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ TIMEOUT")
            results[endpoint['name']] = 'TIMEOUT'
        except requests.exceptions.ConnectionError:
            print(f"   🔌 CONNECTION ERROR")
            results[endpoint['name']] = 'CONNECTION_ERROR'
        except Exception as e:
            print(f"   💥 EXCEPTION: {e}")
            results[endpoint['name']] = 'EXCEPTION'
        
        print()
    
    return results

def start_flask_app():
    """Start Flask app in background for testing"""
    print("🚀 Starting Flask app for testing...")
    
    try:
        from app import app
        
        # Start Flask in a separate thread
        def run_flask():
            app.run(host='localhost', port=5000, debug=False, use_reloader=False)
        
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        # Wait for Flask to start
        print("⏳ Waiting for Flask to start...")
        time.sleep(3)
        
        # Test if Flask is running
        try:
            response = requests.get('http://localhost:5000/api/analysis/status', timeout=5)
            if response.status_code == 200:
                print("✅ Flask app is running!")
                return True
            else:
                print(f"❌ Flask app returned {response.status_code}")
                return False
        except:
            print("❌ Flask app is not responding")
            return False
            
    except ImportError as e:
        print(f"❌ Cannot import Flask app: {e}")
        return False
    except Exception as e:
        print(f"❌ Error starting Flask: {e}")
        return False

def main():
    """Main test function"""
    print("🔬 PyPiPo AI Analysis Windows Test")
    print("=" * 40)
    print(f"🕐 Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Start Flask app
    if not start_flask_app():
        print("💥 Failed to start Flask app. Exiting.")
        return False
    
    print()
    
    # Test AI endpoints
    results = test_ai_endpoints()
    
    # Summary
    print("📋 Test Summary:")
    print("-" * 30)
    
    total_tests = len(results)
    passed = sum(1 for r in results.values() if r == 'PASS')
    failed = total_tests - passed
    
    for test_name, result in results.items():
        status_icon = {
            'PASS': '✅',
            'FAIL': '❌',
            'TIMEOUT': '⏰',
            'CONNECTION_ERROR': '🔌',
            'EXCEPTION': '💥'
        }.get(result, '❓')
        
        print(f"   {status_icon} {test_name}: {result}")
    
    print()
    print(f"📊 Results: {passed}/{total_tests} tests passed")
    
    if passed == total_tests:
        print("🎉 All AI analysis endpoints are working correctly!")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed. Check the errors above.")
        return False

if __name__ == '__main__':
    success = main()
    
    print(f"\n🕐 Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Result: {'🎉 SUCCESS' if success else '❌ FAILURE'}")
    
    # Keep the program running briefly to see results
    input("\nPress Enter to exit...")
    
    sys.exit(0 if success else 1)
