#!/usr/bin/env python3
"""
PLS Workflow with Enhanced Detector V4 Improved - Fixed Version
ใช้ Enhanced Detector V4 Improved แบบเดียวกับเว็บแอปที่ทำงานได้
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.cross_decomposition import PLSRegression
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import os
import glob
import re
from pathlib import Path
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import Enhanced Detector V4 Improved
try:
    from enhanced_detector_v4_improved import EnhancedDetectorV4Improved
    print("✅ Enhanced Detector V4 Improved พร้อมใช้งาน")
    HAS_ENHANCED_V4_IMPROVED = True
except ImportError as e:
    print("❌ Enhanced Detector V4 Improved ไม่พบ")
    HAS_ENHANCED_V4_IMPROVED = False

class PLSWorkflowEnhancedV4ImprovedFixed:
    """
    PLS Workflow ที่ใช้ Enhanced Detector V4 Improved แบบ Fixed
    อ่าน peaks จาก result['peaks'] แทนที่จะเป็น anodic_peaks/cathodic_peaks
    """
    
    def __init__(self, output_dir="pls_results_v4_improved_fixed"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize Enhanced Detector V4 Improved
        if HAS_ENHANCED_V4_IMPROVED:
            self.detector = EnhancedDetectorV4Improved(confidence_threshold=25.0)
        else:
            self.detector = None
            
        # Statistics
        self.stats = {
            'total_files': 0,
            'successful_detections': 0,
            'failed_detections': 0,
            'total_peaks': 0,
            'files_with_both_peaks': 0
        }
        
    def extract_metadata_from_filename(self, filename):
        """แยกข้อมูล metadata จากชื่อไฟล์"""
        # Example: "Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv"
        # Pattern: Device_Concentration_Method_ScanRate_Electrode_scan_Number.csv
        
        filename_only = Path(filename).stem
        
        # Regular expressions for different patterns
        patterns = [
            r'(\w+)_([0-9.]+mM)_CV_([0-9.]+mVpS)_(\w+)_scan_(\d+)',
            r'(\w+)_([0-9.]+)mM_CV_([0-9.]+)mVs_(\w+)_scan_(\d+)',
            r'(\w+)_([0-9.]+mM)_([0-9.]+mVpS)_(\w+)_scan_(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename_only)
            if match:
                groups = match.groups()
                if len(groups) >= 4:
                    device = groups[0]
                    concentration_str = groups[1]
                    scan_rate_str = groups[2] if len(groups) > 2 else "unknown"
                    electrode = groups[3] if len(groups) > 3 else "unknown"
                    scan_number = groups[4] if len(groups) > 4 else "1"
                    
                    # Extract numeric concentration
                    conc_match = re.search(r'([0-9.]+)', concentration_str)
                    concentration = float(conc_match.group(1)) if conc_match else 0.0
                    
                    # Extract scan rate
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
    
    def load_and_analyze_cv_file(self, filepath):
        """โหลดไฟล์ CV และวิเคราะห์ด้วย Enhanced Detector V4 Improved - Fixed"""
        try:
            # โหลดไฟล์ CSV (skip 2 header rows)
            data = pd.read_csv(filepath, skiprows=2, names=['voltage', 'current'])
            
            if data.empty or len(data) < 10:
                logger.warning(f"   ❌ ไฟล์ว่างหรือข้อมูลน้อยเกินไป: {len(data)} จุด")
                return None
            
            # ใช้ Enhanced Detector V4 Improved วิเคราะห์
            logger.info(f"🔬 วิเคราะห์ {filepath.name} ด้วย Enhanced Detector V4 Improved...")
            
            # สร้าง data structure ที่ Enhanced V4 ต้องการ (แบบเว็บแอป)
            cv_data = {
                'voltage': data['voltage'].tolist(),  # Convert to list like web API
                'current': data['current'].tolist()   # Convert to list like web API
            }
            
            # รัน Enhanced Detector V4 Improved
            results = self.detector.analyze_cv_data(cv_data)
            
            if not results:
                logger.warning(f"   ❌ Enhanced V4 Improved ไม่สามารถวิเคราะห์ได้")
                return None
            
            # **FIX: อ่าน peaks จาก results['peaks'] แทนที่จะเป็น anodic_peaks/cathodic_peaks**
            all_peaks = results.get('peaks', [])
            
            if not all_peaks:
                logger.warning(f"   ❌ ไม่พบ peaks ใน results['peaks']")
                return None
            
            # แยก peaks ตาม type
            anodic_peaks = [p for p in all_peaks if p.get('type') == 'oxidation']
            cathodic_peaks = [p for p in all_peaks if p.get('type') == 'reduction']
            
            logger.info(f"   ✅ พบ peaks: {len(anodic_peaks)} anodic + {len(cathodic_peaks)} cathodic = {len(all_peaks)} total")
            
            # ตรวจสอบว่ามี peak ครบทั้ง 2 ด้าน
            has_both_peaks = len(anodic_peaks) > 0 and len(cathodic_peaks) > 0
            
            if has_both_peaks:
                self.stats['files_with_both_peaks'] += 1
                logger.info(f"   🎯 ไฟล์นี้มี peak ครบทั้ง 2 ด้าน!")
            
            # Extract metadata
            metadata = self.extract_metadata_from_filename(filepath.name)
            
            return {
                'filename': filepath.name,
                'filepath': str(filepath),
                'metadata': metadata,
                'voltage': data['voltage'].values,
                'current': data['current'].values,
                'anodic_peaks': anodic_peaks,
                'cathodic_peaks': cathodic_peaks,
                'all_peaks': all_peaks,
                'has_both_peaks': has_both_peaks,
                'enhanced_v4_results': results,
                'data_points': len(data)
            }
            
        except Exception as e:
            logger.error(f"   ❌ Error loading {filepath.name}: {e}")
            return None
    
    def scan_directories(self, base_dirs):
        """สแกนหาไฟล์ CV ในไดเรกทอรี"""
        all_files = []
        
        for base_dir in base_dirs:
            if not os.path.exists(base_dir):
                logger.warning(f"⚠️ ไดเรกทอรี {base_dir} ไม่พบ")
                continue
                
            # หาไฟล์ .csv ทั้งหมด
            pattern = os.path.join(base_dir, "**", "*.csv")
            files = glob.glob(pattern, recursive=True)
            
            logger.info(f"📂 พบไฟล์ใน {base_dir}: {len(files)} ไฟล์")
            all_files.extend([Path(f) for f in files])
        
        logger.info(f"📁 รวมไฟล์ทั้งหมด: {len(all_files)} ไฟล์")
        return all_files
    
    def run_analysis(self, data_directories):
        """รันการวิเคราะห์ PLS"""
        logger.info("🚀 เริ่มต้น PLS Analysis ด้วย Enhanced V4 Improved Fixed")
        
        if not HAS_ENHANCED_V4_IMPROVED:
            logger.error("❌ Enhanced Detector V4 Improved ไม่พร้อมใช้งาน")
            return None
        
        # 1. สแกนไฟล์
        cv_files = self.scan_directories(data_directories)
        
        if not cv_files:
            logger.error("❌ ไม่พบไฟล์ CV")
            return None
        
        # 2. วิเคราะห์ไฟล์ทีละไฟล์
        logger.info(f"🔬 เริ่มวิเคราะห์ {len(cv_files)} ไฟล์...")
        
        valid_data = []
        
        for i, filepath in enumerate(cv_files[:10]):  # ทดสอบ 10 ไฟล์แรก
            logger.info(f"📄 [{i+1}/{len(cv_files[:10])}] {filepath.name}")
            self.stats['total_files'] += 1
            
            result = self.load_and_analyze_cv_file(filepath)
            
            if result:
                valid_data.append(result)
                self.stats['successful_detections'] += 1
                self.stats['total_peaks'] += len(result['all_peaks'])
            else:
                self.stats['failed_detections'] += 1
        
        logger.info(f"✅ วิเคราะห์เสร็จ: {len(valid_data)}/{len(cv_files[:10])} ไฟล์สำเร็จ")
        
        if not valid_data:
            logger.error("❌ ไม่มีข้อมูลที่วิเคราะห์ได้")
            return None
        
        # 3. สร้าง visualization
        self.create_summary_plot(valid_data)
        
        # 4. สร้างรายงาน
        self.create_report(valid_data)
        
        return valid_data
    
    def create_summary_plot(self, data_list):
        """สร้างกราฟสรุปผลการวิเคราะห์"""
        if not data_list:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot 1: CV curves ตัวอย่าง
        ax1 = axes[0, 0]
        for i, data in enumerate(data_list[:5]):  # แสดง 5 curves แรก
            ax1.plot(data['voltage'], data['current'], alpha=0.7, label=data['metadata']['device'])
            
            # Mark peaks
            for peak in data['all_peaks']:
                color = 'red' if peak['type'] == 'oxidation' else 'blue'
                ax1.scatter(peak['voltage'], peak['current'], color=color, s=50, zorder=5)
        
        ax1.set_xlabel('Voltage (V)')
        ax1.set_ylabel('Current (µA)')
        ax1.set_title('CV Curves with Detected Peaks')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Plot 2: Peak count distribution
        ax2 = axes[0, 1]
        peak_counts = [len(data['all_peaks']) for data in data_list]
        ax2.hist(peak_counts, bins=range(max(peak_counts)+2), alpha=0.7, edgecolor='black')
        ax2.set_xlabel('Number of Peaks')
        ax2.set_ylabel('Number of Files')
        ax2.set_title('Peak Count Distribution')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Concentration vs Peak info
        ax3 = axes[1, 0]
        concentrations = [data['metadata']['concentration'] for data in data_list]
        ox_counts = [len(data['anodic_peaks']) for data in data_list]
        red_counts = [len(data['cathodic_peaks']) for data in data_list]
        
        ax3.scatter(concentrations, ox_counts, color='red', label='Oxidation', alpha=0.7)
        ax3.scatter(concentrations, red_counts, color='blue', label='Reduction', alpha=0.7)
        ax3.set_xlabel('Concentration (mM)')
        ax3.set_ylabel('Peak Count')
        ax3.set_title('Concentration vs Peak Count')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Statistics summary
        ax4 = axes[1, 1]
        stats_data = [
            self.stats['successful_detections'],
            self.stats['failed_detections'],
            self.stats['files_with_both_peaks']
        ]
        labels = ['Successful', 'Failed', 'Both Peaks']
        colors = ['green', 'red', 'gold']
        
        ax4.bar(labels, stats_data, color=colors, alpha=0.7)
        ax4.set_ylabel('Number of Files')
        ax4.set_title('Detection Statistics')
        
        for i, v in enumerate(stats_data):
            ax4.text(i, v + 0.1, str(v), ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Save plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_path = self.output_dir / f"pls_analysis_v4_improved_fixed_{timestamp}.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        
        logger.info(f"📊 บันทึกกราฟ: {plot_path}")
        
        plt.show()
        
    def create_report(self, data_list):
        """สร้างรายงานผลการวิเคราะห์"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"pls_report_v4_improved_fixed_{timestamp}.json"
        
        report = {
            'timestamp': timestamp,
            'method': 'Enhanced Detector V4 Improved - Fixed',
            'statistics': self.stats,
            'analysis_summary': {
                'total_files_analyzed': len(data_list),
                'unique_concentrations': len(set(d['metadata']['concentration'] for d in data_list)),
                'unique_devices': len(set(d['metadata']['device'] for d in data_list)),
                'average_peaks_per_file': self.stats['total_peaks'] / len(data_list) if data_list else 0,
                'success_rate': self.stats['successful_detections'] / self.stats['total_files'] * 100 if self.stats['total_files'] > 0 else 0
            },
            'files_analyzed': [
                {
                    'filename': data['filename'],
                    'metadata': data['metadata'],
                    'peak_count': len(data['all_peaks']),
                    'anodic_peaks': len(data['anodic_peaks']),
                    'cathodic_peaks': len(data['cathodic_peaks']),
                    'has_both_peaks': data['has_both_peaks']
                }
                for data in data_list
            ]
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 บันทึกรายงาน: {report_path}")

def main():
    """Main function"""
    if not HAS_ENHANCED_V4_IMPROVED:
        print("❌ Enhanced Detector V4 Improved ไม่พร้อมใช้งาน")
        return
    
    # ตั้งค่า data directories
    data_directories = [
        "Test_data/Palmsens",
        "Test_data/Stm32"
    ]
    
    # สร้าง workflow instance
    workflow = PLSWorkflowEnhancedV4ImprovedFixed()
    
    # รันการวิเคราะห์
    results = workflow.run_analysis(data_directories)
    
    if results:
        print(f"\n✅ เสร็จสิ้น! วิเคราะห์ได้ {len(results)} ไฟล์")
        print(f"📁 ผลลัพธ์บันทึกใน: {workflow.output_dir}")
    else:
        print("\n❌ การวิเคราะห์ล้มเหลว")

if __name__ == "__main__":
    main()
