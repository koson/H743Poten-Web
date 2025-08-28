#!/usr/bin/env python3
"""
🔬 Baseline Detection Comparison Test
Compare Enhanced Baseline v2 with Traditional Method
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from datetime import datetime
import json
import os

# Import Enhanced Detector v2
from enhanced_baseline_detector_v2 import EnhancedBaselineDetector, load_cv_data

def compare_baseline_methods():
    """🔬 Compare Enhanced Baseline v2 with Traditional Method"""
    print("🔬 BASELINE DETECTION COMPARISON TEST")
    print("=" * 70)
    
    # Find test files
    potential_files = [
        "cv_data/measurement_93_100.0mVs_2025-08-25T06-39-11.686802.csv",
        "cv_data/measurement_95_200.0mVs_2025-08-25T06-46-14.158045.csv",
        "cv_data/measurement_96_20.0mVs_2025-08-25T06-46-22.774810.csv",
        "temp_data/preview_Palmsens_0.5mM_Palmsens_0.5mM_CV_100mVpS_E1_scan_05.csv"
    ]
    
    # Find existing files
    test_files = []
    for filepath in potential_files:
        if os.path.exists(filepath):
            test_files.append(filepath)
    
    # If no specific files found, search for any measurement CSV files
    if not test_files:
        print("⚠️ Searching for measurement CSV files...")
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.csv') and ('measurement' in file.lower() or 'cv' in file.lower()):
                    test_files.append(os.path.join(root, file))
                    if len(test_files) >= 3:  # Limit for testing
                        break
            if test_files:
                break
    
    if not test_files:
        print("❌ No suitable test files found!")
        return []
    
    print(f"📁 Found {len(test_files)} test files for comparison:")
    for f in test_files:
        print(f"   {f}")
    
    # Initialize Enhanced Detector v2
    enhanced_detector = EnhancedBaselineDetector()
    
    comparison_results = []
    
    for filepath in test_files:
        print(f"\n📂 Analyzing: {filepath.split('/')[-1]}")
        
        # Load data
        voltages, currents = load_cv_data(filepath)
        if len(voltages) == 0:
            continue
        
        try:
            # Method 1: Traditional rolling median (current method)
            traditional_baseline = traditional_baseline_correction(currents)
            
            # Method 2: Enhanced Baseline v2
            enhanced_baseline, metadata = enhanced_detector.detect_baseline_enhanced(
                voltages, currents, filepath
            )
            
            # Compare results
            comparison = compare_baseline_results(
                currents, traditional_baseline, enhanced_baseline, 
                voltages, filepath, metadata
            )
            
            comparison_results.append(comparison)
            
            # Print comparison summary
            print(f"📊 Traditional vs Enhanced:")
            print(f"   Quality improvement: {comparison['quality_improvement']:.1%}")
            print(f"   Peak enhancement: {comparison['peak_enhancement_ratio']:.2f}x")
            print(f"   Baseline smoothness: Traditional={comparison['traditional_smoothness']:.3f}, Enhanced={comparison['enhanced_smoothness']:.3f}")
            
            # Create visualization
            create_comparison_plot(voltages, currents, traditional_baseline, enhanced_baseline, 
                                 comparison, filepath)
            
        except Exception as e:
            print(f"❌ Error comparing {filepath}: {e}")
            import traceback
            traceback.print_exc()
    
    # Overall summary
    print("\n" + "=" * 70)
    print("🏆 OVERALL COMPARISON SUMMARY")
    print("=" * 70)
    
    if comparison_results:
        avg_quality_improvement = np.mean([r['quality_improvement'] for r in comparison_results])
        avg_enhancement_ratio = np.mean([r['peak_enhancement_ratio'] for r in comparison_results])
        success_rate = len(comparison_results) / len(test_files)
        
        print(f"✅ Files analyzed: {len(comparison_results)}/{len(test_files)} ({success_rate:.1%})")
        print(f"📈 Average quality improvement: {avg_quality_improvement:.1%}")
        print(f"🎯 Average peak enhancement: {avg_enhancement_ratio:.2f}x")
        
        if avg_quality_improvement > 0.1:  # 10% improvement
            print("🏆 Enhanced Baseline v2 shows SIGNIFICANT improvement!")
        elif avg_quality_improvement > 0.05:  # 5% improvement  
            print("✅ Enhanced Baseline v2 shows moderate improvement")
        else:
            print("⚠️ Enhanced Baseline v2 shows marginal improvement")
            
        # Save comparison report
        save_comparison_report(comparison_results)
        
    else:
        print("❌ No successful comparisons completed")
    
    return comparison_results


def traditional_baseline_correction(currents: np.ndarray, window: int = 20) -> np.ndarray:
    """📊 Traditional rolling median baseline correction"""
    baseline = np.zeros_like(currents)
    half_window = window // 2
    
    for i in range(len(currents)):
        start = max(0, i - half_window)
        end = min(len(currents), i + half_window + 1)
        baseline[i] = np.median(currents[start:end])
    
    return baseline


def compare_baseline_results(currents: np.ndarray, traditional_baseline: np.ndarray, 
                           enhanced_baseline: np.ndarray, voltages: np.ndarray,
                           filepath: str, metadata: dict) -> dict:
    """📈 Compare baseline detection results"""
    
    # Corrected signals
    traditional_corrected = currents - traditional_baseline
    enhanced_corrected = currents - enhanced_baseline
    
    # Quality metrics
    traditional_smoothness = calculate_smoothness(traditional_baseline)
    enhanced_smoothness = calculate_smoothness(enhanced_baseline)
    
    # Peak enhancement
    peaks = detect_simple_peaks(currents)
    traditional_peak_enhancement = calculate_peak_enhancement(currents, traditional_corrected, peaks)
    enhanced_peak_enhancement = calculate_peak_enhancement(currents, enhanced_corrected, peaks)
    
    # Overall quality improvement
    quality_improvement = (enhanced_smoothness - traditional_smoothness) / max(traditional_smoothness, 1e-6)
    
    # Peak enhancement ratio
    peak_enhancement_ratio = enhanced_peak_enhancement / max(traditional_peak_enhancement, 1e-6)
    
    # Signal-to-noise improvement
    traditional_snr = calculate_snr(traditional_corrected, peaks)
    enhanced_snr = calculate_snr(enhanced_corrected, peaks)
    snr_improvement = enhanced_snr / max(traditional_snr, 1e-6)
    
    return {
        'filepath': filepath,
        'traditional_smoothness': traditional_smoothness,
        'enhanced_smoothness': enhanced_smoothness,
        'quality_improvement': quality_improvement,
        'peak_enhancement_ratio': peak_enhancement_ratio,
        'snr_improvement': snr_improvement,
        'enhanced_metadata': metadata,
        'peaks_detected': len(peaks),
        'traditional_corrected': traditional_corrected,
        'enhanced_corrected': enhanced_corrected,
        'traditional_baseline': traditional_baseline,
        'enhanced_baseline': enhanced_baseline
    }


def calculate_smoothness(baseline: np.ndarray) -> float:
    """📏 Calculate baseline smoothness (inverse of gradient variation)"""
    if len(baseline) < 2:
        return 0.5
    gradient = np.gradient(baseline)
    return 1.0 / (1.0 + np.std(gradient))


def detect_simple_peaks(currents: np.ndarray) -> list:
    """🎯 Simple peak detection for comparison"""
    abs_currents = np.abs(currents)
    threshold = 0.1 * np.max(abs_currents)
    peaks = []
    
    for i in range(5, len(abs_currents) - 5):
        if abs_currents[i] > threshold:
            if (abs_currents[i] > abs_currents[i-1] and 
                abs_currents[i] > abs_currents[i+1]):
                if not peaks or i - peaks[-1] > 5:
                    peaks.append(i)
    
    return peaks


def calculate_peak_enhancement(original: np.ndarray, corrected: np.ndarray, peaks: list) -> float:
    """📊 Calculate how much peaks are enhanced after baseline correction"""
    if not peaks:
        return 1.0
    
    original_heights = [abs(original[i]) for i in peaks]
    corrected_heights = [abs(corrected[i]) for i in peaks]
    
    original_avg = np.mean(original_heights) if original_heights else 1e-12
    corrected_avg = np.mean(corrected_heights) if corrected_heights else 1e-12
    
    return corrected_avg / original_avg


def calculate_snr(signal: np.ndarray, peaks: list) -> float:
    """📡 Calculate signal-to-noise ratio"""
    if not peaks:
        return 1.0
    
    # Signal: peak heights
    peak_heights = [abs(signal[i]) for i in peaks]
    signal_level = np.mean(peak_heights) if peak_heights else 1e-12
    
    # Noise: standard deviation of non-peak regions
    non_peak_mask = np.ones(len(signal), dtype=bool)
    for peak_idx in peaks:
        start = max(0, peak_idx - 3)
        end = min(len(signal), peak_idx + 4)
        non_peak_mask[start:end] = False
    
    if np.any(non_peak_mask):
        noise_level = np.std(signal[non_peak_mask])
    else:
        noise_level = np.std(signal)
    
    return signal_level / max(noise_level, 1e-12)


def create_comparison_plot(voltages: np.ndarray, currents: np.ndarray, 
                         traditional_baseline: np.ndarray, enhanced_baseline: np.ndarray,
                         comparison: dict, filepath: str):
    """📊 Create comparison visualization"""
    try:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Plot 1: Original data with baselines
        ax1.plot(voltages, currents*1e6, 'b-', alpha=0.7, linewidth=1, label='Original CV Data')
        ax1.plot(voltages, traditional_baseline*1e6, 'r--', linewidth=2, label='Traditional Baseline')
        ax1.plot(voltages, enhanced_baseline*1e6, 'g--', linewidth=2, label='Enhanced Baseline v2')
        ax1.set_xlabel('Voltage (V)')
        ax1.set_ylabel('Current (μA)')
        ax1.set_title('Original Data with Baseline Comparison')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Corrected signals comparison
        traditional_corrected = comparison['traditional_corrected']
        enhanced_corrected = comparison['enhanced_corrected']
        
        ax2.plot(voltages, traditional_corrected*1e6, 'r-', linewidth=2, alpha=0.7, label='Traditional Corrected')
        ax2.plot(voltages, enhanced_corrected*1e6, 'g-', linewidth=2, alpha=0.7, label='Enhanced v2 Corrected')
        ax2.set_xlabel('Voltage (V)')
        ax2.set_ylabel('Corrected Current (μA)')
        ax2.set_title('Baseline Corrected Signals')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Baseline comparison only
        ax3.plot(voltages, traditional_baseline*1e6, 'r-', linewidth=2, label='Traditional Baseline')
        ax3.plot(voltages, enhanced_baseline*1e6, 'g-', linewidth=2, label='Enhanced Baseline v2')
        ax3.set_xlabel('Voltage (V)')
        ax3.set_ylabel('Baseline Current (μA)')
        ax3.set_title('Baseline Methods Comparison')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Quality metrics bar chart
        metrics = ['Smoothness', 'Peak Enhancement', 'SNR Improvement']
        traditional_values = [comparison['traditional_smoothness'], 1.0, 1.0]  # Reference values
        enhanced_values = [comparison['enhanced_smoothness'], 
                         comparison['peak_enhancement_ratio'],
                         comparison['snr_improvement']]
        
        x = np.arange(len(metrics))
        width = 0.35
        
        ax4.bar(x - width/2, traditional_values, width, label='Traditional', alpha=0.7, color='red')
        ax4.bar(x + width/2, enhanced_values, width, label='Enhanced v2', alpha=0.7, color='green')
        
        ax4.set_xlabel('Metrics')
        ax4.set_ylabel('Score / Ratio')
        ax4.set_title('Performance Comparison')
        ax4.set_xticks(x)
        ax4.set_xticklabels(metrics)
        ax4.legend()
        ax4.grid(True, alpha=0.3, axis='y')
        
        # Add improvement text
        improvement_text = f"Quality Improvement: {comparison['quality_improvement']:.1%}\n"
        improvement_text += f"Peak Enhancement: {comparison['peak_enhancement_ratio']:.2f}x\n"
        improvement_text += f"SNR Improvement: {comparison['snr_improvement']:.2f}x"
        
        ax4.text(0.02, 0.98, improvement_text, transform=ax4.transAxes, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"),
                verticalalignment='top', fontsize=10)
        
        plt.suptitle(f'Baseline Detection Comparison: {filepath.split("/")[-1]}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        # Save plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"baseline_comparison_{filepath.split('/')[-1].replace('.csv', '')}_{timestamp}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Comparison plot saved: {filename}")
        
    except Exception as e:
        print(f"⚠️ Error creating comparison plot: {e}")


def save_comparison_report(comparison_results: list):
    """💾 Save detailed comparison report"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"baseline_comparison_report_{timestamp}.json"
        
        # Prepare report data (remove numpy arrays for JSON serialization)
        report_data = []
        for result in comparison_results:
            clean_result = {
                'filepath': result['filepath'],
                'traditional_smoothness': float(result['traditional_smoothness']),
                'enhanced_smoothness': float(result['enhanced_smoothness']),
                'quality_improvement': float(result['quality_improvement']),
                'peak_enhancement_ratio': float(result['peak_enhancement_ratio']),
                'snr_improvement': float(result['snr_improvement']),
                'peaks_detected': result['peaks_detected'],
                'enhanced_metadata': result['enhanced_metadata']
            }
            report_data.append(clean_result)
        
        # Calculate summary statistics
        summary = {
            'timestamp': timestamp,
            'total_files': len(report_data),
            'average_quality_improvement': float(np.mean([r['quality_improvement'] for r in report_data])),
            'average_peak_enhancement': float(np.mean([r['peak_enhancement_ratio'] for r in report_data])),
            'average_snr_improvement': float(np.mean([r['snr_improvement'] for r in report_data])),
            'total_peaks_detected': sum([r['peaks_detected'] for r in report_data])
        }
        
        full_report = {
            'summary': summary,
            'individual_results': report_data
        }
        
        with open(filename, 'w') as f:
            json.dump(full_report, f, indent=2)
        
        print(f"💾 Comparison report saved: {filename}")
        
    except Exception as e:
        print(f"⚠️ Error saving comparison report: {e}")


if __name__ == "__main__":
    # Run comparison test
    results = compare_baseline_methods()