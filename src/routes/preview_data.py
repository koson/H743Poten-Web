from flask import Blueprint, send_from_directory, jsonify
import os

preview_bp = Blueprint('preview', __name__)

@preview_bp.route('/temp_data/<path:filename>')
def serve_temp_file(filename):
    try:
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'temp_data')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        # Check if file exists
        file_path = os.path.join(temp_dir, filename)
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': f'File not found: {file_path}'
            }), 404
            
        # Try to read the file to verify access
        with open(file_path, 'r') as f:
            content = f.read()
            
        # If we can read it, serve it
        return send_from_directory(temp_dir, filename, as_attachment=False)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@preview_bp.route('/api/get-cv-data')
def get_cv_data():
    try:
        # Path to the CSV file
        csv_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'temp_data',
            'preview_Palmsens_Palmsens_0.5mM_CV_100mVpS_E1_scan_05.csv'
        )
        
        # Check if file exists
        if not os.path.exists(csv_path):
            return jsonify({
                'success': False,
                'error': 'CSV file not found'
            })
        
        # Read and parse CSV
        voltage = []
        current = []
        with open(csv_path, 'r') as f:
            # Skip header lines
            next(f)  # Skip filename
            next(f)  # Skip column headers
            
            for line in f:
                if line.strip():
                    v, i = map(float, line.strip().split(','))
                    voltage.append(v)
                    current.append(i)
        
        return jsonify({
            'success': True,
            'data_source': 'real',
            'file_name': 'preview_Palmsens_Palmsens_0.5mM_CV_100mVpS_E1_scan_05.csv',
            'voltage': voltage,
            'current': current
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })