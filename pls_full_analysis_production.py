#!/usr/bin/env python3
"""
Full PLS Analysis: Palmsens (Reference) vs STM32 (Target)
Production Version - ข้าม scan_01, รองรับข้อมูลขนาดใหญ่
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cross_decomposition import PLSRegression
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import os
import glob
import re
from pathlib import Path
import time
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

class PLSAnalysisFull:
    def __init__(self, max_files_per_device=100):
        """
        Full PLS Analysis
        max_files_per_device: จำกัดจำนวนไฟล์เพื่อป้องกัน memory overflow
        """
        self.max_files_per_device = max_files_per_device
        self.results_dir = Path("pls_full_results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Statistics
        self.stats = {
            'palmsens': {'total': 0, 'success': 0, 'failed': 0, 'skipped_scan01': 0},
            'stm32': {'total': 0, 'success': 0, 'failed': 0, 'skipped_scan01': 0},
            'processing_time': 0
        }
        
        try:
            from enhanced_detector_v4_improved import EnhancedDetectorV4Improved
            self.detector = EnhancedDetectorV4Improved(confidence_threshold=25.0)
            print("✅ Enhanced V4 Improved พร้อมใช้งาน")
        except ImportError:
            print("❌ Enhanced V4 Improved ไม่พร้อมใช้งาน")
            self.detector = None
    
    def should_skip_file(self, filename):
        """ตรวจสอบว่าควรข้ามไฟล์หรือไม่ (scan_01)"""
        return 'scan_01' in filename.lower()
    
    def extract_metadata(self, filename):
        """แยกข้อมูล metadata จากชื่อไฟล์"""
        filename_only = Path(filename).stem
        
        # Patterns สำหรับ Palmsens และ STM32
        patterns = [
            # Palmsens: Palmsens_0.5mM_CV_100mVpS_E1_scan_02.csv
            r'(\w+)_([0-9.]+mM)_CV_([0-9.]+mVpS)_(\w+)_scan_(\d+)',
            # STM32: Pipot_Ferro_0_5mM_100mVpS_E1_scan_02.csv  
            r'(\w+)_(\w+)_([0-9_]+mM)_([0-9.]+mVpS)_(\w+)_scan_(\d+)',
            # Backup patterns
            r'(\w+)_([0-9.]+)mM_CV_([0-9.]+)mVs_(\w+)_scan_(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename_only)
            if match:
                groups = match.groups()
                
                if len(groups) >= 5:
                    # Handle different patterns
                    if 'Palmsens' in filename_only:
                        device = groups[0]
                        concentration_str = groups[1]
                        scan_rate_str = groups[2]
                        electrode = groups[3]
                        scan_number = groups[4]
                    elif 'Pipot' in filename_only:
                        device = f"{groups[0]}_{groups[1]}"  # Pipot_Ferro
                        concentration_str = groups[2].replace('_', '.')  # 0_5mM -> 0.5mM
                        scan_rate_str = groups[3]
                        electrode = groups[4]
                        scan_number = groups[5]
                    else:
                        device = groups[0]
                        concentration_str = groups[1]
                        scan_rate_str = groups[2]
                        electrode = groups[3]
                        scan_number = groups[4]
                    
                    # Extract numeric values
                    conc_match = re.search(r'([0-9.]+)', concentration_str)
                    concentration = float(conc_match.group(1)) if conc_match else 0.0
                    
                    rate_match = re.search(r'([0-9.]+)', scan_rate_str)
                    scan_rate = float(rate_match.group(1)) if rate_match else 0.0
                    
                    return {
                        'device': device,
                        'concentration': concentration,
                        'scan_rate': scan_rate,
                        'electrode': electrode,
                        'scan_number': int(scan_number),
                        'filename': filename_only
                    }
        
        # Fallback
        return {
            'device': 'unknown',
            'concentration': 0.0,
            'scan_rate': 0.0,
            'electrode': 'unknown',
            'scan_number': 1,
            'filename': filename_only
        }
    
    def analyze_cv_file(self, filepath):
        """วิเคราะห์ไฟล์ CV ด้วย Enhanced V4 Improved"""
        try:
            # โหลดไฟล์ (skip 2 header rows)
            data = pd.read_csv(filepath, skiprows=2, names=['voltage', 'current'])
            
            if data.empty or len(data) < 10:
                return None
            
            # เตรียมข้อมูลสำหรับ Enhanced V4 Improved
            cv_data = {
                'voltage': data['voltage'].tolist(),
                'current': data['current'].tolist()
            }
            
            # วิเคราะห์ด้วย Enhanced V4 Improved
            results = self.detector.analyze_cv_data(cv_data)
            
            if not results or not isinstance(results, dict):
                return None
            
            # แยก peaks
            all_peaks = results.get('peaks', [])
            if not all_peaks:
                return None
            
            anodic_peaks = [p for p in all_peaks if p.get('type') == 'oxidation']
            cathodic_peaks = [p for p in all_peaks if p.get('type') == 'reduction']
            
            # ตรวจสอบว่ามี peak ครบทั้ง 2 ด้าน
            if len(anodic_peaks) == 0 or len(cathodic_peaks) == 0:
                return None
            
            # Extract metadata
            metadata = self.extract_metadata(filepath.name)
            
            # Extract peak features
            ox_peak = anodic_peaks[0]  # ใช้ peak แรก
            red_peak = cathodic_peaks[0]  # ใช้ peak แรก
            
            peak_features = {
                'ox_voltage': ox_peak.get('voltage', 0),
                'ox_current': ox_peak.get('current', 0),
                'ox_confidence': ox_peak.get('confidence', 0),
                'red_voltage': red_peak.get('voltage', 0),
                'red_current': red_peak.get('current', 0),
                'red_confidence': red_peak.get('confidence', 0),
                
                # Derived features
                'peak_separation_voltage': abs(ox_peak.get('voltage', 0) - red_peak.get('voltage', 0)),
                'peak_separation_current': abs(ox_peak.get('current', 0) - red_peak.get('current', 0)),
                'current_ratio': ox_peak.get('current', 0) / red_peak.get('current', 0) if red_peak.get('current', 0) != 0 else 0,
                'midpoint_potential': (ox_peak.get('voltage', 0) + red_peak.get('voltage', 0)) / 2
            }
            
            return {
                'filename': filepath.name,
                'metadata': metadata,
                'peak_features': peak_features,
                'has_both_peaks': True,
                'peak_count': len(all_peaks)
            }
            
        except Exception as e:
            return None
    
    def collect_device_data(self, data_dir, device_name):
        """รวบรวมข้อมูลจากอุปกรณ์หนึ่ง"""
        print(f"📁 รวบรวมข้อมูล {device_name} จาก {data_dir}...")
        
        if not os.path.exists(data_dir):
            print(f"❌ ไม่พบไดเรกทอรี: {data_dir}")
            return []
        
        # หาไฟล์ทั้งหมด
        pattern = os.path.join(data_dir, "**", "*.csv")
        all_files = [Path(f) for f in glob.glob(pattern, recursive=True)]
        
        # กรองไฟล์ (ข้าม scan_01)
        valid_files = [f for f in all_files if not self.should_skip_file(str(f))]
        skipped_files = len(all_files) - len(valid_files)
        
        # จำกัดจำนวนไฟล์
        if len(valid_files) > self.max_files_per_device:
            print(f"⚠️ จำกัดไฟล์ที่ {self.max_files_per_device} ไฟล์ (จาก {len(valid_files)})")
            valid_files = valid_files[:self.max_files_per_device]
        
        print(f"📊 ไฟล์ทั้งหมด: {len(all_files)}, ข้าม scan_01: {skipped_files}, ใช้งาน: {len(valid_files)}")
        
        # อัปเดตสถิติ
        device_key = device_name.lower().replace(' ', '')
        self.stats[device_key]['total'] = len(valid_files)
        self.stats[device_key]['skipped_scan01'] = skipped_files
        
        # วิเคราะห์ไฟล์
        valid_data = []
        
        for i, filepath in enumerate(valid_files):
            if i % 50 == 0:  # แสดงผลทุก 50 ไฟล์
                print(f"  [{i+1:4d}/{len(valid_files)}] กำลังประมวลผล...")
            
            result = self.analyze_cv_file(filepath)
            
            if result and result['has_both_peaks']:
                valid_data.append(result)
                self.stats[device_key]['success'] += 1
            else:
                self.stats[device_key]['failed'] += 1
        
        success_rate = (self.stats[device_key]['success'] / len(valid_files) * 100) if valid_files else 0
        print(f"✅ {device_name}: {self.stats[device_key]['success']}/{len(valid_files)} สำเร็จ ({success_rate:.1f}%)")
        
        return valid_data
    
    def run_full_analysis(self):
        """รัน Full PLS Analysis"""
        print("🚀 Full PLS Analysis: Palmsens (REF) vs STM32 (TARGET)")
        print("⚠️ ข้าม scan_01 เพราะระบบยังไม่เสถียร")
        print(f"📊 จำกัดไฟล์สูงสุด: {self.max_files_per_device} ไฟล์ต่ออุปกรณ์")
        print("=" * 70)
        
        if not self.detector:
            print("❌ Enhanced V4 Improved ไม่พร้อมใช้งาน")
            return
        
        start_time = time.time()
        
        # รวบรวมข้อมูล Palmsens (Reference)
        palmsens_data = self.collect_device_data("Test_data/Palmsens", "Palmsens")
        
        # รวบรวมข้อมูล STM32 (Target)
        stm32_data = self.collect_device_data("Test_data/Stm32", "STM32")
        
        self.stats['processing_time'] = time.time() - start_time
        
        print(f"\n⏱️ เวลาประมวลผล: {self.stats['processing_time']:.2f} วินาที")
        
        if not palmsens_data:
            print("❌ ไม่มีข้อมูล Palmsens ที่ใช้ได้")
            return
        
        if not stm32_data:
            print("❌ ไม่มีข้อมูล STM32 ที่ใช้ได้")
            return
        
        # สร้าง PLS analysis
        self.create_pls_analysis(palmsens_data, stm32_data)
        
        # สร้างรายงาน
        self.create_comprehensive_report(palmsens_data, stm32_data)
        
        print(f"\n🎉 Full PLS Analysis เสร็จสิ้น!")
        print(f"📁 ผลลัพธ์บันทึกใน: {self.results_dir}")
    
    def create_pls_analysis(self, palmsens_data, stm32_data):
        """สร้าง PLS analysis และ visualization"""
        print(f"\n📈 สร้าง PLS Analysis...")
        
        # สร้าง DataFrames
        palmsens_df = self.create_dataframe(palmsens_data, "Palmsens")
        stm32_df = self.create_dataframe(stm32_data, "STM32")
        
        print(f"📊 Palmsens DataFrame: {len(palmsens_df)} samples")
        print(f"📊 STM32 DataFrame: {len(stm32_df)} samples")
        
        # บันทึก DataFrames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        palmsens_path = self.results_dir / f"palmsens_data_{timestamp}.csv"
        stm32_path = self.results_dir / f"stm32_data_{timestamp}.csv"
        
        palmsens_df.to_csv(palmsens_path, index=False)
        stm32_df.to_csv(stm32_path, index=False)
        
        print(f"📄 บันทึก Palmsens data: {palmsens_path.name}")
        print(f"📄 บันทึก STM32 data: {stm32_path.name}")
        
        # Export LabPlot2 format
        self.export_labplot2_format(palmsens_data, stm32_data, timestamp)
        
        # สร้าง visualization
        self.create_visualization(palmsens_df, stm32_df, timestamp)
    
    def create_dataframe(self, data_list, device_name):
        """สร้าง DataFrame จากข้อมูล"""
        rows = []
        for data in data_list:
            row = data['metadata'].copy()
            row.update(data['peak_features'])
            row['device'] = device_name
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def export_labplot2_format(self, palmsens_data, stm32_data, timestamp):
        """Export ข้อมูลในรูปแบบ LabPlot2"""
        print(f"📊 Export LabPlot2 format...")
        
        # Combined data
        combined_data = []
        
        # Add Palmsens data
        for data in palmsens_data:
            row = {
                'device': 'Palmsens',
                'device_code': 0,
                **data['metadata'],
                **data['peak_features']
            }
            combined_data.append(row)
        
        # Add STM32 data
        for data in stm32_data:
            row = {
                'device': 'STM32', 
                'device_code': 1,
                **data['metadata'],
                **data['peak_features']
            }
            combined_data.append(row)
        
        df = pd.DataFrame(combined_data)
        
        # LabPlot2 compatible file
        labplot_path = self.results_dir / f"pls_labplot2_data_{timestamp}.csv"
        
        with open(labplot_path, 'w', encoding='utf-8') as f:
            # Metadata header
            f.write("# LabPlot2 Data File - PLS Analysis\n")
            f.write("# Palmsens (Reference) vs STM32 (Target) Potentiostat Comparison\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write("# Method: Enhanced Detector V4 Improved\n")
            f.write("# Note: scan_01 files excluded (system not stable)\n")
            f.write(f"# Palmsens samples: {len(palmsens_data)}\n")
            f.write(f"# STM32 samples: {len(stm32_data)}\n")
            f.write("#\n")
            f.write("# Columns:\n")
            for col in df.columns:
                f.write(f"# {col}: {self.get_column_description(col)}\n")
            f.write("#\n")
            
            # CSV data
            df.to_csv(f, index=False)
        
        print(f"📊 LabPlot2 file: {labplot_path.name}")
        print(f"📈 Total samples: {len(df)} ({len(palmsens_data)} Palmsens + {len(stm32_data)} STM32)")
        
        return labplot_path
    
    def get_column_description(self, col):
        """คำอธิบายคอลัมน์สำหรับ LabPlot2"""
        descriptions = {
            'device': 'Device name (Palmsens/STM32)',
            'device_code': 'Numeric device code (0=Palmsens, 1=STM32)',
            'concentration': 'Ferrocyanide concentration (mM)',
            'scan_rate': 'CV scan rate (mV/s)',
            'ox_voltage': 'Oxidation peak voltage (V)',
            'ox_current': 'Oxidation peak current (µA)',
            'red_voltage': 'Reduction peak voltage (V)',
            'red_current': 'Reduction peak current (µA)',
            'peak_separation_voltage': 'Peak voltage separation (V)',
            'current_ratio': 'Anodic/cathodic current ratio',
            'midpoint_potential': 'Midpoint potential (V)',
        }
        return descriptions.get(col, 'Data column')
    
    def create_visualization(self, palmsens_df, stm32_df, timestamp):
        """สร้าง visualization"""
        print(f"📊 สร้าง visualization...")
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        
        # Plot 1: Oxidation voltage comparison
        ax1 = axes[0, 0]
        ax1.scatter(palmsens_df['concentration'], palmsens_df['ox_voltage'], 
                   color='blue', alpha=0.6, label='Palmsens', s=20)
        ax1.scatter(stm32_df['concentration'], stm32_df['ox_voltage'], 
                   color='red', alpha=0.6, label='STM32', s=20)
        ax1.set_xlabel('Concentration (mM)')
        ax1.set_ylabel('Oxidation Voltage (V)')
        ax1.set_title('Oxidation Peak Voltage vs Concentration')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Reduction voltage comparison
        ax2 = axes[0, 1]
        ax2.scatter(palmsens_df['concentration'], palmsens_df['red_voltage'], 
                   color='blue', alpha=0.6, label='Palmsens', s=20)
        ax2.scatter(stm32_df['concentration'], stm32_df['red_voltage'], 
                   color='red', alpha=0.6, label='STM32', s=20)
        ax2.set_xlabel('Concentration (mM)')
        ax2.set_ylabel('Reduction Voltage (V)')
        ax2.set_title('Reduction Peak Voltage vs Concentration')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Peak separation comparison
        ax3 = axes[0, 2]
        ax3.scatter(palmsens_df['concentration'], palmsens_df['peak_separation_voltage'], 
                   color='blue', alpha=0.6, label='Palmsens', s=20)
        ax3.scatter(stm32_df['concentration'], stm32_df['peak_separation_voltage'], 
                   color='red', alpha=0.6, label='STM32', s=20)
        ax3.set_xlabel('Concentration (mM)')
        ax3.set_ylabel('Peak Separation (V)')
        ax3.set_title('Peak Separation vs Concentration')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Correlation plot (ox voltage)
        ax4 = axes[1, 0]
        # Match by concentration for correlation
        common_concentrations = set(palmsens_df['concentration']) & set(stm32_df['concentration'])
        if common_concentrations:
            for conc in sorted(common_concentrations):
                pal_vals = palmsens_df[palmsens_df['concentration'] == conc]['ox_voltage']
                stm32_vals = stm32_df[stm32_df['concentration'] == conc]['ox_voltage']
                
                min_len = min(len(pal_vals), len(stm32_vals))
                if min_len > 0:
                    ax4.scatter(pal_vals.iloc[:min_len], stm32_vals.iloc[:min_len], 
                               alpha=0.6, s=20, label=f'{conc} mM')
            
            # Perfect correlation line
            min_val = min(ax4.get_xlim()[0], ax4.get_ylim()[0])
            max_val = max(ax4.get_xlim()[1], ax4.get_ylim()[1])
            ax4.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, label='y=x')
        
        ax4.set_xlabel('Palmsens Ox Voltage (V)')
        ax4.set_ylabel('STM32 Ox Voltage (V)')
        ax4.set_title('STM32 vs Palmsens Correlation (Ox)')
        ax4.grid(True, alpha=0.3)
        
        # Plot 5: Statistical summary
        ax5 = axes[1, 1]
        devices = ['Palmsens', 'STM32']
        ox_means = [palmsens_df['ox_voltage'].mean(), stm32_df['ox_voltage'].mean()]
        red_means = [palmsens_df['red_voltage'].mean(), stm32_df['red_voltage'].mean()]
        
        x = np.arange(len(devices))
        width = 0.35
        
        ax5.bar(x - width/2, ox_means, width, label='Oxidation', alpha=0.7)
        ax5.bar(x + width/2, red_means, width, label='Reduction', alpha=0.7)
        
        ax5.set_xlabel('Device')
        ax5.set_ylabel('Average Voltage (V)')
        ax5.set_title('Average Peak Voltages')
        ax5.set_xticks(x)
        ax5.set_xticklabels(devices)
        ax5.legend()
        ax5.grid(True, alpha=0.3)
        
        # Plot 6: Sample distribution
        ax6 = axes[1, 2]
        concentrations = sorted(set(list(palmsens_df['concentration']) + list(stm32_df['concentration'])))
        pal_counts = [len(palmsens_df[palmsens_df['concentration'] == c]) for c in concentrations]
        stm32_counts = [len(stm32_df[stm32_df['concentration'] == c]) for c in concentrations]
        
        x = np.arange(len(concentrations))
        width = 0.35
        
        ax6.bar(x - width/2, pal_counts, width, label='Palmsens', alpha=0.7)
        ax6.bar(x + width/2, stm32_counts, width, label='STM32', alpha=0.7)
        
        ax6.set_xlabel('Concentration (mM)')
        ax6.set_ylabel('Number of Samples')
        ax6.set_title('Sample Distribution by Concentration')
        ax6.set_xticks(x)
        ax6.set_xticklabels([f'{c:.1f}' for c in concentrations])
        ax6.legend()
        ax6.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        plot_path = self.results_dir / f"pls_analysis_full_{timestamp}.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        
        print(f"📊 บันทึกกราฟ: {plot_path.name}")
        plt.show()
    
    def create_comprehensive_report(self, palmsens_data, stm32_data):
        """สร้างรายงานครอบคลุม"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Summary statistics
        palmsens_df = self.create_dataframe(palmsens_data, "Palmsens")
        stm32_df = self.create_dataframe(stm32_data, "STM32")
        
        report = {
            'analysis_info': {
                'timestamp': timestamp,
                'method': 'Enhanced Detector V4 Improved',
                'scan_01_excluded': True,
                'max_files_per_device': self.max_files_per_device,
                'processing_time_seconds': self.stats['processing_time']
            },
            'data_summary': {
                'palmsens': {
                    'total_samples': len(palmsens_data),
                    'concentrations': sorted(palmsens_df['concentration'].unique().tolist()),
                    'scan_rates': sorted(palmsens_df['scan_rate'].unique().tolist())
                },
                'stm32': {
                    'total_samples': len(stm32_data),
                    'concentrations': sorted(stm32_df['concentration'].unique().tolist()),
                    'scan_rates': sorted(stm32_df['scan_rate'].unique().tolist())
                }
            },
            'peak_statistics': {
                'palmsens': {
                    'ox_voltage_mean': float(palmsens_df['ox_voltage'].mean()),
                    'ox_voltage_std': float(palmsens_df['ox_voltage'].std()),
                    'red_voltage_mean': float(palmsens_df['red_voltage'].mean()),
                    'red_voltage_std': float(palmsens_df['red_voltage'].std()),
                    'peak_separation_mean': float(palmsens_df['peak_separation_voltage'].mean()),
                    'peak_separation_std': float(palmsens_df['peak_separation_voltage'].std())
                },
                'stm32': {
                    'ox_voltage_mean': float(stm32_df['ox_voltage'].mean()),
                    'ox_voltage_std': float(stm32_df['ox_voltage'].std()),
                    'red_voltage_mean': float(stm32_df['red_voltage'].mean()),
                    'red_voltage_std': float(stm32_df['red_voltage'].std()),
                    'peak_separation_mean': float(stm32_df['peak_separation_voltage'].mean()),
                    'peak_separation_std': float(stm32_df['peak_separation_voltage'].std())
                }
            },
            'processing_statistics': self.stats,
            'files_generated': {
                'labplot2_csv': f"pls_labplot2_data_{timestamp}.csv",
                'palmsens_csv': f"palmsens_data_{timestamp}.csv",
                'stm32_csv': f"stm32_data_{timestamp}.csv",
                'visualization': f"pls_analysis_full_{timestamp}.png",
                'report': f"pls_full_report_{timestamp}.json"
            }
        }
        
        # Save report
        report_path = self.results_dir / f"pls_full_report_{timestamp}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📋 รายงานสรุป: {report_path.name}")
        
        # Print summary
        print(f"\n📊 สรุปผลการวิเคราะห์:")
        print(f"  Palmsens: {len(palmsens_data)} samples")
        print(f"  STM32: {len(stm32_data)} samples")
        print(f"  Processing time: {self.stats['processing_time']:.2f} seconds")
        print(f"  Success rate: Palmsens {self.stats['palmsens']['success']}/{self.stats['palmsens']['total']}, STM32 {self.stats['stm32']['success']}/{self.stats['stm32']['total']}")

if __name__ == "__main__":
    # สร้าง analyzer instance (จำกัด 100 ไฟล์ต่ออุปกรณ์)
    analyzer = PLSAnalysisFull(max_files_per_device=100)
    
    # รัน full analysis
    analyzer.run_full_analysis()
