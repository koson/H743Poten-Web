#!/usr/bin/env python3
"""
Interactive Baseline Selection for CV Analysis
=============================================
Prototype for manual baseline correction with mouse selection
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, SpanSelector
from matplotlib.patches import Rectangle
import json
from pathlib import Path
from scipy import stats
from scipy.optimize import curve_fit
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class InteractiveBaselineSelector:
    """Interactive baseline selection tool for CV data"""
    
    def __init__(self, file_path: str):
        """Initialize with CV data file"""
        self.file_path = Path(file_path)
        self.data = None
        self.voltage = None
        self.current = None
        self.baseline_indices = None
        self.baseline_fit = None
        self.peak_height = None
        self.peak_area = None
        self.corrections = {}
        
        # UI state
        self.selection_mode = False
        self.selected_range = None
        
        # Load data
        self.load_data()
        
    def load_data(self):
        """Load CV data from file"""
        try:
            # Check if first line is metadata
            with open(self.file_path, 'r') as f:
                first_line = f.readline().strip()
            
            skiprows = 1 if first_line.startswith('FileName:') else 0
            self.data = pd.read_csv(self.file_path, encoding='utf-8-sig', skiprows=skiprows)
            
            # Try different column combinations
            if 'V' in self.data.columns and 'uA' in self.data.columns:
                self.voltage = self.data['V'].values
                self.current = self.data['uA'].values
            elif 'Voltage' in self.data.columns and 'Current' in self.data.columns:
                self.voltage = self.data['Voltage'].values
                self.current = self.data['Current'].values
            else:
                raise ValueError("Could not find voltage and current columns")
            
            # Remove NaN values
            mask = ~(np.isnan(self.voltage) | np.isnan(self.current))
            self.voltage = self.voltage[mask]
            self.current = self.current[mask]
            
            logger.info(f"Loaded {len(self.voltage)} data points from {self.file_path.name}")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def auto_detect_baseline(self):
        """Automatic baseline detection (existing algorithm)"""
        # Simple method: use bottom 30% of voltage range
        v_min, v_max = np.min(self.voltage), np.max(self.voltage)
        v_range = v_max - v_min
        baseline_threshold = v_min + 0.3 * v_range
        
        # Find indices where voltage is in baseline region
        baseline_mask = self.voltage <= baseline_threshold
        self.baseline_indices = np.where(baseline_mask)[0]
        
        if len(self.baseline_indices) < 5:
            # Fallback: use first and last 10% of points
            n_points = len(self.voltage)
            start_idx = int(0.1 * n_points)
            end_idx = int(0.9 * n_points)
            self.baseline_indices = np.concatenate([
                np.arange(0, start_idx),
                np.arange(end_idx, n_points)
            ])
        
        self.fit_baseline()
    
    def fit_baseline(self):
        """Fit baseline using selected indices"""
        if self.baseline_indices is None or len(self.baseline_indices) < 2:
            logger.warning("No baseline indices selected")
            return
        
        # Get baseline points
        baseline_v = self.voltage[self.baseline_indices]
        baseline_i = self.current[self.baseline_indices]
        
        # Fit linear baseline
        slope, intercept, r_value, p_value, std_err = stats.linregress(baseline_v, baseline_i)
        
        # Calculate baseline for all voltage points
        self.baseline_fit = slope * self.voltage + intercept
        
        # Calculate peak metrics
        corrected_current = self.current - self.baseline_fit
        self.peak_height = np.max(corrected_current) - np.min(corrected_current)
        self.peak_area = abs(np.trapz(corrected_current, self.voltage))
        
        logger.info(f"Baseline fit: slope={slope:.2e}, R²={r_value**2:.3f}")
        logger.info(f"Peak height: {self.peak_height:.2f} µA")
        logger.info(f"Peak area: {self.peak_area:.2f} µA⋅V")
    
    def on_baseline_select(self, vmin, vmax):
        """Handle baseline selection from SpanSelector"""
        if not self.selection_mode:
            return
        
        # Find indices within selected voltage range
        mask = (self.voltage >= vmin) & (self.voltage <= vmax)
        self.baseline_indices = np.where(mask)[0]
        
        # Re-fit baseline
        self.fit_baseline()
        
        # Update plot
        self.update_plot()
        
        # Store correction
        self.corrections[self.file_path.name] = {
            'voltage_range': [vmin, vmax],
            'baseline_indices': self.baseline_indices.tolist(),
            'peak_height': self.peak_height,
            'peak_area': self.peak_area
        }
        
        logger.info(f"Baseline updated: {vmin:.3f}V to {vmax:.3f}V")
        logger.info(f"New peak height: {self.peak_height:.2f} µA")
    
    def toggle_selection_mode(self, event):
        """Toggle baseline selection mode"""
        self.selection_mode = not self.selection_mode
        
        if self.selection_mode:
            self.selection_button.label.set_text('Exit Selection')
            self.selection_button.color = 'red'
            logger.info("Baseline selection mode: ON - Drag to select baseline region")
        else:
            self.selection_button.label.set_text('Select Baseline')
            self.selection_button.color = 'lightblue'
            logger.info("Baseline selection mode: OFF")
        
        plt.draw()
    
    def reset_baseline(self, event):
        """Reset to automatic baseline detection"""
        self.auto_detect_baseline()
        self.update_plot()
        logger.info("Reset to automatic baseline detection")
    
    def save_corrections(self, event):
        """Save baseline corrections to file"""
        if not self.corrections:
            logger.warning("No corrections to save")
            return
        
        corrections_file = self.file_path.parent / "baseline_corrections.json"
        
        # Load existing corrections if file exists
        existing_corrections = {}
        if corrections_file.exists():
            with open(corrections_file, 'r') as f:
                existing_corrections = json.load(f)
        
        # Update with new corrections
        existing_corrections.update(self.corrections)
        
        # Save to file
        with open(corrections_file, 'w') as f:
            json.dump(existing_corrections, f, indent=2)
        
        logger.info(f"Baseline corrections saved to {corrections_file}")
    
    def update_plot(self):
        """Update the plot with current baseline and metrics"""
        # Clear and redraw
        self.ax.clear()
        
        # Plot original data
        self.ax.plot(self.voltage, self.current, 'b-', alpha=0.7, label='CV Data')
        
        # Plot baseline
        if self.baseline_fit is not None:
            self.ax.plot(self.voltage, self.baseline_fit, 'r--', linewidth=2, 
                        label=f'Baseline (Linear Fit)')
            
            # Plot baseline-corrected data
            corrected = self.current - self.baseline_fit
            self.ax.plot(self.voltage, corrected, 'g-', alpha=0.7, 
                        label=f'Corrected (Peak H: {self.peak_height:.1f}µA)')
        
        # Highlight baseline points
        if self.baseline_indices is not None:
            baseline_v = self.voltage[self.baseline_indices]
            baseline_i = self.current[self.baseline_indices]
            self.ax.scatter(baseline_v, baseline_i, c='red', s=30, alpha=0.8, 
                          label=f'Baseline Points ({len(self.baseline_indices)})')
        
        self.ax.set_xlabel('Voltage (V)')
        self.ax.set_ylabel('Current (µA)')
        self.ax.set_title(f'{self.file_path.name}\nPeak Height: {self.peak_height:.2f} µA, Area: {self.peak_area:.2f} µA⋅V')
        self.ax.legend()
        self.ax.grid(True, alpha=0.3)
        
        plt.draw()
    
    def create_interactive_plot(self):
        """Create interactive plot with baseline selection"""
        # Create figure and axis
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        plt.subplots_adjust(bottom=0.2)
        
        # Initial baseline detection
        self.auto_detect_baseline()
        self.update_plot()
        
        # Create SpanSelector for baseline selection
        self.span_selector = SpanSelector(
            self.ax, self.on_baseline_select, 'horizontal',
            useblit=True, rectprops=dict(alpha=0.3, facecolor='yellow')
        )
        
        # Create buttons
        # Selection mode button
        ax_select = plt.axes([0.1, 0.05, 0.15, 0.05])
        self.selection_button = Button(ax_select, 'Select Baseline')
        self.selection_button.on_clicked(self.toggle_selection_mode)
        
        # Reset button
        ax_reset = plt.axes([0.3, 0.05, 0.1, 0.05])
        reset_button = Button(ax_reset, 'Reset')
        reset_button.on_clicked(self.reset_baseline)
        
        # Save button
        ax_save = plt.axes([0.45, 0.05, 0.1, 0.05])
        save_button = Button(ax_save, 'Save')
        save_button.on_clicked(self.save_corrections)
        
        # Instructions
        plt.figtext(0.6, 0.08, 
                   "Instructions:\n1. Click 'Select Baseline' to enable selection\n2. Drag to select baseline region\n3. Click 'Save' to store corrections", 
                   fontsize=10, ha='left')
        
        plt.show()

def main():
    """Main function to run interactive baseline selector"""
    # Example usage with a sample file
    sample_files = [
        "test_data/raw_stm32/Pipot_Ferro_1_0mM_20mVpS_E4_scan_05.csv",
        "Test_data/Stm32/Pipot_Ferro_1_0mM_20mVpS_E4_scan_05.csv"
    ]
    
    # Find an existing file
    test_file = None
    for file_path in sample_files:
        if Path(file_path).exists():
            test_file = file_path
            break
    
    if test_file is None:
        logger.error("No test file found. Please specify a valid CV data file.")
        return
    
    # Create interactive baseline selector
    logger.info(f"Opening interactive baseline selector for: {test_file}")
    selector = InteractiveBaselineSelector(test_file)
    selector.create_interactive_plot()

if __name__ == "__main__":
    main()