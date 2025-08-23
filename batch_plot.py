#!/usr/bin/env python3
"""
Batch CV Plotting Script
Generate plots for multiple CV files and save as images
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def plot_and_save_cv(file_path, output_dir="plots"):
    """Plot CV curve and save as image"""
    from routes.peak_detection import detect_improved_baseline_2step
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n📊 Processing: {os.path.basename(file_path)}")
    
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
        
        # Split data
        mid_point = len(v) // 2
        v_forward, i_forward = v[:mid_point], i[:mid_point]
        v_reverse, i_reverse = v[mid_point:], i[mid_point:]
        
        # Create figure
        plt.style.use('default')  # Reset style
        fig = plt.figure(figsize=(16, 12))
        
        # Main plot
        ax1 = plt.subplot(2, 2, (1, 2))
        ax1.plot(v, i, 'b-', linewidth=2, alpha=0.8, label='CV Curve')
        ax1.plot(v_forward, bf, 'g-', linewidth=4, alpha=0.9, label=f'Forward Baseline ({len(bf)} pts)')
        ax1.plot(v_reverse, br, 'r-', linewidth=4, alpha=0.9, label=f'Reverse Baseline ({len(br)} pts)')
        ax1.scatter(v_forward, bf, c='green', s=30, alpha=0.7, zorder=4)
        ax1.scatter(v_reverse, br, c='red', s=30, alpha=0.7, zorder=4)
        
        ax1.set_xlabel('Voltage (V)', fontsize=14)
        ax1.set_ylabel(f'Current ({unit})', fontsize=14)
        ax1.set_title(f'CV Analysis: {os.path.basename(file_path)} ({data_type})', fontsize=16, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=12)
        
        # Forward detail
        ax2 = plt.subplot(2, 2, 3)
        ax2.plot(v_forward, i_forward, 'b-', linewidth=2, label='Forward Scan', alpha=0.8)
        ax2.plot(v_forward, bf, 'g-', linewidth=3, label='Baseline')
        ax2.scatter(v_forward, bf, c='green', s=25, alpha=0.8)
        ax2.fill_between(v_forward, bf, i_forward, alpha=0.2, color='green')
        
        forward_span = bf.max() - bf.min()
        ax2.text(0.02, 0.98, f'Span: {forward_span:.1f}µA\nMean: {bf.mean():.1f}µA\nR²: {baseline_info.get("forward_segment", {}).get("r2", 0):.3f}', 
                transform=ax2.transAxes, fontsize=11, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
        
        ax2.set_xlabel('Voltage (V)', fontsize=12)
        ax2.set_ylabel(f'Current ({unit})', fontsize=12)
        ax2.set_title('Forward Scan', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(fontsize=10)
        
        # Reverse detail
        ax3 = plt.subplot(2, 2, 4)
        ax3.plot(v_reverse, i_reverse, 'b-', linewidth=2, label='Reverse Scan', alpha=0.8)
        ax3.plot(v_reverse, br, 'r-', linewidth=3, label='Baseline')
        ax3.scatter(v_reverse, br, c='red', s=25, alpha=0.8)
        ax3.fill_between(v_reverse, br, i_reverse, alpha=0.2, color='red')
        
        reverse_span = br.max() - br.min()
        ax3.text(0.02, 0.98, f'Span: {reverse_span:.1f}µA\nMean: {br.mean():.1f}µA\nR²: {baseline_info.get("reverse_segment", {}).get("r2", 0):.3f}', 
                transform=ax3.transAxes, fontsize=11, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8))
        
        ax3.set_xlabel('Voltage (V)', fontsize=12)
        ax3.set_ylabel(f'Current ({unit})', fontsize=12)
        ax3.set_title('Reverse Scan', fontsize=14, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.legend(fontsize=10)
        
        plt.tight_layout()
        
        # Save plot
        plot_filename = f"{output_dir}/cv_baseline_{os.path.splitext(os.path.basename(file_path))[0]}.png"
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()  # Close to free memory
        
        # Print results
        data_span = i.max() - i.min()
        forward_quality = "🟢" if forward_span < data_span * 0.15 else "🟡" if forward_span < data_span * 0.3 else "🔴"
        reverse_quality = "🟢" if reverse_span < data_span * 0.15 else "🟡" if reverse_span < data_span * 0.3 else "🔴"
        
        print(f"📈 Forward: span={forward_span:.1f}µA {forward_quality}")
        print(f"📈 Reverse: span={reverse_span:.1f}µA {reverse_quality}")
        print(f"💾 Saved: {plot_filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def batch_plot_samples():
    """Plot sample files from both instruments"""
    
    sample_files = [
        # Palmsens samples
        "Test_data/Palmsens/Palmsens_5mM/Palmsens_5mM_CV_20mVpS_E1_scan_05.csv",
        "Test_data/Palmsens/Palmsens_5mM/Palmsens_5mM_CV_50mVpS_E2_scan_06.csv",
        "Test_data/Palmsens/Palmsens_5mM/Palmsens_5mM_CV_400mVpS_E3_scan_08.csv",
        
        # STM32 samples
        "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_20mVpS_E4_scan_05.csv",
        "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_50mVpS_E2_scan_08.csv",
        "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_100mVpS_E4_scan_05.csv",
    ]
    
    print("🎨 BATCH CV PLOTTING")
    print("="*60)
    print("Generating CV baseline plots for sample files")
    print("="*60)
    
    results = []
    for file_path in sample_files:
        if os.path.exists(file_path):
            success = plot_and_save_cv(file_path)
            results.append((os.path.basename(file_path), success))
        else:
            print(f"❌ File not found: {os.path.basename(file_path)}")
            results.append((os.path.basename(file_path), False))
    
    # Summary
    successful = sum(1 for _, success in results if success)
    print(f"\n{'='*50}")
    print(f"SUMMARY: {successful}/{len(results)} plots generated")
    print(f"{'='*50}")
    
    for filename, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {filename}")
    
    if successful > 0:
        print(f"\n📁 Check the 'plots' directory for generated images")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Plot specific file
        file_path = sys.argv[1]
        plot_and_save_cv(file_path)
    else:
        # Batch plot samples
        batch_plot_samples()

if __name__ == "__main__":
    main()