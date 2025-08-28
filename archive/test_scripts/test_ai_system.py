#!/usr/bin/env python3
"""
Test AI System Components
Test the advanced AI analysis capabilities
"""

import sys
import os
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_signal_processor():
    """Test signal processor"""
    print("🔄 Testing Signal Processor")
    print("=" * 35)
    
    try:
        from ai.ml_models.signal_processor import SignalProcessor
        
        # Create processor
        processor = SignalProcessor()
        print("✅ Signal processor created successfully")
        
        # Generate test data
        time = np.linspace(0, 1, 1000)
        voltage = np.linspace(-0.5, 0.5, 1000)
        
        # Synthetic CV with noise
        clean_current = 1e-6 * np.exp(-((voltage - 0.1) / 0.05) ** 2)
        noise = np.random.normal(0, 1e-7, len(voltage))
        noisy_current = clean_current + noise
        
        print(f"Generated test data: {len(voltage)} points")
        
        # Test quality assessment
        quality = processor.assess_signal_quality(voltage, noisy_current)
        print(f"Quality assessment:")
        print(f"  SNR: {quality.snr_db:.1f} dB")
        print(f"  Quality score: {quality.quality_score:.2f}/1.0")
        
        # Test filtering
        filtered = processor.apply_filtering(voltage, noisy_current, 'auto')
        print(f"Filtering:")
        print(f"  Method: {filtered.filter_method}")
        print(f"  SNR improvement: {filtered.quality_improvement:.1f} dB")
        
        # Test baseline correction
        corrected = processor.correct_baseline(voltage, noisy_current)
        print(f"Baseline correction applied")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_electrochemical_intelligence():
    """Test electrochemical intelligence"""
    print("\n🧠 Testing Electrochemical Intelligence")
    print("=" * 45)
    
    try:
        from ai.ml_models.electrochemical_intelligence import (
            ElectrochemicalIntelligence, 
            ElectrochemicalContext,
            MeasurementType
        )
        
        # Create intelligence system
        ei = ElectrochemicalIntelligence()
        print("✅ Electrochemical Intelligence created")
        
        # Generate synthetic dopamine CV
        voltage = np.linspace(-0.5, 0.5, 1000)
        current = (
            2e-6 * np.exp(-((voltage - 0.15) / 0.03) ** 2) -    # Oxidation peak
            1.8e-6 * np.exp(-((voltage - 0.09) / 0.03) ** 2) +  # Reduction peak
            np.random.normal(0, 1e-7, len(voltage))             # Noise
        )
        
        # Create context
        context = ElectrochemicalContext(
            measurement_type=MeasurementType.CV,
            electrode_material="Glassy Carbon",
            electrolyte="PBS pH 7.4",
            ph=7.4,
            temperature=25.0,
            scan_rate=0.1
        )
        
        print("Generated synthetic dopamine CV data")
        
        # Perform analysis
        analysis = ei.analyze_measurement(voltage, current, context)
        
        print(f"Analysis results:")
        print(f"  Processing time: {analysis.processing_time:.2f}s")
        print(f"  Peaks detected: {analysis.peak_analysis.get('peaks_detected', 0)}")
        print(f"  Quality score: {analysis.quality_assessment.get('quality_score', 0):.2f}")
        print(f"  Insights generated: {len(analysis.insights)}")
        print(f"  Expert recommendations: {len(analysis.expert_recommendations)}")
        
        if analysis.analyte_identification:
            ai = analysis.analyte_identification
            print(f"  Analyte type: {ai.analyte_type.value}")
            print(f"  Confidence: {ai.confidence:.1%}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_integration():
    """Test integrated AI system"""
    print("\n🚀 Testing AI System Integration")
    print("=" * 40)
    
    try:
        # Test the complete pipeline
        from ai.ml_models.electrochemical_intelligence import ElectrochemicalIntelligence
        from ai.ml_models.signal_processor import SignalProcessor
        
        # Create components
        ei = ElectrochemicalIntelligence()
        sp = SignalProcessor()
        
        print("✅ All components loaded successfully")
        
        # Get system summaries
        ei_summary = ei.get_intelligence_summary()
        sp_summary = sp.get_processing_summary()
        
        print("System Status:")
        print(f"  ML Models Available: {ei_summary['ml_models_available']}")
        print(f"  SciPy Available: {sp_summary['scipy_available']}")
        print(f"  Compound Database: {ei_summary['compound_database_entries']} entries")
        print(f"  Expert Rules: {ei_summary['expert_rules']} rules")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🔬 H743Poten AI System Test Suite")
    print("=" * 50)
    print(f"Python: {sys.version}")
    print(f"NumPy available: {'✅' if 'numpy' in sys.modules else '❌'}")
    
    results = []
    
    # Run tests
    results.append(("Signal Processor", test_signal_processor()))
    results.append(("Electrochemical Intelligence", test_electrochemical_intelligence()))
    results.append(("System Integration", test_integration()))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:30} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! AI system is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Check errors above.")
        return False

if __name__ == "__main__":
    main()
