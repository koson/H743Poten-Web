"""
File Browser API for H743 Potentiostat
Handles file listing, download, and management
"""

import os
import mimetypes
from flask import Blueprint, jsonify, send_file, request, abort
from datetime import datetime
from typing import Dict, List, Any
import logging

# Import our modules
try:
    from database import db
    from file_exporter import exporter
except ImportError:
    # For standalone testing
    db = None
    exporter = None

logger = logging.getLogger(__name__)

# Create Blueprint for file browser
file_browser_bp = Blueprint('file_browser', __name__, url_prefix='/files')

@file_browser_bp.route('/list', methods=['GET'])
def list_files():
    """List all exported files"""
    try:
        file_type = request.args.get('type')  # csv, png, json
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        if not exporter:
            return jsonify({"success": False, "error": "File exporter not available"}), 500
        
        # Get all files
        all_files = exporter.list_exported_files(file_type)
        
        # Pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        files = all_files[start_idx:end_idx]
        
        # Add measurement info if database is available
        if db:
            for file_info in files:
                # Try to extract measurement ID from filename
                try:
                    # Filename format: TYPE_M{id}_{timestamp}.ext
                    parts = file_info['filename'].split('_')
                    if len(parts) >= 2 and parts[1].startswith('M'):
                        measurement_id = int(parts[1][1:])  # Remove 'M' prefix
                        measurement = db.get_measurement(measurement_id)
                        if measurement:
                            file_info['measurement'] = {
                                'id': measurement_id,
                                'type': measurement['measurement_type'],
                                'status': measurement['status'],
                                'timestamp': measurement['timestamp']
                            }
                except:
                    pass  # Skip if we can't parse measurement ID
        
        return jsonify({
            "success": True,
            "files": files,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": len(all_files),
                "pages": (len(all_files) + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to list files: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@file_browser_bp.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """Download a specific file"""
    try:
        # Security: prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            return jsonify({"success": False, "error": "Invalid filename"}), 400
        
        # Find file in export directories
        file_path = None
        for subdir in ['csv', 'png', 'json']:
            potential_path = os.path.join(exporter.export_dir, subdir, filename)
            if os.path.exists(potential_path) and os.path.isfile(potential_path):
                file_path = potential_path
                break
        
        if not file_path:
            return jsonify({"success": False, "error": "File not found"}), 404
        
        # Determine MIME type
        mimetype, _ = mimetypes.guess_type(filename)
        if not mimetype:
            if filename.endswith('.csv'):
                mimetype = 'text/csv'
            elif filename.endswith('.png'):
                mimetype = 'image/png'
            elif filename.endswith('.json'):
                mimetype = 'application/json'
            else:
                mimetype = 'application/octet-stream'
        
        return send_file(file_path, mimetype=mimetype, as_attachment=True)
        
    except Exception as e:
        logger.error(f"❌ Failed to download file {filename}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@file_browser_bp.route('/preview/<path:filename>', methods=['GET'])
def preview_file(filename):
    """Preview a file (for images) or return file info"""
    try:
        # Security check
        if '..' in filename or filename.startswith('/'):
            return jsonify({"success": False, "error": "Invalid filename"}), 400
        
        # Find file
        file_path = None
        file_type = None
        for subdir in ['csv', 'png', 'json']:
            potential_path = os.path.join(exporter.export_dir, subdir, filename)
            if os.path.exists(potential_path) and os.path.isfile(potential_path):
                file_path = potential_path
                file_type = subdir
                break
        
        if not file_path:
            return jsonify({"success": False, "error": "File not found"}), 404
        
        # For PNG files, serve directly
        if file_type == 'png':
            return send_file(file_path, mimetype='image/png')
        
        # For other files, return file info and preview
        stat = os.stat(file_path)
        file_info = {
            'filename': filename,
            'type': file_type,
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
        
        # Add content preview for small text files
        if file_type in ['csv', 'json'] and stat.st_size < 10000:  # Less than 10KB
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    if file_type == 'csv':
                        # Read first 20 lines for CSV preview
                        lines = []
                        for i, line in enumerate(f):
                            if i >= 20:
                                break
                            lines.append(line.strip())
                        file_info['preview'] = lines
                    elif file_type == 'json':
                        # Read and parse JSON
                        import json
                        f.seek(0)
                        content = json.load(f)
                        file_info['preview'] = content
            except:
                file_info['preview'] = "Preview not available"
        
        return jsonify({
            "success": True,
            "file": file_info
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to preview file {filename}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@file_browser_bp.route('/delete/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a specific file"""
    try:
        # Security check
        if '..' in filename or filename.startswith('/'):
            return jsonify({"success": False, "error": "Invalid filename"}), 400
        
        # Find and delete file
        deleted = False
        for subdir in ['csv', 'png', 'json']:
            file_path = os.path.join(exporter.export_dir, subdir, filename)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                os.remove(file_path)
                deleted = True
                logger.info(f"✅ Deleted file: {filename}")
                break
        
        if not deleted:
            return jsonify({"success": False, "error": "File not found"}), 404
        
        return jsonify({
            "success": True,
            "message": f"File {filename} deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to delete file {filename}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@file_browser_bp.route('/stats', methods=['GET'])
def get_file_stats():
    """Get file system statistics"""
    try:
        stats = {}
        
        if exporter:
            stats['export'] = exporter.get_export_stats()
        
        if db:
            stats['database'] = db.get_database_stats()
        
        # Disk usage
        if os.path.exists(exporter.export_dir):
            total_size = 0
            file_count = 0
            for root, dirs, files in os.walk(exporter.export_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path):
                        total_size += os.path.getsize(file_path)
                        file_count += 1
            
            stats['disk_usage'] = {
                'total_files': file_count,
                'total_size': total_size,
                'export_directory': exporter.export_dir
            }
        
        return jsonify({
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to get file stats: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@file_browser_bp.route('/measurements', methods=['GET'])
def list_measurements():
    """List measurements from database"""
    try:
        if not db:
            return jsonify({"success": False, "error": "Database not available"}), 500
        
        measurement_type = request.args.get('type')
        limit = int(request.args.get('limit', 50))
        
        measurements = db.list_measurements(measurement_type, limit)
        
        # Add file info for each measurement
        for measurement in measurements:
            measurement['files'] = db.get_exported_files(measurement['id'])
        
        return jsonify({
            "success": True,
            "measurements": measurements
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to list measurements: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@file_browser_bp.route('/measurements/<int:measurement_id>', methods=['GET'])
def get_measurement_details(measurement_id):
    """Get detailed measurement information"""
    try:
        if not db:
            return jsonify({"success": False, "error": "Database not available"}), 500
        
        measurement = db.get_measurement(measurement_id)
        if not measurement:
            return jsonify({"success": False, "error": "Measurement not found"}), 404
        
        # Get data points
        data_points = db.get_measurement_data(measurement_id)
        
        # Get exported files
        files = db.get_exported_files(measurement_id)
        
        return jsonify({
            "success": True,
            "measurement": measurement,
            "data_points": data_points,
            "files": files
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to get measurement {measurement_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@file_browser_bp.route('/measurements/<int:measurement_id>/export', methods=['POST'])
def export_measurement(measurement_id):
    """Export measurement in all formats"""
    try:
        if not db or not exporter:
            return jsonify({"success": False, "error": "Database or exporter not available"}), 500
        
        measurement = db.get_measurement(measurement_id)
        if not measurement:
            return jsonify({"success": False, "error": "Measurement not found"}), 404
        
        data_points = db.get_measurement_data(measurement_id)
        
        # Export in all formats
        exported_files = exporter.export_all_formats(measurement_id, measurement, data_points)
        
        # Register files in database
        registered_files = []
        for file_type, file_path in exported_files.items():
            filename = os.path.basename(file_path)
            file_id = db.register_exported_file(measurement_id, file_type, filename, file_path)
            registered_files.append({
                'id': file_id,
                'type': file_type,
                'filename': filename,
                'path': file_path
            })
        
        return jsonify({
            "success": True,
            "message": f"Exported measurement {measurement_id} in {len(exported_files)} formats",
            "files": registered_files
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to export measurement {measurement_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# Helper function to format file size
def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"