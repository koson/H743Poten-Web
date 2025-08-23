#!/usr/bin/env python3
"""
CV Analysis Plotting Script
Visualize CV curves with baseline detection and peak identification
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def plot_cv_analysis(file_path, show_details=True, save_plot=False):
    """Plot CV analysis with baseline and peaks"""
    from routes.peak_detection import detect_improved_baseline_2step, detect_cv_peaks
    
    print(f"\n📊 Analyzing: {os.path.basename(file_path)}")
    
    try:
        # Load data
        df = pd.read_csv(file_path, skiprows=1)
        
        if 'A' in df.columns:
            v, i = df['V'].values, df['A'].values * 1e6  # STM32 format
            unit = "µA"
            data_type = "STM32"
        elif 'uA' in df.columns:
            v, i = df['V'].values, df['uA'].values  # Palmsens format
            unit = "µA"
            data_type = "Palmsens"
        else:
            print("❌ Unknown data format")
            return False
        
        print(f"📈 {data_type} | {len(v)} points, V:[{v.min():.3f},{v.max():.3f}], I:[{i.min():.1f},{i.max():.1f}]{unit}")
        
        # Detect baseline
        baseline_result = detect_improved_baseline_2step(v, i)
        if baseline_result is None:
            print("❌ Baseline detection failed")
            return False
        
        bf, br, baseline_info = baseline_result
        
        # Detect peaks
        peaks_result = detect_cv_peaks(v, i)
        if peaks_result is None:
            print("❌ Peak detection failed")
            return False
        
        peaks_forward, peaks_reverse, peak_info = peaks_result
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle(f'CV Analysis: {os.path.basename(file_path)}', fontsize=14, fontweight='bold')
        
        # Plot 1: Full CV curve with baseline
        ax1.plot(v, i, 'b-', linewidth=1.5, alpha=0.8, label='CV Curve')
        
        # Split data into forward and reverse
        mid_point = len(v) // 2
        v_forward, i_forward = v[:mid_point], i[:mid_point]
        v_reverse, i_reverse = v[mid_point:], i[mid_point:]
        
        # Plot baseline regions
        ax1.plot(v_forward, bf, 'g-', linewidth=3, alpha=0.7, label=f'Forward Baseline (n={len(bf)})')
        ax1.plot(v_reverse, br, 'r-', linewidth=3, alpha=0.7, label=f'Reverse Baseline (n={len(br)})')
        
        # Highlight baseline points
        ax1.scatter(v_forward, bf, c='green', s=15, alpha=0.6, zorder=5)
        ax1.scatter(v_reverse, br, c='red', s=15, alpha=0.6, zorder=5)
        
        # Plot peaks
        if peaks_forward:
            for peak in peaks_forward:
                v_peak, i_peak = peak['voltage'], peak['current']
                height = peak.get('height', 0)
                baseline_at_peak = peak.get('baseline_current', i_peak)
                
                # Peak point
                ax1.scatter(v_peak, i_peak, c='darkgreen', s=100, marker='^', 
                           edgecolors='black', linewidth=1, zorder=10, label='Forward Peaks' if peak == peaks_forward[0] else "")
                
                # Height line
                if height > 0:
                    ax1.plot([v_peak, v_peak], [baseline_at_peak, i_peak], 'g--', 
                            linewidth=2, alpha=0.8)
                    # Height annotation
                    ax1.annotate(f'{height:.1f}µA', 
                               xy=(v_peak, (baseline_at_peak + i_peak)/2),
                               xytext=(5, 0), textcoords='offset points',
                               fontsize=8, color='darkgreen', weight='bold')
        
        if peaks_reverse:
            for peak in peaks_reverse:
                v_peak, i_peak = peak['voltage'], peak['current']
                height = peak.get('height', 0)
                baseline_at_peak = peak.get('baseline_current', i_peak)
                
                # Peak point
                ax1.scatter(v_peak, i_peak, c='darkred', s=100, marker='v', 
                           edgecolors='black', linewidth=1, zorder=10, label='Reverse Peaks' if peak == peaks_reverse[0] else "")
                
                # Height line
                if abs(height) > 0:
                    ax1.plot([v_peak, v_peak], [baseline_at_peak, i_peak], 'r--', 
                            linewidth=2, alpha=0.8)
                    # Height annotation
                    ax1.annotate(f'{abs(height):.1f}µA', 
                               xy=(v_peak, (baseline_at_peak + i_peak)/2),
                               xytext=(5, 0), textcoords='offset points',
                               fontsize=8, color='darkred', weight='bold')
        
        ax1.set_xlabel('Voltage (V)')
        ax1.set_ylabel(f'Current ({unit})')
        ax1.set_title('CV Curve with Baseline and Peak Detection')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='best')
        
        # Plot 2: Separated forward and reverse scans
        ax2.subplot(1, 2, 1)
        ax2 = plt.subplot(2, 2, 3)  # Bottom left
        ax2.plot(v_forward, i_forward, 'b-', linewidth=2, label='Forward Scan')
        ax2.plot(v_forward, bf, 'g-', linewidth=3, alpha=0.7, label='Baseline')
        ax2.scatter(v_forward, bf, c='green', s=20, alpha=0.7)
        
        if peaks_forward:
            for peak in peaks_forward:
                v_peak, i_peak = peak['voltage'], peak['current']
                ax2.scatter(v_peak, i_peak, c='darkgreen', s=120, marker='^', 
                           edgecolors='black', linewidth=1, zorder=10)
        
        ax2.set_xlabel('Voltage (V)')
        ax2.set_ylabel(f'Current ({unit})')
        ax2.set_title('Forward Scan')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Reverse scan
        ax3 = plt.subplot(2, 2, 4)  # Bottom right
        ax3.plot(v_reverse, i_reverse, 'b-', linewidth=2, label='Reverse Scan')
        ax3.plot(v_reverse, br, 'r-', linewidth=3, alpha=0.7, label='Baseline')
        ax3.scatter(v_reverse, br, c='red', s=20, alpha=0.7)
        
        if peaks_reverse:
            for peak in peaks_reverse:
                v_peak, i_peak = peak['voltage'], peak['current']
                ax3.scatter(v_peak, i_peak, c='darkred', s=120, marker='v', 
                           edgecolors='black', linewidth=1, zorder=10)
        
        ax3.set_xlabel('Voltage (V)')
        ax3.set_ylabel(f'Current ({unit})')
        ax3.set_title('Reverse Scan')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        
        plt.tight_layout()
        
        # Print analysis details
        if show_details:
            print(f"\n📊 Analysis Results:")
            print(f"📈 Forward baseline: {len(bf)} points, range=[{bf.min():.1f}, {bf.max():.1f}]µA")
            print(f"📈 Reverse baseline: {len(br)} points, range=[{br.min():.1f}, {br.max():.1f}]µA")
            
            if peaks_forward:
                print(f"🔺 Forward peaks: {len(peaks_forward)}")
                for i, peak in enumerate(peaks_forward):
                    print(f"   Peak {i+1}: V={peak['voltage']:.3f}V, I={peak['current']:.1f}µA, Height={peak.get('height', 0):.1f}µA")
            
            if peaks_reverse:
                print(f"🔻 Reverse peaks: {len(peaks_reverse)}")
                for i, peak in enumerate(peaks_reverse):
                    print(f"   Peak {i+1}: V={peak['voltage']:.3f}V, I={peak['current']:.1f}µA, Height={abs(peak.get('height', 0)):.1f}µA")
        
        # Save plot if requested
        if save_plot:
            plot_filename = f"cv_analysis_{os.path.splitext(os.path.basename(file_path))[0]}.png"
            plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
            print(f"💾 Plot saved as: {plot_filename}")
        
        plt.show()
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def plot_multiple_files(file_list, save_plots=False):
    """Plot multiple CV files for comparison"""
    print("🔬 MULTIPLE CV ANALYSIS")
    print("="*60)
    
    for file_path in file_list:
        if os.path.exists(file_path):
            plot_cv_analysis(file_path, show_details=True, save_plot=save_plots)
            print("\n" + "="*60)
        else:
            print(f"❌ File not found: {file_path}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Plot specific file
        file_path = sys.argv[1]
        save_plot = len(sys.argv) > 2 and sys.argv[2].lower() in ['save', 'true', '1']
        plot_cv_analysis(file_path, save_plot=save_plot)
    else:
        # Plot sample files
        sample_files = [
            "Test_data/Palmsens/Palmsens_5mM/Palmsens_5mM_CV_50mVpS_E2_scan_06.csv",
            "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_50mVpS_E2_scan_08.csv",
        ]
        
        print("🎨 CV ANALYSIS PLOTTING")
        print("="*50)
        print("Plotting sample CV files with baseline and peak detection")
        print("="*50)
        
        plot_multiple_files(sample_files, save_plots=False)

if __name__ == "__main__":
    main()