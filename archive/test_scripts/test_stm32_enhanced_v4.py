#!/usr/bin/env python3
"""
Test Enhanced V4 Improved with STM32 H743 data
"""

import requests
import time
import pandas as pd
import numpy as np
import random

def load_stm32_data():
    """Load STM32 H743 CV data files"""
    
    stm32_files = [
        "cv_data/measurement_100_20.0mVs_2025-08-25T06-48-42.312168.csv",  # 20mV/s
        "cv_data/measurement_102_50.0mVs_2025-08-25T06-49-05.056081.csv",  # 50mV/s
        "cv_data/measurement_106_100.0mVs_2025-08-25T07-17-55.233200.csv", # 100mV/s
        "cv_data/measurement_103_200.0mVs_2025-08-25T06-49-57.973566.csv", # 200mV/s
        "cv_data/measurement_101_400.0mVs_2025-08-25T06-48-52.997092.csv"  # 400mV/s
    ]
    
    data_files = []
    for file_path in stm32_files:
        try:
            df = pd.read_csv(file_path)
            if 'Voltage(V)' in df.columns and 'Current(uA)' in df.columns:
                voltage = df['Voltage(V)'].values.tolist()
                current = df['Current(uA)'].values.tolist()
                
                # Extract scan rate from filename
                scan_rate = file_path.split('_')[1].replace('.0mVs', 'mV/s')
                
                data_files.append({
                    'voltage': voltage,
                    'current': current,
                    'filename': f"STM32_H743_{scan_rate}"
                })
                
                print(f"✅ Loaded {file_path}")
                print(f"   📊 Data points: {len(voltage)}")
                print(f"   📊 Voltage: {min(voltage):.3f}V to {max(voltage):.3f}V")
                print(f"   📊 Current: {min(current):.1f}µA to {max(current):.1f}µA")
                
        except Exception as e:
            print(f"❌ Failed to load {file_path}: {str(e)}")
    
    return data_files

def test_enhanced_v4_with_stm32():
    """Test Enhanced V4 Improved with STM32 data"""
    
    print("🧪 Testing Enhanced V4 Improved with STM32 H743 data...")
    
    # Load STM32 data
    data_files = load_stm32_data()
    
    if not data_files:
        print("❌ No STM32 data files loaded")
        return False
    
    # Test with multiple files (like production workflow)
    print(f"\n🚀 Testing Enhanced V4+ with {len(data_files)} STM32 files...")
    
    data = {'dataFiles': data_files}
    
    try:
        start = time.time()
        response = requests.post('http://127.0.0.1:8080/get-peaks/enhanced_v4_improved', 
                               json=data, timeout=30)
        end = time.time()
        
        print(f"⏱️  Processing time: {end-start:.2f}s")
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            peaks = result.get('peaks', [])
            
            print(f"✅ API Response Success")
            print(f"📊 Peak structure: {len(peaks)} files processed")
            
            total_peaks = 0
            oxidation_peaks = 0
            reduction_peaks = 0
            
            for i, file_peaks in enumerate(peaks):
                file_name = data_files[i]['filename']
                peak_count = len(file_peaks)
                total_peaks += peak_count
                
                ox_count = len([p for p in file_peaks if p.get('type') == 'oxidation'])
                red_count = len([p for p in file_peaks if p.get('type') == 'reduction'])
                
                oxidation_peaks += ox_count
                reduction_peaks += red_count
                
                print(f"   📄 {file_name}: {peak_count} peaks (Ox: {ox_count}, Red: {red_count})")
                
                # Show peak details for first few files
                if i < 3 and peak_count > 0:
                    for j, peak in enumerate(file_peaks[:2]):  # Show first 2 peaks
                        v = peak.get('voltage', 'N/A')
                        i_val = peak.get('current', 'N/A')
                        conf = peak.get('confidence', 'N/A')
                        peak_type = peak.get('type', 'unknown')
                        print(f"      Peak {j+1}: {peak_type} at V={v:.3f}V, I={i_val:.1f}µA, Conf={conf:.1f}%")
            
            print(f"\n📈 STM32 Detection Summary:")
            print(f"   🔴 Total Oxidation peaks: {oxidation_peaks}")
            print(f"   🔵 Total Reduction peaks: {reduction_peaks}")
            print(f"   📊 Total peaks detected: {total_peaks}")
            print(f"   📊 Average peaks per file: {total_peaks/len(peaks):.1f}")
            
            # Check if we have reasonable detection
            has_oxidation = oxidation_peaks > 0
            has_reduction = reduction_peaks > 0
            reasonable_total = total_peaks >= len(peaks)  # At least 1 peak per file on average
            
            if has_oxidation and has_reduction and reasonable_total:
                print(f"✅ STM32 detection looks GOOD!")
                return True
            else:
                print(f"⚠️  STM32 detection may need adjustment:")
                if not has_oxidation:
                    print(f"      - No oxidation peaks detected")
                if not has_reduction:
                    print(f"      - No reduction peaks detected")
                if not reasonable_total:
                    print(f"      - Very few peaks detected overall")
                return False
                
        else:
            print(f"❌ API Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_enhanced_v4_with_stm32()
    if success:
        print(f"\n🎉 STM32 H743 test PASSED!")
    else:
        print(f"\n😞 STM32 H743 test needs adjustments")
