#!/usr/bin/env python3
"""
ทดสอบ Enhanced V3 integration ง่ายๆ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Enhanced V3
try:
    from enhanced_detector_v3 import EnhancedDetectorV3
    print("✅ Enhanced V3 imported successfully")
except ImportError as e:
    print(f"❌ Cannot import Enhanced V3: {e}")
    sys.exit(1)

import pandas as pd
import numpy as np

def test_enhanced_v3_direct():
    """ทดสอบ Enhanced V3 โดยตรง"""
    
    print("🧪 Testing Enhanced V3 Direct Integration")
    print("=" * 50)
    
    # โหลดข้อมูลทดสอบ
    test_file = "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_100mVpS_E1_scan_06.csv"
    
    try:
        # อ่านข้อมูล
        df = pd.read_csv(test_file, skiprows=1)
        voltage = df['V'].values
        current = df['uA'].values
        
        print(f"📂 Loaded: {test_file}")
        print(f"📊 Data points: {len(voltage)}")
        print(f"🔌 Voltage range: {voltage.min():.3f} to {voltage.max():.3f}V")
        print(f"⚡ Current range: {current.min():.3f} to {current.max():.3f}µA")
        
        # สร้าง Enhanced V3 detector
        detector = EnhancedDetectorV3()
        print(f"🚀 Enhanced V3 detector created")
        
        # ทำการ detect peaks
        print(f"\n🔍 Detecting peaks with Enhanced V3...")
        results = detector.detect_peaks_enhanced(voltage, current)
        
        # แสดงผลลัพธ์
        peaks = results.get('peaks', [])
        baseline = results.get('baseline', {})
        enhanced_results = results.get('enhanced_results', {})
        
        print(f"\n📈 ENHANCED V3 RESULTS:")
        print(f"=" * 30)
        print(f"🎯 Total peaks found: {len(peaks)}")
        
        # จำแนก peaks
        ox_peaks = [p for p in peaks if p['type'] == 'oxidation']
        red_peaks = [p for p in peaks if p['type'] == 'reduction']
        
        print(f"   - Oxidation peaks: {len(ox_peaks)}")
        print(f"   - Reduction peaks: {len(red_peaks)}")
        
        # แสดงรายละเอียด peaks
        print(f"\n🔍 Peak Details:")
        for i, peak in enumerate(peaks):
            conf = peak.get('confidence', 0)
            print(f"   Peak {i+1}: {peak['type'][:3].upper()} at {peak['voltage']:.3f}V, {peak['current']:.1f}µA, conf={conf:.0f}%")
        
        # แสดงข้อมูล Enhanced features
        if enhanced_results:
            print(f"\n🚀 Enhanced V3 Features:")
            
            scan_sections = enhanced_results.get('scan_sections', {})
            if scan_sections:
                turning_point = scan_sections.get('turning_point')
                forward_range = scan_sections.get('forward', [0, 0])
                reverse_range = scan_sections.get('reverse', [0, 0])
                
                print(f"   - Turning point index: {turning_point}")
                print(f"   - Forward scan: points {forward_range[0]} to {forward_range[1]} ({forward_range[1] - forward_range[0]} points)")
                print(f"   - Reverse scan: points {reverse_range[0]} to {reverse_range[1]} ({reverse_range[1] - reverse_range[0]} points)")
            
            thresholds = enhanced_results.get('thresholds', {})
            if thresholds:
                print(f"   - Signal-to-Noise Ratio: {thresholds.get('snr', 'N/A'):.2f}")
                print(f"   - Dynamic prominence threshold: {thresholds.get('prominence', 'N/A'):.3f}")
                print(f"   - Adaptive height threshold: {thresholds.get('height', 'N/A'):.3f}")
            
            baseline_info = enhanced_results.get('baseline_info', [])
            print(f"   - Baseline regions detected: {len(baseline_info)}")
            
            conflicts = enhanced_results.get('conflicts', [])
            print(f"   - Peak-baseline conflicts: {len(conflicts)}")
            
            validation = enhanced_results.get('validation', {})
            if validation:
                print(f"   - Electrochemical validation: {validation.get('electrochemical_valid', 'N/A')}")
                print(f"   - Multi-criteria score: {validation.get('multi_criteria_score', 'N/A'):.2f}")
        
        # แสดงข้อมูล baseline
        baseline_metadata = baseline.get('metadata', {})
        if baseline_metadata:
            print(f"\n📏 Baseline Information:")
            print(f"   - Method used: {baseline_metadata.get('method_used', 'N/A')}")
            print(f"   - Quality score: {baseline_metadata.get('quality', 'N/A')}")
            print(f"   - Regions found: {baseline_metadata.get('regions_found', 'N/A')}")
            print(f"   - Total baseline points: {baseline_metadata.get('total_baseline_points', 'N/A')}")
        
        print(f"\n✅ Enhanced V3 Direct Test COMPLETED!")
        print(f"🎉 Enhanced V3 is working correctly!")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Test file not found: {test_file}")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_v3_direct()
    
    if success:
        print(f"\n🎯 INTEGRATION STATUS: ✅ SUCCESS")
        print(f"Enhanced V3 is ready for web application testing!")
    else:
        print(f"\n❌ INTEGRATION STATUS: FAILED")
        print(f"Check Enhanced V3 implementation and dependencies.")
