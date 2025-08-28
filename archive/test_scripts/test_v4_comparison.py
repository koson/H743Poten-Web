#!/usr/bin/env python3
"""
Test script for Enhanced V4 Improved peak detection
Compare with original Enhanced V4 to verify improvements
"""

import os
import sys
import numpy as np
import logging
import json
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to Python path
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, parent_dir)

try:
    from enhanced_detector_v4 import EnhancedDetectorV4
    from enhanced_detector_v4_improved import EnhancedDetectorV4Improved
    logger.info("✅ Successfully imported both Enhanced V4 and V4 Improved")
except ImportError as e:
    logger.error(f"❌ Import error: {e}")
    sys.exit(1)

def load_test_file(filepath):
    """Load a single CV data file"""
    try:
        import pandas as pd
        
        # Try different file formats
        if filepath.endswith('.csv'):
            # Skip first line for Palmsens files (they have filename as first line)
            try:
                df = pd.read_csv(filepath, skiprows=1)
            except:
                df = pd.read_csv(filepath)
        elif filepath.endswith('.txt'):
            df = pd.read_csv(filepath, sep='\t')
        else:
            # Try CSV first, then tab-separated
            try:
                df = pd.read_csv(filepath, skiprows=1)
            except:
                try:
                    df = pd.read_csv(filepath)
                except:
                    df = pd.read_csv(filepath, sep='\t')
        
        # Check if dataframe has at least 2 columns
        if df.shape[1] < 2:
            logger.error(f"File {filepath} has less than 2 columns")
            return None, None, None
        
        # Look for voltage and current columns
        voltage_col = None
        current_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'voltage' in col_lower or 'potential' in col_lower or col_lower in ['v', 'e']:
                voltage_col = col
            elif 'current' in col_lower or col_lower in ['i', 'current(ma)', 'current(µa)', 'current(ua)', 'ua']:
                current_col = col
        
        if voltage_col is None or current_col is None:
            # Fallback: use first two columns
            voltage_col = df.columns[0]
            current_col = df.columns[1]
            logger.info(f"Using fallback columns: {voltage_col}, {current_col}")
        
        voltage = df[voltage_col].values
        current = df[current_col].values
        
        # Remove any NaN values
        valid_mask = ~(np.isnan(voltage) | np.isnan(current))
        voltage = voltage[valid_mask]
        current = current[valid_mask]
        
        if len(voltage) == 0:
            logger.error(f"No valid data points in {filepath}")
            return None, None, None
        
        # Convert current to µA if needed (Palmsens files already in µA)
        if np.max(np.abs(current)) < 1e-3:  # Probably in Amperes
            current = current * 1e6  # Convert to µA
        elif np.max(np.abs(current)) < 1 and 'ua' not in current_col.lower():  # Probably in mA
            current = current * 1e3  # Convert to µA
        
        return voltage, current, os.path.basename(filepath)
        
    except Exception as e:
        logger.error(f"❌ Error loading file {filepath}: {e}")
        return None, None, None

def analyze_single_file(filepath, detectors):
    """Analyze a single file with both Enhanced V4 and V4 Improved"""
    voltage, current, filename = load_test_file(filepath)
    
    if voltage is None:
        return None
    
    logger.info(f"\n🔍 Analyzing: {filename}")
    logger.info(f"   Data points: {len(voltage)}")
    logger.info(f"   Voltage range: {voltage.min():.3f} to {voltage.max():.3f}V")
    logger.info(f"   Current range: {current.min():.3f} to {current.max():.3f}µA")
    
    results = {'filename': filename}
    
    # Test both detectors
    for name, detector in detectors.items():
        try:
            data = {
                'voltage': voltage.tolist(),
                'current': current.tolist()
            }
            
            result = detector.analyze_cv_data(data)
            peaks = result['peaks']
            
            # Count peaks by type
            ox_count = len([p for p in peaks if p['type'] == 'oxidation'])
            red_count = len([p for p in peaks if p['type'] == 'reduction'])
            
            # Check for edge effects (peaks near voltage limits)
            v_min, v_max = voltage.min(), voltage.max()
            v_range = v_max - v_min
            edge_margin = v_range * 0.05  # 5% margin
            
            edge_peaks = []
            for peak in peaks:
                if (peak['voltage'] <= v_min + edge_margin or 
                    peak['voltage'] >= v_max - edge_margin):
                    edge_peaks.append(peak)
            
            results[name] = {
                'total_peaks': len(peaks),
                'oxidation_peaks': ox_count,
                'reduction_peaks': red_count,
                'edge_effects': len(edge_peaks),
                'has_both_peaks': ox_count > 0 and red_count > 0,
                'confidence_threshold': result.get('confidence_threshold', 'unknown'),
                'voltage_ranges': result.get('voltage_ranges', {}),
                'peaks': peaks,
                'edge_peaks': edge_peaks
            }
            
            logger.info(f"   {name}: {ox_count} ox + {red_count} red = {len(peaks)} total ({len(edge_peaks)} edge)")
            
        except Exception as e:
            logger.error(f"   ❌ {name} failed: {e}")
            results[name] = {'error': str(e)}
    
    return results

