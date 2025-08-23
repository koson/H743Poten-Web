"""
Parameter Logging API Routes
Provides endpoints for saving and retrieving analysis parameters
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging
import traceback

try:
    # Try relative import first
    from ..services.parameter_logging import parameter_logger
except ImportError:
    # Fall back to absolute import
    from services.parameter_logging import parameter_logger

logger = logging.getLogger(__name__)

parameter_bp = Blueprint('parameter', __name__, url_prefix='/api/parameters')

@parameter_bp.route('/save_analysis', methods=['POST'])
def save_analysis():
    """
    Save complete analysis session (measurement + peaks)
    
    Expected JSON:
    {
        "measurement": {
            "sample_id": "sample_001",
            "instrument_type": "palmsens|stm32", 
            "scan_rate": 50,
            "voltage_start": -0.4,
            "voltage_end": 0.6,
            "user_notes": "Test sample",
            "original_filename": "data.csv"
        },
        "peaks": [
            {
                "type": "oxidation",
                "voltage": 0.2,
                "current": 15.5,
                "height": 12.3,
                "enabled": true,
                ...
            }
        ],
        "raw_data": {...}  // For STM32 data
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'measurement' not in data or 'peaks' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: measurement, peaks'
            }), 400
        
        measurement_data = data['measurement']
        peaks_data = data['peaks']
        
        # Add timestamp if not provided
        if 'timestamp' not in measurement_data:
            measurement_data['timestamp'] = datetime.now()
        
        # Add data points count
        if 'data_points' not in measurement_data and 'raw_data' in data:
            raw_data = data['raw_data']
            if isinstance(raw_data, dict) and 'voltage' in raw_data:
                measurement_data['data_points'] = len(raw_data['voltage'])
        
        # Add raw data for STM32
        if measurement_data.get('instrument_type') == 'stm32' and 'raw_data' in data:
            measurement_data['raw_data'] = data['raw_data']
        
        # Save measurement
        measurement_id = parameter_logger.save_measurement(measurement_data)
        
        # Save peaks
        saved_peaks = parameter_logger.save_peak_parameters(measurement_id, peaks_data)
        
        return jsonify({
            'success': True,
            'measurement_id': measurement_id,
            'peaks_saved': saved_peaks,
            'message': f'Saved analysis for {measurement_data.get("sample_id", "unknown")} ({measurement_data.get("instrument_type", "unknown")})'
        })
        
    except Exception as e:
        logger.error(f"Error saving analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@parameter_bp.route('/measurements', methods=['GET'])
def get_measurements():
    """Get measurements with optional filtering"""
    try:
        sample_id = request.args.get('sample_id')
        instrument_type = request.args.get('instrument_type')
        
        measurements = parameter_logger.get_measurements(sample_id, instrument_type)
        
        return jsonify({
            'success': True,
            'measurements': measurements,
            'count': len(measurements)
        })
        
    except Exception as e:
        logger.error(f"Error getting measurements: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@parameter_bp.route('/measurements/<int:measurement_id>/peaks', methods=['GET'])
def get_measurement_peaks(measurement_id):
    """Get peak parameters for a specific measurement"""
    try:
        peaks = parameter_logger.get_peak_parameters(measurement_id)
        
        return jsonify({
            'success': True,
            'measurement_id': measurement_id,
            'peaks': peaks,
            'count': len(peaks)
        })
        
    except Exception as e:
        logger.error(f"Error getting peaks for measurement {measurement_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@parameter_bp.route('/calibration_pairs/<string:sample_id>', methods=['GET'])
def get_calibration_pairs(sample_id):
    """Get available calibration pairs for a sample"""
    try:
        pairs = parameter_logger.get_calibration_pairs(sample_id)
        
        return jsonify({
            'success': True,
            'sample_id': sample_id,
            'pairs': pairs,
            'count': len(pairs)
        })
        
    except Exception as e:
        logger.error(f"Error getting calibration pairs for {sample_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@parameter_bp.route('/create_calibration_session', methods=['POST'])
def create_calibration_session():
    """
    Create a new calibration session
    
    Expected JSON:
    {
        "session_name": "Sample_001_Calibration",
        "reference_measurement_id": 1,
        "target_measurement_id": 2,
        "calibration_method": "linear",
        "notes": "Initial calibration attempt"
    }
    """
    try:
        data = request.get_json()
        
        required_fields = ['session_name', 'reference_measurement_id', 'target_measurement_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        session_id = parameter_logger.create_calibration_session(data)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': f'Created calibration session: {data["session_name"]}'
        })
        
    except Exception as e:
        logger.error(f"Error creating calibration session: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@parameter_bp.route('/export/<int:measurement_id>', methods=['GET'])
def export_measurement(measurement_id):
    """Export measurement data in various formats"""
    try:
        format_type = request.args.get('format', 'json')  # json, csv, excel
        
        # Get measurement
        measurements = parameter_logger.get_measurements()
        measurement = next((m for m in measurements if m['id'] == measurement_id), None)
        
        if not measurement:
            return jsonify({
                'success': False,
                'error': f'Measurement {measurement_id} not found'
            }), 404
        
        # Get peaks
        peaks = parameter_logger.get_peak_parameters(measurement_id)
        
        export_data = {
            'measurement': measurement,
            'peaks': peaks,
            'export_timestamp': datetime.now().isoformat(),
            'export_format': format_type
        }
        
        if format_type == 'json':
            return jsonify({
                'success': True,
                'data': export_data
            })
        elif format_type == 'csv':
            # TODO: Implement CSV export
            return jsonify({
                'success': False,
                'error': 'CSV export not yet implemented'
            }), 501
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported format: {format_type}'
            }), 400
            
    except Exception as e:
        logger.error(f"Error exporting measurement {measurement_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@parameter_bp.route('/samples', methods=['GET'])
def get_samples():
    """Get list of unique sample IDs"""
    try:
        measurements = parameter_logger.get_measurements()
        sample_ids = list(set(m['sample_id'] for m in measurements if m['sample_id']))
        sample_ids.sort()
        
        return jsonify({
            'success': True,
            'samples': sample_ids,
            'count': len(sample_ids)
        })
        
    except Exception as e:
        logger.error(f"Error getting samples: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500