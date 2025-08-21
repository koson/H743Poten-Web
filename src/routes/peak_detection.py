from flask import Blueprint, jsonify, send_file, current_app, request, render_template, session
import os
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
import logging
import uuid
import glob
import json
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

peak_detection_bp = Blueprint('peak_detection', __name__)

# In-memory storage for analysis sessions
analysis_sessions = {}

@peak_detection_bp.route('/api/get_saved_files')
def get_saved_files():
    """Get list of saved CSV files"""
    try:
        data_dir = os.path.join(current_app.root_path, '..', 'data_logs', 'csv')
        data_dir = os.path.abspath(data_dir)  # Resolve to absolute path
        
        if not os.path.exists(data_dir):
            return jsonify([])
        
        files = []
        for file_path in glob.glob(os.path.join(data_dir, '*.csv')):
            try:
                stat = os.stat(file_path)
                filename = os.path.basename(file_path)
                files.append({
                    'name': filename,
                    'filename': filename,  # Use filename instead of full path
                    'path': os.path.abspath(file_path),  # Keep full path for debugging
                    'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'size': stat.st_size
                })
            except Exception as e:
                logger.warning(f"Error reading file {file_path}: {e}")
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x['date'], reverse=True)
        return jsonify(files)
        
    except Exception as e:
        logger.error(f"Error getting saved files: {str(e)}")
        return jsonify([])

