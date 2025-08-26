#!/usr/bin/env python3
"""
Quick Test - Enhanced CV Calibration with Sample Files
====================================================
Test the corrected STM32 files with A units using a small sample
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.stats import linregress
import logging
from pathlib import Path
import re
from typing import Dict, List, Tuple, Optional
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_file_reading():
    """Test reading and processing a few sample files"""
    logger.info("🧪 Testing file reading with corrected headers...")
    
    # Test a few sample files
    test_dir = Path("test_data/raw_stm32")
    sample_files = list(test_dir.glob("Pipot_Ferro_5_0mM_*_E2_scan_01.csv"))[:3]
    
    logger.info(f"📂 Testing {len(sample_files)} sample files:")
    
    for file_path in sample_files:
        logger.info(f"\n📄 Testing: {file_path.name}")
        
        try:
            # Read the file (skip first line if it's metadata)
            with open(file_path, 'r') as f:
                first_line = f.readline().strip()
            
            # Skip metadata line if present
            skiprows = 1 if first_line.startswith('FileName:') else 0
            df = pd.read_csv(file_path, encoding='utf-8-sig', skiprows=skiprows)
            logger.info(f"   Columns: {list(df.columns)}")
            logger.info(f"   Shape: {df.shape}")
            
            # Check first few rows
            logger.info("   First 3 data rows:")
            for i in range(min(3, len(df))):
                logger.info(f"     {df.iloc[i].to_dict()}")
            
            # Find voltage and current columns
            voltage_col = None
            current_col = None
            
            for col in df.columns:
                col_clean = col.strip()
                col_lower = col_clean.lower()
                
                if (col_clean == 'V' or 
                    'voltage' in col_lower or 
                    'potential' in col_lower or 
                    col_lower.startswith('v')):
                    voltage_col = col
                
                elif (col_clean == 'A' or 
                      col_clean == 'uA' or 
                      col_clean == 'µA' or
                      'current' in col_lower or 
                      col_lower.startswith('i')):
                    current_col = col
            
            logger.info(f"   Voltage column: {voltage_col}")
            logger.info(f"   Current column: {current_col}")
            
            if voltage_col and current_col:
                voltage = df[voltage_col].values
                current = df[current_col].values
                
                logger.info(f"   Voltage range: {np.min(voltage):.3f} to {np.max(voltage):.3f} V")
                logger.info(f"   Current range: {np.min(current):.2e} to {np.max(current):.2e} A")
                
                # Calculate peak properties
                peak_height = np.max(current) - np.min(current)
                peak_area = abs(np.trapz(current, voltage))
                
                logger.info(f"   Peak height: {peak_height:.2e} A")
                logger.info(f"   Peak area: {peak_area:.2e} A⋅V")
                
                # Extract metadata from filename
                concentration = extract_concentration(file_path.name)
                scan_rate = extract_scan_rate(file_path.name)
                
                logger.info(f"   Concentration: {concentration} mM")
                logger.info(f"   Scan rate: {scan_rate} mV/s")
            
        except Exception as e:
            logger.error(f"   ❌ Error processing {file_path.name}: {e}")

def extract_concentration(filename: str) -> Optional[float]:
    """Extract concentration from filename"""
    filename_lower = filename.lower()
    
    # Handle special cases like "5_0mM" first
    ferro_underscore_pattern = r'ferro[_\-](\d+)[_\-](\d+)mm'
    match = re.search(ferro_underscore_pattern, filename_lower)
    if match:
        try:
            integer_part = float(match.group(1))
            decimal_part = float(match.group(2))
            return integer_part + decimal_part / 10  # Convert 5_0 to 5.0
        except ValueError:
            pass
    
    # Standard patterns
    patterns = [
        r'(\d+\.?\d*)\s*mm',  # e.g., "5.0mM", "20mM"
        r'(\d+\.?\d*)\s*m\b',  # e.g., "1.0M" 
        r'ferro[_\-](\d+\.?\d*)[_\-]?mm',  # e.g., "Ferro_1.0_mM"
        r'(\d+\.?\d*)mm',  # e.g., "5mm"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename_lower)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    
    return None

def extract_scan_rate(filename: str) -> Optional[float]:
    """Extract scan rate from filename"""
    patterns = [
        r'(\d+\.?\d*)\s*mvps',
        r'(\d+\.?\d*)\s*mv[\/\-_]?s',
        r'(\d+\.?\d*)\s*mvs',
    ]
    
    filename_lower = filename.lower()
    for pattern in patterns:
        match = re.search(pattern, filename_lower)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    return None

def create_sample_calibration_plot():
    """Create a sample calibration plot from a few files"""
    logger.info("\n📊 Creating sample calibration plot...")
    
    test_dir = Path("test_data/raw_stm32")
    
    # Get files for one scan rate (50 mV/s) and different concentrations
    scan_rate_pattern = "*50mVpS*E2_scan_01.csv"
    sample_files = list(test_dir.glob(scan_rate_pattern))
    
    logger.info(f"📂 Found {len(sample_files)} files for 50 mV/s scan rate")
    
    concentrations = []
    peak_heights = []
    peak_areas = []
    filenames = []
    
    for file_path in sample_files[:20]:  # Process first 20 files
        try:
            # Extract metadata
            concentration = extract_concentration(file_path.name)
            scan_rate = extract_scan_rate(file_path.name)
            
            if concentration is None or scan_rate is None:
                continue
            
            # Read and process file
            with open(file_path, 'r') as f:
                first_line = f.readline().strip()
            
            # Skip metadata line if present
            skiprows = 1 if first_line.startswith('FileName:') else 0
            df = pd.read_csv(file_path, encoding='utf-8-sig', skiprows=skiprows)
            
            voltage = df['V'].values
            current = df['A'].values
            
            # Remove NaN values
            mask = ~(np.isnan(voltage) | np.isnan(current))
            voltage = voltage[mask]
            current = current[mask]
            
            if len(voltage) < 10:
                continue
            
            # Calculate peaks
            peak_height = np.max(current) - np.min(current)
            peak_area = abs(np.trapz(current, voltage))
            
            concentrations.append(concentration)
            peak_heights.append(peak_height)
            peak_areas.append(peak_area)
            filenames.append(file_path.name)
            
        except Exception as e:
            logger.warning(f"⚠️ Could not process {file_path.name}: {e}")
    
    logger.info(f"✅ Successfully processed {len(concentrations)} files")
    
    if len(concentrations) >= 3:
        # Create calibration plots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Peak height calibration
        if len(set(concentrations)) >= 2:  # Need at least 2 different concentrations
            slope_h, intercept_h, r_value_h, _, _ = linregress(concentrations, peak_heights)
            r_squared_h = r_value_h ** 2
            
            ax1.scatter(concentrations, peak_heights, alpha=0.7, s=50)
            x_fit = np.linspace(min(concentrations), max(concentrations), 100)
            y_fit_h = slope_h * x_fit + intercept_h
            ax1.plot(x_fit, y_fit_h, 'r--', alpha=0.8)
            ax1.set_xlabel('Concentration (mM)')
            ax1.set_ylabel('Peak Height (A)')
            ax1.set_title(f'STM32 Peak Height Calibration\nR² = {r_squared_h:.4f}')
            ax1.grid(True, alpha=0.3)
        
        # Peak area calibration
        if len(set(concentrations)) >= 2:
            slope_a, intercept_a, r_value_a, _, _ = linregress(concentrations, peak_areas)
            r_squared_a = r_value_a ** 2
            
            ax2.scatter(concentrations, peak_areas, alpha=0.7, s=50)
            y_fit_a = slope_a * x_fit + intercept_a
            ax2.plot(x_fit, y_fit_a, 'r--', alpha=0.8)
            ax2.set_xlabel('Concentration (mM)')
            ax2.set_ylabel('Peak Area (A⋅V)')
            ax2.set_title(f'STM32 Peak Area Calibration\nR² = {r_squared_a:.4f}')
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('stm32_sample_calibration_test.png', dpi=300, bbox_inches='tight')
        logger.info("📊 Sample calibration plot saved: stm32_sample_calibration_test.png")
        
        # Print summary
        logger.info("\n📊 Sample Data Summary:")
        logger.info(f"   Concentrations: {sorted(set(concentrations))} mM")
        logger.info(f"   Peak heights: {min(peak_heights):.2e} to {max(peak_heights):.2e} A")
        logger.info(f"   Peak areas: {min(peak_areas):.2e} to {max(peak_areas):.2e} A⋅V")
        
        if len(set(concentrations)) >= 2:
            logger.info(f"   Height R²: {r_squared_h:.4f}")
            logger.info(f"   Area R²: {r_squared_a:.4f}")

def main():
    """Main test function"""
    logger.info("🧪 Quick Test - Enhanced CV Calibration")
    logger.info("=" * 50)
    
    test_file_reading()
    create_sample_calibration_plot()
    
    logger.info("\n✅ Quick test completed!")

if __name__ == "__main__":
    main()