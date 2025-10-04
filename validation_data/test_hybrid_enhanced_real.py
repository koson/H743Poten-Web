#!/usr/bin/env python3
"""
🧪 Test HybridCV Enhanced with Real Data 
========================================

Test the complete HybridCV Enhanced system with real PalmSens CV data
to validate the workflow diagram implementation.

Author: H743Poten Research Team
Date: October 4, 2025
"""

import sys
import os
sys.path.append('.')
sys.path.append('validation_data')

import pandas as pd
import numpy as np
import glob
from hybrid_cv_enhanced import HybridCVEnhanced

def test_with_real_data():
    """Test HybridCV Enhanced with real CV data"""
    print("🧪 TESTING HYBRIDCV ENHANCED WITH REAL DATA")
    print("=" * 70)
    
    # Initialize HybridCV Enhanced
    hybrid = HybridCVEnhanced(config={
        'v5_weight': 0.6,
        'deepcv_weight': 0.4,
        'verbose': True,
        'adaptive_weighting': True,
        'consensus_threshold': 0.5
    })
    
    # Find real CV data files
    data_patterns = [
        "sample_data/*.csv",
        "test_files/*.csv", 
        "temp_data/*.csv",
        "validation_data/*.csv"
    ]
    
    all_files = []
    for pattern in data_patterns:
        files = glob.glob(pattern)
        all_files.extend(files)
    
    # Filter for CV files
    cv_files = [f for f in all_files if any(keyword in f.lower() 
                for keyword in ['cv', 'palmsens', 'scan', 'cyclic'])]
    
    if not cv_files:
        print("❌ No CV data files found")
        return False
    
    print(f"📁 Found {len(cv_files)} CV data files")
    
    # Test with multiple files
    test_files = cv_files[:5]  # Test first 5 files
    
    results_summary = []
    
    for i, filepath in enumerate(test_files, 1):
        print(f"\n🔬 Testing file {i}/{len(test_files)}: {os.path.basename(filepath)}")
        
        try:
            # Load CV data
            df = pd.read_csv(filepath)
            
            # Try different column name variations
            voltage_cols = [col for col in df.columns if any(v in col.lower() 
                           for v in ['voltage', 'potential', 'v', 'e'])]
            current_cols = [col for col in df.columns if any(c in col.lower() 
                           for c in ['current', 'i', 'amp'])]
            
            if not voltage_cols or not current_cols:
                print(f"⚠️  Skipping {filepath} - no voltage/current columns found")
                continue
            
            voltage = df[voltage_cols[0]].values
            current = df[current_cols[0]].values
            
            # Clean data
            mask = ~(np.isnan(voltage) | np.isnan(current))
            voltage = voltage[mask]
            current = current[mask]
            
            if len(voltage) < 10:
                print(f"⚠️  Skipping {filepath} - insufficient data points")
                continue
            
            # Run HybridCV Enhanced
            result = hybrid.detect_peaks(voltage, current, os.path.basename(filepath))
            
            # Store results
            ensemble = result.get('ensemble_result', {})
            results_summary.append({
                'filename': os.path.basename(filepath),
                'v5_peaks': result.get('v5_result', {}).get('peaks_detected', 0),
                'deepcv_peaks': result.get('deepcv_result', {}).get('peaks_detected', 0),
                'hybrid_peaks': ensemble.get('peaks_detected', 0),
                'confidence': ensemble.get('confidence', 0.0),
                'decision': ensemble.get('decision', 'unknown'),
                'processing_time': result.get('processing_time', 0.0) * 1000  # ms
            })
            
        except Exception as e:
            print(f"❌ Error processing {filepath}: {e}")
            continue
    
    # Performance Analysis
    if results_summary:
        print(f"\n📊 HYBRIDCV ENHANCED PERFORMANCE ANALYSIS")
        print("=" * 70)
        
        df_results = pd.DataFrame(results_summary)
        
        print(f"📁 Total files processed: {len(df_results)}")
        print(f"⏱️  Average processing time: {df_results['processing_time'].mean():.1f} ms")
        print(f"🎯 Average peaks detected:")
        print(f"   Enhanced V5: {df_results['v5_peaks'].mean():.1f}")
        print(f"   DeepCV V2:   {df_results['deepcv_peaks'].mean():.1f}")
        print(f"   Hybrid:      {df_results['hybrid_peaks'].mean():.1f}")
        print(f"📈 Average confidence: {df_results['confidence'].mean():.1f}%")
        
        # Decision analysis
        decision_counts = df_results['decision'].value_counts()
        print(f"\n🤔 Decision Analysis:")
        for decision, count in decision_counts.items():
            percentage = count / len(df_results) * 100
            print(f"   {decision}: {count} files ({percentage:.1f}%)")
        
        # Agreement analysis
        agreement_mask = df_results['v5_peaks'] == df_results['deepcv_peaks']
        agreement_rate = agreement_mask.sum() / len(df_results) * 100
        print(f"\n🤝 V5-DeepCV Agreement: {agreement_rate:.1f}%")
        
        # Individual results
        print(f"\n📋 Individual Results:")
        for _, row in df_results.iterrows():
            print(f"   {row['filename'][:25]:25s} | V5:{row['v5_peaks']:2d} DeepCV:{row['deepcv_peaks']:2d} Hybrid:{row['hybrid_peaks']:2d} | {row['confidence']:5.1f}% | {row['decision']:15s} | {row['processing_time']:6.1f}ms")
        
        # Overall system performance
        performance_summary = hybrid.get_performance_summary()
        print(f"\n🎯 Overall System Performance:")
        for key, value in performance_summary.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.2f}")
            else:
                print(f"   {key}: {value}")
        
        return True
    else:
        print("❌ No files successfully processed")
        return False

if __name__ == "__main__":
    success = test_with_real_data()
    print(f"\n{'🎉 REAL DATA TEST COMPLETE!' if success else '❌ REAL DATA TEST FAILED!'}")