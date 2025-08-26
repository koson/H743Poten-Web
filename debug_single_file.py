#!/usr/bin/env python3
"""
Debug single file - ตรวจสอบว่าไฟล์ที่เลือกเกิดอะไรขึ้น
"""

import pandas as pd
import numpy as np
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the detection functions
from src.routes.peak_detection import detect_peaks_prominence

def debug_file(file_path):
    """Debug a specific file to see what happens with peak detection"""
    
    print(f"\n🔍 Debugging file: {file_path}")
    print("=" * 60)
    
    try:
        # Load the file - skip the first line (FileName header)
        df = pd.read_csv(file_path, skiprows=1)
        print(f"📁 File loaded: {len(df)} rows")
        print(f"📊 Columns: {list(df.columns)}")
        
        # Extract voltage and current
        voltage = df.iloc[:, 0].values  # First column (V)
        current = df.iloc[:, 1].values  # Second column (uA)
        
        print(f"⚡ Voltage range: {voltage.min():.3f} to {voltage.max():.3f} V")
        print(f"🔋 Current range: {current.min():.3f} to {current.max():.3f} μA")
        
        # Run peak detection
        print(f"\n🎯 Running peak detection...")
        result = detect_peaks_prominence(voltage, current)
        
        print(f"\n📊 Results:")
        print(f"   Method: {result.get('method', 'unknown')}")
        print(f"   Total peaks: {len(result.get('peaks', []))}")
        print(f"   Rejected peaks: {len(result.get('rejected_peaks', []))}")
        
        if 'peak_summary' in result:
            summary = result['peak_summary']
            print(f"   Valid Ox: {summary.get('oxidation_valid', 0)}")
            print(f"   Valid Red: {summary.get('reduction_valid', 0)}")
            print(f"   Rejected Ox: {summary.get('oxidation_rejected', 0)}")
            print(f"   Rejected Red: {summary.get('reduction_rejected', 0)}")
        
        # Show individual peaks
        peaks = result.get('peaks', [])
        if peaks:
            print(f"\n✅ Valid Peaks:")
            for i, peak in enumerate(peaks):
                print(f"   {i+1}. {peak['type'].title()}: V={peak['voltage']:.3f}V, I={peak['current']:.3f}μA")
        
        rejected = result.get('rejected_peaks', [])
        if rejected:
            print(f"\n❌ Rejected Peaks:")
            for i, peak in enumerate(rejected):
                print(f"   {i+1}. {peak['type'].title()}: V={peak['voltage']:.3f}V, I={peak['current']:.3f}μA")
                print(f"      Reason: {peak['reason']}")
        
        # Check baseline
        baseline = result.get('baseline', {})
        if baseline:
            print(f"\n📈 Baseline Info:")
            print(f"   Forward length: {len(baseline.get('forward', []))}")
            print(f"   Reverse length: {len(baseline.get('reverse', []))}")
            print(f"   Method: {baseline.get('metadata', {}).get('method_used', 'unknown')}")
        
        print("\n" + "=" * 60)
        return result
        
    except Exception as e:
        print(f"❌ Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test the problematic file
    test_file = "Test_data/Stm32/Pipot_Ferro_1_0mM/Pipot_Ferro-1_0mM_100mVpS_E1_scan_02.csv"
    debug_file(test_file)