#!/usr/bin/env python3
"""
Standalone Batch Baseline Analysis for all CSV files in Test_data
Creates enhanced plots with R² values and generates comprehensive report
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

def parse_csv_robust(file_path):
    """Robust CSV parser for different formats"""
    try:
        # Try reading with different encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        # Check if we have voltage and current columns
        voltage_col, current_col = None, None
        
        # Common column name patterns
        voltage_patterns = ['potential', 'voltage', 'volt', 'e', 'v', 'wevolt']
        current_patterns = ['current', 'i', 'wecurrent', 'we current']
        
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
        
        if voltage_col is None or current_col is None:
            return None, None, "Could not identify voltage/current columns"
        
        # Extract data
        voltage = pd.to_numeric(df[voltage_col], errors='coerce').dropna()
        current = pd.to_numeric(df[current_col], errors='coerce').dropna()
        
        # Align lengths
        min_len = min(len(voltage), len(current))
        voltage = voltage.iloc[:min_len]
        current = current.iloc[:min_len]
        
        if len(voltage) < 10:
            return None, None, "Insufficient data points"
        
        return voltage.values, current.values, None
        
    except Exception as e:
        return None, None, f"Error parsing CSV: {str(e)}"

def voltage_window_baseline_detector(voltage, current, window_size=0.05):
    """Detect baseline regions using voltage windows"""
    baseline_segments = []
    
    # Split voltage range into windows
    v_min, v_max = min(voltage), max(voltage)
    v_range = v_max - v_min
    num_windows = max(10, int(v_range / window_size))
    
    for i in range(num_windows):
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
            if current_std < abs(current_mean) * 0.1 + 1e-6:
                baseline_segments.append({
                    'voltage_range': (window_start, window_end),
                    'voltage_values': window_voltage,
                    'current_values': window_current,
                    'stability': current_std
                })
    
    return baseline_segments

def calculate_r2_for_segment(voltage, current):
    """Calculate R² for a single baseline segment"""
    if len(voltage) < 3:
        return 0.0
    
    try:
        slope, intercept, r_value, p_value, std_err = linregress(voltage, current)
        return r_value ** 2
    except:
        return 0.0

def analyze_file_baseline(file_path):
    """Analyze baseline for a single file"""
    
    # Parse CSV
    voltage, current, error = parse_csv_robust(file_path)
    if error:
        return None, error
    
    # Detect baselines
    baseline_segments = voltage_window_baseline_detector(voltage, current)
    
    if len(baseline_segments) == 0:
        return None, "No baseline segments detected"
    
    # Calculate R² for each segment
    segment_r2 = []
    for segment in baseline_segments:
        r2 = calculate_r2_for_segment(segment['voltage_values'], segment['current_values'])
        segment_r2.append(r2)
    
    # Overall statistics
    avg_r2 = np.mean(segment_r2) if segment_r2 else 0.0
    max_r2 = max(segment_r2) if segment_r2 else 0.0
    
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
        'max_r2': max_r2,
        'num_segments': len(baseline_segments),
        'quality': quality,
        'scan_rate': scan_rate,
        'total_points': len(voltage),
        'baseline_segments': baseline_segments,
        'segment_r2': segment_r2
    }
    
    return result, None

def create_baseline_plot(file_path, result, output_dir):
    """Create baseline plot with R² annotation"""
    
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
    
    # Add overall R² annotation
    plt.text(0.02, 0.98, f"Overall R² = {result['avg_r2']:.3f}\n{result['quality']}", 
             transform=plt.gca().transAxes, fontsize=12, 
             verticalalignment='top', 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Labels and formatting
    plt.xlabel('Voltage (V)')
    plt.ylabel('Current (A)')
    filename = os.path.basename(file_path)
    plt.title(f'Baseline Analysis: {filename}')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save plot
    plot_filename = os.path.splitext(filename)[0] + '_baseline_analysis.png'
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
    scan_rate_performance = {}
    
    for r in results:
        if r['result']:
            # Quality count
            quality = r['result']['quality'].split()[0]  # Remove emoji
            if quality in quality_counts:
                quality_counts[quality] += 1
            
            # R² values
            avg_r2 = r['result']['avg_r2']
            r2_values.append(avg_r2)
            
            # Scan rate performance
            scan_rate = r['result']['scan_rate']
            if scan_rate not in scan_rate_performance:
                scan_rate_performance[scan_rate] = []
            scan_rate_performance[scan_rate].append(avg_r2)
    
    # Create report
    report = {
        'timestamp': timestamp,
        'summary': {
            'total_files': total_files,
            'successful_analyses': successful,
            'failed_analyses': failed,
            'success_rate': round((successful / total_files) * 100, 1) if total_files > 0 else 0
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
        },
        'scan_rate_performance': {
            rate: {
                'count': len(values),
                'mean_r2': round(np.mean(values), 3),
                'std_r2': round(np.std(values), 3)
            } for rate, values in scan_rate_performance.items()
        },
        'detailed_results': [
            {
                'file': os.path.basename(r['file_path']),
                'success': r['result'] is not None,
                'quality': r['result']['quality'] if r['result'] else 'FAILED',
                'avg_r2': r['result']['avg_r2'] if r['result'] else 0,
                'num_segments': r['result']['num_segments'] if r['result'] else 0,
                'total_points': r['result']['total_points'] if r['result'] else 0,
                'scan_rate': r['result']['scan_rate'] if r['result'] else 'Unknown',
                'error': r['error']
            } for r in results
        ]
    }
    
    # Save report
    report_file = os.path.join(output_dir, f"batch_baseline_analysis_report_{timestamp}.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report, report_file

def main():
    """Main batch processing function"""
    
    print("🚀 Standalone Batch Baseline Analysis for Test_data")
    print("=" * 60)
    
    # Find all CSV files
    csv_files = find_all_csv_files()
    print(f"📁 Found {len(csv_files)} CSV files in Test_data")
    
    if len(csv_files) == 0:
        print("❌ No CSV files found in Test_data directory")
        return
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"batch_baseline_results_{timestamp}"
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
                print(f"   ✅ Success: {result['quality']} (R²={result['avg_r2']:.3f})")
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
        
        # Print progress every 10 files
        if (i + 1) % 10 == 0 or i == len(csv_files) - 1:
            successful = len([r for r in results if r['result'] is not None])
            print(f"\n📊 Progress: {successful}/{i+1} successful ({successful/(i+1)*100:.1f}%)")
    
    # Generate comprehensive report
    print(f"\n📋 Generating comprehensive report...")
    report, report_file = create_summary_report(results, output_dir)
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎉 BATCH ANALYSIS COMPLETE")
    print(f"📂 Output directory: {output_dir}")
    print(f"📋 Report file: {report_file}")
    print(f"📊 Success rate: {report['summary']['success_rate']}%")
    
    # Print key statistics
    if report['r2_statistics']['mean'] > 0:
        print(f"\n📈 R² STATISTICS:")
        print(f"   Mean: {report['r2_statistics']['mean']:.3f}")
        print(f"   Range: [{report['r2_statistics']['min']:.3f}, {report['r2_statistics']['max']:.3f}]")
    
    # Print quality breakdown
    print(f"\n🎯 QUALITY BREAKDOWN:")
    for quality, count in report['quality_distribution']['counts'].items():
        percentage = report['quality_distribution']['percentages'][quality]
        emoji = {"EXCELLENT": "🟢", "GOOD": "✅", "FAIR": "⚠️", "POOR": "❌"}[quality]
        print(f"   {emoji} {quality}: {count} ({percentage:.1f}%)")
    
    # Print top performing files
    successful_results = [r for r in results if r['result'] is not None]
    if successful_results:
        top_files = sorted(successful_results, key=lambda x: x['result']['avg_r2'], reverse=True)[:5]
        print(f"\n🏆 TOP 5 PERFORMING FILES:")
        for i, r in enumerate(top_files):
            filename = os.path.basename(r['file_path'])[:40]
            print(f"   {i+1}. {filename:40} | R²={r['result']['avg_r2']:.3f} | {r['result']['quality']}")
    
    print(f"\n🔍 Check {output_dir}/ for individual plots and detailed report!")

if __name__ == "__main__":
    main()