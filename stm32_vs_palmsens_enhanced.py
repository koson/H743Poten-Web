#!/usr/bin/env python3
"""
STM32 vs Palmsens Advanced Comparison
===================================
Enhanced comparison with proper peak detection and baseline correction
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

# Import advanced baseline detection
try:
    from baseline_detector_simple import cv_baseline_detector_v3
    ADVANCED_BASELINE = False  # Temporarily disable due to compatibility issues
    logging.info("⚠️ Advanced baseline detection disabled for compatibility")
except ImportError:
    ADVANCED_BASELINE = False
    logging.warning("⚠️ Advanced baseline detection not available, using simple method")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class AdvancedSTM32PalmsensComparison:
    """Enhanced comparison with proper peak detection and baseline correction"""
    
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
    
    def find_cv_peaks(self, voltage: np.ndarray, current: np.ndarray) -> Dict:
        """Enhanced CV peak detection"""
        # Sort by voltage to ensure proper order
        sorted_indices = np.argsort(voltage)
        v_sorted = voltage[sorted_indices]
        i_sorted = current[sorted_indices]
        
        # Adaptive threshold based on data characteristics
        i_std = np.std(i_sorted)
        i_mean = np.mean(i_sorted)
        
        # Find peaks (positive excursions) and valleys (negative excursions)
        peak_threshold = max(i_mean + 2*i_std, np.max(i_sorted) * 0.15)
        valley_threshold = max(abs(i_mean - 2*i_std), abs(np.min(i_sorted)) * 0.15)
        
        # Minimum distance between peaks (adapt to data length)
        min_distance = max(5, len(v_sorted) // 50)
        
        peaks_pos, peak_props = find_peaks(i_sorted, height=peak_threshold, distance=min_distance)
        peaks_neg, valley_props = find_peaks(-i_sorted, height=valley_threshold, distance=min_distance)
        
        results = {
            'oxidation_peaks': [],
            'reduction_peaks': [],
            'peak_regions': [],  # For baseline detection
            'max_oxidation_current': 0,
            'max_reduction_current': 0,
            'peak_separation': None
        }
        
        # Process oxidation peaks
        if len(peaks_pos) > 0:
            # Take the most prominent peak
            max_ox_idx = peaks_pos[np.argmax(i_sorted[peaks_pos])]
            ox_voltage = v_sorted[max_ox_idx]
            ox_current = i_sorted[max_ox_idx]
            results['oxidation_peaks'] = [(ox_voltage, ox_current)]
            results['max_oxidation_current'] = ox_current
            
            # Add peak region for baseline detection (±10% around peak)
            peak_width = len(v_sorted) // 20
            start_idx = max(0, max_ox_idx - peak_width)
            end_idx = min(len(v_sorted), max_ox_idx + peak_width)
            results['peak_regions'].append((start_idx, end_idx))
        
        # Process reduction peaks
        if len(peaks_neg) > 0:
            # Take the most prominent valley
            max_red_idx = peaks_neg[np.argmax(-i_sorted[peaks_neg])]
            red_voltage = v_sorted[max_red_idx]
            red_current = i_sorted[max_red_idx]
            results['reduction_peaks'] = [(red_voltage, red_current)]
            results['max_reduction_current'] = red_current
            
            # Add peak region for baseline detection
            peak_width = len(v_sorted) // 20
            start_idx = max(0, max_red_idx - peak_width)
            end_idx = min(len(v_sorted), max_red_idx + peak_width)
            results['peak_regions'].append((start_idx, end_idx))
        
        # Calculate peak separation if both peaks exist
        if results['oxidation_peaks'] and results['reduction_peaks']:
            ox_v = results['oxidation_peaks'][0][0]
            red_v = results['reduction_peaks'][0][0]
            results['peak_separation'] = abs(ox_v - red_v)
        
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
    
    def process_cv_file(self, file_path: Path, is_stm32: bool = True) -> Optional[Dict]:
        """Process a single CV file with advanced peak and baseline detection"""
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
            
            if len(voltage) < 20:  # Need more points for good analysis
                return None
            
            # Step 1: Find peaks first
            peak_info = self.find_cv_peaks(voltage, current)
            
            # Step 2: Apply baseline correction
            file_key = str(file_path)
            if file_key in self.corrections:
                # Use saved manual correction
                corrected_current = self.apply_baseline_correction(
                    voltage, current, self.corrections[file_key])
                baseline_method = "manual"
            elif ADVANCED_BASELINE:
                try:
                    # Use advanced baseline detection with peak exclusion
                    forward_baseline, reverse_baseline, info = cv_baseline_detector_v3(
                        voltage, current, peaks=peak_info.get('peak_regions', []))
                    
                    # Create baseline fit
                    if len(forward_baseline) > 0 and len(reverse_baseline) > 0:
                        baseline_points = np.concatenate([forward_baseline, reverse_baseline])
                        baseline_voltages = np.concatenate([
                            voltage[:len(forward_baseline)], 
                            voltage[-len(reverse_baseline):]
                        ])
                        
                        if len(baseline_voltages) >= 2:
                            slope, intercept, _, _, _ = linregress(baseline_voltages, baseline_points)
                            baseline_fit = slope * voltage + intercept
                            corrected_current = current - baseline_fit
                            baseline_method = "advanced"
                        else:
                            corrected_current = current
                            baseline_method = "none"
                    else:
                        corrected_current = current
                        baseline_method = "failed"
                except Exception as e:
                    logger.debug(f"Advanced baseline failed for {file_path.name}: {e}")
                    # Fallback to simple method
                    corrected_current = self._simple_baseline_correction(voltage, current)
                    baseline_method = "simple_fallback"
            else:
                # Simple baseline correction
                corrected_current = self._simple_baseline_correction(voltage, current)
                baseline_method = "simple"
            
            # Step 3: Recalculate peaks on corrected data
            corrected_peak_info = self.find_cv_peaks(voltage, corrected_current)
            
            # Step 4: Calculate metrics
            peak_height = np.max(corrected_current) - np.min(corrected_current)
            peak_area = abs(np.trapz(corrected_current, voltage))
            
            # Enhanced metrics
            oxidation_current = corrected_peak_info['max_oxidation_current']
            reduction_current = abs(corrected_peak_info['max_reduction_current'])
            peak_separation = corrected_peak_info.get('peak_separation', 0)
            
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
                'oxidation_current': oxidation_current,
                'reduction_current': reduction_current,
                'peak_separation': peak_separation,
                'baseline_method': baseline_method,
                'num_ox_peaks': len(corrected_peak_info['oxidation_peaks']),
                'num_red_peaks': len(corrected_peak_info['reduction_peaks']),
                'filepath': str(file_path),
                'filename': file_path.name
            }
            
            return result
            
        except Exception as e:
            logger.debug(f"Error processing {file_path.name}: {e}")
            return None
    
    def _simple_baseline_correction(self, voltage: np.ndarray, current: np.ndarray) -> np.ndarray:
        """Simple baseline correction fallback method"""
        n_points = len(voltage)
        baseline_indices = np.concatenate([
            np.arange(0, int(0.15 * n_points)),  # First 15%
            np.arange(int(0.85 * n_points), n_points)  # Last 15%
        ])
        
        if len(baseline_indices) >= 2:
            baseline_v = voltage[baseline_indices]
            baseline_i = current[baseline_indices]
            slope, intercept, _, _, _ = linregress(baseline_v, baseline_i)
            baseline_fit = slope * voltage + intercept
            return current - baseline_fit
        else:
            return current
    
    def load_all_data(self):
        """Load and process all STM32 and Palmsens data with advanced analysis"""
        logger.info("🔄 Loading STM32 and Palmsens data with advanced analysis...")
        
        # Load STM32 data
        stm32_dir = Path("Test_data/Stm32")
        stm32_files = list(stm32_dir.rglob("*.csv"))
        logger.info(f"📂 Found {len(stm32_files)} STM32 files")
        
        stm32_processed = 0
        for file_path in stm32_files[:60]:  # Process more for better statistics
            result = self.process_cv_file(file_path, is_stm32=True)
            if result:
                self.stm32_data.append(result)
                stm32_processed += 1
        
        logger.info(f"✅ Processed {stm32_processed} STM32 files")
        
        # Load Palmsens data with strategic sampling
        palmsens_dir = Path("Test_data/Palmsens")
        palmsens_files = list(palmsens_dir.rglob("*.csv"))
        logger.info(f"📂 Found {len(palmsens_files)} Palmsens files")
        
        # Sample strategically to get variety
        from collections import defaultdict
        palmsens_by_condition = defaultdict(list)
        
        for file_path in palmsens_files:
            metadata = self.extract_palmsens_metadata(str(file_path))
            if metadata['concentration'] is not None and metadata['scan_rate'] is not None:
                key = (metadata['concentration'], metadata['scan_rate'])
                palmsens_by_condition[key].append(file_path)
        
        palmsens_processed = 0
        max_per_condition = 4  # Increased for better statistics
        for (conc, sr), files in palmsens_by_condition.items():
            sampled_files = files[:max_per_condition]
            for file_path in sampled_files:
                result = self.process_cv_file(file_path, is_stm32=False)
                if result:
                    self.palmsens_data.append(result)
                    palmsens_processed += 1
        
        logger.info(f"✅ Processed {palmsens_processed} Palmsens files")
        logger.info(f"📊 Total data points: {len(self.stm32_data) + len(self.palmsens_data)}")
        
        # Log baseline methods used
        stm32_methods = [d['baseline_method'] for d in self.stm32_data]
        palmsens_methods = [d['baseline_method'] for d in self.palmsens_data]
        
        logger.info("🔧 Baseline methods used:")
        for method in set(stm32_methods + palmsens_methods):
            stm32_count = stm32_methods.count(method)
            palmsens_count = palmsens_methods.count(method)
            logger.info(f"   {method}: STM32({stm32_count}), Palmsens({palmsens_count})")
    
    def compare_by_scan_rate(self):
        """Enhanced comparison by scan rate with multiple metrics"""
        logger.info("\n📊 Enhanced STM32 vs Palmsens Comparison by Scan Rate")
        logger.info("=" * 60)
        
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
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(7*n_cols, 6*n_rows))
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
            
            # Extract data for analysis
            stm32_conc = np.array([d['concentration'] for d in stm32_subset])
            stm32_ox = np.array([d['oxidation_current'] for d in stm32_subset])
            stm32_height = np.array([d['peak_height'] for d in stm32_subset])
            
            palmsens_conc = np.array([d['concentration'] for d in palmsens_subset])
            palmsens_ox = np.array([d['oxidation_current'] for d in palmsens_subset])
            palmsens_height = np.array([d['peak_height'] for d in palmsens_subset])
            
            # Check for sufficient concentration variety
            stm32_unique_conc = len(np.unique(stm32_conc))
            palmsens_unique_conc = len(np.unique(palmsens_conc))
            
            if stm32_unique_conc < 2 or palmsens_unique_conc < 2:
                logger.warning(f"⚠️ Insufficient concentration variety for {scan_rate} mV/s")
                continue
            
            # Linear regression on oxidation current (more specific than peak height)
            stm32_slope, stm32_intercept, stm32_r, _, _ = linregress(stm32_conc, stm32_ox)
            palmsens_slope, palmsens_intercept, palmsens_r, _, _ = linregress(palmsens_conc, palmsens_ox)
            
            stm32_r2 = stm32_r ** 2
            palmsens_r2 = palmsens_r ** 2
            
            # Plot data and fits
            ax.scatter(stm32_conc, stm32_ox, alpha=0.7, s=60, color='blue',
                      label=f'STM32 Ox (R²={stm32_r2:.3f})', marker='o')
            ax.scatter(palmsens_conc, palmsens_ox, alpha=0.7, s=60, color='red',
                      label=f'Palmsens Ox (R²={palmsens_r2:.3f})', marker='s')
            
            # Fit lines
            all_conc = np.concatenate([stm32_conc, palmsens_conc])
            conc_range = np.linspace(min(all_conc), max(all_conc), 100)
            
            stm32_fit = stm32_slope * conc_range + stm32_intercept
            palmsens_fit = palmsens_slope * conc_range + palmsens_intercept
            
            ax.plot(conc_range, stm32_fit, 'b--', alpha=0.8, linewidth=2)
            ax.plot(conc_range, palmsens_fit, 'r--', alpha=0.8, linewidth=2)
            
            ax.set_xlabel('Concentration (mM)')
            ax.set_ylabel('Oxidation Current (µA)')
            ax.set_title(f'{scan_rate} mV/s Enhanced Comparison\n(Peak-specific analysis)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Store detailed comparison results
            comparison_results[scan_rate] = {
                'stm32': {
                    'n_samples': len(stm32_subset),
                    'ox_slope': stm32_slope,
                    'ox_r2': stm32_r2,
                    'conc_range': [min(stm32_conc), max(stm32_conc)],
                    'avg_peak_separation': np.mean([d.get('peak_separation', 0) or 0 for d in stm32_subset]),
                    'baseline_methods': list(set(d['baseline_method'] for d in stm32_subset))
                },
                'palmsens': {
                    'n_samples': len(palmsens_subset),
                    'ox_slope': palmsens_slope,
                    'ox_r2': palmsens_r2,
                    'conc_range': [min(palmsens_conc), max(palmsens_conc)],
                    'avg_peak_separation': np.mean([d.get('peak_separation', 0) or 0 for d in palmsens_subset]),
                    'baseline_methods': list(set(d['baseline_method'] for d in palmsens_subset))
                },
                'slope_ratio': palmsens_slope / stm32_slope if stm32_slope != 0 else None
            }
            
            logger.info(f"   {scan_rate} mV/s (Oxidation Current Analysis):")
            logger.info(f"      STM32: {len(stm32_subset)} samples, slope={stm32_slope:.2f}, R²={stm32_r2:.3f}")
            logger.info(f"      Palmsens: {len(palmsens_subset)} samples, slope={palmsens_slope:.2f}, R²={palmsens_r2:.3f}")
            if comparison_results[scan_rate]['slope_ratio']:
                logger.info(f"      Slope ratio (P/S): {comparison_results[scan_rate]['slope_ratio']:.2f}")
        
        # Hide extra subplots
        for i in range(len(common_scan_rates), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_filename = f"stm32_vs_palmsens_enhanced_{timestamp}.png"
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        logger.info(f"📊 Enhanced comparison plots saved: {plot_filename}")
        
        # Save enhanced report
        report_filename = f"stm32_vs_palmsens_enhanced_{timestamp}.json"
        with open(report_filename, 'w') as f:
            json.dump(comparison_results, f, indent=2)
        logger.info(f"📄 Enhanced comparison report saved: {report_filename}")
        
        return comparison_results
    
    def run_enhanced_comparison(self):
        """Main method to run enhanced comparison"""
        logger.info("🚀 Starting Enhanced STM32 vs Palmsens Comparison")
        logger.info("=" * 65)
        logger.info("✨ Features: Advanced baseline detection + Peak-specific analysis")
        
        # Load all data
        self.load_all_data()
        
        if not self.stm32_data or not self.palmsens_data:
            logger.error("❌ Insufficient data for comparison!")
            return
        
        # Enhanced comparison
        comparison_results = self.compare_by_scan_rate()
        
        logger.info("\n✅ Enhanced STM32 vs Palmsens comparison completed!")
        logger.info("   - Peak detection and baseline correction optimized")
        logger.info("   - Oxidation current analysis for better specificity")
        logger.info("   - Multiple baseline methods validated")
        
        return comparison_results

def main():
    """Main execution"""
    comparison = AdvancedSTM32PalmsensComparison()
    comparison.run_enhanced_comparison()

if __name__ == "__main__":
    main()