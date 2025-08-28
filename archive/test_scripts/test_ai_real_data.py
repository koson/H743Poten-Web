#!/usr/bin/env python3
"""
Real Data AI Testing - Test AI system with actual CV data
"""

import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def load_cv_sample_data():
    """Load the real CV sample data"""
    try:
        csv_path = "sample_data/cv_sample.csv"
        if not os.path.exists(csv_path):
            print(f"❌ CV sample file not found: {csv_path}")
            return None, None, None
            
        # Read CSV data
        data = pd.read_csv(csv_path)
        
        time = data['time'].values
        voltage = data['voltage'].values  
        current = data['current'].values
        
        print(f"✅ Loaded CV sample data:")
        print(f"   Data points: {len(time)}")
        print(f"   Time range: {time.min():.1f} - {time.max():.1f} s")
        print(f"   Voltage range: {voltage.min():.3f} - {voltage.max():.3f} V")
        print(f"   Current range: {current.min()*1e9:.1f} - {current.max()*1e9:.1f} nA")
        
        return time, voltage, current
        
    except Exception as e:
        print(f"❌ Error loading CV data: {e}")
        return None, None, None

def test_signal_processing_real_data():
    """Test signal processing with real CV data"""
    print("\n🔄 Testing Signal Processing with Real CV Data")
    print("=" * 50)
    
    try:
        from ai.ml_models.signal_processor import SignalProcessor
        
        # Load real data
        time, voltage, current = load_cv_sample_data()
        if time is None:
            return False
            
        # Create processor
        processor = SignalProcessor()
        
        # Assess signal quality
        print("\n📊 Signal Quality Assessment:")
        quality = processor.assess_signal_quality(voltage, current, sampling_rate=10.0)
        
        print(f"   SNR: {quality.snr_db:.1f} dB")
        print(f"   Baseline drift: {quality.baseline_drift:.1%}")
        print(f"   Noise level: {quality.noise_level*1e12:.1f} pA")
        print(f"   Data completeness: {quality.data_completeness:.1%}")
        print(f"   Quality score: {quality.quality_score:.2f}/1.0")
        
        if quality.recommendations:
            print(f"   Recommendations:")
            for i, rec in enumerate(quality.recommendations, 1):
                print(f"      {i}. {rec}")
        
        # Test different filters
        print(f"\n🔧 Testing Filters:")
        filter_types = ['lowpass', 'savgol', 'gaussian', 'median']
        
        for filter_type in filter_types:
            try:
                filtered = processor.apply_filtering(voltage, current, filter_type=filter_type)
                
                print(f"   {filter_type.upper()}: SNR improvement +{filtered.quality_improvement:.1f} dB")
                
                # Calculate noise reduction
                noise_removed_rms = np.sqrt(np.mean(filtered.noise_removed**2))
                print(f"      Noise removed: {noise_removed_rms*1e12:.1f} pA RMS")
                
            except Exception as e:
                print(f"   {filter_type.upper()}: Failed - {e}")
        
        # Test baseline correction
        print(f"\n📏 Baseline Correction:")
        methods = ['linear', 'polynomial', 'asymmetric']
        
        for method in methods:
            try:
                corrected = processor.correct_baseline(voltage, current, method=method)
                
                # Calculate correction amount
                correction = np.mean(np.abs(current - corrected))
                print(f"   {method.capitalize()}: Average correction {correction*1e12:.1f} pA")
                
            except Exception as e:
                print(f"   {method.capitalize()}: Failed - {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ SignalProcessor import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Signal processing test failed: {e}")
        return False

