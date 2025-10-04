#!/usr/bin/env python3
"""
🔬 Enhanced Detector V6 - Human-Validated Peak Detection
======================================================

Interactive peak validation system for training high-quality datasets.
Allows human experts to validate, remove, or add peaks with reasoning.

Features:
- Interactive CV plot with peak validation UI
- Expert reasoning capture for each decision
- High-quality dataset generation for DeepCV training
- Export validated results for ML training

Author: H743Poten Research Team
Date: October 4, 2025
Version: V6 (Human-Validated)
"""

import sys
import os
sys.path.append('.')
sys.path.append('validation_data')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, CheckButtons, TextBox
import matplotlib.patches as patches
from datetime import datetime
import json
import pickle
from enhanced_detector_v5 import EnhancedDetectorV5

class EnhancedDetectorV6:
    """
    Enhanced Detector V6 with Human Validation Interface
    
    Workflow:
    1. Run V5 automatic detection
    2. Present results to human expert
    3. Allow interactive validation/modification
    4. Capture expert reasoning
    5. Export high-quality training data
    """
    
    def __init__(self):
        self.v5_detector = EnhancedDetectorV5()
        
        # Current session data
        self.current_voltage = None
        self.current_current = None
        self.current_filename = None
        self.v5_peaks = []
        self.validated_peaks = []
        self.peak_validations = []
        self.expert_notes = ""
        
        # UI components
        self.fig = None
        self.ax_main = None
        self.selected_peak_index = None
        
        # Session tracking
        self.session_data = {
            'timestamp': datetime.now().isoformat(),
            'expert_id': 'default_expert',
            'validations': []
        }
        
        print("🔬 Enhanced Detector V6 initialized")
        print("✨ Human-validated peak detection system ready")
    
    def detect_peaks_with_validation(self, voltage, current, filename="unknown.csv"):
        """
        Main detection workflow with human validation
        
        Args:
            voltage: Voltage array
            current: Current array  
            filename: Source filename
            
        Returns:
            dict: Validated peak detection results
        """
        print(f"🔍 Starting V6 validation for: {filename}")
        
        # Store current data
        self.current_voltage = voltage
        self.current_current = current
        self.current_filename = filename
        
        # Step 1: Run V5 automatic detection
        print("📊 Running Enhanced V5 detection...")
        v5_result = self.v5_detector.detect_peaks_enhanced_v5(voltage, current)
        
        # Extract V5 peaks
        self.v5_peaks = v5_result.get('peaks', [])
        self.validated_peaks = self.v5_peaks.copy()  # Start with V5 results
        
        print(f"✅ V5 detected {len(self.v5_peaks)} peaks")
        
        # Step 2: Launch interactive validation UI
        self._launch_validation_ui()
        
        # Step 3: Return validated results
        return self._compile_final_results()
    
    def _launch_validation_ui(self):
        """Launch interactive validation interface"""
        print("🎨 Launching interactive validation UI...")
        
        # Create figure with custom layout
        self.fig = plt.figure(figsize=(16, 10))
        
        # Main CV plot (large)
        self.ax_main = plt.subplot2grid((3, 4), (0, 0), colspan=3, rowspan=2)
        
        # Info panel
        self.ax_info = plt.subplot2grid((3, 4), (0, 3), rowspan=1)
        
        # Peak list
        self.ax_peaks = plt.subplot2grid((3, 4), (1, 3), rowspan=1)
        
        # Controls
        self.ax_controls = plt.subplot2grid((3, 4), (2, 0), colspan=4)
        
        # Plot initial data
        self._update_main_plot()
        self._update_info_panel()
        self._update_peak_list()
        self._setup_controls()
        
        plt.tight_layout()
        plt.show()
    
    def _update_main_plot(self):
        """Update main CV plot with peaks"""
        self.ax_main.clear()
        
        # Plot CV data
        self.ax_main.plot(self.current_voltage, self.current_current, 'b-', 
                         linewidth=2, alpha=0.8, label='CV Data')
        
        # Plot validated peaks
        if self.validated_peaks:
            for i, peak in enumerate(self.validated_peaks):
                if 'voltage' in peak and 'current' in peak:
                    color = 'green' if peak.get('validated', False) else 'red'
                    marker = 'o' if peak.get('validated', False) else 'x'
                    alpha = 1.0 if peak.get('validated', False) else 0.6
                    
                    self.ax_main.scatter(peak['voltage'], peak['current'], 
                                       c=color, marker=marker, s=100, alpha=alpha,
                                       picker=True)
                    
                    # Add peak number
                    self.ax_main.annotate(f'{i+1}', 
                                        (peak['voltage'], peak['current']),
                                        xytext=(5, 5), textcoords='offset points',
                                        fontsize=8, fontweight='bold')
        
        # Highlight selected peak
        if self.selected_peak_index is not None and self.selected_peak_index < len(self.validated_peaks):
            peak = self.validated_peaks[self.selected_peak_index]
            if 'voltage' in peak and 'current' in peak:
                self.ax_main.scatter(peak['voltage'], peak['current'], 
                                   c='yellow', marker='o', s=200, alpha=0.7,
                                   edgecolors='black', linewidth=3)
        
        self.ax_main.set_xlabel('Voltage (V)', fontsize=12)
        self.ax_main.set_ylabel('Current (µA)', fontsize=12)
        self.ax_main.set_title(f'V6 Peak Validation - {self.current_filename}', 
                              fontsize=14, fontweight='bold')
        self.ax_main.grid(True, alpha=0.3)
        self.ax_main.legend()
        
        # Connect click events
        self.fig.canvas.mpl_connect('pick_event', self._on_peak_click)
        self.fig.canvas.mpl_connect('button_press_event', self._on_plot_click)
    
    def _update_info_panel(self):
        """Update information panel"""
        self.ax_info.clear()
        self.ax_info.axis('off')
        
        total_peaks = len(self.validated_peaks)
        validated_count = sum(1 for p in self.validated_peaks if p.get('validated', False))
        pending_count = total_peaks - validated_count
        
        info_text = f"""
📊 Validation Status
──────────────────
Total Peaks: {total_peaks}
✅ Validated: {validated_count}
⏳ Pending: {pending_count}

🎯 Selected Peak: {self.selected_peak_index + 1 if self.selected_peak_index is not None else 'None'}

📝 Instructions:
• Click peak to select
• Use buttons to validate/reject
• Double-click to add new peak
• Add reasoning for decisions

🔬 Expert: {self.session_data['expert_id']}
        """
        
        self.ax_info.text(0.05, 0.95, info_text, transform=self.ax_info.transAxes,
                         verticalalignment='top', fontsize=10, fontfamily='monospace',
                         bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8))
    
    def _update_peak_list(self):
        """Update peak list display"""
        self.ax_peaks.clear()
        self.ax_peaks.axis('off')
        
        if not self.validated_peaks:
            self.ax_peaks.text(0.5, 0.5, 'No peaks detected', transform=self.ax_peaks.transAxes,
                              ha='center', va='center')
            return
        
        peak_text = "📋 Peak List\\n" + "─" * 20 + "\\n"
        
        for i, peak in enumerate(self.validated_peaks[:10]):  # Show first 10
            status = "✅" if peak.get('validated', False) else "❌"
            voltage = peak.get('voltage', 0)
            current = peak.get('current', 0)
            confidence = peak.get('confidence', 0)
            
            peak_text += f"{i+1:2d}. {status} {voltage:+.3f}V, {current:+.1f}µA ({confidence:.0f}%)\\n"
        
        if len(self.validated_peaks) > 10:
            peak_text += f"... and {len(self.validated_peaks) - 10} more"
        
        self.ax_peaks.text(0.05, 0.95, peak_text, transform=self.ax_peaks.transAxes,
                          verticalalignment='top', fontsize=8, fontfamily='monospace',
                          bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.8))
    
    def _setup_controls(self):
        """Setup control buttons and inputs"""
        self.ax_controls.clear()
        self.ax_controls.axis('off')
        
        # Control buttons
        btn_width = 0.08
        btn_height = 0.3
        btn_y = 0.1
        
        # Validate button
        ax_validate = plt.axes([0.1, btn_y, btn_width, btn_height])
        self.btn_validate = Button(ax_validate, 'Validate\\nPeak', color='lightgreen')
        self.btn_validate.on_clicked(self._validate_peak)
        
        # Reject button  
        ax_reject = plt.axes([0.2, btn_y, btn_width, btn_height])
        self.btn_reject = Button(ax_reject, 'Reject\\nPeak', color='lightcoral')
        self.btn_reject.on_clicked(self._reject_peak)
        
        # Add peak button
        ax_add = plt.axes([0.3, btn_y, btn_width, btn_height])
        self.btn_add = Button(ax_add, 'Add\\nPeak', color='lightblue')
        self.btn_add.on_clicked(self._add_peak_mode)
        
        # Export button
        ax_export = plt.axes([0.4, btn_y, btn_width, btn_height])
        self.btn_export = Button(ax_export, 'Export\\nResults', color='gold')
        self.btn_export.on_clicked(self._export_results)
        
        # Finish button
        ax_finish = plt.axes([0.5, btn_y, btn_width, btn_height])
        self.btn_finish = Button(ax_finish, 'Finish\\nValidation', color='lightsteelblue')
        self.btn_finish.on_clicked(self._finish_validation)
        
        # Reasoning text input
        ax_reasoning = plt.axes([0.65, btn_y, 0.3, btn_height])
        self.txt_reasoning = TextBox(ax_reasoning, 'Reasoning: ', initial='')
        
        # Instructions
        instructions = """
🎮 Controls: [Validate] [Reject] [Add Peak] [Export] [Finish] | Reasoning: [Text Input]
📝 Workflow: 1) Click peak → 2) Add reasoning → 3) Validate/Reject → 4) Repeat → 5) Finish
        """
        
        self.ax_controls.text(0.5, 0.7, instructions, transform=self.ax_controls.transAxes,
                             ha='center', va='center', fontsize=10,
                             bbox=dict(boxstyle='round,pad=0.5', facecolor='wheat', alpha=0.8))
    
    def _on_peak_click(self, event):
        """Handle peak selection clicks"""
        if event.artist in self.ax_main.collections:
            # Find which peak was clicked
            for i, peak in enumerate(self.validated_peaks):
                if 'voltage' in peak and 'current' in peak:
                    # Simple distance check (could be improved)
                    if abs(event.mouseevent.xdata - peak['voltage']) < 0.02:
                        self.selected_peak_index = i
                        print(f"📌 Selected peak {i+1}: {peak['voltage']:.3f}V, {peak['current']:.1f}µA")
                        self._update_main_plot()
                        self._update_info_panel()
                        break
    
    def _on_plot_click(self, event):
        """Handle plot area clicks for adding peaks"""
        if event.dblclick and event.inaxes == self.ax_main:
            # Double-click to add new peak
            voltage = event.xdata
            current = event.ydata
            
            new_peak = {
                'voltage': voltage,
                'current': current,
                'confidence': 100.0,  # Human-added peaks have high confidence
                'method': 'human_added',
                'timestamp': datetime.now().isoformat(),
                'validated': False  # Needs validation
            }
            
            self.validated_peaks.append(new_peak)
            self.selected_peak_index = len(self.validated_peaks) - 1
            
            print(f"➕ Added new peak: {voltage:.3f}V, {current:.1f}µA")
            self._update_main_plot()
            self._update_info_panel()
            self._update_peak_list()
    
    def _validate_peak(self, event):
        """Validate selected peak"""
        if self.selected_peak_index is not None:
            peak = self.validated_peaks[self.selected_peak_index]
            reasoning = self.txt_reasoning.text.strip()
            
            if not reasoning:
                print("⚠️  Please provide reasoning for validation")
                return
            
            peak['validated'] = True
            peak['expert_reasoning'] = reasoning
            peak['validation_timestamp'] = datetime.now().isoformat()
            
            self.peak_validations.append({
                'peak_index': self.selected_peak_index,
                'action': 'validated',
                'reasoning': reasoning,
                'peak_data': peak.copy()
            })
            
            print(f"✅ Validated peak {self.selected_peak_index + 1}: {reasoning}")
            self.txt_reasoning.set_val('')  # Clear reasoning box
            self._update_main_plot()
            self._update_info_panel()
    
    def _reject_peak(self, event):
        """Reject selected peak"""
        if self.selected_peak_index is not None:
            reasoning = self.txt_reasoning.text.strip()
            
            if not reasoning:
                print("⚠️  Please provide reasoning for rejection")
                return
            
            peak = self.validated_peaks[self.selected_peak_index]
            
            self.peak_validations.append({
                'peak_index': self.selected_peak_index,
                'action': 'rejected',
                'reasoning': reasoning,
                'peak_data': peak.copy()
            })
            
            print(f"❌ Rejected peak {self.selected_peak_index + 1}: {reasoning}")
            
            # Remove peak
            del self.validated_peaks[self.selected_peak_index]
            self.selected_peak_index = None
            
            self.txt_reasoning.set_val('')  # Clear reasoning box
            self._update_main_plot()
            self._update_info_panel()
            self._update_peak_list()
    
    def _add_peak_mode(self, event):
        """Enter add peak mode"""
        print("➕ Add Peak Mode: Double-click on CV plot to add new peak")
    
    def _export_results(self, event):
        """Export current validation results"""
        results = self._compile_final_results()
        
        # Save to JSON
        filename = f"v6_validation_{self.current_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Exported validation results to: {filename}")
    
    def _finish_validation(self, event):
        """Finish validation and close UI"""
        validated_count = sum(1 for p in self.validated_peaks if p.get('validated', False))
        
        print(f"🎉 Validation complete!")
        print(f"   Original V5 peaks: {len(self.v5_peaks)}")
        print(f"   Final validated peaks: {validated_count}")
        print(f"   Total validations made: {len(self.peak_validations)}")
        
        plt.close(self.fig)
    
    def _compile_final_results(self):
        """Compile final validation results"""
        validated_peaks = [p for p in self.validated_peaks if p.get('validated', False)]
        
        results = {
            'filename': self.current_filename,
            'timestamp': datetime.now().isoformat(),
            'expert_id': self.session_data['expert_id'],
            'original_v5_peaks': len(self.v5_peaks),
            'final_validated_peaks': len(validated_peaks),
            'validation_actions': len(self.peak_validations),
            'validated_peaks': validated_peaks,
            'all_validations': self.peak_validations,
            'data_quality': 'human_validated',
            'version': 'enhanced_detector_v6'
        }
        
        return results

