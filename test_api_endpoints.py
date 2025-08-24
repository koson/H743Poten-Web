#!/usr/bin/env python3
"""
Test API Endpoints for Parameter Logging
Test the complete workflow via REST API
"""

import sys
import os
import requests
import json
import numpy as np
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_DATA_DIR = "test_files"

def create_test_csv_files():
    """Create test CSV files for testing"""
    if not os.path.exists(TEST_DATA_DIR):
        os.makedirs(TEST_DATA_DIR)
    
    # Create Palmsens test file
    palmsens_data = {
        'voltage': np.linspace(-0.4, 0.6, 100),
        'current': np.random.normal(0, 1, 100)
    }
    palmsens_data['current'][50:55] += 10  # Add a peak
    
    palmsens_file = os.path.join(TEST_DATA_DIR, 'Palmsens_5mM_CV_100mVpS_E1_test.csv')
    with open(palmsens_file, 'w') as f:
        f.write("Voltage(V),Current(µA)\n")
        for v, i in zip(palmsens_data['voltage'], palmsens_data['current']):
            f.write(f"{v:.4f},{i:.4f}\n")
    
    # Create STM32 test file
    stm32_data = {
        'voltage': np.linspace(-0.4, 0.6, 100),
        'current': np.random.normal(0, 1, 100)
    }
    stm32_data['current'][50:55] += 8  # Add a peak (slightly different)
    
    stm32_file = os.path.join(TEST_DATA_DIR, 'Pipot_Ferro_5_0mM_100mVpS_E4_test.csv')
    with open(stm32_file, 'w') as f:
        f.write("Voltage(V),Current(µA)\n")
        for v, i in zip(stm32_data['voltage'], stm32_data['current']):
            f.write(f"{v:.4f},{i:.4f}\n")
    
    return palmsens_file, stm32_file

def test_server_running():
    """Test if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ Server is running (status: {response.status_code})")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not accessible: {e}")
        return False

def test_peak_detection_api(csv_file):
    """Test peak detection API endpoint"""
    print(f"\n🔬 Testing peak detection with: {os.path.basename(csv_file)}")
    
    try:
        with open(csv_file, 'rb') as f:
            files = {'file': f}
            data = {
                'user_notes': f'API test with {os.path.basename(csv_file)}',
                'log_parameters': 'true'
            }
            
            response = requests.post(f"{BASE_URL}/analyze", files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Analysis successful")
                print(f"   📊 Peaks found: {len(result.get('peaks', []))}")
                
                if 'measurement_id' in result:
                    print(f"   💾 Measurement ID: {result['measurement_id']}")
                    return result['measurement_id']
                else:
                    print(f"   ⚠️ No measurement ID returned")
                    return None
            else:
                print(f"   ❌ API error: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return None

def test_parameter_api():
    """Test parameter logging API endpoints"""
    print(f"\n📋 Testing parameter API endpoints...")
    
    # Test get measurements
    try:
        response = requests.get(f"{BASE_URL}/api/measurements", timeout=10)
        if response.status_code == 200:
            measurements = response.json()
            print(f"   ✅ Retrieved {len(measurements)} measurements")
            
            # Show sample data
            for m in measurements[:3]:  # Show first 3
                print(f"      - ID {m['id']}: {m['sample_id']} ({m['instrument_type']})")
                
            return measurements
        else:
            print(f"   ❌ Failed to get measurements: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"   ❌ Exception getting measurements: {str(e)}")
        return []

def test_calibration_api():
    """Test calibration API endpoints"""
    print(f"\n🔗 Testing calibration API...")
    
    try:
        # Get calibration pairs
        response = requests.get(f"{BASE_URL}/api/calibration/pairs", timeout=10)
        if response.status_code == 200:
            pairs = response.json()
            print(f"   ✅ Found {len(pairs)} calibration pairs")
            
            for pair in pairs:
                sample_id = pair['sample_id']
                ref_count = len(pair['reference_measurements'])
                target_count = len(pair['target_measurements'])
                print(f"      - Sample '{sample_id}': {ref_count} ref + {target_count} target")
                
            return pairs
        else:
            print(f"   ❌ Failed to get calibration pairs: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"   ❌ Exception getting calibration pairs: {str(e)}")
        return []

def test_export_api():
    """Test data export API"""
    print(f"\n📤 Testing export API...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/export/csv", timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Export successful (size: {len(response.content)} bytes)")
            
            # Save sample export
            export_file = f"test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(export_file, 'wb') as f:
                f.write(response.content)
            print(f"   💾 Saved export to: {export_file}")
            
            return True
        else:
            print(f"   ❌ Export failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception during export: {str(e)}")
        return False

def main():
    """Run comprehensive API tests"""
    print("🚀 COMPREHENSIVE API ENDPOINT TESTS")
    print("=" * 60)
    
    # Check if server is running
    if not test_server_running():
        print("\n❌ Server not running. Please start the development server:")
        print("   python auto_dev.py start")
        return
    
    # Create test files
    print(f"\n📁 Creating test CSV files...")
    palmsens_file, stm32_file = create_test_csv_files()
    print(f"   ✅ Created: {palmsens_file}")
    print(f"   ✅ Created: {stm32_file}")
    
    # Test peak detection with both files
    measurement_ids = []
    for csv_file in [palmsens_file, stm32_file]:
        measurement_id = test_peak_detection_api(csv_file)
        if measurement_id:
            measurement_ids.append(measurement_id)
    
    # Test parameter API
    measurements = test_parameter_api()
    
    # Test calibration API
    pairs = test_calibration_api()
    
    # Test export API
    test_export_api()
    
    # Summary
    print(f"\n📊 TEST SUMMARY")
    print(f"=" * 30)
    print(f"✅ Measurements processed: {len(measurement_ids)}")
    print(f"✅ Total measurements in DB: {len(measurements)}")
    print(f"✅ Calibration pairs found: {len(pairs)}")
    
    # Clean up test files
    try:
        for file in [palmsens_file, stm32_file]:
            if os.path.exists(file):
                os.remove(file)
        if os.path.exists(TEST_DATA_DIR) and not os.listdir(TEST_DATA_DIR):
            os.rmdir(TEST_DATA_DIR)
        print(f"🧹 Cleaned up test files")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")
    
    print(f"\n🎉 API TESTS COMPLETED!")

if __name__ == '__main__':
    main()