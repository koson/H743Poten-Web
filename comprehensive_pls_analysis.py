#!/usr/bin/env python3
"""
Comprehensive Multi-Concentration PLS Analysis
การวิเคราะห์ PLS แบบครอบคลุมที่ใช้หลายความเข้มข้น
"""

import glob
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import json
import requests
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class ComprehensivePLSAnalysis:
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results_dir = f'comprehensive_pls_results_{self.timestamp}'
        Path(self.results_dir).mkdir(exist_ok=True)
        
        # Enhanced V4 Improved settings
        self.peak_detector_url = 'http://localhost:8080/api/enhanced_v4_improved_analysis'
        
        print(f"🎯 Comprehensive Multi-Concentration PLS Analysis")
        print(f"📁 Results directory: {self.results_dir}")
        
    def collect_multi_concentration_data(self, limit_per_concentration=50):
        """รวบรวมข้อมูลจากหลายความเข้มข้น"""
        
        print(f"\n📊 Collecting multi-concentration data...")
        
        # Available concentrations
        concentrations = ['0.5mM', '1mM', '5mM', '10mM', '20mM', '50mM']
        
        all_data = []
        summary = {}
        
        for conc in concentrations:
            print(f"\n🔬 Processing {conc}...")
            
            # Palmsens files
            pal_pattern = f'Test_data/Palmsens/Palmsens_{conc}/*.csv'
            pal_files = [f for f in glob.glob(pal_pattern) if 'scan_01' not in f][:limit_per_concentration]
            
            # STM32 files  
            stm32_pattern = f'Test_data/Stm32/Pipot_{conc}/*.csv'
            stm32_files = [f for f in glob.glob(stm32_pattern) if 'scan_01' not in f][:limit_per_concentration]
            
            print(f"  📁 Palmsens: {len(pal_files)} files")
            print(f"  📁 STM32: {len(stm32_files)} files")
            
            # Process files
            pal_results = self.process_device_data(pal_files, 'Palmsens', conc)
            stm32_results = self.process_device_data(stm32_files, 'STM32', conc)
            
            # Combine results
            conc_data = pal_results + stm32_results
            all_data.extend(conc_data)
            
            summary[conc] = {
                'palmsens_count': len(pal_results),
                'stm32_count': len(stm32_results),
                'total_count': len(conc_data)
            }
        
        print(f"\n📈 Data collection summary:")
        total_samples = 0
        for conc, counts in summary.items():
            total = counts['total_count']
            total_samples += total
            print(f"  {conc}: {total} samples ({counts['palmsens_count']} + {counts['stm32_count']})")
        
        print(f"🎯 Total samples: {total_samples}")
        
        return all_data, summary
    
    def analyze_with_enhanced_v4(self, file_path):
        """วิเคราะห์ไฟล์ด้วย Enhanced Detector V4 Improved"""
        try:
            # Read CSV file
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
            
            # Extract scan rate from filename
            scan_rate = self.extract_scan_rate(Path(file_path).name)
            
            # Prepare payload
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
                    file_result = result['results'][0]
                    if file_result.get('success') and len(file_result.get('peaks', [])) >= 2:
                        peaks = file_result['peaks']
                        return {
                            'ox_voltage': peaks[0]['voltage'],
                            'ox_current': peaks[0]['current'], 
                            'red_voltage': peaks[1]['voltage'],
                            'red_current': peaks[1]['current'],
                            'peak_separation': abs(peaks[0]['voltage'] - peaks[1]['voltage']),
                            'scan_rate': scan_rate,
                            'file_path': file_path,
                            'success': True
                        }
            
            return {'success': False, 'error': 'Insufficient peaks', 'file_path': file_path}
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'file_path': file_path}
    
    def extract_scan_rate(self, filename):
        """สกัด scan rate จากชื่อไฟล์"""
        import re
        
        # Pattern สำหรับ scan rate
        patterns = [
            r'(\d+)mVpS',  # 100mVpS
            r'(\d+)mV_s',  # 100mV_s
            r'(\d+)mVs',   # 100mVs
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return int(match.group(1))
        
        return 100  # default scan rate
    
    def extract_concentration_value(self, concentration_str):
        """แปลงความเข้มข้นเป็นตัวเลข (mM)"""
        import re
        match = re.search(r'([0-9.]+)', concentration_str)
        if match:
            return float(match.group(1))
        return 1.0  # default
    
    def process_device_data(self, files, device_name, concentration):
        """ประมวลผลข้อมูลจากอุปกรณ์หนึ่ง"""
        results = []
        success_count = 0
        
        for file_path in files:
            result = self.analyze_with_enhanced_v4(file_path)
            
            if result['success']:
                result['device'] = device_name
                result['concentration_str'] = concentration
                result['concentration'] = self.extract_concentration_value(concentration)
                results.append(result)
                success_count += 1
        
        return results
    
    def run_comprehensive_pls_analysis(self, data):
        """รัน PLS Analysis แบบครอบคลุม"""
        print(f"\n🧮 Running Comprehensive PLS Analysis...")
        
        df = pd.DataFrame(data)
        
        # Feature engineering
        features = ['ox_voltage', 'ox_current', 'red_voltage', 'red_current', 
                   'peak_separation', 'concentration', 'scan_rate']
        X = df[features].values
        
        # Multiple target variables
        y_device = (df['device'] == 'STM32').astype(int)  # Device classification
        y_concentration = df['concentration'].values      # Concentration regression
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        print(f"📊 Features: {len(features)}")
        print(f"📊 Samples: {len(df)}")
        print(f"📊 Concentrations: {sorted(df['concentration'].unique())}")
        print(f"📊 Devices: {df['device'].value_counts().to_dict()}")
        
        # 1. Device Classification PLS
        print(f"\n🎯 Device Classification PLS...")
        pls_device = PLSRegression(n_components=3, scale=False)
        pls_device.fit(X_scaled, y_device)
        
        y_device_pred = pls_device.predict(X_scaled).flatten()
        device_r2 = r2_score(y_device, y_device_pred)
        device_cv = cross_val_score(pls_device, X_scaled, y_device, cv=5, scoring='r2')
        
        print(f"  📈 Device R²: {device_r2:.4f}")
        print(f"  🔄 Device CV: {device_cv.mean():.4f} ± {device_cv.std():.4f}")
        
        # 2. Concentration Prediction PLS
        print(f"\n🎯 Concentration Prediction PLS...")
        pls_conc = PLSRegression(n_components=3, scale=False)
        pls_conc.fit(X_scaled, y_concentration)
        
        y_conc_pred = pls_conc.predict(X_scaled).flatten()
        conc_r2 = r2_score(y_concentration, y_conc_pred)
        conc_mae = mean_absolute_error(y_concentration, y_conc_pred)
        conc_cv = cross_val_score(pls_conc, X_scaled, y_concentration, cv=5, scoring='r2')
        
        print(f"  📈 Concentration R²: {conc_r2:.4f}")
        print(f"  📉 Concentration MAE: {conc_mae:.4f} mM")
        print(f"  🔄 Concentration CV: {conc_cv.mean():.4f} ± {conc_cv.std():.4f}")
        
        # Feature importance
        device_importance = dict(zip(features, abs(pls_device.coef_.flatten())))
        conc_importance = dict(zip(features, abs(pls_conc.coef_.flatten())))
        
        results = {
            'device_classification': {
                'r2_score': device_r2,
                'cv_mean': device_cv.mean(),
                'cv_std': device_cv.std(),
                'feature_importance': device_importance,
                'predictions': y_device_pred.tolist()
            },
            'concentration_prediction': {
                'r2_score': conc_r2,
                'mae': conc_mae,
                'cv_mean': conc_cv.mean(),
                'cv_std': conc_cv.std(),
                'feature_importance': conc_importance,
                'predictions': y_conc_pred.tolist()
            },
            'total_samples': len(data),
            'features_used': features
        }
        
        return results, df, pls_device, pls_conc, scaler
    
    def create_comprehensive_visualization(self, df, results, pls_device, pls_conc, scaler):
        """สร้างกราฟวิเคราะห์แบบครอบคลุม"""
        
        fig, axes = plt.subplots(3, 3, figsize=(20, 15))
        fig.suptitle('Comprehensive Multi-Concentration PLS Analysis', fontsize=16, fontweight='bold')
        
        features = ['ox_voltage', 'ox_current', 'red_voltage', 'red_current', 
                   'peak_separation', 'concentration', 'scan_rate']
        X = df[features].values
        X_scaled = scaler.transform(X)
        
        # Device and concentration variables
        y_device = (df['device'] == 'STM32').astype(int)
        y_concentration = df['concentration'].values
        
        # Get predictions
        device_pred = pls_device.predict(X_scaled).flatten()
        conc_pred = pls_conc.predict(X_scaled).flatten()
        
        # 1. Device Classification Score Plot
        device_scores = pls_device.transform(X_scaled)
        for device in ['Palmsens', 'STM32']:
            mask = (df['device'] == device)
            color = 'blue' if device == 'Palmsens' else 'red'
            axes[0,0].scatter(device_scores[mask, 0], device_scores[mask, 1], 
                            alpha=0.6, label=device, color=color)
        axes[0,0].set_xlabel('PC1')
        axes[0,0].set_ylabel('PC2')
        axes[0,0].set_title('Device Classification - PLS Score Plot')
        axes[0,0].legend()
        axes[0,0].grid(True, alpha=0.3)
        
        # 2. Concentration Score Plot
        conc_scores = pls_conc.transform(X_scaled)
        scatter = axes[0,1].scatter(conc_scores[:, 0], conc_scores[:, 1], 
                                  c=y_concentration, cmap='viridis', alpha=0.7)
        axes[0,1].set_xlabel('PC1')
        axes[0,1].set_ylabel('PC2')
        axes[0,1].set_title('Concentration Prediction - PLS Score Plot')
        plt.colorbar(scatter, ax=axes[0,1], label='Concentration (mM)')
        axes[0,1].grid(True, alpha=0.3)
        
        # 3. Device Prediction vs Actual
        axes[0,2].scatter(y_device, device_pred, alpha=0.6, color='green')
        axes[0,2].plot([0, 1], [0, 1], 'r--', linewidth=2)
        axes[0,2].set_xlabel('Actual Device (0=Palmsens, 1=STM32)')
        axes[0,2].set_ylabel('Predicted')
        axes[0,2].set_title('Device Classification Performance')
        axes[0,2].grid(True, alpha=0.3)
        
        device_r2 = results['device_classification']['r2_score']
        axes[0,2].text(0.05, 0.95, f'R² = {device_r2:.4f}', transform=axes[0,2].transAxes,
                      bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        # 4. Concentration Prediction vs Actual
        axes[1,0].scatter(y_concentration, conc_pred, alpha=0.6, color='purple')
        min_conc, max_conc = y_concentration.min(), y_concentration.max()
        axes[1,0].plot([min_conc, max_conc], [min_conc, max_conc], 'r--', linewidth=2)
        axes[1,0].set_xlabel('Actual Concentration (mM)')
        axes[1,0].set_ylabel('Predicted Concentration (mM)')
        axes[1,0].set_title('Concentration Prediction Performance')
        axes[1,0].grid(True, alpha=0.3)
        
        conc_r2 = results['concentration_prediction']['r2_score']
        conc_mae = results['concentration_prediction']['mae']
        axes[1,0].text(0.05, 0.95, f'R² = {conc_r2:.4f}\\nMAE = {conc_mae:.2f} mM',
                      transform=axes[1,0].transAxes,
                      bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
        
        # 5. Device Feature Importance
        device_features = list(results['device_classification']['feature_importance'].keys())
        device_importance = list(results['device_classification']['feature_importance'].values())
        
        bars1 = axes[1,1].bar(device_features, device_importance, alpha=0.7, color='skyblue')
        axes[1,1].set_title('Device Classification - Feature Importance')
        axes[1,1].set_ylabel('Importance')
        axes[1,1].tick_params(axis='x', rotation=45)
        axes[1,1].grid(True, alpha=0.3)
        
        # 6. Concentration Feature Importance
        conc_features = list(results['concentration_prediction']['feature_importance'].keys())
        conc_importance = list(results['concentration_prediction']['feature_importance'].values())
        
        bars2 = axes[1,2].bar(conc_features, conc_importance, alpha=0.7, color='lightcoral')
        axes[1,2].set_title('Concentration Prediction - Feature Importance')
        axes[1,2].set_ylabel('Importance')
        axes[1,2].tick_params(axis='x', rotation=45)
        axes[1,2].grid(True, alpha=0.3)
        
        # 7. Concentration Distribution by Device
        for device in ['Palmsens', 'STM32']:
            device_data = df[df['device'] == device]
            axes[2,0].hist(device_data['concentration'], alpha=0.6, 
                          label=device, bins=20, color='blue' if device == 'Palmsens' else 'red')
        axes[2,0].set_xlabel('Concentration (mM)')
        axes[2,0].set_ylabel('Frequency')
        axes[2,0].set_title('Concentration Distribution by Device')
        axes[2,0].legend()
        axes[2,0].grid(True, alpha=0.3)
        
        # 8. Scan Rate vs Peak Separation
        scatter2 = axes[2,1].scatter(df['scan_rate'], df['peak_separation'], 
                                   c=df['concentration'], cmap='plasma', alpha=0.7)
        axes[2,1].set_xlabel('Scan Rate (mV/s)')
        axes[2,1].set_ylabel('Peak Separation (V)')
        axes[2,1].set_title('Scan Rate vs Peak Separation')
        plt.colorbar(scatter2, ax=axes[2,1], label='Concentration (mM)')
        axes[2,1].grid(True, alpha=0.3)
        
        # 9. Cross-validation Results
        cv_data = [
            results['device_classification']['cv_mean'],
            results['concentration_prediction']['cv_mean']
        ]
        cv_std = [
            results['device_classification']['cv_std'],
            results['concentration_prediction']['cv_std']
        ]
        
        x_pos = np.arange(len(['Device', 'Concentration']))
        bars3 = axes[2,2].bar(x_pos, cv_data, yerr=cv_std, alpha=0.7, 
                             color=['lightblue', 'lightgreen'], capsize=5)
        axes[2,2].set_xlabel('PLS Model')
        axes[2,2].set_ylabel('Cross-Validation R²')
        axes[2,2].set_title('Cross-Validation Performance')
        axes[2,2].set_xticks(x_pos)
        axes[2,2].set_xticklabels(['Device', 'Concentration'])
        axes[2,2].grid(True, alpha=0.3)
        
        # Add value labels
        for bar, val, std in zip(bars3, cv_data, cv_std):
            height = bar.get_height()
            axes[2,2].text(bar.get_x() + bar.get_width()/2., height,
                          f'{val:.3f}±{std:.3f}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Save plot
        plot_path = f'{self.results_dir}/comprehensive_pls_analysis_{self.timestamp}.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        print(f"📊 Comprehensive visualization saved: {plot_path}")
        
        return plot_path
    
    def export_comprehensive_data(self, df):
        """Export ข้อมูลแบบครอบคลุม"""
        
        # Export full dataset
        full_path = f'{self.results_dir}/comprehensive_dataset_{self.timestamp}.csv'
        df.to_csv(full_path, index=False)
        print(f"📄 Comprehensive dataset exported: {full_path}")
        
        # Export by device
        for device in ['Palmsens', 'STM32']:
            device_data = df[df['device'] == device]
            device_path = f'{self.results_dir}/{device.lower()}_comprehensive_{self.timestamp}.csv'
            device_data.to_csv(device_path, index=False)
        
        # Export by concentration
        for conc in sorted(df['concentration'].unique()):
            conc_data = df[df['concentration'] == conc]
            conc_path = f'{self.results_dir}/concentration_{conc}mM_{self.timestamp}.csv'
            conc_data.to_csv(conc_path, index=False)
        
        return full_path
    
    def run_complete_analysis(self):
        """รันการวิเคราะห์ครบถ้วน"""
        start_time = datetime.now()
        
        print(f"🚀 Starting Comprehensive Multi-Concentration PLS Analysis")
        print("=" * 70)
        
        # 1. Collect multi-concentration data
        all_data, summary = self.collect_multi_concentration_data()
        
        if len(all_data) < 50:
            print("❌ Error: Insufficient data for comprehensive analysis")
            return
        
        # 2. Run comprehensive PLS analysis
        results, df, pls_device, pls_conc, scaler = self.run_comprehensive_pls_analysis(all_data)
        
        # 3. Create visualization
        plot_path = self.create_comprehensive_visualization(df, results, pls_device, pls_conc, scaler)
        
        # 4. Export data
        data_path = self.export_comprehensive_data(df)
        
        # 5. Save comprehensive report
        report = {
            'metadata': {
                'timestamp': self.timestamp,
                'analysis_type': 'Comprehensive Multi-Concentration PLS',
                'detector': 'Enhanced V4 Improved',
                'processing_time': str(datetime.now() - start_time)
            },
            'data_summary': summary,
            'analysis_results': results,
            'output_files': {
                'visualization': plot_path,
                'comprehensive_data': data_path,
                'results_directory': self.results_dir
            }
        }
        
        report_path = f'{self.results_dir}/comprehensive_pls_report_{self.timestamp}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Final summary
        processing_time = datetime.now() - start_time
        
        print("\n" + "=" * 70)
        print("🎉 Comprehensive Multi-Concentration PLS Analysis Complete!")
        print(f"⏱️  Processing time: {processing_time}")
        print(f"📁 Results directory: {self.results_dir}")
        print(f"📊 Total samples: {len(all_data)}")
        print(f"🎯 Device Classification R²: {results['device_classification']['r2_score']:.4f}")
        print(f"🎯 Concentration Prediction R²: {results['concentration_prediction']['r2_score']:.4f}")
        print(f"📄 Report saved: {report_path}")
        
        return report


def main():
    """รันการวิเคราะห์ครบถ้วน"""
    
    print("🧪 Comprehensive Multi-Concentration PLS Analysis")
    print("📊 This analysis uses multiple concentrations and parameters")
    print("🎯 Objectives:")
    print("  1. Device Classification (Palmsens vs STM32)")
    print("  2. Concentration Prediction across devices")
    print("  3. Feature importance analysis")
    print("  4. Cross-validation performance")
    
    analyzer = ComprehensivePLSAnalysis()
    report = analyzer.run_complete_analysis()
    
    return report


if __name__ == "__main__":
    report = main()
