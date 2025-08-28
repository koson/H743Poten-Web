#!/usr/bin/env python3
"""
Advanced PLS Visualization Toolkit
สำหรับการสร้างกราฟ PLS แบบมาตรฐานงานวิจัย
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import cross_val_predict
import pandas as pd

class AdvancedPLSVisualizer:
    def __init__(self, pls_model, X_scaled, y, feature_names, device_names):
        self.pls_model = pls_model
        self.X_scaled = X_scaled
        self.y = y
        self.feature_names = feature_names
        self.device_names = device_names
        self.predictions = pls_model.predict(X_scaled).flatten()
        
    def create_score_plot(self, ax):
        """PLS Score Plot (PC1 vs PC2)"""
        X_scores = self.pls_model.x_scores_
        
        # Separate by class
        for i, device in enumerate(self.device_names):
            mask = (self.y == i)
            color = ['blue', 'red'][i]
            ax.scatter(X_scores[mask, 0], X_scores[mask, 1], 
                      alpha=0.7, label=device, color=color, s=50)
        
        ax.set_xlabel('PC1 (First Component)')
        ax.set_ylabel('PC2 (Second Component)')
        ax.set_title('PLS Score Plot')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Add explained variance if available
        if hasattr(self.pls_model, 'x_weights_'):
            var_explained = np.var(X_scores, axis=0)
            total_var = np.sum(var_explained)
            pc1_var = (var_explained[0] / total_var) * 100
            pc2_var = (var_explained[1] / total_var) * 100
            ax.set_xlabel(f'PC1 ({pc1_var:.1f}% variance)')
            ax.set_ylabel(f'PC2 ({pc2_var:.1f}% variance)')
    
    def create_loading_plot(self, ax):
        """PLS Loading Plot"""
        loadings = self.pls_model.x_loadings_
        
        # Plot loading vectors
        for i, feature in enumerate(self.feature_names):
            ax.arrow(0, 0, loadings[i, 0], loadings[i, 1], 
                    head_width=0.02, head_length=0.02, fc='red', ec='red')
            ax.text(loadings[i, 0]*1.1, loadings[i, 1]*1.1, feature, 
                   ha='center', va='center', fontsize=9,
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.7))
        
        ax.set_xlabel('PC1 Loading')
        ax.set_ylabel('PC2 Loading')
        ax.set_title('PLS Loading Plot')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        ax.axvline(x=0, color='k', linestyle='-', alpha=0.3)
    
    def create_vip_plot(self, ax):
        """Variable Importance Plot (VIP)"""
        # Calculate VIP scores
        weights = self.pls_model.x_weights_
        loadings = self.pls_model.x_loadings_
        
        # Simplified VIP calculation
        vip_scores = np.sqrt(np.sum(weights**2 * loadings**2, axis=1))
        vip_scores = vip_scores / np.max(vip_scores)  # Normalize
        
        # Create bar plot
        colors = ['red' if vip > 0.8 else 'orange' if vip > 0.5 else 'lightblue' 
                 for vip in vip_scores]
        bars = ax.bar(self.feature_names, vip_scores, color=colors)
        
        ax.set_title('Variable Importance Plot (VIP)')
        ax.set_ylabel('VIP Score (Normalized)')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)
        
        # Add significance lines
        ax.axhline(y=0.8, color='red', linestyle='--', alpha=0.7, label='High Importance')
        ax.axhline(y=0.5, color='orange', linestyle='--', alpha=0.7, label='Medium Importance')
        ax.legend()
        
        # Add value labels
        for bar, vip in zip(bars, vip_scores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{vip:.2f}', ha='center', va='bottom')
    
    def create_prediction_plot(self, ax):
        """Prediction vs Actual Plot"""
        ax.scatter(self.y, self.predictions, alpha=0.6, color='green', s=50)
        ax.plot([0, 1], [0, 1], 'r--', linewidth=2, label='Perfect Prediction')
        
        ax.set_xlabel('Actual (0=Palmsens, 1=STM32)')
        ax.set_ylabel('Predicted')
        ax.set_title('Prediction vs Actual Values')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Add R² score
        from sklearn.metrics import r2_score
        r2 = r2_score(self.y, self.predictions)
        ax.text(0.05, 0.95, f'R² = {r2:.4f}', transform=ax.transAxes, 
               bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    def create_confusion_matrix_plot(self, ax):
        """Confusion Matrix"""
        y_pred_binary = (self.predictions > 0.5).astype(int)
        cm = confusion_matrix(self.y, y_pred_binary)
        
        # Create heatmap
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                   xticklabels=self.device_names, yticklabels=self.device_names)
        ax.set_title('Confusion Matrix')
        ax.set_xlabel('Predicted')
        ax.set_ylabel('Actual')
        
        # Add accuracy
        accuracy = np.trace(cm) / np.sum(cm)
        ax.text(0.5, -0.1, f'Accuracy: {accuracy:.3f}', transform=ax.transAxes,
               ha='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    def create_residuals_plot(self, ax):
        """Residuals Plot"""
        residuals = self.y - self.predictions
        ax.scatter(self.predictions, residuals, alpha=0.6, color='purple')
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.7)
        
        ax.set_xlabel('Predicted Values')
        ax.set_ylabel('Residuals')
        ax.set_title('Residuals vs Predicted')
        ax.grid(True, alpha=0.3)
        
        # Add RMSE
        rmse = np.sqrt(np.mean(residuals**2))
        ax.text(0.05, 0.95, f'RMSE = {rmse:.4f}', transform=ax.transAxes,
               bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8))
    
    def create_comprehensive_plot(self, figsize=(20, 12), save_path=None):
        """สร้างกราฟครอบคลุมทั้งหมด"""
        fig, axes = plt.subplots(2, 3, figsize=figsize)
        fig.suptitle('Comprehensive PLS Analysis Visualization', fontsize=16, fontweight='bold')
        
        # Create all plots
        self.create_score_plot(axes[0, 0])
        self.create_loading_plot(axes[0, 1])
        self.create_vip_plot(axes[0, 2])
        self.create_prediction_plot(axes[1, 0])
        self.create_confusion_matrix_plot(axes[1, 1])
        self.create_residuals_plot(axes[1, 2])
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Advanced PLS plots saved: {save_path}")
        
        return fig


def create_classification_report_plot(y_true, y_pred, class_names, save_path=None):
    """สร้างกราฟ Classification Report"""
    from sklearn.metrics import classification_report
    
    # Get classification report as dict
    y_pred_binary = (y_pred > 0.5).astype(int)
    report = classification_report(y_true, y_pred_binary, 
                                 target_names=class_names, output_dict=True)
    
    # Extract metrics
    metrics = ['precision', 'recall', 'f1-score']
    classes = class_names
    
    # Create DataFrame for plotting
    data = []
    for cls in classes:
        for metric in metrics:
            data.append({
                'Class': cls,
                'Metric': metric,
                'Value': report[cls][metric]
            })
    
    df_report = pd.DataFrame(data)
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Pivot for easier plotting
    pivot_df = df_report.pivot(index='Class', columns='Metric', values='Value')
    
    # Create grouped bar plot
    x = np.arange(len(classes))
    width = 0.25
    
    for i, metric in enumerate(metrics):
        values = [pivot_df.loc[cls, metric] for cls in classes]
        ax.bar(x + i*width, values, width, label=metric, alpha=0.8)
        
        # Add value labels on bars
        for j, val in enumerate(values):
            ax.text(x[j] + i*width, val + 0.01, f'{val:.3f}', 
                   ha='center', va='bottom', fontsize=9)
    
    ax.set_xlabel('Device Classes')
    ax.set_ylabel('Score')
    ax.set_title('Classification Performance Metrics')
    ax.set_xticks(x + width)
    ax.set_xticklabels(classes)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.1)
    
    # Add overall accuracy
    accuracy = report['accuracy']
    ax.text(0.02, 0.98, f'Overall Accuracy: {accuracy:.3f}', 
           transform=ax.transAxes, va='top',
           bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 Classification report plot saved: {save_path}")
    
    return fig


# Example usage function
def demonstrate_advanced_pls_plots():
    """ตัวอย่างการใช้งาน Advanced PLS Visualizer"""
    print("📊 Advanced PLS Visualization Toolkit")
    print("=" * 50)
    print("Features:")
    print("✅ Score Plot (PC1 vs PC2)")
    print("✅ Loading Plot (Variable vectors)")
    print("✅ VIP Plot (Variable Importance)")
    print("✅ Prediction vs Actual")
    print("✅ Confusion Matrix") 
    print("✅ Residuals Plot")
    print("✅ Classification Report Plot")
    print("")
    print("📝 Usage:")
    print("visualizer = AdvancedPLSVisualizer(pls_model, X_scaled, y, feature_names, device_names)")
    print("fig = visualizer.create_comprehensive_plot(save_path='advanced_pls.png')")
    print("fig2 = create_classification_report_plot(y_true, y_pred, class_names, 'classification.png')")


if __name__ == "__main__":
    demonstrate_advanced_pls_plots()
