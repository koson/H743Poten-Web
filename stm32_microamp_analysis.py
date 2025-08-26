#!/usr/bin/env python3
"""
STM32 µA Calibration Analysis
============================
Final calibration analysis with µA units compatible with Palmsens framework
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
import logging
from pathlib import Path
import re
from typing import Dict, List, Optional
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class STM32MicroampAnalyzer:
    """STM32 calibration analyzer with µA units"""
    
    def __init__(self, max_files_per_condition: int = 3):
        """Initialize analyzer"""
        self.max_files_per_condition = max_files_per_condition
        self.processed_data = []
        
    def extract_metadata(self, filename: str) -> Dict:
        """Extract concentration, scan rate, electrode from filename"""
        # Concentration extraction (improved for PiPot format)
        concentration = None
        filename_lower = filename.lower()
        
        # Handle PiPot format like "5_0mM"
        ferro_underscore = re.search(r'ferro[_\-](\d+)[_\-](\d+)mm', filename_lower)
        if ferro_underscore:
            try:
                integer_part = float(ferro_underscore.group(1))
                decimal_part = float(ferro_underscore.group(2))
                concentration = integer_part + decimal_part / 10
            except ValueError:
                pass
        
        # Standard patterns
        if concentration is None:
            patterns = [r'(\d+\.?\d*)\s*mm', r'(\d+\.?\d*)mm']
            for pattern in patterns:
                match = re.search(pattern, filename_lower)
                if match:
                    try:
                        concentration = float(match.group(1))
                        break
                    except ValueError:
                        continue
        
        # Scan rate extraction
        scan_rate = None
        sr_patterns = [r'(\d+\.?\d*)\s*mvps', r'(\d+\.?\d*)\s*mv[\/\-_]?s']
        for pattern in sr_patterns:
            match = re.search(pattern, filename_lower)
            if match:
                try:
                    scan_rate = float(match.group(1))
                    break
                except ValueError:
                    continue
        
        # Electrode extraction
        electrode = None
        elec_match = re.search(r'e(\d+)', filename_lower)
        if elec_match:
            try:
                electrode = int(elec_match.group(1))
            except ValueError:
                pass
        
        # Scan number
        scan_match = re.search(r'scan[_\-]?(\d+)', filename_lower)
        scan_num = int(scan_match.group(1)) if scan_match else None
        
        return {
            'concentration': concentration,
            'scan_rate': scan_rate,
            'electrode': electrode,
            'scan_number': scan_num,
            'filename': filename
        }
    
    def process_file(self, filepath: Path) -> Optional[Dict]:
        """Process a single CSV file with µA units"""
        try:
            # Check if first line is metadata
            with open(filepath, 'r') as f:
                first_line = f.readline().strip()
            
            skiprows = 1 if first_line.startswith('FileName:') else 0
            df = pd.read_csv(filepath, encoding='utf-8-sig', skiprows=skiprows)
            
            # Look for V and uA columns (after conversion)
            if 'V' not in df.columns or 'uA' not in df.columns:
                logger.debug(f"Missing V,uA columns in {filepath.name}")
                return None
            
            voltage = df['V'].values
            current = df['uA'].values  # Now in µA
            
            # Remove NaN values
            mask = ~(np.isnan(voltage) | np.isnan(current))
            voltage = voltage[mask]
            current = current[mask]
            
            if len(voltage) < 10:
                return None
            
            # Calculate peaks (now in µA)
            peak_height = np.max(current) - np.min(current)
            peak_area = abs(np.trapz(current, voltage))
            
            # Extract metadata
            metadata = self.extract_metadata(filepath.name)
            
            if metadata['concentration'] is None or metadata['scan_rate'] is None:
                return None
            
            result = {
                **metadata,
                'peak_height': peak_height,  # µA
                'peak_area': peak_area,      # µA⋅V
                'filepath': str(filepath)
            }
            
            return result
            
        except Exception as e:
            logger.debug(f"Could not process {filepath.name}: {e}")
            return None
    
    def sample_files_intelligently(self, data_dir: Path) -> List[Path]:
        """Sample files intelligently to get good coverage"""
        logger.info("📂 Sampling STM32 files (µA units)...")
        
        all_files = list(data_dir.glob("*.csv"))
        logger.info(f"   Found {len(all_files)} total files")
        
        # Group files by condition
        file_groups = {}
        
        for file_path in all_files:
            metadata = self.extract_metadata(file_path.name)
            if metadata['concentration'] is not None and metadata['scan_rate'] is not None:
                key = (metadata['concentration'], metadata['scan_rate'])
                if key not in file_groups:
                    file_groups[key] = []
                file_groups[key].append(file_path)
        
        logger.info(f"   Found {len(file_groups)} unique conditions")
        
        # Sample from each group
        sampled_files = []
        for (conc, sr), files in file_groups.items():
            files.sort(key=lambda f: (
                self.extract_metadata(f.name).get('electrode', 0),
                self.extract_metadata(f.name).get('scan_number', 0)
            ))
            
            sampled = files[:self.max_files_per_condition]
            sampled_files.extend(sampled)
            
            logger.debug(f"   {conc}mM @ {sr}mV/s: {len(sampled)}/{len(files)} files")
        
        logger.info(f"📊 Selected {len(sampled_files)} files for analysis")
        return sampled_files
    
    def run_analysis(self):
        """Run complete analysis with µA units"""
        logger.info("🚀 Starting STM32 µA Calibration Analysis")
        logger.info("=" * 60)
        
        data_dir = Path("test_data/raw_stm32")
        
        # Sample files intelligently
        sampled_files = self.sample_files_intelligently(data_dir)
        
        # Process sampled files
        logger.info("🔄 Processing files with µA units...")
        successful = 0
        failed = 0
        
        for file_path in sampled_files:
            result = self.process_file(file_path)
            if result:
                self.processed_data.append(result)
                successful += 1
            else:
                failed += 1
        
        logger.info(f"✅ Processed {successful} files successfully")
        logger.info(f"❌ Failed to process {failed} files")
        
        if len(self.processed_data) < 10:
            logger.warning("⚠️ Insufficient data for reliable analysis")
            return
        
        # Analyze by scan rate
        self.analyze_by_scan_rate()
        
        # Generate summary
        self.generate_summary()
    
    def analyze_by_scan_rate(self):
        """Analyze calibration curves for each scan rate"""
        logger.info("\n📊 Analyzing µA calibration curves by scan rate...")
        
        # Group by scan rate
        scan_rate_groups = {}
        for data in self.processed_data:
            sr = data['scan_rate']
            if sr not in scan_rate_groups:
                scan_rate_groups[sr] = []
            scan_rate_groups[sr].append(data)
        
        scan_rates = sorted(scan_rate_groups.keys())
        logger.info(f"📊 Found scan rates: {scan_rates} mV/s")
        
        # Create plots
        n_rates = len(scan_rates)
        n_cols = min(3, n_rates)
        n_rows = (n_rates + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows))
        if n_rates == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
        
        # Hide extra subplots
        for i in range(n_rates, len(axes)):
            axes[i].set_visible(False)
        
        results_summary = {}
        
        for i, scan_rate in enumerate(scan_rates):
            data_group = scan_rate_groups[scan_rate]
            
            # Extract concentration and peak data
            concentrations = [d['concentration'] for d in data_group]
            peak_heights = [d['peak_height'] for d in data_group]
            peak_areas = [d['peak_area'] for d in data_group]
            
            if len(set(concentrations)) < 2:
                logger.warning(f"⚠️ Insufficient concentration variety for {scan_rate} mV/s")
                continue
            
            # Calculate calibration statistics
            slope_h, intercept_h, r_value_h, _, _ = linregress(concentrations, peak_heights)
            slope_a, intercept_a, r_value_a, _, _ = linregress(concentrations, peak_areas)
            
            r_squared_h = r_value_h ** 2
            r_squared_a = r_value_a ** 2
            
            # Plot on subplot
            ax = axes[i]
            
            # Plot peak height data and fit
            ax.scatter(concentrations, peak_heights, alpha=0.7, s=30, label='Peak Height')
            conc_range = np.linspace(min(concentrations), max(concentrations), 100)
            height_fit = slope_h * conc_range + intercept_h
            ax.plot(conc_range, height_fit, 'r--', alpha=0.8, label=f'Height R²={r_squared_h:.3f}')
            
            ax.set_xlabel('Concentration (mM)')
            ax.set_ylabel('Peak Height (µA)')
            ax.set_title(f'{scan_rate} mV/s STM32 µA Calibration')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Store results
            results_summary[scan_rate] = {
                'n_points': len(data_group),
                'concentrations': sorted(set(concentrations)),
                'height_r2': r_squared_h,
                'area_r2': r_squared_a,
                'height_slope': slope_h,  # µA/mM
                'area_slope': slope_a     # µA⋅V/mM
            }
            
            logger.info(f"   {scan_rate} mV/s: {len(data_group)} points, Height R²={r_squared_h:.3f}, Area R²={r_squared_a:.3f}")
        
        plt.tight_layout()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_filename = f"stm32_microamp_calibration_{timestamp}.png"
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        logger.info(f"📊 µA calibration plots saved: {plot_filename}")
        
        # Save detailed results
        report_filename = f"stm32_microamp_report_{timestamp}.json"
        with open(report_filename, 'w') as f:
            json.dump(results_summary, f, indent=2)
        logger.info(f"📄 µA analysis report saved: {report_filename}")
        
        return results_summary
    
    def generate_summary(self):
        """Generate analysis summary"""
        logger.info("\n📊 STM32 µA Analysis Summary:")
        logger.info("=" * 40)
        
        total_files = len(self.processed_data)
        concentrations = sorted(set(d['concentration'] for d in self.processed_data))
        scan_rates = sorted(set(d['scan_rate'] for d in self.processed_data))
        electrodes = sorted(set(d['electrode'] for d in self.processed_data if d['electrode'] is not None))
        
        peak_heights = [d['peak_height'] for d in self.processed_data]
        peak_areas = [d['peak_area'] for d in self.processed_data]
        
        logger.info(f"📂 Total processed files: {total_files}")
        logger.info(f"🧪 Concentrations: {concentrations} mM")
        logger.info(f"⚡ Scan rates: {scan_rates} mV/s")
        logger.info(f"🔌 Electrodes: {electrodes}")
        logger.info(f"📏 Peak height range: {min(peak_heights):.1f} to {max(peak_heights):.1f} µA")
        logger.info(f"📐 Peak area range: {min(peak_areas):.1f} to {max(peak_areas):.1f} µA⋅V")
        
        logger.info("\n✅ STM32 µA Analysis completed!")
        logger.info("   - Units now compatible with Palmsens framework")
        logger.info("   - Ready for unified analysis")

def main():
    """Main execution"""
    analyzer = STM32MicroampAnalyzer(max_files_per_condition=3)
    analyzer.run_analysis()

if __name__ == "__main__":
    main()