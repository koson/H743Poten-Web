#!/usr/bin/env python3
"""
Debug Peak Validation
เทสต์ validation ของ peak
"""

import sys
sys.path.append('/mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web')

import numpy as np
import pandas as pd
from precision_peak_baseline_analyzer import PrecisionPeakBaselineAnalyzer

def main():
    # Initialize analyzer with debug config
    config = {
        'analyte': 'generic',
        'confidence_threshold': 30.0,  # Very low threshold for debugging
        'min_peak_height': 0.1,
        'peak_prominence_factor': 0.05
    }
    
    analyzer = PrecisionPeakBaselineAnalyzer(config)
    
    # Test file
    test_file = "Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv"
    
    print(f"🔬 Debug peak validation on: {test_file}")
    
    try:
        # Load data manually to see raw peak candidates
        df = pd.read_csv(test_file, skiprows=1)
        voltage = df.iloc[:, 0].values
        current = df.iloc[:, 1].values
        
        print(f"📊 Raw data: {len(voltage)} points")
        print(f"   Voltage: {voltage.min():.3f} to {voltage.max():.3f} V")
        print(f"   Current: {current.min():.3f} to {current.max():.3f} μA")
        
        # Test peak finding methods directly
        # Apply basic preprocessing
        mask = ~(np.isnan(voltage) | np.isnan(current))
        voltage_clean = voltage[mask]
        current_clean = current[mask]
        
        # Test SciPy peak finding directly
        print(f"\n🔍 Testing SciPy peak detection...")
        scipy_peaks = analyzer._find_peaks_scipy(voltage_clean, current_clean)
        print(f"   Found {len(scipy_peaks)} SciPy peaks:")
        
        for i, peak in enumerate(scipy_peaks[:5]):  # Show first 5
            print(f"     Peak {i+1}: {peak['voltage']:.3f}V, {peak['current']:.2f}μA, prominence: {peak['prominence']:.2f}")
        
        # Create minimal baseline for validation test
        from precision_peak_baseline_analyzer import BaselineData
        baseline = BaselineData(
            currents=np.zeros_like(current_clean),
            quality=50.0,
            noise_level=np.std(current_clean) * 0.1,
            method='test'
        )
        
        # Test validation directly
        print(f"\n🧪 Testing peak validation...")
        if scipy_peaks:
            test_peak = scipy_peaks[0]  # Test first peak
            
            try:
                peak_data = analyzer._analyze_single_peak(voltage_clean, current_clean, current_clean,
                                                        test_peak, baseline)
                print(f"   Peak analysis result:")
                print(f"     Voltage: {peak_data.voltage:.3f}V")
                print(f"     Height: {peak_data.height:.2f}μA") 
                print(f"     Confidence: {peak_data.confidence:.1f}%")
                print(f"     Signal-to-Noise: {peak_data.signal_to_noise:.1f}")
                print(f"     Quality: {peak_data.quality_score:.1f}%")
                
                # Check if it passes threshold
                threshold = config['confidence_threshold']
                print(f"     Threshold: {threshold}%")
                print(f"     Pass: {'✅' if peak_data.confidence >= threshold else '❌'}")
                
            except Exception as e:
                print(f"   ❌ Peak analysis failed: {e}")
                import traceback
                traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
