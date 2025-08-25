#!/usr/bin/env python3
"""
Direct test of peak detection functions (no web API)
"""

import sys
import os
import numpy as np

# Add src path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from routes.peak_detection import detect_cv_peaks, load_csv_file
    print("✅ Successfully imported peak detection functions")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_direct_peak_detection():
    """Test peak detection functions directly"""
    
    # Load a test file
    test_file = "./Test_data/Palmsens/Palmsens_1.0mM/Palmsens_1.0mM_CV_100mVpS_E1_scan_05.csv"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"🔬 Testing direct peak detection on: {os.path.basename(test_file)}")
    
    try:
        # Load file using the same function as the web API
        result = load_csv_file(test_file)
        
        if not result.get('success'):
            print(f"❌ Failed to load file: {result.get('error')}")
            return
        
        data = result['data']
        voltage = np.array(data['voltage'])
        current = np.array(data['current'])
        
        print(f"✅ Loaded {len(voltage)} data points")
        print(f"📊 Voltage range: {voltage.min():.3f}V to {voltage.max():.3f}V")
        print(f"⚡ Current range: {current.min():.3f}µA to {current.max():.3f}µA")
        
        # Test different methods
        methods = ['prominence', 'ml', 'derivative']
        
        for method in methods:
            print(f"\n🔬 Testing method: {method}")
            
            try:
                result = detect_cv_peaks(voltage, current, method=method)
                peaks = result.get('peaks', [])
                
                print(f"✅ {method}: Found {len(peaks)} peaks")
                
                # Show peak details
                for i, peak in enumerate(peaks[:3]):  # Show first 3 peaks
                    print(f"   Peak {i+1}: {peak.get('voltage', 'N/A'):.3f}V, {peak.get('current', 'N/A'):.3f}µA, type={peak.get('type', 'N/A')}, confidence={peak.get('confidence', 'N/A'):.1f}%")
                
                # Check baseline data
                baseline = result.get('baseline', {})
                if baseline:
                    print(f"   Baseline: keys={list(baseline.keys())}")
                    if 'full' in baseline:
                        print(f"   Baseline full length: {len(baseline['full'])}")
                else:
                    print("   ⚠️ No baseline data")
                    
            except Exception as e:
                print(f"❌ {method}: Error - {e}")
                import traceback
                traceback.print_exc()
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing Direct Peak Detection Functions")
    test_direct_peak_detection()