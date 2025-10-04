#!/usr/bin/env python3
"""
📊 HybridCV Enhanced Visualization
=================================

Visualize CV data and peak detection results from HybridCV Enhanced system.
Show comparison between V5, DeepCV V2, and Hybrid results.

Author: H743Poten Research Team
Date: October 4, 2025
"""

import sys
import os
sys.path.append('.')
sys.path.append('validation_data')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec
import seaborn as sns
from hybrid_cv_enhanced import HybridCVEnhanced

# Set style for better plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def create_comprehensive_visualization():
    """Create comprehensive visualization of HybridCV Enhanced results"""
    print("📊 CREATING HYBRIDCV ENHANCED VISUALIZATIONS")
    print("=" * 70)
    
    # Initialize HybridCV Enhanced
    hybrid = HybridCVEnhanced(config={
        'v5_weight': 0.6,
        'deepcv_weight': 0.4,
        'verbose': False,
        'adaptive_weighting': True
    })
    
    # Generate test data (same as validation)
    test_data = [
        {
            'voltage': np.linspace(-0.4, 0.7, 220),
            'current_pattern': 'ferrocyanide',
            'filename': 'PalmSens_0.5mM_Ferrocyanide_Simulated.csv',
            'title': 'Ferrocyanide (0.5mM)',
            'color': '#FF6B6B'
        },
        {
            'voltage': np.linspace(-0.5, 0.8, 260),
            'current_pattern': 'dopamine',
            'filename': 'PalmSens_1.0mM_Dopamine_Simulated.csv',
            'title': 'Dopamine (1.0mM)',
            'color': '#4ECDC4'
        },
        {
            'voltage': np.linspace(-0.3, 0.6, 180),
            'current_pattern': 'ascorbic_acid',
            'filename': 'PalmSens_5.0mM_AscorbicAcid_Simulated.csv',
            'title': 'Ascorbic Acid (5.0mM)',
            'color': '#45B7D1'
        }
    ]
    
    # Generate CV patterns
    def generate_cv_pattern(voltage, pattern_type):
        if pattern_type == 'ferrocyanide':
            anodic = 15e-6 * np.exp(-((voltage - 0.2) / 0.08)**2)
            cathodic = -12e-6 * np.exp(-((voltage + 0.1) / 0.08)**2)
            background = 1e-8 * voltage
            noise = 0.5e-6 * np.random.normal(0, 1, len(voltage))
        elif pattern_type == 'dopamine':
            anodic = 8e-6 * np.exp(-((voltage - 0.3) / 0.12)**2)
            cathodic = -2e-6 * np.exp(-((voltage - 0.1) / 0.15)**2)
            background = 2e-8 * voltage
            noise = 0.3e-6 * np.random.normal(0, 1, len(voltage))
        elif pattern_type == 'ascorbic_acid':
            peak1 = 6e-6 * np.exp(-((voltage - 0.1) / 0.06)**2)
            peak2 = 4e-6 * np.exp(-((voltage - 0.4) / 0.08)**2)
            background = 0.5e-8 * voltage
            noise = 0.2e-6 * np.random.normal(0, 1, len(voltage))
            cathodic = 0
            anodic = peak1 + peak2
        
        current = anodic + cathodic + background + noise
        return current * 1e6  # Convert to µA
    
    # Process data and get results
    results_data = []
    
    for data in test_data:
        voltage = data['voltage']
        current = generate_cv_pattern(voltage, data['current_pattern'])
        
        # Run HybridCV Enhanced
        result = hybrid.detect_peaks(voltage, current, data['filename'])
        
        # Store results with data
        results_data.append({
            'voltage': voltage,
            'current': current,
            'result': result,
            'title': data['title'],
            'color': data['color'],
            'pattern': data['current_pattern']
        })
    
    # Create comprehensive visualization
    create_detection_comparison_plots(results_data)
    create_performance_summary_plots(results_data)
    create_peak_statistics_plots(results_data)
    
    print("✅ All visualizations created successfully!")
    return results_data

