#!/usr/bin/env python3
"""
H743 Potentiostat Research Platform - Offline Version
Serves the research platform with offline capabilities
"""

from flask import Flask, render_template_string, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import sys
import logging
import json
from datetime import datetime
import sqlite3

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OfflineResearchPlatform:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        self.app.secret_key = 'h743-research-platform-2025'
        
        # Paths
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.exports_dir = os.path.join(self.base_dir, 'exports')
        self.database_path = os.path.join(self.base_dir, 'measurements.db')
        
        # Create directories
        os.makedirs(self.exports_dir, exist_ok=True)
        
        self.setup_routes()
        logger.info("🔬 H743 Research Platform (Offline Mode) initialized")

    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Serve the main research platform page"""
            try:
                html_path = os.path.join(self.base_dir, 'research_platform_v2.html')
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Modify for offline mode
                html_content = html_content.replace(
                    "const SCPI_SERVER_URL = 'http://192.168.9.76:8081';",
                    "const SCPI_SERVER_URL = ''; // Offline mode"
                )
                
                return html_content
            except Exception as e:
                logger.error(f"Error serving index: {e}")
                return f"<h1>Error: {e}</h1>", 500

        @self.app.route('/api/status')
        def system_status():
            """Return system status for offline mode"""
            return jsonify({
                "success": True,
                "mode": "offline",
                "status": {
                    "scpi_server": {
                        "running": False,
                        "device_connected": False,
                        "message": "Offline mode - no hardware connection"
                    },
                    "database": self.get_database_stats(),
                    "exports": self.get_export_stats()
                },
                "timestamp": datetime.now().isoformat()
            })

        @self.app.route('/api/files/list')
        def list_files():
            """List exported files"""
            try:
                files = []
                for root, dirs, file_list in os.walk(self.exports_dir):
                    for file in file_list:
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, self.exports_dir)
                        
                        stat = os.stat(file_path)
                        files.append({
                            "name": file,
                            "path": relative_path,
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "type": file.split('.')[-1].lower() if '.' in file else 'unknown'
                        })
                
                return jsonify({
                    "success": True,
                    "files": sorted(files, key=lambda x: x['modified'], reverse=True),
                    "total": len(files)
                })
            except Exception as e:
                logger.error(f"Error listing files: {e}")
                return jsonify({"success": False, "error": str(e)})

        @self.app.route('/api/files/download/<path:filename>')
        def download_file(filename):
            """Download exported file"""
            try:
                return send_from_directory(self.exports_dir, filename, as_attachment=True)
            except Exception as e:
                logger.error(f"Error downloading file {filename}: {e}")
                return jsonify({"success": False, "error": str(e)}), 404

        @self.app.route('/api/measurements/mock', methods=['POST'])
        def create_mock_measurement():
            """Create mock measurement data for testing offline"""
            try:
                data = request.get_json()
                measurement_type = data.get('type', 'cv')
                
                # Generate mock data
                mock_data = self.generate_mock_data(measurement_type, data.get('parameters', {}))
                
                # Save to exports
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"mock_{measurement_type}_{timestamp}"
                
                # Save CSV
                csv_path = os.path.join(self.exports_dir, f"{filename}.csv")
                with open(csv_path, 'w') as f:
                    f.write("voltage,current\n")
                    for point in mock_data:
                        f.write(f"{point['voltage']:.6f},{point['current']:.6e}\n")
                
                # Save JSON
                json_path = os.path.join(self.exports_dir, f"{filename}_metadata.json")
                metadata = {
                    "measurement_type": measurement_type,
                    "parameters": data.get('parameters', {}),
                    "timestamp": datetime.now().isoformat(),
                    "data_points": len(mock_data),
                    "mode": "offline_mock"
                }
                with open(json_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"✅ Created mock {measurement_type} measurement: {filename}")
                
                return jsonify({
                    "success": True,
                    "measurement_id": f"mock_{timestamp}",
                    "files": [
                        {"filename": f"{filename}.csv", "type": "csv"},
                        {"filename": f"{filename}_metadata.json", "type": "json"}
                    ],
                    "data": mock_data
                })
                
            except Exception as e:
                logger.error(f"Error creating mock measurement: {e}")
                return jsonify({"success": False, "error": str(e)})

        @self.app.route('/files')
        def file_browser():
            """Simple file browser interface"""
            try:
                files_response = list_files()
                files_data = json.loads(files_response.data)
                
                if not files_data.get('success'):
                    return "<h1>Error loading files</h1>", 500
                
                html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>H743 File Browser</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                </head>
                <body>
                    <div class="container mt-4">
                        <h2><i class="fas fa-folder"></i> H743 Research Files</h2>
                        <p class="text-muted">Exported measurement data and analysis files</p>
                        
                        <div class="row">
                """
                
                for file in files_data['files']:
                    size_mb = file['size'] / (1024 * 1024)
                    icon = 'file-csv' if file['type'] == 'csv' else 'file-image' if file['type'] == 'png' else 'file-code'
                    
                    html += f"""
                        <div class="col-md-4 mb-3">
                            <div class="card">
                                <div class="card-body">
                                    <h6><i class="fas fa-{icon}"></i> {file['name']}</h6>
                                    <p class="text-muted small">
                                        Size: {size_mb:.2f} MB<br>
                                        Modified: {file['modified'][:16]}
                                    </p>
                                    <a href="/api/files/download/{file['path']}" class="btn btn-primary btn-sm">
                                        <i class="fas fa-download"></i> Download
                                    </a>
                                </div>
                            </div>
                        </div>
                    """
                
                html += """
                        </div>
                    </div>
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/js/all.min.js"></script>
                </body>
                </html>
                """
                
                return html
                
            except Exception as e:
                logger.error(f"Error in file browser: {e}")
                return f"<h1>Error: {e}</h1>", 500

    def generate_mock_data(self, measurement_type, parameters):
        """Generate mock electrochemical data"""
        import math
        
        start_v = parameters.get('start_voltage', -0.5)
        end_v = parameters.get('end_voltage', 0.5)
        points = 100
        
        data = []
        for i in range(points):
            voltage = start_v + (end_v - start_v) * i / points
            
            if measurement_type == 'cv':
                # Mock CV: sigmoidal response with some noise
                current = 1e-6 * (1 / (1 + math.exp(-10 * voltage)) - 0.5)
                current += 1e-7 * math.sin(voltage * 50) * (1 + 0.1 * (i/points))
            
            elif measurement_type == 'swv':
                # Mock SWV: peaks at specific potentials
                current = 1e-6 * math.exp(-((voltage - 0.1)**2) / 0.01)
                current += 5e-7 * math.exp(-((voltage + 0.2)**2) / 0.02)
            
            else:  # dpv
                # Mock DPV: sharp peaks
                current = 2e-6 * math.exp(-((voltage - 0.0)**2) / 0.005)
                current += 1e-6 * math.exp(-((voltage - 0.3)**2) / 0.008)
            
            # Add realistic noise
            import random
            noise = random.gauss(0, current * 0.05) if current != 0 else random.gauss(0, 1e-8)
            current += noise
            
            data.append({
                'voltage': round(voltage, 6),
                'current': current
            })
        
        return data

    def get_database_stats(self):
        """Get database statistics"""
        try:
            if not os.path.exists(self.database_path):
                return {"stats": {"total_measurements": 0, "total_data_points": 0, "total_exported_files": 0}}
            
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Count measurements
            cursor.execute("SELECT COUNT(*) FROM measurements")
            total_measurements = cursor.fetchone()[0]
            
            # Count data points
            cursor.execute("SELECT COUNT(*) FROM data_points")
            total_data_points = cursor.fetchone()[0]
            
            # Count exported files
            cursor.execute("SELECT COUNT(*) FROM exported_files")
            total_exported_files = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "stats": {
                    "total_measurements": total_measurements,
                    "total_data_points": total_data_points,
                    "total_exported_files": total_exported_files
                }
            }
        except Exception as e:
            logger.error(f"Database stats error: {e}")
            return {"stats": {"total_measurements": 0, "total_data_points": 0, "total_exported_files": 0}}

    def get_export_stats(self):
        """Get export directory statistics"""
        try:
            total_size = 0
            file_count = 0
            
            for root, dirs, files in os.walk(self.exports_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
                    file_count += 1
            
            return {
                "total_files": file_count,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "directory": self.exports_dir
            }
        except Exception as e:
            logger.error(f"Export stats error: {e}")
            return {"total_files": 0, "total_size_mb": 0}

    def run(self, host='0.0.0.0', port=8080, debug=False):
        """Run the Flask application"""
        logger.info(f"🚀 Starting H743 Research Platform on http://{host}:{port}")
        logger.info(f"📁 Exports directory: {self.exports_dir}")
        logger.info("🔬 Offline mode: Use mock measurements for testing")
        
        self.app.run(host=host, port=port, debug=debug)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='H743 Potentiostat Research Platform - Offline Mode')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create and run the platform
    platform = OfflineResearchPlatform()
    platform.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()