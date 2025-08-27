#!/usr/bin/env python3
"""
PLS Workflow Enhanced V4 Improved - Production Ready
ใช้ Enhanced V4 Improved สำหรับการวิเคราะห์ PLS ที่รวดเร็วและแม่นยำ
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cross_decomposition import PLSRegression
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import os
import glob
import re
from pathlib import Path
import time
from datetime import datetime

def extract_metadata_from_filename(filename):
    """แยกข้อมูล metadata จากชื่อไฟล์"""
    filename_only = Path(filename).stem
    
    # Example: "Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv"
    patterns = [
        r'(\w+)_([0-9.]+mM)_CV_([0-9.]+mVpS)_(\w+)_scan_(\d+)',
        r'(\w+)_([0-9.]+)mM_CV_([0-9.]+)mVs_(\w+)_scan_(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename_only)
        if match:
            groups = match.groups()
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
    
    return {
        'device': 'unknown',
        'concentration': 0.0,
        'scan_rate': 0.0,
        'electrode': 'unknown',
        'scan_number': 1,
        'filename': filename_only
    }

def analyze_single_file(filepath, detector):
    """วิเคราะห์ไฟล์เดียวด้วย Enhanced V4 Improved"""
    try:
        # โหลดไฟล์
        data = pd.read_csv(filepath, skiprows=2, names=['voltage', 'current'])
        
        if data.empty or len(data) < 10:
            return None
        
        # เตรียมข้อมูลสำหรับ Enhanced V4 Improved
        cv_data = {
            'voltage': data['voltage'].tolist(),
            'current': data['current'].tolist()
        }
        
        # วิเคราะห์ด้วย Enhanced V4 Improved
        results = detector.analyze_cv_data(cv_data)
        
        if not results or not isinstance(results, dict):
            return None
        
        # แยก peaks
        all_peaks = results.get('peaks', [])
        if not all_peaks:
            return None
        
        anodic_peaks = [p for p in all_peaks if p.get('type') == 'oxidation']
        cathodic_peaks = [p for p in all_peaks if p.get('type') == 'reduction']
        
        # ตรวจสอบว่ามี peak ครบทั้ง 2 ด้าน
        has_both_peaks = len(anodic_peaks) > 0 and len(cathodic_peaks) > 0
        
        # Extract metadata
        metadata = extract_metadata_from_filename(filepath.name)
        
        return {
            'filename': filepath.name,
            'metadata': metadata,
            'anodic_peaks': anodic_peaks,
            'cathodic_peaks': cathodic_peaks,
            'all_peaks': all_peaks,
            'has_both_peaks': has_both_peaks,
            'peak_count': len(all_peaks)
        }
        
    except Exception as e:
        print(f"❌ Error analyzing {filepath.name}: {e}")
        return None

def run_pls_analysis_enhanced_v4():
    """รัน PLS Analysis ด้วย Enhanced V4 Improved"""
    print("🚀 PLS Analysis with Enhanced V4 Improved")
    print("=" * 50)
    
    try:
        from enhanced_detector_v4_improved import EnhancedDetectorV4Improved
        print("✅ Enhanced V4 Improved พร้อมใช้งาน")
    except ImportError:
        print("❌ Enhanced V4 Improved ไม่พร้อมใช้งาน")
        return
    
    # สร้าง detector
    detector = EnhancedDetectorV4Improved(confidence_threshold=25.0)
    
    # หาไฟล์ข้อมูล
    data_dirs = ["Test_data/Palmsens", "Test_data/Stm32"]
    all_files = []
    
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            pattern = os.path.join(data_dir, "**", "*.csv")
            files = glob.glob(pattern, recursive=True)
            all_files.extend([Path(f) for f in files])
    
    print(f"📁 พบไฟล์ทั้งหมด: {len(all_files)}")
    
    if not all_files:
        print("❌ ไม่พบไฟล์ข้อมูล")
        return
    
    # วิเคราะห์ไฟล์ (ทดสอบ 20 ไฟล์แรก)
    test_files = all_files[:20]
    print(f"🔬 วิเคราะห์ {len(test_files)} ไฟล์...")
    
    valid_results = []
    stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'both_peaks': 0,
        'total_peaks': 0
    }
    
    start_time = time.time()
    
    for i, filepath in enumerate(test_files):
        print(f"[{i+1:2d}/{len(test_files)}] {filepath.name}...", end=" ")
        
        stats['total'] += 1
        result = analyze_single_file(filepath, detector)
        
        if result:
            valid_results.append(result)
            stats['success'] += 1
            stats['total_peaks'] += result['peak_count']
            
            if result['has_both_peaks']:
                stats['both_peaks'] += 1
            
            print(f"✅ {result['peak_count']} peaks ({len(result['anodic_peaks'])}ox+{len(result['cathodic_peaks'])}red)")
        else:
            stats['failed'] += 1
            print("❌")
    
    analysis_time = time.time() - start_time
    print(f"\\n⏱️  วิเคราะห์เสร็จใน {analysis_time:.2f} วินาที")
    
    # แสดงสถิติ
    print(f"\\n📊 สถิติการวิเคราะห์:")
    print(f"  ไฟล์ทั้งหมด: {stats['total']}")
    print(f"  สำเร็จ: {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
    print(f"  ล้มเหลว: {stats['failed']}")
    print(f"  มี peak ครบ 2 ด้าน: {stats['both_peaks']} ({stats['both_peaks']/stats['success']*100:.1f}%)" if stats['success'] > 0 else "")
    print(f"  Peak เฉลี่ย/ไฟล์: {stats['total_peaks']/stats['success']:.1f}" if stats['success'] > 0 else "")
    
    if not valid_results:
        print("❌ ไม่มีข้อมูลที่ใช้ได้")
        return
    
    # สร้างกราฟ
    create_analysis_plot(valid_results, stats)
    
    # Export ข้อมูลสำหรับ PLS
    export_pls_data(valid_results)
    
    print(f"\\n🎉 เสร็จสิ้น! วิเคราะห์ได้ {len(valid_results)} ไฟล์")

def create_analysis_plot(results, stats):
    """สร้างกราฟวิเคราะห์ผลลัพธ์"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Plot 1: Peak count distribution
    ax1 = axes[0, 0]
    peak_counts = [r['peak_count'] for r in results]
    ax1.hist(peak_counts, bins=range(max(peak_counts)+2), alpha=0.7, edgecolor='black')
    ax1.set_xlabel('Number of Peaks')
    ax1.set_ylabel('Number of Files')
    ax1.set_title('Peak Count Distribution')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Concentration vs Peaks
    ax2 = axes[0, 1]
    concentrations = [r['metadata']['concentration'] for r in results]
    ox_counts = [len(r['anodic_peaks']) for r in results]
    red_counts = [len(r['cathodic_peaks']) for r in results]
    
    ax2.scatter(concentrations, ox_counts, color='red', label='Oxidation', alpha=0.7)
    ax2.scatter(concentrations, red_counts, color='blue', label='Reduction', alpha=0.7)
    ax2.set_xlabel('Concentration (mM)')
    ax2.set_ylabel('Peak Count')
    ax2.set_title('Concentration vs Peak Count')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Device comparison
    ax3 = axes[1, 0]
    devices = [r['metadata']['device'] for r in results]
    device_counts = {}
    for device in devices:
        device_counts[device] = device_counts.get(device, 0) + 1
    
    ax3.bar(device_counts.keys(), device_counts.values(), alpha=0.7)
    ax3.set_ylabel('Number of Files')
    ax3.set_title('Files by Device')
    ax3.tick_params(axis='x', rotation=45)
    
    # Plot 4: Success statistics
    ax4 = axes[1, 1]
    labels = ['Success', 'Failed', 'Both Peaks']
    values = [stats['success'], stats['failed'], stats['both_peaks']]
    colors = ['green', 'red', 'gold']
    
    ax4.bar(labels, values, color=colors, alpha=0.7)
    ax4.set_ylabel('Number of Files')
    ax4.set_title('Analysis Statistics')
    
    for i, v in enumerate(values):
        ax4.text(i, v + 0.1, str(v), ha='center', va='bottom')
    
    plt.tight_layout()
    
    # Save plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_path = f"pls_analysis_enhanced_v4_improved_{timestamp}.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    
    print(f"📊 บันทึกกราฟ: {plot_path}")
    plt.show()

