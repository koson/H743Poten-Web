#!/usr/bin/env python3
"""
🧪 Test Enhanced Detector V5 with Real CV Data
==============================================

ทดสอบ Enhanced Detector V5 กับข้อมูล CV จริงจาก PalmSens
เพื่อตรวจสอบประสิทธิภาพก่อนใช้เป็น teacher สำหรับ DeepCV V2

Author: H743Poten Research Team
Date: October 4, 2025
"""

import sys
import os
sys.path.append('.')

import numpy as np
import pandas as pd
import glob
import time
from pathlib import Path

def load_cv_data(csv_file: str):
    """Load CV data from CSV file"""
    try:
        df = pd.read_csv(csv_file, skiprows=1)
        voltage = df.iloc[:, 0].values
        current = df.iloc[:, 1].values
        return voltage, current
    except Exception as e:
        print(f"❌ Error loading {csv_file}: {e}")
        return None, None

def test_enhanced_v5():
    """Test Enhanced Detector V5 with real data"""
    print("🧪 TESTING ENHANCED DETECTOR V5")
    print("=" * 60)
    
    # Import Enhanced V5
    try:
        from enhanced_detector_v5 import EnhancedDetectorV5
        print("✅ Successfully imported Enhanced Detector V5")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Initialize detector
    detector = EnhancedDetectorV5()
    print("✅ Enhanced Detector V5 initialized")
    
    # Find test data
    data_dirs = [
        '../Test_Data_CV/palmsense/palmsense-cv-0.5mM',
        '../Test_Data_CV/palmsense/palmsense-cv-1.0mM', 
        '../Test_Data_CV/palmsense/palmsense-cv-5.0mM'
    ]
    
    print(f"🔍 Searching for test data...")
    all_files = []
    
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
            all_files.extend(csv_files)
            print(f"   📁 {data_dir}: {len(csv_files)} files")
    
    if not all_files:
        print("❌ No test data found!")
        return False
    
    print(f"📊 Total files found: {len(all_files)}")
    
    # Test with first 15 files from each concentration
    test_files = []
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            conc_files = glob.glob(os.path.join(data_dir, '*.csv'))[:5]  # 5 from each
            test_files.extend(conc_files)
    
    print(f"🎯 Testing with {len(test_files)} files")
    print()
    
    # Test Enhanced V5
    print("🔬 Testing Enhanced Detector V5...")
    print("-" * 50)
    
    results = []
    processing_times = []
    successful_detections = 0
    
    for i, csv_file in enumerate(test_files):
        filename = os.path.basename(csv_file)
        conc = "0.5mM" if "0.5mM" in filename else "1.0mM" if "1.0mM" in filename else "5.0mM"
        
        print(f"   📄 {i+1:2d}/{len(test_files)}: {conc} - {filename[:35]:35s}", end=" ")
        
        # Load data
        voltage, current = load_cv_data(csv_file)
        if voltage is None:
            print("❌ Load failed")
            continue
        
        try:
            # Test V5 detection
            start_time = time.time()
            
            # Call V5 detect method - use the correct method name
            if hasattr(detector, 'detect_peaks_enhanced_v5'):
                result = detector.detect_peaks_enhanced_v5(voltage, current)
            elif hasattr(detector, 'detect_peaks'):
                result = detector.detect_peaks(voltage, current)
            elif hasattr(detector, 'analyze_file'):
                result = detector.analyze_file(voltage, current)
            else:
                # Fallback - just test scan direction
                scan_result = detector.detect_scan_direction_v5(voltage)
                result = {'peaks_detected': 0, 'confidence': 0.0}
            
            processing_time = time.time() - start_time
            processing_times.append(processing_time * 1000)  # ms
            
            # Extract results from V5 format
            if isinstance(result, dict):
                # V5 returns complex structure with 'peaks' list
                peaks_list = result.get('peaks', [])
                peaks_detected = len(peaks_list)
                
                # Calculate average confidence from peaks
                if peaks_list:
                    confidences = [p.get('confidence', 0.0) for p in peaks_list if 'confidence' in p]
                    confidence = np.mean(confidences) if confidences else 0.0
                else:
                    confidence = 0.0
                    
                # Also check enhanced_results for additional info
                enhanced = result.get('enhanced_results', {})
                if enhanced:
                    validation_passed = enhanced.get('validation_passed', peaks_detected)
                    peaks_detected = validation_passed  # Use validated count
            else:
                peaks_detected = 0
                confidence = 0.0
            
            results.append({
                'file': filename,
                'concentration': conc,
                'peaks_detected': peaks_detected,
                'confidence': confidence,
                'processing_time_ms': processing_time * 1000
            })
            
            if peaks_detected > 0:
                successful_detections += 1
                print(f"✅ {peaks_detected} peaks ({confidence:.1f}% conf, {processing_time*1000:.1f}ms)")
            else:
                print(f"⚠️  No peaks detected ({processing_time*1000:.1f}ms)")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    # Summary
    print()
    print("📊 ENHANCED DETECTOR V5 RESULTS")
    print("=" * 60)
    
    if results:
        total_tests = len(results)
        success_rate = successful_detections / total_tests * 100
        avg_processing_time = np.mean(processing_times)
        
        print(f"📊 Files tested: {total_tests}")
        print(f"🎯 Successful detections: {successful_detections}/{total_tests} ({success_rate:.1f}%)")
        print(f"⏱️  Average processing time: {avg_processing_time:.1f} ms")
        
        # Group by concentration
        print(f"\\n📈 Results by concentration:")
        concentrations = ['0.5mM', '1.0mM', '5.0mM']
        
        for conc in concentrations:
            conc_results = [r for r in results if r['concentration'] == conc]
            if conc_results:
                conc_success = len([r for r in conc_results if r['peaks_detected'] > 0])
                conc_total = len(conc_results)
                conc_rate = conc_success / conc_total * 100 if conc_total > 0 else 0
                avg_peaks = np.mean([r['peaks_detected'] for r in conc_results if isinstance(r['peaks_detected'], (int, float))])
                
                print(f"   {conc:>6s}: {conc_success:2d}/{conc_total} ({conc_rate:5.1f}%) - avg peaks: {avg_peaks:.1f}")
        
        # Performance assessment
        print(f"\\n🏅 PERFORMANCE ASSESSMENT:")
        if success_rate >= 80:
            print("🥇 EXCELLENT: V5 performing very well - ready for training DeepCV V2")
            status = "READY FOR TRAINING"
        elif success_rate >= 60:
            print("🥈 GOOD: V5 working well - suitable for training")
            status = "SUITABLE FOR TRAINING"
        elif success_rate >= 40:
            print("🥉 FAIR: V5 functional but may need optimization")
            status = "NEEDS OPTIMIZATION"
        else:
            print("⚠️  POOR: V5 needs significant improvement")
            status = "NEEDS IMPROVEMENT"
        
        print(f"📋 Status: {status}")
        
        return success_rate >= 40  # Consider 40%+ as acceptable for training
        
    else:
        print("❌ No successful tests!")
        return False

