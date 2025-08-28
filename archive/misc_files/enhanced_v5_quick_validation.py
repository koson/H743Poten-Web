#!/usr/bin/env python3
"""
Enhanced V5 Quick Validation Test
แค่ทดสอบไฟล์บางตัวเพื่อให้แน่ใจว่า Enhanced V5 ทำงานได้
"""

import os
import pandas as pd
import logging
from enhanced_detector_v5 import EnhancedDetectorV5
import json
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(message)s')

def find_data_columns(df):
    """Find voltage and current columns with improved detection"""
    
    # Look for numeric columns only
    numeric_cols = df.select_dtypes(include=['float64', 'int64', 'float32', 'int32']).columns.tolist()
    
    if len(numeric_cols) < 2:
        print(f"⚠️ Warning: Only {len(numeric_cols)} numeric columns found")
        return None, None
    
    # Take first two numeric columns as voltage, current
    voltage_col = numeric_cols[0]
    current_col = numeric_cols[1]
    
    print(f"📊 Using columns: '{voltage_col}' (voltage), '{current_col}' (current)")
    return voltage_col, current_col

def test_single_file_quick(file_path):
    """Quick test of single file"""
    try:
        print(f"\n🔍 Testing: {os.path.basename(file_path)}")
        
        # Read file (skip first row if it's metadata)
        try:
            df = pd.read_csv(file_path)
            # Check if first row is metadata
            if df.shape[1] == 1 or 'FileName:' in str(df.iloc[0, 0]):
                df = pd.read_csv(file_path, skiprows=1)
        except:
            df = pd.read_csv(file_path, skiprows=1)
            
        print(f"📁 Shape: {df.shape}")
        
        # Find data columns
        voltage_col, current_col = find_data_columns(df)
        if voltage_col is None:
            return False, "Column detection failed"
        
        # Extract data
        voltage = df[voltage_col].values
        current = df[current_col].values
        
        print(f"📈 Voltage range: {voltage.min():.3f} to {voltage.max():.3f}")
        print(f"📊 Current range: {current.min():.3f} to {current.max():.3f}")
        
        # Run Enhanced V5
        detector = EnhancedDetectorV5()
        result = detector.detect_peaks_enhanced_v5(voltage, current)
        
        # Parse result (dict format from Enhanced V5)
        if isinstance(result, dict) and 'peaks' in result:
            peaks = result['peaks']
            
            # Count peaks by type
            ox_count = len([p for p in peaks if p['type'] == 'oxidation'])
            red_count = len([p for p in peaks if p['type'] == 'reduction'])
            total_peaks = len(peaks)
            
            print(f"🎯 Results: {ox_count} OX peaks, {red_count} RED peaks (Total: {total_peaks})")
            
            # Success criteria: มี peaks อย่างน้อย 1 peak
            success = total_peaks > 0
            
            return success, {
                'ox_peaks': ox_count,
                'red_peaks': red_count,
                'total_peaks': total_peaks,
                'baseline_regions': len(result.get('baseline_info', [])),
                'rejected_peaks': len(result.get('rejected_peaks', []))
            }
            
        else:
            return False, f"Invalid result format: {type(result)}"
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, str(e)

def main():
    print("🚀 Enhanced V5 Quick Validation Test")
    print("=" * 60)
    
    # Test a few representative files
    test_files = [
        "Test_data/Stm32/Pipot_Ferro_1_0mM/Pipot_Ferro_1_0mM_20mVpS_E4_scan_05.csv",
        "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_100mVpS_E1_scan_01.csv",
        "Test_data/Palmsens_Data/Palmsens_5mM/Palmsens_5mM_CV_100mVpS_E1_scan_01.csv",
    ]
    
    results = []
    
    for test_file in test_files:
        if os.path.exists(test_file):
            success, details = test_single_file_quick(test_file)
            results.append({
                'file': os.path.basename(test_file),
                'success': success,
                'details': details
            })
        else:
            print(f"⚠️ File not found: {test_file}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 QUICK VALIDATION SUMMARY:")
    print("=" * 60)
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['file']}: {result['details']}")
    
    print(f"\n🎯 Success Rate: {successful}/{total} ({100*successful/total:.1f}%)")
    
    if successful > 0:
        print("✨ Enhanced V5 is working correctly!")
    else:
        print("🔧 Enhanced V5 needs debugging")

if __name__ == "__main__":
    main()
