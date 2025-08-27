#!/usr/bin/env python3
"""
🧪 Enhanced V5 Comprehensive Testing
ทดสอบ Enhanced V5 กับไฟล์ทั้งหมดแบบสมบูรณ์

รองรับ:
- STM32 data (ทุกความเข้มข้น)
- PalmSens data (ทุกความเข้มข้น)
- Raw STM32 data
- การวิเคราะห์แบบละเอียด
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import numpy as np

# Import Enhanced V5 detector
try:
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    from enhanced_detector_v5 import EnhancedDetectorV5
    ENHANCED_V5_AVAILABLE = True
    print("✅ Enhanced V5 detector loaded successfully")
except ImportError as e:
    print(f"❌ Cannot import Enhanced V5 detector: {e}")
    ENHANCED_V5_AVAILABLE = False
    sys.exit(1)

def find_all_test_files():
    """🔍 หาไฟล์ทดสอบทั้งหมด"""
    test_data_dir = Path("Test_data")
    
    file_groups = {
        'stm32': {
            'path': test_data_dir / "Stm32",
            'files': [],
            'pattern': "*.csv"
        },
        'palmsens': {
            'path': test_data_dir / "Palmsens",
            'files': [],
            'pattern': "*.csv"
        },
        'raw_stm32': {
            'path': test_data_dir / "raw_stm32",
            'files': [],
            'pattern': "*.csv"
        },
        'isolated': {
            'path': test_data_dir / "isolated-test",
            'files': [],
            'pattern': "*.csv"
        }
    }
    
    total_files = 0
    
    for group_name, group_info in file_groups.items():
        if group_info['path'].exists():
            # หาไฟล์ทั้งหมดใน directory และ subdirectories
            files = list(group_info['path'].rglob(group_info['pattern']))
            group_info['files'] = [str(f) for f in files]
            total_files += len(files)
            print(f"📁 {group_name:12}: {len(files):4d} files")
        else:
            print(f"📁 {group_name:12}: Directory not found")
    
    print(f"📊 Total files found: {total_files}")
    return file_groups

def categorize_files_by_concentration(file_groups):
    """🧪 จัดกลุ่มไฟล์ตามความเข้มข้น"""
    concentrations = defaultdict(list)
    
    # รูปแบบต่างๆ ของชื่อไฟล์
    concentration_patterns = [
        # STM32 patterns
        'Pipot_Ferro_0_5mM', 'Pipot_Ferro-0_5mM',
        'Pipot_Ferro_1_0mM', 'Pipot_Ferro-1_0mM', 
        'Pipot_Ferro_5_0mM', 'Pipot_Ferro-5_0mM',
        'Pipot_Ferro_20mM', 'Pipot_Ferro-20mM',
        
        # PalmSens patterns
        'Palmsens_5mM', 'Palmsens_10mM', 'Palmsens_20mM', 'Palmsens_50mM',
        
        # อื่นๆ
        'test_stm32', 'isolated'
    ]
    
    for group_name, group_info in file_groups.items():
        for file_path in group_info['files']:
            file_name = Path(file_path).name
            
            # จับคู่กับ concentration patterns
            matched = False
            for pattern in concentration_patterns:
                if pattern in file_name:
                    concentrations[pattern].append(file_path)
                    matched = True
                    break
            
            if not matched:
                concentrations['others'].append(file_path)
    
    return concentrations

def test_single_file(detector, file_path):
    """ทดสอบไฟล์เดียว"""
    try:
        # ใช้ function ที่มีอยู่แล้ว
        from enhanced_detector_v5 import test_enhanced_v5
        
        # อ่านข้อมูลและทดสอบ (แบบไม่แสดงผล)
        import pandas as pd
        
        # อ่านข้อมูล
        df = pd.read_csv(file_path, skiprows=1)
        if len(df) < 10:
            return {
                'success': False,
                'error': 'Insufficient data points',
                'ox_peaks': 0,
                'red_peaks': 0,
                'total_peaks': 0,
                'baseline_quality': 0.0
            }
        
        voltage = df['V'].values
        current = df['uA'].values
        
        # Detect peaks
        result = detector.detect_peaks_enhanced_v5(voltage, current)
        
        if result is None:
            return {
                'success': False,
                'error': 'Detection failed',
                'ox_peaks': 0,
                'red_peaks': 0,
                'total_peaks': 0,
                'baseline_quality': 0.0
            }
        
        # นับ peaks
        peaks = result.get('peaks', [])
        ox_peaks = len([p for p in peaks if p.get('peak_type') == 'OX'])
        red_peaks = len([p for p in peaks if p.get('peak_type') == 'RED'])
        
        # เงื่อนไขความสำเร็จ: ต้องมีทั้ง OX และ RED
        success = ox_peaks > 0 and red_peaks > 0
        
        # คุณภาพ baseline
        baseline_info = result.get('baseline_info', {})
        baseline_quality = baseline_info.get('r2_score', 0.0) if baseline_info else 0.0
        
        return {
            'success': success,
            'ox_peaks': ox_peaks,
            'red_peaks': red_peaks,
            'total_peaks': ox_peaks + red_peaks,
            'baseline_quality': baseline_quality,
            'metadata': {
                'scan_direction': result.get('scan_direction', 'unknown'),
                'total_points': result.get('total_points', len(voltage)),
                'snr': result.get('signal_noise_ratio', 0.0)
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'ox_peaks': 0,
            'red_peaks': 0,
            'total_peaks': 0,
            'baseline_quality': 0.0
        }

def test_concentration_group(detector, concentration, files, max_files=None):
    """ทดสอบกลุ่มความเข้มข้น"""
    if max_files:
        files = files[:max_files]
    
    print(f"\n📊 Testing {concentration} ({len(files)} files):")
    print("-" * 60)
    
    results = []
    successful = 0
    
    for i, file_path in enumerate(files):
        file_name = Path(file_path).name
        print(f"  {i+1:3d}. {file_name[:45]:<45}", end=" ")
        
        result = test_single_file(detector, file_path)
        result['file_path'] = file_path
        result['concentration'] = concentration
        results.append(result)
        
        if result['success']:
            successful += 1
            print(f"✅ OX:{result['ox_peaks']}, RED:{result['red_peaks']}")
        else:
            error_msg = result.get('error', 'No valid peaks')
            print(f"❌ {error_msg}")
    
    success_rate = (successful / len(files)) * 100 if files else 0
    print(f"\n  📈 {concentration} Success Rate: {successful}/{len(files)} ({success_rate:.1f}%)")
    
    return {
        'concentration': concentration,
        'total_files': len(files),
        'successful_files': successful,
        'success_rate': success_rate,
        'results': results
    }

def run_comprehensive_test(max_files_per_group=10):
    """🧪 รันการทดสอบแบบสมบูรณ์"""
    
    print("🧪 Enhanced V5 Comprehensive Testing")
    print("=" * 70)
    
    if not ENHANCED_V5_AVAILABLE:
        print("❌ Enhanced V5 detector not available")
        return None
    
    # Initialize detector
    detector = EnhancedDetectorV5()
    
    # หาไฟล์ทั้งหมด
    print("\n🔍 Finding all test files...")
    file_groups = find_all_test_files()
    
    # จัดกลุ่มตามความเข้มข้น
    print("\n🧪 Categorizing by concentration...")
    concentrations = categorize_files_by_concentration(file_groups)
    
    # แสดงสรุปไฟล์
    print(f"\n📋 File Distribution:")
    for conc, files in concentrations.items():
        if files:
            print(f"  {conc:20}: {len(files):4d} files")
    
    # ทดสอบแต่ละกลุ่ม
    print(f"\n🧪 Testing each concentration group...")
    print("=" * 70)
    
    all_results = []
    overall_stats = {
        'total_files': 0,
        'successful_files': 0,
        'failed_files': 0,
        'success_rate': 0.0
    }
    
    for concentration, files in concentrations.items():
        if not files:
            continue
            
        # จำกัดจำนวนไฟล์ถ้าต้องการ
        test_files = files[:max_files_per_group] if max_files_per_group else files
        
        group_result = test_concentration_group(detector, concentration, test_files)
        all_results.append(group_result)
        
        # อัพเดทสถิติรวม
        overall_stats['total_files'] += group_result['total_files']
        overall_stats['successful_files'] += group_result['successful_files']
        overall_stats['failed_files'] += (group_result['total_files'] - group_result['successful_files'])
    
    # คำนวณ success rate รวม
    if overall_stats['total_files'] > 0:
        overall_stats['success_rate'] = (overall_stats['successful_files'] / overall_stats['total_files']) * 100
    
    # แสดงสรุปผลรวม
    print("\n" + "=" * 70)
    print("🎯 COMPREHENSIVE TEST RESULTS:")
    print("=" * 70)
    
    for group_result in all_results:
        concentration = group_result['concentration']
        success_rate = group_result['success_rate']
        successful = group_result['successful_files']
        total = group_result['total_files']
        
        status = "🟢" if success_rate >= 80 else "🟡" if success_rate >= 60 else "🔴"
        print(f"{status} {concentration:20s}: {successful:3d}/{total:3d} ({success_rate:5.1f}%)")
    
    print(f"\n🏆 OVERALL SUCCESS RATE: {overall_stats['successful_files']}/{overall_stats['total_files']} ({overall_stats['success_rate']:.1f}%)")
    
    # สถานะรวม
    if overall_stats['success_rate'] >= 80:
        print("🎉 EXCELLENT! Enhanced V5 ready for full production!")
    elif overall_stats['success_rate'] >= 60:
        print("⚠️  GOOD! Some fine-tuning may be beneficial")
    else:
        print("❌ NEEDS IMPROVEMENT! Review failed cases")
    
    return {
        'overall_stats': overall_stats,
        'concentration_results': all_results,
        'timestamp': datetime.now().isoformat(),
        'detector_version': 'Enhanced V5.0',
        'test_parameters': {
            'max_files_per_group': max_files_per_group,
            'success_criteria': 'OX peaks > 0 AND RED peaks > 0'
        }
    }

def save_comprehensive_report(results):
    """💾 บันทึกรายงานแบบสมบูรณ์"""
    if not results:
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"enhanced_v5_comprehensive_test_report_{timestamp}.json"
    
    # Prepare detailed analysis
    detailed_analysis = {
        'summary': results['overall_stats'],
        'concentration_analysis': [],
        'performance_metrics': {},
        'recommendations': []
    }
    
    # วิเคราะห์แต่ละความเข้มข้น
    for group_result in results['concentration_results']:
        conc_analysis = {
            'concentration': group_result['concentration'],
            'performance': {
                'total_files': group_result['total_files'],
                'successful_files': group_result['successful_files'],
                'success_rate': group_result['success_rate']
            }
        }
        
        # วิเคราะห์ detailed results ถ้ามี
        if 'results' in group_result:
            successful_results = [r for r in group_result['results'] if r['success']]
            if successful_results:
                conc_analysis['peak_statistics'] = {
                    'avg_ox_peaks': np.mean([r['ox_peaks'] for r in successful_results]),
                    'avg_red_peaks': np.mean([r['red_peaks'] for r in successful_results]),
                    'avg_baseline_quality': np.mean([r['baseline_quality'] for r in successful_results])
                }
        
        detailed_analysis['concentration_analysis'].append(conc_analysis)
    
    # Performance metrics
    success_rate = results['overall_stats']['success_rate']
    detailed_analysis['performance_metrics'] = {
        'overall_grade': 'A' if success_rate >= 90 else 'B' if success_rate >= 80 else 'C' if success_rate >= 60 else 'D',
        'production_ready': success_rate >= 80,
        'total_files_tested': results['overall_stats']['total_files']
    }
    
    # Recommendations
    if success_rate >= 80:
        detailed_analysis['recommendations'] = [
            "✅ Enhanced V5 is production-ready",
            "🚀 Proceed with web application integration",
            "📈 Consider expanding to more diverse datasets",
            "🔧 Monitor performance in production environment"
        ]
    elif success_rate >= 60:
        detailed_analysis['recommendations'] = [
            "⚙️ Good performance with room for improvement",
            "🔍 Analyze failed cases for patterns",
            "🧪 Consider algorithm fine-tuning",
            "📊 Test with more representative data"
        ]
    else:
        detailed_analysis['recommendations'] = [
            "🔧 Significant improvement needed",
            "🔍 Deep analysis of failure modes required",
            "⚙️ Algorithm parameters need adjustment",
            "🧪 Extended testing with diverse datasets"
        ]
    
    # Save full report
    full_report = {
        'test_metadata': {
            'timestamp': results['timestamp'],
            'detector_version': results['detector_version'],
            'test_parameters': results['test_parameters']
        },
        'raw_results': results,
        'analysis': detailed_analysis
    }
    
    try:
        # Convert numpy types to JSON serializable
        def convert_numpy(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            return obj
        
        json_safe_report = convert_numpy(full_report)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(json_safe_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Comprehensive report saved: {report_file}")
        return report_file
        
    except Exception as e:
        print(f"⚠️ Could not save report: {e}")
        return None

def show_quick_summary(results):
    """📊 แสดงสรุปแบบย่อ"""
    if not results:
        return
    
    print(f"\n📊 QUICK SUMMARY:")
    print(f"   💯 Overall Success Rate: {results['overall_stats']['success_rate']:.1f}%")
    print(f"   📁 Total Files Tested: {results['overall_stats']['total_files']}")
    print(f"   ✅ Successful: {results['overall_stats']['successful_files']}")
    print(f"   ❌ Failed: {results['overall_stats']['failed_files']}")
    
    # Top performing concentrations
    sorted_results = sorted(results['concentration_results'], 
                          key=lambda x: x['success_rate'], reverse=True)
    
    print(f"\n🏆 TOP PERFORMING CONCENTRATIONS:")
    for i, result in enumerate(sorted_results[:3]):
        print(f"   {i+1}. {result['concentration']:15}: {result['success_rate']:5.1f}%")

if __name__ == "__main__":
    print("🧪 Enhanced V5 Comprehensive Testing System")
    print("=" * 50)
    
    # ตั้งค่าการทดสอบ
    MAX_FILES_PER_GROUP = 15  # จำกัดไฟล์ต่อกลุ่มเพื่อความเร็ว (None = ทั้งหมด)
    
    print(f"⚙️  Test Configuration:")
    print(f"   📁 Max files per concentration: {MAX_FILES_PER_GROUP or 'All'}")
    print(f"   🎯 Success criteria: OX > 0 AND RED > 0")
    
    # รันการทดสอบ
    results = run_comprehensive_test(max_files_per_group=MAX_FILES_PER_GROUP)
    
    if results:
        # แสดงสรุปแบบย่อ
        show_quick_summary(results)
        
        # บันทึกรายงาน
        report_file = save_comprehensive_report(results)
        
        print(f"\n🎯 FINAL ASSESSMENT:")
        success_rate = results['overall_stats']['success_rate']
        
        if success_rate >= 90:
            print("🌟 OUTSTANDING! Enhanced V5 exceeds expectations!")
        elif success_rate >= 80:
            print("🎉 EXCELLENT! Enhanced V5 is production-ready!")
        elif success_rate >= 70:
            print("👍 VERY GOOD! Minor improvements may be beneficial")
        elif success_rate >= 60:
            print("👌 GOOD! Some optimization recommended")
        else:
            print("🔧 NEEDS WORK! Significant improvements required")
        
        print(f"\n✨ Testing complete! Report: {report_file}")
    else:
        print("❌ Testing failed!")