def export_pls_data(results):
    """Export ข้อมูลสำหรับ PLS analysis"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # CSV Export
    csv_data = []
    for result in results:
        base_info = {
            'filename': result['filename'],
            'device': result['metadata']['device'],
            'concentration': result['metadata']['concentration'],
            'scan_rate': result['metadata']['scan_rate'],
            'electrode': result['metadata']['electrode'],
            'total_peaks': result['peak_count'],
            'anodic_peaks': len(result['anodic_peaks']),
            'cathodic_peaks': len(result['cathodic_peaks']),
            'has_both_peaks': result['has_both_peaks']
        }
        
        # Add peak details
        for i, peak in enumerate(result['all_peaks']):
            peak_info = base_info.copy()
            peak_info.update({
                'peak_number': i + 1,
                'peak_type': peak.get('type', 'unknown'),
                'peak_voltage': peak.get('voltage', 0),
                'peak_current': peak.get('current', 0),
                'peak_confidence': peak.get('confidence', 0)
            })
            csv_data.append(peak_info)
    
    # Save CSV
    if csv_data:
        df = pd.DataFrame(csv_data)
        csv_path = f"pls_data_enhanced_v4_improved_{timestamp}.csv"
        df.to_csv(csv_path, index=False)
        print(f"📄 Export CSV: {csv_path}")
    
    print(f"✅ Export เสร็จสิ้น!")

if __name__ == "__main__":
    run_pls_analysis_enhanced_v4()