def create_detection_comparison_plots(results_data):
    """Create detailed CV plots with peak detection results"""
    
    fig = plt.figure(figsize=(20, 15))
    gs = GridSpec(3, 4, figure=fig, hspace=0.3, wspace=0.3)
    
    for i, data in enumerate(results_data):
        voltage = data['voltage']
        current = data['current']
        result = data['result']
        title = data['title']
        color = data['color']
        
        # Extract peak information
        v5_result = result.get('v5_result', {})
        deepcv_result = result.get('deepcv_result', {})
        ensemble_result = result.get('ensemble_result', {})
        
        # Main CV plot
        ax_main = fig.add_subplot(gs[i, 0:2])
        ax_main.plot(voltage, current, 'b-', linewidth=2, alpha=0.7, label='CV Data')
        
        # Add peak markers from V5 (if available)
        v5_peaks = v5_result.get('peaks_list', [])
        if v5_peaks:
            for peak in v5_peaks:
                if 'voltage' in peak and 'current' in peak:
                    ax_main.plot(peak['voltage'], peak['current'], 'ro', 
                               markersize=8, alpha=0.7, label='V5 Peaks' if peak == v5_peaks[0] else "")
        
        ax_main.set_xlabel('Voltage (V)', fontsize=12)
        ax_main.set_ylabel('Current (µA)', fontsize=12)
        ax_main.set_title(f'{title} - CV with Peak Detection', fontsize=14, fontweight='bold')
        ax_main.grid(True, alpha=0.3)
        ax_main.legend()
        
        # Peak count comparison
        ax_bars = fig.add_subplot(gs[i, 2])
        methods = ['V5', 'DeepCV', 'Hybrid']
        peak_counts = [
            v5_result.get('peaks_detected', 0),
            deepcv_result.get('peaks_detected', 0),
            ensemble_result.get('peaks_detected', 0)
        ]
        
        bars = ax_bars.bar(methods, peak_counts, color=['#FF6B6B', '#4ECDC4', '#45B7D1'], alpha=0.8)
        ax_bars.set_ylabel('Peak Count', fontsize=12)
        ax_bars.set_title('Peak Count Comparison', fontsize=12, fontweight='bold')
        ax_bars.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, count in zip(bars, peak_counts):
            ax_bars.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        str(count), ha='center', va='bottom', fontweight='bold')
        
        # Confidence comparison
        ax_conf = fig.add_subplot(gs[i, 3])
        confidences = [
            v5_result.get('confidence', 0),
            deepcv_result.get('confidence', 0),
            ensemble_result.get('confidence', 0)
        ]
        
        bars_conf = ax_conf.bar(methods, confidences, color=['#FF6B6B', '#4ECDC4', '#45B7D1'], alpha=0.8)
        ax_conf.set_ylabel('Confidence (%)', fontsize=12)
        ax_conf.set_title('Confidence Comparison', fontsize=12, fontweight='bold')
        ax_conf.set_ylim(0, 105)
        ax_conf.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, conf in zip(bars_conf, confidences):
            ax_conf.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                        f'{conf:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    plt.suptitle('HybridCV Enhanced - Peak Detection Analysis', fontsize=18, fontweight='bold', y=0.96)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('hybridcv_enhanced_detection_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("📊 Detection comparison plots saved as 'hybridcv_enhanced_detection_analysis.png'")

