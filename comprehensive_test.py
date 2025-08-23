#!/usr/bin/env python3
"""
Comprehensive Baseline Testing Script
Test baseline detection across all available test files
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def discover_test_files(base_path="Test_data", max_files_per_dir=None):
    """Discover all CSV test files"""
    test_files = []
    
    for instrument in ["Palmsens", "Stm32"]:
        instrument_path = Path(base_path) / instrument
        if not instrument_path.exists():
            continue
            
        for concentration_dir in instrument_path.iterdir():
            if concentration_dir.is_dir():
                csv_files = list(concentration_dir.glob("*.csv"))
                if max_files_per_dir:
                    csv_files = csv_files[:max_files_per_dir]
                
                for csv_file in csv_files:
                    test_files.append({
                        'path': str(csv_file),
                        'instrument': instrument,
                        'concentration': concentration_dir.name,
                        'filename': csv_file.name
                    })
    
    return test_files

def test_baseline_comprehensive(file_info):
    """Test baseline detection on a single file with comprehensive reporting"""
    from routes.peak_detection import detect_improved_baseline_2step
    
    file_path = file_info['path']
    
    try:
        # Load data
        df = pd.read_csv(file_path, skiprows=1)
        
        if 'A' in df.columns:
            v, i = df['V'].values, df['A'].values * 1e6  # STM32 format
            data_type = "STM32"
        elif 'uA' in df.columns:
            v, i = df['V'].values, df['uA'].values  # Palmsens format
            data_type = "Palmsens"
        else:
            return {
                'success': False,
                'error': 'Unknown data format',
                'file_info': file_info
            }
        
        # Test baseline detection
        start_time = time.time()
        baseline_result = detect_improved_baseline_2step(v, i)
        processing_time = time.time() - start_time
        
        if baseline_result is None:
            return {
                'success': False,
                'error': 'Baseline detection failed',
                'file_info': file_info,
                'processing_time': processing_time
            }
        
        bf, br, baseline_info = baseline_result
        
        # Analyze results
        n = len(v)
        mid_point = n // 2
        data_span = i.max() - i.min()
        
        # Quality metrics
        forward_span = bf.max() - bf.min()
        reverse_span = br.max() - br.min()
        
        forward_quality = "good" if forward_span < data_span * 0.15 else "fair" if forward_span < data_span * 0.3 else "poor"
        reverse_quality = "good" if reverse_span < data_span * 0.15 else "fair" if reverse_span < data_span * 0.3 else "poor"
        
        # Position validation
        if baseline_info.get('forward_segment'):
            f_start_pct = baseline_info['forward_segment'].get('start_idx', 0) / n
            f_end_pct = baseline_info['forward_segment'].get('end_idx', 0) / n
            forward_position_ok = f_end_pct <= 0.4
        else:
            f_start_pct = f_end_pct = 0
            forward_position_ok = False
            
        if baseline_info.get('reverse_segment'):
            r_start_pct = baseline_info['reverse_segment'].get('start_idx', 0) / n
            r_end_pct = baseline_info['reverse_segment'].get('end_idx', 0) / n
            reverse_position_ok = 0.55 <= r_start_pct <= 0.75
        else:
            r_start_pct = r_end_pct = 0
            reverse_position_ok = False
        
        return {
            'success': True,
            'file_info': file_info,
            'processing_time': processing_time,
            'data_points': n,
            'voltage_range': [v.min(), v.max()],
            'current_range': [i.min(), i.max()],
            'data_span': data_span,
            'forward': {
                'span': forward_span,
                'quality': forward_quality,
                'position_pct': [f_start_pct * 100, f_end_pct * 100],
                'position_ok': forward_position_ok,
                'r2': baseline_info.get('forward_segment', {}).get('r2', 0),
                'slope': baseline_info.get('forward_segment', {}).get('slope', 0)
            },
            'reverse': {
                'span': reverse_span,
                'quality': reverse_quality,
                'position_pct': [r_start_pct * 100, r_end_pct * 100],
                'position_ok': reverse_position_ok,
                'r2': baseline_info.get('reverse_segment', {}).get('r2', 0),
                'slope': baseline_info.get('reverse_segment', {}).get('slope', 0)
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'file_info': file_info,
            'processing_time': 0
        }

def run_comprehensive_test(max_files=None, max_files_per_dir=5):
    """Run comprehensive baseline testing"""
    
    print("🔬 COMPREHENSIVE BASELINE TESTING")
    print("=" * 80)
    
    # Discover test files
    test_files = discover_test_files(max_files_per_dir=max_files_per_dir)
    if max_files:
        test_files = test_files[:max_files]
    
    print(f"📁 Found {len(test_files)} test files")
    
    # Group by instrument and concentration
    by_instrument = {}
    for file_info in test_files:
        instrument = file_info['instrument']
        if instrument not in by_instrument:
            by_instrument[instrument] = {}
        
        concentration = file_info['concentration']
        if concentration not in by_instrument[instrument]:
            by_instrument[instrument][concentration] = []
        
        by_instrument[instrument][concentration].append(file_info)
    
    # Print test structure
    for instrument, concentrations in by_instrument.items():
        print(f"📊 {instrument}: {len(concentrations)} concentrations")
        for conc, files in concentrations.items():
            print(f"   📈 {conc}: {len(files)} files")
    
    print("\n" + "=" * 80)
    print("🚀 Starting comprehensive testing...")
    print("=" * 80)
    
    # Run tests
    results = []
    failed_files = []
    total_time = 0
    
    for i, file_info in enumerate(test_files):
        print(f"\n[{i+1}/{len(test_files)}] Testing: {file_info['filename']}")
        
        result = test_baseline_comprehensive(file_info)
        results.append(result)
        total_time += result.get('processing_time', 0)
        
        if result['success']:
            forward = result['forward']
            reverse = result['reverse']
            
            # Status indicators
            f_quality_icon = "🟢" if forward['quality'] == 'good' else "🟡" if forward['quality'] == 'fair' else "🔴"
            r_quality_icon = "🟢" if reverse['quality'] == 'good' else "🟡" if reverse['quality'] == 'fair' else "🔴"
            f_pos_icon = "✅" if forward['position_ok'] else "❌"
            r_pos_icon = "✅" if reverse['position_ok'] else "❌"
            
            print(f"   📊 {result['data_points']} points, span: {result['data_span']:.1f}µA")
            print(f"   📈 Forward: {forward['span']:.1f}µA {f_quality_icon}, pos: {forward['position_pct'][0]:.1f}-{forward['position_pct'][1]:.1f}% {f_pos_icon}")
            print(f"   📈 Reverse: {reverse['span']:.1f}µA {r_quality_icon}, pos: {reverse['position_pct'][0]:.1f}-{reverse['position_pct'][1]:.1f}% {r_pos_icon}")
        else:
            print(f"   ❌ FAILED: {result['error']}")
            failed_files.append(result)
    
    # Generate comprehensive report
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE ANALYSIS REPORT")
    print("=" * 80)
    
    successful_results = [r for r in results if r['success']]
    
    print(f"📁 Total files tested: {len(test_files)}")
    print(f"✅ Successful: {len(successful_results)}")
    print(f"❌ Failed: {len(failed_files)}")
    print(f"⏱️  Total processing time: {total_time:.2f}s")
    print(f"⚡ Average time per file: {total_time/len(test_files):.3f}s")
    
    if successful_results:
        # Quality analysis
        forward_qualities = [r['forward']['quality'] for r in successful_results]
        reverse_qualities = [r['reverse']['quality'] for r in successful_results]
        
        f_good = sum(1 for q in forward_qualities if q == 'good')
        f_fair = sum(1 for q in forward_qualities if q == 'fair')
        f_poor = sum(1 for q in forward_qualities if q == 'poor')
        
        r_good = sum(1 for q in reverse_qualities if q == 'good')
        r_fair = sum(1 for q in reverse_qualities if q == 'fair')
        r_poor = sum(1 for q in reverse_qualities if q == 'poor')
        
        print(f"\n📈 Forward Quality: 🟢{f_good} 🟡{f_fair} 🔴{f_poor}")
        print(f"📈 Reverse Quality: 🟢{r_good} 🟡{r_fair} 🔴{r_poor}")
        
        # Position analysis
        forward_pos_ok = sum(1 for r in successful_results if r['forward']['position_ok'])
        reverse_pos_ok = sum(1 for r in successful_results if r['reverse']['position_ok'])
        
        print(f"\n📍 Position Accuracy:")
        print(f"   Forward: {forward_pos_ok}/{len(successful_results)} ({forward_pos_ok/len(successful_results)*100:.1f}%)")
        print(f"   Reverse: {reverse_pos_ok}/{len(successful_results)} ({reverse_pos_ok/len(successful_results)*100:.1f}%)")
        
        # Instrument comparison
        palmsens_results = [r for r in successful_results if r['file_info']['instrument'] == 'Palmsens']
        stm32_results = [r for r in successful_results if r['file_info']['instrument'] == 'Stm32']
        
        if palmsens_results and stm32_results:
            print(f"\n🔬 Instrument Comparison:")
            print(f"   Palmsens: {len(palmsens_results)} files")
            print(f"   STM32: {len(stm32_results)} files")
            
            # Average quality by instrument
            for name, results in [("Palmsens", palmsens_results), ("STM32", stm32_results)]:
                f_spans = [r['forward']['span'] for r in results]
                r_spans = [r['reverse']['span'] for r in results]
                print(f"   {name} avg spans: F={np.mean(f_spans):.1f}µA, R={np.mean(r_spans):.1f}µA")
    
    # Failed files analysis
    if failed_files:
        print(f"\n❌ Failed Files Analysis:")
        error_types = {}
        for failed in failed_files:
            error = failed['error']
            if error not in error_types:
                error_types[error] = []
            error_types[error].append(failed['file_info']['filename'])
        
        for error, files in error_types.items():
            print(f"   {error}: {len(files)} files")
            for filename in files[:3]:  # Show first 3
                print(f"      - {filename}")
            if len(files) > 3:
                print(f"      ... and {len(files)-3} more")
    
    success_rate = len(successful_results) / len(test_files) * 100
    print(f"\n🎯 Overall Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 95:
        print("🎉 EXCELLENT! Algorithm is very robust")
    elif success_rate >= 85:
        print("✅ GOOD! Algorithm is quite robust")
    elif success_rate >= 70:
        print("⚠️  FAIR! Some improvements needed")
    else:
        print("🔴 POOR! Significant improvements required")
    
    return results

def main():
    """Main function"""
    max_files = None
    max_files_per_dir = 10  # Test up to 10 files per concentration
    
    if len(sys.argv) > 1:
        try:
            max_files = int(sys.argv[1])
        except:
            max_files_per_dir = int(sys.argv[1])
    
    run_comprehensive_test(max_files=max_files, max_files_per_dir=max_files_per_dir)

if __name__ == "__main__":
    main()