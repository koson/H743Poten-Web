#!/usr/bin/env python3
"""
Interactive Palmsens Baseline Correction Tool
============================================
Tool for manual baseline correction of Palmsens CV files
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector, Button
from pathlib import Path
import json
import re
from typing import Dict, Optional, Tuple
from datetime import datetime

class InteractivePalmsensCorrector:
    """Interactive tool for baseline correction of Palmsens CV data"""
    
    def __init__(self):
        self.current_file = None
        self.voltage = None
        self.current = None
        self.original_current = None
        self.corrected_current = None
        
        # UI elements
        self.fig = None
        self.ax = None
        self.span_selector = None
        self.save_button = None
        self.next_button = None
        self.skip_button = None
        
        # Baseline data
        self.baseline_start = None
        self.baseline_end = None
        
        # File management
        self.file_list = []
        self.current_file_index = 0
        self.corrections_file = "palmsens_baseline_corrections.json"
        self.corrections = self.load_corrections()
        
    def load_corrections(self) -> Dict:
        """Load existing baseline corrections"""
        try:
            with open(self.corrections_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_corrections(self):
        """Save baseline corrections to file"""
        with open(self.corrections_file, 'w') as f:
            json.dump(self.corrections, f, indent=2)
        print(f"✅ Corrections saved to {self.corrections_file}")
    
    def extract_metadata(self, filename: str) -> Dict:
        """Extract concentration and scan rate from filename"""
        filename_lower = filename.lower()
        
        # Concentration
        concentration = None
        if 'palmsens_' in filename_lower:
            conc_match = re.search(r'palmsens_(\d+\.?\d*)mm', filename_lower)
            if conc_match:
                try:
                    concentration = float(conc_match.group(1))
                except ValueError:
                    pass
        
        # Scan rate
        scan_rate = None
        sr_patterns = [
            r'(\d+\.?\d*)\s*mv[\/\-_]?s',
            r'cv[_\-](\d+\.?\d*)mvps'
        ]
        
        for pattern in sr_patterns:
            match = re.search(pattern, filename_lower)
            if match:
                try:
                    scan_rate = float(match.group(1))
                    break
                except ValueError:
                    continue
        
        return {
            'concentration': concentration,
            'scan_rate': scan_rate
        }
    
    def find_problematic_files(self) -> list:
        """Find files that might need baseline correction"""
        print("🔍 Searching for Palmsens files that might need baseline correction...")
        
        data_dir = Path("Test_data/Palmsens")
        all_files = list(data_dir.rglob("*.csv"))
        
        problematic_files = []
        
        for file_path in all_files:
            try:
                # Quick check for files that might have baseline issues
                df = pd.read_csv(file_path, encoding='utf-8-sig', skiprows=1 if 
                               open(file_path, 'r').readline().startswith('FileName:') else 0)
                
                if 'V' not in df.columns or 'uA' not in df.columns:
                    continue
                
                current = df['uA'].values
                if len(current) < 50:
                    continue
                
                # Simple heuristic: large baseline offset or drift
                baseline_start = np.mean(current[:10])
                baseline_end = np.mean(current[-10:])
                baseline_diff = abs(baseline_end - baseline_start)
                current_range = np.max(current) - np.min(current)
                
                # If baseline drift is > 10% of current range, flag it
                if baseline_diff > 0.1 * current_range or abs(baseline_start) > 0.2 * current_range:
                    metadata = self.extract_metadata(str(file_path))
                    if metadata['concentration'] is not None and metadata['scan_rate'] is not None:
                        problematic_files.append({
                            'path': file_path,
                            'metadata': metadata,
                            'baseline_issues': {
                                'drift': baseline_diff,
                                'offset': abs(baseline_start),
                                'ratio': baseline_diff / current_range
                            }
                        })
                        
            except Exception:
                continue
        
        # Sort by severity of baseline issues
        problematic_files.sort(key=lambda x: x['baseline_issues']['ratio'], reverse=True)
        
        print(f"📊 Found {len(problematic_files)} files that might need correction")
        return problematic_files[:20]  # Limit to top 20 most problematic
    
    def load_file(self, file_info: dict):
        """Load a file for baseline correction"""
        file_path = file_info['path']
        self.current_file = str(file_path)
        
        print(f"\n📂 Loading: {file_path.name}")
        print(f"   Concentration: {file_info['metadata']['concentration']} mM")
        print(f"   Scan rate: {file_info['metadata']['scan_rate']} mV/s")
        
        # Read file
        with open(file_path, 'r') as f:
            first_line = f.readline().strip()
        
        skiprows = 1 if first_line.startswith('FileName:') else 0
        df = pd.read_csv(file_path, encoding='utf-8-sig', skiprows=skiprows)
        
        self.voltage = df['V'].values
        self.current = df['uA'].values
        self.original_current = self.current.copy()
        self.corrected_current = self.current.copy()
        
        # Reset baseline selection
        self.baseline_start = None
        self.baseline_end = None
    
    def setup_interactive_plot(self):
        """Setup the interactive plot for baseline selection"""
        if self.fig is not None:
            plt.close(self.fig)
        
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.ax.set_position([0.1, 0.15, 0.8, 0.75])  # Make room for buttons
        
        # Plot original data
        self.ax.plot(self.voltage, self.original_current, 'b-', alpha=0.7, 
                    label='Original', linewidth=1)
        self.ax.plot(self.voltage, self.corrected_current, 'r-', alpha=0.8, 
                    label='Corrected', linewidth=2)
        
        self.ax.set_xlabel('Voltage (V)')
        self.ax.set_ylabel('Current (µA)')
        self.ax.set_title(f'Baseline Correction: {Path(self.current_file).name}')
        self.ax.legend()
        self.ax.grid(True, alpha=0.3)
        
        # Setup span selector for baseline region
        self.span_selector = SpanSelector(
            self.ax, self.on_baseline_select, 'horizontal',
            useblit=True, span_stays=True,
            props=dict(alpha=0.3, facecolor='yellow')
        )
        
        # Add buttons
        ax_save = plt.axes([0.1, 0.02, 0.15, 0.05])
        self.save_button = Button(ax_save, 'Save Correction')
        self.save_button.on_clicked(self.save_current_correction)
        
        ax_next = plt.axes([0.3, 0.02, 0.15, 0.05])
        self.next_button = Button(ax_next, 'Next File')
        self.next_button.on_clicked(self.next_file)
        
        ax_skip = plt.axes([0.5, 0.02, 0.15, 0.05])
        self.skip_button = Button(ax_skip, 'Skip File')
        self.skip_button.on_clicked(self.skip_file)
        
        # Instructions
        self.fig.suptitle('Instructions: Drag to select baseline region, then click "Save Correction"', 
                         fontsize=12, y=0.95)
        
        plt.show()
    
    def on_baseline_select(self, vmin: float, vmax: float):
        """Handle baseline region selection"""
        self.baseline_start = vmin
        self.baseline_end = vmax
        
        print(f"📏 Selected baseline region: {vmin:.3f} V to {vmax:.3f} V")
        
        # Apply baseline correction
        self.apply_baseline_correction()
        
        # Update plot
        self.ax.clear()
        self.ax.plot(self.voltage, self.original_current, 'b-', alpha=0.7, 
                    label='Original', linewidth=1)
        self.ax.plot(self.voltage, self.corrected_current, 'r-', alpha=0.8, 
                    label='Corrected', linewidth=2)
        
        # Highlight baseline region
        mask = (self.voltage >= vmin) & (self.voltage <= vmax)
        if np.any(mask):
            self.ax.plot(self.voltage[mask], self.original_current[mask], 
                        'yo', markersize=3, alpha=0.7, label='Baseline region')
        
        self.ax.set_xlabel('Voltage (V)')
        self.ax.set_ylabel('Current (µA)')
        self.ax.set_title(f'Baseline Correction: {Path(self.current_file).name}')
        self.ax.legend()
        self.ax.grid(True, alpha=0.3)
        
        plt.draw()
    
    def apply_baseline_correction(self):
        """Apply baseline correction using selected region"""
        if self.baseline_start is None or self.baseline_end is None:
            return
        
        # Find points in baseline region
        mask = (self.voltage >= self.baseline_start) & (self.voltage <= self.baseline_end)
        
        if not np.any(mask):
            print("⚠️ No points found in selected baseline region")
            return
        
        # Linear fit to baseline region
        baseline_v = self.voltage[mask]
        baseline_i = self.original_current[mask]
        
        if len(baseline_v) >= 2:
            # Linear regression
            coeffs = np.polyfit(baseline_v, baseline_i, 1)
            baseline_fit = np.polyval(coeffs, self.voltage)
            
            # Apply correction
            self.corrected_current = self.original_current - baseline_fit
            
            print(f"✅ Applied baseline correction (slope: {coeffs[0]:.3e}, intercept: {coeffs[1]:.3f})")
    
    def save_current_correction(self, event):
        """Save the current baseline correction"""
        if self.baseline_start is None or self.baseline_end is None:
            print("⚠️ No baseline region selected")
            return
        
        correction_data = {
            'baseline_start': self.baseline_start,
            'baseline_end': self.baseline_end,
            'timestamp': datetime.now().isoformat(),
            'original_file': self.current_file
        }
        
        self.corrections[self.current_file] = correction_data
        self.save_corrections()
        
        print(f"✅ Baseline correction saved for {Path(self.current_file).name}")
    
    def next_file(self, event):
        """Move to next file"""
        self.current_file_index += 1
        if self.current_file_index < len(self.file_list):
            self.load_file(self.file_list[self.current_file_index])
            self.setup_interactive_plot()
        else:
            print("🎉 All files processed!")
            plt.close(self.fig)
    
    def skip_file(self, event):
        """Skip current file without saving"""
        print(f"⏭️ Skipped {Path(self.current_file).name}")
        self.next_file(event)
    
    def run_interactive_correction(self):
        """Main method to run interactive baseline correction"""
        print("🚀 Starting Interactive Palmsens Baseline Correction")
        print("=" * 55)
        
        # Find problematic files
        self.file_list = self.find_problematic_files()
        
        if not self.file_list:
            print("✅ No files found that need baseline correction")
            return
        
        print(f"\n📊 Found {len(self.file_list)} files to review")
        print("🎯 Starting with the most problematic files...")
        
        # Start with first file
        self.current_file_index = 0
        self.load_file(self.file_list[0])
        self.setup_interactive_plot()
        
        print("\n📋 Instructions:")
        print("   1. Drag mouse to select baseline region")
        print("   2. Click 'Save Correction' to save the correction")
        print("   3. Click 'Next File' to move to next file")
        print("   4. Click 'Skip File' to skip without saving")

def main():
    """Main execution"""
    corrector = InteractivePalmsensCorrector()
    corrector.run_interactive_correction()

if __name__ == "__main__":
    main()