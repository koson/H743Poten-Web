#!/usr/bin/env python3
"""
STM32 Baseline Test Script
Test baseline detection on STM32 format data
"""

import sys
import os
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_stm32_baseline(file_path):
    """Test baseline detection on STM32 data"""
    from routes.peak_detection import detect_improved_baseline_2step
    
    print(f"\n📁 {os.path.basename(file_path)}")
    
    try:
        # Load STM32 data
        df = pd.read_csv(file_path, skiprows=1)
        if 'A' in df.columns:
            v, i = df['V'].values, df['A'].values * 1e6  # Convert A to µA
            unit = "µA (from A)"
        elif 'uA' in df.columns:
            v, i = df['V'].values, df['uA'].values
            unit = "µA"
        else:
            print("❌ Unknown data format")
            return False
        
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
        
        # Quality metrics (more lenient for noisy STM32 data)
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

def main():
    """Main function for STM32 testing"""
    # STM32 test files (5.0mM concentration)
    stm32_files = [
        "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_50mVpS_E2_scan_08.csv",
        "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_100mVpS_E4_scan_05.csv",
        "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_200mVpS_E4_scan_05.csv",
        "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_20mVpS_E4_scan_05.csv",
    ]
    
    print("🔬 STM32 BASELINE TEST")
    print("="*50)
    
    for file_path in stm32_files:
        if os.path.exists(file_path):
            test_stm32_baseline(file_path)
        else:
            print(f"❌ File not found: {os.path.basename(file_path)}")

if __name__ == "__main__":
    main()