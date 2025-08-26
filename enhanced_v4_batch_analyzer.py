#!/usr/bin/env python3
"""
Enhanced Batch Baseline Analysis using v4 Algorithm
==================================================
Uses cv_baseline_detector_v4 for improved baseline detection
"""

import os
import glob
import json
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from scipy.stats import linregress

# Try to import the advanced v4 algorithm
try:
    from baseline_detector_v4 import cv_baseline_detector_v4
    from baseline_detector_voltage_windows import voltage_window_baseline_detector as voltage_window_detector
    ADVANCED_BASELINE_AVAILABLE = True
    print("✅ Advanced baseline detector v4 loaded")
except ImportError:
    ADVANCED_BASELINE_AVAILABLE = False
    print("⚠️ Advanced baseline detector not available, using fallback")

def parse_csv_robust(file_path):
    """Robust CSV parser for different formats"""
    try:
        filename = os.path.basename(file_path)
        print(f"   📄 Parsing: {filename}")
        
        # Check if this is a Palmsens file (has header format)
        if 'Palmsens' in filename:
            # Palmsens format: 2-line header, then data
            df = pd.read_csv(file_path, skiprows=1)  # Skip the filename line
            print(f"   📊 Palmsens format detected")
        else:
            # STM32 format: regular CSV
            df = pd.read_csv(file_path)
            print(f"   📊 STM32 format detected")
        
        print(f"   📋 Shape: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"   📊 Columns: {list(df.columns)}")
        
        # Find voltage and current columns
        voltage_col, current_col = None, None
        
        # Column mapping for different formats
        voltage_patterns = ['v', 'voltage', 'potential', 'volt', 'e', 'wevolt']
        current_patterns = ['ua', 'current', 'i', 'wecurrent', 'we current']
        
        columns_lower = [col.lower().strip() for col in df.columns]
        
        # Find voltage column
        for pattern in voltage_patterns:
            for i, col in enumerate(columns_lower):
                if pattern in col:
                    voltage_col = df.columns[i]
                    break
            if voltage_col:
                break
        
        # Find current column  
        for pattern in current_patterns:
            for i, col in enumerate(columns_lower):
                if pattern in col:
                    current_col = df.columns[i]
                    break
            if current_col:
                break
        
        print(f"   🔍 Voltage column: {voltage_col}")
        print(f"   🔍 Current column: {current_col}")
        
        if voltage_col is None or current_col is None:
            return None, None, f"Could not identify columns from: {df.columns.tolist()}"
        
        # Extract and convert data
        voltage = pd.to_numeric(df[voltage_col], errors='coerce').dropna()
        current = pd.to_numeric(df[current_col], errors='coerce').dropna()
        
        # Convert uA to keep original units for v4 (v4 expects µA)
        if current_col.lower() == 'ua':
            print(f"   🔄 Keeping uA units for V4 algorithm")
            # Don't convert to A - v4 expects µA
        else:
            current = current * 1e-6  # Convert other units to A only if not µA
            print(f"   🔄 Converted to A")
        
        # Align lengths
        min_len = min(len(voltage), len(current))
        voltage = voltage.iloc[:min_len].values
        current = current.iloc[:min_len].values
        
        print(f"   📈 Data points: {len(voltage)}")
        print(f"   ⚡ Voltage range: [{voltage.min():.3f}, {voltage.max():.3f}] V")
        print(f"   ⚡ Current range: [{current.min():.2f}, {current.max():.2f}] µA" if current_col.lower() == 'ua' 
               else f"   ⚡ Current range: [{current.min():.2e}, {current.max():.2e}] A")
        
        if len(voltage) < 10:
            return None, None, "Insufficient data points"
        
        return voltage, current, None
        
    except Exception as e:
        return None, None, f"Error parsing CSV: {str(e)}"

def enhanced_baseline_detector(voltage, current):
    """Enhanced baseline detection using v4 algorithm when available"""
    
    if ADVANCED_BASELINE_AVAILABLE:
        try:
            print("   🧠 Using advanced v4 baseline detector")
            
            # Use the advanced v4 algorithm
            forward_baseline, reverse_baseline, info = cv_baseline_detector_v4(voltage, current)
            
            # Extract R² from v4 info (which already calculated correctly)
            forward_r2 = info.get('forward_segment', {}).get('r2', 0.0)
            reverse_r2 = info.get('reverse_segment', {}).get('r2', 0.0)
            avg_r2 = (forward_r2 + reverse_r2) / 2.0
            
            print(f"   📊 V4 Results: Forward R²={forward_r2:.3f}, Reverse R²={reverse_r2:.3f}, Avg={avg_r2:.3f}")
            
            # Create compatible baseline segments for plotting
            baseline_segments = []
            segment_r2 = [forward_r2, reverse_r2]
            
            # Forward segment
            if len(forward_baseline) > 0:
                n = len(voltage)
                mid = n // 2
                forward_voltages = voltage[:mid]
                forward_mask = ~np.isnan(forward_baseline)
                if np.any(forward_mask) and len(forward_voltages) == len(forward_baseline):
                    baseline_segments.append({
                        'voltage_values': forward_voltages[forward_mask],
                        'current_values': forward_baseline[forward_mask]
                    })
                
            # Reverse segment  
            if len(reverse_baseline) > 0:
                n = len(voltage)
                mid = n // 2
                reverse_voltages = voltage[mid:]
                reverse_mask = ~np.isnan(reverse_baseline)
                if np.any(reverse_mask) and len(reverse_voltages) == len(reverse_baseline):
                    baseline_segments.append({
                        'voltage_values': reverse_voltages[reverse_mask],
                        'current_values': reverse_baseline[reverse_mask]
                    })
            
            return {
                'baseline_segments': baseline_segments,
                'segment_r2': segment_r2,
                'forward_r2': forward_r2,
                'reverse_r2': reverse_r2,
                'avg_r2': avg_r2,
                'method': 'v4_enhanced',
                'info': info
            }
            
        except Exception as e:
            print(f"   ⚠️ V4 algorithm failed: {e}, falling back to simple method")
    
    # Fallback to simple method
    print("   📐 Using fallback baseline detector")
    baseline_segments = []
    
    # Simple voltage window approach
    v_min, v_max = min(voltage), max(voltage)
    v_range = v_max - v_min
    window_size = v_range / 15  # 15 windows
    
    for i in range(15):
        window_start = v_min + i * window_size
        window_end = window_start + window_size
        
        # Find points in this window
        mask = (voltage >= window_start) & (voltage <= window_end)
        window_current = current[mask]
        window_voltage = voltage[mask]
        
        if len(window_current) > 5:
            # Check if current is relatively stable (low std)
            current_std = np.std(window_current)
            current_mean = np.mean(window_current)
            
            # Relative stability check
            if current_std < abs(current_mean) * 0.1 + 1e-9:
                baseline_segments.append({
                    'voltage_values': window_voltage,
                    'current_values': window_current
                })
    
    # Calculate R² for each segment
    segment_r2 = []
    for segment in baseline_segments:
        if len(segment['voltage_values']) > 3:
            try:
                slope, intercept, r_value, p_value, std_err = linregress(
                    segment['voltage_values'], segment['current_values']
                )
                segment_r2.append(r_value ** 2)
            except:
                segment_r2.append(0.0)
        else:
            segment_r2.append(0.0)
    
    avg_r2 = np.mean(segment_r2) if segment_r2 else 0.0
    
    return {
        'baseline_segments': baseline_segments,
        'segment_r2': segment_r2,
        'forward_r2': 0.0,
        'reverse_r2': 0.0,
        'avg_r2': avg_r2,
        'method': 'fallback_simple',
        'info': {}
    }

def analyze_file_baseline(file_path):
    """Analyze baseline for a single file using enhanced detector"""
    
    # Parse CSV
    voltage, current, error = parse_csv_robust(file_path)
    if error:
        return None, error
    
    # Enhanced baseline detection
    baseline_result = enhanced_baseline_detector(voltage, current)
    
    if len(baseline_result['baseline_segments']) == 0:
        return None, "No baseline segments detected"
    
    # Overall statistics
    avg_r2 = baseline_result['avg_r2']
    
    # Determine quality
    if avg_r2 >= 0.9:
        quality = "EXCELLENT 🟢"
    elif avg_r2 >= 0.7:
        quality = "GOOD ✅"
    elif avg_r2 >= 0.5:
        quality = "FAIR ⚠️"
    else:
        quality = "POOR ❌"
    
    # Extract scan rate from filename
    scan_rate = "Unknown"
    filename = os.path.basename(file_path)
    if 'mVpS' in filename:
        import re
        match = re.search(r'(\d+)mVpS', filename, re.IGNORECASE)
        if match:
            scan_rate = f"{match.group(1)}mVpS"
    
    result = {
        'avg_r2': avg_r2,
        'forward_r2': baseline_result['forward_r2'],
        'reverse_r2': baseline_result['reverse_r2'],
        'num_segments': len(baseline_result['baseline_segments']),
        'quality': quality,
        'scan_rate': scan_rate,
        'total_points': len(voltage),
        'method': baseline_result['method'],
        'baseline_segments': baseline_result['baseline_segments'],
        'segment_r2': baseline_result['segment_r2']
    }
    
    return result, None

def create_baseline_plot(file_path, result, output_dir):
    """Create enhanced baseline plot with v4 results"""
    
    # Parse data again for plotting
    voltage, current, _ = parse_csv_robust(file_path)
    if voltage is None:
        return None
    
    # Create plot
    plt.figure(figsize=(12, 8))
    
    # Plot main CV curve
    plt.plot(voltage, current, 'b-', linewidth=0.8, alpha=0.7, label='CV Curve')
    
    # Highlight baseline segments
    colors = ['red', 'green', 'orange', 'purple', 'brown', 'pink']
    for i, (segment, r2) in enumerate(zip(result['baseline_segments'], result['segment_r2'])):
        color = colors[i % len(colors)]
        v_vals = segment['voltage_values']
        i_vals = segment['current_values']
        
        plt.scatter(v_vals, i_vals, c=color, s=20, alpha=0.8, 
                   label=f'Baseline {i+1} (R²={r2:.3f})')
    
    # Enhanced annotation with method info
    method_info = result.get('method', 'unknown')
    annotation_text = f"Method: {method_info}\n"
    annotation_text += f"Overall R² = {result['avg_r2']:.3f}\n"
    if result['forward_r2'] > 0 or result['reverse_r2'] > 0:
        annotation_text += f"Forward R² = {result['forward_r2']:.3f}\n"
        annotation_text += f"Reverse R² = {result['reverse_r2']:.3f}\n"
    annotation_text += f"{result['quality']}"
    
    plt.text(0.02, 0.98, annotation_text, 
             transform=plt.gca().transAxes, fontsize=11, 
             verticalalignment='top', 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Labels and formatting
    plt.xlabel('Voltage (V)')
    plt.ylabel('Current (µA)' if 'ua' in file_path.lower() or 'palmsens' in file_path.lower() 
               else 'Current (A)')
    filename = os.path.basename(file_path)
    plt.title(f'Enhanced Baseline Analysis: {filename}')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save plot
    plot_filename = os.path.splitext(filename)[0] + '_enhanced_baseline.png'
    plot_path = os.path.join(output_dir, plot_filename)
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return plot_path

def find_all_csv_files(root_dir="Test_data"):
    """Find all CSV files in Test_data directory"""
    csv_files = []
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.csv') and not file.endswith('.backup'):
                csv_files.append(os.path.join(root, file))
    
    return sorted(csv_files)

def create_summary_report(results, output_dir):
    """Create comprehensive summary report"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Calculate statistics
    total_files = len(results)
    successful = len([r for r in results if r['result'] is not None])
    failed = total_files - successful
    
    # Quality distribution
    quality_counts = {'EXCELLENT': 0, 'GOOD': 0, 'FAIR': 0, 'POOR': 0}
    r2_values = []
    method_counts = {}
    
    for r in results:
        if r['result']:
            # Quality count
            quality = r['result']['quality'].split()[0]  # Remove emoji
            if quality in quality_counts:
                quality_counts[quality] += 1
            
            # R² values
            avg_r2 = r['result']['avg_r2']
            r2_values.append(avg_r2)
            
            # Method count
            method = r['result'].get('method', 'unknown')
            method_counts[method] = method_counts.get(method, 0) + 1
    
    # Create report
    report = {
        'timestamp': timestamp,
        'enhanced_analysis': True,
        'v4_algorithm_used': ADVANCED_BASELINE_AVAILABLE,
        'summary': {
            'total_files': total_files,
            'successful_analyses': successful,
            'failed_analyses': failed,
            'success_rate': round((successful / total_files) * 100, 1) if total_files > 0 else 0
        },
        'algorithm_performance': {
            'methods_used': method_counts,
            'v4_success_rate': round((method_counts.get('v4_enhanced', 0) / successful) * 100, 1) if successful > 0 else 0
        },
        'quality_distribution': {
            'counts': quality_counts,
            'percentages': {k: round((v / successful) * 100, 1) if successful > 0 else 0 
                          for k, v in quality_counts.items()}
        },
        'r2_statistics': {
            'mean': round(np.mean(r2_values), 3) if r2_values else 0,
            'median': round(np.median(r2_values), 3) if r2_values else 0,
            'std': round(np.std(r2_values), 3) if r2_values else 0,
            'min': round(min(r2_values), 3) if r2_values else 0,
            'max': round(max(r2_values), 3) if r2_values else 0
        }
    }
    
    # Save report
    report_file = os.path.join(output_dir, f"enhanced_baseline_report_{timestamp}.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report, report_file

def main():
    """Main enhanced batch processing function"""
    
    print("🚀 Enhanced Batch Baseline Analysis using V4 Algorithm")
    print("=" * 60)
    
    # Find all CSV files - limit to first 20 for testing
    all_csv_files = find_all_csv_files()
    csv_files = all_csv_files[:20]  # Test with first 20 files
    
    print(f"📁 Testing with {len(csv_files)} files (limited from {len(all_csv_files)} total)")
    
    if len(csv_files) == 0:
        print("❌ No CSV files found in Test_data directory")
        return
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"enhanced_baseline_test_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"📂 Output directory: {output_dir}")
    
    # Process files
    results = []
    
    for i, file_path in enumerate(csv_files):
        print(f"\n📁 Processing ({i+1}/{len(csv_files)}): {os.path.basename(file_path)}")
        
        try:
            # Analyze baseline
            result, error = analyze_file_baseline(file_path)
            
            if result:
                # Create plot
                plot_path = create_baseline_plot(file_path, result, output_dir)
                print(f"   ✅ Success: {result['quality']} (R²={result['avg_r2']:.3f}, Method={result['method']})")
                if plot_path:
                    print(f"   📊 Plot saved: {os.path.basename(plot_path)}")
                
                results.append({
                    'file_path': file_path,
                    'result': result,
                    'error': None,
                    'plot_path': plot_path
                })
            else:
                print(f"   ❌ Failed: {error}")
                results.append({
                    'file_path': file_path,
                    'result': None,
                    'error': error,
                    'plot_path': None
                })
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            results.append({
                'file_path': file_path,
                'result': None,
                'error': str(e),
                'plot_path': None
            })
    
    # Generate comprehensive report
    print(f"\n📋 Generating enhanced report...")
    report, report_file = create_summary_report(results, output_dir)
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎉 ENHANCED BATCH ANALYSIS COMPLETE")
    print(f"📂 Output directory: {output_dir}")
    print(f"📋 Report file: {report_file}")
    print(f"📊 Success rate: {report['summary']['success_rate']}%")
    print(f"🧠 V4 Algorithm used: {ADVANCED_BASELINE_AVAILABLE}")
    
    if ADVANCED_BASELINE_AVAILABLE and 'algorithm_performance' in report:
        print(f"🎯 V4 Success rate: {report['algorithm_performance']['v4_success_rate']}%")
        print(f"📈 Methods used: {report['algorithm_performance']['methods_used']}")
    
    # Print key statistics
    if report['r2_statistics']['mean'] > 0:
        print(f"\n📈 R² STATISTICS:")
        print(f"   Mean: {report['r2_statistics']['mean']:.3f}")
        print(f"   Range: [{report['r2_statistics']['min']:.3f}, {report['r2_statistics']['max']:.3f}]")
    
    print(f"\n🔍 Check {output_dir}/ for enhanced plots and detailed report!")

if __name__ == "__main__":
    main()