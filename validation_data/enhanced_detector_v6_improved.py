#!/usr/bin/env python3
"""
🚀 Enhanced Detector V6 - Improved Version
==========================================

Major improvements:
1. Better peak detection algorithm
2. Database storage for validation results
3. Batch validation UI for multiple peaks
4. Training data collection system
5. Session management and export

Author: H743Poten Research Team
Date: October 4, 2025
"""

import sys
import os
import json
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, CheckButtons
from datetime import datetime
import uuid
from pathlib import Path

sys.path.append('.')
sys.path.append('validation_data')

# Import Enhanced V5 as backend
try:
    from enhanced_detector_v5 import EnhancedDetectorV5
except ImportError:
    print("⚠️  Enhanced V5 not found, using mock detector")
    EnhancedDetectorV5 = None

class ValidationDatabase:
    """Database for storing validation results"""
    
    def __init__(self, db_path="validation_data/peak_validation.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Validation sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS validation_sessions (
                session_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                compound_name TEXT,
                concentration TEXT,
                scan_rate TEXT,
                date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validator_id TEXT,
                status TEXT DEFAULT 'in_progress',
                notes TEXT
            )
        ''')
        
        # Peak validations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS peak_validations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                peak_index INTEGER,
                voltage REAL,
                current REAL,
                peak_type TEXT,
                is_valid BOOLEAN,
                confidence REAL,
                reasoning TEXT,
                validation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES validation_sessions (session_id)
            )
        ''')
        
        # Training datasets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_name TEXT UNIQUE,
                description TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_count INTEGER,
                peak_count INTEGER,
                validation_accuracy REAL
            )
        ''')
        
        # Dataset-session mapping
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dataset_sessions (
                dataset_name TEXT,
                session_id TEXT,
                PRIMARY KEY (dataset_name, session_id),
                FOREIGN KEY (dataset_name) REFERENCES training_datasets (dataset_name),
                FOREIGN KEY (session_id) REFERENCES validation_sessions (session_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized: {self.db_path}")
    
    def create_session(self, filename, compound_name=None, concentration=None, scan_rate=None, validator_id="expert"):
        """Create new validation session"""
        session_id = str(uuid.uuid4())[:8]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO validation_sessions 
            (session_id, filename, compound_name, concentration, scan_rate, validator_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, filename, compound_name, concentration, scan_rate, validator_id))
        
        conn.commit()
        conn.close()
        
        print(f"📝 Created validation session: {session_id}")
        return session_id
    
    def save_peak_validation(self, session_id, peak_index, voltage, current, peak_type, is_valid, confidence, reasoning=""):
        """Save individual peak validation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO peak_validations 
            (session_id, peak_index, voltage, current, peak_type, is_valid, confidence, reasoning)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, peak_index, voltage, current, peak_type, is_valid, confidence, reasoning))
        
        conn.commit()
        conn.close()
    
    def complete_session(self, session_id, notes=""):
        """Mark session as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE validation_sessions 
            SET status = 'completed', notes = ?
            WHERE session_id = ?
        ''', (notes, session_id))
        
        conn.commit()
        conn.close()
        print(f"✅ Session completed: {session_id}")
    
    def get_training_data(self, dataset_name=None, min_confidence=0.7):
        """Get validated peaks for training"""
        conn = sqlite3.connect(self.db_path)
        
        if dataset_name:
            query = '''
                SELECT pv.*, vs.compound_name, vs.concentration, vs.filename
                FROM peak_validations pv
                JOIN validation_sessions vs ON pv.session_id = vs.session_id
                JOIN dataset_sessions ds ON vs.session_id = ds.session_id
                WHERE ds.dataset_name = ? AND pv.confidence >= ? AND vs.status = 'completed'
                ORDER BY pv.session_id, pv.peak_index
            '''
            df = pd.read_sql_query(query, conn, params=(dataset_name, min_confidence))
        else:
            query = '''
                SELECT pv.*, vs.compound_name, vs.concentration, vs.filename
                FROM peak_validations pv
                JOIN validation_sessions vs ON pv.session_id = vs.session_id
                WHERE pv.confidence >= ? AND vs.status = 'completed'
                ORDER BY pv.session_id, pv.peak_index
            '''
            df = pd.read_sql_query(query, conn, params=(min_confidence,))
        
        conn.close()
        return df

