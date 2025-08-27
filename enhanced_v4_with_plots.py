#!/usr/bin/env python3
"""
Enhanced Detector V4 with Plotting Capability
สำหรับการทดสอบและวิเคราะห์ผลลัพธ์แบบ visual
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime
import logging

# Import Enhanced V4
from enhanced_detector_v4 import EnhancedDetectorV4

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedDetectorV4WithPlot(EnhancedDetectorV4):
    """
    Enhanced V4 พร้อมฟังก์ชัน plotting
    """
    
    def __init__(self):
        super().__init__()
        self.plot_counter = 0
        
    def plot_analysis_results(self, voltage, current, results, filename="", save_path="plots"):
        """
        Plot comprehensive analysis results and save as PNG
        """
        self.plot_counter += 1
        
        # สร้างโฟลเดอร์ plots ถ้ายังไม่มี
        os.makedirs(save_path, exist_ok=True)
        
        # สร้าง figure ขนาดใหญ่
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Enhanced V4 Analysis: {os.path.basename(filename)}', fontsize=16, fontweight='bold')
        
        # Plot 1: CV Data with Peaks and Baseline
        self._plot_cv_with_annotations(ax1, voltage, current, results)
        
        # Plot 2: Baseline Segments Detail
        self._plot_baseline_segments(ax2, voltage, current, results)
        
        # Plot 3: Peak Detection Parameters
        self._plot_detection_parameters(ax3, voltage, current, results)
        
        # Plot 4: Analysis Summary
        self._plot_analysis_summary(ax4, results)
        
        plt.tight_layout()
        
        # สร้างชื่อไฟล์
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(filename))[0] if filename else f"analysis_{self.plot_counter}"
        plot_filename = f"{base_name}_v4_analysis_{timestamp}.png"
        plot_path = os.path.join(save_path, plot_filename)
        
        # บันทึกไฟล์
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()  # ปิดเพื่อประหยัด memory
        
        print(f"📊 Plot saved: {plot_path}")
        return plot_path
    
    def _plot_cv_with_annotations(self, ax, voltage, current, results):
        """
        Plot CV data พร้อม peaks และ baseline annotations
        """
        ax.plot(voltage, current, 'b-', linewidth=2, label='CV Data', alpha=0.8)
        
        # Plot peaks
        peaks = results.get('peaks', [])
        for peak in peaks:
            color = 'red' if peak['type'] == 'oxidation' else 'green'
            marker = '^' if peak['type'] == 'oxidation' else 'v'  # ใช้ ^ และ v แทน unicode
            ax.scatter(peak['voltage'], peak['current'], 
                      c=color, s=100, marker=marker, 
                      label=f"{peak['type'][:3].upper()} Peak" if peak == peaks[0] or peak['type'] != peaks[0]['type'] else "",
                      zorder=5)
            
            # Confidence annotation
            ax.annotate(f"{peak.get('confidence', 0):.0f}%", 
                       (peak['voltage'], peak['current']),
                       xytext=(10, 10), textcoords='offset points',
                       fontsize=9, ha='left',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.3))
        
        # Plot baseline points
        baseline_indices = results.get('baseline_indices', [])
        if baseline_indices:
            baseline_v = voltage[baseline_indices]
            baseline_i = current[baseline_indices]
            ax.scatter(baseline_v, baseline_i, c='orange', s=20, alpha=0.6, label='Baseline Points')
        
        # Scan direction annotation
        scan_sections = results.get('enhanced_results', {}).get('scan_sections', {})
        turning_point = scan_sections.get('turning_point')
        if turning_point:
            ax.axvline(voltage[turning_point], color='purple', linestyle='--', alpha=0.5, label='Turning Point')
        
        ax.set_xlabel('Voltage (V)')
        ax.set_ylabel('Current (µA)')
        ax.set_title('CV Analysis with Peak Detection')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
    
    def _plot_baseline_segments(self, ax, voltage, current, results):
        """
        Plot รายละเอียด baseline segments
        """
        ax.plot(voltage, current, 'b-', linewidth=1, alpha=0.6, label='CV Data')
        
        # Plot baseline regions
        baseline_info = results.get('baseline_info', [])
        colors = ['red', 'green', 'blue', 'orange', 'purple']
        
        for i, region in enumerate(baseline_info):
            indices = region['indices']
            color = colors[i % len(colors)]
            
            # Plot baseline points
            region_v = voltage[indices]
            region_i = current[indices]
            ax.scatter(region_v, region_i, c=color, s=30, alpha=0.8, 
                      label=f"{region['name']} Region ({region['count']} pts)")
            
            # Plot mean line
            mean_current = region['mean_current']
            std_current = region['std_current']
            v_min, v_max = np.min(region_v), np.max(region_v)
            
            ax.hlines(mean_current, v_min, v_max, colors=color, linestyles='-', alpha=0.8, linewidth=2)
            ax.fill_between([v_min, v_max], 
                           [mean_current - std_current] * 2,
                           [mean_current + std_current] * 2,
                           color=color, alpha=0.2)
            
            # Region statistics
            ax.text(np.mean(region_v), mean_current + std_current + np.std(current) * 0.1,
                   f'{mean_current:.2f}±{std_current:.2f}µA',
                   ha='center', va='bottom', fontsize=8,
                   bbox=dict(boxstyle='round,pad=0.2', facecolor=color, alpha=0.3))
        
        ax.set_xlabel('Voltage (V)')
        ax.set_ylabel('Current (µA)')
        ax.set_title('Baseline Segment Analysis')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    
    def _plot_detection_parameters(self, ax, voltage, current, results):
        """
        Plot detection parameters และ thresholds
        """
        enhanced_results = results.get('enhanced_results', {})
        thresholds = enhanced_results.get('thresholds', {})
        
        # Plot current distribution
        ax.hist(current, bins=30, alpha=0.6, color='lightblue', density=True, label='Current Distribution')
        
        # Plot threshold lines
        if 'baseline' in thresholds:
            baseline = thresholds['baseline']
            ax.axvline(baseline, color='red', linestyle='-', linewidth=2, label=f'Baseline: {baseline:.2f}µA')
        
        if 'prominence' in thresholds:
            prominence = thresholds['prominence']
            if 'baseline' in thresholds:
                ax.axvline(baseline + prominence, color='orange', linestyle='--', 
                          label=f'OX Threshold: +{prominence:.2f}µA')
                ax.axvline(baseline - prominence, color='green', linestyle='--', 
                          label=f'RED Threshold: -{prominence:.2f}µA')
        
        # Statistics text
        stats_text = []
        if 'snr' in thresholds:
            stats_text.append(f"SNR: {thresholds['snr']:.1f}")
        if 'width' in thresholds:
            stats_text.append(f"Width: {thresholds['width']}")
        
        validation_passed = enhanced_results.get('validation_passed', 0)
        total_detected = enhanced_results.get('total_detected', 0)
        stats_text.append(f"Valid/Total: {validation_passed}/{total_detected}")
        
        ax.text(0.05, 0.95, '\n'.join(stats_text), transform=ax.transAxes,
               fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='wheat', alpha=0.8))
        
        ax.set_xlabel('Current (µA)')
        ax.set_ylabel('Density')
        ax.set_title('Detection Parameters & Thresholds')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
    
    def _plot_analysis_summary(self, ax, results):
        """
        Plot สรุปผลการวิเคราะห์
        """
        ax.axis('off')  # ไม่แสดง axes
        
        # สร้างข้อมูลสรุป
        peaks = results.get('peaks', [])
        rejected_peaks = results.get('rejected_peaks', [])
        baseline_info = results.get('baseline_info', [])
        enhanced_results = results.get('enhanced_results', {})
        
        ox_peaks = [p for p in peaks if p['type'] == 'oxidation']
        red_peaks = [p for p in peaks if p['type'] == 'reduction']
        
        # สร้างตาราง summary
        summary_text = f"""
