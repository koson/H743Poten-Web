#!/usr/bin/env python3
"""
Baseline-only test script
Focus on testing baseline detection algorithms quickly
"""

import sys
import os
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_baseline_only(file_path):
    """Test only baseline detection"""
    from routes.peak_detection import detect_improved_baseline_2step
    
    print(f"\n📁 {os.path.basename(file_path)}")
    
    try:
        # Load data
        df = pd.read_csv(file_path, skiprows=1)
        if 'uA' in df.columns:
            v, i = df['V'].values, df['uA'].values
            unit = "µA"
        else:
            v, i = df['V'].values, df['A'].values * 1e6
            unit = "µA (converted)"
        
        print(f"📊 {len(v)} points, V:[{v.min():.3f},{v.max():.3f}], I:[{i.min():.1f},{i.max():.1f}]{unit}")
        
        # Test baseline detection
        result = detect_improved_baseline_2step(v, i)
        
        if result is None:
            print("❌ Baseline detection FAILED")
            return False
        
        bf, br, info = result
        
        # Stats
        print(f"✅ Forward: {len(bf)} points, range=[{bf.min():.1f}, {bf.max():.1f}]µA, mean={bf.mean():.1f}µA")
        print(f"✅ Reverse: {len(br)} points, range=[{br.min():.1f}, {br.max():.1f}]µA, mean={br.mean():.1f}µA")
        
        # Check quality
        forward_span = bf.max() - bf.min()
        reverse_span = br.max() - br.min()
        data_span = i.max() - i.min()
        
        # Quality metrics
        forward_quality = "🟢" if forward_span < data_span * 0.1 else "🟡" if forward_span < data_span * 0.2 else "🔴"
        reverse_quality = "🟢" if reverse_span < data_span * 0.1 else "🟡" if reverse_span < data_span * 0.2 else "🔴"
        
        print(f"📈 Quality: Forward {forward_quality} (span:{forward_span:.1f}), Reverse {reverse_quality} (span:{reverse_span:.1f})")
        
        # Segment info
        if info:
            if 'forward_segment' in info and info['forward_segment']:
                fs = info['forward_segment']
                print(f"🔵 Forward segment: R²={fs.get('r2', 0):.3f}, slope={fs.get('slope', 0):.2e}")
            
            if 'reverse_segment' in info and info['reverse_segment']:
                rs = info['reverse_segment']
                print(f"🔵 Reverse segment: R²={rs.get('r2', 0):.3f}, slope={rs.get('slope', 0):.2e}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def batch_test(directory, pattern="*.csv", max_files=10):
    """Test multiple files"""
    from pathlib import Path
    
    test_path = Path(directory)
    csv_files = list(test_path.glob(pattern))[:max_files]
    
    if not csv_files:
        print(f"❌ No CSV files found in {directory}")
        return
    
    print(f"\n{'='*60}")
    print(f"BATCH TEST: {len(csv_files)} files in {directory}")
    print(f"{'='*60}")
    
    results = []
    for file_path in csv_files:
        success = test_baseline_only(str(file_path))
        results.append((file_path.name, success))
    
    # Summary
    passed = sum(1 for _, success in results if success)
    print(f"\n{'='*40}")
    print(f"SUMMARY: {passed}/{len(results)} passed")
    print(f"{'='*40}")
    
    for filename, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {filename}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Test specific file
        test_baseline_only(sys.argv[1])
    else:
        # Test sample files
        sample_files = [
            "Test_data/Palmsens/Palmsens_5mM/Palmsens_5mM_CV_400mVpS_E3_scan_08.csv",
            "Test_data/Palmsens/Palmsens_5mM/Palmsens_5mM_CV_20mVpS_E1_scan_05.csv",
            "Test_data/Palmsens/Palmsens_5mM/Palmsens_5mM_CV_50mVpS_E2_scan_06.csv",
        ]
        
        print("🚀 QUICK BASELINE TEST")
        print("="*50)
        
        for file_path in sample_files:
            if os.path.exists(file_path):
                test_baseline_only(file_path)
        
        # Optional: Batch test
        batch_test_palmsens = False  # Set True to enable
        if batch_test_palmsens:
            batch_test("Test_data/Palmsens/Palmsens_5mM", max_files=5)

if __name__ == "__main__":
    main()