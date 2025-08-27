#!/usr/bin/env python3
"""
Enhanced V5 Peak Detector with Comprehensive Plotting
สร้างกราฟวิเคราะห์ผลการ detect peaks และ baseline แบบครบถ้วน
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime
from pathlib import Path
import logging

# Import Enhanced V5 detector
from enhanced_detector_v5 import EnhancedDetectorV5

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedDetectorV5WithPlot(EnhancedDetectorV5):
    """
    Enhanced V5 Detector with comprehensive plotting capabilities
    """
    
    def __init__(self):
        super().__init__()
        
        # สร้าง plots directory
        self.plots_dir = Path("plots")
        self.plots_dir.mkdir(exist_ok=True)
        
        # Set Thai-compatible font
        plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
        plt.rcParams['font.size'] = 10
        
    def plot_analysis_results(self, file_path, save_plot=True):
        """
        สร้างกราฟวิเคราะห์ผลการตรวจจับแบบครบถ้วน
        """
        logger.info(f"🎨 Creating V5 analysis plots for: {Path(file_path).name}")
        
        try:
            # โหลดข้อมูล
            df = pd.read_csv(file_path, skiprows=1)
            voltage = df['V'].values
            current = df['uA'].values
            
            # ทำการ detect
            results = self.detect_peaks_enhanced_v5(voltage, current)
            
            # สร้างกราฟ 6 panels
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            fig.suptitle(f'Enhanced V5 Analysis: {Path(file_path).stem}', fontsize=16, fontweight='bold')
            
            # Panel 1: CV with Peak Detection
            self._plot_cv_with_annotations(axes[0, 0], voltage, current, results)
            
            # Panel 2: Baseline Regions Detail
            self._plot_baseline_regions(axes[0, 1], voltage, current, results)
            
            # Panel 3: Peak Validation Analysis
            self._plot_peak_validation(axes[0, 2], voltage, current, results)
            
            # Panel 4: Detection Parameters
            self._plot_detection_parameters(axes[1, 0], results)
            
            # Panel 5: Signal Analysis
            self._plot_signal_analysis(axes[1, 1], voltage, current, results)
            
            # Panel 6: Analysis Summary
            self._plot_analysis_summary(axes[1, 2], results)
            
            plt.tight_layout()
            
            if save_plot:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{Path(file_path).stem}_v5_analysis_{timestamp}.png"
                save_path = self.plots_dir / filename
                
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"💾 Plot saved: {save_path}")
                
            plt.show()
            
            return results, save_path if save_plot else None
            
        except Exception as e:
            logger.error(f"❌ Plotting failed: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def _plot_cv_with_annotations(self, ax, voltage, current, results):
        """
        Panel 1: CV curve พร้อม peak และ baseline annotations
        """
        ax.plot(voltage, current, 'b-', linewidth=2, label='CV Data', alpha=0.8)
        
        # Plot valid peaks
        valid_peaks = results['peaks']
        ox_peaks = [p for p in valid_peaks if p['type'] == 'oxidation']
        red_peaks = [p for p in valid_peaks if p['type'] == 'reduction']
        
        if ox_peaks:
            ox_v = [p['voltage'] for p in ox_peaks]
            ox_i = [p['current'] for p in ox_peaks]
            ax.scatter(ox_v, ox_i, c='red', s=100, marker='^', 
                      label=f'OX Peaks ({len(ox_peaks)})', zorder=5)
        
        if red_peaks:
            red_v = [p['voltage'] for p in red_peaks]
            red_i = [p['current'] for p in red_peaks]
            ax.scatter(red_v, red_i, c='green', s=100, marker='v', 
                      label=f'RED Peaks ({len(red_peaks)})', zorder=5)
        
        # Plot rejected peaks
        rejected = results['rejected_peaks']
        if rejected:
            rej_v = [p['voltage'] for p in rejected]
            rej_i = [p['current'] for p in rejected]
            ax.scatter(rej_v, rej_i, c='orange', s=60, marker='x', 
                      label=f'Rejected ({len(rejected)})', zorder=4)
        
        # Plot baseline points
        baseline_indices = results['baseline_indices']
        if baseline_indices:
            baseline_v = voltage[baseline_indices]
            baseline_i = current[baseline_indices]
            ax.scatter(baseline_v, baseline_i, c='gray', s=20, alpha=0.6, 
                      label=f'Baseline ({len(baseline_indices)})')
        
        # Scan direction indicator
        scan_info = results['enhanced_results']['scan_sections']
        turning_point = scan_info['turning_point']
        ax.axvline(voltage[turning_point], color='purple', linestyle='--', alpha=0.7, 
                  label='Turning Point')
        
        ax.set_xlabel('Voltage (V)')
        ax.set_ylabel('Current (µA)')
        ax.set_title('CV Analysis with Peak Detection')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # Add performance indicator
        total_detected = results['enhanced_results']['total_detected']
        validation_passed = results['enhanced_results']['validation_passed']
        success_rate = (validation_passed / total_detected * 100) if total_detected > 0 else 0
        
        textstr = f'{success_rate:.0f}%'
        props = dict(boxstyle='round', facecolor='lightblue', alpha=0.8)
        ax.text(0.95, 0.95, textstr, transform=ax.transAxes, fontsize=14, 
                verticalalignment='top', horizontalalignment='right', bbox=props)
    
    def _plot_baseline_regions(self, ax, voltage, current, results):
        """
        Panel 2: Baseline regions แยกตาม voltage
        """
        ax.plot(voltage, current, 'b-', linewidth=1, alpha=0.5, label='CV Data')
        
        # Plot baseline regions with different colors
        baseline_regions = results['baseline_info']
        colors = ['red', 'green', 'blue', 'orange', 'purple']
        
        for i, region in enumerate(baseline_regions):
            indices = region['indices']
            color = colors[i % len(colors)]
            
            if indices:
                region_v = voltage[indices]
                region_i = current[indices]
                
                ax.scatter(region_v, region_i, c=color, s=30, alpha=0.7, 
                          label=f"{region['name']}: {region['mean_current']:.2f}±{region['std_current']:.2f}µA")
                
                # แสดง voltage range
                v_range = region['voltage_range']
                ax.axvspan(v_range[0], v_range[1], alpha=0.1, color=color)
        
        ax.set_xlabel('Voltage (V)')
        ax.set_ylabel('Current (µA)')
        ax.set_title('Baseline Regions by Voltage')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # Add baseline quality indicator
        quality = results['enhanced_results']['baseline_quality']
        textstr = f'Quality: {quality:.1%}'
        props = dict(boxstyle='round', facecolor='lightgreen', alpha=0.8)
        ax.text(0.95, 0.95, textstr, transform=ax.transAxes, fontsize=12, 
                verticalalignment='top', horizontalalignment='right', bbox=props)
    
    def _plot_peak_validation(self, ax, voltage, current, results):
        """
        Panel 3: Peak validation analysis
        """
        all_peaks = results['peaks'] + results['rejected_peaks']
        
        if not all_peaks:
            ax.text(0.5, 0.5, 'No peaks detected', transform=ax.transAxes, 
                   ha='center', va='center', fontsize=14)
            ax.set_title('Peak Validation Analysis')
            return
        
        # Scatter plot: confidence vs shape score
        valid_peaks = results['peaks']
        rejected_peaks = results['rejected_peaks']
        
        if valid_peaks:
            valid_conf = [p.get('confidence', 0) for p in valid_peaks]
            valid_shape = [p.get('shape_score', 0) for p in valid_peaks]
            ax.scatter(valid_conf, valid_shape, c='green', s=60, alpha=0.7, 
                      label=f'Valid ({len(valid_peaks)})')
        
        if rejected_peaks:
            rej_conf = [p.get('confidence', 0) for p in rejected_peaks]
            rej_shape = [p.get('shape_score', 0) for p in rejected_peaks]
            ax.scatter(rej_conf, rej_shape, c='red', s=60, alpha=0.7, 
                      label=f'Rejected ({len(rejected_peaks)})')
        
        # Add threshold lines
        ax.axvline(self.confidence_threshold, color='orange', linestyle='--', 
                  label=f'Min Confidence: {self.confidence_threshold}%')
        ax.axhline(0.5, color='purple', linestyle='--', alpha=0.7, 
                  label='Shape Threshold: 0.5')
        
        ax.set_xlabel('Confidence (%)')
        ax.set_ylabel('Shape Score')
        ax.set_title('Peak Validation Analysis')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 1)
    
    def _plot_detection_parameters(self, ax, results):
        """
        Panel 4: Detection parameters และ thresholds
        """
        thresholds = results['enhanced_results']['thresholds']
        adaptive_factors = results['enhanced_results']['adaptive_factors']
        
        params = {
            'Prominence': thresholds['prominence'],
            'Height': thresholds['height'],
            'Width': thresholds['width'],
            'SNR': thresholds['snr'],
            'Current Range': adaptive_factors['current_range'],
            'Baseline': thresholds['baseline']
        }
        
        # Bar chart
        param_names = list(params.keys())
        param_values = list(params.values())
        
        bars = ax.bar(param_names, param_values, color=['red', 'green', 'blue', 'orange', 'purple', 'brown'])
        
        # Add value labels on bars
        for bar, value in zip(bars, param_values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.2f}', ha='center', va='bottom', fontsize=8)
        
        ax.set_title('Detection Parameters')
        ax.set_ylabel('Value')
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        ax.grid(True, alpha=0.3)
    
    def _plot_signal_analysis(self, ax, voltage, current, results):
        """
        Panel 5: Signal characteristics analysis
        """
        # Calculate signal characteristics
        current_range = np.max(current) - np.min(current)
        current_std = np.std(current)
        snr = current_range / current_std if current_std > 0 else 0
        
        # Voltage distribution
        v_min, v_max = np.min(voltage), np.max(voltage)
        v_range = v_max - v_min
        
        # Current distribution by voltage regions
        n_regions = 5
        region_stats = []
        
        for i in range(n_regions):
            v_start = v_min + (i * v_range / n_regions)
            v_end = v_min + ((i + 1) * v_range / n_regions)
            
            if i == n_regions - 1:  # Last region
                mask = (voltage >= v_start) & (voltage <= v_end)
            else:
                mask = (voltage >= v_start) & (voltage < v_end)
            
            if np.sum(mask) > 0:
                region_current = current[mask]
                region_stats.append({
                    'voltage_range': f'{v_start:.2f}-{v_end:.2f}V',
                    'mean': np.mean(region_current),
                    'std': np.std(region_current),
                    'count': len(region_current)
                })
        
        # Plot current distribution
        regions = [stat['voltage_range'] for stat in region_stats]
        means = [stat['mean'] for stat in region_stats]
        stds = [stat['std'] for stat in region_stats]
        
        x_pos = np.arange(len(regions))
        bars = ax.bar(x_pos, means, yerr=stds, capsize=5, 
                     color=['red', 'green', 'blue', 'orange', 'purple'][:len(regions)])
        
        ax.set_title(f'Signal Analysis (SNR: {snr:.1f})')
        ax.set_xlabel('Voltage Regions')
        ax.set_ylabel('Current (µA)')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(regions, rotation=45, ha='right')
        ax.grid(True, alpha=0.3)
        
        # Add SNR indicator
        textstr = f'Range: {current_range:.2f}µA\nStd: {current_std:.2f}µA\nSNR: {snr:.1f}'
        props = dict(boxstyle='round', facecolor='lightyellow', alpha=0.8)
        ax.text(0.95, 0.95, textstr, transform=ax.transAxes, fontsize=9, 
                verticalalignment='top', horizontalalignment='right', bbox=props)
    
    def _plot_analysis_summary(self, ax, results):
        """
        Panel 6: Summary ของการวิเคราะห์
        """
        ax.axis('off')  # Turn off axis
        
        # Summary statistics
        peaks = results['peaks']
        rejected = results['rejected_peaks']
        baseline_info = results['baseline_info']
        enhanced_results = results['enhanced_results']
        
        ox_count = len([p for p in peaks if p['type'] == 'oxidation'])
        red_count = len([p for p in peaks if p['type'] == 'reduction'])
        
        summary_text = f"""