🎯 ENHANCED V4 ANALYSIS SUMMARY

📈 Peak Detection Results:
   ✅ Valid Peaks: {len(peaks)}
      - Oxidation: {len(ox_peaks)}
      - Reduction: {len(red_peaks)}
   ❌ Rejected: {len(rejected_peaks)}

📏 Baseline Analysis:
   ✅ Regions Found: {len(baseline_info)}
   📊 Total Points: {len(results.get('baseline_indices', []))}
   🎯 Quality: {enhanced_results.get('baseline_quality', 0):.1%}

🔧 Detection Parameters:
   📡 SNR: {enhanced_results.get('thresholds', {}).get('snr', 'N/A')}
   📏 Prominence: {enhanced_results.get('thresholds', {}).get('prominence', 'N/A'):.3f}
   ⚡ Width: {enhanced_results.get('thresholds', {}).get('width', 'N/A')}

🔍 Peak Details:"""

        # เพิ่มรายละเอียด peaks
        for i, peak in enumerate(peaks):
            conf = peak.get('confidence', 0)
            summary_text += f"\n   Peak {i+1}: {peak['type'][:3].upper()} at {peak['voltage']:.3f}V, {peak['current']:.2f}µA (conf: {conf:.0f}%)"
        
        # แสดงปัญหาจาก rejected peaks
        if rejected_peaks:
            summary_text += f"\n\n❌ Rejection Reasons:"
            for i, peak in enumerate(rejected_peaks[:3]):  # แสดงแค่ 3 ตัวแรก
                reason = peak.get('rejection_reason', 'Unknown')
                summary_text += f"\n   {peak['type'][:3].upper()} {peak['voltage']:.3f}V: {reason[:50]}..."
        
        # แสดงข้อความ
        ax.text(0.05, 0.95, summary_text, transform=ax.transAxes,
               fontsize=11, verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle='round,pad=1', facecolor='lightgray', alpha=0.8))

def test_files_with_plots(test_files, detector=None):
    """
    ทดสอบไฟล์หลายๆ ไฟล์พร้อมสร้าง plots
    """
    if detector is None:
        detector = EnhancedDetectorV4WithPlot()
    
    print("🎨 Enhanced V4 Testing with Visual Analysis")
    print("=" * 60)
    
    for i, test_file in enumerate(test_files):
        if not os.path.exists(test_file):
            print(f"❌ File not found: {test_file}")
            continue
            
        print(f"\n🧪 Test {i+1}/{len(test_files)}: {os.path.basename(test_file)}")
        
        try:
            # โหลดข้อมูล
            df = pd.read_csv(test_file, skiprows=1)
            voltage = df['V'].values
            current = df['uA'].values
            
            print(f"📊 Data: {len(voltage)} points")
            print(f"🔌 Voltage: {voltage.min():.3f} to {voltage.max():.3f}V")
            print(f"⚡ Current: {current.min():.3f} to {current.max():.3f}µA")
            
            # ทำการ detect
            results = detector.detect_peaks_enhanced_v4(voltage, current)
            
            # สร้าง plot
            plot_path = detector.plot_analysis_results(voltage, current, results, test_file)
            
            # สรุปผลลัพธ์
            peaks = results['peaks']
            ox_count = len([p for p in peaks if p['type'] == 'oxidation'])
            red_count = len([p for p in peaks if p['type'] == 'reduction'])
            
            print(f"🎯 Results: {len(peaks)} peaks (OX:{ox_count}, RED:{red_count})")
            print(f"📊 Plot saved: {os.path.basename(plot_path)}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

def main():
    """
    Main testing function
    """
    # ไฟล์ทดสอบจากรูปที่แนบมา
    test_files = [
        "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_100mVpS_E5_scan_02.csv",
        "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_200mVpS_E2_scan_01.csv", 
        "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_20mVpS_E1_scan_02.csv",
        "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_200mVpS_E4_scan_01.csv"
    ]
    
    # หาไฟล์ที่มีอยู่จริง
    existing_files = [f for f in test_files if os.path.exists(f)]
    
    if not existing_files:
        print("❌ No test files found. Searching for available files...")
        # หาไฟล์ .csv ที่มี
        import glob
        csv_files = glob.glob("Test_data/**/*.csv", recursive=True)
        existing_files = csv_files[:5]  # เอาแค่ 5 ไฟล์แรก
    
    if existing_files:
        detector = EnhancedDetectorV4WithPlot()
        test_files_with_plots(existing_files, detector)
        
        print(f"\n🎉 Testing completed!")
        print(f"📁 Check 'plots' folder for analysis results")
    else:
        print("❌ No CSV files found for testing")

if __name__ == "__main__":
    main()
