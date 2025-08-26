#!/usr/bin/env python3
"""
STM32 vs Palmsens with Peak Detection
===================================
Enhanced comparison with proper peak detection
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
from scipy.signal import find_peaks
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class PeakEnhancedComparison:
    """Comparison with proper peak detection and baseline correction"""
    
    def __init__(self):
        self.stm32_data = []
        self.palmsens_data = []
        
    def find_cv_peaks(self, voltage: np.ndarray, current: np.ndarray) -> Dict:
        """Enhanced CV peak detection"""
        # Sort by voltage to ensure proper order
        sorted_indices = np.argsort(voltage)
        v_sorted = voltage[sorted_indices]
        i_sorted = current[sorted_indices]
        
        # Adaptive threshold based on data characteristics
        i_std = np.std(i_sorted)
        i_mean = np.mean(i_sorted)
        i_range = np.max(i_sorted) - np.min(i_sorted)
        
        # Find peaks (positive excursions) and valleys (negative excursions)
        peak_threshold = max(i_mean + 1.5*i_std, i_range * 0.1)
        valley_threshold = max(abs(i_mean - 1.5*i_std), i_range * 0.1)
        
        # Minimum distance between peaks
        min_distance = max(3, len(v_sorted) // 30)
        
        try:
            peaks_pos, _ = find_peaks(i_sorted, height=peak_threshold, distance=min_distance)
            peaks_neg, _ = find_peaks(-i_sorted, height=valley_threshold, distance=min_distance)
        except Exception:
            peaks_pos = []
            peaks_neg = []
        
        results = {
            'oxidation_current': 0,
            'reduction_current': 0,
            'peak_separation': 0,
            'oxidation_voltage': None,
            'reduction_voltage': None
        }
        
        # Process oxidation peaks
        if len(peaks_pos) > 0:
            max_ox_idx = peaks_pos[np.argmax(i_sorted[peaks_pos])]
            results['oxidation_current'] = i_sorted[max_ox_idx]
            results['oxidation_voltage'] = v_sorted[max_ox_idx]
        
        # Process reduction peaks
        if len(peaks_neg) > 0:
            max_red_idx = peaks_neg[np.argmax(-i_sorted[peaks_neg])]
            results['reduction_current'] = abs(i_sorted[max_red_idx])
            results['reduction_voltage'] = v_sorted[max_red_idx]
        
        # Calculate peak separation if both peaks exist
        if results['oxidation_voltage'] is not None and results['reduction_voltage'] is not None:
            results['peak_separation'] = abs(results['oxidation_voltage'] - results['reduction_voltage'])
        
        return results
    
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
        
        # Concentration from STM32 filename
        concentration = None
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
    
    def simple_baseline_correction(self, voltage: np.ndarray, current: np.ndarray) -> np.ndarray:
        """Improved simple baseline correction"""
        n_points = len(voltage)
        
        # Use smaller baseline regions (first/last 10%)
        baseline_indices = np.concatenate([
            np.arange(0, int(0.1 * n_points)),
            np.arange(int(0.9 * n_points), n_points)
        ])
        
        if len(baseline_indices) >= 2:
            baseline_v = voltage[baseline_indices]
            baseline_i = current[baseline_indices]
            
            # Linear fit to baseline region
            try:
                slope, intercept, _, _, _ = linregress(baseline_v, baseline_i)
                baseline_fit = slope * voltage + intercept
                return current - baseline_fit
            except Exception:
                return current
        else:
            return current
    
    def process_cv_file(self, file_path: Path, is_stm32: bool = True) -> Optional[Dict]:
        """Process a single CV file with peak detection"""
        try:
            # Read file
            with open(file_path, 'r') as f:
                first_line = f.readline().strip()
            
            skiprows = 1 if first_line.startswith('FileName:') else 0
            df = pd.read_csv(file_path, encoding='utf-8-sig', skiprows=skiprows)
            
            # Should have V and uA columns
            if 'V' not in df.columns or 'uA' not in df.columns:
                return None
            
            voltage = df['V'].values
            current = df['uA'].values
            
            # Remove NaN values
            mask = ~(np.isnan(voltage) | np.isnan(current))
            voltage = voltage[mask]
            current = current[mask]
            
            if len(voltage) < 20:
                return None
            
            # Apply baseline correction
            corrected_current = self.simple_baseline_correction(voltage, current)
            
            # Find peaks on corrected data
            peak_info = self.find_cv_peaks(voltage, corrected_current)
            
            # Calculate traditional metrics
            peak_height = np.max(corrected_current) - np.min(corrected_current)
            peak_area = abs(np.trapz(corrected_current, voltage))
            
            # Extract metadata
            if is_stm32:
                metadata = self.extract_stm32_metadata(str(file_path))
            else:
                metadata = self.extract_palmsens_metadata(str(file_path))
            
            if metadata['concentration'] is None or metadata['scan_rate'] is None:
                return None
            
            result = {
                **metadata,
                'peak_height': peak_height,
                'peak_area': peak_area,
                'oxidation_current': peak_info['oxidation_current'],
                'reduction_current': peak_info['reduction_current'],
                'peak_separation': peak_info['peak_separation'],
                'filepath': str(file_path),
                'filename': file_path.name
            }
            
            return result
            
        except Exception as e:
            logger.debug(f"Error processing {file_path.name}: {e}")
            return None
    
    def load_all_data(self):
        """Load and process all STM32 and Palmsens data"""
        logger.info("🔄 Loading data with enhanced peak detection...")
        
        # Load STM32 data
        stm32_dir = Path("Test_data/Stm32")
        stm32_files = list(stm32_dir.rglob("*.csv"))
        logger.info(f"📂 Found {len(stm32_files)} STM32 files")
        
        stm32_processed = 0
        for file_path in stm32_files[:50]:
            result = self.process_cv_file(file_path, is_stm32=True)
            if result:
                self.stm32_data.append(result)
                stm32_processed += 1
        
        logger.info(f"✅ Processed {stm32_processed} STM32 files")
        
        # Load Palmsens data strategically
        palmsens_dir = Path("Test_data/Palmsens")
        palmsens_files = list(palmsens_dir.rglob("*.csv"))
        logger.info(f"📂 Found {len(palmsens_files)} Palmsens files")
        
        # Strategic sampling
        from collections import defaultdict
        palmsens_by_condition = defaultdict(list)
        
        for file_path in palmsens_files:
            metadata = self.extract_palmsens_metadata(str(file_path))
            if metadata['concentration'] is not None and metadata['scan_rate'] is not None:
                key = (metadata['concentration'], metadata['scan_rate'])
                palmsens_by_condition[key].append(file_path)
        
        palmsens_processed = 0
        max_per_condition = 3
        for (conc, sr), files in palmsens_by_condition.items():
            sampled_files = files[:max_per_condition]
            for file_path in sampled_files:
                result = self.process_cv_file(file_path, is_stm32=False)
                if result:
                    self.palmsens_data.append(result)
                    palmsens_processed += 1
        
        logger.info(f"✅ Processed {palmsens_processed} Palmsens files")
        logger.info(f"📊 Total data points: {len(self.stm32_data) + len(self.palmsens_data)}")
    
    def compare_by_metrics(self):
        """Compare systems using multiple metrics"""
        logger.info("\n📊 Peak-Enhanced STM32 vs Palmsens Comparison")
        logger.info("=" * 55)
        
        # Get common scan rates
        stm32_scan_rates = set(d['scan_rate'] for d in self.stm32_data)
        palmsens_scan_rates = set(d['scan_rate'] for d in self.palmsens_data)
        common_scan_rates = sorted(stm32_scan_rates & palmsens_scan_rates)
        
        logger.info(f"🎯 Common scan rates: {common_scan_rates}")
        
        if not common_scan_rates:
            logger.warning("⚠️ No common scan rates found!")
            return
        
        # Create comprehensive plots
        fig, axes = plt.subplots(2, len(common_scan_rates), figsize=(6*len(common_scan_rates), 10))
        if len(common_scan_rates) == 1:
            axes = axes.reshape(-1, 1)
        
        comparison_results = {}
        
        for i, scan_rate in enumerate(common_scan_rates):
            # Filter data
            stm32_subset = [d for d in self.stm32_data if d['scan_rate'] == scan_rate]
            palmsens_subset = [d for d in self.palmsens_data if d['scan_rate'] == scan_rate]
            
            if len(stm32_subset) < 3 or len(palmsens_subset) < 3:
                continue
            
            # Extract data
            stm32_conc = np.array([d['concentration'] for d in stm32_subset])
            stm32_ox = np.array([d['oxidation_current'] for d in stm32_subset])
            stm32_height = np.array([d['peak_height'] for d in stm32_subset])
            
            palmsens_conc = np.array([d['concentration'] for d in palmsens_subset])
            palmsens_ox = np.array([d['oxidation_current'] for d in palmsens_subset])
            palmsens_height = np.array([d['peak_height'] for d in palmsens_subset])
            
            # Check concentration variety
            if len(np.unique(stm32_conc)) < 2 or len(np.unique(palmsens_conc)) < 2:
                continue
            
            # Top plot: Oxidation current
            ax1 = axes[0, i]
            
            # Linear regression on oxidation current
            stm32_slope_ox, stm32_int_ox, stm32_r_ox, _, _ = linregress(stm32_conc, stm32_ox)
            palmsens_slope_ox, palmsens_int_ox, palmsens_r_ox, _, _ = linregress(palmsens_conc, palmsens_ox)
            
            stm32_r2_ox = stm32_r_ox ** 2
            palmsens_r2_ox = palmsens_r_ox ** 2
            
            # Plot oxidation current
            ax1.scatter(stm32_conc, stm32_ox, alpha=0.7, s=60, color='blue',
                       label=f'STM32 (R²={stm32_r2_ox:.3f})', marker='o')
            ax1.scatter(palmsens_conc, palmsens_ox, alpha=0.7, s=60, color='red',
                       label=f'Palmsens (R²={palmsens_r2_ox:.3f})', marker='s')
            
            # Fit lines
            all_conc = np.concatenate([stm32_conc, palmsens_conc])
            conc_range = np.linspace(min(all_conc), max(all_conc), 100)
            
            stm32_fit_ox = stm32_slope_ox * conc_range + stm32_int_ox
            palmsens_fit_ox = palmsens_slope_ox * conc_range + palmsens_int_ox
            
            ax1.plot(conc_range, stm32_fit_ox, 'b--', alpha=0.8, linewidth=2)
            ax1.plot(conc_range, palmsens_fit_ox, 'r--', alpha=0.8, linewidth=2)
            
            ax1.set_xlabel('Concentration (mM)')
            ax1.set_ylabel('Oxidation Current (µA)')
            ax1.set_title(f'{scan_rate} mV/s - Oxidation Current')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Bottom plot: Peak height (traditional)
            ax2 = axes[1, i]
            
            # Linear regression on peak height
            stm32_slope_h, stm32_int_h, stm32_r_h, _, _ = linregress(stm32_conc, stm32_height)
            palmsens_slope_h, palmsens_int_h, palmsens_r_h, _, _ = linregress(palmsens_conc, palmsens_height)
            
            stm32_r2_h = stm32_r_h ** 2
            palmsens_r2_h = palmsens_r_h ** 2
            
            # Plot peak height
            ax2.scatter(stm32_conc, stm32_height, alpha=0.7, s=60, color='darkblue',
                       label=f'STM32 (R²={stm32_r2_h:.3f})', marker='o')
            ax2.scatter(palmsens_conc, palmsens_height, alpha=0.7, s=60, color='darkred',
                       label=f'Palmsens (R²={palmsens_r2_h:.3f})', marker='s')
            
            stm32_fit_h = stm32_slope_h * conc_range + stm32_int_h
            palmsens_fit_h = palmsens_slope_h * conc_range + palmsens_int_h
            
            ax2.plot(conc_range, stm32_fit_h, 'b--', alpha=0.8, linewidth=2)
            ax2.plot(conc_range, palmsens_fit_h, 'r--', alpha=0.8, linewidth=2)
            
            ax2.set_xlabel('Concentration (mM)')
            ax2.set_ylabel('Peak Height (µA)')
            ax2.set_title(f'{scan_rate} mV/s - Peak Height')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # Store results
            comparison_results[scan_rate] = {
                'stm32': {
                    'n_samples': len(stm32_subset),
                    'ox_slope': stm32_slope_ox,
                    'ox_r2': stm32_r2_ox,
                    'height_slope': stm32_slope_h,
                    'height_r2': stm32_r2_h,
                    'conc_range': [min(stm32_conc), max(stm32_conc)]
                },
                'palmsens': {
                    'n_samples': len(palmsens_subset),
                    'ox_slope': palmsens_slope_ox,
                    'ox_r2': palmsens_r2_ox,
                    'height_slope': palmsens_slope_h,
                    'height_r2': palmsens_r2_h,
                    'conc_range': [min(palmsens_conc), max(palmsens_conc)]
                },
                'ox_slope_ratio': palmsens_slope_ox / stm32_slope_ox if stm32_slope_ox != 0 else None,
                'height_slope_ratio': palmsens_slope_h / stm32_slope_h if stm32_slope_h != 0 else None
            }
            
            logger.info(f"   {scan_rate} mV/s:")
            logger.info(f"      STM32: Ox R²={stm32_r2_ox:.3f}, Height R²={stm32_r2_h:.3f}")
            logger.info(f"      Palmsens: Ox R²={palmsens_r2_ox:.3f}, Height R²={palmsens_r2_h:.3f}")
        
        plt.tight_layout()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_filename = f"peak_enhanced_comparison_{timestamp}.png"
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        logger.info(f"📊 Peak-enhanced plots saved: {plot_filename}")
        
        # Save report
        report_filename = f"peak_enhanced_report_{timestamp}.json"
        with open(report_filename, 'w') as f:
            json.dump(comparison_results, f, indent=2)
        logger.info(f"📄 Peak-enhanced report saved: {report_filename}")
        
        return comparison_results
    
    def run_comparison(self):
        """Main method to run peak-enhanced comparison"""
        logger.info("🚀 Starting Peak-Enhanced CV Comparison")
        logger.info("=" * 50)
        logger.info("✨ Features: Peak detection + Improved baseline correction")
        
        # Load all data
        self.load_all_data()
        
        if not self.stm32_data or not self.palmsens_data:
            logger.error("❌ Insufficient data for comparison!")
            return
        
        # Enhanced comparison
        comparison_results = self.compare_by_metrics()
        
        logger.info("\n✅ Peak-enhanced comparison completed!")
        logger.info("   - Specific oxidation current analysis")
        logger.info("   - Improved baseline correction")
        logger.info("   - Dual metric validation")
        
        return comparison_results

def main():
    """Main execution"""
    comparison = PeakEnhancedComparison()
    comparison.run_comparison()

if __name__ == "__main__":
    main()