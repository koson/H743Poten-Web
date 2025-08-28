#!/usr/bin/env python3
"""
Batch Baseline Analysis for all CSV files in Test_data
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

# Import the single file analyzer
from single_baseline_analyzer import analyze_single_file

def find_all_csv_files(root_dir="Test_data"):
    """Find all CSV files in Test_data directory"""
    csv_files = []
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.csv') and not file.endswith('.backup'):
                csv_files.append(os.path.join(root, file))
    
    return sorted(csv_files)

def categorize_files(csv_files):
    """Categorize files by instrument and scan rate"""
    categories = {}
    
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        
        # Determine instrument type
        if 'Palmsens' in filename:
            instrument = 'Palmsens'
        elif 'Pipot' in filename or 'Stm32' in file_path:
            instrument = 'STM32'
        else:
            instrument = 'Unknown'
        
        # Extract scan rate
        scan_rate = 'Unknown'
        if 'mVpS' in filename:
            try:
                import re
                match = re.search(r'(\d+)mVpS', filename, re.IGNORECASE)
                if match:
                    scan_rate = f"{match.group(1)}mVpS"
            except:
                pass
        
        # Extract concentration
        concentration = 'Unknown'
        conc_patterns = [r'(\d+\.?\d*)mM', r'(\d+\.?\d*)_\d*mM']
        for pattern in conc_patterns:
            try:
                import re
                match = re.search(pattern, filename, re.IGNORECASE)
                if match:
                    concentration = f"{match.group(1)}mM"
                    break
            except:
                pass
        
        category = f"{instrument}_{scan_rate}_{concentration}"
        if category not in categories:
            categories[category] = []
        categories[category].append(file_path)
    
    return categories

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
    instrument_performance = {}
    
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
            
            # Instrument performance
            filename = os.path.basename(r['file_path'])
            if 'Palmsens' in filename:
                instrument = 'Palmsens'
            elif 'Pipot' in filename:
                instrument = 'STM32'
            else:
                instrument = 'Unknown'
            
            if instrument not in instrument_performance:
                instrument_performance[instrument] = []
            instrument_performance[instrument].append(avg_r2)
    
    # Create report
    report = {
        'timestamp': timestamp,
        'summary': {
            'total_files': total_files,
            'successful_analyses': successful,
            'failed_analyses': failed,
            'success_rate': round((successful / total_files) * 100, 1)
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
        'instrument_performance': {
            inst: {
                'count': len(values),
                'mean_r2': round(np.mean(values), 3),
                'std_r2': round(np.std(values), 3)
            } for inst, values in instrument_performance.items()
        },
        'detailed_results': [
            {
                'file': os.path.basename(r['file_path']),
                'success': r['result'] is not None,
                'quality': r['result']['quality'] if r['result'] else 'FAILED',
                'forward_r2': r['result']['forward_r2'] if r['result'] else 0,
                'reverse_r2': r['result']['reverse_r2'] if r['result'] else 0,
                'avg_r2': r['result']['avg_r2'] if r['result'] else 0,
                'total_points': r['result']['total_points'] if r['result'] else 0,
                'scan_rate': r['result']['scan_rate'] if r['result'] else 'Unknown',
                'error': r['error']
            } for r in results
        ]
    }
    
    # Add recommendations
    recommendations = []
    
    # Performance analysis
    if report['r2_statistics']['mean'] < 0.5:
        recommendations.append("Overall R² performance is low. Consider adjusting baseline detection parameters.")
    
    # Quality distribution analysis
    poor_ratio = quality_counts['POOR'] / successful if successful > 0 else 0
    if poor_ratio > 0.3:
        recommendations.append(f"High percentage of POOR quality detections ({poor_ratio*100:.1f}%). Algorithm needs improvement.")
    
    # Scan rate analysis
    if scan_rate_performance:
        best_rate = max(scan_rate_performance.items(), key=lambda x: np.mean(x[1]))
        worst_rate = min(scan_rate_performance.items(), key=lambda x: np.mean(x[1]))
        recommendations.append(f"Best performance at {best_rate[0]} (R²={np.mean(best_rate[1]):.3f}), worst at {worst_rate[0]} (R²={np.mean(worst_rate[1]):.3f})")
    
    # Instrument analysis
    if len(instrument_performance) > 1:
        for inst, values in instrument_performance.items():
            mean_r2 = np.mean(values)
            if mean_r2 < 0.4:
                recommendations.append(f"{inst} shows poor performance (R²={mean_r2:.3f}). May need instrument-specific tuning.")
    
    report['recommendations'] = recommendations
    
    # Save report
    report_file = os.path.join(output_dir, f"batch_baseline_analysis_report_{timestamp}.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report, report_file

def print_progress_summary(results, categories):
    """Print progress summary during processing"""
    total = len(results)
    successful = len([r for r in results if r['result'] is not None])
    failed = total - successful
    
    print(f"\n📊 PROGRESS SUMMARY")
    print(f"✅ Successful: {successful}/{total} ({successful/total*100:.1f}%)")
    print(f"❌ Failed: {failed}/{total} ({failed/total*100:.1f}%)")
    
    if successful > 0:
        # Quick quality breakdown
        quality_counts = {'EXCELLENT': 0, 'GOOD': 0, 'FAIR': 0, 'POOR': 0}
        avg_r2_values = []
        
        for r in results:
            if r['result']:
                quality = r['result']['quality'].split()[0]
                if quality in quality_counts:
                    quality_counts[quality] += 1
                avg_r2_values.append(r['result']['avg_r2'])
        
        print(f"\n🎯 QUALITY BREAKDOWN:")
        for quality, count in quality_counts.items():
            percentage = (count / successful) * 100
            emoji = {"EXCELLENT": "🟢", "GOOD": "✅", "FAIR": "⚠️", "POOR": "❌"}[quality]
            print(f"   {emoji} {quality}: {count} ({percentage:.1f}%)")
        
        if avg_r2_values:
            print(f"\n📈 R² STATISTICS:")
            print(f"   Mean: {np.mean(avg_r2_values):.3f}")
            print(f"   Median: {np.median(avg_r2_values):.3f}")
            print(f"   Range: [{min(avg_r2_values):.3f}, {max(avg_r2_values):.3f}]")

def main():
    """Main batch processing function"""
    
    print("🚀 Batch Baseline Analysis for Test_data")
    print("=" * 60)
    
    # Find all CSV files
    csv_files = find_all_csv_files()
    print(f"📁 Found {len(csv_files)} CSV files in Test_data")
    
    if len(csv_files) == 0:
        print("❌ No CSV files found in Test_data directory")
        return
    
    # Categorize files
    categories = categorize_files(csv_files)
    print(f"📊 Files categorized into {len(categories)} groups")
    
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
            result = analyze_single_file(file_path, output_dir)
            results.append({
                'file_path': file_path,
                'result': result,
                'error': None
            })
            
            if result:
                print(f"   ✅ Success: {result['quality']} (R²={result['avg_r2']:.3f})")
            else:
                print(f"   ❌ Failed: Analysis returned None")
                results[-1]['error'] = "Analysis returned None"
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({
                'file_path': file_path,
                'result': None,
                'error': str(e)
            })
        
        # Print progress every 20 files
        if (i + 1) % 20 == 0 or i == len(csv_files) - 1:
            print_progress_summary(results, categories)
    
    # Generate comprehensive report
    print(f"\n📋 Generating comprehensive report...")
    report, report_file = create_summary_report(results, output_dir)
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎉 BATCH ANALYSIS COMPLETE")
    print(f"📂 Output directory: {output_dir}")
    print(f"📋 Report file: {report_file}")
    print(f"📊 Success rate: {report['summary']['success_rate']}%")
    
    # Print key findings
    if report['recommendations']:
        print(f"\n💡 KEY RECOMMENDATIONS:")
        for rec in report['recommendations'][:3]:  # Show top 3
            print(f"   • {rec}")
    
    # Print top performing files
    successful_results = [r for r in results if r['result'] is not None]
    if successful_results:
        # Sort by average R²
        top_files = sorted(successful_results, key=lambda x: x['result']['avg_r2'], reverse=True)[:5]
        print(f"\n🏆 TOP 5 PERFORMING FILES:")
        for i, r in enumerate(top_files):
            filename = os.path.basename(r['file_path'])[:50]
            print(f"   {i+1}. {filename:50} | R²={r['result']['avg_r2']:.3f} | {r['result']['quality']}")
    
    print(f"\n🔍 Check the output directory for individual plots and detailed report!")

if __name__ == "__main__":
    main()