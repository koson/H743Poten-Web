#!/usr/bin/env python3
"""
Quick baseline detection test script
Test baseline detection algorithms without web interface
"""

import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from routes.peak_detection import detect_peaks_prominence, detect_improved_baseline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_cv_data(file_path):
    """Load CV data from file"""
    try:
        # Read CSV file
        df = pd.read_csv(file_path, skiprows=1)  # Skip filename header
        
        # Handle different column formats
        if 'V' in df.columns and 'uA' in df.columns:
            voltage = df['V'].values
            current = df['uA'].values
        elif 'V' in df.columns and 'A' in df.columns:
            voltage = df['V'].values
            current = df['A'].values * 1e6  # Convert A to µA
        else:
            logger.error(f"Unknown column format in {file_path}")
            return None, None
            
        return voltage, current
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None, None

def test_single_file(file_path, show_plot=True):
    """Test baseline detection on a single file"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing: {os.path.basename(file_path)}")
    logger.info(f"{'='*60}")
    
    # Load data
    voltage, current = load_cv_data(file_path)
    if voltage is None:
        return False
        
    logger.info(f"Data points: {len(voltage)}")
    logger.info(f"Voltage range: [{voltage.min():.3f}, {voltage.max():.3f}] V")
    logger.info(f"Current range: [{current.min():.3f}, {current.max():.3f}] µA")
    
    try:
        # Test baseline detection
        baseline_result = detect_improved_baseline(voltage, current)
        
        if baseline_result is None:
            logger.error("Baseline detection failed!")
            return False
            
        baseline_forward, baseline_reverse, segment_info = baseline_result
        baseline_full = np.concatenate([baseline_forward, baseline_reverse])
        
        logger.info(f"Forward baseline: {len(baseline_forward)} points, range: [{baseline_forward.min():.3f}, {baseline_forward.max():.3f}] µA")
        logger.info(f"Reverse baseline: {len(baseline_reverse)} points, range: [{baseline_reverse.min():.3f}, {baseline_reverse.max():.3f}] µA")
        
        # Test peak detection
        peaks_data = detect_peaks_prominence(voltage, current, prominence=50, width=3)
        
        if peaks_data and 'peaks' in peaks_data:
            peaks = peaks_data['peaks']
            logger.info(f"Found {len(peaks)} peaks:")
            
            for i, peak in enumerate(peaks):
                logger.info(f"  Peak {i+1}: {peak['type']} at {peak['voltage']:.3f}V, "
                          f"current {peak['current']:.3f}µA, height {peak['height']:.3f}µA, "
                          f"baseline {peak['baseline_current']:.3f}µA")
        
        # Plot results if requested
        if show_plot:
            plt.figure(figsize=(12, 8))
            
            # Plot CV curve
            plt.plot(voltage, current, 'b-', linewidth=1.5, label='CV Data', alpha=0.7)
            
            # Plot baselines
            plt.plot(voltage[:len(baseline_forward)], baseline_forward, 'r--', 
                    linewidth=2, label='Forward Baseline', alpha=0.8)
            plt.plot(voltage[len(baseline_forward):], baseline_reverse, 'c--', 
                    linewidth=2, label='Reverse Baseline', alpha=0.8)
            
            # Plot peaks
            if peaks_data and 'peaks' in peaks_data:
                ox_peaks = [p for p in peaks if p['type'] == 'oxidation']
                red_peaks = [p for p in peaks if p['type'] == 'reduction']
                
                if ox_peaks:
                    ox_v = [p['voltage'] for p in ox_peaks]
                    ox_i = [p['current'] for p in ox_peaks]
                    plt.scatter(ox_v, ox_i, color='red', s=100, marker='o', 
                              label=f'Ox Peaks ({len(ox_peaks)})', zorder=5)
                    
                    # Plot drop lines for ox peaks
                    for peak in ox_peaks:
                        plt.plot([peak['voltage'], peak['voltage']], 
                               [peak['current'], peak['baseline_current']], 
                               'r:', linewidth=2, alpha=0.7)
                
                if red_peaks:
                    red_v = [p['voltage'] for p in red_peaks]
                    red_i = [p['current'] for p in red_peaks]
                    plt.scatter(red_v, red_i, color='green', s=100, marker='o', 
                              label=f'Red Peaks ({len(red_peaks)})', zorder=5)
                    
                    # Plot drop lines for red peaks
                    for peak in red_peaks:
                        plt.plot([peak['voltage'], peak['voltage']], 
                               [peak['current'], peak['baseline_current']], 
                               'g:', linewidth=2, alpha=0.7)
            
            plt.xlabel('Voltage (V)')
            plt.ylabel('Current (µA)')
            plt.title(f'CV Analysis: {os.path.basename(file_path)}')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()
        
        return True
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_files(test_dir, pattern="*.csv", max_files=5, show_plots=False):
    """Test multiple files in a directory"""
    test_path = Path(test_dir)
    csv_files = list(test_path.glob(pattern))
    
    if not csv_files:
        logger.error(f"No CSV files found in {test_dir}")
        return
    
    logger.info(f"Found {len(csv_files)} CSV files in {test_dir}")
    
    # Limit number of files for quick testing
    test_files = csv_files[:max_files]
    
    results = []
    for file_path in test_files:
        success = test_single_file(str(file_path), show_plot=show_plots)
        results.append((file_path.name, success))
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("SUMMARY")
    logger.info(f"{'='*60}")
    successful = sum(1 for _, success in results if success)
    logger.info(f"Tested: {len(results)} files")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {len(results) - successful}")
    
    for filename, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"  {status} - {filename}")

def main():
    """Main test function"""
    # Test directories
    palmsens_5mm_dir = r"D:\GitHubRepos\__Potentiostat\poten-2025\H743Poten\H743Poten-Web\Test_data\Palmsens\Palmsens_5mM"
    stm32_5mm_dir = r"D:\GitHubRepos\__Potentiostat\poten-2025\H743Poten\H743Poten-Web\Test_data\Stm32\Pipot_Ferro_5_0mM"
    
    # Test options
    SINGLE_FILE_TEST = True      # Test one file with plot
    BATCH_TEST_PALMSENS = True   # Test multiple Palmsens files
    BATCH_TEST_STM32 = True      # Test multiple STM32 files
    
    if SINGLE_FILE_TEST:
        # Test a single file with detailed plot
        test_file = os.path.join(palmsens_5mm_dir, "Palmsens_5mM_CV_400mVpS_E3_scan_08.csv")
        if os.path.exists(test_file):
            logger.info("=== SINGLE FILE TEST WITH PLOT ===")
            test_single_file(test_file, show_plot=True)
        else:
            logger.warning(f"Test file not found: {test_file}")
    
    if BATCH_TEST_PALMSENS:
        # Test multiple Palmsens files (no plots for speed)
        logger.info("\n=== BATCH TEST: PALMSENS FILES ===")
        test_multiple_files(palmsens_5mm_dir, max_files=5, show_plots=False)
    
    if BATCH_TEST_STM32:
        # Test multiple STM32 files (no plots for speed)
        logger.info("\n=== BATCH TEST: STM32 FILES ===")
        test_multiple_files(stm32_5mm_dir, max_files=5, show_plots=False)

if __name__ == "__main__":
    main()