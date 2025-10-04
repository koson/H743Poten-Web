#!/usr/bin/env python3
"""
🎯 CV Peak Validation Standalone GUI
====================================

Standalone matplotlib-based GUI for CV peak validation.
Features similar UI to the web version but using matplotlib widgets.

Usage:
python cv_validation_standalone.py

Author: H743Poten Research Team
Date: October 4, 2025
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, CheckButtons, RadioButtons
import matplotlib.patches as patches
from datetime import datetime
import glob
from pathlib import Path

# Add validation_data to path
sys.path.append('validation_data')

try:
    from enhanced_detector_v6_improved import EnhancedDetectorV6Improved, ValidationDatabase
    from enhanced_detector_v5 import EnhancedDetectorV5
except ImportError as e:
    print(f"⚠️  Import warning: {e}")
    EnhancedDetectorV6Improved = None
    EnhancedDetectorV5 = None

class CVPeakValidationGUI:
    """Standalone GUI for CV Peak Validation"""
    
    def __init__(self):
        self.test_data_path = "Test_Data_CV"
        self.detector_v6 = EnhancedDetectorV6Improved() if EnhancedDetectorV6Improved else None
        self.detector_v5 = EnhancedDetectorV5() if EnhancedDetectorV5 else None
        self.database = ValidationDatabase() if ValidationDatabase else None
        
        # Data storage
        self.cv_files = []
        self.current_file_index = 0
        self.current_cv_data = None
        self.current_peaks = []
        self.peak_validations = {}
        self.current_session = None
        
        # UI state
        self.selected_peaks = set()
        
        print("🎯 CV Peak Validation Standalone GUI")
        print(f"📁 Test data path: {self.test_data_path}")
        
        self.load_cv_files()
        self.create_ui()
    
    def load_cv_files(self):
        """Load available CV files"""
        try:
            self.cv_files = []
            if os.path.exists(self.test_data_path):
                # Find all CSV files
                pattern = os.path.join(self.test_data_path, "**", "*.csv")
                csv_files = glob.glob(pattern, recursive=True)
                
                for csv_file in csv_files[:50]:  # Limit to first 50 files for demo
                    filename = os.path.basename(csv_file)
                    metadata = self._extract_metadata(filename)
                    
                    self.cv_files.append({
                        'filename': filename,
                        'path': csv_file,
                        'metadata': metadata
                    })
                
                # Sort by compound and concentration
                self.cv_files.sort(key=lambda x: (x['metadata'].get('compound', ''), 
                                                x['metadata'].get('concentration', 0)))
                
                print(f"📁 Loaded {len(self.cv_files)} CV files")
            else:
                print(f"⚠️  {self.test_data_path} not found")
                
        except Exception as e:
            print(f"❌ Error loading files: {e}")
            self.cv_files = []
    
    def _extract_metadata(self, filename):
        """Extract metadata from filename"""
        metadata = {
            'compound': 'Unknown',
            'concentration': 0,
            'scan_rate': 0,
            'electrode': 1,
            'scan_number': 1
        }
        
        try:
            # Parse different filename formats
            filename_lower = filename.lower()
            
            if 'ferro' in filename_lower:
                metadata['compound'] = 'Ferrocyanide'
            elif 'dopamine' in filename_lower:
                metadata['compound'] = 'Dopamine'
            elif 'ascorbic' in filename_lower:
                metadata['compound'] = 'Ascorbic Acid'
            
            # Extract concentration
            parts = filename.replace('.csv', '').split('_')
            for part in parts:
                if 'mm' in part.lower():
                    conc_str = part.lower().replace('mm', '')
                    try:
                        if '-' in conc_str:
                            conc_str = conc_str.split('-')[1]
                        conc_str = conc_str.replace('_', '.')
                        metadata['concentration'] = float(conc_str)
                    except:
                        pass
                elif 'mvps' in part.lower():
                    try:
                        scan_rate = int(part.lower().replace('mvps', ''))
                        metadata['scan_rate'] = scan_rate
                    except:
                        pass
                        
        except Exception as e:
            print(f"⚠️  Error parsing {filename}: {e}")
        
        return metadata
    
    def create_ui(self):
        """Create the matplotlib GUI"""
        # Create figure with subplots
        self.fig = plt.figure(figsize=(16, 10))
        self.fig.suptitle('CV Peak Validation - DeepCV Training Interface', fontsize=16, fontweight='bold')
        
        # Main plot area
        self.ax_main = plt.subplot2grid((4, 4), (0, 0), colspan=3, rowspan=3)
        
        # Control panels
        self.ax_files = plt.subplot2grid((4, 4), (0, 3), rowspan=1)
        self.ax_peaks = plt.subplot2grid((4, 4), (1, 3), rowspan=2)
        self.ax_controls = plt.subplot2grid((4, 4), (3, 0), colspan=4)
        
        self.setup_controls()
        
        if self.cv_files:
            self.load_current_file()
        
        plt.tight_layout()
        plt.show()
    
    def setup_controls(self):
        """Setup control widgets"""
        # File navigation
        self.ax_files.set_title('File Navigation', fontsize=10, fontweight='bold')
        self.ax_files.axis('off')
        
        # Previous/Next buttons
        ax_prev = plt.axes([0.75, 0.80, 0.08, 0.04])
        ax_next = plt.axes([0.84, 0.80, 0.08, 0.04])
        
        self.btn_prev = Button(ax_prev, 'Previous', color='lightblue')
        self.btn_next = Button(ax_next, 'Next', color='lightblue')
        
        self.btn_prev.on_clicked(self.prev_file)
        self.btn_next.on_clicked(self.next_file)
        
        # Peak validation controls
        self.ax_peaks.set_title('Peak Validation', fontsize=10, fontweight='bold')
        self.ax_peaks.axis('off')
        
        # Validation buttons
        ax_validate = plt.axes([0.75, 0.45, 0.08, 0.04])
        ax_reject = plt.axes([0.84, 0.45, 0.08, 0.04])
        ax_select_all = plt.axes([0.75, 0.40, 0.08, 0.04])
        ax_clear = plt.axes([0.84, 0.40, 0.08, 0.04])
        ax_export = plt.axes([0.75, 0.35, 0.17, 0.04])
        
        self.btn_validate = Button(ax_validate, 'Validate', color='lightgreen')
        self.btn_reject = Button(ax_reject, 'Reject', color='lightcoral')
        self.btn_select_all = Button(ax_select_all, 'Select All', color='lightyellow')
        self.btn_clear = Button(ax_clear, 'Clear', color='lightgray')
        self.btn_export = Button(ax_export, 'Export Training Data', color='lightsteelblue')
        
        self.btn_validate.on_clicked(self.validate_selected)
        self.btn_reject.on_clicked(self.reject_selected)
        self.btn_select_all.on_clicked(self.select_all_peaks)
        self.btn_clear.on_clicked(self.clear_selection)
        self.btn_export.on_clicked(self.export_training_data)
        
        # Status display
        self.ax_controls.axis('off')
        self.status_text = self.ax_controls.text(0.02, 0.8, 'Ready', fontsize=12, 
                                               transform=self.ax_controls.transAxes)
        self.file_info_text = self.ax_controls.text(0.02, 0.6, '', fontsize=10,
                                                  transform=self.ax_controls.transAxes)
        self.peak_info_text = self.ax_controls.text(0.02, 0.4, '', fontsize=10,
                                                  transform=self.ax_controls.transAxes)
        self.validation_info_text = self.ax_controls.text(0.02, 0.2, '', fontsize=10,
                                                        transform=self.ax_controls.transAxes)
    
    def load_current_file(self):
        """Load and analyze current CV file"""
        if not self.cv_files or self.current_file_index >= len(self.cv_files):
            return
        
        current_file = self.cv_files[self.current_file_index]
        
        try:
            # Update status
            self.status_text.set_text(f'Loading file {self.current_file_index + 1}/{len(self.cv_files)}...')
            self.fig.canvas.draw()
            
            # Load CV data
            self.current_cv_data = self._load_cv_data(current_file['path'])
            
            if self.current_cv_data is None:
                self.status_text.set_text('❌ Failed to load CV data')
                return
            
            # Detect peaks
            self.current_peaks = self._detect_peaks(
                self.current_cv_data['voltage'], 
                self.current_cv_data['current']
            )
            
            # Create validation session
            self.current_session = self._create_validation_session(current_file)
            
            # Reset UI state
            self.selected_peaks.clear()
            self.peak_validations = {}
            
            # Update display
            self.plot_cv_data()
            self.update_info_display()
            
            self.status_text.set_text('✅ Analysis complete - Select peaks to validate/reject')
            
        except Exception as e:
            self.status_text.set_text(f'❌ Error: {str(e)}')
            print(f"Error loading file: {e}")
    
    def _load_cv_data(self, file_path):
        """Load CV data from file"""
        try:
            df = pd.read_csv(file_path)
            
            # Handle different CSV formats
            if 'Voltage' in df.columns and 'Current' in df.columns:
                voltage = df['Voltage'].values
                current = df['Current'].values
            elif len(df.columns) >= 2:
                voltage = df.iloc[:, 0].values  
                current = df.iloc[:, 1].values
            else:
                return None
            
            return {
                'voltage': voltage,
                'current': current,
                'filename': os.path.basename(file_path),
                'file_path': file_path
            }
            
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None
    
    def _detect_peaks(self, voltage, current):
        """Detect peaks using available detectors"""
        try:
            if self.detector_v5:
                # Use Enhanced V5
                result = self.detector_v5.detect_peaks_enhanced_v5(voltage, current)
                
                if result and 'peaks' in result:
                    peaks = []
                    for i, peak in enumerate(result['peaks']):
                        peaks.append({
                            'id': i,
                            'voltage': peak.get('voltage', 0.0),
                            'current': peak.get('current', 0.0),
                            'type': peak.get('type', 'unknown'),
                            'confidence': peak.get('confidence', 0.5),
                            'snr': peak.get('snr', 1.0),
                            'method': 'Enhanced_V5'
                        })
                    return peaks
            
            # Fallback detection
            return self._fallback_peak_detection(voltage, current)
            
        except Exception as e:
            print(f"Peak detection error: {e}")
            return []
    
    def _fallback_peak_detection(self, voltage, current):
        """Simple fallback peak detection"""
        try:
            # Basic peak detection using numpy
            current_std = np.std(current)
            current_mean = np.mean(current)
            
            # Find local maxima and minima
            peaks = []
            for i in range(2, len(current) - 2):
                # Check for local maximum (oxidation)
                if (current[i] > current[i-1] and current[i] > current[i+1] and
                    current[i] > current_mean + current_std):
                    peaks.append({
                        'id': len(peaks),
                        'voltage': voltage[i],
                        'current': current[i],
                        'type': 'oxidation',
                        'confidence': 0.7,
                        'snr': abs(current[i] - current_mean) / current_std,
                        'method': 'Fallback'
                    })
                
                # Check for local minimum (reduction)
                elif (current[i] < current[i-1] and current[i] < current[i+1] and
                      current[i] < current_mean - current_std):
                    peaks.append({
                        'id': len(peaks),
                        'voltage': voltage[i],
                        'current': current[i],
                        'type': 'reduction',
                        'confidence': 0.7,
                        'snr': abs(current[i] - current_mean) / current_std,
                        'method': 'Fallback'
                    })
            
            return peaks[:10]  # Limit to 10 peaks
            
        except Exception as e:
            print(f"Fallback detection error: {e}")
            return []
    
    def _create_validation_session(self, file_info):
        """Create validation session"""
        try:
            if self.database:
                return self.database.create_session(
                    file_info['path'],
                    file_info['metadata']['compound'],
                    f"{file_info['metadata']['concentration']}mM",
                    f"{file_info['metadata']['scan_rate']}mV/s"
                )
            else:
                return f"gui_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        except Exception as e:
            print(f"Session creation error: {e}")
            return f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def plot_cv_data(self):
        """Plot CV data with detected peaks"""
        self.ax_main.clear()
        
        if not self.current_cv_data or not self.current_peaks:
            return
        
        voltage = self.current_cv_data['voltage']
        current = self.current_cv_data['current']
        
        # Plot CV curve
        self.ax_main.plot(voltage, current, 'b-', linewidth=2, label='CV Data', alpha=0.8)
        
        # Plot peaks
        peak_colors = {'oxidation': 'red', 'reduction': 'green', 'unknown': 'orange'}
        peak_markers = {'oxidation': 'o', 'reduction': '^', 'unknown': 's'}
        
        self.peak_artists = {}  # Store artists for click detection
        
        for peak in self.current_peaks:
            color = peak_colors.get(peak['type'], 'gray')
            marker = peak_markers.get(peak['type'], 'o')
            
            # Determine style based on validation status
            if peak['id'] in self.peak_validations:
                if self.peak_validations[peak['id']]['is_valid']:
                    edgecolor = 'darkgreen'
                    linewidth = 3
                else:
                    edgecolor = 'darkred'
                    linewidth = 3
            elif peak['id'] in self.selected_peaks:
                edgecolor = 'blue'
                linewidth = 3
            else:
                edgecolor = 'black'
                linewidth = 1
            
            artist = self.ax_main.scatter(peak['voltage'], peak['current'],
                                        c=color, s=120, marker=marker,
                                        edgecolors=edgecolor, linewidth=linewidth,
                                        alpha=0.8, picker=True)
            
            self.peak_artists[peak['id']] = artist
            
            # Add peak labels
            self.ax_main.annotate(f"{peak['id']}", 
                                (peak['voltage'], peak['current']),
                                xytext=(5, 5), textcoords='offset points',
                                fontsize=9, fontweight='bold',
                                bbox=dict(boxstyle='round,pad=0.2', 
                                        facecolor=color, alpha=0.7))
        
        # Setup plot
        current_file = self.cv_files[self.current_file_index]
        metadata = current_file['metadata']
        
        self.ax_main.set_xlabel('Voltage (V)', fontsize=12)
        self.ax_main.set_ylabel('Current (µA)', fontsize=12)
        self.ax_main.set_title(f"Peak Analysis: {metadata['compound']} "
                             f"({metadata['concentration']}mM) - {current_file['filename']}", 
                             fontsize=14, fontweight='bold')
        self.ax_main.grid(True, alpha=0.3)
        self.ax_main.legend()
        
        # Connect click events
        self.fig.canvas.mpl_connect('pick_event', self.on_peak_click)
        
        self.fig.canvas.draw()
    
    def on_peak_click(self, event):
        """Handle peak click events"""
        # Find which peak was clicked
        for peak_id, artist in self.peak_artists.items():
            if event.artist == artist:
                self.toggle_peak_selection(peak_id)
                break
    
    def toggle_peak_selection(self, peak_id):
        """Toggle peak selection"""
        if peak_id in self.selected_peaks:
            self.selected_peaks.remove(peak_id)
        else:
            self.selected_peaks.add(peak_id)
        
        self.plot_cv_data()  # Refresh plot
        self.update_info_display()
    
    def update_info_display(self):
        """Update information displays"""
        if not self.cv_files:
            return
        
        current_file = self.cv_files[self.current_file_index]
        metadata = current_file['metadata']
        
        # File info
        file_info = (f"File: {current_file['filename']}\n"
                    f"Compound: {metadata['compound']}\n"
                    f"Concentration: {metadata['concentration']}mM\n"
                    f"Scan Rate: {metadata['scan_rate']}mV/s")
        self.file_info_text.set_text(file_info)
        
        # Peak info  
        validated_count = len([v for v in self.peak_validations.values() if v['is_valid']])
        rejected_count = len([v for v in self.peak_validations.values() if not v['is_valid']])
        
        peak_info = (f"Peaks Detected: {len(self.current_peaks)}\n"
                    f"Selected: {len(self.selected_peaks)}\n"
                    f"Method: {self.current_peaks[0]['method'] if self.current_peaks else 'None'}")
        self.peak_info_text.set_text(peak_info)
        
        # Validation info
        validation_info = (f"Validated: {validated_count}\n"
                         f"Rejected: {rejected_count}\n"
                         f"Pending: {len(self.current_peaks) - validated_count - rejected_count}")
        self.validation_info_text.set_text(validation_info)
        
        self.fig.canvas.draw()
    
    def prev_file(self, event):
        """Load previous file"""
        if self.current_file_index > 0:
            self.current_file_index -= 1
            self.load_current_file()
    
    def next_file(self, event):
        """Load next file"""
        if self.current_file_index < len(self.cv_files) - 1:
            self.current_file_index += 1
            self.load_current_file()
    
    def validate_selected(self, event):
        """Validate selected peaks"""
        for peak_id in self.selected_peaks:
            self.peak_validations[peak_id] = {
                'peak_id': peak_id,
                'is_valid': True,
                'reasoning': 'GUI validation'
            }
            
            # Save to database
            if self.database and peak_id < len(self.current_peaks):
                peak = self.current_peaks[peak_id]
                self.database.save_peak_validation(
                    self.current_session, peak_id,
                    peak['voltage'], peak['current'], peak['type'],
                    True, peak['confidence'], 'GUI validation'
                )
        
        self.selected_peaks.clear()
        self.plot_cv_data()
        self.update_info_display()
        
        validated_count = len([v for v in self.peak_validations.values() if v['is_valid']])
        self.status_text.set_text(f'✅ Validated {validated_count} peaks total')
    
    def reject_selected(self, event):
        """Reject selected peaks"""
        for peak_id in self.selected_peaks:
            self.peak_validations[peak_id] = {
                'peak_id': peak_id,
                'is_valid': False,
                'reasoning': 'GUI rejection'
            }
            
            # Save to database
            if self.database and peak_id < len(self.current_peaks):
                peak = self.current_peaks[peak_id]
                self.database.save_peak_validation(
                    self.current_session, peak_id,
                    peak['voltage'], peak['current'], peak['type'],
                    False, peak['confidence'], 'GUI rejection'
                )
        
        self.selected_peaks.clear()
        self.plot_cv_data()
        self.update_info_display()
        
        rejected_count = len([v for v in self.peak_validations.values() if not v['is_valid']])
        self.status_text.set_text(f'❌ Rejected {rejected_count} peaks total')
    
    def select_all_peaks(self, event):
        """Select all peaks"""
        self.selected_peaks = set(range(len(self.current_peaks)))
        self.plot_cv_data()
        self.update_info_display()
        self.status_text.set_text(f'🔹 Selected all {len(self.current_peaks)} peaks')
    
    def clear_selection(self, event):
        """Clear peak selection"""
        self.selected_peaks.clear()
        self.plot_cv_data()
        self.update_info_display()
        self.status_text.set_text('🔸 Selection cleared')
    
    def export_training_data(self, event):
        """Export training data"""
        try:
            # Complete current session
            if self.database and self.current_session:
                validated_count = len([v for v in self.peak_validations.values() if v['is_valid']])
                rejected_count = len([v for v in self.peak_validations.values() if not v['is_valid']])
                notes = f"GUI validation: {validated_count} validated, {rejected_count} rejected"
                self.database.complete_session(self.current_session, notes)
            
            # Get training data
            if self.database:
                training_data = self.database.get_training_data(min_confidence=0.5)
                
                if not training_data.empty:
                    # Export to JSON
                    export_data = {
                        'timestamp': datetime.now().isoformat(),
                        'total_peaks': len(training_data),
                        'sessions': training_data['session_id'].nunique(),
                        'compounds': training_data['compound_name'].nunique(),
                        'peaks': training_data.to_dict('records')
                    }
                    
                    filename = f"cv_training_data_gui_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(filename, 'w') as f:
                        json.dump(export_data, f, indent=2)
                    
                    self.status_text.set_text(f'💾 Exported {len(training_data)} peaks to {filename}')
                else:
                    self.status_text.set_text('⚠️  No training data to export')
            else:
                self.status_text.set_text('❌ Database not available for export')
                
        except Exception as e:
            self.status_text.set_text(f'❌ Export error: {str(e)}')
            print(f"Export error: {e}")

def main():
    """Main function"""
    print("🎯 Starting CV Peak Validation Standalone GUI")
    
    try:
        gui = CVPeakValidationGUI()
        
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()