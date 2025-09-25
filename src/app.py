"""
Flask application routes for H74    from routes.production_calibration_api import calibration_bp as production_calibration_bp
    from routes.auth_routes import auth_bp, admin_bp
    from services.user_service import user_service
    from services.feature_service import FeatureService
    from middleware.auth import AuthMiddleware
except ImportError:
    # Fall back to absolute imports (when run directly)
    from config.settings import Configen Web Interface
"""

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import logging
import json
import io
import csv
import time
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the parent directory to the Python path to handle imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    # Try relative imports first (when run as module)
    from .config.settings import Config
    from .hardware import SCPIHandler
    from .services.measurement_service import MeasurementService
    from .services.data_service import DataService
    from .services.cv_measurement_service import CVMeasurementService
    from .services.data_logging_service import DataLoggingService
    from .routes import ai_bp, port_bp
    from .routes.cv_routes import cv_bp
    from .routes.data_logging_routes import data_logging_bp
    from .routes.workflow_routes import workflow_bp
    from .routes.preview_data import preview_bp
    from .routes.workflow_api import workflow_api_bp
    from .routes.peak_detection import peak_detection_bp
    from .routes.peak_analysis import bp as peak_analysis_bp
    from .routes.parameter_api import parameter_bp, parameter_api_bp
    from .routes.calibration_api import calibration_api_bp
    from .routes.production_calibration_api import calibration_bp as production_calibration_bp