def test_v6_with_sample_data():
    """Test V6 with sample electrochemical data"""
    print("🧪 TESTING ENHANCED DETECTOR V6")
    print("=" * 50)
    
    # Create V6 detector
    v6 = EnhancedDetectorV6()
    
    # Generate sample CV data (ferrocyanide-like)
    voltage = np.linspace(-0.4, 0.7, 220)
    
    # Realistic ferrocyanide CV
    anodic_peak = 15e-6 * np.exp(-((voltage - 0.2) / 0.08)**2)
    cathodic_peak = -12e-6 * np.exp(-((voltage + 0.1) / 0.08)**2)
    background = 1e-8 * voltage
    noise = 0.5e-6 * np.random.normal(0, 1, len(voltage))
    
    current = (anodic_peak + cathodic_peak + background + noise) * 1e6  # µA
    
    print("📊 Sample Data Generated:")
    print(f"   Voltage range: {voltage.min():.2f} to {voltage.max():.2f} V")
    print(f"   Current range: {current.min():.2f} to {current.max():.2f} µA")
    print(f"   Data points: {len(voltage)}")
    
    # Run V6 validation
    print("\\n🔬 Starting V6 Interactive Validation...")
    print("🎯 Instructions:")
    print("   1. Click on peaks to select them")
    print("   2. Add reasoning in the text box")
    print("   3. Click 'Validate Peak' or 'Reject Peak'")
    print("   4. Double-click to add new peaks")
    print("   5. Click 'Finish Validation' when done")
    
    results = v6.detect_peaks_with_validation(voltage, current, "test_ferrocyanide.csv")
    
    return results

if __name__ == "__main__":
    print("🔬 Enhanced Detector V6 - Human-Validated Peak Detection")
    print("=" * 60)
    print("✨ Interactive peak validation system")
    print("🎯 Creates high-quality training data for DeepCV")
    print()
    
    try:
        results = test_v6_with_sample_data()
        
        if results:
            print("\\n📊 Final Results Summary:")
            print(f"   File: {results['filename']}")
            print(f"   Original V5 peaks: {results['original_v5_peaks']}")
            print(f"   Validated peaks: {results['final_validated_peaks']}")
            print(f"   Validation actions: {results['validation_actions']}")
        
        print("\\n✅ V6 test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing V6: {e}")
        import traceback
        traceback.print_exc()