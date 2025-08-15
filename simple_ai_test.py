#!/usr/bin/env python3
"""
Simple AI Test - Quick verification of AI system functionality
"""

import sys
import os
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_imports():
    """Test basic imports"""
    print("🔍 Testing Basic Imports...")
    
    try:
        import numpy as np
        print("   ✅ NumPy imported")
        
        import scipy
        print("   ✅ SciPy imported")
        
        import pandas as pd
        print("   ✅ Pandas imported")
        
        from ai.ml_models.signal_processor import SignalProcessor
        print("   ✅ SignalProcessor imported")
        
        from ai.ml_models.electrochemical_intelligence import ElectrochemicalIntelligence
        print("   ✅ ElectrochemicalIntelligence imported")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False

def test_signal_processor_basic():
    """Test basic signal processor functionality"""
    print("\n🔧 Testing Signal Processor...")
    
    try:
        from ai.ml_models.signal_processor import SignalProcessor
        
        processor = SignalProcessor()
        print("   ✅ SignalProcessor created")
        
        # Simple test data
        voltage = np.linspace(-1, 1, 100)
        current = np.sin(voltage * np.pi) * 1e-6 + np.random.normal(0, 1e-7, 100)
        
        # Test quality assessment
        quality = processor.assess_signal_quality(voltage, current)
        print(f"   ✅ Quality assessment: score {quality.quality_score:.2f}")
        
        # Test filtering
        filtered = processor.apply_filtering(voltage, current, 'lowpass')
        print(f"   ✅ Filtering: {filtered.filter_method} applied")
        
        return True
        
    except Exception as e:
        print(f"   ❌ SignalProcessor test failed: {e}")
        return False

def test_ai_basic():
    """Test basic AI functionality"""  
    print("\n🧠 Testing AI System...")
    
    try:
        from ai.ml_models.electrochemical_intelligence import (
            ElectrochemicalIntelligence,
            ElectrochemicalContext,
            MeasurementType
        )
        
        ei = ElectrochemicalIntelligence()
        print("   ✅ ElectrochemicalIntelligence created")
        
        # Simple test data - dopamine-like CV
        voltage = np.linspace(-0.5, 0.5, 200)
        current = (2e-6 * np.exp(-((voltage - 0.15) / 0.03) ** 2) - 
                  1.5e-6 * np.exp(-((voltage - 0.09) / 0.03) ** 2) +
                  np.random.normal(0, 1e-7, 200))
        
        context = ElectrochemicalContext(
            measurement_type=MeasurementType.CV,
            electrode_material="Glassy Carbon",
            electrolyte="PBS",
            scan_rate=0.1
        )
        
        analysis = ei.analyze_measurement(voltage, current, context)
        print(f"   ✅ AI Analysis completed in {analysis.processing_time:.3f}s")
        print(f"   📊 Results: {analysis.peak_analysis.get('peaks_detected', 0)} peaks detected")
        
        return True
        
    except Exception as e:
        print(f"   ❌ AI system test failed: {e}")
        return False

def test_real_data_load():
    """Test loading real CV data"""
    print("\n📁 Testing Real Data Loading...")
    
    try:
        import pandas as pd
        
        csv_path = "sample_data/cv_sample.csv"
        if os.path.exists(csv_path):
            data = pd.read_csv(csv_path)
            print(f"   ✅ Loaded {len(data)} data points")
            print(f"   📊 Columns: {list(data.columns)}")
            print(f"   🔍 Voltage range: {data['voltage'].min():.3f} to {data['voltage'].max():.3f} V")
            print(f"   ⚡ Current range: {data['current'].min()*1e9:.1f} to {data['current'].max()*1e9:.1f} nA")
            return True
        else:
            print(f"   ❌ CV sample file not found: {csv_path}")
            return False
            
    except Exception as e:
        print(f"   ❌ Real data loading failed: {e}")
        return False

def main():
    """Main test function"""
    print("⚡ Simple AI System Test")
    print("=" * 30)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Signal Processor", test_signal_processor_basic), 
        ("AI System", test_ai_basic),
        ("Real Data Loading", test_real_data_load)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 20)
    
    passed = 0
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResult: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! AI system is working!")
    else:
        print("⚠️  Some tests failed - check errors above")
    
    return passed == len(results)

if __name__ == "__main__":
    main()