except ImportError:
    # Fall back to absolute imports (when run directly)
    from config.settings import Config
    from hardware import SCPIHandler
    from services.measurement_service import MeasurementService
    from services.data_service import DataService
    from services.cv_measurement_service import CVMeasurementService
    from services.data_logging_service import DataLoggingService
    from routes import ai_bp, port_bp
    from routes.cv_routes import cv_bp
    from routes.data_logging_routes import data_logging_bp
    from routes.workflow_routes import workflow_bp
    from routes.preview_data import preview_bp
    from routes.workflow_api import workflow_api_bp
    from routes.peak_detection import peak_detection_bp
    from routes.peak_analysis import bp as peak_analysis_bp
    from routes.parameter_api import parameter_bp, parameter_api_bp
    from routes.calibration_api import calibration_api_bp
    from routes.production_calibration_api import calibration_bp as production_calibration_bp
    from routes.auth_routes import auth_bp, admin_bp
    from services.user_service import user_service
    from services.feature_service import FeatureService
    from middleware.auth import AuthMiddleware

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure Flask application"""
    
    # Set up paths
    current_dir = Path(__file__).parent.resolve()
    project_root = current_dir.parent
    
    template_dir = project_root / 'templates'
    static_dir = project_root / 'static'
    
    # Create directories if they don't exist
    template_dir.mkdir(parents=True, exist_ok=True)
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # Create Flask app with configured folders
    app = Flask(__name__,
                template_folder=str(template_dir),
                static_folder=str(static_dir),
                static_url_path='/static')
    
    # Additional static folder for temp_data
    @app.route('/temp_data/<path:filename>')
    def serve_temp_file(filename):
        temp_dir = os.path.join(project_root, 'temp_data')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        return send_from_directory(temp_dir, filename)
    
    # Additional static folder for sample_data
    @app.route('/sample_data/<path:filename>')
    def serve_sample_file(filename):
        sample_dir = os.path.join(project_root, 'sample_data')
        return send_from_directory(sample_dir, filename)
    
    # Configure file upload limits and security
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
    app.config['UPLOAD_EXTENSIONS'] = ['.csv', '.txt', '.xlsx', '.json']
    app.config['SECRET_KEY'] = 'h743poten-workflow-2025'  # For session management
    
    # Initialize services
    scpi_handler = SCPIHandler()
    measurement_service = MeasurementService(scpi_handler)
    data_service = DataService()
    cv_service = CVMeasurementService(scpi_handler)
    
    # Initialize data logging service with correct path
    data_logs_path = project_root / "data_logs"
    data_logging_service = DataLoggingService(str(data_logs_path))
    
    # Store services in application context
    app.config['scpi_handler'] = scpi_handler
    app.config['measurement_service'] = measurement_service
    app.config['data_service'] = data_service
    app.config['cv_service'] = cv_service
    app.config['data_logging_service'] = data_logging_service
    
    # Initialize user and feature services if available
    try:
        from services.user_service import user_service
        from services.feature_service import FeatureService
        from middleware.auth import AuthMiddleware
        
        app.config['user_service'] = user_service
        feature_service = FeatureService(project_root / 'config', user_service)
        app.config['feature_service'] = feature_service
        
        # Initialize auth middleware
        auth_middleware = AuthMiddleware(app)
    except Exception as e:
        logger.warning(f"Auth services not available: {e}")
        # Create dummy services for fallback
        app.config['user_service'] = None
        app.config['feature_service'] = None
    
    # Register blueprints
    # Register auth blueprints if available
    try:
        from routes.auth_routes import auth_bp, admin_bp
        from routes.feature_api import feature_api_bp
        app.register_blueprint(auth_bp)  # Authentication routes
        app.register_blueprint(admin_bp)  # Admin routes
        app.register_blueprint(feature_api_bp)  # Feature management API
    except Exception as e:
        logger.warning(f"Auth blueprints not available: {e}")
    
    app.register_blueprint(ai_bp)
    app.register_blueprint(port_bp)
    app.register_blueprint(cv_bp)
    app.register_blueprint(data_logging_bp)
    app.register_blueprint(workflow_bp)
    app.register_blueprint(preview_bp)
    app.register_blueprint(workflow_api_bp)
    app.register_blueprint(peak_detection_bp)  # Remove url_prefix to use root URLs
    app.register_blueprint(peak_analysis_bp, url_prefix='/peak_detection')
    app.register_blueprint(parameter_bp)
    app.register_blueprint(parameter_api_bp)
    app.register_blueprint(calibration_api_bp)
    app.register_blueprint(production_calibration_bp)  # Production cross-sample calibration
    
    # Error handlers
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle file too large error"""
        return jsonify({
            'success': False,
            'error': 'File too large. Maximum size is 100MB.',
            'error_code': 413,
            'max_size_mb': 100
        }), 413
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return jsonify({
            'success': False,
            'error': 'Resource not found',
            'error_code': 404
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle internal server errors"""
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 500
        }), 500
    
    @app.route('/debug')
    def debug():
        """Debug endpoint to check application state"""
        app.logger.info("Debug endpoint accessed")
        return jsonify({
            'status': 'ok',
            'template_dir': str(template_dir),
            'static_dir': str(static_dir),
            'blueprints': [str(bp) for bp in app.blueprints.keys()],
            'routes': [str(rule) for rule in app.url_map.iter_rules()],
            'config': {
                'DEBUG': app.debug,
                'TESTING': app.testing
            }
        })
    
    @app.route('/')
    def index():
        """Main dashboard"""
        return render_template('index.html')
        
    @app.route('/measurements')
    def measurements():
        """Measurement interface"""
        return render_template('measurement.html')
    
    @app.route('/data-browser')
    def data_browser():
        """Data browser interface"""
        return render_template('data_browser.html')
        
    @app.route('/peak_detection')
    def peak_detection_view():
        """Peak detection visualization interface"""
        return render_template('peak_detection.html')
    
    @app.route('/calibration')
    def calibration_view():
        """Cross-instrument calibration interface"""
        return render_template('calibration.html')
    
    @app.route('/settings')
    def settings_view():
        """Settings and feature management interface"""
        return render_template('settings.html')
    
    @app.route('/workflow')
    def workflow_view():
        """Analysis workflow interface"""
        return render_template('workflow_visualization.html')
    
    @app.route('/favicon.ico')
    def favicon():
        """Serve favicon"""
        try:
            favicon_path = static_dir / 'img' / 'favicon.ico'
            if not favicon_path.exists():
                # Create img directory if it doesn't exist
                (static_dir / 'img').mkdir(exist_ok=True)
                # Return a default transparent favicon if the file doesn't exist
                return '', 204
            return send_file(
                str(favicon_path),
                mimetype='image/x-icon'
            )
        except Exception as e:
            app.logger.error(f"Error serving favicon: {e}")
            return '', 204
    
    @app.route('/api/connection/status')
    def connection_status():
        """Get connection status"""
        return jsonify({
            'connected': app.config['scpi_handler'].is_connected,
            'port': app.config['scpi_handler'].port,
            'baud_rate': app.config['scpi_handler'].baud_rate
        })
    
    @app.route('/api/connection/connect', methods=['POST'])
    def connect_device():
        """Connect to device"""
        try:
            data = request.get_json()
            port = data.get('port')
            baud_rate = data.get('baud_rate', 115200)  # Default to 115200 if not provided
            
            if not port:
                return jsonify({'success': False, 'error': 'Port is required'}), 400

            app.config['scpi_handler'].port = port
            app.config['scpi_handler'].baud_rate = baud_rate
            success = app.config['scpi_handler'].connect()
            return jsonify({'success': success})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/connection/disconnect', methods=['POST'])
    def disconnect_device():
        """Disconnect from device"""
        try:
            app.config['scpi_handler'].disconnect()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/measurement/modes')
    def get_measurement_modes():
        """Get available measurement modes and their parameters"""
        return jsonify({
            'modes': ['CV', 'CA', 'DPV', 'SWV'],
            'default_params': Config.DEFAULT_PARAMS
        })
    
    @app.route('/api/measurement/setup', methods=['POST'])
    def setup_measurement():
        """Setup measurement parameters"""
        try:
            data = request.get_json()
            mode = data.get('mode')
            params = data.get('params', {})
            
            success = app.config['measurement_service'].setup_measurement(mode, params)
            return jsonify({'success': success})
            
        except Exception as e:
            logger.error(f"Failed to setup measurement: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/measurement/start', methods=['POST'])
    def start_measurement():
        """Start measurement"""
        try:
            success = app.config['measurement_service'].start_measurement()
            return jsonify({'success': success})
        except Exception as e:
            logger.error(f"Failed to start measurement: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/measurement/stop', methods=['POST'])
    def stop_measurement():
        """Stop measurement"""
        try:
            success = app.config['measurement_service'].stop_measurement()
            return jsonify({'success': success})
        except Exception as e:
            logger.error(f"Failed to stop measurement: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/measurement/status')
    def measurement_status():
        """Get measurement status"""
        try:
            status = app.config['measurement_service'].get_status()
            return jsonify(status)
        except Exception as e:
            logger.error(f"Failed to get measurement status: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/data/current')
    def get_current_data():
        """Get current measurement data"""
        try:
            # Get data from measurement service and update data service
            measurement_data = app.config['measurement_service'].get_measurement_data()
            app.config['data_service'].update_measurement_data(measurement_data)
            
            data = app.config['data_service'].get_current_data()
            return jsonify(data)
        except Exception as e:
            logger.error(f"Failed to get current data: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/data/export')
    def export_data():
        """Export measurement data as CSV"""
        try:
            # Get current data
            data = app.config['data_service'].get_current_data()
            
            if not data['points']:
                return jsonify({'error': 'No data to export'}), 400
            
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Timestamp', 'Voltage (V)', 'Current (A)', 'Mode'])
            
            # Write data
            for point in data['points']:
                writer.writerow([
                    point['timestamp'],
                    point['voltage'],
                    point['current'],
                    point['mode']
                ])
            
            # Prepare file download
            output.seek(0)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'measurement_{timestamp}.csv'
            
            return send_file(
                io.BytesIO(output.getvalue().encode()),
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
            
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/device/info')
    def get_device_info():
        """Get device information"""
        try:
            if not app.config['scpi_handler'].is_connected:
                return jsonify({'error': 'Device not connected'}), 400
            
            device_id = app.config['scpi_handler'].query("*IDN?")
            return jsonify({
                'device_id': device_id,
                'connected': True
            })
            
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/uart/send', methods=['POST'])
    def send_uart_command():
        """Send custom SCPI command for UART testing with STM32H743 optimizations"""
        command = ''
        try:
            data = request.get_json()
            command = data.get('command', '').strip()
            
            if not command:
                return jsonify({'error': 'Command is required'}), 400
            
            if not app.config['scpi_handler'].is_connected:
                return jsonify({'error': 'Device not connected'}), 400
            
            # Add rate limiting to prevent rapid commands with exceptions for long commands
            long_running_commands = [
                'poten:dpv:start',
                'poten:swv:start', 
                'poten:cv:start',
                'poten:ca:start'
            ]
            
            # Check if this is a long-running command
            is_long_command = any(cmd in command.lower() for cmd in long_running_commands)
            
            # Rate limiting logic using app.config
            rate_limit_time = 2.0 if is_long_command else 0.5  # 2s for long commands, 0.5s for others
            
            # Skip rate limiting for consecutive identical long commands (auto-retry)
            last_command_time = app.config.get('_last_uart_command_time')
            last_command = app.config.get('_last_uart_command')
            
            if last_command_time and last_command:
                time_since_last = time.time() - last_command_time
                same_command = (last_command == command)
                
                # Only apply rate limiting if it's not the same long command being retried
                if time_since_last < rate_limit_time and not (is_long_command and same_command):
                    return jsonify({
                        'success': False,
                        'command': command,
                        'response': None,
                        'error': f'Rate limited. Wait {rate_limit_time - time_since_last:.1f}s',
                        'timestamp': time.time()
                    }), 429
            
            app.config['_last_uart_command_time'] = time.time()
            app.config['_last_uart_command'] = command
            
            # Log the command attempt
            logger.info(f"Web UART command: {command}")
            
            # Send command using the SCPI handler
            result = app.config['scpi_handler'].send_custom_command(command)
            
            # Log the result
            if result['success']:
                logger.info(f"Web UART success: {result['response']}")
            else:
                logger.warning(f"Web UART failed: {result['error']}")
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Failed to send UART command: {e}")
            return jsonify({
                'success': False,
                'command': command,
                'response': None,
                'error': str(e),
                'timestamp': time.time()
            }), 500
    
    @app.route('/api/emulation/csv/load', methods=['POST'])
    def load_csv_emulation():
        """Load CSV file for emulation"""
        try:
            data = request.get_json()
            file_path = data.get('file_path')
            
            if not file_path:
                return jsonify({'success': False, 'error': 'File path is required'}), 400
            
            # Check if we're using mock handler
            if hasattr(app.config['scpi_handler'], 'load_csv_data'):
                success = app.config['scpi_handler'].load_csv_data(file_path)
                if success:
                    info = app.config['scpi_handler'].get_csv_info()
                    return jsonify({
                        'success': True,
                        'message': f'Loaded {info["total_points"]} data points',
                        'info': info
                    })
                else:
                    return jsonify({'success': False, 'error': 'Failed to load CSV file'}), 400
            else:
                return jsonify({'success': False, 'error': 'CSV emulation not supported by current handler'}), 400
                
        except Exception as e:
            logger.error(f"Failed to load CSV emulation: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/emulation/csv/start', methods=['POST'])
    def start_csv_emulation():
        """Start CSV data emulation"""
        try:
            data = request.get_json() or {}
            speed = data.get('speed', 1.0)
            loop = data.get('loop', False)
            
            # Check if we're using mock handler
            if hasattr(app.config['scpi_handler'], 'start_csv_emulation'):
                success = app.config['scpi_handler'].start_csv_emulation(speed, loop)
                return jsonify({
                    'success': success,
                    'message': f'CSV emulation {"started" if success else "failed to start"}'
                })
            else:
                return jsonify({'success': False, 'error': 'CSV emulation not supported by current handler'}), 400
                
        except Exception as e:
            logger.error(f"Failed to start CSV emulation: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/emulation/csv/stop', methods=['POST'])
    def stop_csv_emulation():
        """Stop CSV data emulation"""
        try:
            # Check if we're using mock handler
            if hasattr(app.config['scpi_handler'], 'stop_csv_emulation'):
                app.config['scpi_handler'].stop_csv_emulation()
                return jsonify({'success': True, 'message': 'CSV emulation stopped'})
            else:
                return jsonify({'success': False, 'error': 'CSV emulation not supported by current handler'}), 400
                
        except Exception as e:
            logger.error(f"Failed to stop CSV emulation: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/emulation/csv/status')
    def get_csv_emulation_status():
        """Get CSV emulation status and progress"""
        try:
            # Check if we're using mock handler
            if hasattr(app.config['scpi_handler'], 'get_csv_progress'):
                progress = app.config['scpi_handler'].get_csv_progress()
                info = app.config['scpi_handler'].get_csv_info()
                
                return jsonify({
                    'loaded': info.get('loaded', False),
                    'progress': progress,
                    'info': info
                })
            else:
                return jsonify({
                    'loaded': False,
                    'error': 'CSV emulation not supported by current handler'
                })
                
        except Exception as e:
            logger.error(f"Failed to get CSV emulation status: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/emulation/csv/seek', methods=['POST'])
    def seek_csv_emulation():
        """Seek to specific time in CSV data"""
        try:
            data = request.get_json()
            target_time = data.get('time')
            
            if target_time is None:
                return jsonify({'success': False, 'error': 'Time parameter is required'}), 400
            
            # Use SCPI command for seeking
            command = f"csv:seek {target_time}"
            result = app.config['scpi_handler'].send_custom_command(command)
            
            return jsonify({
                'success': result['success'],
                'message': f'Seeked to {target_time}s' if result['success'] else result['error']
            })
                
        except Exception as e:
            logger.error(f"Failed to seek CSV emulation: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # Settings API routes
    @app.route('/api/settings/features')
    def get_feature_settings():
        """Get current feature settings"""
        try:
            # Get features from config or default settings
            default_features = {
                'measurements': {
                    'enabled': True,
                    'label': 'Measurements',
                    'description': 'Basic electrochemical measurement functionality',
                    'category': 'core'
                },
                'analysis_workflow': {
                    'enabled': True,
                    'label': 'Analysis Workflow',
                    'description': 'Advanced data analysis and visualization tools',
                    'category': 'analysis'
                },
                'ai_dashboard': {
                    'enabled': False,
                    'label': 'AI Dashboard',
                    'description': 'Machine learning-powered analysis tools',
                    'category': 'ai'
                },
                'calibration': {
                    'enabled': True,
                    'label': 'Calibration',
                    'description': 'Cross-instrument calibration and validation',
                    'category': 'calibration'
                },
                'peak_detection': {
                    'enabled': True,
                    'label': 'Peak Detection',
                    'description': 'Automated peak detection and analysis',
                    'category': 'analysis'
                },
                'data_logging': {
                    'enabled': True,
                    'label': 'Data Logging',
                    'description': 'Automated data logging and storage',
                    'category': 'core'
                },
                'csv_emulation': {
                    'enabled': True,
                    'label': 'CSV Emulation',
                    'description': 'CSV data emulation for testing',
                    'category': 'development'
                },
                'hardware_diagnostics': {
                    'enabled': False,
                    'label': 'Hardware Diagnostics',
                    'description': 'Advanced hardware testing and diagnostics',
                    'category': 'development'
                }
            }
            
            # Load from config file if it exists
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'features.json')
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        stored_features = json.load(f)
                    # Merge with defaults (add new features, keep existing settings)
                    for key, value in stored_features.items():
                        if key in default_features:
                            default_features[key]['enabled'] = value.get('enabled', default_features[key]['enabled'])
                except Exception as e:
                    logger.warning(f"Failed to load feature settings: {e}")
            
            return jsonify({
                'success': True,
                'features': default_features
            })
            
        except Exception as e:
            logger.error(f"Failed to get feature settings: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/settings/features', methods=['POST'])
    def update_feature_settings():
        """Update feature settings"""
        try:
            data = request.get_json()
            features = data.get('features', {})
            
            # Ensure config directory exists
            config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
            os.makedirs(config_dir, exist_ok=True)
            
            # Save to config file
            config_path = os.path.join(config_dir, 'features.json')
            with open(config_path, 'w') as f:
                json.dump(features, f, indent=2)
            
            logger.info(f"Updated feature settings: {features}")
            
            return jsonify({
                'success': True,
                'message': 'Feature settings updated successfully'
            })
            
        except Exception as e:
            logger.error(f"Failed to update feature settings: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/settings/system')
    def get_system_settings():
        """Get system configuration"""
        try:
            return jsonify({
                'success': True,
                'system': {
                    'version': '1.0.0-rpi5',
                    'platform': 'Raspberry Pi 5',
                    'python_version': sys.version,
                    'flask_debug': app.debug,
                    'upload_max_size': app.config.get('MAX_CONTENT_LENGTH', 0) // (1024 * 1024),  # MB
                    'data_path': str(Path(__file__).parent.parent / 'data_logs'),
                    'temp_path': str(Path(__file__).parent.parent / 'temp_data')
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to get system settings: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return app

if __name__ == "__main__":
    """Allow direct execution of app.py for development"""
    
    # Configure logging
    import os
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/h743poten_dev.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting H743Poten Web Interface in development mode")
    
    # Create and run the app
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