def create_performance_summary_plots(results_data):
    """Create performance summary visualization"""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Extract data for plotting
    titles = [data['title'] for data in results_data]
    v5_peaks = [data['result']['v5_result'].get('peaks_detected', 0) for data in results_data]
    deepcv_peaks = [data['result']['deepcv_result'].get('peaks_detected', 0) for data in results_data]
    hybrid_peaks = [data['result']['ensemble_result'].get('peaks_detected', 0) for data in results_data]
    
    v5_conf = [data['result']['v5_result'].get('confidence', 0) for data in results_data]
    deepcv_conf = [data['result']['deepcv_result'].get('confidence', 0) for data in results_data]
    hybrid_conf = [data['result']['ensemble_result'].get('confidence', 0) for data in results_data]
    
    processing_times = [data['result'].get('processing_time', 0) * 1000 for data in results_data]
    
    # 1. Peak Detection Comparison
    x = np.arange(len(titles))
    width = 0.25
    
    ax1.bar(x - width, v5_peaks, width, label='Enhanced V5', color='#FF6B6B', alpha=0.8)
    ax1.bar(x, deepcv_peaks, width, label='DeepCV V2', color='#4ECDC4', alpha=0.8)
    ax1.bar(x + width, hybrid_peaks, width, label='Hybrid Enhanced', color='#45B7D1', alpha=0.8)
    
    ax1.set_xlabel('Electrochemical Systems')
    ax1.set_ylabel('Peak Count')
    ax1.set_title('Peak Detection Performance Comparison', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(titles, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 2. Confidence Analysis
    ax2.bar(x - width, v5_conf, width, label='Enhanced V5', color='#FF6B6B', alpha=0.8)
    ax2.bar(x, deepcv_conf, width, label='DeepCV V2', color='#4ECDC4', alpha=0.8)
    ax2.bar(x + width, hybrid_conf, width, label='Hybrid Enhanced', color='#45B7D1', alpha=0.8)
    
    ax2.set_xlabel('Electrochemical Systems')
    ax2.set_ylabel('Confidence (%)')
    ax2.set_title('Detection Confidence Comparison', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(titles, rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Processing Time Analysis
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    bars = ax3.bar(titles, processing_times, color=colors, alpha=0.8)
    ax3.set_xlabel('Electrochemical Systems')
    ax3.set_ylabel('Processing Time (ms)')
    ax3.set_title('Processing Speed Analysis', fontweight='bold')
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bar, time_val in zip(bars, processing_times):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{time_val:.1f}ms', ha='center', va='bottom', fontweight='bold')
    
    # 4. Method Agreement Analysis
    agreements = []
    agreement_labels = []
    
    for i, data in enumerate(results_data):
        v5_count = data['result']['v5_result'].get('peaks_detected', 0)
        deepcv_count = data['result']['deepcv_result'].get('peaks_detected', 0)
        hybrid_count = data['result']['ensemble_result'].get('peaks_detected', 0)
        
        v5_deepcv_diff = abs(v5_count - deepcv_count)
        v5_hybrid_diff = abs(v5_count - hybrid_count)
        deepcv_hybrid_diff = abs(deepcv_count - hybrid_count)
        
        agreements.extend([v5_deepcv_diff, v5_hybrid_diff, deepcv_hybrid_diff])
        agreement_labels.extend([f'{titles[i]}\\nV5-DeepCV', f'{titles[i]}\\nV5-Hybrid', f'{titles[i]}\\nDeepCV-Hybrid'])
    
    x_agree = np.arange(len(agreement_labels))
    colors_agree = ['red' if diff > 1 else 'orange' if diff == 1 else 'green' for diff in agreements]
    
    bars_agree = ax4.bar(x_agree, agreements, color=colors_agree, alpha=0.7)
    ax4.set_xlabel('Method Comparisons')
    ax4.set_ylabel('Peak Count Difference')
    ax4.set_title('Method Agreement Analysis', fontweight='bold')
    ax4.set_xticks(x_agree)
    ax4.set_xticklabels(agreement_labels, rotation=45, ha='right', fontsize=9)
    ax4.grid(True, alpha=0.3, axis='y')
    
    # Add reference line for perfect agreement
    ax4.axhline(y=0, color='green', linestyle='--', alpha=0.7, label='Perfect Agreement')
    ax4.axhline(y=1, color='orange', linestyle='--', alpha=0.7, label='Close Agreement')
    ax4.legend()
    
    plt.tight_layout()
    plt.suptitle('HybridCV Enhanced - Performance Summary', fontsize=16, fontweight='bold', y=1.02)
    plt.savefig('hybridcv_enhanced_performance_summary.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("📈 Performance summary plots saved as 'hybridcv_enhanced_performance_summary.png'")

def create_peak_statistics_plots(results_data):
    """Create detailed peak statistics visualization"""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Peak Distribution by Method
    all_v5_peaks = [data['result']['v5_result'].get('peaks_detected', 0) for data in results_data]
    all_deepcv_peaks = [data['result']['deepcv_result'].get('peaks_detected', 0) for data in results_data]
    all_hybrid_peaks = [data['result']['ensemble_result'].get('peaks_detected', 0) for data in results_data]
    
    methods = ['Enhanced V5', 'DeepCV V2', 'Hybrid Enhanced']
    peak_data = [all_v5_peaks, all_deepcv_peaks, all_hybrid_peaks]
    
    bp = ax1.boxplot(peak_data, labels=methods, patch_artist=True)
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax1.set_ylabel('Peak Count')
    ax1.set_title('Peak Count Distribution by Method', fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 2. Confidence Distribution
    all_v5_conf = [data['result']['v5_result'].get('confidence', 0) for data in results_data]
    all_deepcv_conf = [data['result']['deepcv_result'].get('confidence', 0) for data in results_data]
    all_hybrid_conf = [data['result']['ensemble_result'].get('confidence', 0) for data in results_data]
    
    conf_data = [all_v5_conf, all_deepcv_conf, all_hybrid_conf]
    
    bp2 = ax2.boxplot(conf_data, labels=methods, patch_artist=True)
    for patch, color in zip(bp2['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax2.set_ylabel('Confidence (%)')
    ax2.set_title('Confidence Distribution by Method', fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Peak Count vs Confidence Scatter
    for i, (method, peaks, confs, color) in enumerate(zip(methods, peak_data, conf_data, colors)):
        ax3.scatter(peaks, confs, c=color, alpha=0.7, s=100, label=method)
    
    ax3.set_xlabel('Peak Count')
    ax3.set_ylabel('Confidence (%)')
    ax3.set_title('Peak Count vs Confidence Relationship', fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Processing Efficiency
    titles = [data['title'] for data in results_data]
    processing_times = [data['result'].get('processing_time', 0) * 1000 for data in results_data]
    total_peaks = [data['result']['ensemble_result'].get('peaks_detected', 1) for data in results_data]  # Avoid division by zero
    
    efficiency = [time/peaks if peaks > 0 else time for time, peaks in zip(processing_times, total_peaks)]
    
    bars = ax4.bar(titles, efficiency, color=['#FF6B6B', '#4ECDC4', '#45B7D1'], alpha=0.8)
    ax4.set_xlabel('Electrochemical Systems')
    ax4.set_ylabel('Time per Peak (ms/peak)')
    ax4.set_title('Processing Efficiency (Time per Peak)', fontweight='bold')
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(True, alpha=0.3, axis='y')
    
    # Add efficiency values
    for bar, eff in zip(bars, efficiency):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f'{eff:.1f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.suptitle('HybridCV Enhanced - Peak Detection Statistics', fontsize=16, fontweight='bold', y=1.02)
    plt.savefig('hybridcv_enhanced_peak_statistics.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("📊 Peak statistics plots saved as 'hybridcv_enhanced_peak_statistics.png'")

def create_detailed_cv_plots(results_data):
    """Create detailed individual CV plots with peak annotations"""
    
    for i, data in enumerate(results_data):
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        voltage = data['voltage']
        current = data['current']
        result = data['result']
        title = data['title']
        color = data['color']
        
        # Extract results
        v5_result = result.get('v5_result', {})
        deepcv_result = result.get('deepcv_result', {})
        ensemble_result = result.get('ensemble_result', {})
        
        # 1. Raw CV Data
        ax1.plot(voltage, current, 'b-', linewidth=2, alpha=0.8)
        ax1.set_xlabel('Voltage (V)')
        ax1.set_ylabel('Current (µA)')
        ax1.set_title(f'{title} - Raw CV Data')
        ax1.grid(True, alpha=0.3)
        
        # Add voltage scan direction arrows
        mid_point = len(voltage) // 2
        ax1.annotate('Forward Scan', xy=(voltage[mid_point//2], current[mid_point//2]), 
                    xytext=(voltage[mid_point//2]-0.1, current[mid_point//2]+2),
                    arrowprops=dict(arrowstyle='->', color='red', alpha=0.7))
        ax1.annotate('Reverse Scan', xy=(voltage[mid_point + mid_point//2], current[mid_point + mid_point//2]), 
                    xytext=(voltage[mid_point + mid_point//2]+0.1, current[mid_point + mid_point//2]+2),
                    arrowprops=dict(arrowstyle='->', color='blue', alpha=0.7))
        
        # 2. V5 Peak Detection Results
        ax2.plot(voltage, current, 'b-', linewidth=2, alpha=0.6, label='CV Data')
        
        v5_peaks = v5_result.get('peaks_list', [])
        if v5_peaks:
            peak_voltages = []
            peak_currents = []
            for peak in v5_peaks:
                if 'voltage' in peak and 'current' in peak:
                    peak_voltages.append(peak['voltage'])
                    peak_currents.append(peak['current'])
            
            if peak_voltages:
                ax2.scatter(peak_voltages, peak_currents, c='red', s=50, alpha=0.8, 
                           label=f'V5 Peaks (n={len(peak_voltages)})', zorder=5)
        
        ax2.set_xlabel('Voltage (V)')
        ax2.set_ylabel('Current (µA)')
        ax2.set_title(f'Enhanced V5 Detection: {v5_result.get("peaks_detected", 0)} peaks ({v5_result.get("confidence", 0):.1f}%)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. DeepCV V2 Results (simulated peak positions)
        ax3.plot(voltage, current, 'b-', linewidth=2, alpha=0.6, label='CV Data')
        
        # Since DeepCV V2 only gives count, simulate peak positions for visualization
        deepcv_peak_count = deepcv_result.get('peaks_detected', 0)
        if deepcv_peak_count > 0:
            # Find highest points as likely peaks
            from scipy.signal import find_peaks
            try:
                peaks_pos, _ = find_peaks(current, height=np.std(current), distance=5)
                peaks_neg, _ = find_peaks(-current, height=np.std(current), distance=5)
                
                all_peak_indices = sorted(list(peaks_pos) + list(peaks_neg))[:deepcv_peak_count]
                
                if all_peak_indices:
                    peak_v = voltage[all_peak_indices]
                    peak_i = current[all_peak_indices]
                    ax3.scatter(peak_v, peak_i, c='green', s=50, alpha=0.8, 
                               label=f'DeepCV V2 Peaks (n={deepcv_peak_count})', zorder=5)
            except:
                pass
        
        ax3.set_xlabel('Voltage (V)')
        ax3.set_ylabel('Current (µA)')
        ax3.set_title(f'DeepCV V2 Detection: {deepcv_peak_count} peaks ({deepcv_result.get("confidence", 0):.1f}%)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Hybrid Results Summary
        methods = ['V5', 'DeepCV', 'Hybrid']
        peak_counts = [
            v5_result.get('peaks_detected', 0),
            deepcv_result.get('peaks_detected', 0),
            ensemble_result.get('peaks_detected', 0)
        ]
        confidences = [
            v5_result.get('confidence', 0),
            deepcv_result.get('confidence', 0),
            ensemble_result.get('confidence', 0)
        ]
        
        x = np.arange(len(methods))
        width = 0.35
        
        bars1 = ax4.bar(x - width/2, peak_counts, width, label='Peak Count', 
                       color=['#FF6B6B', '#4ECDC4', '#45B7D1'], alpha=0.8)
        
        ax4_twin = ax4.twinx()
        bars2 = ax4_twin.bar(x + width/2, confidences, width, label='Confidence (%)', 
                            color=['#FF6B6B', '#4ECDC4', '#45B7D1'], alpha=0.5)
        
        ax4.set_xlabel('Detection Methods')
        ax4.set_ylabel('Peak Count', color='black')
        ax4_twin.set_ylabel('Confidence (%)', color='gray')
        ax4.set_title('Method Comparison Summary')
        ax4.set_xticks(x)
        ax4.set_xticklabels(methods)
        
        # Add value labels
        for bar, count in zip(bars1, peak_counts):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    str(count), ha='center', va='bottom', fontweight='bold')
        
        for bar, conf in zip(bars2, confidences):
            ax4_twin.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                         f'{conf:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        ax4.grid(True, alpha=0.3, axis='y')
        
        # Add decision information
        decision = ensemble_result.get('decision', 'unknown')
        consensus_score = ensemble_result.get('consensus_score', 0.0)
        
        ax4.text(0.02, 0.98, f'Decision: {decision}\\nConsensus: {consensus_score:.2f}', 
                transform=ax4.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        plt.suptitle(f'{title} - Detailed Analysis', fontsize=16, fontweight='bold', y=1.02)
        plt.savefig(f'detailed_cv_analysis_{data["pattern"]}.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"📊 Detailed analysis for {title} saved as 'detailed_cv_analysis_{data['pattern']}.png'")

if __name__ == "__main__":
    print("🎨 Starting HybridCV Enhanced Visualization Suite...")
    
    try:
        # Create all visualizations
        results_data = create_comprehensive_visualization()
        
        # Create detailed individual plots
        create_detailed_cv_plots(results_data)
        
        print("\\n🎉 VISUALIZATION COMPLETE!")
        print("=" * 50)
        print("📁 Generated Files:")
        print("   • hybridcv_enhanced_detection_analysis.png")
        print("   • hybridcv_enhanced_performance_summary.png") 
        print("   • hybridcv_enhanced_peak_statistics.png")
        print("   • detailed_cv_analysis_ferrocyanide.png")
        print("   • detailed_cv_analysis_dopamine.png")
        print("   • detailed_cv_analysis_ascorbic_acid.png")
        
    except Exception as e:
        print(f"❌ Error creating visualizations: {e}")
        import traceback
        traceback.print_exc()