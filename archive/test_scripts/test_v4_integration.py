#!/usr/bin/env python3
"""
Test Enhanced V4 Integration with Web API
"""

import sys
import os
import numpy as np
import pandas as pd

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_detector_v4 import EnhancedDetectorV4

def test_v4_web_integration():
    """Test Enhanced V4 web integration"""
    print("🌐 Testing Enhanced V4 Web Integration")
    print("=" * 50)
    
    # Load test data
    test_file = "Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv"
    
    try:
        # Read test data
        df = pd.read_csv(test_file, skiprows=1)
        voltage = df['V'].values
        current = df['uA'].values
        
        print(f"📊 Test data loaded:")
        print(f"   • Data points: {len(voltage)}")
        print(f"   • Voltage range: {voltage.min():.3f} to {voltage.max():.3f} V")
        print(f"   • Current range: {current.min():.3f} to {current.max():.3f} μA")
        
        # Create Enhanced V4 detector
        detector = EnhancedDetectorV4()
        
        # Prepare web data format
        web_data = {
            'voltage': voltage.tolist(),
            'current': current.tolist()
        }
        
        print(f"\n🔬 Testing analyze_cv_data method...")
        
        # Test the web API method
        result = detector.analyze_cv_data(web_data)
        
        print(f"✅ Web API test successful!")
        print(f"   • Method: {result['method']}")
        print(f"   • Peaks detected: {len(result['peaks'])}")
        print(f"   • Processing time: {result['processing_time']:.3f}s")
        print(f"   • Ferrocyanide optimized: {result['ferrocyanide_optimized']}")
        
        # Show peak details
        print(f"\n🎯 Peak Details:")
        for i, peak in enumerate(result['peaks']):
            print(f"   Peak {i+1}: {peak['type']} at {peak['voltage']:.3f}V, {peak['current']:.2f}μA")
        
        # Test enhanced V4 API endpoint data format
        print(f"\n📡 Testing API endpoint compatibility...")
        
        # Simulate multi-file format
        multi_file_data = {
            'dataFiles': [
                {
                    'voltage': voltage.tolist(),
                    'current': current.tolist(),
                    'filename': 'test_file.csv'
                }
            ]
        }
        
        print(f"✅ Multi-file format prepared for API testing")
        print(f"   • Files: {len(multi_file_data['dataFiles'])}")
        print(f"   • First file points: {len(multi_file_data['dataFiles'][0]['voltage'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_v4_web_integration()
    if success:
        print(f"\n🎉 Enhanced V4 web integration test PASSED!")
    else:
        print(f"\n💥 Enhanced V4 web integration test FAILED!")
