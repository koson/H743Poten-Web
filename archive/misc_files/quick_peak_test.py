#!/usr/bin/env python3
"""
Quick Peak Detection Test
เทสต์เร็วเพื่อดูการตรวจจับ peak
"""

import sys
sys.path.append('/mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from precision_peak_baseline_analyzer import PrecisionPeakBaselineAnalyzer

def main():
    # Initialize analyzer
    config = {
        'analyte': 'generic',
        'confidence_threshold': 50.0,
        'min_peak_height': 0.5,
        'peak_prominence_factor': 0.10  # Reduced for better detection
    }
    
    analyzer = PrecisionPeakBaselineAnalyzer(config)
    
    # Test file
    test_file = "Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv"
    
    print(f"🔬 Testing peak detection on: {test_file}")
    
    try:
        # Load data
        data = pd.read_csv(test_file)
        voltage = data.iloc[:, 0].values
        current = data.iloc[:, 1].values * 1e6  # Convert to μA
        
        print(f"📊 Data loaded: {len(voltage)} points")
        print(f"   Voltage: {voltage.min():.3f} to {voltage.max():.3f} V")
        print(f"   Current: {current.min():.3f} to {current.max():.3f} μA")
        
        # Run analysis
        result = analyzer.analyze_cv_data(test_file)
        
        print(f"\n🎯 ANALYSIS RESULTS:")
        print(f"   Success: {result['success']}")
        print(f"   Peaks detected: {len(result['peaks'])}")
        print(f"   Baseline quality: {result['baseline_quality']:.1f}%")
        print(f"   Overall quality: {result['overall_quality']:.1f}%")
        
        if result['peaks']:
            print(f"\n📍 DETECTED PEAKS:")
            for i, peak in enumerate(result['peaks']):
                print(f"   Peak {i+1}: {peak['voltage']:.3f}V, {peak['current']:.2f}μA ({peak['peak_type']})")
                print(f"             Confidence: {peak['confidence']:.1f}%, Height: {peak['height']:.2f}μA")
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        
        # Original data
        plt.subplot(2, 1, 1)
        plt.plot(voltage, current, 'b-', alpha=0.7, label='Original Data')
        
        if 'baseline' in result:
            baseline = result['baseline']['currents']
            plt.plot(voltage[:len(baseline)], baseline, 'r--', alpha=0.8, label='Baseline')
        
        if result['peaks']:
            peak_voltages = [p['voltage'] for p in result['peaks']]
            peak_currents = [p['current'] for p in result['peaks']]
            plt.scatter(peak_voltages, peak_currents, c='red', s=100, zorder=5, label='Peaks')
        
        plt.xlabel('Voltage (V)')
        plt.ylabel('Current (μA)')
        plt.title('CV Data with Peak Detection')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Peak details
        plt.subplot(2, 1, 2)
        if result['peaks']:
            peak_numbers = range(1, len(result['peaks']) + 1)
            confidences = [p['confidence'] for p in result['peaks']]
            heights = [p['height'] for p in result['peaks']]
            
            plt.bar([p - 0.2 for p in peak_numbers], confidences, 0.4, 
                   label='Confidence (%)', alpha=0.7, color='green')
            plt.bar([p + 0.2 for p in peak_numbers], heights, 0.4, 
                   label='Height (μA)', alpha=0.7, color='orange')
        
        plt.xlabel('Peak Number')
        plt.ylabel('Value')
        plt.title('Peak Confidence and Height')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('quick_peak_test_result.png', dpi=150, bbox_inches='tight')
        print(f"\n📊 Visualization saved: quick_peak_test_result.png")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
