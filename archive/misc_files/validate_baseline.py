#!/usr/bin/env python3
"""
Baseline Position Validator
Check if baseline segments are positioned correctly (before peaks)
"""

import sys
import os
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def validate_baseline_position(file_path):
    """Validate that baseline segments are positioned correctly"""
    from routes.peak_detection import detect_improved_baseline_2step
    
    print(f"\n🔍 Validating: {os.path.basename(file_path)}")
    
    try:
        # Load data
        df = pd.read_csv(file_path, skiprows=1)
        
        if 'A' in df.columns:
            v, i = df['V'].values, df['A'].values * 1e6  # STM32 format
            data_type = "STM32"
        elif 'uA' in df.columns:
            v, i = df['V'].values, df['uA'].values  # Palmsens format
            data_type = "Palmsens"
        else:
            print("❌ Unknown data format")
            return False
        
        print(f"📈 {data_type} | {len(v)} points")
        
        # Detect baseline
        baseline_result = detect_improved_baseline_2step(v, i)
        if baseline_result is None:
            print("❌ Baseline detection failed")
            return False
        
        bf, br, baseline_info = baseline_result
        
        # Analyze positioning
        n = len(v)
        mid_point = n // 2
        
        # Find turning point (minimum voltage)
        min_v_idx = np.argmin(v)
        
        # Get baseline segment info from logs
        forward_segment = baseline_info.get('forward_segment')
        reverse_segment = baseline_info.get('reverse_segment')
        
        validation_results = {
            'forward_position_ok': False,
            'reverse_position_ok': False,
            'forward_details': {},
            'reverse_details': {}
        }
        
        # Validate forward baseline position
        if forward_segment:
            f_start = forward_segment.get('start_idx', 0)
            f_end = forward_segment.get('end_idx', 0)
            f_start_pct = f_start / n
            f_end_pct = f_end / n
            
            # Forward baseline should be in first 40% of data
            forward_ok = f_end_pct <= 0.4
            
            validation_results['forward_position_ok'] = forward_ok
            validation_results['forward_details'] = {
                'start_idx': f_start,
                'end_idx': f_end,
                'start_percent': f_start_pct * 100,
                'end_percent': f_end_pct * 100,
                'position_status': '✅ Correct' if forward_ok else '❌ Too late'
            }
            
            print(f"📊 Forward baseline: indices [{f_start}:{f_end}] = [{f_start_pct*100:.1f}%:{f_end_pct*100:.1f}%] {validation_results['forward_details']['position_status']}")
        
        # Validate reverse baseline position  
        if reverse_segment:
            r_start = reverse_segment.get('start_idx', 0)
            r_end = reverse_segment.get('end_idx', 0)
            r_start_pct = r_start / n
            r_end_pct = r_end / n
            
            # CORRECTED: Reverse baseline should be in EARLY part of reverse scan (55-75% of data)
            # This is after turning point but before reverse redox peak
            reverse_ok = 0.55 <= r_start_pct <= 0.75
            
            validation_results['reverse_position_ok'] = reverse_ok
            validation_results['reverse_details'] = {
                'start_idx': r_start,
                'end_idx': r_end,
                'start_percent': r_start_pct * 100,
                'end_percent': r_end_pct * 100,
                'position_status': '✅ Correct' if reverse_ok else '❌ Wrong position'
            }
            
            print(f"📊 Reverse baseline: indices [{r_start}:{r_end}] = [{r_start_pct*100:.1f}%:{r_end_pct*100:.1f}%] {validation_results['reverse_details']['position_status']}")
        
        # Overall validation
        overall_ok = validation_results['forward_position_ok'] and validation_results['reverse_position_ok']
        
        print(f"🎯 Overall validation: {'✅ PASS' if overall_ok else '❌ FAIL'}")
        
        # Additional analysis: Peak detection (simple)
        print(f"📍 Data structure: Turning point at {min_v_idx} ({min_v_idx/n*100:.1f}%)")
        
        # Find approximate peak regions by looking for current extremes
        forward_current = i[:mid_point]
        reverse_current = i[mid_point:]
        
        # Find peaks as local maxima/minima
        forward_max_idx = np.argmax(np.abs(forward_current))
        reverse_max_idx = np.argmax(np.abs(reverse_current)) + mid_point
        
        print(f"📍 Approximate peaks: Forward at {forward_max_idx} ({forward_max_idx/n*100:.1f}%), Reverse at {reverse_max_idx} ({reverse_max_idx/n*100:.1f}%)")
        
        # Check if baselines are before peaks
        if forward_segment and reverse_segment:
            forward_before_peak = forward_segment['end_idx'] < forward_max_idx
            reverse_after_peak = reverse_segment['start_idx'] > reverse_max_idx
            
            print(f"🎯 Peak relationship: Forward baseline before forward peak: {'✅' if forward_before_peak else '❌'}")
            print(f"🎯 Peak relationship: Reverse baseline after reverse peak: {'✅' if reverse_after_peak else '❌'}")
        
        return overall_ok
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def batch_validate():
    """Validate multiple test files"""
    
    test_files = [
        "Test_data/Palmsens/Palmsens_5mM/Palmsens_5mM_CV_20mVpS_E1_scan_05.csv",
        "Test_data/Palmsens/Palmsens_5mM/Palmsens_5mM_CV_50mVpS_E2_scan_06.csv", 
        "Test_data/Palmsens/Palmsens_5mM/Palmsens_5mM_CV_400mVpS_E3_scan_08.csv",
        "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_20mVpS_E4_scan_05.csv",
        "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_50mVpS_E2_scan_08.csv",
        "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_100mVpS_E4_scan_05.csv",
    ]
    
    print("🔍 BASELINE POSITION VALIDATION")
    print("="*60)
    print("Checking if baselines are positioned correctly (before peaks)")
    print("="*60)
    
    results = []
    for file_path in test_files:
        if os.path.exists(file_path):
            success = validate_baseline_position(file_path)
            results.append((os.path.basename(file_path), success))
        else:
            print(f"❌ File not found: {os.path.basename(file_path)}")
            results.append((os.path.basename(file_path), False))
    
    # Summary
    passed = sum(1 for _, success in results if success)
    print(f"\n{'='*50}")
    print(f"VALIDATION SUMMARY: {passed}/{len(results)} files have correct baseline positioning")
    print(f"{'='*50}")
    
    for filename, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {filename}")
    
    return passed == len(results)

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Validate specific file
        file_path = sys.argv[1]
        validate_baseline_position(file_path)
    else:
        # Batch validation
        batch_validate()

if __name__ == "__main__":
    main()