class EnhancedDetectorV6Improved:
    """Enhanced V6 with improved UI and data management"""
    
    def __init__(self, gui_mode=False):
        self.validator = EnhancedDetectorV5() if EnhancedDetectorV5 else None
        self.database = ValidationDatabase()
        self.current_session = None
        self.gui_mode = gui_mode
        
        # UI state
        self.current_peaks = []
        self.validation_states = []
        self.selected_indices = []
        
        # Results
        self.validated_peaks = []
        
        print("🚀 Enhanced Detector V6 (Improved) initialized")
        print("📊 Features: Batch validation, Database storage, Training data collection")
        if gui_mode:
            print("🖱️  GUI mode enabled - Interactive validation UI will be shown")
    
    def analyze_cv_file(self, csv_file, compound_name=None, concentration=None, scan_rate=None):
        """
        Main analysis function with improved peak detection
        """
        print(f"\n🔬 Analyzing: {csv_file}")
        
        # Create validation session
        self.current_session = self.database.create_session(
            csv_file, compound_name, concentration, scan_rate
        )
        
        # Load and process data
        try:
            df = pd.read_csv(csv_file)
            
            # Handle different CSV formats
            if 'Voltage' in df.columns and 'Current' in df.columns:
                voltage = df['Voltage'].values
                current = df['Current'].values
            elif len(df.columns) >= 2:
                voltage = df.iloc[:, 0].values
                current = df.iloc[:, 1].values
            else:
                raise ValueError("Invalid CSV format")
            
            print(f"📊 Data loaded: {len(voltage)} points")
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return None
        
        # Enhanced peak detection using V5 backend
        if self.validator:
            print("🎯 Running Enhanced V5 detection...")
            try:
                v5_results = self.validator.detect_peaks_enhanced_v5(voltage, current)
                
                if v5_results and 'peaks' in v5_results:
                    detected_peaks = v5_results['peaks']
                    print(f"📈 V5 detected {len(detected_peaks)} peaks")
                    
                    # Convert to our format
                    self.current_peaks = []
                    for i, peak in enumerate(detected_peaks):
                        self.current_peaks.append({
                            'index': i,
                            'voltage': peak.get('voltage', 0.0),
                            'current': peak.get('current', 0.0),
                            'type': peak.get('type', 'unknown'),
                            'confidence': peak.get('confidence', 0.5),
                            'snr': peak.get('snr', 1.0)
                        })
                else:
                    print("⚠️  V5 detection returned no peaks, using fallback")
                    self.current_peaks = self._fallback_peak_detection(voltage, current)
            except Exception as e:
                print(f"⚠️  V5 detection failed ({e}), using fallback")
                self.current_peaks = self._fallback_peak_detection(voltage, current)
        else:
            print("⚠️  Using fallback peak detection")
            self.current_peaks = self._fallback_peak_detection(voltage, current)
        
        # Initialize validation states
        self.validation_states = ['pending'] * len(self.current_peaks)
        self.selected_indices = []
        
        # Check if running in GUI mode
        if hasattr(self, 'gui_mode') and self.gui_mode:
            try:
                # Try to show interactive validation UI
                import matplotlib
                # Force check for GUI availability
                if 'DISPLAY' not in os.environ and matplotlib.get_backend() in ['TkAgg', 'Qt5Agg', 'Qt4Agg']:
                    raise Exception("No display available")
                self._show_batch_validation_ui(voltage, current)
            except Exception as e:
                print(f"⚠️  GUI mode failed ({e}), switching to command line validation")
                self._command_line_validation()
        else:
            # Non-GUI mode - just show summary
            print(f"📊 Peak detection completed:")
            print(f"   🎯 Detected peaks: {len(self.current_peaks)}")
            print(f"   💡 Use GUI mode for interactive validation")
            print(f"   ▶️  Run: python validation_data/v6_cli_demo.py")
        
        return {
            'session_id': self.current_session,
            'total_peaks': len(self.current_peaks),
            'validated_peaks': self.validated_peaks
        }
    
    def _fallback_peak_detection(self, voltage, current):
        """Fallback peak detection when V5 is not available"""
        try:
            from scipy.signal import find_peaks
            
            # Find positive peaks
            pos_peaks, _ = find_peaks(current, height=np.std(current)*0.5, distance=5)
            # Find negative peaks
            neg_peaks, _ = find_peaks(-current, height=np.std(current)*0.5, distance=5)
            
            peaks = []
            
            # Add positive peaks
            for i, idx in enumerate(pos_peaks):
                peaks.append({
                    'index': len(peaks),
                    'voltage': voltage[idx],
                    'current': current[idx],
                    'type': 'oxidation',
                    'confidence': 0.7,
                    'snr': abs(current[idx]) / np.std(current)
                })
            
            # Add negative peaks
            for i, idx in enumerate(neg_peaks):
                peaks.append({
                    'index': len(peaks),
                    'voltage': voltage[idx],
                    'current': current[idx],
                    'type': 'reduction',
                    'confidence': 0.7,
                    'snr': abs(current[idx]) / np.std(current)
                })
            
            # Sort by voltage
            peaks.sort(key=lambda x: x['voltage'])
            
            # Re-index
            for i, peak in enumerate(peaks):
                peak['index'] = i
            
            return peaks
            
        except ImportError:
            # Very basic fallback
            print("⚠️  Using basic peak detection")
            peaks = []
            for i in range(0, len(current), len(current)//5):
                if i < len(current):
                    peaks.append({
                        'index': len(peaks),
                        'voltage': voltage[i],
                        'current': current[i],
                        'type': 'unknown',
                        'confidence': 0.5,
                        'snr': 1.0
                    })
            return peaks[:10]  # Limit to 10 peaks
    
    def _show_batch_validation_ui(self, voltage, current):
        """Interactive batch validation UI"""
        
        # Check if GUI is available - force CLI mode in WSL/headless environments
        import matplotlib
        backend = matplotlib.get_backend()
        has_display = 'DISPLAY' in os.environ
        
        print(f"🖥️  GUI Check: Backend={backend}, Display={has_display}")
        
        # Force CLI mode for common headless scenarios or if explicitly requested
        if (not has_display or backend == 'Agg' or 'ssh' in os.environ.get('SSH_CONNECTION', '') or 
            hasattr(self, 'force_cli_mode') and self.force_cli_mode):
            raise Exception("CLI mode requested or headless environment detected")
        
        # Create figure with subplots
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        # Main CV plot
        ax_main = fig.add_subplot(gs[0:2, :])
        
        # Plot CV data
        ax_main.plot(voltage, current, 'b-', linewidth=2, alpha=0.8, label='CV Data')
        
        # Plot detected peaks
        peak_colors = {'oxidation': 'red', 'reduction': 'green', 'unknown': 'orange'}
        
        for peak in self.current_peaks:
            color = peak_colors.get(peak['type'], 'gray')
            marker = 'o' if peak['type'] == 'oxidation' else '^' if peak['type'] == 'reduction' else 's'
            
            ax_main.scatter(peak['voltage'], peak['current'], 
                          c=color, s=100, marker=marker, alpha=0.8,
                          edgecolors='black', linewidth=1)
            
            # Add peak index labels
            ax_main.annotate(f"{peak['index']}", 
                           (peak['voltage'], peak['current']),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=10, fontweight='bold')
        
        ax_main.set_xlabel('Voltage (V)', fontsize=12)
        ax_main.set_ylabel('Current (µA)', fontsize=12)
        ax_main.set_title('Peak Validation - Select peaks to validate/reject', fontsize=14, fontweight='bold')
        ax_main.grid(True, alpha=0.3)
        ax_main.legend()
        
        # Peak information table
        ax_table = fig.add_subplot(gs[2, :])
        ax_table.axis('off')
        
        # Create peak info table
        table_data = []
        headers = ['Index', 'Voltage (V)', 'Current (µA)', 'Type', 'Confidence', 'SNR', 'Status']
        
        for i, peak in enumerate(self.current_peaks):
            table_data.append([
                f"{peak['index']}",
                f"{peak['voltage']:.3f}",
                f"{peak['current']:.2f}",
                peak['type'],
                f"{peak['confidence']:.2f}",
                f"{peak['snr']:.2f}",
                self.validation_states[i]
            ])
        
        table = ax_table.table(cellText=table_data, colLabels=headers,
                              cellLoc='center', loc='center',
                              colWidths=[0.08, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # Color code the status column
        for i in range(len(table_data)):
            if self.validation_states[i] == 'valid':
                table[(i+1, 6)].set_facecolor('#90EE90')  # Light green
            elif self.validation_states[i] == 'invalid':
                table[(i+1, 6)].set_facecolor('#FFB6C1')  # Light red
            else:
                table[(i+1, 6)].set_facecolor('#FFFFFF')  # White
        
        # Interactive buttons
        self._add_validation_buttons(fig)
        
        plt.show()
    
    def _add_validation_buttons(self, fig):
        """Add interactive validation buttons"""
        
        # Button positions
        btn_width, btn_height = 0.12, 0.04
        btn_y = 0.02
        
        # Validate Selected button
        ax_validate = plt.axes([0.1, btn_y, btn_width, btn_height])
        btn_validate = Button(ax_validate, 'Validate Selected', color='lightgreen')
        btn_validate.on_clicked(self._validate_selected)
        
        # Reject Selected button
        ax_reject = plt.axes([0.25, btn_y, btn_width, btn_height])
        btn_reject = Button(ax_reject, 'Reject Selected', color='lightcoral')
        btn_reject.on_clicked(self._reject_selected)
        
        # Select All button
        ax_select_all = plt.axes([0.4, btn_y, btn_width, btn_height])
        btn_select_all = Button(ax_select_all, 'Select All', color='lightblue')
        btn_select_all.on_clicked(self._select_all)
        
        # Clear Selection button
        ax_clear = plt.axes([0.55, btn_y, btn_width, btn_height])
        btn_clear = Button(ax_clear, 'Clear Selection', color='lightyellow')
        btn_clear.on_clicked(self._clear_selection)
        
        # Complete Session button
        ax_complete = plt.axes([0.7, btn_y, btn_width, btn_height])
        btn_complete = Button(ax_complete, 'Complete Session', color='lightsteelblue')
        btn_complete.on_clicked(self._complete_session)
        
        # Export button
        ax_export = plt.axes([0.85, btn_y, btn_width, btn_height])
        btn_export = Button(ax_export, 'Export Results', color='wheat')
        btn_export.on_clicked(self._export_results)
        
        # Store button references
        self.buttons = {
            'validate': btn_validate,
            'reject': btn_reject,
            'select_all': btn_select_all,
            'clear': btn_clear,
            'complete': btn_complete,
            'export': btn_export
        }
        
        # Mouse click handler for peak selection
        fig.canvas.mpl_connect('button_press_event', self._on_peak_click)
    
    def _on_peak_click(self, event):
        """Handle peak selection clicks"""
        if event.inaxes and event.inaxes.get_title().startswith('Peak Validation'):
            # Find closest peak
            if event.xdata is not None and event.ydata is not None:
                distances = []
                for peak in self.current_peaks:
                    dist = np.sqrt((peak['voltage'] - event.xdata)**2 + 
                                 (peak['current'] - event.ydata)**2)
                    distances.append(dist)
                
                if distances:
                    closest_idx = np.argmin(distances)
                    if distances[closest_idx] < 0.1:  # Threshold for selection
                        if closest_idx in self.selected_indices:
                            self.selected_indices.remove(closest_idx)
                            print(f"🔸 Deselected peak {closest_idx}")
                        else:
                            self.selected_indices.append(closest_idx)
                            print(f"🔹 Selected peak {closest_idx}")
                        
                        # Update plot
                        self._update_peak_visualization()
    
    def _update_peak_visualization(self):
        """Update peak visualization to show selection"""
        # This would update the scatter plot colors to show selection
        # Implementation would depend on matplotlib backend
        pass
    
    def _validate_selected(self, event):
        """Validate selected peaks"""
        if not self.selected_indices:
            print("⚠️  No peaks selected")
            return
        
        for idx in self.selected_indices:
            self.validation_states[idx] = 'valid'
            peak = self.current_peaks[idx]
            
            # Save to database
            self.database.save_peak_validation(
                self.current_session, idx, 
                peak['voltage'], peak['current'], peak['type'],
                True, peak['confidence'], "Human validated"
            )
        
        print(f"✅ Validated {len(self.selected_indices)} peaks")
        self.selected_indices.clear()
    
    def _reject_selected(self, event):
        """Reject selected peaks"""
        if not self.selected_indices:
            print("⚠️  No peaks selected")
            return
        
        for idx in self.selected_indices:
            self.validation_states[idx] = 'invalid'
            peak = self.current_peaks[idx]
            
            # Save to database
            self.database.save_peak_validation(
                self.current_session, idx,
                peak['voltage'], peak['current'], peak['type'],
                False, peak['confidence'], "Human rejected"
            )
        
        print(f"❌ Rejected {len(self.selected_indices)} peaks")
        self.selected_indices.clear()
    
    def _select_all(self, event):
        """Select all peaks"""
        self.selected_indices = list(range(len(self.current_peaks)))
        print(f"🔹 Selected all {len(self.current_peaks)} peaks")
    
    def _clear_selection(self, event):
        """Clear peak selection"""
        self.selected_indices.clear()
        print("🔸 Cleared selection")
    
    def _complete_session(self, event):
        """Complete validation session"""
        if self.current_session:
            # Collect validated peaks
            self.validated_peaks = []
            for i, peak in enumerate(self.current_peaks):
                if self.validation_states[i] == 'valid':
                    self.validated_peaks.append(peak)
            
            notes = f"Validated {len(self.validated_peaks)} out of {len(self.current_peaks)} peaks"
            self.database.complete_session(self.current_session, notes)
            
            print(f"✅ Session completed: {len(self.validated_peaks)} validated peaks")
            plt.close('all')
    
    def _export_results(self, event):
        """Export validation results"""
        if not self.current_session:
            print("⚠️  No active session")
            return
        
        # Export to JSON
        export_data = {
            'session_id': self.current_session,
            'timestamp': datetime.now().isoformat(),
            'total_peaks': len(self.current_peaks),
            'validated_peaks': []
        }
        
        for i, peak in enumerate(self.current_peaks):
            if self.validation_states[i] == 'valid':
                export_data['validated_peaks'].append({
                    'index': peak['index'],
                    'voltage': peak['voltage'],
                    'current': peak['current'],
                    'type': peak['type'],
                    'confidence': peak['confidence']
                })
        
        filename = f"validation_export_{self.current_session}.json"
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"📁 Results exported to: {filename}")
    
    def _command_line_validation(self):
        """Command line validation interface when GUI is not available"""
        print("\n🖥️  COMMAND LINE VALIDATION MODE")
        print("-" * 40)
        
        if not self.current_peaks:
            print("❌ No peaks detected to validate")
            return
        
        print(f"📊 Found {len(self.current_peaks)} peaks to validate:")
        print()
        
        # Show peak details
        for i, peak in enumerate(self.current_peaks):
            print(f"Peak {i+1}:")
            print(f"   📍 Voltage: {peak['voltage']:.3f} V")
            print(f"   ⚡ Current: {peak['current']:.2f} µA")
            print(f"   🏷️  Type: {peak['type']}")
            print(f"   📊 Confidence: {peak['confidence']:.2f}")
            print(f"   📈 SNR: {peak['snr']:.2f}")
            print()
        
        print("🎯 Validation Options:")
        print("   v <numbers> - Validate peaks (e.g., 'v 1 2 3')")
        print("   r <numbers> - Reject peaks (e.g., 'r 4 5')")
        print("   va - Validate all peaks")
        print("   ra - Reject all peaks")
        print("   s - Show peak summary")
        print("   c - Complete session")
        print("   q - Quit without saving")
        print()
        
        while True:
            try:
                cmd = input("👉 Enter command: ").strip().lower()
                
                if cmd == 'q':
                    print("⚠️  Session cancelled")
                    break
                elif cmd == 'c':
                    self._complete_session_cli()
                    break
                elif cmd == 's':
                    self._show_validation_summary()
                elif cmd == 'va':
                    self._validate_all_peaks()
                elif cmd == 'ra':
                    self._reject_all_peaks()
                elif cmd.startswith('v '):
                    peak_nums = [int(x) for x in cmd[2:].split()]
                    self._validate_peaks_by_numbers(peak_nums)
                elif cmd.startswith('r '):
                    peak_nums = [int(x) for x in cmd[2:].split()]
                    self._reject_peaks_by_numbers(peak_nums)
                else:
                    print("❌ Invalid command. Type 'c' to complete or 'q' to quit.")
                    
            except (ValueError, IndexError):
                print("❌ Invalid input. Please check peak numbers.")
            except KeyboardInterrupt:
                print("\n⚠️  Session interrupted")
                break
    
    def _validate_peaks_by_numbers(self, peak_numbers):
        """Validate peaks by their numbers"""
        validated_count = 0
        for num in peak_numbers:
            if 1 <= num <= len(self.current_peaks):
                idx = num - 1
                peak = self.current_peaks[idx]
                self.database.save_peak_validation(
                    self.current_session, idx,
                    peak['voltage'], peak['current'], peak['type'],
                    True, peak['confidence'], "CLI validation"
                )
                self.validation_states[idx] = 'valid'
                validated_count += 1
                print(f"✅ Peak {num} validated")
            else:
                print(f"❌ Peak {num} not found")
        
        if validated_count > 0:
            print(f"✅ Validated {validated_count} peaks")
    
    def _reject_peaks_by_numbers(self, peak_numbers):
        """Reject peaks by their numbers"""
        rejected_count = 0
        for num in peak_numbers:
            if 1 <= num <= len(self.current_peaks):
                idx = num - 1
                peak = self.current_peaks[idx]
                self.database.save_peak_validation(
                    self.current_session, idx,
                    peak['voltage'], peak['current'], peak['type'],
                    False, peak['confidence'], "CLI rejection"
                )
                self.validation_states[idx] = 'invalid'
                rejected_count += 1
                print(f"❌ Peak {num} rejected")
            else:
                print(f"❌ Peak {num} not found")
        
        if rejected_count > 0:
            print(f"❌ Rejected {rejected_count} peaks")
    
    def _validate_all_peaks(self):
        """Validate all peaks"""
        for i, peak in enumerate(self.current_peaks):
            self.database.save_peak_validation(
                self.current_session, i,
                peak['voltage'], peak['current'], peak['type'],
                True, peak['confidence'], "CLI validate all"
            )
            self.validation_states[i] = 'valid'
        print(f"✅ All {len(self.current_peaks)} peaks validated")
    
    def _reject_all_peaks(self):
        """Reject all peaks"""
        for i, peak in enumerate(self.current_peaks):
            self.database.save_peak_validation(
                self.current_session, i,
                peak['voltage'], peak['current'], peak['type'],
                False, peak['confidence'], "CLI reject all"
            )
            self.validation_states[i] = 'invalid'
        print(f"❌ All {len(self.current_peaks)} peaks rejected")
    
    def _show_validation_summary(self):
        """Show current validation status"""
        valid_count = sum(1 for state in self.validation_states if state == 'valid')
        invalid_count = sum(1 for state in self.validation_states if state == 'invalid')
        pending_count = sum(1 for state in self.validation_states if state == 'pending')
        
        print(f"\n📊 VALIDATION SUMMARY:")
        print(f"   ✅ Validated: {valid_count}")
        print(f"   ❌ Rejected: {invalid_count}")
        print(f"   ⏳ Pending: {pending_count}")
        print()
    
    def _complete_session_cli(self):
        """Complete session in CLI mode"""
        # Collect validated peaks
        self.validated_peaks = []
        for i, peak in enumerate(self.current_peaks):
            if self.validation_states[i] == 'valid':
                self.validated_peaks.append(peak)
        
        if self.current_session:
            notes = f"CLI validation: {len(self.validated_peaks)} validated out of {len(self.current_peaks)} peaks"
            self.database.complete_session(self.current_session, notes)
            
            print(f"\n✅ Session completed!")
            print(f"📊 Validated {len(self.validated_peaks)} out of {len(self.current_peaks)} peaks")
    
    def get_training_dataset(self, dataset_name="default", min_confidence=0.8):
        """Get training dataset for AI training"""
        return self.database.get_training_data(dataset_name, min_confidence)

def main():
    """Test the improved V6 system"""
    detector = EnhancedDetectorV6Improved()
    
    # Test files
    test_files = [
        "sample_data/cv_sample.csv",
        "validation_data/ferrocyanide_test.csv" if os.path.exists("validation_data/ferrocyanide_test.csv") else None
    ]
    
    for test_file in test_files:
        if test_file and os.path.exists(test_file):
            print(f"\n🧪 Testing with: {test_file}")
            result = detector.analyze_cv_file(
                test_file, 
                compound_name="Test Compound",
                concentration="1.0 mM",
                scan_rate="100 mV/s"
            )
            
            if result:
                print(f"📊 Session: {result['session_id']}")
                print(f"📈 Validated: {len(result['validated_peaks'])} peaks")
                
                # Show training data availability
                training_data = detector.get_training_dataset()
                print(f"🎓 Training data available: {len(training_data)} validated points")
                break
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    print("\n🎉 Enhanced V6 Improved system ready!")
    return detector

if __name__ == "__main__":
    main()