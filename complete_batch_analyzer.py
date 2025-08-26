#!/usr/bin/env python3
"""
FINAL: Complete Batch Baseline Analysis
Handles both Palmsens and STM32 formats correctly with proper R² calculation
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import linregress

def parse_csv_robust(file_path):
    """Robust CSV parser for both Palmsens and STM32 formats"""
    try:
        filename = os.path.basename(file_path)
        
        # Both formats have a header line with filename, skip it
        df = pd.read_csv(file_path, skiprows=1)
        
        # Find voltage and current columns
        voltage_col, current_col = None, None
        columns_lower = [col.lower().strip() for col in df.columns]
        
        # Standard column mapping: V = voltage, uA = current
        for i, col in enumerate(columns_lower):
            if col == 'v':
                voltage_col = df.columns[i]
            elif col == 'ua':
                current_col = df.columns[i]
        
        if voltage_col is None or current_col is None:
            return None, None, f"Could not find V,uA columns in: {df.columns.tolist()}"
        
        # Extract and convert data
        voltage = pd.to_numeric(df[voltage_col], errors='coerce').dropna()
        current = pd.to_numeric(df[current_col], errors='coerce').dropna()
        
        # Convert uA to A
        current = current * 1e-6
        
        # Align lengths
        min_len = min(len(voltage), len(current))
        voltage = voltage.iloc[:min_len].values
        current = current.iloc[:min_len].values
        
        if len(voltage) < 10:
            return None, None, "Insufficient data points"
        
        return voltage, current, None
        
    except Exception as e:
        return None, None, f"Error parsing CSV: {str(e)}"

def improved_baseline_detector(voltage, current, window_size=0.05, stability_threshold=0.15):
    """Improved baseline detector with better parameters"""
    baseline_segments = []
    
    # Sort by voltage for consistent windowing
    sorted_indices = np.argsort(voltage)
    v_sorted = voltage[sorted_indices]
    i_sorted = current[sorted_indices]
    
    # Split voltage range into windows
    v_min, v_max = v_sorted.min(), v_sorted.max()
    v_range = v_max - v_min
    num_windows = max(20, int(v_range / window_size))  # More windows for better detection
    
    for i in range(num_windows):
        window_start = v_min + i * (v_range / num_windows)
        window_end = window_start + (v_range / num_windows)
        
        # Find points in this window
        mask = (v_sorted >= window_start) & (v_sorted <= window_end)
        window_current = i_sorted[mask]
        window_voltage = v_sorted[mask]
        
        if len(window_current) > 3:
            # Check if current is relatively stable
            current_std = np.std(window_current)
            current_mean = abs(np.mean(window_current))
            
            # Adaptive stability check
            if current_mean > 0:
                relative_std = current_std / current_mean
            else:
                relative_std = current_std / (abs(i_sorted).max() + 1e-9)
            
            # More lenient baseline detection
            if relative_std < stability_threshold or current_std < 1e-7:
                baseline_segments.append({
                    'voltage_range': (window_start, window_end),
                    'voltage_values': window_voltage,
                    'current_values': window_current,
                    'stability': relative_std
                })
    
    return baseline_segments

def calculate_r2_for_segment(voltage, current):
    """Calculate R² for a single baseline segment"""
    if len(voltage) < 3:
        return 0.0
    
    try:
        slope, intercept, r_value, p_value, std_err = linregress(voltage, current)
        return max(0.0, r_value ** 2)  # Ensure non-negative
    except:
        return 0.0

def analyze_file_baseline(file_path):
    """Analyze baseline for a single file"""
    
    # Parse CSV
    voltage, current, error = parse_csv_robust(file_path)
    if error:
        return None, error
    
    # Detect baselines with improved algorithm
    baseline_segments = improved_baseline_detector(voltage, current)
    
    if len(baseline_segments) == 0:
        # Try with more lenient parameters
        baseline_segments = improved_baseline_detector(voltage, current, stability_threshold=0.3)
    
    if len(baseline_segments) == 0:
        return None, "No baseline segments detected even with lenient parameters"
    
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
        quality = "EXCELLENT"
    elif avg_r2 >= 0.7:
        quality = "GOOD"
    elif avg_r2 >= 0.5:
        quality = "FAIR"
    else:
        quality = "POOR"
    
    # Extract scan rate from filename
    scan_rate = "Unknown"
    filename = os.path.basename(file_path)
    if 'mVpS' in filename:
        import re
        match = re.search(r'(\d+)mVpS', filename, re.IGNORECASE)
        if match:
            scan_rate = f"{match.group(1)}mV/s"
    
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
    plt.plot(voltage, current * 1e6, 'b-', linewidth=0.8, alpha=0.7, label='CV Curve')  # Convert back to uA for display
    
    # Highlight baseline segments
    colors = ['red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan']
    for i, (segment, r2) in enumerate(zip(result['baseline_segments'], result['segment_r2'])):
        color = colors[i % len(colors)]
        v_vals = segment['voltage_values']
        i_vals = segment['current_values'] * 1e6  # Convert back to uA for display
        
        plt.scatter(v_vals, i_vals, c=color, s=25, alpha=0.8, 
                   label=f'Baseline {i+1} (R²={r2:.3f})')
    
    # Quality emoji mapping
    quality_emoji = {
        "EXCELLENT": "🟢", "GOOD": "✅", 
        "FAIR": "⚠️", "POOR": "❌"
    }
    emoji = quality_emoji.get(result['quality'], "")
    
    # Add overall R² annotation (avoid emoji for file saving)
    plt.text(0.02, 0.98, f"Overall R² = {result['avg_r2']:.3f}\n{result['quality']} {emoji}\nSegments: {result['num_segments']}", 
             transform=plt.gca().transAxes, fontsize=12, 
             verticalalignment='top', 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Labels and formatting
    plt.xlabel('Voltage (V)')
    plt.ylabel('Current (µA)')
    filename = os.path.basename(file_path)
    plt.title(f'Baseline Analysis: {filename[:50]}{"..." if len(filename) > 50 else ""}')
    plt.grid(True, alpha=0.3)
    
    # Smart legend
    if len(result['baseline_segments']) <= 8:
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    else:
        plt.legend(['CV Curve'] + [f'Baseline {i+1}' for i in range(len(result['baseline_segments']))])
    
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
    instrument_performance = {'Palmsens': [], 'STM32': []}
    
    for r in results:
        if r['result']:
            quality = r['result']['quality']
            quality_counts[quality] += 1
            
            avg_r2 = r['result']['avg_r2']
            r2_values.append(avg_r2)
            
            # Scan rate performance
            scan_rate = r['result']['scan_rate']
            if scan_rate not in scan_rate_performance:
                scan_rate_performance[scan_rate] = []
            scan_rate_performance[scan_rate].append(avg_r2)
            
            # Instrument performance
            filename = os.path.basename(r['file_path'])
            if 'Palmsens' in filename:
                instrument_performance['Palmsens'].append(avg_r2)
            else:
                instrument_performance['STM32'].append(avg_r2)
    
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
                'std_r2': round(np.std(values), 3) if len(values) > 1 else 0
            } for rate, values in scan_rate_performance.items()
        },
        'instrument_performance': {
            inst: {
                'count': len(values),
                'mean_r2': round(np.mean(values), 3) if values else 0,
                'std_r2': round(np.std(values), 3) if len(values) > 1 else 0
            } for inst, values in instrument_performance.items() if values
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
                'error': r['error'] if 'error' in r else None
            } for r in results
        ]
    }
    
    # Save report
    report_file = os.path.join(output_dir, f"comprehensive_baseline_report_{timestamp}.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report, report_file

def main():
    """Main batch processing function"""
    
    print("🚀 COMPLETE BATCH BASELINE ANALYSIS")
    print("=" * 60)
    
    # Find all CSV files
    csv_files = find_all_csv_files()
    print(f"📁 Found {len(csv_files)} CSV files in Test_data")
    
    if len(csv_files) == 0:
        print("❌ No CSV files found in Test_data directory")
        return
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"complete_baseline_analysis_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"📂 Output directory: {output_dir}")
    
    # Process files
    results = []
    successful_count = 0
    
    for i, file_path in enumerate(csv_files):
        filename = os.path.basename(file_path)
        print(f"\n📁 [{i+1:3d}/{len(csv_files)}] {filename}")
        
        try:
            # Analyze baseline
            result, error = analyze_file_baseline(file_path)
            
            if result:
                # Create plot
                plot_path = create_baseline_plot(file_path, result, output_dir)
                successful_count += 1
                
                print(f"    ✅ {result['quality']} (R²={result['avg_r2']:.3f}, {result['num_segments']} segments)")
                
                results.append({
                    'file_path': file_path,
                    'result': result,
                    'plot_path': plot_path
                })
            else:
                print(f"    ❌ Failed: {error}")
                results.append({
                    'file_path': file_path,
                    'result': None,
                    'error': error
                })
                
        except Exception as e:
            print(f"    ❌ Exception: {str(e)}")
            results.append({
                'file_path': file_path,
                'result': None,
                'error': str(e)
            })
        
        # Progress update every 25 files
        if (i + 1) % 25 == 0:
            progress = ((i + 1) / len(csv_files)) * 100
            print(f"\n📊 Progress: {progress:.1f}% ({successful_count}/{i+1} successful)")
    
    # Generate comprehensive report
    print(f"\n📋 Generating comprehensive report...")
    report, report_file = create_summary_report(results, output_dir)
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎉 COMPLETE BATCH ANALYSIS FINISHED!")
    print(f"📂 Output directory: {output_dir}")
    print(f"📋 Report file: {os.path.basename(report_file)}")
    print(f"📊 Success rate: {report['summary']['success_rate']}% ({report['summary']['successful_analyses']}/{report['summary']['total_files']})")
    
    # Print key statistics
    if report['r2_statistics']['mean'] > 0:
        print(f"\n📈 R² STATISTICS:")
        print(f"   Mean: {report['r2_statistics']['mean']:.3f}")
        print(f"   Range: [{report['r2_statistics']['min']:.3f} - {report['r2_statistics']['max']:.3f}]")
    
    # Print quality breakdown
    print(f"\n🎯 QUALITY BREAKDOWN:")
    quality_emojis = {"EXCELLENT": "🟢", "GOOD": "✅", "FAIR": "⚠️", "POOR": "❌"}
    for quality, count in report['quality_distribution']['counts'].items():
        if count > 0:
            percentage = report['quality_distribution']['percentages'][quality]
            emoji = quality_emojis[quality]
            print(f"   {emoji} {quality}: {count} files ({percentage:.1f}%)")
    
    # Print instrument comparison
    if 'instrument_performance' in report:
        print(f"\n🔬 INSTRUMENT COMPARISON:")
        for instrument, stats in report['instrument_performance'].items():
            if stats['count'] > 0:
                print(f"   {instrument}: {stats['count']} files, avg R² = {stats['mean_r2']:.3f}")
    
    # Print top performing files
    successful_results = [r for r in results if r['result'] is not None]
    if successful_results:
        top_files = sorted(successful_results, key=lambda x: x['result']['avg_r2'], reverse=True)[:5]
        print(f"\n🏆 TOP 5 PERFORMING FILES:")
        for i, r in enumerate(top_files):
            filename = os.path.basename(r['file_path'])[:45]
            print(f"   {i+1}. {filename:45} | R²={r['result']['avg_r2']:.3f}")
    
    print(f"\n🔍 Check {output_dir}/ for all plots and detailed report!")
    print(f"📊 Total plots generated: {successful_count}")

if __name__ == "__main__":
    main()