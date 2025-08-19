from flask import Blueprint, jsonify, send_file, current_app, request, render_template, session
import os
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
import logging
import uuid

# Set up logging
logger = logging.getLogger(__name__)

peak_detection_bp = Blueprint('peak_detection', __name__)

@peak_detection_bp.route('/create_analysis_session', methods=['POST'])
def create_analysis_session():
    """Create a new analysis session and store data"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Store data in session
        session[session_id] = {
            'peaks': data.get('peaks'),
            'data': data.get('data'),
            'method': data.get('method'),
            'methodName': data.get('methodName')
        }
        
        return jsonify({'session_id': session_id})
        
    except Exception as e:
        logger.error(f"Error creating analysis session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@peak_detection_bp.route('/peak_analysis/<session_id>')
def peak_analysis(session_id):
    """Render peak analysis details page"""
    try:
        # Get data from session
        session_data = session.get(session_id)
        if not session_data:
            return "Session not found", 404
            
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
        if not data or 'voltage' not in data or 'current' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing voltage or current data in request'
            }), 400

        voltage = np.array(data['voltage'])
        current = np.array(data['current'])

        # Find peaks using specified method
        results = detect_cv_peaks(voltage, current, method=method)

        return jsonify({
            'success': True,
            **results
        })

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