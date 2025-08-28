#!/usr/bin/env python3
"""
Quick test for Fair PLS Comparison
"""

import requests
import glob
from pathlib import Path

def test_server():
    """ทดสอบ server connection"""
    try:
        response = requests.get('http://localhost:8080/', timeout=5)
        print(f"✅ Server connection: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Server error: {e}")
        return False

def test_api():
    """ทดสอบ API endpoint"""
    try:
        test_data = {
            'dataFiles': [{
                'voltage': [0.0, 0.1, 0.2, 0.3],
                'current': [0.001, 0.002, 0.001, 0.0005],
                'filename': 'test.csv'
            }]
        }
        response = requests.post(
            'http://localhost:8080/api/enhanced_v4_improved_analysis', 
            json=test_data, 
            timeout=10
        )
        result = response.json()
        print(f"✅ API test: {result.get('success', False)}")
        return result.get('success', False)
    except Exception as e:
        print(f"❌ API error: {e}")
        return False

def test_data_access():
    """ทดสอบการเข้าถึงข้อมูล"""
    pal_files = glob.glob('Test_data/Palmsens/Palmsens_10mM/*.csv')
    stm32_files = glob.glob('Test_data/Stm32/Pipot_10mM/*.csv')
    
    pal_filtered = [f for f in pal_files if 'scan_01' not in f][:5]
    stm32_filtered = [f for f in stm32_files if 'scan_01' not in f][:5]
    
    print(f"✅ Data access: Palmsens {len(pal_filtered)}, STM32 {len(stm32_filtered)}")
    return pal_filtered, stm32_filtered

def test_real_file_analysis():
    """ทดสอบการวิเคราะห์ไฟล์จริง"""
    pal_files, stm32_files = test_data_access()
    
    if not pal_files:
        print("❌ No Palmsens files found")
        return False
    
    try:
        # Read test file
        import pandas as pd
        df = pd.read_csv(pal_files[0], skiprows=1)
        
        # Get voltage and current data
        if 'V' in df.columns and 'uA' in df.columns:
            voltage = df['V'].values.tolist()
            current = df['uA'].values.tolist()
        else:
            print("❌ Unknown CSV format")
            return False
        
        payload = {
            'dataFiles': [{
                'voltage': voltage,
                'current': current,
                'filename': Path(pal_files[0]).name
            }]
        }
        
        response = requests.post(
            'http://localhost:8080/api/enhanced_v4_improved_analysis',
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('results'):
                file_result = result['results'][0]
                if file_result.get('success'):
                    peaks = file_result.get('peaks', [])
                    print(f"✅ Real file analysis: {len(peaks)} peaks found")
                    if len(peaks) >= 2:
                        print(f"   Peak 1: {peaks[0]['voltage']:.3f}V, {peaks[0]['current']:.6f}A")
                        print(f"   Peak 2: {peaks[1]['voltage']:.3f}V, {peaks[1]['current']:.6f}A")
                    return True
                else:
                    print(f"❌ File analysis failed: {file_result}")
                    return False
            else:
                print(f"❌ Analysis failed: {result}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ File analysis error: {e}")
        return False

def main():
    print("🧪 Fair PLS Comparison - Quick Test")
    print("=" * 50)
    
    # Test 1: Server connection
    if not test_server():
        print("⚠️ Server not available")
        return
    
    # Test 2: API endpoint
    if not test_api():
        print("⚠️ API not working")
        return
    
    # Test 3: Data access
    pal_files, stm32_files = test_data_access()
    if not pal_files or not stm32_files:
        print("⚠️ Data not available")
        return
    
    # Test 4: Real file analysis
    if not test_real_file_analysis():
        print("⚠️ Real file analysis failed")
        return
    
    print("\n🎉 All tests passed! Ready for full analysis!")

if __name__ == "__main__":
    main()