def inspect_v5_methods():
    """Inspect V5 methods to understand the API"""
    print("\\n🔍 INSPECTING ENHANCED DETECTOR V5 API")
    print("-" * 50)
    
    try:
        from enhanced_detector_v5 import EnhancedDetectorV5
        detector = EnhancedDetectorV5()
        
        print("📋 Available methods:")
        methods = [method for method in dir(detector) if not method.startswith('_')]
        for method in sorted(methods):
            print(f"   • {method}")
        
        # Try to find the main detection method
        if hasattr(detector, 'detect_peaks'):
            print("\\n🎯 Found detect_peaks method")
        elif hasattr(detector, 'analyze_cv'):
            print("\\n🎯 Found analyze_cv method")
        elif hasattr(detector, 'process_data'):
            print("\\n🎯 Found process_data method")
        else:
            print("\\n⚠️  No obvious detection method found")
            
    except Exception as e:
        print(f"❌ Error inspecting V5: {e}")

def main():
    """Main test function"""
    print("🧪 ENHANCED DETECTOR V5 TESTING SUITE")
    print("=" * 60)
    
    # First inspect the API
    inspect_v5_methods()
    
    # Then run tests
    success = test_enhanced_v5()
    
    print(f"\\n{'🎉 V5 TESTING COMPLETE!' if success else '❌ V5 TESTING FAILED!'}")
    
    if success:
        print("🚀 Enhanced Detector V5 is ready to be used as teacher for DeepCV V2!")
    else:
        print("🔧 Enhanced Detector V5 needs optimization before training DeepCV V2")
    
    return success

if __name__ == "__main__":
    main()