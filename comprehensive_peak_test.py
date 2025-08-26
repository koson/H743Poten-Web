#!/usr/bin/env python3
"""
Comprehensive Peak Detection Testing
ทดสอบ enhanced algorithm กับไฟล์ทุก concentration และ scan rate
เพื่อให้แน่ใจว่าได้ Ox และ Red อย่างละ 1 peak ตามที่ควรจะเป็น
"""

import os
import glob
import pandas as pd
import numpy as np
import logging
from enhanced_peak_detector import EnhancedPeakDetector
import json
from datetime import datetime

def load_cv_file(file_path):
    """Load CV data from various file formats"""
    try:
        # Try to determine file format by reading first few lines
        with open(file_path, 'r') as f:
            first_line = f.readline().strip()
            second_line = f.readline().strip()
        
        # Palmsens format: starts with "FileName:"
        if first_line.startswith('FileName:'):
            df = pd.read_csv(file_path, skiprows=1)
        # STM32 format: usually starts with numbers
        elif first_line.replace('.', '').replace('-', '').replace(',', '').replace(' ', '').isdigit():
            df = pd.read_csv(file_path)
        # Has header row
        elif not first_line.replace('.', '').replace('-', '').replace(',', '').replace(' ', '').isdigit():
            df = pd.read_csv(file_path, skiprows=1)
        else:
            df = pd.read_csv(file_path)
        
        if len(df.columns) < 2:
            return None, None
        
        voltage = df.iloc[:, 0].values
        current = df.iloc[:, 1].values
        
        # Basic validation
        if len(voltage) < 10 or len(current) < 10:
            return None, None
        
        return voltage, current
        
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return None, None

def extract_file_info(file_path):
    """Extract concentration and scan rate from filename"""
    filename = os.path.basename(file_path)
    
    info = {
        'concentration': 'unknown',
        'scan_rate': 'unknown',
        'dataset': 'unknown'
    }
    
    # Extract dataset
    if 'Palmsens' in file_path:
        info['dataset'] = 'Palmsens'
    elif 'Stm32' in file_path or 'STM32' in file_path:
        info['dataset'] = 'STM32'
    
    # Extract concentration
    if '0.5mM' in filename or '0_5mM' in filename:
        info['concentration'] = '0.5mM'
    elif '1.0mM' in filename or '1_0mM' in filename:
        info['concentration'] = '1.0mM'
    elif '2.0mM' in filename or '2_0mM' in filename:
        info['concentration'] = '2.0mM'
    
    # Extract scan rate
    if '20mVpS' in filename or '20mV' in filename:
        info['scan_rate'] = '20mV/s'
    elif '50mVpS' in filename or '50mV' in filename:
        info['scan_rate'] = '50mV/s'
    elif '100mVpS' in filename or '100mV' in filename:
        info['scan_rate'] = '100mV/s'
    elif '200mVpS' in filename or '200mV' in filename:
        info['scan_rate'] = '200mV/s'
    
    return info

