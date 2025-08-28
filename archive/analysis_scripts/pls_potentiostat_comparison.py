#!/usr/bin/env python3
"""
PLS Analysis: Palmsens (Reference) vs STM32 (Target)
Complete workflow for potentiostat comparison using Enhanced Detector V4 Improved
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cross_decomposition import PLSRegression
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import seaborn as sns
import os
import glob
import re
from pathlib import Path
import time
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import Enhanced Detector V4 Improved
try:
    from enhanced_detector_v4_improved import EnhancedDetectorV4Improved
    print("✅ Enhanced Detector V4 Improved ready")
    HAS_ENHANCED_V4 = True
except ImportError:
    print("❌ Enhanced Detector V4 Improved not available")
    HAS_ENHANCED_V4 = False

class PLSPotentiostatComparison:
    """
    Complete PLS analysis for comparing STM32 vs Palmsens potentiostats
    """
    
    def __init__(self, output_dir="pls_comparison_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize Enhanced Detector
        if HAS_ENHANCED_V4:
            self.detector = EnhancedDetectorV4Improved(confidence_threshold=25.0)
        else:
            self.detector = None
            
        # Data storage
        self.palmsens_data = []
        self.stm32_data = []
        self.matched_pairs = []
        
        # Statistics
        self.stats = {
            'palmsens': {'total': 0, 'success': 0, 'both_peaks': 0},
            'stm32': {'total': 0, 'success': 0, 'both_peaks': 0},
            'matched_pairs': 0
        }
    
    def extract_metadata(self, filename):
        """Extract metadata from filename"""
        filename_only = Path(filename).stem
        
        patterns = [
            r'(\w+)_([0-9.]+mM)_CV_([0-9.]+mVpS)_(\w+)_scan_(\d+)',
            r'(\w+)_([0-9.]+)mM_CV_([0-9.]+)mVs_(\w+)_scan_(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename_only)
            if match:
                groups = match.groups()
                device = groups[0]
                concentration_str = groups[1]
                scan_rate_str = groups[2]
                electrode = groups[3]
                scan_number = groups[4]
                
                # Extract numeric values
                conc_match = re.search(r'([0-9.]+)', concentration_str)
                concentration = float(conc_match.group(1)) if conc_match else 0.0
                
                rate_match = re.search(r'([0-9.]+)', scan_rate_str)
                scan_rate = float(rate_match.group(1)) if rate_match else 0.0
                
                return {
                    'device': device,
                    'concentration': concentration,
                    'scan_rate': scan_rate,
                    'electrode': electrode,
                    'scan_number': int(scan_number),
                    'filename': filename_only
                }
        
        return None
    
    def analyze_cv_file(self, filepath):
        """Analyze single CV file with Enhanced V4 Improved"""
        try:
            # Load CSV file
            data = pd.read_csv(filepath, skiprows=2, names=['voltage', 'current'])
            
            if data.empty or len(data) < 10:
                return None
            
            # Prepare data for Enhanced V4 Improved
            cv_data = {
                'voltage': data['voltage'].tolist(),
                'current': data['current'].tolist()
            }
            
            # Run Enhanced V4 Improved detection
            results = self.detector.analyze_cv_data(cv_data)
            
            if not results or not isinstance(results, dict):
                return None
            
            # Extract peaks
            all_peaks = results.get('peaks', [])
            if not all_peaks:
                return None
            
            # Separate peak types
            ox_peaks = [p for p in all_peaks if p.get('type') == 'oxidation']
            red_peaks = [p for p in all_peaks if p.get('type') == 'reduction']
            
            # Check if both peak types exist
            has_both_peaks = len(ox_peaks) > 0 and len(red_peaks) > 0
            
            if not has_both_peaks:
                return None
            
            # Extract metadata
            metadata = self.extract_metadata(filepath.name)
            if not metadata:
                return None
            
            # Calculate features
            ox_peak = ox_peaks[0]  # Take first oxidation peak
            red_peak = red_peaks[0]  # Take first reduction peak
            
            features = {
                'filename': filepath.name,
                'device': metadata['device'],
                'concentration': metadata['concentration'],
                'scan_rate': metadata['scan_rate'],
                'electrode': metadata['electrode'],
                'scan_number': metadata['scan_number'],
                
                # Peak features
                'ox_voltage': ox_peak.get('voltage', 0),
                'ox_current': ox_peak.get('current', 0),
                'ox_confidence': ox_peak.get('confidence', 0),
                'red_voltage': red_peak.get('voltage', 0),
                'red_current': red_peak.get('current', 0),
                'red_confidence': red_peak.get('confidence', 0),
                
                # Derived features
                'peak_separation_voltage': abs(ox_peak.get('voltage', 0) - red_peak.get('voltage', 0)),
                'peak_separation_current': abs(ox_peak.get('current', 0) - red_peak.get('current', 0)),
                'current_ratio': abs(ox_peak.get('current', 0) / red_peak.get('current', 0)) if red_peak.get('current', 0) != 0 else 0,
                'midpoint_potential': (ox_peak.get('voltage', 0) + red_peak.get('voltage', 0)) / 2
            }
            
            return features
            
        except Exception as e:
            print(f"❌ Error analyzing {filepath.name}: {e}")
            return None
    
    def load_device_data(self, data_dir, device_name):
        """Load and analyze all files from a device directory"""
        if not os.path.exists(data_dir):
            print(f"❌ Directory not found: {data_dir}")
            return []
        
        # Find all CSV files
        pattern = os.path.join(data_dir, "**", "*.csv")
        files = glob.glob(pattern, recursive=True)
        
        print(f"📁 Found {len(files)} files in {data_dir}")
        
        device_results = []
        stats = {'total': 0, 'success': 0, 'both_peaks': 0}
        
        for filepath in files[:20]:  # Limit to 20 files for testing
            print(f"🔬 Analyzing {Path(filepath).name}...", end=" ")
            
            stats['total'] += 1
            result = self.analyze_cv_file(Path(filepath))
            
            if result:
                device_results.append(result)
                stats['success'] += 1
                stats['both_peaks'] += 1  # All successful results have both peaks
                print("✅")
            else:
                print("❌")
        
        self.stats[device_name.lower()] = stats
        
        print(f"📊 {device_name} Results: {stats['success']}/{stats['total']} successful ({stats['success']/stats['total']*100:.1f}%)")
        
        return device_results
    
    def match_measurement_pairs(self):
        """Match Palmsens and STM32 measurements by concentration, scan_rate, and electrode"""
        matched = []
        
        print(f"🔗 Matching measurements...")
        print(f"  Palmsens: {len(self.palmsens_data)} measurements")
        print(f"  STM32: {len(self.stm32_data)} measurements")
        
        for palmsens in self.palmsens_data:
            for stm32 in self.stm32_data:
                # Match criteria
                if (abs(palmsens['concentration'] - stm32['concentration']) < 0.01 and
                    abs(palmsens['scan_rate'] - stm32['scan_rate']) < 1.0 and
                    palmsens['electrode'] == stm32['electrode']):
                    
                    matched.append({
                        'concentration': palmsens['concentration'],
                        'scan_rate': palmsens['scan_rate'],
                        'electrode': palmsens['electrode'],
                        'palmsens': palmsens,
                        'stm32': stm32
                    })
        
        self.matched_pairs = matched
        self.stats['matched_pairs'] = len(matched)
        
        print(f"🎯 Found {len(matched)} matched pairs")
        
        return matched
    
    def perform_pls_analysis(self):
        """Perform PLS regression analysis"""
        if not self.matched_pairs:
            print("❌ No matched pairs for PLS analysis")
            return None
        
        print(f"📊 Performing PLS analysis on {len(self.matched_pairs)} pairs...")
        
        # Prepare feature matrices
        feature_names = ['ox_voltage', 'ox_current', 'red_voltage', 'red_current', 
                        'peak_separation_voltage', 'current_ratio', 'midpoint_potential']
        
        # STM32 features (X - predictor)
        X = np.array([[pair['stm32'][feat] for feat in feature_names] for pair in self.matched_pairs])
        
        # Palmsens features (Y - target)  
        Y = np.array([[pair['palmsens'][feat] for feat in feature_names] for pair in self.matched_pairs])
        
        # Concentration for validation
        concentrations = np.array([pair['concentration'] for pair in self.matched_pairs])
        
        print(f"  X shape (STM32 features): {X.shape}")
        print(f"  Y shape (Palmsens features): {Y.shape}")
        
        # Scale features
        scaler_X = StandardScaler()
        scaler_Y = StandardScaler()
        
        X_scaled = scaler_X.fit_transform(X)
        Y_scaled = scaler_Y.fit_transform(Y)
        
        # PLS regression
        pls = PLSRegression(n_components=min(3, X.shape[1]), scale=False)  # Already scaled
        pls.fit(X_scaled, Y_scaled)
        
        # Predictions
        Y_pred_scaled = pls.predict(X_scaled)
        Y_pred = scaler_Y.inverse_transform(Y_pred_scaled)
        
        # Performance metrics
        metrics = {}
        for i, feat in enumerate(feature_names):
            y_true = Y[:, i]
            y_pred = Y_pred[:, i]
            
            metrics[feat] = {
                'r2': r2_score(y_true, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
                'mae': mean_absolute_error(y_true, y_pred),
                'bias': np.mean(y_pred - y_true)
            }
        
        # Cross-validation
        cv_scores = cross_val_score(pls, X_scaled, Y_scaled, cv=min(5, len(X)), scoring='r2')
        
        # Store results
        self.pls_results = {
            'model': pls,
            'scalers': {'X': scaler_X, 'Y': scaler_Y},
            'predictions': {'Y_true': Y, 'Y_pred': Y_pred},
            'metrics': metrics,
            'cv_scores': cv_scores,
            'feature_names': feature_names,
            'concentrations': concentrations
        }
        
        # Print summary
        print(f"\\n📈 PLS Analysis Results:")
        print(f"  Cross-validation R²: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        print(f"  Number of components: {pls.n_components}")
        
        print(f"\\n📋 Feature-wise Performance:")
        for feat, met in metrics.items():
            print(f"  {feat:20s}: R²={met['r2']:.3f}, RMSE={met['rmse']:.4f}, Bias={met['bias']:.4f}")
        
        return self.pls_results
    
    def create_pls_visualizations(self):
        """Create comprehensive PLS visualization plots"""
        if not hasattr(self, 'pls_results'):
            print("❌ No PLS results to visualize")
            return
        
        # Set up plot style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Create figure with subplots
        fig = plt.figure(figsize=(20, 16))
        
        # 1. PLS Scores Plot
        ax1 = plt.subplot(3, 3, 1)
        pls = self.pls_results['model']
        X_scaled = self.pls_results['scalers']['X'].transform(
            np.array([[pair['stm32'][feat] for feat in self.pls_results['feature_names']] 
                     for pair in self.matched_pairs])
        )
        
        X_scores = pls.transform(X_scaled)
        concentrations = self.pls_results['concentrations']
        
        if X_scores.shape[1] >= 2:
            scatter = ax1.scatter(X_scores[:, 0], X_scores[:, 1], c=concentrations, cmap='viridis', s=60)
            ax1.set_xlabel('PC1 Scores')
            ax1.set_ylabel('PC2 Scores')
            ax1.set_title('PLS Scores Plot')
            plt.colorbar(scatter, ax=ax1, label='Concentration (mM)')
            ax1.grid(True, alpha=0.3)
        
        # 2-7. Predicted vs Actual for key features
        key_features = ['ox_voltage', 'ox_current', 'red_voltage', 'red_current', 'peak_separation_voltage', 'current_ratio']
        
        for i, feat in enumerate(key_features):
            ax = plt.subplot(3, 3, i+2)
            feat_idx = self.pls_results['feature_names'].index(feat)
            
            y_true = self.pls_results['predictions']['Y_true'][:, feat_idx]
            y_pred = self.pls_results['predictions']['Y_pred'][:, feat_idx]
            
            ax.scatter(y_true, y_pred, alpha=0.7, s=50)
            
            # Perfect correlation line
            min_val = min(y_true.min(), y_pred.min())
            max_val = max(y_true.max(), y_pred.max())
            ax.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.8, linewidth=2)
            
            # R² annotation
            r2 = self.pls_results['metrics'][feat]['r2']
            ax.text(0.05, 0.95, f'R² = {r2:.3f}', transform=ax.transAxes, 
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            ax.set_xlabel(f'Palmsens {feat}')
            ax.set_ylabel(f'STM32 Predicted {feat}')
            ax.set_title(f'{feat.replace("_", " ").title()}')
            ax.grid(True, alpha=0.3)
        
        # 8. Overall R² comparison
        ax8 = plt.subplot(3, 3, 8)
        features = list(self.pls_results['metrics'].keys())
        r2_values = [self.pls_results['metrics'][feat]['r2'] for feat in features]
        
        bars = ax8.bar(range(len(features)), r2_values, alpha=0.7)
        ax8.set_xlabel('Features')
        ax8.set_ylabel('R² Score')
        ax8.set_title('Feature-wise R² Performance')
        ax8.set_xticks(range(len(features)))
        ax8.set_xticklabels([f.replace('_', '\\n') for f in features], rotation=45, ha='right')
        ax8.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, r2 in zip(bars, r2_values):
            height = bar.get_height()
            ax8.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{r2:.3f}', ha='center', va='bottom')
        
        # 9. Cross-validation results
        ax9 = plt.subplot(3, 3, 9)
        cv_scores = self.pls_results['cv_scores']
        ax9.boxplot(cv_scores)
        ax9.set_ylabel('Cross-validation R²')
        ax9.set_title('Cross-validation Performance')
        ax9.grid(True, alpha=0.3)
        
        # Add statistics
        ax9.text(0.5, 0.95, f'Mean: {cv_scores.mean():.3f}\\nStd: {cv_scores.std():.3f}', 
                transform=ax9.transAxes, ha='center', va='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        # Save plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_path = self.output_dir / f"pls_comparison_analysis_{timestamp}.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        
        print(f"📊 PLS visualization saved: {plot_path}")
        plt.show()
        
        return plot_path
    
    def export_results(self):
        """Export all results in multiple formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. CSV export of matched pairs
        if self.matched_pairs:
            csv_data = []
            for pair in self.matched_pairs:
                row = {
                    'concentration': pair['concentration'],
                    'scan_rate': pair['scan_rate'],
                    'electrode': pair['electrode']
                }
                
                # Add Palmsens data
                for key, value in pair['palmsens'].items():
                    row[f'palmsens_{key}'] = value
                
                # Add STM32 data  
                for key, value in pair['stm32'].items():
                    row[f'stm32_{key}'] = value
                
                csv_data.append(row)
            
            df = pd.DataFrame(csv_data)
            csv_path = self.output_dir / f"pls_matched_pairs_{timestamp}.csv"
            df.to_csv(csv_path, index=False)
            print(f"📄 Matched pairs CSV: {csv_path}")
        
        # 2. PLS results JSON
        if hasattr(self, 'pls_results'):
            export_data = {
                'timestamp': timestamp,
                'statistics': self.stats,
                'pls_metrics': self.pls_results['metrics'],
                'cv_scores': self.pls_results['cv_scores'].tolist(),
                'feature_names': self.pls_results['feature_names'],
                'n_components': self.pls_results['model'].n_components,
                'analysis_summary': {
                    'total_matched_pairs': len(self.matched_pairs),
                    'mean_cv_r2': float(self.pls_results['cv_scores'].mean()),
                    'std_cv_r2': float(self.pls_results['cv_scores'].std())
                }
            }
            
            json_path = self.output_dir / f"pls_results_{timestamp}.json"
            with open(json_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            print(f"📋 PLS results JSON: {json_path}")
        
        # 3. Summary report
        report_path = self.output_dir / f"pls_summary_report_{timestamp}.txt"
        with open(report_path, 'w') as f:
            f.write("PLS Analysis Report: Palmsens vs STM32 Potentiostat Comparison\\n")
            f.write("=" * 60 + "\\n\\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Method: Enhanced Detector V4 Improved\\n\\n")
            
            f.write("Data Statistics:\\n")
            f.write(f"  Palmsens files: {self.stats['palmsens']['success']}/{self.stats['palmsens']['total']}\\n")
            f.write(f"  STM32 files: {self.stats['stm32']['success']}/{self.stats['stm32']['total']}\\n")
            f.write(f"  Matched pairs: {self.stats['matched_pairs']}\\n\\n")
            
            if hasattr(self, 'pls_results'):
                f.write("PLS Performance:\\n")
                f.write(f"  Cross-validation R²: {self.pls_results['cv_scores'].mean():.3f} ± {self.pls_results['cv_scores'].std():.3f}\\n")
                f.write(f"  Number of components: {self.pls_results['model'].n_components}\\n\\n")
                
                f.write("Feature Performance:\\n")
                for feat, metrics in self.pls_results['metrics'].items():
                    f.write(f"  {feat}: R²={metrics['r2']:.3f}, RMSE={metrics['rmse']:.4f}\\n")
        
        print(f"📝 Summary report: {report_path}")
        
        return {
            'csv': csv_path if self.matched_pairs else None,
            'json': json_path if hasattr(self, 'pls_results') else None,
            'report': report_path
        }
    
    def run_complete_analysis(self, palmsens_dir="Test_data/Palmsens", stm32_dir="Test_data/Stm32"):
        """Run complete PLS comparison analysis"""
        print("🚀 Starting Complete PLS Potentiostat Comparison")
        print("=" * 60)
        
        if not HAS_ENHANCED_V4:
            print("❌ Enhanced Detector V4 Improved not available")
            return None
        
        start_time = time.time()
        
        # 1. Load Palmsens data
        print("\\n📊 Step 1: Loading Palmsens (Reference) Data")
        self.palmsens_data = self.load_device_data(palmsens_dir, "Palmsens")
        
        # 2. Load STM32 data
        print("\\n📊 Step 2: Loading STM32 (Target) Data")
        self.stm32_data = self.load_device_data(stm32_dir, "STM32")
        
        # 3. Match measurement pairs
        print("\\n📊 Step 3: Matching Measurement Pairs")
        matched_pairs = self.match_measurement_pairs()
        
        if not matched_pairs:
            print("❌ No matched pairs found. Cannot proceed with PLS analysis.")
            return None
        
        # 4. PLS analysis
        print("\\n📊 Step 4: PLS Regression Analysis")
        pls_results = self.perform_pls_analysis()
        
        # 5. Visualization
        print("\\n📊 Step 5: Creating Visualizations")
        plot_path = self.create_pls_visualizations()
        
        # 6. Export results
        print("\\n📊 Step 6: Exporting Results")
        exports = self.export_results()
        
        total_time = time.time() - start_time
        
        # Final summary
        print(f"\\n🎉 Analysis Complete!")
        print(f"⏱️  Total time: {total_time:.2f} seconds")
        print(f"📁 Results saved in: {self.output_dir}")
        print(f"\\n📈 Key Results:")
        if hasattr(self, 'pls_results'):
            cv_r2 = self.pls_results['cv_scores'].mean()
            print(f"  Cross-validation R²: {cv_r2:.3f}")
            print(f"  Data pairs analyzed: {len(self.matched_pairs)}")
            print(f"  Overall correlation: {'Excellent' if cv_r2 > 0.9 else 'Good' if cv_r2 > 0.8 else 'Moderate'}")
        
        return {
            'pls_results': pls_results,
            'matched_pairs': matched_pairs,
            'statistics': self.stats,
            'exports': exports,
            'processing_time': total_time
        }

def main():
    """Main execution function"""
    if not HAS_ENHANCED_V4:
        print("❌ Enhanced Detector V4 Improved required for this analysis")
        return
    
    # Create analysis instance
    analyzer = PLSPotentiostatComparison()
    
    # Run complete analysis
    results = analyzer.run_complete_analysis()
    
    if results:
        print("\\n✅ PLS comparison analysis completed successfully!")
    else:
        print("\\n❌ PLS comparison analysis failed!")

if __name__ == "__main__":
    main()
