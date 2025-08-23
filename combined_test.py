#!/usr/bin/env python3
"""
Combined Test Script - Both Palmsens and STM32
Quick validation of baseline detection across different instrument formats
"""

import sys
import os
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_baseline(file_path, instrument_type="auto"):
    """Test baseline detection with format detection"""
    from routes.peak_detection import detect_improved_baseline_2step
    
    print(f"\n📁 {os.path.basename(file_path)}")
    
    try:
        # Load data with auto-detection
        df = pd.read_csv(file_path, skiprows=1)
        
        if 'A' in df.columns:
            v, i = df['V'].values, df['A'].values * 1e6  # STM32 format
            unit = "µA (STM32)"
            data_type = "STM32"
        elif 'uA' in df.columns:
            v, i = df['V'].values, df['uA'].values  # Palmsens format
            unit = "µA (Palmsens)"
            data_type = "Palmsens"
        else:
            print("❌ Unknown data format")
            return False
        
        print(f"📊 {data_type} | {len(v)} points, V:[{v.min():.3f},{v.max():.3f}], I:[{i.min():.1f},{i.max():.1f}]{unit}")
        
        # Test baseline detection
        result = detect_improved_baseline_2step(v, i)
        
        if result is None:
            print("❌ Baseline detection FAILED")
            return False
        
        bf, br, info = result
        
        # Stats
        print(f"✅ Forward: {len(bf)} points, range=[{bf.min():.1f}, {bf.max():.1f}]µA, mean={bf.mean():.1f}µA")
        print(f"✅ Reverse: {len(br)} points, range=[{br.min():.1f}, {br.max():.1f}]µA, mean={br.mean():.1f}µA")
        
        # Quality assessment (adjusted for instrument type)
        forward_span = bf.max() - bf.min()
        reverse_span = br.max() - br.min()
        data_span = i.max() - i.min()
        
        # Different thresholds for different instruments
        if data_type == "Palmsens":
            # Palmsens data is usually cleaner
            forward_quality = "🟢" if forward_span < data_span * 0.1 else "🟡" if forward_span < data_span * 0.2 else "🔴"
            reverse_quality = "🟢" if reverse_span < data_span * 0.1 else "🟡" if reverse_span < data_span * 0.2 else "🔴"
        else:
            # STM32 data can be noisier
            forward_quality = "🟢" if forward_span < data_span * 0.15 else "🟡" if forward_span < data_span * 0.3 else "🔴"
            reverse_quality = "🟢" if reverse_span < data_span * 0.15 else "🟡" if reverse_span < data_span * 0.3 else "🔴"
        
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

def run_comprehensive_test():
    """Run tests on both instrument types"""
    
    # Test files for both instruments
    test_files = [
        # Palmsens files (clean data)
        "Test_data/Palmsens/Palmsens_5mM/Palmsens_5mM_CV_20mVpS_E1_scan_05.csv",
        "Test_data/Palmsens/Palmsens_5mM/Palmsens_5mM_CV_50mVpS_E2_scan_06.csv",
        "Test_data/Palmsens/Palmsens_5mM/Palmsens_5mM_CV_400mVpS_E3_scan_08.csv",
        
        # STM32 files (noisier data)
        "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_20mVpS_E4_scan_05.csv",
        "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_50mVpS_E2_scan_08.csv",
        "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_100mVpS_E4_scan_05.csv",
    ]
    
    print("🔬 COMPREHENSIVE BASELINE TEST")
    print("="*60)
    print("Testing baseline detection across Palmsens and STM32 formats")
    print("="*60)
    
    results = []
    for file_path in test_files:
        if os.path.exists(file_path):
            success = test_baseline(file_path)
            results.append((os.path.basename(file_path), success))
        else:
            print(f"❌ File not found: {os.path.basename(file_path)}")
            results.append((os.path.basename(file_path), False))
    
    # Summary
    passed = sum(1 for _, success in results if success)
    print(f"\n{'='*50}")
    print(f"SUMMARY: {passed}/{len(results)} files processed successfully")
    print(f"{'='*50}")
    
    for filename, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {filename}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Test specific file
        test_baseline(sys.argv[1])
    else:
        # Run comprehensive test
        run_comprehensive_test()

if __name__ == "__main__":
    main()