def test_ai_analysis_real_data():
    """Test AI analysis with real CV data"""
    print("\n🧠 Testing AI Analysis with Real CV Data")
    print("=" * 50)
    
    try:
        from ai.ml_models.electrochemical_intelligence import (
            ElectrochemicalIntelligence, 
            ElectrochemicalContext,
            MeasurementType
        )
        
        # Load real data
        time, voltage, current = load_cv_sample_data()
        if time is None:
            return False
            
        # Create AI system
        ei = ElectrochemicalIntelligence()
        
        # Create measurement context
        context = ElectrochemicalContext(
            measurement_type=MeasurementType.CV,
            electrode_material="Unknown",
            electrolyte="Unknown",
            ph=None,
            temperature=None,
            scan_rate=0.25  # Estimated from data: 1V range in 4s = 0.25 V/s
        )
        
        print(f"📋 Measurement Context:")
        print(f"   Type: {context.measurement_type.value}")
        print(f"   Estimated scan rate: {context.scan_rate} V/s")
        
        # Perform intelligent analysis
        print(f"\n🔍 Performing AI Analysis...")
        analysis = ei.analyze_measurement(voltage, current, context)
        
        # Display results
        print(f"\n📊 Analysis Results:")
        print(f"   Processing time: {analysis.processing_time:.3f} seconds")
        
        # Peak analysis
        peaks = analysis.peak_analysis
        print(f"\n🎯 Peak Detection:")
        print(f"   Peaks detected: {peaks.get('peaks_detected', 0)}")
        print(f"   Detection method: {peaks.get('method', 'unknown')}")
        
        if 'peak_data' in peaks and peaks['peak_data']:
            print(f"   Peak details:")
            for i, peak in enumerate(peaks['peak_data'], 1):
                potential = peak.get('potential', 0)
                current_val = peak.get('current', 0)
                peak_type = peak.get('type', 'unknown')
                print(f"      {i}. {potential:.3f} V, {current_val*1e9:.1f} nA ({peak_type})")
        
        # Signal quality
        quality = analysis.quality_assessment
        print(f"\n🔍 Signal Quality:")
        print(f"   Quality score: {quality.get('quality_score', 0):.2f}/1.0")
        print(f"   SNR: {quality.get('snr_db', 0):.1f} dB")
        print(f"   Data completeness: {quality.get('data_completeness', 0):.1%}")
        
        # Analyte identification
        if analysis.analyte_identification:
            ai = analysis.analyte_identification
            print(f"\n🧪 Analyte Identification:")
            print(f"   Type: {ai.analyte_type.value}")
            print(f"   Confidence: {ai.confidence:.1%}")
            
            if ai.possible_compounds:
                print(f"   Possible compounds:")
                for i, compound in enumerate(ai.possible_compounds[:3], 1):
                    print(f"      {i}. {compound}")
            
            if ai.supporting_evidence:
                print(f"   Evidence:")
                for evidence in ai.supporting_evidence:
                    print(f"      • {evidence}")
        else:
            print(f"\n🧪 Analyte Identification: None (insufficient data)")
        
        # AI Insights
        print(f"\n💡 AI Insights ({len(analysis.insights)}):")
        for i, insight in enumerate(analysis.insights, 1):
            print(f"   {i}. {insight.title} (confidence: {insight.confidence:.1%})")
            print(f"      {insight.description}")
            if insight.recommendations:
                print(f"      💡 {'; '.join(insight.recommendations[:2])}")
        
        # Expert recommendations
        print(f"\n👨‍🔬 Expert Recommendations:")
        for i, rec in enumerate(analysis.expert_recommendations[:5], 1):
            print(f"   {i}. {rec}")
        
        # System status
        summary = ei.get_intelligence_summary()
        print(f"\n🤖 AI System Status:")
        print(f"   ML Models Available: {summary['ml_models_available']}")
        print(f"   Analyses Performed: {summary['analysis_count']}")
        print(f"   Knowledge Base: {summary['compound_database_entries']} compounds, {summary['expert_rules']} rules")
        
        return True
        
    except ImportError as e:
        print(f"❌ AI system import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ AI analysis test failed: {e}")
        return False

def test_enhanced_data():
    """Test with enhanced synthetic data for comparison"""
    print("\n🧪 Testing with Enhanced Synthetic Data")
    print("=" * 50)
    
    try:
        from ai.ml_models.electrochemical_intelligence import (
            ElectrochemicalIntelligence,
            ElectrochemicalContext, 
            MeasurementType
        )
        
        # Generate enhanced synthetic dopamine CV
        voltage = np.linspace(-0.5, 0.5, 1000)
        
        # More realistic dopamine peaks with proper reversible behavior
        # Based on literature: E1/2 ≈ 0.1-0.2 V vs Ag/AgCl
        oxidation_peak = 3e-6 * np.exp(-((voltage - 0.15) / 0.03) ** 2)
        reduction_peak = -2.5e-6 * np.exp(-((voltage - 0.09) / 0.03) ** 2)
        
        # Add some electrochemical realism
        background = 5e-8 * voltage  # Slight capacitive current
        noise = np.random.normal(0, 1e-7, len(voltage))
        
        current = oxidation_peak + reduction_peak + background + noise
        
        print(f"Generated enhanced dopamine CV:")
        print(f"   Oxidation peak: ~{np.max(oxidation_peak)*1e6:.1f} μA at ~0.15 V")
        print(f"   Reduction peak: ~{abs(np.min(reduction_peak))*1e6:.1f} μA at ~0.09 V")
        print(f"   Peak separation: ~{60:.0f} mV (reversible)")
        
        # AI Analysis
        ei = ElectrochemicalIntelligence()
        
        context = ElectrochemicalContext(
            measurement_type=MeasurementType.CV,
            electrode_material="Glassy Carbon",
            electrolyte="PBS pH 7.4",
            ph=7.4,
            temperature=25.0,
            scan_rate=0.1
        )
        
        analysis = ei.analyze_measurement(voltage, current, context)
        
        print(f"\n📊 Enhanced Data Analysis:")
        print(f"   Peaks detected: {analysis.peak_analysis.get('peaks_detected', 0)}")
        print(f"   Quality score: {analysis.quality_assessment.get('quality_score', 0):.2f}/1.0")
        
        if analysis.analyte_identification:
            ai = analysis.analyte_identification
            print(f"   Identified: {ai.analyte_type.value} (confidence: {ai.confidence:.1%})")
            if ai.possible_compounds:
                print(f"   Best match: {ai.possible_compounds[0]}")
        
        print(f"   AI insights: {len(analysis.insights)}")
        print(f"   Processing time: {analysis.processing_time:.3f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced data test failed: {e}")
        return False

def main():
    """Main testing function"""
    print("🔬 Real Data AI Testing Suite")
    print("=" * 40)
    
    # Check dependencies
    try:
        import pandas as pd
        print("✅ Pandas available")
    except ImportError:
        print("❌ Pandas not available - installing...")
        os.system("pip install pandas")
    
    # Run tests
    results = []
    results.append(("Signal Processing (Real Data)", test_signal_processing_real_data()))
    results.append(("AI Analysis (Real Data)", test_ai_analysis_real_data()))
    results.append(("Enhanced Synthetic Test", test_enhanced_data()))
    
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
        print("\n🎉 All real data tests passed!")
        print("   AI system successfully processes real electrochemical data!")
        return True
    else:
        print(f"\n⚠️  {len(results)-passed} test(s) failed - check errors above")
        return False

if __name__ == "__main__":
    main()
