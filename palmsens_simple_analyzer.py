#!/usr/bin/env python3
"""
Palmsens Simple Analysis by Scan Rate
====================================
Simple analysis without sklearn dependency
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import re
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class SimplePalmsensAnalyzer:
    """Simple analysis for Palmsens CV data by scan rate"""
    
    def __init__(self, max_files_per_condition: int = 3):
        """Initialize analyzer with limited file processing"""
        self.max_files_per_condition = max_files_per_condition
        self.processed_data = []
        
    def extract_metadata(self, filename: str) -> Dict:
        """Extract concentration and scan rate from filename"""
        filename_lower = filename.lower()
        
        # Concentration from filename path or name
        concentration = None
        
        # Try directory name first (e.g., "Palmsens_0.5mM")
        if 'palmsens_' in filename_lower:
            conc_match = re.search(r'palmsens_(\d+\.?\d*)mm', filename_lower)
            if conc_match:
                try:
                    concentration = float(conc_match.group(1))
                except ValueError:
                    pass
        
        # Scan rate extraction
        scan_rate = None
        sr_patterns = [
            r'(\d+\.?\d*)\s*mv[\/\-_]?s',
            r'cv[_\-](\d+\.?\d*)mvps'
        ]
        
        for pattern in sr_patterns:
            match = re.search(pattern, filename_lower)
            if match:
                try:
                    scan_rate = float(match.group(1))
                    break
                except ValueError:
                    continue
        
        return {
            'concentration': concentration,
            'scan_rate': scan_rate,
            'filename': filename
        }
    
    def process_file(self, file_path: Path) -> Optional[Dict]:
        """Process a single Palmsens CSV file"""
        try:
            # Check for metadata line
            with open(file_path, 'r') as f:
                first_line = f.readline().strip()
            
            skiprows = 1 if first_line.startswith('FileName:') else 0
            df = pd.read_csv(file_path, encoding='utf-8-sig', skiprows=skiprows)
            
            # Assume standard format: V, uA
            if 'V' not in df.columns or 'uA' not in df.columns:
                return None
            
            voltage = df['V'].values
            current = df['uA'].values
            
            # Remove NaN values
            mask = ~(np.isnan(voltage) | np.isnan(current))
            voltage = voltage[mask]
            current = current[mask]
            
            if len(voltage) < 10:
                return None
            
            # Simple baseline correction (linear fit to first/last 20%)
            n_points = len(voltage)
            baseline_indices = np.concatenate([
                np.arange(0, int(0.2 * n_points)),
                np.arange(int(0.8 * n_points), n_points)
            ])
            
            if len(baseline_indices) >= 2:
                baseline_v = voltage[baseline_indices]
                baseline_i = current[baseline_indices]
                slope, intercept, _, _, _ = linregress(baseline_v, baseline_i)
                baseline_fit = slope * voltage + intercept
                corrected_current = current - baseline_fit
            else:
                corrected_current = current
            
            # Calculate peak metrics
            peak_height = np.max(corrected_current) - np.min(corrected_current)
            peak_area = abs(np.trapz(corrected_current, voltage))
            
            # Extract metadata
            metadata = self.extract_metadata(str(file_path))
            
            if metadata['concentration'] is None or metadata['scan_rate'] is None:
                return None
            
            result = {
                **metadata,
                'peak_height': peak_height,
                'peak_area': peak_area,
                'filepath': str(file_path)
            }
            
            return result
            
        except Exception as e:
            logger.debug(f"Error processing {file_path.name}: {e}")
            return None
    
    def sample_files_intelligently(self, data_dir: Path) -> List[Path]:
        """Sample files to avoid overwhelming processing"""
        logger.info("📂 Sampling Palmsens files for analysis...")
        
        all_files = list(data_dir.rglob("*.csv"))
        logger.info(f"   Found {len(all_files)} total files")
        
        # Group files by concentration and scan rate
        file_groups = {}
        
        for file_path in all_files:
            metadata = self.extract_metadata(str(file_path))
            if metadata['concentration'] is not None and metadata['scan_rate'] is not None:
                key = (metadata['concentration'], metadata['scan_rate'])
                if key not in file_groups:
                    file_groups[key] = []
                file_groups[key].append(file_path)
        
        logger.info(f"   Found {len(file_groups)} unique conditions")
        
        # Sample from each group
        sampled_files = []
        for (conc, sr), files in file_groups.items():
            # Sort files for consistent sampling
            files.sort()
            sampled = files[:self.max_files_per_condition]
            sampled_files.extend(sampled)
            
            logger.debug(f"   {conc}mM @ {sr}mV/s: {len(sampled)}/{len(files)} files")
        
        logger.info(f"📊 Selected {len(sampled_files)} files for analysis")
        return sampled_files
    
    def run_analysis(self):
        """Run simple analysis by scan rate"""
        logger.info("🚀 Starting Simple Palmsens Analysis by Scan Rate")
        logger.info("=" * 55)
        
        data_dir = Path("Test_data/Palmsens")
        
        # Sample files intelligently
        sampled_files = self.sample_files_intelligently(data_dir)
        
        # Process sampled files
        logger.info("🔄 Processing sampled files...")
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
        """Simple calibration analysis by scan rate"""
        logger.info("\n📊 Calibration Analysis by Scan Rate")
        
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
        
        results_summary = {}
        
        for i, scan_rate in enumerate(scan_rates):
            data_group = scan_rate_groups[scan_rate]
            
            if len(data_group) < 3:
                logger.warning(f"⚠️ Insufficient data for {scan_rate} mV/s")
                continue
            
            # Extract data
            concentrations = np.array([d['concentration'] for d in data_group])
            peak_heights = np.array([d['peak_height'] for d in data_group])
            peak_areas = np.array([d['peak_area'] for d in data_group])
            
            # Check concentration variety
            unique_concentrations = len(np.unique(concentrations))
            if unique_concentrations < 2:
                logger.warning(f"⚠️ Insufficient concentration variety for {scan_rate} mV/s")
                continue
            
            # Linear regression for peak height and area
            slope_h, intercept_h, r_value_h, _, _ = linregress(concentrations, peak_heights)
            slope_a, intercept_a, r_value_a, _, _ = linregress(concentrations, peak_areas)
            
            r2_height = r_value_h ** 2
            r2_area = r_value_a ** 2
            
            # Plot results
            ax = axes[i]
            
            # Peak height calibration
            ax.scatter(concentrations, peak_heights, alpha=0.7, s=50, 
                      label=f'Peak Height (R²={r2_height:.3f})')
            
            # Fit line
            conc_range = np.linspace(min(concentrations), max(concentrations), 100)
            height_fit = slope_h * conc_range + intercept_h
            ax.plot(conc_range, height_fit, 'r--', alpha=0.8)
            
            # Peak area if different trend
            if abs(r2_area - r2_height) > 0.1:
                ax2 = ax.twinx()
                ax2.scatter(concentrations, peak_areas, alpha=0.5, s=30, 
                           color='green', label=f'Peak Area (R²={r2_area:.3f})')
                area_fit = slope_a * conc_range + intercept_a
                ax2.plot(conc_range, area_fit, 'g:', alpha=0.8)
                ax2.set_ylabel('Peak Area (µA⋅V)', color='green')
                ax2.tick_params(axis='y', labelcolor='green')
            
            ax.set_xlabel('Concentration (mM)')
            ax.set_ylabel('Peak Height (µA)')
            ax.set_title(f'{scan_rate} mV/s Palmsens Calibration')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Store results
            results_summary[scan_rate] = {
                'n_samples': len(data_group),
                'height_r2': r2_height,
                'area_r2': r2_area,
                'height_slope': slope_h,
                'area_slope': slope_a,
                'concentrations': sorted(set(concentrations))
            }
            
            logger.info(f"   {scan_rate} mV/s: {len(data_group)} samples, "
                       f"Height R²={r2_height:.3f}, Area R²={r2_area:.3f}")
        
        # Hide extra subplots
        for i in range(len(scan_rates), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_filename = f"palmsens_simple_analysis_{timestamp}.png"
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        logger.info(f"📊 Analysis plots saved: {plot_filename}")
        
        # Save results
        report_filename = f"palmsens_simple_report_{timestamp}.json"
        with open(report_filename, 'w') as f:
            json.dump(results_summary, f, indent=2)
        logger.info(f"📄 Analysis report saved: {report_filename}")
        
        return results_summary
    
    def generate_summary(self):
        """Generate summary report"""
        logger.info("\n📊 Palmsens Simple Analysis Summary:")
        logger.info("=" * 40)
        
        total_files = len(self.processed_data)
        concentrations = sorted(set(d['concentration'] for d in self.processed_data))
        scan_rates = sorted(set(d['scan_rate'] for d in self.processed_data))
        
        peak_heights = [d['peak_height'] for d in self.processed_data]
        peak_areas = [d['peak_area'] for d in self.processed_data]
        
        logger.info(f"📂 Total processed files: {total_files}")
        logger.info(f"🧪 Concentrations: {concentrations} mM")
        logger.info(f"⚡ Scan rates: {scan_rates} mV/s")
        logger.info(f"📏 Peak height range: {min(peak_heights):.1f} to {max(peak_heights):.1f} µA")
        logger.info(f"📐 Peak area range: {min(peak_areas):.1f} to {max(peak_areas):.1f} µA⋅V")
        
        logger.info("\n✅ Palmsens Simple Analysis completed!")
        logger.info("   - Linear calibration curves generated")
        logger.info("   - Analysis by scan rate completed")
        logger.info("   - Ready for comparison with STM32 data")

def main():
    """Main execution"""
    analyzer = SimplePalmsensAnalyzer(max_files_per_condition=3)
    analyzer.run_analysis()

if __name__ == "__main__":
    main()