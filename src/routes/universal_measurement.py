"""
Universal Measurement API for all electrochemical measurement modes
Supports CV, DPV, SWV, and CA measurements with unified interface
"""

from flask import Blueprint, request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

# Create blueprint
universal_measurement = Blueprint('universal_measurement', __name__)

def get_measurement_service(mode):
    """Get the appropriate measurement service for the mode"""
    mode = mode.upper()
    
    if mode == 'CV':
        service = getattr(current_app, 'cv_service', None)
        # Update service to use shared scpi_handler for consistent connection state
        if service and hasattr(current_app, 'config'):
            service.scpi_handler = current_app.config.get('scpi_handler')
        return service
    elif mode == 'DPV':
        service = getattr(current_app, 'dpv_service', None)
        if service and hasattr(current_app, 'config'):
            service.scpi_handler = current_app.config.get('scpi_handler')
        return service
    elif mode == 'SWV':
        service = getattr(current_app, 'swv_service', None)
        if service and hasattr(current_app, 'config'):
            service.scpi_handler = current_app.config.get('scpi_handler')
        return service
    elif mode == 'CA':
        service = getattr(current_app, 'ca_service', None)
        if service and hasattr(current_app, 'config'):
            service.scpi_handler = current_app.config.get('scpi_handler')
        return service
    else:
        return None

@universal_measurement.route('/api/measurement/setup', methods=['POST'])
def setup_measurement():
    """Setup measurement with specified mode and parameters"""
    try:
        data = request.get_json()
        mode = data.get('mode', '').upper()
        params = data.get('parameters', {})
        
        logger.info(f"Setup request for {mode} mode with params: {params}")
        
        # Get appropriate service
        service = get_measurement_service(mode)
        if not service:
            return jsonify({
                'success': False,
                'error': f'Unsupported measurement mode: {mode}'
            }), 400
        
        # Setup measurement
        success = service.setup_measurement(params)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'{mode} measurement setup successful',
                'mode': mode
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to setup {mode} measurement'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in setup_measurement: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@universal_measurement.route('/api/measurement/start', methods=['POST'])
def start_measurement():
    """Start measurement for specified mode"""
    try:
        data = request.get_json()
        mode = data.get('mode', '').upper()
        
        logger.info(f"Start request for {mode} mode")
        
        # Get appropriate service
        service = get_measurement_service(mode)
        if not service:
            return jsonify({
                'success': False,
                'error': f'Unsupported measurement mode: {mode}'
            }), 400
        
        # Start measurement
        success = service.start_measurement()
        
        if success:
            return jsonify({
                'success': True,
                'message': f'{mode} measurement started',
                'mode': mode
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to start {mode} measurement'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in start_measurement: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@universal_measurement.route('/api/measurement/stop', methods=['POST'])
def stop_measurement():
    """Stop measurement for specified mode"""
    try:
        data = request.get_json()
        mode = data.get('mode', '').upper()
        
        logger.info(f"Stop request for {mode} mode")
        
        # Get appropriate service
        service = get_measurement_service(mode)
        if not service:
            return jsonify({
                'success': False,
                'error': f'Unsupported measurement mode: {mode}'
            }), 400
        
        # Stop measurement
        success = service.stop_measurement()
        
        if success:
            return jsonify({
                'success': True,
                'message': f'{mode} measurement stopped',
                'mode': mode
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to stop {mode} measurement'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in stop_measurement: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@universal_measurement.route('/api/measurement/data/<mode>')
def get_measurement_data(mode):
    """Get measurement data for specified mode"""
    try:
        mode = mode.upper()
        
        # Get appropriate service
        service = get_measurement_service(mode)
        if not service:
            return jsonify({
                'success': False,
                'error': f'Unsupported measurement mode: {mode}'
            }), 400
        
        # Get measurement data
        data = service.get_measurement_data()
        
        return jsonify({
            'success': True,
            'mode': mode,
            'data': data
        })
        
    except Exception as e:
        logger.error(f"Error in get_measurement_data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@universal_measurement.route('/api/measurement/status/<mode>')
def get_measurement_status(mode):
    """Get measurement status for specified mode"""
    try:
        mode = mode.upper()
        
        # Get appropriate service
        service = get_measurement_service(mode)
        if not service:
            return jsonify({
                'success': False,
                'error': f'Unsupported measurement mode: {mode}'
            }), 400
        
        # Get measurement status
        status = service.get_status()
        
        return jsonify({
            'success': True,
            'mode': mode,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"Error in get_measurement_status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@universal_measurement.route('/api/measurement/export/<mode>')
def export_measurement_data(mode):
    """Export measurement data for specified mode"""
    try:
        mode = mode.upper()
        
        # Get appropriate service
        service = get_measurement_service(mode)
        if not service:
            return jsonify({
                'success': False,
                'error': f'Unsupported measurement mode: {mode}'
            }), 400
        
        # Export measurement data
        export_result = service.export_data()
        
        return jsonify({
            'success': export_result['success'],
            'mode': mode,
            'data': export_result.get('data'),
            'message': export_result.get('message')
        })
        
    except Exception as e:
        logger.error(f"Error in export_measurement_data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@universal_measurement.route('/api/measurement/modes')
def get_available_modes():
    """Get list of available measurement modes"""
    try:
        modes = []
        
        # Check which services are available
        if hasattr(current_app, 'cv_service') and current_app.cv_service:
            modes.append({
                'mode': 'CV',
                'name': 'Cyclic Voltammetry',
                'description': 'Triangular waveform potential sweep',
                'parameters': ['begin_voltage', 'upper_voltage', 'lower_voltage', 'scan_rate', 'cycles']
            })
        
        if hasattr(current_app, 'dpv_service') and current_app.dpv_service:
            modes.append({
                'mode': 'DPV',
                'name': 'Differential Pulse Voltammetry',
                'description': 'Pulsed potential with differential current measurement',
                'parameters': ['initial_potential', 'final_potential', 'pulse_height', 'pulse_increment', 'pulse_width', 'pulse_period']
            })
        
        if hasattr(current_app, 'swv_service') and current_app.swv_service:
            modes.append({
                'mode': 'SWV',
                'name': 'Square Wave Voltammetry',
                'description': 'Square wave modulation with differential measurement',
                'parameters': ['start_potential', 'end_potential', 'frequency', 'amplitude', 'step_potential']
            })
        
        if hasattr(current_app, 'ca_service') and current_app.ca_service:
            modes.append({
                'mode': 'CA',
                'name': 'Chronoamperometry',
                'description': 'Constant potential with current vs time measurement',
                'parameters': ['initial_potential', 'step_potential', 'duration', 'sampling_interval']
            })
        
        return jsonify({
            'success': True,
            'modes': modes,
            'total_modes': len(modes)
        })
        
    except Exception as e:
        logger.error(f"Error in get_available_modes: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500