"""
Parameter API Routes - Updated Version
Provides API endpoints for parameter management
"""

from flask import Blueprint, request, jsonify, current_app, render_template, send_file
from datetime import datetime
import logging
import traceback
import io
import csv
import json

try:
    # Try relative import first
    from ..services.parameter_logging import parameter_logger
    from ..services.hybrid_data_manager import hybrid_manager
except ImportError:
    # Fall back to absolute import
    from services.parameter_logging import parameter_logger
    from services.hybrid_data_manager import hybrid_manager

logger = logging.getLogger(__name__)

# Dashboard route (no prefix)
parameter_bp = Blueprint('parameter', __name__)

@parameter_bp.route('/parameter_dashboard')
def parameter_dashboard():
    """Display parameter management dashboard"""
    logger.info("Parameter dashboard accessed")
    return render_template('parameter_dashboard.html')

# API routes with prefix
parameter_api_bp = Blueprint('parameter_api', __name__, url_prefix='/api/parameters')

@parameter_api_bp.route('/save_analysis', methods=['POST'])
def save_analysis():
    """
    Save complete analysis session (measurement + peaks)
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
        
        # Ensure peaks_data is a dictionary, not a string
        if isinstance(peaks_data, str):
            try:
                peaks_data = json.loads(peaks_data)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse peaks_data as JSON: {peaks_data}")
                peaks_data = {}
        
        # Save measurement
        measurement_id = parameter_logger.save_measurement(measurement_data)
        
        # Save peaks (handle both dict and string formats)
        peaks_saved_count = 0
        if peaks_data:
            # Convert dict format to list format expected by save_peak_parameters
            if isinstance(peaks_data, dict):
                # Convert peak dict to list of peaks
                peaks_list = []
                for peak_name, peak_info in peaks_data.items():
                    if isinstance(peak_info, dict):
                        peak_info['peak_type'] = peak_name
                        peak_info['enabled'] = True
                        peaks_list.append(peak_info)
                peaks_data = peaks_list
            
            peaks_saved_count = parameter_logger.save_peak_parameters(measurement_id, peaks_data)
            if peaks_saved_count is None:
                peaks_saved_count = len(peaks_data) if isinstance(peaks_data, list) else 0
        
        # 🚀 AUTO-EXPORT: Save CV data to files immediately
        cv_data = None
        if 'cv_data' in data:
            cv_data = data['cv_data']
        elif 'raw_data' in measurement_data:
            # Extract CV data from raw data if available
            raw_data = measurement_data['raw_data']
            if isinstance(raw_data, list):
                cv_data = raw_data
        
        # Export CV data to file system
        if cv_data:
            try:
                # Save to database
                parameter_logger.update_measurement_cv_data(measurement_id, cv_data)
                
                # Save to file system with mapping
                export_success = hybrid_manager.save_cv_data_to_files(measurement_id, cv_data)
                
                if export_success:
                    logger.info(f"✅ Auto-exported CV data for measurement {measurement_id} to file system")
                else:
                    logger.warning(f"⚠️ Failed to export CV data for measurement {measurement_id} to file system")
                    
            except Exception as e:
                logger.error(f"Error auto-exporting CV data for measurement {measurement_id}: {e}")
        
        logger.info(f"Saved analysis session: measurement_id={measurement_id}")
        
        # Get file export info
        cv_info = hybrid_manager.get_cv_data_info(measurement_id) if cv_data else None
        export_file_path = cv_info.get('file_path') if cv_info else None
        
        return jsonify({
            'success': True,
            'measurement_id': measurement_id,
            'message': f'Analysis saved successfully (ID: {measurement_id})',
            'peaks_saved': peaks_saved_count,
            'cv_data_exported': cv_data is not None,
            'total_cv_points': len(cv_data) if cv_data else 0,
            'export_info': {
                'file_exported': export_file_path is not None,
                'file_path': export_file_path,
                'mapping_updated': cv_data is not None,
                'data_source': cv_info.get('source_used') if cv_info else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error saving analysis: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@parameter_api_bp.route('/measurements', methods=['GET'])
def get_measurements():
    """Get measurements with optional filtering"""
    try:
        sample_id = request.args.get('sample_id')
        instrument_type = request.args.get('instrument_type')
        
        measurements = parameter_logger.get_measurements(sample_id, instrument_type)
        
        return jsonify(measurements)
        
    except Exception as e:
        logger.error(f"Error getting measurements: {e}")
        return jsonify({'error': str(e)}), 500

@parameter_api_bp.route('/measurements/<int:measurement_id>/peaks', methods=['GET'])
def get_peaks(measurement_id):
    """Get peak parameters for a specific measurement"""
    try:
        peaks = parameter_logger.get_peak_parameters(measurement_id)
        
        # 🚀 USE HYBRID MANAGER: Get CV data from multiple sources
        cv_data = hybrid_manager.get_cv_data(measurement_id)
        
        # Get data source info for debugging
        cv_info = hybrid_manager.get_cv_data_info(measurement_id)
        data_source = cv_info.get('source_used', 'unknown')
        
        logger.info(f"📊 Retrieved CV data for measurement {measurement_id} from {data_source} ({len(cv_data)} points)")
        
        if not cv_data:
            logger.warning(f"⚠️ No CV data found for measurement {measurement_id}")
            cv_data = []
        
        return jsonify({
            'success': True,
            'measurement_id': measurement_id,
            'peaks': peaks,
            'cv_data': cv_data,
            'count': len(peaks),
            'data_source': data_source,
            'cv_data_points': len(cv_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting peaks for measurement {measurement_id}: {e}")
        return jsonify({'error': str(e)}), 500

@parameter_api_bp.route('/calibration/pairs', methods=['GET'])
def get_calibration_pairs():
    """Get all calibration pairs grouped by sample_id"""
    try:
        # Get all sample IDs
        measurements = parameter_logger.get_measurements()
        
        # Group by sample_id and find pairs
        sample_groups = {}
        for m in measurements:
            sample_id = m['sample_id']
            if sample_id not in sample_groups:
                sample_groups[sample_id] = {'reference': [], 'target': []}
            
            if m['instrument_type'] == 'palmsens':
                sample_groups[sample_id]['reference'].append(m)
            elif m['instrument_type'] == 'stm32':
                sample_groups[sample_id]['target'].append(m)
        
        # Convert to pairs format
        pairs = []
        for sample_id, group in sample_groups.items():
            if group['reference'] and group['target']:
                pairs.append({
                    'sample_id': sample_id,
                    'reference_measurements': group['reference'],
                    'target_measurements': group['target']
                })
        
        return jsonify(pairs)
        
    except Exception as e:
        logger.error(f"Error getting calibration pairs: {e}")
        return jsonify({'error': str(e)}), 500

@parameter_api_bp.route('/calibration/sessions', methods=['POST'])
def create_calibration_session():
    """Create a new calibration session"""
    try:
        data = request.get_json()
        
        required_fields = ['session_name', 'reference_measurement_id', 'target_measurement_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        session_data = {
            'session_name': data['session_name'],
            'reference_measurement_id': data['reference_measurement_id'],
            'target_measurement_id': data['target_measurement_id'],
            'calibration_method': data.get('calibration_method', 'linear'),
            'notes': data.get('notes', ''),
            'created_at': datetime.now()
        }
        
        session_id = parameter_logger.create_calibration_session(session_data)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': f'Calibration session created successfully (ID: {session_id})'
        })
        
    except Exception as e:
        logger.error(f"Error creating calibration session: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@parameter_api_bp.route('/export/csv', methods=['GET'])
def export_measurements_csv():
    """Export all measurements to CSV"""
    try:
        measurements = parameter_logger.get_measurements()
        
        if not measurements:
            return jsonify({'error': 'No measurements to export'}), 400
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Sample ID', 'Instrument Type', 'Timestamp', 'Scan Rate (mV/s)',
            'Voltage Start (V)', 'Voltage End (V)', 'Data Points', 'Original Filename', 'Notes'
        ])
        
        # Write data
        for m in measurements:
            writer.writerow([
                m['id'],
                m['sample_id'],
                m['instrument_type'],
                m['timestamp'],
                m['scan_rate'],
                m['voltage_start'],
                m['voltage_end'],
                m['data_points'],
                m['original_filename'],
                m['user_notes']
            ])
        
        # Prepare file download
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'measurements_export_{timestamp}.csv'
        
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting measurements: {e}")
        return jsonify({'error': str(e)}), 500

@parameter_api_bp.route('/samples', methods=['GET'])
def get_samples():
    """Get unique sample IDs"""
    try:
        samples = parameter_logger.get_unique_sample_ids()
        
        return jsonify({
            'success': True,
            'samples': samples,
            'count': len(samples)
        })
        
    except Exception as e:
        logger.error(f"Error getting samples: {e}")
        return jsonify({'error': str(e)}), 500

@parameter_api_bp.route('/measurements/<int:measurement_id>', methods=['DELETE'])
def delete_measurement(measurement_id):
    """Delete a measurement and all associated data"""
    try:
        logger.info(f"Attempting to delete measurement {measurement_id}")
        
        # Check if measurement exists
        measurement = parameter_logger.get_measurement_by_id(measurement_id)
        if not measurement:
            return jsonify({
                'success': False,
                'error': f'Measurement {measurement_id} not found'
            }), 404
        
        # Delete from hybrid data manager (files and mapping)
        try:
            hybrid_manager.delete_measurement_data(measurement_id)
            logger.info(f"Deleted hybrid data for measurement {measurement_id}")
        except Exception as e:
            # This is not a critical error - old data might not have files
            logger.info(f"No hybrid data to delete for measurement {measurement_id}: {e}")
        
        # Delete from database (will cascade to related records)
        result = parameter_logger.delete_measurement(measurement_id)
        
        if result:
            logger.info(f"Successfully deleted measurement {measurement_id}")
            return jsonify({
                'success': True,
                'message': f'Measurement {measurement_id} deleted successfully',
                'deleted_id': measurement_id
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to delete measurement {measurement_id}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error deleting measurement {measurement_id}: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@parameter_api_bp.route('/measurements/batch-delete', methods=['POST'])
def batch_delete_measurements():
    """Delete multiple measurements"""
    try:
        data = request.get_json()
        measurement_ids = data.get('measurement_ids', [])
        
        if not measurement_ids:
            return jsonify({
                'success': False,
                'error': 'No measurement IDs provided'
            }), 400
        
        logger.info(f"Attempting to delete {len(measurement_ids)} measurements: {measurement_ids}")
        
        deleted_ids = []
        failed_ids = []
        
        for measurement_id in measurement_ids:
            try:
                # Check if measurement exists
                measurement = parameter_logger.get_measurement_by_id(measurement_id)
                if not measurement:
                    failed_ids.append({
                        'id': measurement_id,
                        'error': 'Measurement not found'
                    })
                    continue
                
                # Delete from hybrid data manager
                try:
                    hybrid_manager.delete_measurement_data(measurement_id)
                except Exception as e:
                    # This is not a critical error - old data might not have files
                    logger.info(f"No hybrid data to delete for measurement {measurement_id}: {e}")
                
                # Delete from database
                result = parameter_logger.delete_measurement(measurement_id)
                
                if result:
                    deleted_ids.append(measurement_id)
                    logger.info(f"Successfully deleted measurement {measurement_id}")
                else:
                    failed_ids.append({
                        'id': measurement_id,
                        'error': 'Database deletion failed'
                    })
                    
            except Exception as e:
                failed_ids.append({
                    'id': measurement_id,
                    'error': str(e)
                })
                logger.error(f"Error deleting measurement {measurement_id}: {e}")
        
        return jsonify({
            'success': len(failed_ids) == 0,
            'deleted_count': len(deleted_ids),
            'deleted_ids': deleted_ids,
            'failed_count': len(failed_ids),
            'failed_ids': failed_ids,
            'message': f'Deleted {len(deleted_ids)} measurements, {len(failed_ids)} failed'
        })
        
    except Exception as e:
        logger.error(f"Error in batch delete: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500