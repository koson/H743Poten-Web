"""
Data Logging Routes for H743Poten Web Interface
Handles CV measurement data logging and browsing
"""

from flask import Blueprint, request, jsonify, current_app, send_file
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

data_logging_bp = Blueprint('data_logging', __name__, url_prefix='/api/data-logging')

@data_logging_bp.route('/save', methods=['POST'])
def save_measurement():
    """Save current CV measurement data and plot"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        # Get CV service and data logging service
        cv_service = current_app.config.get('cv_service')
        data_logging_service = current_app.config.get('data_logging_service')
        
        if not cv_service:
            return jsonify({'success': False, 'error': 'CV service not available'}), 500
        
        if not data_logging_service:
            return jsonify({'success': False, 'error': 'Data logging service not available'}), 500
        
        # Get current measurement data
        data_points = cv_service.get_data_points()
        status = cv_service.get_status()
        
        if not data_points:
            return jsonify({'success': False, 'error': 'No measurement data to save'}), 400
        
        # Get parameters from status
        parameters = status.get('parameters', {})
        
        # Add additional info
        parameters['measurement_type'] = 'CV'
        parameters['device_connected'] = status.get('device_connected', False)
        
        # Save data
        result = data_logging_service.save_cv_measurement(
            data_points=data_points,
            parameters=parameters,
            session_id=session_id
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Failed to save measurement: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@data_logging_bp.route('/sessions')
def list_sessions():
    """List all saved measurement sessions"""
    try:
        # Get optional parameters
        limit = request.args.get('limit', type=int)
        
        data_logging_service = current_app.config.get('data_logging_service')
        if not data_logging_service:
            return jsonify({'error': 'Data logging service not available'}), 500
        
        sessions = data_logging_service.list_sessions(limit=limit)
        
        return jsonify({
            'sessions': sessions,
            'count': len(sessions)
        })
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        return jsonify({'error': str(e)}), 500

@data_logging_bp.route('/sessions/<session_id>')
def get_session(session_id):
    """Get detailed information about a specific session"""
    try:
        data_logging_service = current_app.config.get('data_logging_service')
        if not data_logging_service:
            return jsonify({'error': 'Data logging service not available'}), 500
        
        session_data = data_logging_service.get_session_data(session_id)
        
        if not session_data:
            return jsonify({'error': f'Session {session_id} not found'}), 404
        
        return jsonify(session_data)
        
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {e}")
        return jsonify({'error': str(e)}), 500

@data_logging_bp.route('/sessions/<session_id>/download/<file_type>')
def download_session_file(session_id, file_type):
    """Download session file (csv or png)"""
    try:
        data_logging_service = current_app.config.get('data_logging_service')
        if not data_logging_service:
            return jsonify({'error': 'Data logging service not available'}), 500
        
        if file_type not in ['csv', 'png']:
            return jsonify({'error': 'Invalid file type. Use csv or png'}), 400
        
        # Get session directory
        session_dir = Path(data_logging_service.base_data_dir) / "sessions" / session_id
        
        if not session_dir.exists():
            return jsonify({'error': f'Session {session_id} not found'}), 404
        
        # Determine file path
        if file_type == 'csv':
            file_path = session_dir / f"{session_id}.csv"
            mimetype = 'text/csv'
        else:  # png
            file_path = session_dir / f"{session_id}.png"
            mimetype = 'image/png'
        
        if not file_path.exists():
            return jsonify({'error': f'{file_type.upper()} file not found for session {session_id}'}), 404
        
        return send_file(
            file_path,
            mimetype=mimetype,
            as_attachment=True,
            download_name=f"{session_id}.{file_type}"
        )
        
    except Exception as e:
        logger.error(f"Failed to download {file_type} for session {session_id}: {e}")
        return jsonify({'error': str(e)}), 500

@data_logging_bp.route('/sessions/<session_id>/view/png')
def view_session_png(session_id):
    """View session PNG file in browser"""
    try:
        data_logging_service = current_app.config.get('data_logging_service')
        if not data_logging_service:
            return jsonify({'error': 'Data logging service not available'}), 500
        
        # Get session directory
        session_dir = Path(data_logging_service.base_data_dir) / "sessions" / session_id
        
        if not session_dir.exists():
            return jsonify({'error': f'Session {session_id} not found'}), 404
        
        png_file = session_dir / f"{session_id}.png"
        
        if not png_file.exists():
            return jsonify({'error': f'PNG file not found for session {session_id}'}), 404
        
        return send_file(
            png_file,
            mimetype='image/png',
            as_attachment=False  # Display in browser
        )
        
    except Exception as e:
        logger.error(f"Failed to view PNG for session {session_id}: {e}")
        return jsonify({'error': str(e)}), 500

@data_logging_bp.route('/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a measurement session"""
    try:
        data_logging_service = current_app.config.get('data_logging_service')
        if not data_logging_service:
            return jsonify({'error': 'Data logging service not available'}), 500
        
        success, message = data_logging_service.delete_session(session_id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
        
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@data_logging_bp.route('/info')
def get_data_info():
    """Get information about data logging system"""
    try:
        data_logging_service = current_app.config.get('data_logging_service')
        if not data_logging_service:
            return jsonify({'error': 'Data logging service not available'}), 500
        
        info = data_logging_service.get_data_directory_info()
        
        return jsonify(info)
        
    except Exception as e:
        logger.error(f"Failed to get data info: {e}")
        return jsonify({'error': str(e)}), 500

@data_logging_bp.route('/auto-save', methods=['POST'])
def set_auto_save():
    """Enable/disable auto-save for measurements"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        # Store auto-save setting in app config
        current_app.config['auto_save_enabled'] = enabled
        
        return jsonify({
            'success': True,
            'auto_save_enabled': enabled,
            'message': f"Auto-save {'enabled' if enabled else 'disabled'}"
        })
        
    except Exception as e:
        logger.error(f"Failed to set auto-save: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@data_logging_bp.route('/auto-save')
def get_auto_save_status():
    """Get current auto-save status"""
    try:
        auto_save_enabled = current_app.config.get('auto_save_enabled', False)
        
        return jsonify({
            'auto_save_enabled': auto_save_enabled
        })
        
    except Exception as e:
        logger.error(f"Failed to get auto-save status: {e}")
        return jsonify({'error': str(e)}), 500
