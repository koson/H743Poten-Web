#!/usr/bin/env python3
"""
Simple CV Plotting Script
Visualize CV curves with baseline detection only
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def plot_cv_with_baseline(file_path, save_plot=False):
    """Plot CV curve with baseline detection"""
    from routes.peak_detection import detect_improved_baseline_2step
    
    print(f"\n📊 Plotting: {os.path.basename(file_path)}")
    
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
        
        # Split data into forward and reverse
        mid_point = len(v) // 2
        v_forward, i_forward = v[:mid_point], i[:mid_point]
        v_reverse, i_reverse = v[mid_point:], i[mid_point:]
        
        # Create figure with subplots
        fig = plt.figure(figsize=(15, 10))
        
        # Main plot (top)
        ax1 = plt.subplot(2, 2, (1, 2))  # Top row, both columns
        ax1.plot(v, i, 'b-', linewidth=1.5, alpha=0.8, label='CV Curve', zorder=1)
        
        # Plot baseline regions with different colors
        ax1.plot(v_forward, bf, 'g-', linewidth=3, alpha=0.9, label=f'Forward Baseline ({len(bf)} pts)', zorder=3)
        ax1.plot(v_reverse, br, 'r-', linewidth=3, alpha=0.9, label=f'Reverse Baseline ({len(br)} pts)', zorder=3)
        
        # Highlight baseline points
        ax1.scatter(v_forward, bf, c='green', s=25, alpha=0.7, zorder=4, edgecolors='darkgreen', linewidth=0.5)
        ax1.scatter(v_reverse, br, c='red', s=25, alpha=0.7, zorder=4, edgecolors='darkred', linewidth=0.5)
        
        # Add direction arrows
        mid_v = v[len(v)//2]
        mid_i = i[len(i)//2]
        ax1.annotate('→ Forward', xy=(v[len(v)//4], i[len(i)//4]), 
                    xytext=(10, 10), textcoords='offset points',
                    fontsize=10, color='green', weight='bold',
                    arrowprops=dict(arrowstyle='->', color='green', lw=1.5))
        ax1.annotate('← Reverse', xy=(v[3*len(v)//4], i[3*len(i)//4]), 
                    xytext=(-10, 10), textcoords='offset points',
                    fontsize=10, color='red', weight='bold',
                    arrowprops=dict(arrowstyle='->', color='red', lw=1.5))
        
        ax1.set_xlabel('Voltage (V)', fontsize=12)
        ax1.set_ylabel(f'Current ({unit})', fontsize=12)
        ax1.set_title(f'CV Analysis: {os.path.basename(file_path)} ({data_type})', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='best', fontsize=10)
        
        # Forward scan detail (bottom left)
        ax2 = plt.subplot(2, 2, 3)
        ax2.plot(v_forward, i_forward, 'b-', linewidth=2, label='Forward Scan', alpha=0.8)
        ax2.plot(v_forward, bf, 'g-', linewidth=3, alpha=0.9, label='Baseline')
        ax2.scatter(v_forward, bf, c='green', s=30, alpha=0.8, zorder=5, edgecolors='darkgreen')
        ax2.fill_between(v_forward, bf, i_forward, alpha=0.2, color='green', label='Peak Area')
        
        # Stats
        forward_span = bf.max() - bf.min()
        ax2.text(0.02, 0.98, f'Baseline span: {forward_span:.1f}µA\nMean: {bf.mean():.1f}µA', 
                transform=ax2.transAxes, fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
        
        ax2.set_xlabel('Voltage (V)', fontsize=11)
        ax2.set_ylabel(f'Current ({unit})', fontsize=11)
        ax2.set_title('Forward Scan Detail', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(fontsize=9)
        
        # Reverse scan detail (bottom right)
        ax3 = plt.subplot(2, 2, 4)
        ax3.plot(v_reverse, i_reverse, 'b-', linewidth=2, label='Reverse Scan', alpha=0.8)
        ax3.plot(v_reverse, br, 'r-', linewidth=3, alpha=0.9, label='Baseline')
        ax3.scatter(v_reverse, br, c='red', s=30, alpha=0.8, zorder=5, edgecolors='darkred')
        ax3.fill_between(v_reverse, br, i_reverse, alpha=0.2, color='red', label='Peak Area')
        
        # Stats
        reverse_span = br.max() - br.min()
        ax3.text(0.02, 0.98, f'Baseline span: {reverse_span:.1f}µA\nMean: {br.mean():.1f}µA', 
                transform=ax3.transAxes, fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8))
        
        ax3.set_xlabel('Voltage (V)', fontsize=11)
        ax3.set_ylabel(f'Current ({unit})', fontsize=11)
        ax3.set_title('Reverse Scan Detail', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.legend(fontsize=9)
        
        plt.tight_layout()
        
        # Print analysis details
        print(f"\n📊 Analysis Results:")
        print(f"📈 Forward baseline: {len(bf)} points, range=[{bf.min():.1f}, {bf.max():.1f}]µA, span={forward_span:.1f}µA")
        print(f"📈 Reverse baseline: {len(br)} points, range=[{br.min():.1f}, {br.max():.1f}]µA, span={reverse_span:.1f}µA")
        
        # Quality assessment
        data_span = i.max() - i.min()
        forward_quality = "🟢 Good" if forward_span < data_span * 0.15 else "🟡 Fair" if forward_span < data_span * 0.3 else "🔴 Poor"
        reverse_quality = "🟢 Good" if reverse_span < data_span * 0.15 else "🟡 Fair" if reverse_span < data_span * 0.3 else "🔴 Poor"
        
        print(f"📈 Quality: Forward {forward_quality}, Reverse {reverse_quality}")
        
        if baseline_info:
            if 'forward_segment' in baseline_info and baseline_info['forward_segment']:
                fs = baseline_info['forward_segment']
                print(f"🔵 Forward segment: R²={fs.get('r2', 0):.3f}, slope={fs.get('slope', 0):.2e}")
            
            if 'reverse_segment' in baseline_info and baseline_info['reverse_segment']:
                rs = baseline_info['reverse_segment']
                print(f"🔵 Reverse segment: R²={rs.get('r2', 0):.3f}, slope={rs.get('slope', 0):.2e}")
        
        # Save plot if requested
        if save_plot:
            plot_filename = f"cv_baseline_{os.path.splitext(os.path.basename(file_path))[0]}.png"
            plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
            print(f"💾 Plot saved as: {plot_filename}")
        
        plt.show()
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Plot specific file
        file_path = sys.argv[1]
        save_plot = len(sys.argv) > 2 and sys.argv[2].lower() in ['save', 'true', '1']
        plot_cv_with_baseline(file_path, save_plot=save_plot)
    else:
        # Plot sample files
        sample_files = [
            "Test_data/Palmsens/Palmsens_5mM/Palmsens_5mM_CV_50mVpS_E2_scan_06.csv",
            "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_50mVpS_E2_scan_08.csv",
        ]
        
        print("🎨 CV BASELINE PLOTTING")
        print("="*50)
        print("Visualizing CV curves with baseline detection")
        print("="*50)
        
        for file_path in sample_files:
            if os.path.exists(file_path):
                plot_cv_with_baseline(file_path, save_plot=False)
                print("\n" + "="*60)
            else:
                print(f"❌ File not found: {os.path.basename(file_path)}")

if __name__ == "__main__":
    main()