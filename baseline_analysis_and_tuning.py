#!/usr/bin/env python3
"""
🔧 Enhanced Baseline Detector v2 - Parameter Tuning & Analysis
Analysis and optimization of Enhanced Baseline Detection v2
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import json
import os

from enhanced_baseline_detector_v2 import EnhancedBaselineDetector, load_cv_data
from baseline_comparison_test import traditional_baseline_correction, compare_baseline_results

def analyze_algorithm_performance():
    """🔍 Deep analysis of Enhanced Baseline v2 performance"""
    print("🔍 ENHANCED BASELINE v2 PERFORMANCE ANALYSIS")
    print("=" * 70)
    
    # Load the comparison report
    report_files = [f for f in os.listdir('.') if f.startswith('baseline_comparison_report_') and f.endswith('.json')]
    if not report_files:
        print("❌ No comparison report found! Run baseline_comparison_test.py first.")
        return
    
    latest_report = sorted(report_files)[-1]
    print(f"📊 Analyzing report: {latest_report}")
    
    with open(latest_report, 'r') as f:
        report_data = json.load(f)
    
    # Extract key findings
    print("\n🎯 KEY FINDINGS:")
    print("-" * 40)
    
    summary = report_data['summary']
    print(f"📈 Quality Improvement: {summary['average_quality_improvement']:.1%}")
    print(f"🎯 Peak Enhancement: {summary['average_peak_enhancement']:.2f}x")
    print(f"📡 SNR Improvement: {summary['average_snr_improvement']:.2f}x")
    
    # Analysis of why Enhanced v2 performed worse
    print("\n🤔 WHY ENHANCED v2 PERFORMED WORSE:")
    print("-" * 50)
    
    print("1. 📉 OVER-COMPLEXITY for simple data:")
    print("   • Traditional rolling median is very effective for smooth baselines")
    print("   • Enhanced v2 adds complexity that may not be needed for clean CV data")
    print("   • Multiple feature weighting may introduce artifacts")
    
    print("\n2. 🎛️ PARAMETER MISMATCH:")
    print("   • Current parameters optimized for noisy/complex data")
    print("   • CV data from STM32 is relatively clean")
    print("   • Need different parameter sets for different data types")
    
    print("\n3. 📊 SMOOTHNESS vs ACCURACY TRADE-OFF:")
    print("   • Enhanced v2 less smooth due to adaptive windowing")
    print("   • Traditional method prioritizes smoothness")
    print("   • Quality metric heavily weighs smoothness")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("-" * 30)
    print("1. 🎛️ PARAMETER OPTIMIZATION:")
    print("   • Increase baseline_smoothing (5 → 10)")
    print("   • Reduce peak_proximity_weight (0.3 → 0.1)")
    print("   • Increase base_window for smoother baselines")
    
    print("\n2. 📊 ADAPTIVE METHOD SELECTION:")
    print("   • Use Traditional for clean, simple CV data")
    print("   • Use Enhanced v2 for noisy, complex, or multi-peak data")
    print("   • Implement automatic method selection")
    
    print("\n3. 🧪 HYBRID APPROACH:")
    print("   • Combine Traditional smoothness with Enhanced features")
    print("   • Use Enhanced v2 for peak detection, Traditional for baseline")
    
    return report_data


def optimize_parameters():
    """🎛️ Test different parameter configurations"""
    print("\n🎛️ PARAMETER OPTIMIZATION TEST")
    print("=" * 50)
    
    # Parameter configurations to test
    configs = {
        'Original': {
            'base_window': 20,
            'peak_proximity_weight': 0.3,
            'baseline_smoothing': 5,
            'segment_min_length': 5,
            'scan_direction_adaptive': True,
            'noise_estimation_window': 10,
            'peak_distance_threshold': 15,
            'stability_threshold': 0.05,
            'confidence_threshold': 0.7,
        },
        'Smoother': {
            'base_window': 30,
            'peak_proximity_weight': 0.1,
            'baseline_smoothing': 10,
            'segment_min_length': 5,
            'scan_direction_adaptive': True,
            'noise_estimation_window': 15,
            'peak_distance_threshold': 20,
            'stability_threshold': 0.05,
            'confidence_threshold': 0.7,
        },
        'Conservative': {
            'base_window': 25,
            'peak_proximity_weight': 0.2,
            'baseline_smoothing': 8,
            'segment_min_length': 5,
            'scan_direction_adaptive': True,
            'noise_estimation_window': 12,
            'peak_distance_threshold': 18,
            'stability_threshold': 0.05,
            'confidence_threshold': 0.7,
        },
        'Aggressive': {
            'base_window': 15,
            'peak_proximity_weight': 0.5,
            'baseline_smoothing': 3,
            'segment_min_length': 3,
            'scan_direction_adaptive': True,
            'noise_estimation_window': 8,
            'peak_distance_threshold': 12,
            'stability_threshold': 0.03,
            'confidence_threshold': 0.6,
        }
    }
    
    # Test file
    test_file = "cv_data/measurement_93_100.0mVs_2025-08-25T06-39-11.686802.csv"
    if not os.path.exists(test_file):
        print("❌ Test file not found!")
        return
    
    # Load test data
    voltages, currents = load_cv_data(test_file)
    if len(voltages) == 0:
        print("❌ Could not load test data!")
        return
    
    print(f"📊 Testing with: {test_file.split('/')[-1]}")
    print(f"📈 Data points: {len(voltages)}")
    
    # Test each configuration
    results = {}
    traditional_baseline = traditional_baseline_correction(currents)
    
    for config_name, config_params in configs.items():
        print(f"\n🧪 Testing {config_name} configuration...")
        
        try:
            # Create detector with specific config
            detector = EnhancedBaselineDetector(config_params)
            
            # Run enhanced detection
            enhanced_baseline, metadata = detector.detect_baseline_enhanced(
                voltages, currents, f"{config_name}_test"
            )
            
            # Compare with traditional
            comparison = compare_baseline_results(
                currents, traditional_baseline, enhanced_baseline,
                voltages, test_file, metadata
            )
            
            results[config_name] = {
                'quality_improvement': comparison['quality_improvement'],
                'peak_enhancement': comparison['peak_enhancement_ratio'],
                'snr_improvement': comparison['snr_improvement'],
                'smoothness': comparison['enhanced_smoothness'],
                'processing_time': metadata['processing_time']
            }
            
            print(f"  Quality: {comparison['quality_improvement']:.1%}")
            print(f"  Smoothness: {comparison['enhanced_smoothness']:.3f}")
            print(f"  Peak Enhancement: {comparison['peak_enhancement_ratio']:.2f}x")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results[config_name] = None
    
    # Find best configuration
    valid_results = {k: v for k, v in results.items() if v is not None}
    if valid_results:
        best_config = max(valid_results.keys(), 
                         key=lambda k: valid_results[k]['quality_improvement'])
        
        print(f"\n🏆 BEST CONFIGURATION: {best_config}")
        print(f"📈 Quality improvement: {valid_results[best_config]['quality_improvement']:.1%}")
        
        # Create comparison visualization
        create_parameter_comparison_plot(valid_results, configs)
    
    return results


def create_parameter_comparison_plot(results: dict, configs: dict):
    """📊 Create parameter comparison visualization"""
    try:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        config_names = list(results.keys())
        
        # Plot 1: Quality Improvement
        quality_improvements = [results[name]['quality_improvement'] for name in config_names]
        ax1.bar(config_names, quality_improvements, color='skyblue', alpha=0.7)
        ax1.set_title('Quality Improvement by Configuration')
        ax1.set_ylabel('Quality Improvement (%)')
        ax1.grid(True, alpha=0.3, axis='y')
        ax1.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        
        # Add value labels
        for i, v in enumerate(quality_improvements):
            ax1.text(i, v + 0.001, f'{v:.1%}', ha='center', va='bottom')
        
        # Plot 2: Smoothness
        smoothness_values = [results[name]['smoothness'] for name in config_names]
        ax2.bar(config_names, smoothness_values, color='lightgreen', alpha=0.7)
        ax2.set_title('Baseline Smoothness by Configuration')
        ax2.set_ylabel('Smoothness Score')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Plot 3: Peak Enhancement
        peak_enhancement = [results[name]['peak_enhancement'] for name in config_names]
        ax3.bar(config_names, peak_enhancement, color='lightcoral', alpha=0.7)
        ax3.set_title('Peak Enhancement by Configuration')
        ax3.set_ylabel('Enhancement Ratio')
        ax3.grid(True, alpha=0.3, axis='y')
        ax3.axhline(y=1.0, color='red', linestyle='--', alpha=0.5)
        
        # Plot 4: Configuration Parameters
        base_windows = [configs[name]['base_window'] for name in config_names]
        smoothing = [configs[name]['baseline_smoothing'] for name in config_names]
        
        x = np.arange(len(config_names))
        width = 0.35
        
        ax4.bar(x - width/2, base_windows, width, label='Base Window', alpha=0.7)
        ax4.bar(x + width/2, smoothing, width, label='Smoothing', alpha=0.7)
        ax4.set_title('Parameter Values by Configuration')
        ax4.set_ylabel('Parameter Value')
        ax4.set_xticks(x)
        ax4.set_xticklabels(config_names)
        ax4.legend()
        ax4.grid(True, alpha=0.3, axis='y')
        
        plt.suptitle('Enhanced Baseline v2 - Parameter Optimization Results', 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        # Save plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"parameter_optimization_{timestamp}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Parameter comparison plot saved: {filename}")
        
    except Exception as e:
        print(f"⚠️ Error creating parameter comparison plot: {e}")


def create_hybrid_detector():
    """🔬 Create hybrid baseline detector"""
    print("\n🔬 CREATING HYBRID BASELINE DETECTOR")
    print("=" * 50)
    
    class HybridBaselineDetector:
        """🔄 Hybrid detector that chooses best method based on data characteristics"""
        
        def __init__(self):
            self.enhanced_detector = EnhancedBaselineDetector({
                'base_window': 30,
                'peak_proximity_weight': 0.1,
                'baseline_smoothing': 10,
                'noise_estimation_window': 15,
                'segment_min_length': 5,
                'scan_direction_adaptive': True,
                'peak_distance_threshold': 20,
                'stability_threshold': 0.05,
                'confidence_threshold': 0.7,
            })
        
        def detect_baseline(self, voltages, currents, filename="unknown"):
            """🎯 Adaptive baseline detection"""
            
            # Analyze data characteristics
            data_complexity = self._assess_data_complexity(currents)
            
            print(f"📊 Data complexity score: {data_complexity:.3f}")
            
            if data_complexity > 0.5:
                print("🚀 Using Enhanced v2 (complex data)")
                return self.enhanced_detector.detect_baseline_enhanced(voltages, currents, filename)
            else:
                print("📊 Using Traditional method (simple data)")
                traditional_baseline = traditional_baseline_correction(currents, window=25)
                metadata = {
                    'method': 'traditional',
                    'data_complexity': data_complexity,
                    'quality_metrics': {'overall_quality': 0.8}  # Assumed good quality
                }
                return traditional_baseline, metadata
        
        def _assess_data_complexity(self, currents):
            """🔍 Assess data complexity to choose appropriate method"""
            
            # Multiple complexity indicators
            factors = []
            
            # 1. Noise level
            noise_level = np.std(np.diff(currents)) / (np.std(currents) + 1e-12)
            factors.append(min(noise_level * 10, 1.0))
            
            # 2. Number of local extrema
            extrema_count = 0
            for i in range(1, len(currents) - 1):
                if ((currents[i] > currents[i-1] and currents[i] > currents[i+1]) or
                    (currents[i] < currents[i-1] and currents[i] < currents[i+1])):
                    extrema_count += 1
            
            extrema_factor = min(extrema_count / len(currents) * 50, 1.0)
            factors.append(extrema_factor)
            
            # 3. Dynamic range variation
            range_variation = (np.max(currents) - np.min(currents)) / (np.std(currents) + 1e-12)
            range_factor = min(range_variation / 10, 1.0)
            factors.append(range_factor)
            
            # Combined complexity score
            complexity = np.mean(factors)
            return complexity
    
    # Test hybrid detector
    hybrid = HybridBaselineDetector()
    
    test_files = [
        "cv_data/measurement_93_100.0mVs_2025-08-25T06-39-11.686802.csv",
        "cv_data/measurement_96_20.0mVs_2025-08-25T06-46-22.774810.csv"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n🧪 Testing hybrid on: {test_file.split('/')[-1]}")
            voltages, currents = load_cv_data(test_file)
            if len(voltages) > 0:
                baseline, metadata = hybrid.detect_baseline(voltages, currents, test_file)
                print(f"✅ Method selected: {metadata.get('method', 'enhanced')}")
    
    return hybrid


if __name__ == "__main__":
    # Run analysis
    print("🎯 ENHANCED BASELINE DETECTION v2 - COMPREHENSIVE ANALYSIS")
    print("=" * 80)
    
    # 1. Analyze current performance
    analyze_algorithm_performance()
    
    # 2. Optimize parameters
    optimize_parameters()
    
    # 3. Create hybrid detector
    create_hybrid_detector()
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("📊 Check generated plots and reports for detailed insights")
    print("💡 Consider using hybrid approach for best results")