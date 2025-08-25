#!/usr/bin/env python3
"""
Test Voltage Window Baseline Detector
=====================================
Direct test of the new voltage window-based baseline detector
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging
from baseline_detector_voltage_windows import voltage_window_baseline_detector

# Set up logging to see debug info
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

def load_test_file(filepath):
    """Load CV data from CSV file"""
    try:
        df = pd.read_csv(filepath)
        
        # Handle different file formats
        if 'V' in df.columns and 'I' in df.columns:
            voltage = df['V'].values
            current = df['I'].values
        elif 'Voltage' in df.columns and 'Current' in df.columns:
            voltage = df['Voltage'].values
            current = df['Current'].values
        elif len(df.columns) >= 2:
            voltage = df.iloc[:, 0].values
            current = df.iloc[:, 1].values
        else:
            raise ValueError("Cannot identify voltage and current columns")
            
        return voltage, current
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return None, None

def test_voltage_window_detector():
    """Test the voltage window baseline detector on real files"""
    
    print("🧪 VOLTAGE WINDOW BASELINE DETECTOR TEST")
    print("=" * 60)
    
    # Test files
    test_files = [
        "cv_data/measurement_93_100.0mVs_2025-08-25T06-39-11.686802.csv",
        "cv_data/measurement_95_200.0mVs_2025-08-25T06-46-14.158045.csv", 
        "cv_data/measurement_96_20.0mVs_2025-08-25T06-46-22.774810.csv"
    ]
    
    for i, filepath in enumerate(test_files):
        print(f"\n📂 Test {i+1}: {filepath}")
        print("-" * 40)
        
        voltage, current = load_test_file(filepath)
        if voltage is None:
            continue
            
        print(f"📊 Data loaded: {len(voltage)} points")
        print(f"🔋 Voltage range: {voltage.min():.3f}V to {voltage.max():.3f}V")
        print(f"⚡ Current range: {current.min():.2e} to {current.max():.2e} A")
        
        # Run voltage window detector
        try:
            forward_baseline, reverse_baseline, info = voltage_window_baseline_detector(
                voltage, current
            )
            
            print(f"\n✅ Detection completed!")
            print(f"📈 Forward baseline points: {np.count_nonzero(forward_baseline)}/{len(forward_baseline)}")
            print(f"📉 Reverse baseline points: {np.count_nonzero(reverse_baseline)}/{len(reverse_baseline)}")
            
            if 'forward_info' in info and info['forward_info']:
                fwd_info = info['forward_info']
                print(f"🔍 Forward: {fwd_info.get('segment_count', 0)} segments, "
                      f"avg R²={fwd_info.get('avg_r2', 0):.3f}")
                      
            if 'reverse_info' in info and info['reverse_info']:
                rev_info = info['reverse_info']
                print(f"🔍 Reverse: {rev_info.get('segment_count', 0)} segments, "
                      f"avg R²={rev_info.get('avg_r2', 0):.3f}")
            
            # Basic quality check
            total_baseline_points = np.count_nonzero(forward_baseline) + np.count_nonzero(reverse_baseline)
            coverage = total_baseline_points / len(voltage)
            print(f"📊 Coverage: {coverage:.1%} of data points")
            
            if coverage < 0.1:
                print("⚠️ Low baseline coverage - may need parameter tuning")
            elif coverage > 0.5:
                print("✅ Good baseline coverage")
            else:
                print("📊 Moderate baseline coverage")
                
        except Exception as e:
            print(f"❌ Error in detection: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_voltage_window_detector()