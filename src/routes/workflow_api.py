from flask import Blueprint, jsonify, session
import os
import csv
import logging

logger = logging.getLogger(__name__)
workflow_api_bp = Blueprint('workflow_api', __name__, url_prefix='/api/workflow_api')

@workflow_api_bp.route('/debug-info')
def debug_info():
    """Debug endpoint to check paths and file existence"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    temp_dir = os.path.join(base_dir, 'temp_data')
    csv_path = os.path.join(temp_dir, 'preview_Palmsens_Palmsens_0.5mM_CV_100mVpS_E1_scan_05.csv')
    win_path = os.path.join('D:', os.path.relpath(csv_path, '/mnt/d'))
    
    # Get info from workflow session
    workflow_files = session.get('workflow_files', {})
    sample_path = workflow_files.get('sample_file_path')
    
    return jsonify({
        'base_dir_exists': os.path.exists(base_dir),
        'base_dir_path': base_dir,
        'temp_dir_exists': os.path.exists(temp_dir),
        'temp_dir_path': temp_dir,
        'temp_dir_contents': os.listdir(temp_dir) if os.path.exists(temp_dir) else [],
        'csv_path_exists': os.path.exists(csv_path),
        'csv_path': csv_path,
        'win_path_exists': os.path.exists(win_path),
        'win_path': win_path,
        'session_sample_path': sample_path,
        'session_sample_exists': os.path.exists(sample_path) if sample_path else False,
        'workflow_files': workflow_files
    })

@workflow_api_bp.route('/get-graph-data')
def get_graph_data():
    try:
        # First try to get path from session
        workflow_files = session.get('workflow_files', {})
        sample_path = workflow_files.get('sample_file_path')
        
        if sample_path and os.path.exists(sample_path):
            logger.info(f"Using sample path from session: {sample_path}")
            actual_path = sample_path
        else:
            # Fallback to default paths
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            csv_path = os.path.join(base_dir, 'temp_data', 'preview_Palmsens_Palmsens_0.5mM_CV_100mVpS_E1_scan_05.csv')
            win_path = os.path.join('D:', os.path.relpath(csv_path, '/mnt/d'))
            
            logger.info(f"Trying CSV paths - Unix: {csv_path}, Windows: {win_path}")
            
            # Try both Unix and Windows paths
            if os.path.exists(csv_path):
                actual_path = csv_path
                logger.info("Using Unix path")
            elif os.path.exists(win_path):
                actual_path = win_path
                logger.info("Using Windows path")
            else:
                debug_info = {
                    'base_dir': base_dir,
                    'temp_dir_exists': os.path.exists(os.path.join(base_dir, 'temp_data')),
                    'session_data': workflow_files
                }
                logger.error(f"CSV file not found. Debug info: {debug_info}")
                return jsonify({
                    'success': False,
                    'error': 'CSV file not found',
                    'paths_tried': [csv_path, win_path],
                    'debug_info': debug_info
                }), 404
            
        # Read CSV file
        voltage = []
        current = []
        try:
            with open(actual_path, 'r') as f:
                csv_reader = csv.reader(f)
                next(csv_reader)  # Skip the filename row
                next(csv_reader)  # Skip the header row
                for row in csv_reader:
                    if len(row) >= 2:
                        try:
                            v = float(row[0])
                            c = float(row[1])
                            voltage.append(v)
                            current.append(c)
                        except ValueError:
                            continue  # Skip invalid rows
            
            if not voltage or not current:
                raise ValueError("No valid data found in CSV")
                
            return jsonify({
                'success': True,
                'data': {
                    'voltage': voltage,
                    'current': current,
                    'fileName': os.path.basename(actual_path)
                }
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to read CSV: {str(e)}',
                'path': actual_path
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500