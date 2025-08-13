#!/usr/bin/env python3
"""
Minimal test for AI analysis functionality
"""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, 'src')

def test_ai_imports():
    """Test basic AI analysis imports"""
    print("🧪 Testing AI Analysis Imports...")
    
    try:
        # Test service import
        from services.ai_analysis_service import create_analyzer
        print("✅ AI analysis service imported successfully")
        
        # Test route imports
        from routes.ai_analysis_routes import ai_analysis_bp, peak_detection, quality_assessment
        print("✅ AI analysis routes imported successfully")
        
        # Test app import
        from app import app
        print("✅ Flask app imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_analyzer_creation():
    """Test analyzer creation"""
    print("\n🧪 Testing Analyzer Creation...")
    
    try:
        from services.ai_analysis_service import create_analyzer
        analyzer = create_analyzer()
        print("✅ Analyzer created successfully")
        print(f"   Type: {type(analyzer).__name__}")
        return True
    except Exception as e:
        print(f"❌ Analyzer creation failed: {e}")
        return False

def test_basic_analysis():
    """Test basic analysis with dummy data"""
    print("\n🧪 Testing Basic Analysis...")
    
    try:
        import numpy as np
        from services.ai_analysis_service import create_analyzer
        
        # Create dummy DPV data
        voltages = np.linspace(-0.5, 0.5, 100)
        currents = np.random.normal(0, 1e-6, 100)  # Random noise
        
        # Add a simple peak
        peak_idx = 50
        currents[peak_idx] += 5e-6  # Add peak
        
        analyzer = create_analyzer()
        result = analyzer.analyze_measurement(voltages, currents, "DPV")
        
        print("✅ Basic analysis completed")
        print(f"   Peaks detected: {len(result.peaks)}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Quality metrics keys: {list(result.quality_metrics.keys())}")
        
        # Test JSON serialization of results
        import json
        from routes.ai_analysis_routes import convert_numpy_types
        
        # Test peak serialization
        peak_data = []
        for peak in result.peaks:
            peak_dict = {
                'potential': float(peak.voltage),
                'current': float(peak.current),
                'index': int(peak.index),
                'height': float(peak.height),
                'width': float(peak.width),
                'area': float(peak.area)
            }
            peak_data.append(peak_dict)
        
        # Test conversion of quality metrics
        quality_metrics = convert_numpy_types(result.quality_metrics)
        
        # Try to serialize everything
        test_response = {
            'peaks': peak_data,
            'quality_metrics': quality_metrics,
            'confidence_score': float(result.confidence_score)
        }
        
        json_str = json.dumps(test_response)
        print("✅ JSON serialization test passed")
        
        return True
    except Exception as e:
        print(f"❌ Basic analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_route_functions():
    """Test route functions can be called directly"""
    print("\n🧪 Testing Route Functions...")
    
    try:
        from routes.ai_analysis_routes import get_analyzer
        
        analyzer = get_analyzer()
        print("✅ get_analyzer() works")
        print(f"   Analyzer type: {type(analyzer).__name__}")
        
        return True
    except Exception as e:
        print(f"❌ Route function test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔬 PyPiPo AI Analysis Minimal Test")
    print("=" * 40)
    
    tests = [
        test_ai_imports,
        test_analyzer_creation,
        test_basic_analysis,
        test_route_functions
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! AI analysis should work correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
