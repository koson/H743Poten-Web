#!/usr/bin/env python3
"""
AI Demo - Demonstrate working AI functionality without complex imports
"""

import numpy as np
import pandas as pd
from pathlib import Path
import os

def load_and_analyze_cv_data():
    """Load CV data and perform basic analysis"""
    print("🔍 Loading CV Sample Data")
    print("=" * 30)
    
    try:
        # Load data
        csv_path = "sample_data/cv_sample.csv"
        data = pd.read_csv(csv_path)
        
        voltage = data['voltage'].values
        current = data['current'].values
        time = data['time'].values
        
        print(f"✅ Data loaded: {len(data)} points")
        print(f"   Time range: {time.min():.1f} - {time.max():.1f} s")
        print(f"   Voltage range: {voltage.min():.3f} - {voltage.max():.3f} V")
        print(f"   Current range: {current.min()*1e9:.1f} - {current.max()*1e9:.1f} nA")
        
        return voltage, current, time
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None, None, None

def basic_signal_analysis(voltage, current):
    """Perform basic signal analysis without ML"""
    print(f"\n📊 Basic Signal Analysis")
    print("=" * 30)
    
    try:
        # Signal statistics
        current_rms = np.sqrt(np.mean(current**2))
        current_std = np.std(current)
        voltage_range = np.ptp(voltage)
        
        print(f"Signal Statistics:")
        print(f"   RMS current: {current_rms*1e12:.1f} pA")
        print(f"   Current std: {current_std*1e12:.1f} pA")
        print(f"   Voltage range: {voltage_range:.3f} V")
        
        # Simple peak detection using gradient
        gradient = np.gradient(current)
        
        # Find zero crossings in gradient (peaks)
        peaks = []
        for i in range(1, len(gradient)-1):
            if gradient[i-1] > 0 and gradient[i+1] < 0:  # Local maximum
                if abs(current[i]) > 2 * current_std:  # Significant peak
                    peaks.append({
                        'index': i,
                        'voltage': voltage[i],
                        'current': current[i],
                        'type': 'oxidation' if current[i] > 0 else 'reduction'
                    })
        
        print(f"\nPeak Detection:")
        print(f"   Peaks found: {len(peaks)}")
        
        for i, peak in enumerate(peaks, 1):
            print(f"   Peak {i}: {peak['voltage']:.3f} V, {peak['current']*1e9:.1f} nA ({peak['type']})")
        
        # Simple quality assessment
        if len(peaks) > 0:
            peak_current = max(abs(p['current']) for p in peaks)
            snr_estimate = peak_current / current_std if current_std > 0 else 0
            quality_score = min(1.0, snr_estimate / 10)  # Normalize to 0-1
        else:
            snr_estimate = 0
            quality_score = 0
        
        print(f"\nQuality Assessment:")
        print(f"   Estimated SNR: {snr_estimate:.1f}")
        print(f"   Quality score: {quality_score:.2f}/1.0")
        
        return {
            'peaks': peaks,
            'quality_score': quality_score,
            'snr_estimate': snr_estimate,
            'statistics': {
                'rms_current': current_rms,
                'std_current': current_std,
                'voltage_range': voltage_range
            }
        }
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return None

def generate_ai_insights(analysis_result):
    """Generate AI-like insights from analysis"""
    print(f"\n💡 AI Insights")
    print("=" * 20)
    
    if not analysis_result:
        print("   No analysis data available")
        return
    
    peaks = analysis_result['peaks']
    quality = analysis_result['quality_score']
    
    insights = []
    
    # Peak insights
    if len(peaks) == 0:
        insights.append("No significant electrochemical peaks detected")
        insights.append("Consider: increasing analyte concentration or expanding potential window")
    elif len(peaks) == 1:
        insights.append("Single redox process detected")
        insights.append("Suggest: repeat measurement for reproducibility verification")
    elif len(peaks) == 2:
        # Check for reversible couple
        oxidation_peaks = [p for p in peaks if p['type'] == 'oxidation']
        reduction_peaks = [p for p in peaks if p['type'] == 'reduction']
        
        if len(oxidation_peaks) == 1 and len(reduction_peaks) == 1:
            delta_e = abs(oxidation_peaks[0]['voltage'] - reduction_peaks[0]['voltage'])
            if delta_e < 0.1:  # Less than 100 mV separation
                insights.append(f"Potential reversible redox couple detected (ΔE = {delta_e*1000:.0f} mV)")
                insights.append("Suggest: scan rate studies for kinetic characterization")
            else:
                insights.append("Two distinct redox processes detected")
        else:
            insights.append("Multiple redox processes detected")
    else:
        insights.append(f"Complex electrochemical system with {len(peaks)} peaks")
        insights.append("Suggest: check for interferences or multiple analytes")
    
    # Quality insights
    if quality > 0.8:
        insights.append("Excellent signal quality - suitable for quantitative analysis")
    elif quality > 0.5:
        insights.append("Good signal quality - minor improvements recommended")
    else:
        insights.append("Poor signal quality - optimization needed before analysis")
        insights.append("Consider: electrode cleaning, electrolyte purification, or shielding")
    
    # Display insights
    for i, insight in enumerate(insights, 1):
        print(f"   {i}. {insight}")

def demonstrate_ai_capabilities():
    """Demonstrate the AI system capabilities"""
    print("🚀 AI Capabilities Demonstration")
    print("=" * 40)
    
    # Real data analysis
    voltage, current, time = load_and_analyze_cv_data()
    
    if voltage is not None:
        analysis = basic_signal_analysis(voltage, current)
        generate_ai_insights(analysis)
    
    # Synthetic data for comparison
    print(f"\n🧪 Synthetic Data Comparison")
    print("=" * 35)
    
    # Generate dopamine-like CV
    v_synth = np.linspace(-0.5, 0.5, 1000)
    i_synth = (
        3e-6 * np.exp(-((v_synth - 0.15) / 0.03) ** 2) -      # Oxidation peak
        2.5e-6 * np.exp(-((v_synth - 0.09) / 0.03) ** 2) +    # Reduction peak
        np.random.normal(0, 1e-7, len(v_synth))               # Noise
    )
    
    print("Generated synthetic dopamine CV:")
    print(f"   Oxidation peak: ~0.15 V, {np.max(i_synth)*1e6:.1f} μA")
    print(f"   Reduction peak: ~0.09 V, {abs(np.min(i_synth))*1e6:.1f} μA")
    
    synth_analysis = basic_signal_analysis(v_synth, i_synth)
    generate_ai_insights(synth_analysis)

def main():
    """Main demo function"""
    print("🔬 H743Poten AI System Demo")
    print("=" * 35)
    print("Demonstrating AI capabilities without complex ML dependencies")
    print()
    
    try:
        demonstrate_ai_capabilities()
        
        print(f"\n🎉 AI Demo Complete!")
        print(f"This demonstrates the intelligence capabilities that will be")
        print(f"enhanced with full ML integration.")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

if __name__ == "__main__":
    main()
