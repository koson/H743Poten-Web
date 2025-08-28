#!/usr/bin/env python3
"""
Enhanced CV Calibration Analysis with Unit Conversion Support
=============================================================
Extended version that supports both original and converted STM32 files
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
from stm32_unit_converter import STM32UnitConverter

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class EnhancedCVCalibrationAnalyzer:
    """Enhanced CV Calibration Analyzer with automatic unit conversion"""
    
    def __init__(self, auto_convert_units: bool = True, 
                 conversion_input_dir: str = "test_data/raw_stm32",
                 conversion_output_dir: str = "test_data/converted_stm32"):
        """
        Initialize analyzer with unit conversion support
        
        Args:
            auto_convert_units: If True, automatically convert A to µA units
            conversion_input_dir: Directory with raw STM32 files (A units)
            conversion_output_dir: Directory for converted files (µA units)
        """
        self.auto_convert_units = auto_convert_units
        self.conversion_input_dir = conversion_input_dir
        self.conversion_output_dir = conversion_output_dir
        
        # Data storage
        self.palmsens_data = []
        self.stm32_data = []
        
        # Track which files came from conversion
        self.converted_files = set()
        
        logger.info(f"🔧 Auto-convert units: {auto_convert_units}")
        
    def run_unit_conversion_if_needed(self):
        """Run unit conversion for STM32 files if needed"""
        if not self.auto_convert_units:
            return
            
        # Check if there are files to convert
        input_path = Path(self.conversion_input_dir)
        if not input_path.exists():
            logger.info(f"📁 No conversion input directory found: {input_path}")
            return
            
        csv_files = list(input_path.glob("*.csv"))
        if not csv_files:
            logger.info(f"📁 No CSV files to convert in: {input_path}")
            return
            
        logger.info(f"🔄 Running automatic unit conversion...")
        converter = STM32UnitConverter(
            input_dir=self.conversion_input_dir,
            output_dir=self.conversion_output_dir
        )
        
        stats = converter.convert_batch()
        
        if stats['converted'] > 0:
            logger.info(f"✅ Converted {stats['converted']} files from A to µA")
            
            # Track which files were converted
            output_path = Path(self.conversion_output_dir)
            for converted_file in output_path.glob("*.csv"):
                self.converted_files.add(str(converted_file))
        
    def get_enhanced_data_directories(self) -> List[str]:
        """Get list of data directories including converted files"""
        directories = []
        
        # Original directories - use the large STM32 dataset
        original_dirs = ["Test_data/Palmsens", "test_data/raw_stm32"]
        for dir_path in original_dirs:
            if Path(dir_path).exists():
                directories.append(dir_path)
        
        # Add converted files directory if it exists and has files
        converted_path = Path(self.conversion_output_dir)
        if converted_path.exists() and any(converted_path.glob("*.csv")):
            directories.append(str(converted_path))
            logger.info(f"📁 Including converted files from: {converted_path}")
        
        return directories
    
    def detect_file_source(self, filepath: str) -> str:
        """Detect whether file is from Palmsens, STM32, or converted STM32"""
        filepath_lower = filepath.lower()
        
        # Check if it's a converted file
        if str(filepath) in self.converted_files:
            return "stm32_converted"
        
        # Check file path patterns
        if "palmsens" in filepath_lower:
            return "palmsens"
        elif "stm32" in filepath_lower or "pipot" in filepath_lower:
            return "stm32"
        elif self.conversion_output_dir in filepath:
            return "stm32_converted"
        else:
            # Fallback: try to detect from filename patterns
            filename = Path(filepath).name.lower()
            if filename.startswith("palmsens"):
                return "palmsens"
            elif filename.startswith("pipot") or "stm32" in filename:
                return "stm32"
            else:
                logger.warning(f"⚠️ Could not detect source for: {filename}")
                return "unknown"
    
    def extract_concentration_from_filename(self, filename: str) -> Optional[float]:
        """Extract concentration from filename - enhanced version"""
        filename_lower = filename.lower()
        
        # Handle special cases like "5_0mM" first (for PiPot data)
        ferro_underscore_pattern = r'ferro[_\-](\d+)[_\-](\d+)mm'
        match = re.search(ferro_underscore_pattern, filename_lower)
        if match:
            try:
                integer_part = float(match.group(1))
                decimal_part = float(match.group(2))
                return integer_part + decimal_part / 10  # Convert 5_0 to 5.0
            except ValueError:
                pass
        
        # Pattern 1: Standard patterns (e.g., "1.0mM", "10mM", "0.5mM")
        patterns = [
            r'(\d+\.?\d*)\s*mm',  # e.g., "1.0mM", "10mM"
            r'(\d+\.?\d*)\s*m\b',  # e.g., "1.0M" 
            r'ferro[_\-](\d+\.?\d*)[_\-]?mm',  # e.g., "Ferro_1.0_mM"
            r'(\d+\.?\d*)mm',  # e.g., "1mm"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename_lower)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
                pass
        
        logger.warning(f"⚠️ Could not extract concentration from: {filename}")
        return None
    
    def run_comprehensive_analysis(self):
        """Run comprehensive analysis including unit conversion"""
        logger.info("🚀 Starting Enhanced CV Calibration Analysis...")
        
        # Step 1: Run unit conversion if needed
        self.run_unit_conversion_if_needed()
        
        # Step 2: Get enhanced data directories
        data_dirs = self.get_enhanced_data_directories()
        logger.info(f"📁 Scanning directories: {data_dirs}")
        
        # Step 3: Process all files
        total_files = 0
        for data_dir in data_dirs:
            csv_files = list(Path(data_dir).glob("*.csv"))
            logger.info(f"📁 Found {len(csv_files)} files in {data_dir}")
            total_files += len(csv_files)
            
            for csv_file in csv_files:
                self.process_enhanced_file(str(csv_file))
        
        logger.info(f"📊 Total files processed: {total_files}")
        logger.info(f"📊 Palmsens data points: {len(self.palmsens_data)}")
        logger.info(f"📊 STM32 data points: {len(self.stm32_data)}")
        
        # Step 4: Create enhanced plots
        if self.palmsens_data and self.stm32_data:
            self.create_enhanced_comparison_plots()
        else:
            logger.warning("⚠️ Insufficient data for comparison plots")
    
    def process_enhanced_file(self, filepath: str):
        """Process a single file with enhanced source detection"""
        try:
            # Detect file source
            source = self.detect_file_source(filepath)
            if source == "unknown":
                return
                
            # Map converted files to stm32 for processing
            if source == "stm32_converted":
                source = "stm32"
                
            # Extract metadata
            filename = Path(filepath).name
            concentration = self.extract_concentration_from_filename(filename)
            scan_rate = self.extract_scan_rate_from_filename(filename)
            
            if concentration is None or scan_rate is None:
                logger.warning(f"⚠️ Missing metadata for {filename}")
                return
            
            # Process the file (reuse existing logic)
            peak_height, peak_area = self.extract_peaks_from_file(filepath)
            
            if peak_height is None or peak_area is None:
                logger.warning(f"⚠️ Could not extract peaks from {filename}")
                return
            
            # Store results
            result = {
                'filename': filename,
                'concentration': concentration,
                'scan_rate': scan_rate,
                'peak_height': peak_height,
                'peak_area': peak_area,
                'source_type': 'converted' if str(filepath) in self.converted_files else 'original'
            }
            
            if source == "palmsens":
                self.palmsens_data.append(result)
                logger.info(f"✅ palmsens: {filename} - {concentration}mM, SR={scan_rate}mV/s, height={peak_height:.2f}µA, area={peak_area:.2f}")
            elif source == "stm32":
                self.stm32_data.append(result)
                converted_marker = " (converted)" if str(filepath) in self.converted_files else ""
                logger.info(f"✅ stm32: {filename} - {concentration}mM, SR={scan_rate}mV/s, height={peak_height:.2f}µA, area={peak_area:.2f}{converted_marker}")
                
        except Exception as e:
            logger.error(f"❌ Error processing {filepath}: {e}")
    
    def extract_scan_rate_from_filename(self, filename: str) -> Optional[float]:
        """Extract scan rate from filename"""
        # Pattern: look for number followed by mVpS or mV/s
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
    
    def extract_peaks_from_file(self, filepath: str) -> Tuple[Optional[float], Optional[float]]:
        """Extract peak height and area from CV file - enhanced for converted files"""
        try:
            # Check if first line is metadata and skip it
            with open(filepath, 'r') as f:
                first_line = f.readline().strip()
            
            # Skip metadata line if present
            skiprows = 1 if first_line.startswith('FileName:') else 0
            df = pd.read_csv(filepath, encoding='utf-8-sig', skiprows=skiprows)
            
            # Find voltage and current columns (handles both original and converted units)
            voltage_col = None
            current_col = None
            
            for col in df.columns:
                col_clean = col.strip()
                col_lower = col_clean.lower()
                
                # Check for voltage columns (V, Voltage, Potential, etc.)
                if (col_clean == 'V' or 
                    'voltage' in col_lower or 
                    'potential' in col_lower or 
                    col_lower.startswith('v')):
                    voltage_col = col
                
                # Check for current columns (A, uA, Current, I, etc.)
                elif (col_clean == 'A' or 
                      col_clean == 'uA' or 
                      col_clean == 'µA' or
                      'current' in col_lower or 
                      col_lower.startswith('i')):
                    current_col = col
            
            if voltage_col is None or current_col is None:
                logger.warning(f"⚠️ Could not find voltage/current columns in {Path(filepath).name}")
                return None, None
            
            # Get data
            voltage = df[voltage_col].values
            current = df[current_col].values
            
            # Remove any NaN values
            mask = ~(np.isnan(voltage) | np.isnan(current))
            voltage = voltage[mask]
            current = current[mask]
            
            if len(voltage) < 10:
                logger.warning(f"⚠️ Insufficient data points in {Path(filepath).name}")
                return None, None
            
            # Simple peak detection
            peak_height = np.max(current) - np.min(current)
            
            # Area calculation (trapezoidal rule)
            peak_area = abs(np.trapz(current, voltage))
            
            return peak_height, peak_area
            
        except Exception as e:
            logger.error(f"❌ Error extracting peaks from {filepath}: {e}")
            return None, None
    
    def create_enhanced_comparison_plots(self):
        """Create enhanced comparison plots"""
        logger.info("📊 Creating enhanced comparison plots...")
        
        # Group data by scan rate
        palmsens_by_scanrate = {}
        stm32_by_scanrate = {}
        
        for data in self.palmsens_data:
            sr = data['scan_rate']
            if sr not in palmsens_by_scanrate:
                palmsens_by_scanrate[sr] = []
            palmsens_by_scanrate[sr].append(data)
        
        for data in self.stm32_data:
            sr = data['scan_rate']
            if sr not in stm32_by_scanrate:
                stm32_by_scanrate[sr] = []
            stm32_by_scanrate[sr].append(data)
        
        # Get all scan rates
        all_scan_rates = sorted(set(list(palmsens_by_scanrate.keys()) + list(stm32_by_scanrate.keys())))
        logger.info(f"📊 Found scan rates: {all_scan_rates} mV/s")
        
        # Create plots for each scan rate
        n_rates = len(all_scan_rates)
        fig, axes = plt.subplots(2, n_rates, figsize=(5*n_rates, 10))
        
        if n_rates == 1:
            axes = axes.reshape(-1, 1)
        
        colors = ['#E74C3C', '#3498DB']  # Red for Palmsens, Blue for STM32
        
        for i, scan_rate in enumerate(all_scan_rates):
            # Peak Height Plot
            ax_height = axes[0, i]
            
            # Palmsens data
            if scan_rate in palmsens_by_scanrate:
                palm_data = palmsens_by_scanrate[scan_rate]
                concentrations = [d['concentration'] for d in palm_data]
                heights = [d['peak_height'] for d in palm_data]
                ax_height.scatter(concentrations, heights, color=colors[0], alpha=0.7, s=50, label='Palmsens')
                
                # Fit line
                if len(concentrations) >= 2:
                    slope, intercept, r_value, p_value, std_err = linregress(concentrations, heights)
                    x_fit = np.linspace(min(concentrations), max(concentrations), 100)
                    y_fit = slope * x_fit + intercept
                    ax_height.plot(x_fit, y_fit, color=colors[0], linestyle='--', alpha=0.8)
                    ax_height.text(0.05, 0.95, f'Palmsens R²={r_value**2:.3f}', 
                                  transform=ax_height.transAxes, verticalalignment='top',
                                  bbox=dict(boxstyle='round', facecolor=colors[0], alpha=0.1))
            
            # STM32 data
            if scan_rate in stm32_by_scanrate:
                stm32_data_sr = stm32_by_scanrate[scan_rate]
                concentrations = [d['concentration'] for d in stm32_data_sr]
                heights = [d['peak_height'] for d in stm32_data_sr]
                
                # Mark converted vs original data differently
                converted_conc = [d['concentration'] for d in stm32_data_sr if d.get('source_type') == 'converted']
                converted_heights = [d['peak_height'] for d in stm32_data_sr if d.get('source_type') == 'converted']
                original_conc = [d['concentration'] for d in stm32_data_sr if d.get('source_type') != 'converted']
                original_heights = [d['peak_height'] for d in stm32_data_sr if d.get('source_type') != 'converted']
                
                if converted_conc:
                    ax_height.scatter(converted_conc, converted_heights, color=colors[1], alpha=0.7, s=50, 
                                    marker='s', label='STM32 (converted)')
                if original_conc:
                    ax_height.scatter(original_conc, original_heights, color=colors[1], alpha=0.7, s=50, 
                                    marker='o', label='STM32 (original)')
                
                # Fit line for all STM32 data
                if len(concentrations) >= 2:
                    slope, intercept, r_value, p_value, std_err = linregress(concentrations, heights)
                    x_fit = np.linspace(min(concentrations), max(concentrations), 100)
                    y_fit = slope * x_fit + intercept
                    ax_height.plot(x_fit, y_fit, color=colors[1], linestyle='--', alpha=0.8)
                    ax_height.text(0.05, 0.85, f'STM32 R²={r_value**2:.3f}', 
                                  transform=ax_height.transAxes, verticalalignment='top',
                                  bbox=dict(boxstyle='round', facecolor=colors[1], alpha=0.1))
            
            ax_height.set_xlabel('Concentration (mM)')
            ax_height.set_ylabel('Peak Height (µA)')
            ax_height.set_title(f'Peak Height vs Concentration\n{scan_rate} mV/s')
            ax_height.legend()
            ax_height.grid(True, alpha=0.3)
            
            # Peak Area Plot
            ax_area = axes[1, i]
            
            # Similar process for area...
            # (Implementation similar to height plot)
            
        plt.tight_layout()
        
        # Save plot
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_cv_calibration_{timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        logger.info(f"💾 Saved enhanced calibration plot: {filename}")
        
        plt.show()

def main():
    """Main function"""
    analyzer = EnhancedCVCalibrationAnalyzer(auto_convert_units=True)
    analyzer.run_comprehensive_analysis()

if __name__ == "__main__":
    main()