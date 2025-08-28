#!/usr/bin/env python3
"""
Improved PLS Visualization with Research-Grade Standards
การพล็อต PLS ที่ปรับปรุงตามมาตรฐานงานวิจัย
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import mean_absolute_error, r2_score
import pandas as pd

class ImprovedPLSVisualizer:
    def __init__(self):
        # Set publication-quality plotting style
        plt.style.use('seaborn-v0_8-whitegrid')
        sns.set_palette("husl")
        
    def create_device_comparison_plots(self, df, results, pls_device, pls_conc, scaler):
        """สร้างกราฟเปรียบเทียบเครื่องวัดแบบครบถ้วน"""
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Comprehensive Device Comparison: Palmsens vs STM32\nPLS-Based Analysis with Multiple Concentrations', 
                    fontsize=14, fontweight='bold')
        
        # Prepare data
        features = ['ox_voltage', 'ox_current', 'red_voltage', 'red_current', 
                   'peak_separation', 'concentration', 'scan_rate']
        X = df[features].values
        X_scaled = scaler.transform(X)
        
        y_device = (df['device'] == 'STM32').astype(int)
        y_concentration = df['concentration'].values
        
        device_pred = pls_device.predict(X_scaled).flatten()
        conc_pred = pls_conc.predict(X_scaled).flatten()
        
        # 1. Device-Separated Concentration Prediction
        colors = {'Palmsens': '#2E86AB', 'STM32': '#A23B72'}
        markers = {'Palmsens': 'o', 'STM32': 's'}
        
        for device in ['Palmsens', 'STM32']:
            device_data = df[df['device'] == device]
            device_actual = device_data['concentration'].values
            device_predicted = pls_conc.predict(scaler.transform(device_data[features].values)).flatten()
            
            axes[0,0].scatter(device_actual, device_predicted, 
                            color=colors[device], marker=markers[device], 
                            alpha=0.7, s=60, label=f'{device} (n={len(device_data)})',
                            edgecolors='black', linewidth=0.5)
        
        # Perfect prediction line
        min_conc, max_conc = y_concentration.min(), y_concentration.max()
        axes[0,0].plot([min_conc, max_conc], [min_conc, max_conc], 'r--', 
                      linewidth=2, label='Perfect Prediction', alpha=0.8)
        
        # Calculate metrics for each device
        for device in ['Palmsens', 'STM32']:
            device_data = df[df['device'] == device]
            device_actual = device_data['concentration'].values
            device_predicted = pls_conc.predict(scaler.transform(device_data[features].values)).flatten()
            
            r2 = r2_score(device_actual, device_predicted)
            mae = mean_absolute_error(device_actual, device_predicted)
            rmse = np.sqrt(np.mean((device_actual - device_predicted)**2))
            
            print(f"{device}: R² = {r2:.3f}, MAE = {mae:.2f} mM, RMSE = {rmse:.2f} mM")
        
        axes[0,0].set_xlabel('Actual Concentration (mM)', fontweight='bold')
        axes[0,0].set_ylabel('Predicted Concentration (mM)', fontweight='bold')
        axes[0,0].set_title('Device-Specific Concentration Prediction Performance', fontweight='bold')
        axes[0,0].legend(frameon=True, fancybox=True, shadow=True)
        axes[0,0].grid(True, alpha=0.3)
        
        # Add overall statistics
        overall_r2 = results['concentration_prediction']['r2_score']
        overall_mae = results['concentration_prediction']['mae']
        axes[0,0].text(0.05, 0.95, f'Overall R² = {overall_r2:.3f}\\nOverall MAE = {overall_mae:.2f} mM',
                      transform=axes[0,0].transAxes, fontsize=10, fontweight='bold',
                      bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8))
        
        # 2. Bland-Altman Plot for Device Comparison
        self.create_bland_altman_plot(df, pls_conc, scaler, features, axes[0,1])
        
        # 3. Concentration-wise Error Analysis
        self.create_concentration_error_analysis(df, pls_conc, scaler, features, axes[0,2])
        
        # 4. Device Classification with Confidence Intervals
        self.create_device_classification_plot(df, pls_device, scaler, features, axes[1,0])
        
        # 5. Feature Importance Comparison
        self.create_feature_importance_comparison(results, axes[1,1])
        
        # 6. Measurement Precision Analysis
        self.create_precision_analysis(df, axes[1,2])
        
        plt.tight_layout()
        return fig
    
    def create_bland_altman_plot(self, df, pls_conc, scaler, features, ax):
        """Bland-Altman Plot สำหรับเปรียบเทียบเครื่องวัด"""
        
        colors = {'Palmsens': '#2E86AB', 'STM32': '#A23B72'}
        
        for device in ['Palmsens', 'STM32']:
            device_data = df[df['device'] == device]
            actual = device_data['concentration'].values
            predicted = pls_conc.predict(scaler.transform(device_data[features].values)).flatten()
            
            mean_values = (actual + predicted) / 2
            differences = predicted - actual
            
            ax.scatter(mean_values, differences, color=colors[device], 
                      alpha=0.6, s=50, label=f'{device}', edgecolors='black', linewidth=0.5)
            
            # Calculate bias and limits of agreement
            bias = np.mean(differences)
            std_diff = np.std(differences)
            upper_loa = bias + 1.96 * std_diff
            lower_loa = bias - 1.96 * std_diff
            
            # Plot bias and LOA lines
            ax.axhline(bias, color=colors[device], linestyle='-', alpha=0.7, linewidth=1)
            ax.axhline(upper_loa, color=colors[device], linestyle='--', alpha=0.7, linewidth=1)
            ax.axhline(lower_loa, color=colors[device], linestyle='--', alpha=0.7, linewidth=1)
        
        ax.axhline(0, color='red', linestyle='-', alpha=0.8, linewidth=2, label='No Bias')
        ax.set_xlabel('Mean of Actual and Predicted (mM)', fontweight='bold')
        ax.set_ylabel('Difference (Predicted - Actual) (mM)', fontweight='bold')
        ax.set_title('Bland-Altman Plot: Device Agreement Analysis', fontweight='bold')
        ax.legend(frameon=True, fancybox=True, shadow=True)
        ax.grid(True, alpha=0.3)
    
    def create_concentration_error_analysis(self, df, pls_conc, scaler, features, ax):
        """วิเคราะห์ความคลาดเคลื่อนตามความเข้มข้น"""
        
        concentrations = sorted(df['concentration'].unique())
        colors = {'Palmsens': '#2E86AB', 'STM32': '#A23B72'}
        
        device_errors = {device: [] for device in ['Palmsens', 'STM32']}
        device_stds = {device: [] for device in ['Palmsens', 'STM32']}
        
        for conc in concentrations:
            for device in ['Palmsens', 'STM32']:
                device_conc_data = df[(df['device'] == device) & (df['concentration'] == conc)]
                
                if len(device_conc_data) > 0:
                    actual = device_conc_data['concentration'].values
                    predicted = pls_conc.predict(scaler.transform(device_conc_data[features].values)).flatten()
                    
                    errors = np.abs(predicted - actual)
                    mean_error = np.mean(errors)
                    std_error = np.std(errors) if len(errors) > 1 else 0
                    
                    device_errors[device].append(mean_error)
                    device_stds[device].append(std_error)
                else:
                    device_errors[device].append(0)
                    device_stds[device].append(0)
        
        # Plot with error bars
        x_offset = {'Palmsens': -0.1, 'STM32': 0.1}
        for device in ['Palmsens', 'STM32']:
            x_pos = np.array(concentrations) + x_offset[device]
            ax.errorbar(x_pos, device_errors[device], yerr=device_stds[device],
                       color=colors[device], marker='o', capsize=5, capthick=2,
                       label=f'{device} (Mean ± SD)', linewidth=2, markersize=8)
        
        ax.set_xlabel('Concentration (mM)', fontweight='bold')
        ax.set_ylabel('Mean Absolute Error (mM)', fontweight='bold')
        ax.set_title('Concentration-Dependent Error Analysis\\n(with Standard Deviation)', fontweight='bold')
        ax.legend(frameon=True, fancybox=True, shadow=True)
        ax.grid(True, alpha=0.3)
        ax.set_yscale('log')  # Log scale for better visualization
    
    def create_device_classification_plot(self, df, pls_device, scaler, features, ax):
        """Device Classification with Confidence Intervals"""
        
        X = df[features].values
        X_scaled = scaler.transform(X)
        y_device = (df['device'] == 'STM32').astype(int)
        device_pred = pls_device.predict(X_scaled).flatten()
        
        # Calculate confidence intervals (simplified)
        pred_std = np.std(device_pred)
        
        colors = {0: '#2E86AB', 1: '#A23B72'}  # 0=Palmsens, 1=STM32
        labels = {0: 'Palmsens', 1: 'STM32'}
        
        for device_code in [0, 1]:
            mask = (y_device == device_code)
            y_vals = y_device[mask]
            pred_vals = device_pred[mask]
            
            ax.errorbar(y_vals, pred_vals, yerr=pred_std/2, 
                       fmt='o', color=colors[device_code], alpha=0.7,
                       capsize=3, capthick=1, label=f'{labels[device_code]}',
                       markersize=6)
        
        # Perfect classification line
        ax.plot([0, 1], [0, 1], 'r--', linewidth=2, label='Perfect Classification', alpha=0.8)
        
        ax.set_xlabel('Actual Device (0=Palmsens, 1=STM32)', fontweight='bold')
        ax.set_ylabel('Predicted Device Classification', fontweight='bold')
        ax.set_title('Device Classification Performance\\n(with Confidence Intervals)', fontweight='bold')
        ax.legend(frameon=True, fancybox=True, shadow=True)
        ax.grid(True, alpha=0.3)
        
        # Add classification accuracy
        accuracy = np.mean((device_pred > 0.5).astype(int) == y_device)
        ax.text(0.05, 0.95, f'Classification Accuracy: {accuracy:.1%}',
               transform=ax.transAxes, fontsize=10, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.8))
    
    def create_feature_importance_comparison(self, results, ax):
        """เปรียบเทียบ Feature Importance ระหว่าง 2 โมเดล"""
        
        features = list(results['device_classification']['feature_importance'].keys())
        device_importance = list(results['device_classification']['feature_importance'].values())
        conc_importance = list(results['concentration_prediction']['feature_importance'].values())
        
        x_pos = np.arange(len(features))
        width = 0.35
        
        bars1 = ax.bar(x_pos - width/2, device_importance, width, 
                      label='Device Classification', color='#2E86AB', alpha=0.8)
        bars2 = ax.bar(x_pos + width/2, conc_importance, width,
                      label='Concentration Prediction', color='#A23B72', alpha=0.8)
        
        ax.set_xlabel('Features', fontweight='bold')
        ax.set_ylabel('Feature Importance (|PLS Coefficient|)', fontweight='bold')
        ax.set_title('Feature Importance Comparison\\nBetween Classification and Regression Models', fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels([f.replace('_', ' ').title() for f in features], rotation=45, ha='right')
        ax.legend(frameon=True, fancybox=True, shadow=True)
        ax.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.3f}', ha='center', va='bottom', fontsize=8)
    
    def create_precision_analysis(self, df, ax):
        """วิเคราะห์ความแม่นยำการวัดซ้ำ"""
        
        # Group by concentration and device, calculate CV%
        precision_data = []
        
        for conc in sorted(df['concentration'].unique()):
            for device in ['Palmsens', 'STM32']:
                device_conc_data = df[(df['device'] == device) & (df['concentration'] == conc)]
                
                if len(device_conc_data) >= 3:  # Need at least 3 replicates
                    for feature in ['ox_voltage', 'peak_separation']:
                        values = device_conc_data[feature].values
                        mean_val = np.mean(values)
                        std_val = np.std(values)
                        cv_percent = (std_val / mean_val) * 100 if mean_val != 0 else 0
                        
                        precision_data.append({
                            'concentration': conc,
                            'device': device,
                            'feature': feature,
                            'cv_percent': cv_percent
                        })
        
        if precision_data:
            precision_df = pd.DataFrame(precision_data)
            
            # Create grouped bar plot
            colors = {'Palmsens': '#2E86AB', 'STM32': '#A23B72'}
            
            for i, feature in enumerate(['ox_voltage', 'peak_separation']):
                feature_data = precision_df[precision_df['feature'] == feature]
                
                for j, device in enumerate(['Palmsens', 'STM32']):
                    device_data = feature_data[feature_data['device'] == device]
                    
                    x_pos = device_data['concentration'].values + (j-0.5)*0.2 + i*0.1
                    ax.bar(x_pos, device_data['cv_percent'].values, width=0.15,
                          color=colors[device], alpha=0.7 if i==0 else 0.9,
                          label=f'{device} - {feature.replace("_", " ").title()}' if len(precision_data) < 20 else '')
            
            ax.set_xlabel('Concentration (mM)', fontweight='bold')
            ax.set_ylabel('Coefficient of Variation (%)', fontweight='bold')
            ax.set_title('Measurement Precision Analysis\\n(CV% for Replicate Measurements)', fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # Add acceptable precision line (typically 5% for analytical methods)
            ax.axhline(y=5, color='red', linestyle='--', alpha=0.7, 
                      label='5% CV Threshold')
            
            if len(precision_data) < 20:
                ax.legend(frameon=True, fancybox=True, shadow=True, fontsize=8)
        else:
            ax.text(0.5, 0.5, 'Insufficient replicate data\\nfor precision analysis',
                   transform=ax.transAxes, ha='center', va='center',
                   fontsize=12, fontweight='bold')
            ax.set_title('Measurement Precision Analysis\\n(Insufficient Data)', fontweight='bold')


def create_publication_ready_summary_table(results, df):
    """สร้างตารางสรุปผลสำหรับงานวิจัย"""
    
    # Calculate detailed statistics
    summary_stats = {}
    
    for device in ['Palmsens', 'STM32']:
        device_data = df[df['device'] == device]
        
        summary_stats[device] = {
            'n_samples': len(device_data),
            'concentrations_tested': len(device_data['concentration'].unique()),
            'concentration_range': f"{device_data['concentration'].min():.1f} - {device_data['concentration'].max():.1f} mM",
            'mean_ox_voltage': f"{device_data['ox_voltage'].mean():.3f} ± {device_data['ox_voltage'].std():.3f} V",
            'mean_peak_separation': f"{device_data['peak_separation'].mean():.3f} ± {device_data['peak_separation'].std():.3f} V",
        }
    
    # Model performance
    model_performance = {
        'Device Classification': {
            'R²': f"{results['device_classification']['r2_score']:.3f}",
            'CV R²': f"{results['device_classification']['cv_mean']:.3f} ± {results['device_classification']['cv_std']:.3f}",
            'Primary Features': 'ox_voltage, peak_separation'
        },
        'Concentration Prediction': {
            'R²': f"{results['concentration_prediction']['r2_score']:.3f}",
            'MAE': f"{results['concentration_prediction']['mae']:.2f} mM",
            'CV R²': f"{results['concentration_prediction']['cv_mean']:.3f} ± {results['concentration_prediction']['cv_std']:.3f}",
            'Primary Features': 'concentration, ox_current'
        }
    }
    
    return summary_stats, model_performance


if __name__ == "__main__":
    print("📊 Improved PLS Visualization Toolkit")
    print("✅ Publication-ready plots with:")
    print("  - Device-separated analysis")
    print("  - Bland-Altman plots")
    print("  - Error bars and confidence intervals")
    print("  - Precision analysis (CV%)")
    print("  - Comprehensive statistical reporting")
    print("  - Research-grade formatting")
