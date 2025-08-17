"""
Flask application factory and routes for H743Poten Web Interface
"""

from flask import Flask, send_from_directory
import os

def create_app():
    """Create and configure Flask application"""
    
    app = Flask(__name__)
    
    # Configure static folders
    app.static_folder = 'static'
    app.static_url_path = '/static'
    
    # Additional static folder for temp_data
    @app.route('/temp_data/<path:filename>')
    def serve_temp_file(filename):
        temp_dir = os.path.join(app.root_path, '..', 'temp_data')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        return send_from_directory(temp_dir, filename)
    
    return app