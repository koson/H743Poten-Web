#!/usr/bin/env python3
"""
CV PLS Calibration Comparison: Palmsens vs STM32
Compare peak height and peak area calibration curves between two systems
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.integrate import trapz
from scipy.signal import find_peaks
from scipy.stats import linregress
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
import os
import glob
import re
import logging
from typing import Dict, List, Tuple, Optional
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Set plot style
plt.style.use('default')
sns.set_palette("husl")

class CVPLSAnalyzer:
    """CV Peak Analysis and PLS Calibration Comparison"""
    
    def __init__(self):
        self.data_cache = {}
        self.results = {
            'palmsens': {'concentrations': [], 'peak_heights': [], 'peak_areas': [], 'files': []},
            'stm32': {'concentrations': [], 'peak_heights': [], 'peak_areas': [], 'files': []}
        }
        
    def extract_concentration_from_filename(self, filename: str) -> Optional[float]:
        """
        Extract concentration from filename patterns like:
        - Palmsens_0.5mM_... -> 0.5
        - Pipot_Ferro_1_0mM_... -> 1.0
        - ...2_5mM_... -> 2.5
        """
        # Pattern for different concentration formats
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
            # Try different loading approaches
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
                logger.error(f"Unknown column format in {filepath}")
                return None
            
            # Convert current to consistent units (µA)
            if current_unit == 'A':
                current = current * 1e6  # Convert A to µA
                
            return voltage, current
            
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
            return None
    
    def find_cv_peaks(self, voltage: np.ndarray, current: np.ndarray) -> Dict:
        """
        Find oxidation and reduction peaks in CV data
        """
        # Sort by voltage to ensure proper order
        sorted_indices = np.argsort(voltage)
        v_sorted = voltage[sorted_indices]
        i_sorted = current[sorted_indices]
        
        # Find peaks and valleys
        # For oxidation: positive current peaks
        # For reduction: negative current peaks (valleys)
        
        peaks_pos, _ = find_peaks(i_sorted, height=np.max(i_sorted) * 0.1, distance=10)
        peaks_neg, _ = find_peaks(-i_sorted, height=-np.min(i_sorted) * 0.1, distance=10)
        
        results = {
            'oxidation_peaks': [],
            'reduction_peaks': [],
            'peak_separation': None,
            'max_oxidation_current': 0,
            'max_reduction_current': 0
        }
        
        if len(peaks_pos) > 0:
            # Find the most prominent oxidation peak
            max_ox_idx = peaks_pos[np.argmax(i_sorted[peaks_pos])]
            results['oxidation_peaks'] = [(v_sorted[max_ox_idx], i_sorted[max_ox_idx])]
            results['max_oxidation_current'] = i_sorted[max_ox_idx]
        
        if len(peaks_neg) > 0:
            # Find the most prominent reduction peak
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
        """
        Calculate peak areas using different methods
        """
        # Sort data
        sorted_indices = np.argsort(voltage)
        v_sorted = voltage[sorted_indices]
        i_sorted = current[sorted_indices]
        
        # Method 1: Simple integration
        total_area = abs(trapz(i_sorted, v_sorted))
        
        # Method 2: Positive and negative areas separately
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
        # Extract concentration
        concentration = self.extract_concentration_from_filename(os.path.basename(filepath))
        if concentration is None:
            return None
        
        # Load data
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
            'peak_height': peak_height,
            'peak_area': area_info['combined_area'],
            'oxidation_area': area_info['oxidation_area'],
            'reduction_area': area_info['reduction_area'],
            'peak_separation': peak_info['peak_separation'],
            'voltage': voltage,
            'current': current,
            'peak_info': peak_info,
            'area_info': area_info
        }
    
    def scan_data_directories(self):
        """Scan for CV data files and categorize by system"""
        logger.info("🔍 Scanning for CV data files...")
        
        # Define search patterns
        patterns = {
            'palmsens': 'Test_data/Palmsens/**/*.csv',
            'stm32': 'Test_data/Stm32/**/*.csv'
        }
        
        for system, pattern in patterns.items():
            files = glob.glob(pattern, recursive=True)
            logger.info(f"📁 Found {len(files)} {system} files")
            
            for filepath in files:
                result = self.process_file(filepath)
                if result:
                    self.results[system]['concentrations'].append(result['concentration'])
                    self.results[system]['peak_heights'].append(result['peak_height'])
                    self.results[system]['peak_areas'].append(result['peak_area'])
                    self.results[system]['files'].append(result['filename'])
                    
                    logger.info(f"✅ {system}: {result['filename']} - {result['concentration']}mM, "
                              f"height={result['peak_height']:.2f}µA, area={result['peak_area']:.2f}")
    
    def perform_pls_analysis(self, X: np.ndarray, y: np.ndarray, n_components: int = 2) -> Dict:
        """Perform PLS regression analysis"""
        if len(X) < 3:
            logger.warning("Not enough data points for PLS analysis")
            return {'error': 'Insufficient data'}
        
        # Reshape X if it's 1D
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        
        # Standardize features
        scaler_X = StandardScaler()
        scaler_y = StandardScaler()
        
        X_scaled = scaler_X.fit_transform(X)
        y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()
        
        # Fit PLS
        n_components = min(n_components, X.shape[1], len(X) - 1)
        pls = PLSRegression(n_components=n_components)
        pls.fit(X_scaled, y_scaled)
        
        # Predictions
        y_pred_scaled = pls.predict(X_scaled).ravel()
        y_pred = scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).ravel()
        
        # Metrics
        r2 = r2_score(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        
        return {
            'pls_model': pls,
            'scaler_X': scaler_X,
            'scaler_y': scaler_y,
            'y_pred': y_pred,
            'r2': r2,
            'rmse': rmse,
            'n_components': n_components
        }
    
    def create_comparison_plots(self):
        """Create comprehensive comparison plots"""
        fig = plt.figure(figsize=(16, 12))
        
        # Prepare data
        systems = ['palmsens', 'stm32']
        colors = ['#E74C3C', '#3498DB']  # Red for Palmsens, Blue for STM32
        
        # Plot 1: Peak Height vs Concentration
        plt.subplot(2, 3, 1)
        for i, system in enumerate(systems):
            if len(self.results[system]['concentrations']) > 0:
                x = np.array(self.results[system]['concentrations'])
                y = np.array(self.results[system]['peak_heights'])
                
                plt.scatter(x, y, c=colors[i], label=f'{system.title()} (n={len(x)})', 
                           s=60, alpha=0.7, edgecolors='black', linewidth=0.5)
                
                # Linear fit
                if len(x) > 1:
                    slope, intercept, r_value, p_value, std_err = linregress(x, y)
                    x_fit = np.linspace(x.min(), x.max(), 100)
                    y_fit = slope * x_fit + intercept
                    plt.plot(x_fit, y_fit, color=colors[i], linestyle='--', alpha=0.8)
                    plt.text(0.05, 0.95 - i*0.1, f'{system.title()}: R²={r_value**2:.3f}', 
                            transform=plt.gca().transAxes, color=colors[i], fontweight='bold')
        
        plt.xlabel('Concentration (mM)')
        plt.ylabel('Peak Height (µA)')
        plt.title('Peak Height Calibration')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot 2: Peak Area vs Concentration
        plt.subplot(2, 3, 2)
        for i, system in enumerate(systems):
            if len(self.results[system]['concentrations']) > 0:
                x = np.array(self.results[system]['concentrations'])
                y = np.array(self.results[system]['peak_areas'])
                
                plt.scatter(x, y, c=colors[i], label=f'{system.title()} (n={len(x)})', 
                           s=60, alpha=0.7, edgecolors='black', linewidth=0.5)
                
                # Linear fit
                if len(x) > 1:
                    slope, intercept, r_value, p_value, std_err = linregress(x, y)
                    x_fit = np.linspace(x.min(), x.max(), 100)
                    y_fit = slope * x_fit + intercept
                    plt.plot(x_fit, y_fit, color=colors[i], linestyle='--', alpha=0.8)
                    plt.text(0.05, 0.95 - i*0.1, f'{system.title()}: R²={r_value**2:.3f}', 
                            transform=plt.gca().transAxes, color=colors[i], fontweight='bold')
        
        plt.xlabel('Concentration (mM)')
        plt.ylabel('Peak Area (µA·V)')
        plt.title('Peak Area Calibration')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot 3: Direct Comparison - Peak Height
        plt.subplot(2, 3, 3)
        if (len(self.results['palmsens']['concentrations']) > 0 and 
            len(self.results['stm32']['concentrations']) > 0):
            
            # Find common concentrations
            palm_conc = np.array(self.results['palmsens']['concentrations'])
            stm32_conc = np.array(self.results['stm32']['concentrations'])
            common_conc = np.intersect1d(palm_conc, stm32_conc)
            
            if len(common_conc) > 0:
                palm_heights = []
                stm32_heights = []
                
                for conc in common_conc:
                    palm_idx = np.where(palm_conc == conc)[0]
                    stm32_idx = np.where(stm32_conc == conc)[0]
                    
                    if len(palm_idx) > 0 and len(stm32_idx) > 0:
                        palm_heights.append(np.mean([self.results['palmsens']['peak_heights'][i] for i in palm_idx]))
                        stm32_heights.append(np.mean([self.results['stm32']['peak_heights'][i] for i in stm32_idx]))
                
                if len(palm_heights) > 1:
                    plt.scatter(palm_heights, stm32_heights, c='purple', s=80, alpha=0.7, edgecolors='black')
                    
                    # Linear fit
                    slope, intercept, r_value, p_value, std_err = linregress(palm_heights, stm32_heights)
                    x_fit = np.linspace(min(palm_heights), max(palm_heights), 100)
                    y_fit = slope * x_fit + intercept
                    plt.plot(x_fit, y_fit, 'purple', linestyle='--', alpha=0.8)
                    
                    # Unity line
                    min_val = min(min(palm_heights), min(stm32_heights))
                    max_val = max(max(palm_heights), max(stm32_heights))
                    plt.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, label='Unity')
                    
                    plt.text(0.05, 0.95, f'R²={r_value**2:.3f}', transform=plt.gca().transAxes, 
                            fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        plt.xlabel('Palmsens Peak Height (µA)')
        plt.ylabel('STM32 Peak Height (µA)')
        plt.title('Peak Height: Palmsens vs STM32')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot 4: Data Distribution
        plt.subplot(2, 3, 4)
        conc_data = []
        system_labels = []
        
        for system in systems:
            if len(self.results[system]['concentrations']) > 0:
                conc_data.extend(self.results[system]['concentrations'])
                system_labels.extend([system.title()] * len(self.results[system]['concentrations']))
        
        if conc_data:
            df_dist = pd.DataFrame({'Concentration': conc_data, 'System': system_labels})
            sns.boxplot(data=df_dist, x='System', y='Concentration', palette=colors)
            plt.title('Concentration Distribution by System')
            plt.ylabel('Concentration (mM)')
        
        # Plot 5: Peak Height Distribution
        plt.subplot(2, 3, 5)
        height_data = []
        system_labels = []
        
        for system in systems:
            if len(self.results[system]['peak_heights']) > 0:
                height_data.extend(self.results[system]['peak_heights'])
                system_labels.extend([system.title()] * len(self.results[system]['peak_heights']))
        
        if height_data:
            df_height = pd.DataFrame({'Peak Height': height_data, 'System': system_labels})
            sns.boxplot(data=df_height, x='System', y='Peak Height', palette=colors)
            plt.title('Peak Height Distribution by System')
            plt.ylabel('Peak Height (µA)')
        
        # Plot 6: Summary Statistics
        plt.subplot(2, 3, 6)
        plt.axis('off')
        
        summary_text = "📊 ANALYSIS SUMMARY\n\n"
        
        for i, system in enumerate(systems):
            data = self.results[system]
            if len(data['concentrations']) > 0:
                conc_array = np.array(data['concentrations'])
                height_array = np.array(data['peak_heights'])
                area_array = np.array(data['peak_areas'])
                
                summary_text += f"{system.upper()}:\n"
                summary_text += f"  • Files: {len(data['files'])}\n"
                summary_text += f"  • Conc range: {conc_array.min():.1f}-{conc_array.max():.1f} mM\n"
                summary_text += f"  • Height range: {height_array.min():.1f}-{height_array.max():.1f} µA\n"
                summary_text += f"  • Area range: {area_array.min():.1f}-{area_array.max():.1f} µA·V\n\n"
        
        plt.text(0.05, 0.95, summary_text, transform=plt.gca().transAxes, 
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))
        
        plt.tight_layout()
        
        # Save plot
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cv_pls_comparison_{timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        logger.info(f"💾 Saved comparison plot: {filename}")
        
        plt.show()
        
        return filename
    
    def generate_report(self) -> str:
        """Generate detailed analysis report"""
        report = []
        report.append("="*60)
        report.append("CV PLS CALIBRATION COMPARISON REPORT")
        report.append("="*60)
        report.append(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # System summaries
        for system in ['palmsens', 'stm32']:
            data = self.results[system]
            if len(data['concentrations']) > 0:
                conc_array = np.array(data['concentrations'])
                height_array = np.array(data['peak_heights'])
                area_array = np.array(data['peak_areas'])
                
                report.append(f"{system.upper()} SYSTEM:")
                report.append(f"  Files analyzed: {len(data['files'])}")
                report.append(f"  Concentration range: {conc_array.min():.2f} - {conc_array.max():.2f} mM")
                report.append(f"  Peak height range: {height_array.min():.2f} - {height_array.max():.2f} µA")
                report.append(f"  Peak area range: {area_array.min():.2f} - {area_array.max():.2f} µA·V")
                
                # Linear regression stats
                if len(conc_array) > 1:
                    slope_h, intercept_h, r_h, p_h, se_h = linregress(conc_array, height_array)
                    slope_a, intercept_a, r_a, p_a, se_a = linregress(conc_array, area_array)
                    
                    report.append(f"  Height calibration: R² = {r_h**2:.4f}, slope = {slope_h:.2f}")
                    report.append(f"  Area calibration: R² = {r_a**2:.4f}, slope = {slope_a:.2f}")
                
                report.append("")
        
        # Cross-system comparison
        if (len(self.results['palmsens']['concentrations']) > 0 and 
            len(self.results['stm32']['concentrations']) > 0):
            
            report.append("CROSS-SYSTEM COMPARISON:")
            
            # Find common concentrations
            palm_conc = np.array(self.results['palmsens']['concentrations'])
            stm32_conc = np.array(self.results['stm32']['concentrations'])
            common_conc = np.intersect1d(palm_conc, stm32_conc)
            
            report.append(f"  Common concentrations: {len(common_conc)}")
            if len(common_conc) > 0:
                report.append(f"  Concentrations: {', '.join([f'{c:.1f}' for c in sorted(common_conc)])} mM")
        
        report.append("="*60)
        
        report_text = "\n".join(report)
        
        # Save report
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"cv_pls_report_{timestamp}.txt"
        with open(report_filename, 'w') as f:
            f.write(report_text)
        
        logger.info(f"📄 Saved report: {report_filename}")
        print(report_text)
        
        return report_filename


def main():
    """Main analysis workflow"""
    logger.info("🚀 Starting CV PLS Calibration Analysis...")
    
    # Initialize analyzer
    analyzer = CVPLSAnalyzer()
    
    # Scan and process data
    analyzer.scan_data_directories()
    
    # Create comparison plots
    plot_file = analyzer.create_comparison_plots()
    
    # Generate report
    report_file = analyzer.generate_report()
    
    logger.info("✅ Analysis complete!")
    logger.info(f"📊 Plot saved: {plot_file}")
    logger.info(f"📄 Report saved: {report_file}")


if __name__ == "__main__":
    main()