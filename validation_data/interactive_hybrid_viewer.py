#!/usr/bin/env python3
"""
🎯 Interactive HybridCV Enhanced Results Viewer
==============================================

Interactive display and analysis of HybridCV Enhanced peak detection results.
Shows detailed CV data with peak annotations and comparative analysis.

Author: H743Poten Research Team
Date: October 4, 2025
"""

import sys
import os
sys.path.append('.')
sys.path.append('validation_data')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.widgets import Button, CheckButtons
import seaborn as sns
from hybrid_cv_enhanced import HybridCVEnhanced

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class InteractiveHybridViewer:
    """Interactive viewer for HybridCV Enhanced results"""
    
    def __init__(self):
        self.current_data_index = 0
        self.show_v5_peaks = True
        self.show_deepcv_prediction = True
        self.show_baseline = True
        self.show_annotations = True
        
        # Initialize HybridCV Enhanced
        self.hybrid = HybridCVEnhanced(config={
            'v5_weight': 0.6,
            'deepcv_weight': 0.4,
            'verbose': False
        })
        
        # Generate test data
        self.test_data = self._generate_test_data()
        self.results_data = []
        
        # Process all data
        self._process_all_data()
        
        # Create interactive plot
        self._create_interactive_plot()
    
    def _generate_test_data(self):
        """Generate the same test data as validation"""
        return [
            {
                'voltage': np.linspace(-0.4, 0.7, 220),
                'current_pattern': 'ferrocyanide',
                'title': 'Ferrocyanide (0.5mM)',
                'description': 'Classic reversible redox couple with distinct anodic and cathodic peaks',
                'color': '#FF6B6B'
            },
            {
                'voltage': np.linspace(-0.5, 0.8, 260),
                'current_pattern': 'dopamine',
                'title': 'Dopamine (1.0mM)',
                'description': 'Irreversible oxidation with predominant anodic peak',
                'color': '#4ECDC4'
            },
            {
                'voltage': np.linspace(-0.3, 0.6, 180),
                'current_pattern': 'ascorbic_acid',
                'title': 'Ascorbic Acid (5.0mM)',
                'description': 'Multiple oxidation peaks with complex electrochemistry',
                'color': '#45B7D1'
            }
        ]
    
    def _generate_cv_pattern(self, voltage, pattern_type):
        """Generate CV patterns matching validation data"""
        if pattern_type == 'ferrocyanide':
            anodic = 15e-6 * np.exp(-((voltage - 0.2) / 0.08)**2)
            cathodic = -12e-6 * np.exp(-((voltage + 0.1) / 0.08)**2)
            background = 1e-8 * voltage
            noise = 0.5e-6 * np.random.normal(0, 1, len(voltage))
        elif pattern_type == 'dopamine':
            anodic = 8e-6 * np.exp(-((voltage - 0.3) / 0.12)**2)
            cathodic = -2e-6 * np.exp(-((voltage - 0.1) / 0.15)**2)
            background = 2e-8 * voltage
            noise = 0.3e-6 * np.random.normal(0, 1, len(voltage))
        elif pattern_type == 'ascorbic_acid':
            peak1 = 6e-6 * np.exp(-((voltage - 0.1) / 0.06)**2)
            peak2 = 4e-6 * np.exp(-((voltage - 0.4) / 0.08)**2)
            background = 0.5e-8 * voltage
            noise = 0.2e-6 * np.random.normal(0, 1, len(voltage))
            cathodic = 0
            anodic = peak1 + peak2
        
        current = anodic + cathodic + background + noise
        return current * 1e6  # Convert to µA
    
    def _process_all_data(self):
        """Process all test data with HybridCV Enhanced"""
        print("🔄 Processing all data with HybridCV Enhanced...")
        
        for i, data in enumerate(self.test_data):
            voltage = data['voltage']
            current = self._generate_cv_pattern(voltage, data['current_pattern'])
            
            # Run HybridCV Enhanced
            result = self.hybrid.detect_peaks(voltage, current, f"{data['title']}.csv")
            
            # Store comprehensive data
            self.results_data.append({
                'voltage': voltage,
                'current': current,
                'result': result,
                'title': data['title'],
                'description': data['description'],
                'color': data['color'],
                'pattern': data['current_pattern'],
                'index': i
            })
        
        print(f"✅ Processed {len(self.results_data)} datasets")
    
    def _create_interactive_plot(self):
        """Create interactive matplotlib plot"""
        # Create figure with subplots
        self.fig, ((self.ax_main, self.ax_stats), (self.ax_comparison, self.ax_info)) = plt.subplots(
            2, 2, figsize=(16, 12)
        )
        
        # Add control buttons
        self._add_control_buttons()
        
        # Initial plot
        self._update_plot()
        
        # Show plot
        plt.tight_layout(rect=[0, 0.15, 1, 0.95])
        plt.show()
    
    def _add_control_buttons(self):
        """Add interactive control buttons"""
        # Navigation buttons
        ax_prev = plt.axes([0.1, 0.02, 0.1, 0.04])
        ax_next = plt.axes([0.25, 0.02, 0.1, 0.04])
        
        self.btn_prev = Button(ax_prev, 'Previous')
        self.btn_next = Button(ax_next, 'Next')
        
        self.btn_prev.on_clicked(self._prev_data)
        self.btn_next.on_clicked(self._next_data)
        
        # Toggle buttons
        ax_toggles = plt.axes([0.45, 0.02, 0.4, 0.08])
        self.toggles = CheckButtons(
            ax_toggles, 
            ['V5 Peaks', 'DeepCV Prediction', 'Baseline', 'Annotations'],
            [self.show_v5_peaks, self.show_deepcv_prediction, self.show_baseline, self.show_annotations]
        )
        self.toggles.on_clicked(self._toggle_display)
        
        # Export button
        ax_export = plt.axes([0.87, 0.02, 0.1, 0.04])
        self.btn_export = Button(ax_export, 'Export')
        self.btn_export.on_clicked(self._export_current)
    
    def _update_plot(self):
        """Update all subplots with current data"""
        # Clear all axes
        for ax in [self.ax_main, self.ax_stats, self.ax_comparison, self.ax_info]:
            ax.clear()
        
        current_data = self.results_data[self.current_data_index]
        voltage = current_data['voltage']
        current = current_data['current']
        result = current_data['result']
        title = current_data['title']
        color = current_data['color']
        
        # Main CV plot
        self._plot_main_cv(voltage, current, result, title, color)
        
        # Statistics plot
        self._plot_statistics(result)
        
        # Comparison plot
        self._plot_comparison()
        
        # Info panel
        self._plot_info_panel(current_data)
        
        # Update title
        self.fig.suptitle(f'HybridCV Enhanced Analysis - {title} ({self.current_data_index + 1}/{len(self.results_data)})', 
                         fontsize=16, fontweight='bold')
        
        # Refresh display
        self.fig.canvas.draw()
    
    def _plot_main_cv(self, voltage, current, result, title, color):
        """Plot main CV data with peaks"""
        # Plot CV data
        self.ax_main.plot(voltage, current, 'b-', linewidth=2, alpha=0.8, label='CV Data')
        
        # Extract results
        v5_result = result.get('v5_result', {})
        deepcv_result = result.get('deepcv_result', {})
        ensemble_result = result.get('ensemble_result', {})
        
        # Plot V5 peaks if enabled
        if self.show_v5_peaks:
            v5_peaks = v5_result.get('peaks_list', [])
            if v5_peaks:
                peak_voltages = []
                peak_currents = []
                for peak in v5_peaks:
                    if 'voltage' in peak and 'current' in peak:
                        peak_voltages.append(peak['voltage'])
                        peak_currents.append(peak['current'])
                
                if peak_voltages:
                    self.ax_main.scatter(peak_voltages, peak_currents, c='red', s=50, alpha=0.8,
                                       label=f'V5 Peaks (n={len(peak_voltages)})', zorder=5)
        
        # Show DeepCV prediction if enabled
        if self.show_deepcv_prediction:
            deepcv_peaks = deepcv_result.get('peaks_detected', 0)
            if deepcv_peaks > 0:
                # Simulate peak positions for visualization
                try:
                    from scipy.signal import find_peaks
                    peaks_pos, _ = find_peaks(current, height=np.std(current), distance=5)
                    peaks_neg, _ = find_peaks(-current, height=np.std(current), distance=5)
                    
                    all_peak_indices = sorted(list(peaks_pos) + list(peaks_neg))[:deepcv_peaks]
                    
                    if all_peak_indices:
                        peak_v = voltage[all_peak_indices]
                        peak_i = current[all_peak_indices]
                        self.ax_main.scatter(peak_v, peak_i, c='green', s=60, alpha=0.7, marker='^',
                                           label=f'DeepCV Prediction (n={deepcv_peaks})', zorder=4)
                except:
                    pass
        
        # Show baseline if enabled
        if self.show_baseline:
            # Simple baseline estimation
            baseline = np.percentile(current, 10)
            self.ax_main.axhline(y=baseline, color='gray', linestyle='--', alpha=0.5, label='Baseline Est.')
        
        # Annotations
        if self.show_annotations:
            # Add scan direction arrows
            mid_point = len(voltage) // 2
            self.ax_main.annotate('Forward', xy=(voltage[mid_point//2], current[mid_point//2]),
                                xytext=(voltage[mid_point//2]-0.1, current[mid_point//2]+2),
                                arrowprops=dict(arrowstyle='->', color='red', alpha=0.7))
            self.ax_main.annotate('Reverse', xy=(voltage[mid_point + mid_point//2], current[mid_point + mid_point//2]),
                                xytext=(voltage[mid_point + mid_point//2]+0.1, current[mid_point + mid_point//2]+2),
                                arrowprops=dict(arrowstyle='->', color='blue', alpha=0.7))
        
        self.ax_main.set_xlabel('Voltage (V)', fontsize=12)
        self.ax_main.set_ylabel('Current (µA)', fontsize=12)
        self.ax_main.set_title('Cyclic Voltammogram with Peak Detection', fontweight='bold')
        self.ax_main.legend()
        self.ax_main.grid(True, alpha=0.3)
    
    def _plot_statistics(self, result):
        """Plot statistics comparison"""
        v5_result = result.get('v5_result', {})
        deepcv_result = result.get('deepcv_result', {})
        ensemble_result = result.get('ensemble_result', {})
        
        methods = ['V5', 'DeepCV', 'Hybrid']
        peak_counts = [
            v5_result.get('peaks_detected', 0),
            deepcv_result.get('peaks_detected', 0),
            ensemble_result.get('peaks_detected', 0)
        ]
        confidences = [
            v5_result.get('confidence', 0),
            deepcv_result.get('confidence', 0),
            ensemble_result.get('confidence', 0)
        ]
        
        x = np.arange(len(methods))
        width = 0.35
        
        bars1 = self.ax_stats.bar(x - width/2, peak_counts, width, label='Peak Count',
                                 color=['#FF6B6B', '#4ECDC4', '#45B7D1'], alpha=0.8)
        
        ax_stats_twin = self.ax_stats.twinx()
        bars2 = ax_stats_twin.bar(x + width/2, confidences, width, label='Confidence (%)',
                                 color=['#FF6B6B', '#4ECDC4', '#45B7D1'], alpha=0.5)
        
        # Add value labels
        for bar, count in zip(bars1, peak_counts):
            self.ax_stats.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                              str(count), ha='center', va='bottom', fontweight='bold')
        
        for bar, conf in zip(bars2, confidences):
            ax_stats_twin.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                              f'{conf:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        self.ax_stats.set_xlabel('Detection Methods')
        self.ax_stats.set_ylabel('Peak Count', color='black')
        ax_stats_twin.set_ylabel('Confidence (%)', color='gray')
        self.ax_stats.set_title('Method Performance Comparison', fontweight='bold')
        self.ax_stats.set_xticks(x)
        self.ax_stats.set_xticklabels(methods)
        self.ax_stats.grid(True, alpha=0.3, axis='y')
    
    def _plot_comparison(self):
        """Plot comparison across all datasets"""
        all_titles = [data['title'].split('(')[0].strip() for data in self.results_data]
        
        v5_peaks = [data['result']['v5_result'].get('peaks_detected', 0) for data in self.results_data]
        deepcv_peaks = [data['result']['deepcv_result'].get('peaks_detected', 0) for data in self.results_data]
        hybrid_peaks = [data['result']['ensemble_result'].get('peaks_detected', 0) for data in self.results_data]
        
        x = np.arange(len(all_titles))
        width = 0.25
        
        bars1 = self.ax_comparison.bar(x - width, v5_peaks, width, label='V5', color='#FF6B6B', alpha=0.8)
        bars2 = self.ax_comparison.bar(x, deepcv_peaks, width, label='DeepCV', color='#4ECDC4', alpha=0.8)
        bars3 = self.ax_comparison.bar(x + width, hybrid_peaks, width, label='Hybrid', color='#45B7D1', alpha=0.8)
        
        # Highlight current dataset
        bars_list = [bars1, bars2, bars3]
        for bars in bars_list:
            bars[self.current_data_index].set_edgecolor('black')
            bars[self.current_data_index].set_linewidth(3)
        
        self.ax_comparison.set_xlabel('Electrochemical Systems')
        self.ax_comparison.set_ylabel('Peak Count')
        self.ax_comparison.set_title('Cross-Dataset Comparison', fontweight='bold')
        self.ax_comparison.set_xticks(x)
        self.ax_comparison.set_xticklabels(all_titles, rotation=45, ha='right')
        self.ax_comparison.legend()
        self.ax_comparison.grid(True, alpha=0.3, axis='y')
    
    def _plot_info_panel(self, current_data):
        """Plot information panel"""
        self.ax_info.axis('off')
        
        result = current_data['result']
        ensemble_result = result.get('ensemble_result', {})
        
        info_text = f"""
{current_data['title']}
{current_data['description']}

📊 Detection Results:
• V5 Peaks: {result['v5_result'].get('peaks_detected', 0)} ({result['v5_result'].get('confidence', 0):.1f}%)
• DeepCV Prediction: {result['deepcv_result'].get('peaks_detected', 0)} ({result['deepcv_result'].get('confidence', 0):.1f}%)
• Hybrid Result: {ensemble_result.get('peaks_detected', 0)} ({ensemble_result.get('confidence', 0):.1f}%)

🤖 Ensemble Decision: {ensemble_result.get('decision', 'unknown')}
📈 Consensus Score: {ensemble_result.get('consensus_score', 0):.2f}

⚖️ Weights:
• V5: {ensemble_result.get('v5_weight', 0):.2f}
• DeepCV: {ensemble_result.get('deepcv_weight', 0):.2f}

⏱️ Processing Time: {result.get('processing_time', 0)*1000:.1f} ms
        """
        
        self.ax_info.text(0.05, 0.95, info_text, transform=self.ax_info.transAxes,
                         verticalalignment='top', fontsize=10, fontfamily='monospace',
                         bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.8))
    
    def _prev_data(self, event):
        """Navigate to previous dataset"""
        self.current_data_index = (self.current_data_index - 1) % len(self.results_data)
        self._update_plot()
    
    def _next_data(self, event):
        """Navigate to next dataset"""
        self.current_data_index = (self.current_data_index + 1) % len(self.results_data)
        self._update_plot()
    
    def _toggle_display(self, label):
        """Toggle display options"""
        if label == 'V5 Peaks':
            self.show_v5_peaks = not self.show_v5_peaks
        elif label == 'DeepCV Prediction':
            self.show_deepcv_prediction = not self.show_deepcv_prediction
        elif label == 'Baseline':
            self.show_baseline = not self.show_baseline
        elif label == 'Annotations':
            self.show_annotations = not self.show_annotations
        
        self._update_plot()
    
    def _export_current(self, event):
        """Export current view"""
        current_data = self.results_data[self.current_data_index]
        filename = f"interactive_view_{current_data['pattern']}.png"
        self.fig.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"💾 Exported current view as '{filename}'")

def main():
    """Main function to run interactive viewer"""
    print("🎯 INTERACTIVE HYBRIDCV ENHANCED VIEWER")
    print("=" * 60)
    print("🎮 Controls:")
    print("   • Previous/Next: Navigate between datasets")
    print("   • Checkboxes: Toggle display elements")
    print("   • Export: Save current view as PNG")
    print("   • Close window to exit")
    print()
    
    try:
        viewer = InteractiveHybridViewer()
        print("✅ Interactive viewer started successfully!")
        print("📊 Use the controls to explore the data")
        
    except Exception as e:
        print(f"❌ Error starting interactive viewer: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()