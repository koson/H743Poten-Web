#!/usr/bin/env python3
"""
Debug script to test PalmSens baseline detection
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import logging
import os
import glob

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_palmsens_file(file_path):
    """Load and parse PalmSens CSV file"""
    try:
        # Read CSV file
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            raise ValueError('File too short')
        
        # Handle instrument file format (FileName: header)
        header_line_idx = 0
        data_start_idx = 1
        
        if lines[0].strip().startswith('FileName:'):
            header_line_idx = 1
            data_start_idx = 2
            logger.info("Detected instrument file format with FileName header")
        
        # Parse headers
        headers = [h.strip().lower() for h in lines[header_line_idx].strip().split(',')]
        logger.info(f"Headers found: {headers}")
        
        # Find voltage and current columns
        voltage_idx = -1
        current_idx = -1
        
        for i, header in enumerate(headers):
            if header in ['v', 'voltage'] or 'volt' in header or 'potential' in header:
                voltage_idx = i
            elif header in ['a', 'ua', 'ma', 'na', 'current'] or 'amp' in header or 'curr' in header:
                current_idx = i
        
        if voltage_idx == -1 or current_idx == -1:
            raise ValueError(f'Could not find voltage or current columns in headers: {headers}')
        
        # Determine current scaling - keep in µA for baseline detection
        current_unit = headers[current_idx]
        current_scale = 1.0
        
        # Check if this is STM32/Pipot file (uses 'A' header but values are actually in µA)
        is_stm32_file = (
            'pipot' in file_path.lower() or 
            'stm32' in file_path.lower() or
            (current_unit == 'a' and lines[0].strip().startswith('FileName:'))
        )
        
        if current_unit == 'ma':
            current_scale = 1e3  # milliAmps to microAmps
        elif current_unit == 'na':
            current_scale = 1e-3  # nanoAmps to microAmps
        elif current_unit == 'a' and is_stm32_file:
            current_scale = 1e6  # STM32 'A' values are actually µA, so multiply by 1e6 to convert from A to µA
            logger.info("Detected STM32/Pipot file - treating 'A' column as µA values")
        elif current_unit == 'a' and not is_stm32_file:
            current_scale = 1e6  # True Amperes to microAmps
        # For 'ua' or 'uA' - keep as is (no scaling)
        
        logger.info(f"Current unit: {current_unit}, scale: {current_scale} (keeping in µA), STM32: {is_stm32_file}")
        
        # Parse data
        voltage = []
        current = []
        
        for i in range(data_start_idx, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
                
            values = line.split(',')
            if len(values) > max(voltage_idx, current_idx):
                try:
                    v = float(values[voltage_idx])
                    c = float(values[current_idx]) * current_scale
                    voltage.append(v)
                    current.append(c)
                except ValueError:
                    continue
        
        if len(voltage) == 0 or len(current) == 0:
            raise ValueError('No valid data points found')
        
        voltage = np.array(voltage)
        current = np.array(current)
        
        logger.info(f"Loaded {len(voltage)} data points from {file_path}")
        logger.info(f"Voltage range: {np.min(voltage):.3f} to {np.max(voltage):.3f} V")
        logger.info(f"Current range: {np.min(current):.3f} to {np.max(current):.3f} µA")
        
        return voltage, current
        
    except Exception as e:
        logger.error(f"Error loading CSV file: {str(e)}")
        raise

def test_peak_detection(voltage, current, filename):
    """Test peak detection on PalmSens data"""
    logger.info(f"\n=== Testing Peak Detection on {filename} ===")
    
    # Check data quality
    logger.info(f"Data quality check:")
    logger.info(f"  Voltage: min={np.min(voltage):.3f}V, max={np.max(voltage):.3f}V, mean={np.mean(voltage):.3f}V")
    logger.info(f"  Current: min={np.min(current):.3f}µA, max={np.max(current):.3f}µA, mean={np.mean(current):.3f}µA")
    logger.info(f"  NaN values: voltage={np.sum(np.isnan(voltage))}, current={np.sum(np.isnan(current))}")
    logger.info(f"  Inf values: voltage={np.sum(np.isinf(voltage))}, current={np.sum(np.isinf(current))}")
    
    # Normalize current for peak detection
    current_norm = current / np.abs(current).max()
    logger.info(f"  Normalized current range: {np.min(current_norm):.3f} to {np.max(current_norm):.3f}")
    
    # Test basic peak detection
    try:
        # Find positive peaks (oxidation)
        pos_peaks, pos_properties = find_peaks(
            current_norm,
            prominence=0.1,
            width=5
        )
        
        # Find negative peaks (reduction)
        neg_peaks, neg_properties = find_peaks(
            -current_norm,
            prominence=0.1,
            width=5
        )
        
        logger.info(f"Peak detection results:")
        logger.info(f"  Positive peaks found: {len(pos_peaks)} at indices {pos_peaks}")
        logger.info(f"  Negative peaks found: {len(neg_peaks)} at indices {neg_peaks}")
        
        if len(pos_peaks) > 0:
            logger.info(f"  Positive peak voltages: {[voltage[i] for i in pos_peaks]}")
            logger.info(f"  Positive peak currents: {[current[i] for i in pos_peaks]}")
            logger.info(f"  Positive peak prominences: {pos_properties['prominences']}")
        
        if len(neg_peaks) > 0:
            logger.info(f"  Negative peak voltages: {[voltage[i] for i in neg_peaks]}")
            logger.info(f"  Negative peak currents: {[current[i] for i in neg_peaks]}")
            logger.info(f"  Negative peak prominences: {neg_properties['prominences']}")
        
        # Try different prominence thresholds
        for prom in [0.05, 0.02, 0.01]:
            pos_test, _ = find_peaks(current_norm, prominence=prom, width=3)
            neg_test, _ = find_peaks(-current_norm, prominence=prom, width=3)
            logger.info(f"  At prominence {prom}: {len(pos_test)} pos peaks, {len(neg_test)} neg peaks")
            
        return len(pos_peaks) + len(neg_peaks)
        
    except Exception as e:
        logger.error(f"Error in peak detection: {e}")
        return 0

def main():
    """Main function to test PalmSens files"""
    logger.info("🔍 Starting PalmSens Baseline Detection Debug")
    
    # Find PalmSens 1.0mM files from the logs
    test_files = [
        "./Test_data/Palmsens/Palmsens_1.0mM/Palmsens_1.0mM_CV_100mVpS_E1_scan_05.csv",
        "./Test_data/Palmsens/Palmsens_1.0mM/Palmsens_1.0mM_CV_100mVpS_E3_scan_08.csv",
        "./Test_data/Palmsens/Palmsens_1.0mM/Palmsens_1.0mM_CV_20mVpS_E1_scan_05.csv"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                voltage, current = load_palmsens_file(file_path)
                peak_count = test_peak_detection(voltage, current, os.path.basename(file_path))
                logger.info(f"✅ {os.path.basename(file_path)}: {peak_count} peaks detected")
            except Exception as e:
                logger.error(f"❌ {os.path.basename(file_path)}: Error - {e}")
        else:
            logger.warning(f"⚠️ File not found: {file_path}")
    
    logger.info("🏁 Debug completed")

if __name__ == "__main__":
    main()