def compare_detectors():
    """Compare Enhanced V4 vs V4 Improved on Palmsens dataset"""
    
    # Initialize detectors
    detectors = {
        'Enhanced_V4': EnhancedDetectorV4(),  # No confidence_threshold parameter
        'Enhanced_V4_Improved': EnhancedDetectorV4Improved(confidence_threshold=25.0)
    }
    
    logger.info("🚀 Enhanced V4 vs V4 Improved Comparison Test")
    logger.info("=" * 60)
    
    # Test data directory
    test_dir = "Test_data/Palmsens/Palmsens_0.5mM"
    
    if not os.path.exists(test_dir):
        logger.error(f"❌ Test directory not found: {test_dir}")
        return
    
    # Get test files (limit to 10 for quick comparison)
    test_files = []
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            if file.endswith(('.csv', '.txt')) and not file.startswith('.'):
                test_files.append(os.path.join(root, file))
    
    # Select representative files
    selected_files = test_files[:10]  # First 10 files
    
    logger.info(f"📁 Found {len(test_files)} total files, testing {len(selected_files)} files")
    
    # Analyze files
    all_results = []
    summary_stats = {
        'Enhanced_V4': {'total_peaks': 0, 'ox_peaks': 0, 'red_peaks': 0, 'both_peaks': 0, 'edge_effects': 0, 'errors': 0},
        'Enhanced_V4_Improved': {'total_peaks': 0, 'ox_peaks': 0, 'red_peaks': 0, 'both_peaks': 0, 'edge_effects': 0, 'errors': 0}
    }
    
    for i, filepath in enumerate(selected_files):
        logger.info(f"\n📊 Processing file {i+1}/{len(selected_files)}")
        
        result = analyze_single_file(filepath, detectors)
        if result:
            all_results.append(result)
            
            # Update summary statistics
            for detector_name in ['Enhanced_V4', 'Enhanced_V4_Improved']:
                if detector_name in result and 'error' not in result[detector_name]:
                    stats = result[detector_name]
                    summary_stats[detector_name]['total_peaks'] += stats['total_peaks']
                    summary_stats[detector_name]['ox_peaks'] += stats['oxidation_peaks']
                    summary_stats[detector_name]['red_peaks'] += stats['reduction_peaks']
                    summary_stats[detector_name]['both_peaks'] += (1 if stats['has_both_peaks'] else 0)
                    summary_stats[detector_name]['edge_effects'] += stats['edge_effects']
                else:
                    summary_stats[detector_name]['errors'] += 1
    
    # Print comparison results
    logger.info("\n" + "=" * 60)
    logger.info("📊 COMPARISON RESULTS")
    logger.info("=" * 60)
    
    for detector_name, stats in summary_stats.items():
        success_files = len(selected_files) - stats['errors']
        logger.info(f"\n🔧 {detector_name}:")
        logger.info(f"   Successfully processed: {success_files}/{len(selected_files)} files")
        logger.info(f"   Total peaks detected: {stats['total_peaks']}")
        logger.info(f"   Oxidation peaks: {stats['ox_peaks']}")
        logger.info(f"   Reduction peaks: {stats['red_peaks']}")
        logger.info(f"   Files with both peak types: {stats['both_peaks']}/{success_files} ({stats['both_peaks']/success_files*100:.1f}%)" if success_files > 0 else "   No successful files")
        logger.info(f"   Edge effects detected: {stats['edge_effects']}")
        logger.info(f"   Errors: {stats['errors']}")
    
    # Calculate improvements
    if summary_stats['Enhanced_V4']['total_peaks'] > 0:
        improvement_ratio = summary_stats['Enhanced_V4_Improved']['red_peaks'] / max(1, summary_stats['Enhanced_V4']['red_peaks'])
        logger.info(f"\n📈 IMPROVEMENTS:")
        logger.info(f"   Reduction peak detection improvement: {improvement_ratio:.2f}x")
        logger.info(f"   Both-peaks detection improvement: {summary_stats['Enhanced_V4_Improved']['both_peaks'] - summary_stats['Enhanced_V4']['both_peaks']} more files")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"enhanced_v4_comparison_{timestamp}.json"
    
    comparison_data = {
        'timestamp': timestamp,
        'test_directory': test_dir,
        'files_tested': len(selected_files),
        'summary_statistics': summary_stats,
        'detailed_results': all_results,
        'detector_configs': {
            'Enhanced_V4': {
                'confidence_threshold': 40.0,
                'oxidation_range': [0.2, 0.6],
                'reduction_range': [0.0, 0.3]
            },
            'Enhanced_V4_Improved': {
                'confidence_threshold': 25.0,
                'oxidation_range': [0.1, 0.7],
                'reduction_range': [-0.1, 0.4],
                'edge_margin': 0.05,
                'improvements': [
                    'Expanded voltage ranges',
                    'Lowered confidence threshold',
                    'Edge effect filtering',
                    'Savgol smoothing',
                    'Improved peak sensitivity'
                ]
            }
        }
    }
    
    with open(result_file, 'w') as f:
        json.dump(comparison_data, f, indent=2, default=str)
    
    logger.info(f"\n💾 Detailed results saved to: {result_file}")
    
    return comparison_data

if __name__ == "__main__":
    try:
        results = compare_detectors()
        logger.info("\n✅ Comparison completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Comparison failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
