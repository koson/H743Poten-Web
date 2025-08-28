#!/usr/bin/env python3
"""
CV Calibration Comparison: Palmsens vs STM32 (Simplified Version)
Compare peak height and peak area calibration curves between two systems
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.integrate import trapz
from scipy.signal import find_peaks
from scipy.stats import linregress
import os
import glob
import re
import logging
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class CVCalibrationAnalyzer:
    """CV Peak Analysis and Calibration Comparison (Simplified)"""
    
    def __init__(self):
        self.results = {
            'palmsens': {'concentrations': [], 'peak_heights': [], 'peak_areas': [], 'scan_rates': [], 'files': []},
            'stm32': {'concentrations': [], 'peak_heights': [], 'peak_areas': [], 'scan_rates': [], 'files': []}
        }
        
    def extract_scan_rate_from_filename(self, filename: str) -> Optional[float]:
        """
        Extract scan rate from filename patterns like:
        - ...100mVpS... -> 100
        - ...20mVpS... -> 20
        - ...400mVpS... -> 400
        """
        patterns = [
            r'(\d+)mVpS',           # 100mVpS, 20mVpS, 400mVpS
            r'(\d+)mV[/_]s',        # Alternative formats
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return float(match.group(1))
        
        logger.warning(f"Could not extract scan rate from: {filename}")
        return None
    
    def extract_concentration_from_filename(self, filename: str) -> Optional[float]:
        """
        Extract concentration from filename patterns like:
        - Palmsens_0.5mM_... -> 0.5
        - Pipot_Ferro_1_0mM_... -> 1.0
        - ...2_5mM_... -> 2.5
        """
        patterns = [
            r'(\d+\.?\d*)mM',           # 0.5mM, 1.0mM, 2.5mM
            r'(\d+)_(\d+)mM',           # 1_0mM, 2_5mM  
            r'Ferro_(\d+\.?\d*)_',      # Ferro_0.5_, Ferro_1.0_
            r'Ferro_(\d+)_(\d+)_'       # Ferro_1_0_, Ferro_2_5_
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                if len(match.groups()) == 1:
                    return float(match.group(1))
                else:
                    # Handle formats like 1_0 -> 1.0
                    return float(f"{match.group(1)}.{match.group(2)}")
        
        logger.warning(f"Could not extract concentration from: {filename}")
        return None
    
    def load_cv_data(self, filepath: str) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Load CV data from different file formats"""
        try:
            df = None
            try:
                df = pd.read_csv(filepath)
                if len(df.columns) == 1 or df.columns[0].startswith('FileName:'):
                    df = pd.read_csv(filepath, skiprows=1)
            except:
                df = pd.read_csv(filepath, skiprows=1)
            
            # Handle different column formats
            if 'WE(1).Potential (V)' in df.columns and 'WE(1).Current (A)' in df.columns:
                voltage = df['WE(1).Potential (V)'].values
                current = df['WE(1).Current (A)'].values
                current_unit = 'A'
            elif 'Voltage (V)' in df.columns and 'Current (A)' in df.columns:
                voltage = df['Voltage (V)'].values
                current = df['Current (A)'].values
                current_unit = 'A'
            elif 'V' in df.columns and 'uA' in df.columns:
                voltage = df['V'].values
                current = df['uA'].values
                current_unit = 'uA'
            else:
                logger.error(f"Unknown column format in {filepath}: {list(df.columns)}")
                return None
            
            # Convert current to consistent units (µA)
            if current_unit == 'A':
                current = current * 1e6  # Convert A to µA
                
            return voltage, current
            
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
            return None
    
    def find_cv_peaks(self, voltage: np.ndarray, current: np.ndarray) -> Dict:
        """Find oxidation and reduction peaks in CV data"""
        # Sort by voltage to ensure proper order
        sorted_indices = np.argsort(voltage)
        v_sorted = voltage[sorted_indices]
        i_sorted = current[sorted_indices]
        
        # Find peaks (positive current) and valleys (negative current)
        peak_threshold = np.max(i_sorted) * 0.1 if np.max(i_sorted) > 0 else 0
        valley_threshold = -np.min(i_sorted) * 0.1 if np.min(i_sorted) < 0 else 0
        
        peaks_pos, _ = find_peaks(i_sorted, height=peak_threshold, distance=10)
        peaks_neg, _ = find_peaks(-i_sorted, height=valley_threshold, distance=10)
        
        results = {
            'oxidation_peaks': [],
            'reduction_peaks': [],
            'peak_separation': None,
            'max_oxidation_current': 0,
            'max_reduction_current': 0
        }
        
        if len(peaks_pos) > 0:
            max_ox_idx = peaks_pos[np.argmax(i_sorted[peaks_pos])]
            results['oxidation_peaks'] = [(v_sorted[max_ox_idx], i_sorted[max_ox_idx])]
            results['max_oxidation_current'] = i_sorted[max_ox_idx]
        
        if len(peaks_neg) > 0:
            max_red_idx = peaks_neg[np.argmax(-i_sorted[peaks_neg])]
            results['reduction_peaks'] = [(v_sorted[max_red_idx], i_sorted[max_red_idx])]
            results['max_reduction_current'] = i_sorted[max_red_idx]
        
        # Calculate peak separation if both peaks exist
        if results['oxidation_peaks'] and results['reduction_peaks']:
            ox_v = results['oxidation_peaks'][0][0]
            red_v = results['reduction_peaks'][0][0]
            results['peak_separation'] = abs(ox_v - red_v)
        
        return results
    
    def calculate_peak_area(self, voltage: np.ndarray, current: np.ndarray) -> Dict:
        """Calculate peak areas using integration"""
        # Sort data
        sorted_indices = np.argsort(voltage)
        v_sorted = voltage[sorted_indices]
        i_sorted = current[sorted_indices]
        
        # Method 1: Total absolute area
        total_area = abs(trapz(i_sorted, v_sorted))
        
        # Method 2: Separate positive and negative areas
        positive_mask = i_sorted > 0
        negative_mask = i_sorted < 0
        
        pos_area = trapz(i_sorted[positive_mask], v_sorted[positive_mask]) if np.any(positive_mask) else 0
        neg_area = abs(trapz(i_sorted[negative_mask], v_sorted[negative_mask])) if np.any(negative_mask) else 0
        
        return {
            'total_area': total_area,
            'oxidation_area': pos_area,
            'reduction_area': neg_area,
            'combined_area': pos_area + neg_area
        }
    
    def process_file(self, filepath: str) -> Optional[Dict]:
        """Process a single CV file and extract features"""
        concentration = self.extract_concentration_from_filename(os.path.basename(filepath))
        if concentration is None:
            return None
        
        scan_rate = self.extract_scan_rate_from_filename(os.path.basename(filepath))
        if scan_rate is None:
            return None
        
        cv_data = self.load_cv_data(filepath)
        if cv_data is None:
            return None
        
        voltage, current = cv_data
        
        # Find peaks
        peak_info = self.find_cv_peaks(voltage, current)
        
        # Calculate areas
        area_info = self.calculate_peak_area(voltage, current)
        
        # Determine peak height (use max absolute current)
        peak_height = max(abs(peak_info['max_oxidation_current']), 
                         abs(peak_info['max_reduction_current']))
        
        return {
            'filename': os.path.basename(filepath),
            'concentration': concentration,
            'scan_rate': scan_rate,
            'peak_height': peak_height,
            'peak_area': area_info['combined_area'],
            'oxidation_area': area_info['oxidation_area'],
            'reduction_area': area_info['reduction_area'],
            'peak_separation': peak_info['peak_separation']
        }
    
    def scan_data_directories(self):
        """Scan for CV data files and categorize by system"""
        logger.info("🔍 Scanning for CV data files...")
        
        patterns = {
            'palmsens': 'Test_data/Palmsens/**/*.csv',
            'stm32': 'Test_data/Stm32/**/*.csv'
        }
        
        total_processed = 0
        
        for system, pattern in patterns.items():
            files = glob.glob(pattern, recursive=True)
            logger.info(f"📁 Found {len(files)} {system} files")
            
            processed_count = 0
            for filepath in files:
                result = self.process_file(filepath)
                if result:
                    self.results[system]['concentrations'].append(result['concentration'])
                    self.results[system]['peak_heights'].append(result['peak_height'])
                    self.results[system]['peak_areas'].append(result['peak_area'])
                    self.results[system]['scan_rates'].append(result['scan_rate'])
                    self.results[system]['files'].append(result['filename'])
                    processed_count += 1
                    
                    logger.info(f"✅ {system}: {result['filename']} - {result['concentration']}mM, "
                              f"SR={result['scan_rate']}mV/s, height={result['peak_height']:.2f}µA, area={result['peak_area']:.2f}")
            
            logger.info(f"📊 {system}: {processed_count}/{len(files)} files processed successfully")
            total_processed += processed_count
        
        logger.info(f"🎯 Total files processed: {total_processed}")
    
    def create_comparison_plots(self):
        """Create comprehensive comparison plots separated by scan rate"""
        # Get unique scan rates
        all_scan_rates = set()
        for system in ['palmsens', 'stm32']:
            if len(self.results[system]['scan_rates']) > 0:
                all_scan_rates.update(self.results[system]['scan_rates'])
        
        scan_rates = sorted(list(all_scan_rates))
        logger.info(f"📊 Found scan rates: {scan_rates} mV/s")
        
        # Create figure with subplots
        n_scan_rates = len(scan_rates)
        fig = plt.figure(figsize=(20, 6 * n_scan_rates))
        
        systems = ['palmsens', 'stm32']
        colors = ['#E74C3C', '#3498DB']  # Red for Palmsens, Blue for STM32
        markers = ['o', 's']  # Circle for Palmsens, Square for STM32
        
        plot_idx = 1
        r2_summary = {}
        
        for scan_rate in scan_rates:
            # Filter data for this scan rate
            sr_data = {system: {'conc': [], 'height': [], 'area': []} for system in systems}
            
            for system in systems:
                if len(self.results[system]['scan_rates']) > 0:
                    sr_indices = [i for i, sr in enumerate(self.results[system]['scan_rates']) if sr == scan_rate]
                    
                    sr_data[system]['conc'] = [self.results[system]['concentrations'][i] for i in sr_indices]
                    sr_data[system]['height'] = [self.results[system]['peak_heights'][i] for i in sr_indices]
                    sr_data[system]['area'] = [self.results[system]['peak_areas'][i] for i in sr_indices]
            
            r2_summary[scan_rate] = {}
            
            # Plot 1: Peak Height vs Concentration for this scan rate
            plt.subplot(n_scan_rates, 3, plot_idx)
            
            for i, system in enumerate(systems):
                if len(sr_data[system]['conc']) > 0:
                    x = np.array(sr_data[system]['conc'])
                    y = np.array(sr_data[system]['height'])
                    
                    plt.scatter(x, y, c=colors[i], marker=markers[i], s=80, alpha=0.7, 
                               edgecolors='black', linewidth=0.5, label=f'{system.title()} (n={len(x)})')
                    
                    # Linear fit if we have enough points
                    if len(x) > 1:
                        slope, intercept, r_value, p_value, std_err = linregress(x, y)
                        x_fit = np.linspace(x.min(), x.max(), 100)
                        y_fit = slope * x_fit + intercept
                        plt.plot(x_fit, y_fit, color=colors[i], linestyle='--', alpha=0.8, linewidth=2)
                        
                        r2_summary[scan_rate][f'{system}_height_r2'] = r_value**2
                        
                        # Add R² annotation
                        plt.text(0.05, 0.95 - i*0.08, f'{system.title()}: R²={r_value**2:.3f}', 
                                transform=plt.gca().transAxes, color=colors[i], fontweight='bold',
                                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
            
            plt.xlabel('Concentration (mM)', fontsize=12)
            plt.ylabel('Peak Height (µA)', fontsize=12)
            plt.title(f'Peak Height vs Concentration\nScan Rate: {scan_rate} mV/s', fontsize=14, fontweight='bold')
            plt.legend(fontsize=10)
            plt.grid(True, alpha=0.3)
            
            # Plot 2: Peak Area vs Concentration for this scan rate
            plt.subplot(n_scan_rates, 3, plot_idx + 1)
            
            for i, system in enumerate(systems):
                if len(sr_data[system]['conc']) > 0:
                    x = np.array(sr_data[system]['conc'])
                    y = np.array(sr_data[system]['area'])
                    
                    plt.scatter(x, y, c=colors[i], marker=markers[i], s=80, alpha=0.7,
                               edgecolors='black', linewidth=0.5, label=f'{system.title()} (n={len(x)})')
                    
                    if len(x) > 1:
                        slope, intercept, r_value, p_value, std_err = linregress(x, y)
                        x_fit = np.linspace(x.min(), x.max(), 100)
                        y_fit = slope * x_fit + intercept
                        plt.plot(x_fit, y_fit, color=colors[i], linestyle='--', alpha=0.8, linewidth=2)
                        
                        r2_summary[scan_rate][f'{system}_area_r2'] = r_value**2
                        
                        plt.text(0.05, 0.95 - i*0.08, f'{system.title()}: R²={r_value**2:.3f}', 
                                transform=plt.gca().transAxes, color=colors[i], fontweight='bold',
                                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
            
            plt.xlabel('Concentration (mM)', fontsize=12)
            plt.ylabel('Peak Area (µA·V)', fontsize=12)
            plt.title(f'Peak Area vs Concentration\nScan Rate: {scan_rate} mV/s', fontsize=14, fontweight='bold')
            plt.legend(fontsize=10)
            plt.grid(True, alpha=0.3)
            
            # Plot 3: Direct System Comparison for this scan rate
            plt.subplot(n_scan_rates, 3, plot_idx + 2)
            
            if (len(sr_data['palmsens']['conc']) > 0 and len(sr_data['stm32']['conc']) > 0):
                # Find common concentrations for this scan rate
                palm_conc = np.array(sr_data['palmsens']['conc'])
                stm32_conc = np.array(sr_data['stm32']['conc'])
                common_conc = np.intersect1d(palm_conc, stm32_conc)
                
                if len(common_conc) > 0:
                    palm_heights = []
                    stm32_heights = []
                    
                    for conc in common_conc:
                        palm_idx = np.where(palm_conc == conc)[0]
                        stm32_idx = np.where(stm32_conc == conc)[0]
                        
                        if len(palm_idx) > 0 and len(stm32_idx) > 0:
                            palm_heights.append(np.mean([sr_data['palmsens']['height'][i] for i in palm_idx]))
                            stm32_heights.append(np.mean([sr_data['stm32']['height'][i] for i in stm32_idx]))
                    
                    if len(palm_heights) > 1:
                        plt.scatter(palm_heights, stm32_heights, c='purple', s=100, alpha=0.7, 
                                   edgecolors='black', linewidth=1, marker='^')
                        
                        # Linear fit
                        slope, intercept, r_value, p_value, std_err = linregress(palm_heights, stm32_heights)
                        x_fit = np.linspace(min(palm_heights), max(palm_heights), 100)
                        y_fit = slope * x_fit + intercept
                        plt.plot(x_fit, y_fit, 'purple', linestyle='--', alpha=0.8, linewidth=2)
                        
                        r2_summary[scan_rate]['correlation_r2'] = r_value**2
                        
                        # Unity line (ideal correlation)
                        min_val = min(min(palm_heights), min(stm32_heights))
                        max_val = max(max(palm_heights), max(stm32_heights))
                        plt.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, 
                                linewidth=1, label='Perfect correlation')
                        
                        plt.text(0.05, 0.95, f'R²={r_value**2:.3f}', transform=plt.gca().transAxes, 
                                fontweight='bold', fontsize=12,
                                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.8))
            
            plt.xlabel('Palmsens Peak Height (µA)', fontsize=12)
            plt.ylabel('STM32 Peak Height (µA)', fontsize=12)
            plt.title(f'System Correlation\nScan Rate: {scan_rate} mV/s', fontsize=14, fontweight='bold')
            plt.legend(fontsize=10)
            plt.grid(True, alpha=0.3)
            
            plot_idx += 3
        
        plt.tight_layout(pad=3.0)
        
        # Save plot
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cv_calibration_by_scanrate_{timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        logger.info(f"💾 Saved scan rate comparison plot: {filename}")
        
        plt.show()
        
        # Create summary R² plot
        self.create_r2_summary_plot(r2_summary, timestamp)
        
        return filename
    
    def create_r2_summary_plot(self, r2_summary: Dict, timestamp: str):
        """Create summary plot of R² values across scan rates"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        scan_rates = sorted(r2_summary.keys())
        colors = ['#E74C3C', '#3498DB', '#9B59B6']  # Red, Blue, Purple
        
        # Plot 1: Peak Height R² vs Scan Rate
        palm_height_r2 = [r2_summary[sr].get('palmsens_height_r2', 0) for sr in scan_rates]
        stm32_height_r2 = [r2_summary[sr].get('stm32_height_r2', 0) for sr in scan_rates]
        
        ax1.plot(scan_rates, palm_height_r2, 'o-', color=colors[0], linewidth=2, markersize=8, 
                label='Palmsens Height', markeredgecolor='black')
        ax1.plot(scan_rates, stm32_height_r2, 's-', color=colors[1], linewidth=2, markersize=8,
                label='STM32 Height', markeredgecolor='black')
        
        ax1.set_xlabel('Scan Rate (mV/s)', fontsize=12)
        ax1.set_ylabel('R² Value', fontsize=12)
        ax1.set_title('Peak Height Calibration Quality vs Scan Rate', fontsize=14, fontweight='bold')
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 1.05)
        
        # Add R² threshold lines
        ax1.axhline(y=0.95, color='green', linestyle='--', alpha=0.7, label='Excellent (R²>0.95)')
        ax1.axhline(y=0.90, color='orange', linestyle='--', alpha=0.7, label='Good (R²>0.90)')
        ax1.axhline(y=0.80, color='red', linestyle='--', alpha=0.7, label='Acceptable (R²>0.80)')
        ax1.legend(fontsize=10)
        
        # Plot 2: Peak Area R² vs Scan Rate
        palm_area_r2 = [r2_summary[sr].get('palmsens_area_r2', 0) for sr in scan_rates]
        stm32_area_r2 = [r2_summary[sr].get('stm32_area_r2', 0) for sr in scan_rates]
        
        ax2.plot(scan_rates, palm_area_r2, 'o-', color=colors[0], linewidth=2, markersize=8,
                label='Palmsens Area', markeredgecolor='black')
        ax2.plot(scan_rates, stm32_area_r2, 's-', color=colors[1], linewidth=2, markersize=8,
                label='STM32 Area', markeredgecolor='black')
        
        ax2.set_xlabel('Scan Rate (mV/s)', fontsize=12)
        ax2.set_ylabel('R² Value', fontsize=12)
        ax2.set_title('Peak Area Calibration Quality vs Scan Rate', fontsize=14, fontweight='bold')
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 1.05)
        
        # Add R² threshold lines
        ax2.axhline(y=0.95, color='green', linestyle='--', alpha=0.7, label='Excellent (R²>0.95)')
        ax2.axhline(y=0.90, color='orange', linestyle='--', alpha=0.7, label='Good (R²>0.90)')
        ax2.axhline(y=0.80, color='red', linestyle='--', alpha=0.7, label='Acceptable (R²>0.80)')
        ax2.legend(fontsize=10)
        
        plt.tight_layout()
        
        # Save R² summary plot
        r2_filename = f"cv_r2_summary_{timestamp}.png"
        plt.savefig(r2_filename, dpi=300, bbox_inches='tight')
        logger.info(f"💾 Saved R² summary plot: {r2_filename}")
        plt.show()
        
        return r2_filename
    
    def generate_report(self) -> str:
        """Generate detailed analysis report"""
        report = []
        report.append("="*70)
        report.append("CV CALIBRATION COMPARISON REPORT")
        report.append("Palmsens vs STM32 Peak Analysis")
        report.append("="*70)
        report.append(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # System summaries
        for system in ['palmsens', 'stm32']:
            data = self.results[system]
            if len(data['concentrations']) > 0:
                conc_array = np.array(data['concentrations'])
                height_array = np.array(data['peak_heights'])
                area_array = np.array(data['peak_areas'])
                
                report.append(f"{system.upper()} SYSTEM ANALYSIS:")
                report.append(f"  Files analyzed: {len(data['files'])}")
                report.append(f"  Concentration range: {conc_array.min():.2f} - {conc_array.max():.2f} mM")
                report.append(f"  Peak height range: {height_array.min():.2f} - {height_array.max():.2f} µA")
                report.append(f"  Peak area range: {area_array.min():.2f} - {area_array.max():.2f} µA·V")
                
                # Calibration statistics
                if len(conc_array) > 1:
                    slope_h, intercept_h, r_h, p_h, se_h = linregress(conc_array, height_array)
                    slope_a, intercept_a, r_a, p_a, se_a = linregress(conc_array, area_array)
                    
                    report.append(f"  Height calibration:")
                    report.append(f"    Equation: y = {slope_h:.3f}x + {intercept_h:.3f}")
                    report.append(f"    R² = {r_h**2:.4f}, p-value = {p_h:.2e}")
                    report.append(f"    Standard error = {se_h:.3f}")
                    
                    report.append(f"  Area calibration:")
                    report.append(f"    Equation: y = {slope_a:.3f}x + {intercept_a:.3f}")
                    report.append(f"    R² = {r_a**2:.4f}, p-value = {p_a:.2e}")
                    report.append(f"    Standard error = {se_a:.3f}")
                
                report.append("")
        
        # Cross-system comparison
        if (len(self.results['palmsens']['concentrations']) > 0 and 
            len(self.results['stm32']['concentrations']) > 0):
            
            palm_conc = np.array(self.results['palmsens']['concentrations'])
            stm32_conc = np.array(self.results['stm32']['concentrations'])
            common_conc = np.intersect1d(palm_conc, stm32_conc)
            
            report.append("CROSS-SYSTEM COMPARISON:")
            report.append(f"  Palmsens unique concentrations: {len(np.unique(palm_conc))}")
            report.append(f"  STM32 unique concentrations: {len(np.unique(stm32_conc))}")
            report.append(f"  Common concentrations: {len(common_conc)}")
            
            if len(common_conc) > 0:
                report.append(f"  Common values: {', '.join([f'{c:.1f}' for c in sorted(common_conc)])} mM")
        
        report.append("="*70)
        
        report_text = "\n".join(report)
        
        # Save report
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"cv_calibration_report_{timestamp}.txt"
        with open(report_filename, 'w') as f:
            f.write(report_text)
        
        logger.info(f"📄 Saved report: {report_filename}")
        print(report_text)
        
        return report_filename


def main():
    """Main analysis workflow"""
    logger.info("🚀 Starting CV Calibration Analysis...")
    
    analyzer = CVCalibrationAnalyzer()
    analyzer.scan_data_directories()
    
    if (len(analyzer.results['palmsens']['concentrations']) == 0 and 
        len(analyzer.results['stm32']['concentrations']) == 0):
        logger.error("❌ No valid data found. Please check Test_data directory structure.")
        return
    
    plot_file = analyzer.create_comparison_plots()
    report_file = analyzer.generate_report()
    
    logger.info("✅ Analysis complete!")
    logger.info(f"📊 Plot saved: {plot_file}")
    logger.info(f"📄 Report saved: {report_file}")


if __name__ == "__main__":
    main()