def test_comprehensive_peak_detection():
    """ทดสอบ peak detection กับไฟล์หลากหลาย"""
    
    print("🔬 Comprehensive Peak Detection Testing")
    print("=" * 70)
    
    # Find all CSV files in Test_data
    test_patterns = [
        "Test_data/Palmsens/**/*.csv",
        "Test_data/Stm32/**/*.csv",
        "Test_data/converted_stm32/**/*.csv"
    ]
    
    all_files = []
    for pattern in test_patterns:
        files = glob.glob(pattern, recursive=True)
        all_files.extend(files)
    
    print(f"📁 Found {len(all_files)} CSV files to test")
    
    # Initialize detector
    detector = EnhancedPeakDetector()
    detector.logger.setLevel(logging.WARNING)  # Reduce log noise
    
    # Results tracking
    results = {
        'total_files': 0,
        'successful_files': 0,
        'failed_files': 0,
        'perfect_files': 0,  # Files with exactly 1 Ox + 1 Red
        'by_concentration': {},
        'by_scan_rate': {},
        'by_dataset': {},
        'detailed_results': []
    }
    
    # Test each file
    for i, file_path in enumerate(all_files[:50]):  # Limit to first 50 for testing
        print(f"\n📂 Testing {i+1}/{min(50, len(all_files))}: {os.path.basename(file_path)}")
        
        # Load data
        voltage, current = load_cv_file(file_path)
        if voltage is None:
            print(f"   ❌ Failed to load file")
            results['failed_files'] += 1
            continue
        
        # Extract file info
        file_info = extract_file_info(file_path)
        
        print(f"   📊 Data: {len(voltage)} points, V: [{voltage.min():.3f}, {voltage.max():.3f}]V, I: [{current.min():.1f}, {current.max():.1f}]μA")
        print(f"   🏷️  Info: {file_info['dataset']}, {file_info['concentration']}, {file_info['scan_rate']}")
        
        # Run detection
        try:
            detection_results = detector.detect_peaks_enhanced(voltage, current)
            peaks = detection_results['peaks']
            rejected = detection_results['rejected_peaks']
            
            # Count peaks by type
            ox_peaks = [p for p in peaks if p['type'] == 'oxidation']
            red_peaks = [p for p in peaks if p['type'] == 'reduction']
            
            print(f"   🎯 Results: {len(ox_peaks)} Ox + {len(red_peaks)} Red = {len(peaks)} valid peaks")
            print(f"   ❌ Rejected: {len(rejected)} peaks")
            
            # Check if perfect (1 Ox + 1 Red)
            is_perfect = len(ox_peaks) == 1 and len(red_peaks) == 1
            if is_perfect:
                results['perfect_files'] += 1
                print(f"   ✅ PERFECT: 1 Ox + 1 Red as expected!")
            else:
                print(f"   ⚠️  Not ideal: Expected 1 Ox + 1 Red, got {len(ox_peaks)} Ox + {len(red_peaks)} Red")
            
            # Store detailed results
            file_result = {
                'file': os.path.basename(file_path),
                'dataset': file_info['dataset'],
                'concentration': file_info['concentration'],
                'scan_rate': file_info['scan_rate'],
                'ox_peaks': len(ox_peaks),
                'red_peaks': len(red_peaks),
                'total_valid': len(peaks),
                'rejected': len(rejected),
                'is_perfect': is_perfect,
                'peak_details': []
            }
            
            # Add peak details
            for peak in peaks:
                file_result['peak_details'].append({
                    'type': peak['type'],
                    'voltage': round(peak['voltage'], 3),
                    'current': round(peak['current'], 2),
                    'confidence': round(peak['confidence'], 1)
                })
            
            results['detailed_results'].append(file_result)
            results['successful_files'] += 1
            
            # Update statistics by category
            conc = file_info['concentration']
            scan = file_info['scan_rate']
            dataset = file_info['dataset']
            
            if conc not in results['by_concentration']:
                results['by_concentration'][conc] = {'total': 0, 'perfect': 0}
            results['by_concentration'][conc]['total'] += 1
            if is_perfect:
                results['by_concentration'][conc]['perfect'] += 1
            
            if scan not in results['by_scan_rate']:
                results['by_scan_rate'][scan] = {'total': 0, 'perfect': 0}
            results['by_scan_rate'][scan]['total'] += 1
            if is_perfect:
                results['by_scan_rate'][scan]['perfect'] += 1
            
            if dataset not in results['by_dataset']:
                results['by_dataset'][dataset] = {'total': 0, 'perfect': 0}
            results['by_dataset'][dataset]['total'] += 1
            if is_perfect:
                results['by_dataset'][dataset]['perfect'] += 1
            
        except Exception as e:
            print(f"   ❌ Detection failed: {e}")
            results['failed_files'] += 1
        
        results['total_files'] += 1
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 70)
    
    print(f"📁 Files tested: {results['total_files']}")
    print(f"✅ Successful: {results['successful_files']}")
    print(f"❌ Failed: {results['failed_files']}")
    print(f"🎯 Perfect (1 Ox + 1 Red): {results['perfect_files']}")
    print(f"📈 Perfect rate: {results['perfect_files']/results['successful_files']*100:.1f}%" if results['successful_files'] > 0 else "📈 Perfect rate: N/A")
    
    # By concentration
    print(f"\n📊 Results by Concentration:")
    for conc, stats in results['by_concentration'].items():
        perfect_rate = stats['perfect']/stats['total']*100 if stats['total'] > 0 else 0
        print(f"   {conc}: {stats['perfect']}/{stats['total']} perfect ({perfect_rate:.1f}%)")
    
    # By scan rate
    print(f"\n⚡ Results by Scan Rate:")
    for scan, stats in results['by_scan_rate'].items():
        perfect_rate = stats['perfect']/stats['total']*100 if stats['total'] > 0 else 0
        print(f"   {scan}: {stats['perfect']}/{stats['total']} perfect ({perfect_rate:.1f}%)")
    
    # By dataset
    print(f"\n🔬 Results by Dataset:")
    for dataset, stats in results['by_dataset'].items():
        perfect_rate = stats['perfect']/stats['total']*100 if stats['total'] > 0 else 0
        print(f"   {dataset}: {stats['perfect']}/{stats['total']} perfect ({perfect_rate:.1f}%)")
    
    # Show some examples of perfect files
    perfect_examples = [r for r in results['detailed_results'] if r['is_perfect']]
    if perfect_examples:
        print(f"\n✅ Examples of perfect detections (1 Ox + 1 Red):")
        for i, example in enumerate(perfect_examples[:5]):
            ox_peak = next(p for p in example['peak_details'] if p['type'] == 'oxidation')
            red_peak = next(p for p in example['peak_details'] if p['type'] == 'reduction')
            print(f"   {i+1}. {example['file']} ({example['concentration']}, {example['scan_rate']})")
            print(f"      Ox: {ox_peak['voltage']}V, {ox_peak['current']}μA")
            print(f"      Red: {red_peak['voltage']}V, {red_peak['current']}μA")
    
    # Show some examples of non-perfect files
    non_perfect_examples = [r for r in results['detailed_results'] if not r['is_perfect']]
    if non_perfect_examples:
        print(f"\n⚠️  Examples of non-perfect detections:")
        for i, example in enumerate(non_perfect_examples[:3]):
            print(f"   {i+1}. {example['file']} ({example['concentration']}, {example['scan_rate']})")
            print(f"      Got: {example['ox_peaks']} Ox + {example['red_peaks']} Red")
            for peak in example['peak_details']:
                print(f"      {peak['type']}: {peak['voltage']}V, {peak['current']}μA")
    
    # Save detailed results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"comprehensive_peak_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = test_comprehensive_peak_detection()