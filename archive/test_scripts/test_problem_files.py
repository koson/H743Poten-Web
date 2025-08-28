#!/usr/bin/env python3
"""
Test Problematic Files - วิเคราะห์ไฟล์ที่มีปัญหาการตรวจจับ peak และ baseline
วิเคราะห์ปัญหาจากรูปที่แนบมา:

1. Pipot_Ferro_0_5mM_100mVpS_E1_scan_08.csv - baseline segment ไม่ถูก (ไม่อยู่ช่วงยาว)
2. Pipot_Ferro_0_5mM_200mVpS_E5_scan_05.csv - มี OX 2 อัน แต่ไม่มี RED, OX ที่ +0.7V ไม่ถูก
3. Pipot_Ferro_0_5mM_20mVpS_E1_scan_02.csv - ไม่เจอ peak และ baseline เลย
4. Pipot_Ferro_0_5mM_20mVpS_E2_scan_04.csv - ไม่เจอ segment ใช้ baseline เป็นศูนย์
5. Pipot_Ferro_0_5mM_400mVpS_E5_scan_06.csv - baseline segment อยู่ตรงที่ควรเป็น peak
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import json
import time

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import local modules
try:
    from src.routes.baseline_detector_v4 import cv_baseline_detector_v4
    from src.routes.peak_detection import detect_peaks_prominence, validate_peak_pre_detection
    from enhanced_peak_detector import EnhancedPeakDetector
    print("✅ Local modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Trying alternative imports...")
    try:
        from baseline_detector_v4 import cv_baseline_detector_v4
        from peak_detection import detect_peaks_prominence, validate_peak_pre_detection
        print("✅ Alternative imports successful")
    except ImportError as e2:
        print(f"❌ All imports failed: {e2}")
        sys.exit(1)

class ProblemFileAnalyzer:
    """วิเคราะห์ไฟล์ที่มีปัญหาการตรวจจับ"""
    
    def __init__(self):
        self.base_path = Path("Test_data/Stm32/Pipot_Ferro_0_5mM")
        self.problem_files = [
            {
                'file': 'Pipot_Ferro_0_5mM_100mVpS_E1_scan_08.csv',
                'issue': 'baseline segment ไม่ถูก (ไม่อยู่ช่วงยาว)',
                'expected': 'ควรมี baseline segment ที่ยาวกว่า'
            },
            {
                'file': 'Pipot_Ferro_0_5mM_200mVpS_E5_scan_05.csv', 
                'issue': 'มี OX 2 อัน แต่ไม่มี RED, OX ที่ +0.7V ไม่ถูก',
                'expected': 'ควรเจอ RED peak และ OX ที่ +0.7V ไม่ควรถูกตรวจจับ'
            },
            {
                'file': 'Pipot_Ferro_0_5mM_20mVpS_E1_scan_02.csv',
                'issue': 'ไม่เจอ peak และ baseline เลย',
                'expected': 'ควรเจอ peak และ baseline แม้สัญญาณอ่อน'
            },
            {
                'file': 'Pipot_Ferro_0_5mM_20mVpS_E2_scan_04.csv',
                'issue': 'ไม่เจอ segment ใช้ baseline เป็นศูนย์',
                'expected': 'ควรเจอ baseline segment ที่ถูกต้อง'
            },
            {
                'file': 'Pipot_Ferro_0_5mM_400mVpS_E5_scan_06.csv',
                'issue': 'baseline segment อยู่ตรงที่ควรเป็น peak',
                'expected': 'baseline ไม่ควรทับกับ peak'
            }
        ]
        
        self.results = []
        
    def load_csv_data(self, filepath):
        """โหลดข้อมูลจากไฟล์ CSV"""
        try:
            if not os.path.exists(filepath):
                print(f"❌ File not found: {filepath}")
                return None, None
                
            df = pd.read_csv(filepath)
            
            # ตรวจสอบชื่อคอลัมน์
            voltage_col = None
            current_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'volt' in col_lower or 'potential' in col_lower or col_lower == 'v':
                    voltage_col = col
                elif 'current' in col_lower or 'amp' in col_lower or col_lower == 'i':
                    current_col = col
            
            if voltage_col is None or current_col is None:
                print(f"❌ Could not find voltage/current columns in {filepath}")
                print(f"Available columns: {list(df.columns)}")
                return None, None
                
            voltage = df[voltage_col].values
            current = df[current_col].values
            
            # แปลงหน่วยถ้าจำเป็น
            if np.abs(current).max() < 1e-3:  # ถ้าอยู่ในหน่วย A แปลงเป็น µA
                current = current * 1e6
                print(f"📊 Converted current from A to µA")
            
            print(f"📈 Data loaded: {len(voltage)} points")
            print(f"   Voltage range: {voltage.min():.3f} to {voltage.max():.3f} V")
            print(f"   Current range: {current.min():.3f} to {current.max():.3f} µA")
            
            return voltage, current
            
        except Exception as e:
            print(f"❌ Error loading {filepath}: {e}")
            return None, None
    
    def analyze_baseline_detection(self, voltage, current, filename):
        """วิเคราะห์การตรวจจับ baseline"""
        print(f"\n🔍 Analyzing baseline detection for: {filename}")
        
        baseline_results = {}
        
        # Method 1: Voltage Window Detector V4
        try:
            print("   Testing cv_baseline_detector_v4...")
            baseline_forward, baseline_reverse, segment_info = cv_baseline_detector_v4(
                voltage, current, []  # ไม่มี peak regions
            )
            
            if baseline_forward is not None and baseline_reverse is not None:
                baseline_results['v4'] = {
                    'success': True,
                    'forward_len': len(baseline_forward),
                    'reverse_len': len(baseline_reverse),
                    'forward_range': (baseline_forward.min(), baseline_forward.max()),
                    'reverse_range': (baseline_reverse.min(), baseline_reverse.max()),
                    'segment_info': segment_info
                }
                print(f"   ✅ V4 Success: forward={len(baseline_forward)}, reverse={len(baseline_reverse)}")
            else:
                baseline_results['v4'] = {'success': False, 'error': 'No baseline detected'}
                print(f"   ❌ V4 Failed: No baseline detected")
                
        except Exception as e:
            baseline_results['v4'] = {'success': False, 'error': str(e)}
            print(f"   ❌ V4 Error: {e}")
        
        return baseline_results
    
    def analyze_peak_detection(self, voltage, current, filename):
        """วิเคราะห์การตรวจจับ peak"""
        print(f"\n🎯 Analyzing peak detection for: {filename}")
        
        peak_results = {}
        
        # Method 1: Prominence Method
        try:
            print("   Testing prominence method...")
            result = detect_peaks_prominence(voltage, current)
            
            if result and 'peaks' in result:
                peaks = result['peaks']
                ox_peaks = [p for p in peaks if p.get('type') == 'oxidation']
                red_peaks = [p for p in peaks if p.get('type') == 'reduction']
                
                peak_results['prominence'] = {
                    'success': True,
                    'total_peaks': len(peaks),
                    'ox_peaks': len(ox_peaks),
                    'red_peaks': len(red_peaks),
                    'peaks': peaks,
                    'baseline_info': result.get('baseline_info', {})
                }
                
                print(f"   ✅ Prominence Success: {len(peaks)} peaks (OX:{len(ox_peaks)}, RED:{len(red_peaks)})")
                
                # แสดงรายละเอียด peaks
                for i, peak in enumerate(peaks):
                    print(f"      Peak {i+1}: {peak['type'][:3].upper()} at {peak['voltage']:.3f}V, {peak['current']:.1f}µA")
                    
            else:
                peak_results['prominence'] = {'success': False, 'error': 'No peaks detected'}
                print(f"   ❌ Prominence Failed: No peaks detected")
                
        except Exception as e:
            peak_results['prominence'] = {'success': False, 'error': str(e)}
            print(f"   ❌ Prominence Error: {e}")
        
        # Method 2: Enhanced Detector
        try:
            print("   Testing enhanced detector...")
            detector = EnhancedPeakDetector()
            
            # ต้องมี baseline ก่อน
            baseline_forward, baseline_reverse, _ = cv_baseline_detector_v4(voltage, current, [])
            
            if baseline_forward is not None and baseline_reverse is not None:
                peaks = detector.detect_peaks_enhanced(voltage, current, baseline_forward, baseline_reverse)
                
                ox_peaks = [p for p in peaks if p.get('type') == 'oxidation']
                red_peaks = [p for p in peaks if p.get('type') == 'reduction']
                
                peak_results['enhanced'] = {
                    'success': True,
                    'total_peaks': len(peaks),
                    'ox_peaks': len(ox_peaks),
                    'red_peaks': len(red_peaks),
                    'peaks': peaks
                }
                
                print(f"   ✅ Enhanced Success: {len(peaks)} peaks (OX:{len(ox_peaks)}, RED:{len(red_peaks)})")
            else:
                peak_results['enhanced'] = {'success': False, 'error': 'No baseline for enhanced detection'}
                print(f"   ❌ Enhanced Failed: No baseline")
                
        except Exception as e:
            peak_results['enhanced'] = {'success': False, 'error': str(e)}
            print(f"   ❌ Enhanced Error: {e}")
        
        return peak_results
    
    def create_diagnostic_plot(self, voltage, current, baseline_results, peak_results, filename, issue):
        """สร้างกราฟวินิจฉัยปัญหา"""
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot 1: รวมทุกอย่าง
        ax1.plot(voltage, current, 'b-', linewidth=1, label='CV Data', alpha=0.7)
        
        # แสดง baseline ถ้ามี
        if baseline_results.get('v4', {}).get('success'):
            baseline_forward = baseline_results['v4'].get('baseline_forward')
            baseline_reverse = baseline_results['v4'].get('baseline_reverse')
            
            if baseline_forward is not None and baseline_reverse is not None:
                n_forward = len(baseline_forward)
                n_reverse = len(baseline_reverse)
                
                # สร้าง voltage array สำหรับ baseline
                voltage_forward = voltage[:n_forward] if len(voltage) >= n_forward else voltage
                voltage_reverse = voltage[n_forward:n_forward+n_reverse] if len(voltage) >= n_forward+n_reverse else voltage[n_forward:]
                
                if len(voltage_forward) == len(baseline_forward):
                    ax1.plot(voltage_forward, baseline_forward, 'r--', linewidth=2, label='Forward Baseline')
                if len(voltage_reverse) == len(baseline_reverse):
                    ax1.plot(voltage_reverse, baseline_reverse, 'g--', linewidth=2, label='Reverse Baseline')
        
        # แสดง peaks ถ้ามี
        for method in ['prominence', 'enhanced']:
            if peak_results.get(method, {}).get('success'):
                peaks = peak_results[method]['peaks']
                for peak in peaks:
                    marker = '*' if peak['type'] == 'oxidation' else 'v'
                    color = 'red' if peak['type'] == 'oxidation' else 'green'
                    ax1.plot(peak['voltage'], peak['current'], marker, markersize=10, 
                            color=color, label=f"{method.title()} {peak['type'][:3].upper()}")
        
        ax1.set_xlabel('Voltage (V)')
        ax1.set_ylabel('Current (µA)')
        ax1.set_title(f'Diagnostic Plot: {filename}\nIssue: {issue}')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: ซูมไปที่ช่วงที่น่าสนใจ
        # หาช่วงที่มี peak หรือ variation มากที่สุด
        current_variation = np.abs(np.gradient(current))
        high_variation_indices = np.where(current_variation > np.percentile(current_variation, 80))[0]
        
        if len(high_variation_indices) > 0:
            start_idx = max(0, high_variation_indices.min() - 50)
            end_idx = min(len(voltage), high_variation_indices.max() + 50)
            
            ax2.plot(voltage[start_idx:end_idx], current[start_idx:end_idx], 'b-', linewidth=1.5, label='CV Data (Zoomed)')
            
            # แสดง baseline ในช่วงซูม
            if baseline_results.get('v4', {}).get('success'):
                baseline_forward = baseline_results['v4'].get('baseline_forward')
                baseline_reverse = baseline_results['v4'].get('baseline_reverse')
                
                if baseline_forward is not None:
                    n_forward = len(baseline_forward)
                    if start_idx < n_forward and end_idx > start_idx:
                        zoom_forward_start = max(0, start_idx)
                        zoom_forward_end = min(n_forward, end_idx)
                        if zoom_forward_end > zoom_forward_start:
                            voltage_forward_zoom = voltage[zoom_forward_start:zoom_forward_end]
                            baseline_forward_zoom = baseline_forward[zoom_forward_start:zoom_forward_end]
                            ax2.plot(voltage_forward_zoom, baseline_forward_zoom, 'r--', linewidth=2, label='Forward Baseline')
                
                if baseline_reverse is not None:
                    n_reverse = len(baseline_reverse)
                    reverse_start_idx = len(baseline_forward) if baseline_forward is not None else 0
                    if start_idx < reverse_start_idx + n_reverse and end_idx > reverse_start_idx:
                        zoom_reverse_start = max(0, start_idx - reverse_start_idx)
                        zoom_reverse_end = min(n_reverse, end_idx - reverse_start_idx)
                        if zoom_reverse_end > zoom_reverse_start:
                            voltage_reverse_zoom = voltage[reverse_start_idx + zoom_reverse_start:reverse_start_idx + zoom_reverse_end]
                            baseline_reverse_zoom = baseline_reverse[zoom_reverse_start:zoom_reverse_end]
                            ax2.plot(voltage_reverse_zoom, baseline_reverse_zoom, 'g--', linewidth=2, label='Reverse Baseline')
            
            ax2.set_xlabel('Voltage (V)')
            ax2.set_ylabel('Current (µA)')
            ax2.set_title('Zoomed View - High Variation Region')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        else:
            ax2.text(0.5, 0.5, 'No significant variation found', 
                    transform=ax2.transAxes, ha='center', va='center', fontsize=12)
            ax2.set_title('Zoomed View - No Significant Variation')
        
        plt.tight_layout()
        
        # บันทึกกราฟ
        plot_filename = f"diagnostic_{filename.replace('.csv', '')}.png"
        plt.savefig(plot_filename, dpi=150, bbox_inches='tight')
        print(f"📊 Diagnostic plot saved: {plot_filename}")
        
        plt.show()
    
    def analyze_file(self, file_info):
        """วิเคราะห์ไฟล์หนึ่งไฟล์"""
        filename = file_info['file']
        issue = file_info['issue']
        expected = file_info['expected']
        
        print(f"\n{'='*80}")
        print(f"🔍 ANALYZING: {filename}")
        print(f"🚨 Known Issue: {issue}")
        print(f"💡 Expected: {expected}")
        print(f"{'='*80}")
        
        # โหลดข้อมูล
        filepath = self.base_path / filename
        voltage, current = self.load_csv_data(filepath)
        
        if voltage is None or current is None:
            print(f"❌ Skipping {filename} - failed to load data")
            return
        
        # วิเคราะห์ baseline
        baseline_results = self.analyze_baseline_detection(voltage, current, filename)
        
        # วิเคราะห์ peak
        peak_results = self.analyze_peak_detection(voltage, current, filename)
        
        # สร้างกราฟวินิจฉัย
        self.create_diagnostic_plot(voltage, current, baseline_results, peak_results, filename, issue)
        
        # เก็บผลลัพธ์
        result = {
            'filename': filename,
            'issue': issue,
            'expected': expected,
            'data_info': {
                'voltage_range': (float(voltage.min()), float(voltage.max())),
                'current_range': (float(current.min()), float(current.max())),
                'data_points': len(voltage)
            },
            'baseline_results': baseline_results,
            'peak_results': peak_results,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.results.append(result)
        
        return result
    
    def run_analysis(self):
        """รันการวิเคราะห์ทั้งหมด"""
        print("🚀 Starting Problem File Analysis")
        print(f"📁 Base path: {self.base_path}")
        print(f"📝 Analyzing {len(self.problem_files)} problematic files")
        
        for i, file_info in enumerate(self.problem_files, 1):
            print(f"\n📊 Progress: {i}/{len(self.problem_files)}")
            try:
                self.analyze_file(file_info)
            except Exception as e:
                print(f"❌ Error analyzing {file_info['file']}: {e}")
                continue
        
        # สรุปผลการวิเคราะห์
        self.generate_summary_report()
    
    def generate_summary_report(self):
        """สร้างรายงานสรุป"""
        print(f"\n{'='*80}")
        print("📋 ANALYSIS SUMMARY REPORT")
        print(f"{'='*80}")
        
        baseline_success = 0
        peak_success = 0
        
        for result in self.results:
            filename = result['filename']
            issue = result['issue']
            
            print(f"\n📄 {filename}")
            print(f"   🚨 Issue: {issue}")
            
            # Baseline results
            if result['baseline_results'].get('v4', {}).get('success'):
                baseline_success += 1
                baseline_info = result['baseline_results']['v4']
                print(f"   ✅ Baseline: SUCCESS (forward:{baseline_info['forward_len']}, reverse:{baseline_info['reverse_len']})")
            else:
                print(f"   ❌ Baseline: FAILED")
            
            # Peak results
            peak_found = False
            for method in ['prominence', 'enhanced']:
                if result['peak_results'].get(method, {}).get('success'):
                    peak_info = result['peak_results'][method]
                    print(f"   ✅ Peaks ({method}): {peak_info['total_peaks']} total (OX:{peak_info['ox_peaks']}, RED:{peak_info['red_peaks']})")
                    peak_found = True
                    break
            
            if peak_found:
                peak_success += 1
            else:
                print(f"   ❌ Peaks: NO METHOD SUCCESSFUL")
        
        print(f"\n📊 Overall Statistics:")
        print(f"   Files analyzed: {len(self.results)}")
        print(f"   Baseline detection success: {baseline_success}/{len(self.results)} ({baseline_success/len(self.results)*100:.1f}%)")
        print(f"   Peak detection success: {peak_success}/{len(self.results)} ({peak_success/len(self.results)*100:.1f}%)")
        
        # บันทึกรายงานเป็น JSON
        report_filename = f"problem_files_analysis_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Full report saved: {report_filename}")

def main():
    """Main function"""
    analyzer = ProblemFileAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
