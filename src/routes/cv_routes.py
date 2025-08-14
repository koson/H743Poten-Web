"""
CV Measurement Routes for H743Poten Web Interface
"""

from flask import Blueprint, request, jsonify, current_app
import logging
import time

logger = logging.getLogger(__name__)

cv_bp = Blueprint('cv', __name__, url_prefix='/api/cv')

@cv_bp.route('/simulation', methods=['POST'])
def set_simulation_mode():
    """Enable or disable simulation mode"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        # Get CV service from app config
        cv_service = current_app.config.get('cv_service')
        if not cv_service:
            return jsonify({'success': False, 'error': 'CV service not available'}), 500
        
        cv_service.set_simulation_mode(enabled)
        return jsonify({
            'success': True,
            'message': f"Simulation mode {'enabled' if enabled else 'disabled'}",
            'simulation_mode': enabled
        })
        
    except Exception as e:
        logger.error(f"Failed to set simulation mode: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cv_bp.route('/setup', methods=['POST'])
def setup_cv_measurement():
    """Setup CV measurement parameters"""
    try:
        data = request.get_json()
        params = data.get('params', {})
        
        # Get CV service from app config
        cv_service = current_app.config.get('cv_service')
        if not cv_service:
            return jsonify({'success': False, 'error': 'CV service not available'}), 500
        
        success, message = cv_service.setup_measurement(params)
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Failed to setup CV measurement: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cv_bp.route('/start', methods=['POST'])
def start_cv_measurement():
    """Start CV measurement"""
    try:
        cv_service = current_app.config.get('cv_service')
        if not cv_service:
            return jsonify({'success': False, 'error': 'CV service not available'}), 500
        
        success, message = cv_service.start_measurement()
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Failed to start CV measurement: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cv_bp.route('/stop', methods=['POST'])
def stop_cv_measurement():
    """Stop CV measurement"""
    try:
        cv_service = current_app.config.get('cv_service')
        if not cv_service:
            return jsonify({'success': False, 'error': 'CV service not available'}), 500
        
        success, message = cv_service.stop_measurement()
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Failed to stop CV measurement: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cv_bp.route('/pause', methods=['POST'])
def pause_cv_measurement():
    """Pause CV measurement"""
    try:
        cv_service = current_app.config.get('cv_service')
        if not cv_service:
            return jsonify({'success': False, 'error': 'CV service not available'}), 500
        
        success, message = cv_service.pause_measurement()
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Failed to pause CV measurement: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cv_bp.route('/resume', methods=['POST'])
def resume_cv_measurement():
    """Resume CV measurement"""
    try:
        cv_service = current_app.config.get('cv_service')
        if not cv_service:
            return jsonify({'success': False, 'error': 'CV service not available'}), 500
        
        success, message = cv_service.resume_measurement()
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Failed to resume CV measurement: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cv_bp.route('/status')
def get_cv_status():
    """Get CV measurement status"""
    try:
        cv_service = current_app.config.get('cv_service')
        if not cv_service:
            return jsonify({'error': 'CV service not available'}), 500
        
        status = cv_service.get_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Failed to get CV status: {e}")
        return jsonify({'error': str(e)}), 500

@cv_bp.route('/data')
def get_cv_data():
    """Get CV measurement data"""
    try:
        # Get optional limit parameter
        limit = request.args.get('limit', type=int)
        
        cv_service = current_app.config.get('cv_service')
        if not cv_service:
            return jsonify({'error': 'CV service not available'}), 500
        
        data_points = cv_service.get_data_points(limit=limit)
        return jsonify({
            'data_points': data_points,
            'count': len(data_points),
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Failed to get CV data: {e}")
        return jsonify({'error': str(e)}), 500

@cv_bp.route('/data/stream')
def stream_cv_data():
    """Get real-time CV data stream"""
    try:
        cv_service = current_app.config.get('cv_service')
        if not cv_service:
            return jsonify({'error': 'CV service not available'}), 500
        
        # Get ALL data points for proper CV plotting (remove limit)
        # Frontend will handle incremental updates efficiently
        print(f"[CV DEBUG] About to call get_data_points() without limit")
        data_points = cv_service.get_data_points()  # No limit = all data
        status = cv_service.get_status()
        
        # Debug logging for data sync issues
        total_points = len(data_points)
        backend_count = status.get('data_points_count', 0)
        
        print(f"[CV DEBUG] Streaming API - returning {total_points} points, backend has {backend_count}")
        logger.info(f"[DEBUG] Streaming API called - returning {total_points} points, backend has {backend_count}")
        
        if total_points != backend_count:
            print(f"[CV DEBUG] MISMATCH: returning {total_points} vs backend {backend_count}")
            logger.warning(f"Data count mismatch: returning {total_points} points but status says {backend_count}")
        
        # Check voltage range for debugging
        if data_points:
            voltages = [p.get('potential', 0) for p in data_points]
            min_v, max_v = min(voltages), max(voltages)
            negative_count = sum(1 for v in voltages if v < 0)
            print(f"[CV DEBUG] V range: {min_v:.4f} to {max_v:.4f}, negative: {negative_count}/{total_points}")
            logger.info(f"[DEBUG] V range: {min_v:.4f} to {max_v:.4f}, negative: {negative_count}/{total_points}")
        
        return jsonify({
            'data_points': data_points,
            'status': status,
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Failed to stream CV data: {e}")
        return jsonify({'error': str(e)}), 500

@cv_bp.route('/export/csv')
def export_cv_csv():
    """Export CV data as CSV"""
    try:
        cv_service = current_app.config.get('cv_service')
        if not cv_service:
            return jsonify({'error': 'CV service not available'}), 500
        
        csv_data = cv_service.export_data_csv()
        if not csv_data:
            return jsonify({'error': 'No data to export'}), 400
        
        # Return CSV data
        from flask import Response
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f'cv_measurement_{timestamp}.csv'
        
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
    except Exception as e:
        logger.error(f"Failed to export CV data: {e}")
        return jsonify({'error': str(e)}), 500

@cv_bp.route('/defaults')
def get_cv_defaults():
    """Get default CV parameters"""
    return jsonify({
        'begin': 0.0,
        'upper': 0.7,
        'lower': -0.4,
        'rate': 0.1,
        'cycles': 1,
        'description': 'Default CV parameters for H743Poten'
    })

@cv_bp.route('/validate', methods=['POST'])
def validate_cv_parameters():
    """Validate CV parameters without starting measurement"""
    try:
        data = request.get_json()
        params = data.get('params', {})
        
        # Import CV parameters for validation
        import sys
        import os
        
        # Add the parent directory to the Python path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        
        try:
            from services.cv_measurement_service import CVParameters
        except ImportError:
            # Fallback import
            from ..services.cv_measurement_service import CVParameters
        
        try:
            cv_params = CVParameters(
                begin=float(params.get('begin', 0.0)),
                upper=float(params.get('upper', 1.0)), 
                lower=float(params.get('lower', -1.0)),
                rate=float(params.get('rate', 0.1)),
                cycles=int(params.get('cycles', 1))
            )
            
            is_valid, message = cv_params.validate()
            
            return jsonify({
                'valid': is_valid,
                'message': message,
                'scpi_command': cv_params.to_scpi_command() if is_valid else None
            })
            
        except (ValueError, TypeError) as e:
            return jsonify({
                'valid': False,
                'message': f'Invalid parameter format: {e}',
                'scpi_command': None
            })
        
    except Exception as e:
        logger.error(f"Failed to validate CV parameters: {e}")
        return jsonify({
            'valid': False, 
            'message': f'Validation error: {e}',
            'scpi_command': None
        })
