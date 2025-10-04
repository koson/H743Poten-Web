#!/usr/bin/env python3
"""
🎯 CV Peak Validation Web UI
===========================

Interactive web interface for CV peak validation using real data
from Test_Data_CV folder. Features:
- File browser for CV data selection
- Interactive peak detection with Enhanced V5/V6
- Peak validation/rejection interface
- Training data collection for DeepCV

Author: H743Poten Research Team
Date: October 4, 2025
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import os
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
import logging
import sys
from pathlib import Path

# Add path for imports
sys.path.append('.')
sys.path.append('validation_data')

try:
    # Try direct imports first (when running from validation_data directory)
    from enhanced_detector_v6_improved import EnhancedDetectorV6Improved, ValidationDatabase
    from enhanced_detector_v5 import EnhancedDetectorV5
except ImportError as e:
    print(f"⚠️  Import warning: {e}")
    # Try relative imports (when running from parent directory)
    try:
        from validation_data.enhanced_detector_v6_improved import EnhancedDetectorV6Improved, ValidationDatabase
        from validation_data.enhanced_detector_v5 import EnhancedDetectorV5
    except ImportError as e2:
        print(f"❌ Fatal: Could not import detectors: {e2}")
        EnhancedDetectorV6Improved = None
        ValidationDatabase = None
        EnhancedDetectorV5 = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CVPeakValidationApp:
    """Main CV Peak Validation Web Application"""
    
    def __init__(self):
        # Set template and static folders
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static')
        
        self.app = Flask(__name__, 
                        template_folder=template_dir,
                        static_folder=static_dir)
        self.app.secret_key = 'cv_peak_validation_secret_key_2025'
        
        # Initialize components
        self.detector_v6 = EnhancedDetectorV6Improved() if EnhancedDetectorV6Improved else None
        self.detector_v5 = EnhancedDetectorV5() if EnhancedDetectorV5 else None
        self.database = ValidationDatabase() if ValidationDatabase else None
        
        # Configuration
        self.test_data_path = "Test_Data_CV"
        self.current_session = None
        self.current_peaks = []
        self.current_cv_data = None
        
        # Setup routes
        self.setup_routes()
        
        print("🎯 CV Peak Validation Web UI initialized")
        print(f"📁 Test data path: {self.test_data_path}")
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template('cv_validation.html')
        
        @self.app.route('/api/files')
        def get_files():
            """Get list of available CV files"""
            try:
                files = []
                if os.path.exists(self.test_data_path):
                    for root, dirs, filenames in os.walk(self.test_data_path):
                        for filename in filenames:
                            if filename.endswith('.csv'):
                                full_path = os.path.join(root, filename)
                                rel_path = os.path.relpath(full_path, self.test_data_path)
                                
                                # Extract metadata from filename
                                metadata = self._extract_metadata(filename)
                                
                                files.append({
                                    'filename': filename,
                                    'path': rel_path,
                                    'full_path': full_path,
                                    'metadata': metadata
                                })
                
                # Sort by compound and concentration
                files.sort(key=lambda x: (x['metadata'].get('compound', ''), 
                                        x['metadata'].get('concentration', 0)))
                
                return jsonify({'files': files})
                
            except Exception as e:
                logger.error(f"Error getting files: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analyze', methods=['POST'])
        def analyze_file():
            """Analyze selected CV file"""
            try:
                data = request.get_json()
                file_path = data.get('file_path')
                
                if not file_path or not os.path.exists(file_path):
                    return jsonify({'error': 'File not found'}), 404
                
                # Load CV data
                cv_data = self._load_cv_data(file_path)
                if cv_data is None:
                    return jsonify({'error': 'Failed to load CV data'}), 500
                
                # Detect peaks
                peaks_result = self._detect_peaks(cv_data['voltage'], cv_data['current'])
                
                # Generate plot
                plot_url = self._generate_plot(cv_data, peaks_result['peaks'])
                if not plot_url:
                    plot_url = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='  # 1x1 transparent pixel
                    logger.warning('Plot generation failed, using placeholder')
                
                # Create validation session
                session_id = self._create_validation_session(file_path, cv_data)
                
                result = {
                    'session_id': session_id,
                    'cv_data': {
                        'voltage': cv_data['voltage'].tolist(),
                        'current': cv_data['current'].tolist(),
                        'data_points': len(cv_data['voltage'])
                    },
                    'peaks': peaks_result['peaks'],
                    'baseline': peaks_result.get('baseline', {}),
                    'plot_url': plot_url,
                    'metadata': cv_data['metadata']
                }
                
                # Store current data
                self.current_session = session_id
                self.current_peaks = peaks_result['peaks']
                self.current_cv_data = cv_data
                
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"Error analyzing file: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/validate_peaks', methods=['POST'])
        def validate_peaks():
            """Validate/reject selected peaks"""
            try:
                data = request.get_json()
                session_id = data.get('session_id')
                peak_validations = data.get('peak_validations', [])
                
                if not session_id or session_id != self.current_session:
                    return jsonify({'error': 'Invalid session'}), 400
                
                # Save validations to database
                validated_count = 0
                rejected_count = 0
                
                for validation in peak_validations:
                    peak_id = validation.get('peak_id')
                    is_valid = validation.get('is_valid')
                    reasoning = validation.get('reasoning', '')
                    
                    if peak_id < len(self.current_peaks):
                        peak = self.current_peaks[peak_id]
                        
                        if self.database:
                            self.database.save_peak_validation(
                                session_id, peak_id,
                                peak['voltage'], peak['current'], peak['type'],
                                is_valid, peak.get('confidence', 0.5),
                                reasoning
                            )
                        
                        if is_valid:
                            validated_count += 1
                        else:
                            rejected_count += 1
                
                # Complete session
                if self.database:
                    notes = f"Web UI validation: {validated_count} validated, {rejected_count} rejected"
                    self.database.complete_session(session_id, notes)
                
                return jsonify({
                    'success': True,
                    'validated_count': validated_count,
                    'rejected_count': rejected_count,
                    'total_peaks': len(peak_validations)
                })
                
            except Exception as e:
                logger.error(f"Error validating peaks: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/upload_csv', methods=['POST'])
        def upload_csv():
            """Handle CSV file upload"""
            try:
                if 'file' not in request.files:
                    return jsonify({'error': 'No file provided'}), 400
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': 'No file selected'}), 400
                
                if not file.filename.lower().endswith('.csv'):
                    return jsonify({'error': 'File must be a CSV file'}), 400
                
                # Save file to uploads directory
                uploads_dir = os.path.join(str(self.data_dir), 'uploads')
                os.makedirs(uploads_dir, exist_ok=True)
                
                # Create safe filename
                filename = file.filename
                safe_filename = f"uploaded_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file_path = os.path.join(uploads_dir, safe_filename)
                
                file.save(file_path)
                
                # Validate CSV format
                try:
                    df = pd.read_csv(file_path)
                    if len(df) < 10:
                        return jsonify({'error': 'CSV file too short (needs at least 10 rows)'}), 400
                    
                    # Check for required columns (flexible)
                    required_cols = ['potential', 'current']
                    has_required = any(
                        any(req in col.lower() for req in required_cols)
                        for col in df.columns
                    )
                    
                    if not has_required:
                        return jsonify({'error': 'CSV must contain potential and current columns'}), 400
                        
                except Exception as e:
                    return jsonify({'error': f'Invalid CSV format: {str(e)}'}), 400
                
                # Add to available files
                relative_path = os.path.relpath(file_path, str(self.data_dir))
                
                return jsonify({
                    'success': True,
                    'filename': relative_path,
                    'message': f'File {filename} uploaded successfully'
                })
                
            except Exception as e:
                logger.error(f"Error uploading file: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/export_data')
        def export_training_data():
            """Export validated data for training"""
            try:
                if not self.database:
                    return jsonify({'error': 'Database not available'}), 500
                
                # Get all validated peaks
                training_data = self.database.get_training_data(min_confidence=0.5)
                
                if training_data.empty:
                    return jsonify({'error': 'No training data available'}), 404
                
                # Convert to JSON
                export_data = {
                    'timestamp': datetime.now().isoformat(),
                    'total_peaks': len(training_data),
                    'sessions': training_data['session_id'].nunique(),
                    'compounds': training_data['compound_name'].nunique(),
                    'peaks': training_data.to_dict('records')
                }
                
                # Create file
                filename = f"cv_training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                return jsonify({
                    'data': export_data,
                    'filename': filename
                })
                
            except Exception as e:
                logger.error(f"Error exporting data: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _extract_metadata(self, filename):
        """Extract metadata from CV filename"""
        metadata = {
            'compound': 'Unknown',
            'concentration': 0,
            'scan_rate': 0,
            'electrode': 1,
            'scan_number': 1
        }
        
        try:
            # Parse Palmsens format: Palmsens_10mM_CV_100mVpS_E1_scan_05.csv
            if 'Palmsens' in filename:
                parts = filename.replace('.csv', '').split('_')
                for i, part in enumerate(parts):
                    if 'mM' in part:
                        metadata['concentration'] = float(part.replace('mM', ''))
                        metadata['compound'] = 'Ferrocyanide'  # Assume ferrocyanide
                    elif 'mVpS' in part:
                        metadata['scan_rate'] = int(part.replace('mVpS', ''))
                    elif part.startswith('E') and len(part) > 1:
                        metadata['electrode'] = int(part[1:])
                    elif part.startswith('scan'):
                        metadata['scan_number'] = int(parts[i+1]) if i+1 < len(parts) else 1
            
            # Parse Pipot format: Pipot_Ferro_0_5mM_100mVpS_E1_scan_02.csv
            elif 'Pipot' in filename:
                parts = filename.replace('.csv', '').split('_')
                for i, part in enumerate(parts):
                    if 'Ferro' in part:
                        metadata['compound'] = 'Ferrocyanide'
                    elif 'mM' in part:
                        # Handle formats like "0_5mM" or "10mM"
                        conc_str = part.replace('mM', '')
                        if '_' in conc_str:
                            conc_str = conc_str.replace('_', '.')
                        metadata['concentration'] = float(conc_str)
                    elif 'mVpS' in part:
                        metadata['scan_rate'] = int(part.replace('mVpS', ''))
                    elif part.startswith('E') and len(part) > 1:
                        metadata['electrode'] = int(part[1:])
                    elif part == 'scan' and i+1 < len(parts):
                        metadata['scan_number'] = int(parts[i+1])
        
        except Exception as e:
            logger.warning(f"Error parsing filename {filename}: {e}")
        
        return metadata
    
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
            
            # Extract metadata from filename
            filename = os.path.basename(file_path)
            metadata = self._extract_metadata(filename)
            
            return {
                'voltage': voltage,
                'current': current,
                'metadata': metadata,
                'filename': filename,
                'file_path': file_path
            }
            
        except Exception as e:
            logger.error(f"Error loading CV data: {e}")
            return None
    
    def _detect_peaks(self, voltage, current):
        """Detect peaks using available detectors"""
        try:
            peaks = []
            baseline = {}
            
            if self.detector_v5:
                # Use Enhanced V5 for peak detection
                result = self.detector_v5.detect_peaks_enhanced_v5(voltage, current)
                
                if result and 'peaks' in result:
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
                
                if result and 'baseline' in result:
                    baseline = result['baseline']
            
            else:
                # Fallback peak detection
                peaks = self._fallback_peak_detection(voltage, current)
            
            return {
                'peaks': peaks,
                'baseline': baseline,
                'method': 'Enhanced_V5' if self.detector_v5 else 'Fallback'
            }
            
        except Exception as e:
            logger.error(f"Error detecting peaks: {e}")
            return {'peaks': [], 'baseline': {}, 'method': 'Error'}
    
    def _fallback_peak_detection(self, voltage, current):
        """Fallback peak detection when Enhanced detectors not available"""
        try:
            from scipy.signal import find_peaks
            
            # Simple peak detection
            current_std = np.std(current)
            height_threshold = current_std * 1.5
            
            # Find positive peaks
            pos_peaks, _ = find_peaks(current, height=height_threshold, distance=5)
            # Find negative peaks
            neg_peaks, _ = find_peaks(-current, height=height_threshold, distance=5)
            
            peaks = []
            
            # Add positive peaks
            for i, idx in enumerate(pos_peaks):
                peaks.append({
                    'id': len(peaks),
                    'voltage': voltage[idx],
                    'current': current[idx],
                    'type': 'oxidation',
                    'confidence': 0.7,
                    'snr': abs(current[idx]) / current_std,
                    'method': 'Fallback'
                })
            
            # Add negative peaks
            for i, idx in enumerate(neg_peaks):
                peaks.append({
                    'id': len(peaks),
                    'voltage': voltage[idx],
                    'current': current[idx],
                    'type': 'reduction',
                    'confidence': 0.7,
                    'snr': abs(current[idx]) / current_std,
                    'method': 'Fallback'
                })
            
            return peaks
            
        except ImportError:
            # Very basic detection
            return [{
                'id': 0,
                'voltage': voltage[len(voltage)//3],
                'current': current[len(voltage)//3],
                'type': 'oxidation',
                'confidence': 0.5,
                'snr': 1.0,
                'method': 'Basic'
            }]
    
    def _generate_plot(self, cv_data, peaks):
        """Generate CV plot with detected peaks"""
        try:
            plt.figure(figsize=(12, 8))
            
            # Plot CV data
            plt.plot(cv_data['voltage'], cv_data['current'], 'b-', linewidth=2, label='CV Data')
            
            # Plot baseline if available
            if peaks and len(peaks) > 0 and hasattr(self, '_last_baseline'):
                baseline_data = self._last_baseline
                if 'voltage' in baseline_data and 'current' in baseline_data:
                    plt.plot(baseline_data['voltage'], baseline_data['current'], 
                           'c--', linewidth=1, alpha=0.7, label='Forward Baseline')
                    plt.plot(baseline_data['voltage'], baseline_data['current'], 
                           'g--', linewidth=1, alpha=0.7, label='Reverse Baseline')
            
            # Plot peaks
            peak_colors = {'oxidation': 'red', 'reduction': 'green', 'unknown': 'orange'}
            peak_markers = {'oxidation': 'o', 'reduction': '^', 'unknown': 's'}
            
            for peak in peaks:
                color = peak_colors.get(peak['type'], 'gray')
                marker = peak_markers.get(peak['type'], 'o')
                
                plt.scatter(peak['voltage'], peak['current'], 
                          c=color, s=100, marker=marker, 
                          edgecolors='black', linewidth=1,
                          label=f"{peak['type'].title()} Peak" if peak['id'] == 0 or 
                               not any(p['type'] == peak['type'] and p['id'] < peak['id'] for p in peaks) else "")
                
                # Add peak labels
                plt.annotate(f"{peak['id']}", 
                           (peak['voltage'], peak['current']),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=10, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.7))
            
            plt.xlabel('Voltage (V)', fontsize=12)
            plt.ylabel('Current (µA)', fontsize=12)
            plt.title(f"CV Analysis: {cv_data['metadata']['compound']} "
                     f"({cv_data['metadata']['concentration']}mM)", fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Save plot to base64 string
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"Error generating plot: {e}")
            # Return a simple placeholder plot
            try:
                plt.figure(figsize=(8, 6))
                plt.text(0.5, 0.5, 'Plot Generation Failed\nCheck console for errors', 
                        ha='center', va='center', fontsize=14, color='red')
                plt.xlim(0, 1)
                plt.ylim(0, 1)
                plt.axis('off')
                
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
                buffer.seek(0)
                plot_data = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                
                return f"data:image/png;base64,{plot_data}"
            except:
                return None
    
    def _create_validation_session(self, file_path, cv_data):
        """Create validation session in database"""
        try:
            if self.database:
                session_id = self.database.create_session(
                    file_path,
                    cv_data['metadata']['compound'],
                    f"{cv_data['metadata']['concentration']}mM",
                    f"{cv_data['metadata']['scan_rate']}mV/s"
                )
                return session_id
            else:
                # Generate simple session ID
                return f"web_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def run(self, host='127.0.0.1', port=5003, debug=True):
        """Run the Flask application"""
        print(f"🚀 Starting CV Peak Validation Web UI")
        print(f"📱 Access at: http://{host}:{port}")
        print(f"📁 Test data: {os.path.abspath(self.test_data_path)}")
        self.app.run(host=host, port=port, debug=debug)

def main():
    """Main function"""
    app = CVPeakValidationApp()
    app.run()

if __name__ == "__main__":
    main()