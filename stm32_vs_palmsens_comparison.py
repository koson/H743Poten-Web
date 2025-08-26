#!/usr/bin/env python3
"""
STM32 vs Palmsens Comparison Analysis
===================================
Compare calibration results between STM32 and Palmsens systems
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime

# Import advanced baseline detection
try:
    from baseline_detector_v4 import cv_baseline_detector_v4
    ADVANCED_BASELINE = True
    logging.info("✅ Advanced baseline detection available")
except ImportError:
    ADVANCED_BASELINE = False
    logging.warning("⚠️ Advanced baseline detection not available, using simple method")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class STM32PalmsensComparison:
    """Compare calibration results between STM32 and Palmsens systems"""
    
    def __init__(self):
        self.stm32_data = []
        self.palmsens_data = []
        self.corrections = self.load_baseline_corrections()
        
    def load_baseline_corrections(self) -> Dict:
        """Load baseline corrections if available"""
        try:
            with open("palmsens_baseline_corrections.json", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def extract_stm32_metadata(self, filename: str) -> Dict:
        """Extract scan rate from STM32 filename"""
        filename_lower = filename.lower()
        
        # Scan rate patterns for STM32
        scan_rate = None
        sr_patterns = [
            r'(\d+\.?\d*)\s*mvps',  # 20mVpS format
            r'(\d+\.?\d*)\s*mv[\/\-_]?s'
        ]
        
        for pattern in sr_patterns:
            match = re.search(pattern, filename_lower)
            if match:
                try:
                    scan_rate = float(match.group(1))
                    break
                except ValueError:
                    continue
        
        # Concentration from STM32 filename (different pattern)
        concentration = None
        # STM32 files typically have ferro concentration
        conc_patterns = [
            r'ferro[_\-](\d+\.?\d*)[_\-]?(\d*)mm',  # ferro_1_0mM
            r'(\d+\.?\d*)mm'  # Simple pattern
        ]
        
        for pattern in conc_patterns:
            match = re.search(pattern, filename_lower)
            if match:
                try:
                    if match.group(2):  # ferro_1_0mM format
                        concentration = float(f"{match.group(1)}.{match.group(2)}")
                    else:
                        concentration = float(match.group(1))
                    break
                except ValueError:
                    continue
        
        return {
            'concentration': concentration,
            'scan_rate': scan_rate,
            'system': 'STM32'
        }
    
    def extract_palmsens_metadata(self, filename: str) -> Dict:
        """Extract concentration and scan rate from Palmsens filename"""
        filename_lower = filename.lower()
        
        # Concentration from directory or filename
        concentration = None
        if 'palmsens_' in filename_lower:
            conc_match = re.search(r'palmsens_(\d+\.?\d*)mm', filename_lower)
            if conc_match:
                try:
                    concentration = float(conc_match.group(1))
                except ValueError:
                    pass
        
        # Scan rate
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
            'system': 'Palmsens'
        }
    
    def apply_baseline_correction(self, voltage: np.ndarray, current: np.ndarray, 
                                 correction: Dict) -> np.ndarray:
        """Apply saved baseline correction"""
        baseline_start = correction['baseline_start']
        baseline_end = correction['baseline_end']
        
        # Find points in baseline region
        mask = (voltage >= baseline_start) & (voltage <= baseline_end)
        
        if not np.any(mask):
            return current
        
        # Linear fit to baseline region
        baseline_v = voltage[mask]
        baseline_i = current[mask]
        
        if len(baseline_v) >= 2:
            coeffs = np.polyfit(baseline_v, baseline_i, 1)
            baseline_fit = np.polyval(coeffs, voltage)
            return current - baseline_fit
        
        return current
    
    def process_stm32_file(self, file_path: Path) -> Optional[Dict]:
        """Process a single STM32 file"""
        try:
            # Read STM32 file (should already be in µA)
            with open(file_path, 'r') as f:
                first_line = f.readline().strip()
            
            skiprows = 1 if first_line.startswith('FileName:') else 0
            df = pd.read_csv(file_path, encoding='utf-8-sig', skiprows=skiprows)
            
            # Should have V and uA columns (after conversion)
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
            
            # Advanced baseline correction if available
            if ADVANCED_BASELINE:
                try:
                    forward_baseline, reverse_baseline, info = cv_baseline_detector_v4(voltage, current)
                    # Create baseline fit from detected baseline points
                    baseline_fit = np.concatenate([forward_baseline, reverse_baseline])
                    baseline_v = np.concatenate([voltage[:len(forward_baseline)], voltage[-len(reverse_baseline):]])
                    
                    if len(baseline_v) >= 2:
                        # Fit line to detected baseline
                        slope, intercept, _, _, _ = linregress(baseline_v, baseline_fit)
                        full_baseline_fit = slope * voltage + intercept
                        corrected_current = current - full_baseline_fit
                        logger.debug(f"Advanced baseline: {info.get('detection_method', 'unknown')}")
                    else:
                        corrected_current = current
                except Exception as e:
                    logger.debug(f"Advanced baseline failed: {e}, using simple method")
                    # Fallback to simple method
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
            else:
                # Simple baseline correction (first/last 20%)
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
            metadata = self.extract_stm32_metadata(str(file_path))
            
            if metadata['concentration'] is None or metadata['scan_rate'] is None:
                return None
            
            result = {
                **metadata,
                'peak_height': peak_height,
                'peak_area': peak_area,
                'filepath': str(file_path),
                'filename': file_path.name
            }
            
            return result
            
        except Exception as e:
            logger.debug(f"Error processing STM32 {file_path.name}: {e}")
            return None
    
    def process_palmsens_file(self, file_path: Path) -> Optional[Dict]:
        """Process a single Palmsens file"""
        try:
            # Read Palmsens file
            with open(file_path, 'r') as f:
                first_line = f.readline().strip()
            
            skiprows = 1 if first_line.startswith('FileName:') else 0
            df = pd.read_csv(file_path, encoding='utf-8-sig', skiprows=skiprows)
            
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
            
            # Apply baseline correction if available
            file_key = str(file_path)
            if file_key in self.corrections:
                corrected_current = self.apply_baseline_correction(
                    voltage, current, self.corrections[file_key])
                logger.debug(f"Applied saved correction to {file_path.name}")
            elif ADVANCED_BASELINE:
                try:
                    forward_baseline, reverse_baseline, info = cv_baseline_detector_v4(voltage, current)
                    # Create baseline fit from detected baseline points
                    baseline_fit = np.concatenate([forward_baseline, reverse_baseline])
                    baseline_v = np.concatenate([voltage[:len(forward_baseline)], voltage[-len(reverse_baseline):]])
                    
                    if len(baseline_v) >= 2:
                        # Fit line to detected baseline
                        slope, intercept, _, _, _ = linregress(baseline_v, baseline_fit)
                        full_baseline_fit = slope * voltage + intercept
                        corrected_current = current - full_baseline_fit
                        logger.debug(f"Advanced baseline: {info.get('detection_method', 'unknown')}")
                    else:
                        corrected_current = current
                except Exception as e:
                    logger.debug(f"Advanced baseline failed: {e}, using simple method")
                    # Default baseline correction
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
            else:
                # Default baseline correction
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
            metadata = self.extract_palmsens_metadata(str(file_path))
            
            if metadata['concentration'] is None or metadata['scan_rate'] is None:
                return None
            
            result = {
                **metadata,
                'peak_height': peak_height,
                'peak_area': peak_area,
                'filepath': str(file_path),
                'filename': file_path.name
            }
            
            return result
            
        except Exception as e:
            logger.debug(f"Error processing Palmsens {file_path.name}: {e}")
            return None
    
    def load_all_data(self):
        """Load and process all STM32 and Palmsens data"""
        logger.info("🔄 Loading STM32 and Palmsens data for comparison...")
        
        # Load STM32 data
        stm32_dir = Path("Test_data/Stm32")
        stm32_files = list(stm32_dir.rglob("*.csv"))
        logger.info(f"📂 Found {len(stm32_files)} STM32 files")
        
        stm32_processed = 0
        for file_path in stm32_files[:50]:  # Limit for performance
            result = self.process_stm32_file(file_path)
            if result:
                self.stm32_data.append(result)
                stm32_processed += 1
        
        logger.info(f"✅ Processed {stm32_processed} STM32 files")
        
        # Load Palmsens data
        palmsens_dir = Path("Test_data/Palmsens")
        palmsens_files = list(palmsens_dir.rglob("*.csv"))
        logger.info(f"📂 Found {len(palmsens_files)} Palmsens files")
        
        palmsens_processed = 0
        # Sample files more strategically to get variety
        from collections import defaultdict
        palmsens_by_condition = defaultdict(list)
        
        # Group files by condition first
        for file_path in palmsens_files:
            metadata = self.extract_palmsens_metadata(str(file_path))
            if metadata['concentration'] is not None and metadata['scan_rate'] is not None:
                key = (metadata['concentration'], metadata['scan_rate'])
                palmsens_by_condition[key].append(file_path)
        
        # Sample from each condition
        max_per_condition = 3
        for (conc, sr), files in palmsens_by_condition.items():
            sampled_files = files[:max_per_condition]
            for file_path in sampled_files:
                result = self.process_palmsens_file(file_path)
                if result:
                    self.palmsens_data.append(result)
                    palmsens_processed += 1
        
        logger.info(f"✅ Processed {palmsens_processed} Palmsens files")
        logger.info(f"📊 Total data points: {len(self.stm32_data) + len(self.palmsens_data)}")
    
    def compare_by_scan_rate(self):
        """Compare calibration curves by scan rate between systems"""
        logger.info("\n📊 Comparing STM32 vs Palmsens by Scan Rate")
        logger.info("=" * 50)
        
        # Get common scan rates
        stm32_scan_rates = set(d['scan_rate'] for d in self.stm32_data)
        palmsens_scan_rates = set(d['scan_rate'] for d in self.palmsens_data)
        common_scan_rates = sorted(stm32_scan_rates & palmsens_scan_rates)
        
        logger.info(f"🔄 STM32 scan rates: {sorted(stm32_scan_rates)}")
        logger.info(f"🔄 Palmsens scan rates: {sorted(palmsens_scan_rates)}")
        logger.info(f"🎯 Common scan rates: {common_scan_rates}")
        
        if not common_scan_rates:
            logger.warning("⚠️ No common scan rates found!")
            return
        
        # Create comparison plots
        n_rates = len(common_scan_rates)
        n_cols = min(3, n_rates)
        n_rows = (n_rates + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(6*n_cols, 5*n_rows))
        if n_rates == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = axes if n_cols > 1 else [axes]
        else:
            axes = axes.flatten()
        
        comparison_results = {}
        
        for i, scan_rate in enumerate(common_scan_rates):
            # Filter data for this scan rate
            stm32_subset = [d for d in self.stm32_data if d['scan_rate'] == scan_rate]
            palmsens_subset = [d for d in self.palmsens_data if d['scan_rate'] == scan_rate]
            
            if len(stm32_subset) < 3 or len(palmsens_subset) < 3:
                logger.warning(f"⚠️ Insufficient data for {scan_rate} mV/s")
                continue
            
            ax = axes[i]
            
            # STM32 data
            stm32_conc = np.array([d['concentration'] for d in stm32_subset])
            stm32_height = np.array([d['peak_height'] for d in stm32_subset])
            
            # Palmsens data
            palmsens_conc = np.array([d['concentration'] for d in palmsens_subset])
            palmsens_height = np.array([d['peak_height'] for d in palmsens_subset])
            
            # Linear regression for each system
            # Check for sufficient concentration variety
            stm32_unique_conc = len(np.unique(stm32_conc))
            palmsens_unique_conc = len(np.unique(palmsens_conc))
            
            if stm32_unique_conc < 2:
                logger.warning(f"⚠️ STM32: Insufficient concentration variety for {scan_rate} mV/s")
                continue
            if palmsens_unique_conc < 2:
                logger.warning(f"⚠️ Palmsens: Insufficient concentration variety for {scan_rate} mV/s")
                continue
            
            stm32_slope, stm32_intercept, stm32_r, _, _ = linregress(stm32_conc, stm32_height)
            palmsens_slope, palmsens_intercept, palmsens_r, _, _ = linregress(palmsens_conc, palmsens_height)
            
            stm32_r2 = stm32_r ** 2
            palmsens_r2 = palmsens_r ** 2
            
            # Plot data and fits
            ax.scatter(stm32_conc, stm32_height, alpha=0.7, s=50, color='blue',
                      label=f'STM32 (R²={stm32_r2:.3f})')
            ax.scatter(palmsens_conc, palmsens_height, alpha=0.7, s=50, color='red',
                      label=f'Palmsens (R²={palmsens_r2:.3f})')
            
            # Fit lines
            all_conc = np.concatenate([stm32_conc, palmsens_conc])
            conc_range = np.linspace(min(all_conc), max(all_conc), 100)
            
            stm32_fit = stm32_slope * conc_range + stm32_intercept
            palmsens_fit = palmsens_slope * conc_range + palmsens_intercept
            
            ax.plot(conc_range, stm32_fit, 'b--', alpha=0.8, linewidth=2)
            ax.plot(conc_range, palmsens_fit, 'r--', alpha=0.8, linewidth=2)
            
            ax.set_xlabel('Concentration (mM)')
            ax.set_ylabel('Peak Height (µA)')
            ax.set_title(f'{scan_rate} mV/s Comparison')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Store comparison results
            comparison_results[scan_rate] = {
                'stm32': {
                    'n_samples': len(stm32_subset),
                    'slope': stm32_slope,
                    'r2': stm32_r2,
                    'conc_range': [min(stm32_conc), max(stm32_conc)]
                },
                'palmsens': {
                    'n_samples': len(palmsens_subset),
                    'slope': palmsens_slope,
                    'r2': palmsens_r2,
                    'conc_range': [min(palmsens_conc), max(palmsens_conc)]
                },
                'slope_ratio': palmsens_slope / stm32_slope if stm32_slope != 0 else None
            }
            
            logger.info(f"   {scan_rate} mV/s:")
            logger.info(f"      STM32: {len(stm32_subset)} samples, slope={stm32_slope:.2f}, R²={stm32_r2:.3f}")
            logger.info(f"      Palmsens: {len(palmsens_subset)} samples, slope={palmsens_slope:.2f}, R²={palmsens_r2:.3f}")
            if comparison_results[scan_rate]['slope_ratio']:
                logger.info(f"      Slope ratio (P/S): {comparison_results[scan_rate]['slope_ratio']:.2f}")
        
        # Hide extra subplots
        for i in range(len(common_scan_rates), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_filename = f"stm32_vs_palmsens_comparison_{timestamp}.png"
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        logger.info(f"📊 Comparison plots saved: {plot_filename}")
        
        # Save comparison report
        report_filename = f"stm32_vs_palmsens_report_{timestamp}.json"
        with open(report_filename, 'w') as f:
            json.dump(comparison_results, f, indent=2)
        logger.info(f"📄 Comparison report saved: {report_filename}")
        
        return comparison_results
    
    def generate_summary_table(self):
        """Generate summary comparison table"""
        logger.info("\n📊 STM32 vs Palmsens Summary Comparison")
        logger.info("=" * 55)
        
        # System summaries
        stm32_conc = sorted(set(d['concentration'] for d in self.stm32_data))
        stm32_sr = sorted(set(d['scan_rate'] for d in self.stm32_data))
        palmsens_conc = sorted(set(d['concentration'] for d in self.palmsens_data))
        palmsens_sr = sorted(set(d['scan_rate'] for d in self.palmsens_data))
        
        logger.info("📊 STM32 System:")
        logger.info(f"   📂 Files processed: {len(self.stm32_data)}")
        logger.info(f"   🧪 Concentrations: {stm32_conc} mM")
        logger.info(f"   ⚡ Scan rates: {stm32_sr} mV/s")
        
        logger.info("\n📊 Palmsens System:")
        logger.info(f"   📂 Files processed: {len(self.palmsens_data)}")
        logger.info(f"   🧪 Concentrations: {palmsens_conc} mM")
        logger.info(f"   ⚡ Scan rates: {palmsens_sr} mV/s")
        
        # Peak ranges
        stm32_heights = [d['peak_height'] for d in self.stm32_data]
        palmsens_heights = [d['peak_height'] for d in self.palmsens_data]
        
        logger.info(f"\n📏 Peak Height Ranges:")
        logger.info(f"   STM32: {min(stm32_heights):.1f} to {max(stm32_heights):.1f} µA")
        logger.info(f"   Palmsens: {min(palmsens_heights):.1f} to {max(palmsens_heights):.1f} µA")
        
        # Common conditions
        common_conc = sorted(set(stm32_conc) & set(palmsens_conc))
        common_sr = sorted(set(stm32_sr) & set(palmsens_sr))
        
        logger.info(f"\n🎯 Common Conditions:")
        logger.info(f"   Concentrations: {common_conc} mM")
        logger.info(f"   Scan rates: {common_sr} mV/s")
        
        if self.corrections:
            logger.info(f"\n🔧 Baseline Corrections Applied: {len(self.corrections)} files")
        
        logger.info("\n✅ STM32 vs Palmsens comparison completed!")
        logger.info("   - Both systems analyzed in µA units")
        logger.info("   - Calibration curves compared by scan rate")
        logger.info("   - Ready for detailed analysis and validation")
    
    def run_comparison(self):
        """Main method to run full comparison"""
        logger.info("🚀 Starting STM32 vs Palmsens Comparison Analysis")
        logger.info("=" * 60)
        
        # Load all data
        self.load_all_data()
        
        if not self.stm32_data or not self.palmsens_data:
            logger.error("❌ Insufficient data for comparison!")
            return
        
        # Compare by scan rate
        comparison_results = self.compare_by_scan_rate()
        
        # Generate summary
        self.generate_summary_table()
        
        return comparison_results

def main():
    """Main execution"""
    comparison = STM32PalmsensComparison()
    comparison.run_comparison()

if __name__ == "__main__":
    main()