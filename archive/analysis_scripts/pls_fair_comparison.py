#!/usr/bin/env python3
"""
PLS Fair Comparison Analysis
เปรียบเทียบ Palmsens vs STM32 ที่ความเข้มข้นเท่ากัน
"""

import glob
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, confusion_matrix, classification_report
from sklearn.metrics import accuracy_score, precision_score, recall_score
import json
import requests
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import advanced visualizer
try:
    from advanced_pls_visualizer import AdvancedPLSVisualizer, create_classification_report_plot
    ADVANCED_PLOTS_AVAILABLE = True
except ImportError:
    ADVANCED_PLOTS_AVAILABLE = False
    print("⚠️ Advanced visualizer not available, using basic plots")

class FairPLSComparison:
    def __init__(self, concentration='10mM'):
        self.concentration = concentration
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results_dir = f'pls_fair_results_{concentration.replace(".", "_")}'
        Path(self.results_dir).mkdir(exist_ok=True)
        
        # Enhanced V4 Improved settings
        self.peak_detector_url = 'http://localhost:8080/api/enhanced_v4_improved_analysis'
        self.detector_params = {
            'confidence_threshold': 25.0,
            'min_peak_distance': 10,
            'baseline_method': 'als'
        }
        
        print(f"🎯 Fair PLS Comparison Analysis - {concentration}")
        print(f"📁 Results directory: {self.results_dir}")
        
    def collect_data(self, limit_per_device=100):
        """รวบรวมข้อมูลจากทั้งสองอุปกรณ์ที่ความเข้มข้นเท่ากัน"""
        
        print(f"\n📊 Collecting {self.concentration} data...")
        
        # Palmsens files
        pal_pattern = f'Test_data/Palmsens/Palmsens_{self.concentration}/*.csv'
        pal_files = [f for f in glob.glob(pal_pattern) if 'scan_01' not in f][:limit_per_device]
        
        # STM32 files  
        stm32_pattern = f'Test_data/Stm32/Pipot_{self.concentration}/*.csv'
        stm32_files = [f for f in glob.glob(stm32_pattern) if 'scan_01' not in f][:limit_per_device]
        
        print(f"  Palmsens: {len(pal_files)} files")
        print(f"  STM32: {len(stm32_files)} files")
        print(f"  Total: {len(pal_files) + len(stm32_files)} files")
        
        return pal_files, stm32_files
    
    def analyze_with_enhanced_v4(self, file_path):
        """วิเคราะห์ไฟล์ด้วย Enhanced Detector V4 Improved"""
        try:
            # Read CSV file
            import pandas as pd
            df = pd.read_csv(file_path, skiprows=1)
            
            # Get voltage and current data
            if 'V' in df.columns and 'uA' in df.columns:
                voltage = df['V'].values.tolist()
                current = df['uA'].values.tolist()
            elif 'Voltage' in df.columns and 'Current' in df.columns:
                voltage = df['Voltage'].values.tolist()
                current = df['Current'].values.tolist()
            else:
                return {'success': False, 'error': 'Unknown CSV format', 'file_path': file_path}
            
            # Prepare payload for Enhanced V4 Improved API
            payload = {
                'dataFiles': [{
                    'voltage': voltage,
                    'current': current,
                    'filename': Path(file_path).name
                }]
            }
            
            response = requests.post(self.peak_detector_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('results'):
                    # Get first file result
                    file_result = result['results'][0]
                    if file_result.get('success') and len(file_result.get('peaks', [])) >= 2:
                        peaks = file_result['peaks']
                        return {
                            'ox_voltage': peaks[0]['voltage'],
                            'ox_current': peaks[0]['current'], 
                            'red_voltage': peaks[1]['voltage'],
                            'red_current': peaks[1]['current'],
                            'peak_separation': abs(peaks[0]['voltage'] - peaks[1]['voltage']),
                            'file_path': file_path,
                            'success': True
                        }
            
            return {'success': False, 'error': 'Insufficient peaks', 'file_path': file_path}
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'file_path': file_path}
    
    def process_device_data(self, files, device_name):
        """ประมวลผลข้อมูลจากอุปกรณ์หนึ่ง"""
        print(f"\n🔬 Processing {device_name} data...")
        
        results = []
        success_count = 0
        
        for i, file_path in enumerate(files):
            if i % 20 == 0:
                print(f"  Progress: {i+1}/{len(files)}")
            
            result = self.analyze_with_enhanced_v4(file_path)
            
            if result['success']:
                result['device'] = device_name
                result['concentration'] = self.concentration
                results.append(result)
                success_count += 1
        
        success_rate = (success_count / len(files)) * 100
        print(f"  ✅ Success: {success_count}/{len(files)} ({success_rate:.1f}%)")
        
        return results
    
    def run_pls_analysis(self, data):
        """รัน PLS Analysis"""
        print(f"\n🧮 Running PLS Analysis...")
        
        df = pd.DataFrame(data)
        
        # เตรียมข้อมูล
        features = ['ox_voltage', 'ox_current', 'red_voltage', 'red_current', 'peak_separation']
        X = df[features].values
        y = (df['device'] == 'STM32').astype(int)  # 0=Palmsens, 1=STM32
        
        # Standardize
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # PLS Regression
        pls = PLSRegression(n_components=2, scale=False)
        pls.fit(X_scaled, y)
        
        # Predictions
        y_pred = pls.predict(X_scaled).flatten()
        
        # Cross-validation
        cv_scores = cross_val_score(pls, X_scaled, y, cv=5, scoring='r2')
        
        # Statistics
        r2 = r2_score(y, y_pred)
        mse = mean_squared_error(y, y_pred)
        
        results = {
            'r2_score': r2,
            'mse': mse, 
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'feature_importance': dict(zip(features, abs(pls.coef_.flatten()))),
            'loadings': pls.x_loadings_.tolist(),
            'total_samples': len(data),
            'concentration': self.concentration
        }
        
        print(f"  📈 R² Score: {r2:.4f}")
        print(f"  📉 MSE: {mse:.6f}")
        print(f"  🔄 CV Score: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        
        return results, df, pls, scaler
    
    def create_visualization(self, df, pls_results, pls_model, scaler):
        """สร้างกราฟเปรียบเทียบแบบครอบคลุม"""
        
        fig, axes = plt.subplots(3, 2, figsize=(16, 18))
        fig.suptitle(f'Comprehensive PLS Analysis: Palmsens vs STM32 at {self.concentration}', 
                    fontsize=16, fontweight='bold')
        
        # เตรียมข้อมูล
        features = ['ox_voltage', 'ox_current', 'red_voltage', 'red_current', 'peak_separation']
        X = df[features].values
        y = (df['device'] == 'STM32').astype(int)
        X_scaled = scaler.transform(X)
        
        # PLS scores และ predictions
        X_scores = pls_model.x_scores_
        y_pred = pls_model.predict(X_scaled).flatten()
        
        # Device statistics
        pal_data = df[df['device'] == 'Palmsens']
        stm32_data = df[df['device'] == 'STM32']
        
        # 1. PLS Score Plot (PC1 vs PC2)
        pal_mask = (df['device'] == 'Palmsens')
        stm32_mask = (df['device'] == 'STM32')
        
        axes[0,0].scatter(X_scores[pal_mask, 0], X_scores[pal_mask, 1], 
                         alpha=0.7, label='Palmsens', color='blue', s=50)
        axes[0,0].scatter(X_scores[stm32_mask, 0], X_scores[stm32_mask, 1], 
                         alpha=0.7, label='STM32', color='red', s=50)
        axes[0,0].set_xlabel('PC1 (First Component)')
        axes[0,0].set_ylabel('PC2 (Second Component)')
        axes[0,0].set_title('PLS Score Plot - Sample Separation')
        axes[0,0].legend()
        axes[0,0].grid(True, alpha=0.3)
        
        # Add explained variance
        var_explained = pls_model.score(X_scaled, y) * 100
        axes[0,0].text(0.02, 0.98, f'Model Score: {var_explained:.1f}%', 
                      transform=axes[0,0].transAxes, va='top', 
                      bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # 2. Prediction vs Actual
        axes[0,1].scatter(y, y_pred, alpha=0.6, color='green', s=50)
        axes[0,1].plot([0, 1], [0, 1], 'r--', linewidth=2, label='Perfect Prediction')
        axes[0,1].set_xlabel('Actual (0=Palmsens, 1=STM32)')
        axes[0,1].set_ylabel('Predicted')
        axes[0,1].set_title('Prediction vs Actual Values')
        axes[0,1].legend()
        axes[0,1].grid(True, alpha=0.3)
        
        # Add R² score
        r2 = pls_results['r2_score']
        axes[0,1].text(0.02, 0.98, f'R² = {r2:.4f}', 
                      transform=axes[0,1].transAxes, va='top',
                      bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        # 3. Feature Importance (VIP-style)
        features_display = ['Ox Voltage', 'Ox Current', 'Red Voltage', 'Red Current', 'Peak Sep.']
        importance = list(pls_results['feature_importance'].values())
        
        bars = axes[1,0].bar(features_display, importance, 
                           color=['skyblue', 'lightcoral', 'lightgreen', 'gold', 'plum'])
        axes[1,0].set_title('Feature Importance (PLS Coefficients)')
        axes[1,0].set_ylabel('Absolute Coefficient Value')
        axes[1,0].tick_params(axis='x', rotation=45)
        
        # Add significance line at arbitrary threshold
        axes[1,0].axhline(y=np.mean(importance), color='red', linestyle='--', 
                         alpha=0.7, label='Mean Importance')
        axes[1,0].legend()
        
        # Add value labels on bars
        for bar, val in zip(bars, importance):
            height = bar.get_height()
            axes[1,0].text(bar.get_x() + bar.get_width()/2., height,
                          f'{val:.3f}', ha='center', va='bottom')
        
        # 4. Device Comparison - Oxidation Voltage
        bp1 = axes[1,1].boxplot([pal_data['ox_voltage'], stm32_data['ox_voltage']], 
                               labels=['Palmsens', 'STM32'], patch_artist=True)
        bp1['boxes'][0].set_facecolor('lightblue')
        bp1['boxes'][1].set_facecolor('lightcoral')
        axes[1,1].set_title('Oxidation Voltage Distribution')
        axes[1,1].set_ylabel('Voltage (V)')
        axes[1,1].grid(True, alpha=0.3)
        
        # Add statistical info
        pal_mean = pal_data['ox_voltage'].mean()
        stm32_mean = stm32_data['ox_voltage'].mean()
        axes[1,1].text(0.02, 0.98, f'Palmsens: {pal_mean:.3f}V\\nSTM32: {stm32_mean:.3f}V', 
                      transform=axes[1,1].transAxes, va='top',
                      bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # 5. Cross-validation Results
        cv_scores = [pls_results['cv_mean'] - pls_results['cv_std'],
                    pls_results['cv_mean'],
                    pls_results['cv_mean'] + pls_results['cv_std']]
        
        axes[2,0].bar(['CV-STD', 'CV Mean', 'CV+STD'], cv_scores, 
                     color=['lightblue', 'blue', 'lightblue'])
        axes[2,0].set_title('Cross-Validation Performance')
        axes[2,0].set_ylabel('R² Score')
        axes[2,0].grid(True, alpha=0.3)
        
        # Add value labels
        for i, val in enumerate(cv_scores):
            axes[2,0].text(i, val, f'{val:.3f}', ha='center', va='bottom')
        
        # 6. Peak Separation Analysis
        axes[2,1].scatter(pal_data['ox_voltage'], pal_data['peak_separation'], 
                         alpha=0.6, label='Palmsens', color='blue')
        axes[2,1].scatter(stm32_data['ox_voltage'], stm32_data['peak_separation'], 
                         alpha=0.6, label='STM32', color='red')
        axes[2,1].set_xlabel('Oxidation Voltage (V)')
        axes[2,1].set_ylabel('Peak Separation (V)')
        axes[2,1].set_title('Oxidation Voltage vs Peak Separation')
        axes[2,1].legend()
        axes[2,1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        plot_path = f'{self.results_dir}/comprehensive_pls_analysis_{self.concentration}_{self.timestamp}.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        print(f"📊 Comprehensive visualization saved: {plot_path}")
        
        return plot_path
    
    def generate_statistics_summary(self, df):
        """สร้างสรุปสถิติ"""
        
        summary = {}
        
        for device in ['Palmsens', 'STM32']:
            device_data = df[df['device'] == device]
            
            summary[device] = {
                'count': len(device_data),
                'ox_voltage_mean': device_data['ox_voltage'].mean(),
                'ox_voltage_std': device_data['ox_voltage'].std(),
                'red_voltage_mean': device_data['red_voltage'].mean(), 
                'red_voltage_std': device_data['red_voltage'].std(),
                'peak_separation_mean': device_data['peak_separation'].mean(),
                'peak_separation_std': device_data['peak_separation'].std(),
                'ox_current_mean': device_data['ox_current'].mean(),
                'ox_current_std': device_data['ox_current'].std()
            }
        
        return summary
    
    def export_labplot2_format(self, df):
        """Export ข้อมูลในรูปแบบ LabPlot2"""
        
        # เตรียมข้อมูลสำหรับ LabPlot2
        export_df = df.copy()
        export_df['device_code'] = (export_df['device'] == 'STM32').astype(int)
        
        # เรียงลำดับคอลัมน์
        columns = ['device', 'device_code', 'concentration', 'ox_voltage', 'ox_current', 
                  'red_voltage', 'red_current', 'peak_separation', 'file_path']
        export_df = export_df[columns]
        
        # สร้างไฟล์ CSV พร้อม metadata header
        labplot_path = f'{self.results_dir}/labplot2_fair_comparison_{self.concentration}_{self.timestamp}.csv'
        
        with open(labplot_path, 'w') as f:
            # เขียน metadata header
            f.write(f"# Fair PLS Comparison Data - {self.concentration}\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n") 
            f.write(f"# Concentration: {self.concentration}\n")
            f.write(f"# Total samples: {len(export_df)}\n")
            f.write(f"# Palmsens samples: {len(export_df[export_df['device']=='Palmsens'])}\n")
            f.write(f"# STM32 samples: {len(export_df[export_df['device']=='STM32'])}\n")
            f.write("# Device codes: 0=Palmsens, 1=STM32\n")
            f.write("# Detector: Enhanced V4 Improved\n")
            f.write("#\n")
            
            # เขียนข้อมูล
            export_df.to_csv(f, index=False)
        
        print(f"📄 LabPlot2 data exported: {labplot_path}")
        return labplot_path
    
    def save_device_csv(self, df, device_name):
        """บันทึกข้อมูลแยกตามอุปกรณ์"""
        device_data = df[df['device'] == device_name]
        csv_path = f'{self.results_dir}/{device_name.lower()}_data_{self.concentration}_{self.timestamp}.csv'
        device_data.to_csv(csv_path, index=False)
        print(f"💾 {device_name} data saved: {csv_path}")
        return csv_path
    
    def run_complete_analysis(self):
        """รันการวิเคราะห์ครบถ้วน"""
        start_time = datetime.now()
        
        print(f"🚀 Starting Fair PLS Comparison Analysis at {self.concentration}")
        print("=" * 60)
        
        # 1. Collect data
        pal_files, stm32_files = self.collect_data()
        
        # 2. Process both devices
        all_results = []
        
        pal_results = self.process_device_data(pal_files, 'Palmsens')
        all_results.extend(pal_results)
        
        stm32_results = self.process_device_data(stm32_files, 'STM32')
        all_results.extend(stm32_results)
        
        if len(all_results) < 20:
            print("❌ Error: Insufficient data for analysis")
            return
        
        # 3. PLS Analysis
        pls_results, df, pls_model, scaler = self.run_pls_analysis(all_results)
        
        # 4. Generate statistics
        stats_summary = self.generate_statistics_summary(df)
        
        # 5. Create visualization
        plot_path = self.create_visualization(df, pls_results, pls_model, scaler)
        
        # 5.5. Create advanced PLS plots (if available)
        advanced_plot_path = None
        classification_plot_path = None
        
        if ADVANCED_PLOTS_AVAILABLE:
            try:
                features = ['ox_voltage', 'ox_current', 'red_voltage', 'red_current', 'peak_separation']
                feature_names = ['Ox Voltage', 'Ox Current', 'Red Voltage', 'Red Current', 'Peak Sep.']
                device_names = ['Palmsens', 'STM32']
                
                X = df[features].values
                y = (df['device'] == 'STM32').astype(int)
                X_scaled = scaler.transform(X)
                
                # Advanced PLS visualizer
                visualizer = AdvancedPLSVisualizer(pls_model, X_scaled, y, feature_names, device_names)
                
                advanced_plot_path = f'{self.results_dir}/advanced_pls_plots_{self.concentration}_{self.timestamp}.png'
                visualizer.create_comprehensive_plot(save_path=advanced_plot_path)
                
                # Classification report plot
                y_pred = pls_model.predict(X_scaled).flatten()
                classification_plot_path = f'{self.results_dir}/classification_report_{self.concentration}_{self.timestamp}.png'
                create_classification_report_plot(y, y_pred, device_names, classification_plot_path)
                
                print(f"📊 Advanced PLS visualizations created!")
                
            except Exception as e:
                print(f"⚠️ Advanced plots failed: {e}")
                advanced_plot_path = None
                classification_plot_path = None
        
        # 6. Export data
        labplot_path = self.export_labplot2_format(df)
        pal_csv = self.save_device_csv(df, 'Palmsens')
        stm32_csv = self.save_device_csv(df, 'STM32')
        
        # 7. Save comprehensive report
        report = {
            'metadata': {
                'concentration': self.concentration,
                'timestamp': self.timestamp,
                'analysis_type': 'Fair PLS Comparison',
                'detector': 'Enhanced V4 Improved',
                'processing_time': str(datetime.now() - start_time)
            },
            'data_summary': {
                'total_samples': len(all_results),
                'palmsens_samples': len([r for r in all_results if r['device'] == 'Palmsens']),
                'stm32_samples': len([r for r in all_results if r['device'] == 'STM32'])
            },
            'pls_results': pls_results,
            'device_statistics': stats_summary,
            'output_files': {
                'basic_visualization': plot_path,
                'advanced_pls_plots': advanced_plot_path,
                'classification_report': classification_plot_path,
                'labplot2_data': labplot_path,
                'palmsens_csv': pal_csv,
                'stm32_csv': stm32_csv
            }
        }
        
        report_path = f'{self.results_dir}/fair_comparison_report_{self.concentration}_{self.timestamp}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # 8. Final summary
        processing_time = datetime.now() - start_time
        
        print("\n" + "=" * 60)
        print("🎉 Fair PLS Comparison Analysis Complete!")
        print(f"⏱️  Processing time: {processing_time}")
        print(f"📁 Results directory: {self.results_dir}")
        print(f"📊 Total samples analyzed: {len(all_results)}")
        print(f"🎯 PLS R² Score: {pls_results['r2_score']:.4f}")
        print(f"📄 Report saved: {report_path}")
        
        return report


def main():
    """หลักการใช้งาน"""
    
    print("🎯 Fair PLS Comparison Tool")
    print("🎯 Running analysis at 10mM concentration (recommended)")
    print("📊 Available options: 5mM (500), 10mM (505), 20mM (550) samples")
    
    # ใช้ 10mM เป็นค่า default
    concentration = '10mM'
    
    # รัน analysis
    analyzer = FairPLSComparison(concentration=concentration)
    report = analyzer.run_complete_analysis()
    
    return report


if __name__ == "__main__":
    report = main()