Enhanced V5 Analysis Summary

🎯 Peak Detection Results:
• Valid Peaks: {len(peaks)}
  - Oxidation: {ox_count}
  - Reduction: {red_count}
• Rejected Peaks: {len(rejected)}

📊 Baseline Analysis:
• Regions: {len(baseline_info)}
• Quality: {enhanced_results['baseline_quality']:.1%}
• Total Points: {len(results['baseline_indices'])}

⚙️ Algorithm Performance:
• Detection Rate: {enhanced_results['validation_passed']}/{enhanced_results['total_detected']}
• Success Rate: {(enhanced_results['validation_passed']/enhanced_results['total_detected']*100) if enhanced_results['total_detected'] > 0 else 0:.0f}%
• Version: {enhanced_results['version']}

🔧 Signal Characteristics:
• SNR: {enhanced_results['thresholds']['snr']:.1f}
• Current Range: {enhanced_results['adaptive_factors']['current_range']:.2f}µA
• Confidence Threshold: {self.confidence_threshold}%

📈 Improvements from V4:
• ✅ RED Peak Detection Fixed
• ✅ Multi-method Approach
• ✅ Adaptive Thresholding
• ✅ Voltage-based Baseline
        """
        
        ax.text(0.05, 0.95, summary_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', horizontalalignment='left',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8))
        
        ax.set_title('Analysis Summary', fontsize=12, fontweight='bold')

def test_v5_with_plots():
    """
    ทดสอบ Enhanced V5 พร้อมสร้างกราฟ
    """
    detector = EnhancedDetectorV5WithPlot()
    
    test_files = [
        "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_100mVpS_E5_scan_02.csv",
        "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_200mVpS_E2_scan_01.csv",
        "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_20mVpS_E1_scan_02.csv",
        "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_200mVpS_E4_scan_01.csv"
    ]
    
    results_summary = []
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\n{'='*70}")
            print(f"🎨 Creating V5 analysis plots for: {Path(file_path).name}")
            
            results, save_path = detector.plot_analysis_results(file_path, save_plot=True)
            
            if results:
                peaks = results['peaks']
                ox_count = len([p for p in peaks if p['type'] == 'oxidation'])
                red_count = len([p for p in peaks if p['type'] == 'reduction'])
                
                results_summary.append({
                    'file': Path(file_path).name,
                    'ox_peaks': ox_count,
                    'red_peaks': red_count,
                    'total_valid': len(peaks),
                    'rejected': len(results['rejected_peaks']),
                    'plot_saved': save_path
                })
                
                print(f"✅ Results: OX={ox_count}, RED={red_count}, Total={len(peaks)}")
                if save_path:
                    print(f"💾 Plot saved: {save_path.name}")
        else:
            print(f"❌ File not found: {file_path}")
    
    # Print summary
    print(f"\n{'='*70}")
    print("📊 V5 ANALYSIS SUMMARY:")
    print(f"{'='*70}")
    
    for result in results_summary:
        print(f"📁 {result['file']}")
        print(f"   OX: {result['ox_peaks']}, RED: {result['red_peaks']}, "
              f"Valid: {result['total_valid']}, Rejected: {result['rejected']}")
    
    print(f"\n🎯 Total plots created: {len(results_summary)}")
    print(f"📁 Plots saved in: plots/")

if __name__ == "__main__":
    test_v5_with_plots()