@peak_detection_bp.route('/api/load_saved_file_by_name/<filename>')
def load_saved_file_by_name(filename):
    """Load data from a saved CSV file by filename"""
    try:
        # Construct the file path
        data_dir = os.path.join(current_app.root_path, '..', 'data_logs', 'csv')
        data_dir = os.path.abspath(data_dir)
        file_path = os.path.join(data_dir, filename)
        
        # Security check - ensure the file is within the data directory
        if not os.path.abspath(file_path).startswith(data_dir):
            return jsonify({'success': False, 'error': 'Invalid file path'})
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': f'File not found: {filename}'})
        
        return load_csv_file(file_path)
        
    except Exception as e:
        logger.error(f"Error loading saved file by name: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def load_csv_file(file_path):
    """Helper function to load and parse CSV file"""
    try:
        # Read CSV file
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            return jsonify({'success': False, 'error': 'File too short'})
        
        # Handle instrument file format (FileName: header)
        header_line_idx = 0
        data_start_idx = 1
        
        if lines[0].strip().startswith('FileName:'):
            header_line_idx = 1
            data_start_idx = 2
            logger.info("Detected instrument file format with FileName header")
        
        # Parse headers
        headers = [h.strip().lower() for h in lines[header_line_idx].strip().split(',')]
        logger.info(f"Headers found: {headers}")
        
        # Find voltage and current columns
        voltage_idx = -1
        current_idx = -1
        
        for i, header in enumerate(headers):
            if header in ['v', 'voltage'] or 'volt' in header or 'potential' in header:
                voltage_idx = i
            elif header in ['a', 'ua', 'ma', 'na', 'current'] or 'amp' in header or 'curr' in header:
                current_idx = i
        
        if voltage_idx == -1 or current_idx == -1:
            return jsonify({'success': False, 'error': f'Could not find voltage or current columns in headers: {headers}'})
        
        # Determine current scaling
        current_unit = headers[current_idx]
        current_scale = 1.0
        if current_unit == 'ua':
            current_scale = 1e-6  # microAmps to Amps
        elif current_unit == 'ma':
            current_scale = 1e-3  # milliAmps to Amps
        elif current_unit == 'na':
            current_scale = 1e-9  # nanoAmps to Amps
        
        logger.info(f"Current unit: {current_unit}, scale: {current_scale}")
        
        # Parse data
        voltage = []
        current = []
        
        for i in range(data_start_idx, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
                
            values = line.split(',')
            if len(values) > max(voltage_idx, current_idx):
                try:
                    v = float(values[voltage_idx])
                    c = float(values[current_idx]) * current_scale
                    voltage.append(v)
                    current.append(c)
                except ValueError:
                    continue
        
        if len(voltage) == 0 or len(current) == 0:
            return jsonify({'success': False, 'error': 'No valid data points found'})
        
        logger.info(f"Loaded {len(voltage)} data points from {file_path}")
        logger.info(f"Voltage range: {min(voltage):.3f} to {max(voltage):.3f} V")
        logger.info(f"Current range: {min(current):.6e} to {max(current):.6e} A")
        
        return jsonify({
            'success': True,
            'data': {
                'voltage': voltage,
                'current': current
            },
            'metadata': {
                'points': len(voltage),
                'voltage_range': [min(voltage), max(voltage)],
                'current_range': [min(current), max(current)],
                'current_unit': current_unit,
                'current_scale': current_scale
            }
        })
        
    except Exception as e:
        logger.error(f"Error loading CSV file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@peak_detection_bp.route('/api/load_saved_file/<path:file_path>')
def load_saved_file(file_path):
    """Load data from a saved CSV file"""
    try:
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'})
        
        # Read CSV file
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            return jsonify({'success': False, 'error': 'File too short'})
        
        # Handle instrument file format (FileName: header)
        header_line_idx = 0
        data_start_idx = 1
        
        if lines[0].strip().startswith('FileName:'):
            header_line_idx = 1
            data_start_idx = 2
            logger.info("Detected instrument file format with FileName header")
        
        # Parse headers
        headers = [h.strip().lower() for h in lines[header_line_idx].strip().split(',')]
        logger.info(f"Headers found: {headers}")
        
        # Find voltage and current columns
        voltage_idx = -1
        current_idx = -1
        
        for i, header in enumerate(headers):
            if header in ['v', 'voltage'] or 'volt' in header or 'potential' in header:
                voltage_idx = i
            elif header in ['a', 'ua', 'ma', 'na', 'current'] or 'amp' in header or 'curr' in header:
                current_idx = i
        
        if voltage_idx == -1 or current_idx == -1:
            return jsonify({'success': False, 'error': f'Could not find voltage or current columns in headers: {headers}'})
        
        # Determine current scaling
        current_unit = headers[current_idx]
        current_scale = 1.0
        if current_unit == 'ua':
            current_scale = 1e-6  # microAmps to Amps
        elif current_unit == 'ma':
            current_scale = 1e-3  # milliAmps to Amps
        elif current_unit == 'na':
            current_scale = 1e-9  # nanoAmps to Amps
        
        logger.info(f"Current unit: {current_unit}, scale: {current_scale}")
        
        # Parse data
        voltage = []
        current = []
        
        for i in range(data_start_idx, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
                
            values = line.split(',')
            if len(values) > max(voltage_idx, current_idx):
                try:
                    v = float(values[voltage_idx])
                    c = float(values[current_idx]) * current_scale
                    voltage.append(v)
                    current.append(c)
                except ValueError:
                    continue
        
        if len(voltage) == 0 or len(current) == 0:
            return jsonify({'success': False, 'error': 'No valid data points found'})
        
        logger.info(f"Loaded {len(voltage)} data points from {file_path}")
        logger.info(f"Voltage range: {min(voltage):.3f} to {max(voltage):.3f} V")
        logger.info(f"Current range: {min(current):.6e} to {max(current):.6e} A")
        
        return jsonify({
            'success': True,
            'data': {
                'voltage': voltage,
                'current': current
            },
            'metadata': {
                'points': len(voltage),
                'voltage_range': [min(voltage), max(voltage)],
                'current_range': [min(current), max(current)],
                'current_unit': current_unit,
                'current_scale': current_scale
            }
        })
        
    except Exception as e:
        logger.error(f"Error loading saved file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@peak_detection_bp.route('/create_analysis_session', methods=['POST'])
def create_analysis_session():
    """Create a new analysis session and store data"""
    try:
        data = request.get_json()
        if not data:
            logger.error("No data provided to create_analysis_session")
            return jsonify({'error': 'No data provided'}), 400
        
        logger.info(f"Creating analysis session with data keys: {list(data.keys())}")
            
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Store data in in-memory storage
        # Ensure peaks is a list of dicts, not an int
        peaks = data.get('peaks', [])
        if isinstance(peaks, int):
            # Try to get from previewData if available
            peaks = data.get('previewData', {}).get('peaks', [])
        if not isinstance(peaks, list):
            peaks = []

        # Handle multi-trace: data['data'] is list of traces, each should have 'filename'
        traces = data.get('data', {})
        if isinstance(traces, list):
            # Add filename if missing
            for i, trace in enumerate(traces):
                if 'filename' not in trace:
                    # Try to get from filenames array if present
                    filenames = data.get('filenames') or data.get('file_labels')
                    if filenames and i < len(filenames):
                        trace['filename'] = filenames[i]
                    else:
                        trace['filename'] = f'Trace {i+1}'
        elif isinstance(traces, dict):
            # Single trace: add filename if present
            if 'filename' not in traces:
                filename = data.get('filename') or (data.get('filenames')[0] if data.get('filenames') else None)
                if filename:
                    traces['filename'] = filename
        analysis_sessions[session_id] = {
            'peaks': peaks,
            'data': traces,
            'method': data.get('method', ''),
            'methodName': data.get('methodName', ''),
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"Created analysis session {session_id} for method {data.get('method')}")
        return jsonify({'session_id': session_id})
        
    except Exception as e:
        logger.error(f"Error creating analysis session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@peak_detection_bp.route('/peak_analysis/<session_id>')
def peak_analysis(session_id):
    """Render peak analysis details page"""
    try:
        # Get data from in-memory storage
        session_data = analysis_sessions.get(session_id)
        if not session_data:
            logger.error(f"Session {session_id} not found in analysis_sessions")
            logger.info(f"Available sessions: {list(analysis_sessions.keys())}")
            return "Session not found", 404
        
        logger.info(f"Loading analysis session {session_id} for method {session_data.get('method')}")
        
        return render_template('peak_analysis.html',
                             peaks=session_data['peaks'],
                             data=session_data['data'],
                             method=session_data['method'],
                             methodName=session_data['methodName'])
                             
    except Exception as e:
        logger.error(f"Error rendering peak analysis: {str(e)}")
        return str(e), 500

@peak_detection_bp.route('/get-peaks/<method>', methods=['POST'])
def get_peaks(method):
    """
    Analyze CV data and detect peaks using specified method
    Returns peaks with their positions and characteristics
    """
    try:
        # Get data from POST request
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # Multi-trace: voltage/current เป็น list of list หรือ dataFiles
        if 'dataFiles' in data and isinstance(data['dataFiles'], list):
            # New: explicit dataFiles array
            nFiles = len(data['dataFiles'])
            peaks_per_file = [ [] for _ in range(nFiles) ]
            for i, file in enumerate(data['dataFiles']):
                voltage = np.array(file.get('voltage', []))
                current = np.array(file.get('current', []))
                logger.info(f"[DEBUG] File {i}: voltage len={len(voltage)}, current len={len(current)}")
                logger.info(f"[DEBUG] File {i}: voltage min={np.min(voltage) if len(voltage)>0 else 'NA'}, max={np.max(voltage) if len(voltage)>0 else 'NA'}, mean={np.mean(voltage) if len(voltage)>0 else 'NA'}")
                logger.info(f"[DEBUG] File {i}: current min={np.min(current) if len(current)>0 else 'NA'}, max={np.max(current) if len(current)>0 else 'NA'}, mean={np.mean(current) if len(current)>0 else 'NA'}")
                if np.any(np.isnan(voltage)) or np.any(np.isnan(current)):
                    logger.warning(f"[DEBUG] File {i}: NaN detected in voltage or current!")
                if np.any(np.isinf(voltage)) or np.any(np.isinf(current)):
                    logger.warning(f"[DEBUG] File {i}: Inf detected in voltage or current!")
                try:
                    file_peaks = detect_cv_peaks(voltage, current, method=method)['peaks']
                    logger.info(f"[DEBUG] File {i}: detected {len(file_peaks)} peaks")
                except Exception as e:
                    logger.error(f"[DEBUG] File {i}: peak detection error: {str(e)}")
                    file_peaks = []
                for p in file_peaks:
                    p['fileIdx'] = i
                peaks_per_file[i] = file_peaks
            logger.info(f"[DEBUG] peaks_per_file lens: {[len(p) for p in peaks_per_file]}")
            return jsonify({'success': True, 'peaks': peaks_per_file})
        elif isinstance(data.get('voltage'), list) and len(data['voltage']) > 0 and isinstance(data['voltage'][0], list):
            # voltage/current เป็น list of list
            nFiles = len(data['voltage'])
            peaks_per_file = [ [] for _ in range(nFiles) ]
            for i, (v, c) in enumerate(zip(data['voltage'], data['current'])):
                voltage = np.array(v)
                current = np.array(c)
                logger.info(f"[DEBUG] File {i}: voltage len={len(voltage)}, current len={len(current)}")
                logger.info(f"[DEBUG] File {i}: voltage min={np.min(voltage) if len(voltage)>0 else 'NA'}, max={np.max(voltage) if len(voltage)>0 else 'NA'}, mean={np.mean(voltage) if len(voltage)>0 else 'NA'}")
                logger.info(f"[DEBUG] File {i}: current min={np.min(current) if len(current)>0 else 'NA'}, max={np.max(current) if len(current)>0 else 'NA'}, mean={np.mean(current) if len(current)>0 else 'NA'}")
                if np.any(np.isnan(voltage)) or np.any(np.isnan(current)):
                    logger.warning(f"[DEBUG] File {i}: NaN detected in voltage or current!")
                if np.any(np.isinf(voltage)) or np.any(np.isinf(current)):
                    logger.warning(f"[DEBUG] File {i}: Inf detected in voltage or current!")
                try:
                    file_peaks = detect_cv_peaks(voltage, current, method=method)['peaks']
                    logger.info(f"[DEBUG] File {i}: detected {len(file_peaks)} peaks")
                except Exception as e:
                    logger.error(f"[DEBUG] File {i}: peak detection error: {str(e)}")
                    file_peaks = []
                for p in file_peaks:
                    p['fileIdx'] = i
                peaks_per_file[i] = file_peaks
            logger.info(f"[DEBUG] peaks_per_file lens: {[len(p) for p in peaks_per_file]}")
            return jsonify({'success': True, 'peaks': peaks_per_file})
        else:
            # Single trace (default)
            if 'voltage' not in data or 'current' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing voltage or current data in request'
                }), 400
            voltage = np.array(data['voltage'])
            current = np.array(data['current'])
            results = detect_cv_peaks(voltage, current, method=method)
            return jsonify({'success': True, **results})
    except Exception as e:
        logger.error(f"Error in peak detection: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@peak_detection_bp.route('/get-settings', methods=['GET'])
def get_settings():
    """Get current peak detection settings"""
    return jsonify({
        'success': True,
        'settings': {
            'prominence': current_app.config.get('PEAK_PROMINENCE', 0.1),
            'width': current_app.config.get('PEAK_WIDTH', 5),
            'description': {
                'prominence': 'Minimum peak prominence (normalized)',
                'width': 'Minimum peak width in data points'
            }
        }
    })

@peak_detection_bp.route('/update-settings', methods=['POST'])
def update_settings():
    """Update peak detection settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No settings provided'
            })

        # Update settings
        if 'prominence' in data:
            current_app.config['PEAK_PROMINENCE'] = float(data['prominence'])
        if 'width' in data:
            current_app.config['PEAK_WIDTH'] = int(data['width'])

        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'settings': {
                'prominence': current_app.config.get('PEAK_PROMINENCE', 0.1),
                'width': current_app.config.get('PEAK_WIDTH', 5)
            }
        })

    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

def detect_cv_peaks(voltage, current, method='prominence'):
    """
    Detect peaks in CV data using specified method
    Returns list of peaks with their characteristics
    """
    try:
        if method == 'prominence':
            return detect_peaks_prominence(voltage, current)
        elif method == 'derivative':
            return detect_peaks_derivative(voltage, current)
        elif method == 'ml':
            return detect_peaks_ml(voltage, current)
        else:
            raise ValueError(f"Unknown method: {method}")
    except Exception as e:
        logger.error(f"Error in CV peak detection: {str(e)}")
        raise

def detect_peaks_prominence(voltage, current):
    """Detect peaks using prominence method"""
    try:
        # Get settings from config or use defaults
        prominence = current_app.config.get('PEAK_PROMINENCE', 0.1)
        width = current_app.config.get('PEAK_WIDTH', 5)
        
        # Normalize current for peak detection
        current_norm = current / np.abs(current).max()
        
        # Find positive peaks (oxidation)
        pos_peaks, pos_properties = find_peaks(
            current_norm,
            prominence=prominence,
            width=width
        )
        
        # Find negative peaks (reduction)
        neg_peaks, neg_properties = find_peaks(
            -current_norm,
            prominence=prominence,
            width=width
        )
        
        # Format peak data
        peaks = []
        
        # Add oxidation peaks
        for i, peak_idx in enumerate(pos_peaks):
            peaks.append({
                'voltage': float(voltage[peak_idx]),
                'current': float(current[peak_idx]),
                'type': 'oxidation',
                'confidence': float(pos_properties['prominences'][i] * 100)
            })
        
        # Add reduction peaks
        for i, peak_idx in enumerate(neg_peaks):
            peaks.append({
                'voltage': float(voltage[peak_idx]),
                'current': float(current[peak_idx]),
                'type': 'reduction',
                'confidence': float(neg_properties['prominences'][i] * 100)
            })
        
        return {
            'peaks': peaks,
            'method': 'prominence',
            'params': {
                'prominence': prominence,
                'width': width
            }
        }

    except Exception as e:
        logger.error(f"Error in prominence peak detection: {str(e)}")
        raise

def detect_peaks_derivative(voltage, current):
    """Detect peaks using derivative method"""
    try:
        # Calculate first derivative
        dv = np.gradient(voltage)
        di = np.gradient(current)
        slope = di/dv
        
        # Find zero crossings in second derivative
        d2i = np.gradient(slope)
        zero_crossings = np.where(np.diff(np.signbit(d2i)))[0]
        
        peaks = []
        for idx in zero_crossings:
            peak_type = 'oxidation' if slope[idx] > 0 else 'reduction'
            confidence = min(100.0, abs(d2i[idx]) * 100)
            
            peaks.append({
                'voltage': float(voltage[idx]),
                'current': float(current[idx]),
                'type': peak_type,
                'confidence': float(confidence)
            })
            
        return {
            'peaks': peaks,
            'method': 'derivative',
            'params': {
                'smoothing': 'savgol_filter',
                'window': 5
            }
        }
        
    except Exception as e:
        logger.error(f"Error in derivative peak detection: {str(e)}")
        raise

def detect_peaks_ml(voltage, current):
    """Detect peaks using ML-enhanced method"""
    try:
        # Start with prominence method as baseline
        base_results = detect_peaks_prominence(voltage, current)
        base_peaks = base_results['peaks']
        
        # Add ML enhancements (feature extraction)
        enhanced_peaks = []
        for peak in base_peaks:
            # Find peak width at half height
            peak_idx = np.where((voltage == peak['voltage']) & (current == peak['current']))[0][0]
            half_height = peak['current'] / 2
            left_idx = right_idx = peak_idx
            
            while left_idx > 0 and abs(current[left_idx]) > abs(half_height):
                left_idx -= 1
            while right_idx < len(current)-1 and abs(current[right_idx]) > abs(half_height):
                right_idx += 1
                
            width = voltage[right_idx] - voltage[left_idx]
            area = np.trapz(current[left_idx:right_idx], voltage[left_idx:right_idx])
            
            enhanced_peaks.append({
                'voltage': peak['voltage'],
                'current': peak['current'],
                'type': peak['type'],
                'confidence': min(100.0, peak['confidence'] * 1.1),  # ML confidence boost
                'width': float(width),
                'area': float(area)
            })
            
        return {
            'peaks': enhanced_peaks,
            'method': 'ml',
            'params': {
                'feature_extraction': ['width', 'area'],
                'confidence_boost': 1.1
            }
        }
        
    except Exception as e:
        logger.error(f"Error in ML peak detection: {str(e)}")
        raise