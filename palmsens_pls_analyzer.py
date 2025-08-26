#!/usr/bin/env python3
"""
Palmsens PLS Analysis by Scan Rate
=================================
Analyze Palmsens calibration data with corrected baselines
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
from sklearn.cross_decomposition import PLSRegression
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class PalmsensPlsAnalyzer:
    """PLS analysis for Palmsens CV data by scan rate"""
    
    def __init__(self, data_dir: str = "Test_data/Palmsens", corrections_file: str = None):
        """Initialize analyzer"""
        self.data_dir = Path(data_dir)
        self.corrections_file = corrections_file
        self.corrections = {}
        self.processed_data = []
        
        # Load baseline corrections if available
        if corrections_file and Path(corrections_file).exists():
            with open(corrections_file, 'r') as f:
                self.corrections = json.load(f)
            logger.info(f"Loaded {len(self.corrections)} baseline corrections")
    
    def extract_metadata(self, filename: str) -> Dict:
        """Extract concentration and scan rate from filename"""
        filename_lower = filename.lower()
        
        # Concentration extraction
        concentration = None
        conc_patterns = [
            r'(\d+\.?\d*)\s*mm',
            r'ferro[_\-](\d+\.?\d*)[_\-]?mm',
            r'(\d+\.?\d*)mm'
        ]
        
        for pattern in conc_patterns:
            match = re.search(pattern, filename_lower)
            if match:
                try:
                    concentration = float(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue
        
        # Scan rate extraction  
        scan_rate = None
        sr_patterns = [
            r'(\d+\.?\d*)\s*mv[\/\-_]?s',
            r'(\d+\.?\d*)\s*mvps',
            r'scan[_\-]?rate[_\-]?(\d+\.?\d*)'
        ]
        
        for pattern in sr_patterns:
            match = re.search(pattern, filename_lower)
            if match:
                try:
                    scan_rate = float(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue
        
        return {
            'concentration': concentration,
            'scan_rate': scan_rate,
            'filename': filename
        }
    
    def apply_baseline_correction(self, voltage: np.ndarray, current: np.ndarray, 
                                filename: str) -> Tuple[np.ndarray, float, float]:
        """Apply baseline correction if available"""
        if filename in self.corrections:
            correction = self.corrections[filename]
            v_min, v_max = correction['voltage_range']
            
            # Find baseline indices
            baseline_mask = (voltage >= v_min) & (voltage <= v_max)
            baseline_indices = np.where(baseline_mask)[0]
            
            if len(baseline_indices) >= 2:
                # Fit corrected baseline
                baseline_v = voltage[baseline_indices]
                baseline_i = current[baseline_indices]
                slope, intercept, _, _, _ = linregress(baseline_v, baseline_i)
                
                # Apply correction
                baseline_fit = slope * voltage + intercept
                corrected_current = current - baseline_fit
                
                # Calculate metrics
                peak_height = np.max(corrected_current) - np.min(corrected_current)
                peak_area = abs(np.trapz(corrected_current, voltage))
                
                logger.debug(f"Applied correction to {filename}: height={peak_height:.2f}")
                return corrected_current, peak_height, peak_area
        
        # No correction available - use original algorithm
        return self.auto_baseline_correction(voltage, current)
    
    def auto_baseline_correction(self, voltage: np.ndarray, current: np.ndarray) -> Tuple[np.ndarray, float, float]:
        """Automatic baseline correction"""
        # Simple method: linear fit to first/last 20% of data
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
            # Fallback: use original current
            corrected_current = current
        
        peak_height = np.max(corrected_current) - np.min(corrected_current)
        peak_area = abs(np.trapz(corrected_current, voltage))
        
        return corrected_current, peak_height, peak_area
    
    def process_file(self, file_path: Path) -> Optional[Dict]:
        """Process a single Palmsens CSV file"""
        try:
            # Load data
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            
            # Find voltage and current columns
            voltage_col = None
            current_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'voltage' in col_lower or col == 'V':
                    voltage_col = col
                elif 'current' in col_lower or col in ['uA', 'Current (µA)', 'I']:
                    current_col = col
            
            if voltage_col is None or current_col is None:
                logger.warning(f"Could not find voltage/current columns in {file_path.name}")
                return None
            
            voltage = df[voltage_col].values
            current = df[current_col].values
            
            # Remove NaN values
            mask = ~(np.isnan(voltage) | np.isnan(current))
            voltage = voltage[mask]
            current = current[mask]
            
            if len(voltage) < 10:
                logger.warning(f"Insufficient data in {file_path.name}")
                return None
            
            # Apply baseline correction
            corrected_current, peak_height, peak_area = self.apply_baseline_correction(
                voltage, current, file_path.name
            )
            
            # Extract metadata
            metadata = self.extract_metadata(file_path.name)
            
            if metadata['concentration'] is None or metadata['scan_rate'] is None:
                logger.warning(f"Could not extract metadata from {file_path.name}")
                return None
            
            # Additional features for PLS analysis
            features = {
                'peak_height': peak_height,
                'peak_area': peak_area,
                'voltage_range': np.max(voltage) - np.min(voltage),
                'current_std': np.std(corrected_current),
                'peak_position': voltage[np.argmax(corrected_current)],
                'peak_width': self.calculate_peak_width(voltage, corrected_current),
                'asymmetry': self.calculate_asymmetry(corrected_current)
            }
            
            result = {
                **metadata,
                **features,
                'filepath': str(file_path)
            }
            
            return result
            
        except Exception as e:
            logger.warning(f"Error processing {file_path.name}: {e}")
            return None
    
    def calculate_peak_width(self, voltage: np.ndarray, current: np.ndarray) -> float:
        """Calculate peak width at half maximum"""
        try:
            peak_idx = np.argmax(current)
            peak_value = current[peak_idx]
            half_max = peak_value / 2
            
            # Find indices where current > half_max
            above_half = current > half_max
            indices = np.where(above_half)[0]
            
            if len(indices) > 1:
                width_voltage = voltage[indices[-1]] - voltage[indices[0]]
                return abs(width_voltage)
            else:
                return 0.0
        except:
            return 0.0
    
    def calculate_asymmetry(self, current: np.ndarray) -> float:
        """Calculate peak asymmetry factor"""
        try:
            peak_idx = np.argmax(current)
            peak_value = current[peak_idx]
            
            left_area = np.sum(current[:peak_idx])
            right_area = np.sum(current[peak_idx:])
            
            if left_area + right_area > 0:
                return (right_area - left_area) / (right_area + left_area)
            else:
                return 0.0
        except:
            return 0.0
    
    def run_pls_analysis(self):
        """Run complete PLS analysis by scan rate"""
        logger.info("🚀 Starting Palmsens PLS Analysis by Scan Rate")
        logger.info("=" * 60)
        
        # Check if data directory exists
        if not self.data_dir.exists():
            logger.error(f"Data directory not found: {self.data_dir}")
            return
        
        # Process all CSV files recursively
        csv_files = list(self.data_dir.rglob("*.csv"))
        logger.info(f"Found {len(csv_files)} CSV files")
        
        successful = 0
        failed = 0
        
        for file_path in csv_files:
            result = self.process_file(file_path)
            if result:
                self.processed_data.append(result)
                successful += 1
            else:
                failed += 1
        
        logger.info(f"✅ Processed {successful} files successfully")
        logger.info(f"❌ Failed to process {failed} files")
        
        if len(self.processed_data) < 10:
            logger.warning("⚠️ Insufficient data for reliable PLS analysis")
            return
        
        # Group by scan rate and analyze
        self.analyze_by_scan_rate()
        
        # Generate summary report
        self.generate_summary_report()
    
    def analyze_by_scan_rate(self):
        """Analyze PLS models for each scan rate"""
        logger.info("\n📊 PLS Analysis by Scan Rate")
        
        # Group data by scan rate
        scan_rate_groups = {}
        for data in self.processed_data:
            sr = data['scan_rate']
            if sr not in scan_rate_groups:
                scan_rate_groups[sr] = []
            scan_rate_groups[sr].append(data)
        
        scan_rates = sorted(scan_rate_groups.keys())
        logger.info(f"📊 Found scan rates: {scan_rates} mV/s")
        
        # Feature names for PLS
        feature_names = ['peak_height', 'peak_area', 'voltage_range', 'current_std', 
                        'peak_position', 'peak_width', 'asymmetry']
        
        # Analyze each scan rate
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
            
            if len(data_group) < 5:
                logger.warning(f"⚠️ Insufficient data for {scan_rate} mV/s")
                continue
            
            # Prepare data for PLS
            concentrations = np.array([d['concentration'] for d in data_group])
            features_matrix = np.array([[d[feat] for feat in feature_names] for d in data_group])
            
            # Check for sufficient concentration variety
            unique_concentrations = len(np.unique(concentrations))
            if unique_concentrations < 3:
                logger.warning(f"⚠️ Insufficient concentration variety for {scan_rate} mV/s")
                continue
            
            # Standardize features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features_matrix)
            
            # PLS analysis
            try:
                # Try different numbers of components
                best_r2 = -1
                best_n_components = 1
                
                for n_comp in range(1, min(len(feature_names), unique_concentrations)):
                    pls = PLSRegression(n_components=n_comp)
                    pls.fit(features_scaled, concentrations)
                    y_pred = pls.predict(features_scaled)
                    r2 = r2_score(concentrations, y_pred)
                    
                    if r2 > best_r2:
                        best_r2 = r2
                        best_n_components = n_comp
                
                # Final PLS model with best components
                pls_final = PLSRegression(n_components=best_n_components)
                pls_final.fit(features_scaled, concentrations)
                concentrations_pred = pls_final.predict(features_scaled).flatten()
                
                # Calculate metrics
                r2_pls = r2_score(concentrations, concentrations_pred)
                rmse_pls = np.sqrt(mean_squared_error(concentrations, concentrations_pred))
                
                # Simple linear regression for comparison
                peak_heights = [d['peak_height'] for d in data_group]
                slope, intercept, r_value, _, _ = linregress(concentrations, peak_heights)
                r2_simple = r_value ** 2
                
                # Plot results
                ax = axes[i]
                
                # PLS predictions vs actual
                ax.scatter(concentrations, concentrations_pred, alpha=0.7, s=50, 
                          label=f'PLS (R²={r2_pls:.3f})')
                
                # Simple linear relationship
                conc_range = np.linspace(min(concentrations), max(concentrations), 100)
                simple_pred = (np.array(peak_heights) - intercept) / slope
                ax.scatter(concentrations, simple_pred, alpha=0.5, s=30,
                          label=f'Simple (R²={r2_simple:.3f})')
                
                # Perfect prediction line
                ax.plot(conc_range, conc_range, 'k--', alpha=0.5, label='Perfect')
                
                ax.set_xlabel('Actual Concentration (mM)')
                ax.set_ylabel('Predicted Concentration (mM)')
                ax.set_title(f'{scan_rate} mV/s Palmsens PLS')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                # Store results
                results_summary[scan_rate] = {
                    'n_samples': len(data_group),
                    'n_components': best_n_components,
                    'pls_r2': r2_pls,
                    'pls_rmse': rmse_pls,
                    'simple_r2': r2_simple,
                    'concentrations': sorted(set(concentrations)),
                    'feature_importance': pls_final.coef_.flatten().tolist()
                }
                
                logger.info(f"   {scan_rate} mV/s: {len(data_group)} samples, "
                           f"PLS R²={r2_pls:.3f}, Simple R²={r2_simple:.3f}")
                
            except Exception as e:
                logger.warning(f"PLS analysis failed for {scan_rate} mV/s: {e}")
                continue
        
        # Hide extra subplots
        for i in range(len(scan_rates), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_filename = f"palmsens_pls_analysis_{timestamp}.png"
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        logger.info(f"📊 PLS analysis plots saved: {plot_filename}")
        
        # Save results
        report_filename = f"palmsens_pls_report_{timestamp}.json"
        with open(report_filename, 'w') as f:
            json.dump(results_summary, f, indent=2)
        logger.info(f"📄 PLS analysis report saved: {report_filename}")
        
        return results_summary
    
    def generate_summary_report(self):
        """Generate summary report"""
        logger.info("\n📊 Palmsens PLS Analysis Summary:")
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
        
        if self.corrections:
            corrected_files = len(self.corrections)
            logger.info(f"🔧 Applied baseline corrections: {corrected_files} files")
        
        logger.info("\n✅ Palmsens PLS Analysis completed!")
        logger.info("   - Multi-feature PLS models generated")
        logger.info("   - Compared with simple linear regression")
        logger.info("   - Results saved for scientific publication")

def main():
    """Main execution"""
    # Check for baseline corrections file
    corrections_file = "baseline_corrections.json"
    
    analyzer = PalmsensPlsAnalyzer(
        data_dir="Test_data/Palmsens",
        corrections_file=corrections_file if Path(corrections_file).exists() else None
    )
    analyzer.run_pls_analysis()

if __name__ == "__main__":
    main()