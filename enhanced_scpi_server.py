#!/usr/bin/env python3
"""
Enhanced SCPI Server with STM32 H743 Streaming Support
Supports new firmware with clean SCPI responses and CV streaming
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import serial
import time
import json
import logging
import threading
import os
import sys
from datetime import datetime

# Import our modules
try:
    from database import MeasurementDatabase
    from file_exporter import FileExporter
    from file_browser import file_browser_bp
    DB_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Database/Export modules not available: {e}")
    DB_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedSCPIServer:
    """Enhanced SCPI Server supporting STM32 H743 streaming commands"""
    
    def __init__(self, port='/dev/ttyACM1', baud_rate=115200):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.is_connected = False
        
        # Streaming state management
        self.streaming_active = False
        self.streaming_type = None  # 'cv', 'dpv', 'swv'
        self.streaming_progress = 0
        self.streaming_data = []
        self.current_measurement_id = None
        
        # Database and file export
        self.database = None
        self.file_exporter = None
        self.setup_database()
        
        logger.info("🔬 Enhanced SCPI Server initialized")
    
    def setup_database(self):
        """Initialize database and file exporter"""
        if DB_AVAILABLE:
            try:
                self.database = MeasurementDatabase()
                self.file_exporter = FileExporter()
                logger.info("✅ Database and file exporter ready")
            except Exception as e:
                logger.error(f"❌ Database setup failed: {e}")
    
    def connect(self):
        """Connect to STM32 H743"""
        try:
            # Try multiple possible ports
            possible_ports = [self.port, '/dev/ttyACM0', '/dev/ttyUSB0', '/dev/ttyUSB1']
            
            for port in possible_ports:
                if os.path.exists(port):
                    try:
                        self.serial_conn = serial.Serial(
                            port=port,
                            baudrate=self.baud_rate,
                            timeout=1.0,
                            write_timeout=1.0
                        )
                        self.port = port
                        break
                    except Exception as e:
                        logger.debug(f"Failed to connect to {port}: {e}")
                        continue
            
            if not self.serial_conn:
                raise Exception("No STM32 device found on any port")
            
            # Test connection with IDN query
            time.sleep(2)  # Allow device to initialize
            self.serial_conn.flush()
            
            test_response = self.send_scpi_command("*IDN?")
            if test_response and "MANUFACTURE" in test_response:
                self.is_connected = True
                logger.info(f"✅ Connected to STM32 H743 on {self.port}")
                logger.info(f"📋 Device: {test_response}")
                return {"success": True, "message": f"Connected to {self.port}", "device_info": test_response}
            else:
                raise Exception(f"Invalid device response: {test_response}")
                
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            self.is_connected = False
            if self.serial_conn:
                self.serial_conn.close()
                self.serial_conn = None
            return {"success": False, "message": str(e)}
    
    def disconnect(self):
        """Disconnect from STM32"""
        try:
            if self.serial_conn:
                self.serial_conn.close()
            self.is_connected = False
            self.serial_conn = None
            self.streaming_active = False
            logger.info("🔌 Disconnected from STM32")
            return {"success": True, "message": "Disconnected"}
        except Exception as e:
            logger.error(f"❌ Disconnect error: {e}")
            return {"success": False, "message": str(e)}
    
    def send_scpi_command(self, command):
        """Send SCPI command and get clean response (production mode)"""
        if not self.is_connected or not self.serial_conn:
            return None
        
        try:
            # Add SCPI termination
            if not command.endswith('\r\n'):
                command = command.strip() + '\r\n'
            
            logger.debug(f"📤 Sending: {command.strip()}")
            self.serial_conn.write(command.encode())
            
            # Read response for query commands
            if '?' in command:
                # Production firmware should give clean responses
                try:
                    # Use readline with proper timeout like direct test
                    self.serial_conn.timeout = 3.0  # Match direct test timeout
                    line_bytes = self.serial_conn.readline()
                    
                    if line_bytes:
                        response = line_bytes.decode('utf-8', errors='ignore').strip()
                    else:
                        response = ""
                        
                except Exception as e:
                    logger.debug(f"Read error: {e}")
                    response = ""
                
                logger.debug(f"📥 Received: {response}")
                return response
            else:
                # For non-query commands, read OK/ERROR response
                time.sleep(0.1)
                response_bytes = self.serial_conn.readline()
                if response_bytes:
                    response = response_bytes.decode('utf-8', errors='ignore').strip()
                    logger.debug(f"📥 Command response: {response}")
                    return response
                return "OK"  # Assume success if no explicit response
                
        except Exception as e:
            logger.error(f"❌ SCPI command error: {e}")
            return None
    
    # ===== NEW STREAMING COMMANDS =====
    
    def start_cv_streaming(self, parameters, notes=""):
        """Start CV measurement with new streaming protocol"""
        try:
            # Extract parameters
            start_v = parameters.get('start_voltage', -0.5)
            end_v = parameters.get('end_voltage', 0.5)
            begin_v = parameters.get('begin_voltage', start_v)  
            scan_rate = parameters.get('scan_rate', 0.05)
            cycles = parameters.get('cycles', 1)
            
            logger.info(f"🚀 Starting CV Streaming: {start_v}V to {end_v}V, rate: {scan_rate}V/s, cycles: {cycles}")
            
            # Create measurement record first
            measurement_id = None
            if self.database:
                measurement_id = self.database.create_measurement(
                    measurement_type='cv',
                    parameters=parameters,
                    notes=notes
                )
                self.current_measurement_id = measurement_id
                logger.info(f"📝 Created measurement record: {measurement_id}")
            
            # Use new streaming command: POTEn:CV:Stream:START LowerV,UpperV,BeginV,SweepRate,Cycles
            stream_cmd = f"POTEn:CV:Stream:START {start_v},{end_v},{begin_v},{scan_rate},{cycles}"
            response = self.send_scpi_command(stream_cmd)
            
            if not response or response.strip() != "OK":
                raise Exception(f"CV streaming start failed: {response}")
            
            # Set streaming state
            self.streaming_active = True
            self.streaming_type = 'cv'
            self.streaming_progress = 0
            self.streaming_data = []
            
            logger.info("✅ CV streaming started successfully")
            return {
                "success": True,
                "measurement_id": measurement_id,
                "message": "CV streaming started"
            }
            
        except Exception as e:
            logger.error(f"❌ CV streaming start failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_streaming_status(self):
        """Get streaming status and progress"""
        if not self.streaming_active:
            return {"state": "IDLE", "progress": 0}
        
        try:
            # Query streaming status: POTEn:CV:Stream:STATUS?
            status_response = self.send_scpi_command("POTEn:CV:Stream:STATUS?")
            
            if status_response:
                # Parse response: "MEASURING 75" or "COMPLETE 100"
                parts = status_response.split()
                if len(parts) >= 2:
                    state = parts[0]
                    progress = int(parts[1])
                    self.streaming_progress = progress
                    
                    if state == "COMPLETE":
                        self.streaming_active = False
                    
                    return {"state": state, "progress": progress}
            
            # Fallback
            return {"state": "MEASURING", "progress": self.streaming_progress}
            
        except Exception as e:
            logger.error(f"❌ Status query failed: {e}")
            return {"state": "ERROR", "progress": 0}
    
    def get_streaming_data(self):
        """Get complete streaming data"""
        try:
            # Query complete data: POTEn:CV:Stream:DATA?
            data_response = self.send_scpi_command("POTEn:CV:Stream:DATA?")
            
            if not data_response:
                return {"success": False, "error": "No data received"}
            
            # Parse CSV data
            lines = data_response.split('\n')
            data_points = []
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('voltage,current'):
                    continue
                
                try:
                    parts = line.split(',')
                    if len(parts) >= 2:
                        voltage = float(parts[0])
                        current = float(parts[1])
                        data_points.append({
                            'voltage': voltage,
                            'current': current,
                            'timestamp': time.time()
                        })
                except ValueError:
                    continue
            
            self.streaming_data = data_points
            
            # Store in database
            if self.database and self.current_measurement_id and data_points:
                try:
                    self.database.store_data_points(self.current_measurement_id, data_points)
                    self.database.update_measurement_status(self.current_measurement_id, 'COMPLETE')
                    logger.info(f"📊 Stored {len(data_points)} data points")
                    
                    # Auto-export files
                    if self.file_exporter:
                        export_result = self.file_exporter.export_all_formats(
                            self.current_measurement_id, 
                            'cv', 
                            data_points
                        )
                        logger.info(f"📁 Auto-exported files: {export_result}")
                        
                except Exception as e:
                    logger.error(f"Database/export error: {e}")
            
            return {
                "success": True,
                "data": data_points,
                "count": len(data_points),
                "measurement_id": self.current_measurement_id
            }
            
        except Exception as e:
            logger.error(f"❌ Data retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    def stop_streaming(self):
        """Stop current streaming measurement"""
        try:
            # Send stop command: POTEn:CV:Stream:STOP
            response = self.send_scpi_command("POTEn:CV:Stream:STOP")
            
            self.streaming_active = False
            self.streaming_type = None
            self.streaming_progress = 0
            
            # Update database if needed
            if self.database and self.current_measurement_id:
                self.database.update_measurement_status(self.current_measurement_id, 'STOPPED')
            
            logger.info("⏹️ Streaming stopped")
            return {"success": True, "message": "Streaming stopped"}
            
        except Exception as e:
            logger.error(f"❌ Stop streaming failed: {e}")
            return {"success": False, "error": str(e)}

# Flask App Setup
app = Flask(__name__)
CORS(app)

# Initialize SCPI server
scpi_server = EnhancedSCPIServer()

# Database setup
db = None
if DB_AVAILABLE:
    try:
        db = MeasurementDatabase()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

# Register file browser blueprint
if DB_AVAILABLE:
    app.register_blueprint(file_browser_bp, url_prefix='/files')

# ===== FLASK ROUTES =====

@app.route('/')
def index():
    return jsonify({
        "name": "Enhanced H743 SCPI Server",
        "version": "2.0",
        "features": ["streaming_commands", "clean_scpi", "database_integration"],
        "status": "ready"
    })

@app.route('/connect', methods=['POST'])
def connect():
    result = scpi_server.connect()
    return jsonify(result)

@app.route('/disconnect', methods=['POST'])  
def disconnect():
    result = scpi_server.disconnect()
    return jsonify(result)

@app.route('/system/status')
def system_status():
    """Get system status"""
    status = {
        "scpi_server": {
            "running": True,
            "device_connected": scpi_server.is_connected,
            "port": scpi_server.port,
            "streaming_active": scpi_server.streaming_active,
            "streaming_type": scpi_server.streaming_type,
            "streaming_progress": scpi_server.streaming_progress
        }
    }
    
    # Add database stats
    if db:
        try:
            stats = db.get_statistics()
            status["database"] = {"available": True, "stats": stats}
        except Exception as e:
            status["database"] = {"available": False, "error": str(e)}
    else:
        status["database"] = {"available": False}
    
    return jsonify({"success": True, "status": status})

# ===== NEW STREAMING ENDPOINTS =====

@app.route('/cv/stream/start', methods=['POST'])
def cv_stream_start():
    """Start CV streaming measurement"""
    if not scpi_server.is_connected:
        return jsonify({"success": False, "error": "Device not connected"})
    
    data = request.get_json() or {}
    parameters = data.get('parameters', {
        'start_voltage': -0.5,
        'end_voltage': 0.5,
        'begin_voltage': -0.5,
        'scan_rate': 0.05,
        'cycles': 1
    })
    notes = data.get('notes', 'CV streaming measurement')
    
    result = scpi_server.start_cv_streaming(parameters, notes)
    return jsonify(result)

@app.route('/cv/stream/status')
def cv_stream_status():
    """Get CV streaming status"""
    status = scpi_server.get_streaming_status()
    return jsonify({"success": True, "status": status})

@app.route('/cv/stream/data')
def cv_stream_data():
    """Get complete CV streaming data"""
    result = scpi_server.get_streaming_data()
    return jsonify(result)

@app.route('/cv/stream/stop', methods=['POST'])
def cv_stream_stop():
    """Stop CV streaming"""
    result = scpi_server.stop_streaming()
    return jsonify(result)

# ===== MEASUREMENT EXPORT =====

@app.route('/measurements/export/<int:measurement_id>', methods=['POST'])
def export_measurement(measurement_id):
    """Export measurement to files"""
    if not db:
        return jsonify({"success": False, "error": "Database not available"})
    
    try:
        # Get measurement data
        measurement = db.get_measurement(measurement_id)
        if not measurement:
            return jsonify({"success": False, "error": "Measurement not found"})
        
        data_points = db.get_measurement_data(measurement_id)
        if not data_points:
            return jsonify({"success": False, "error": "No data points found"})
        
        # Export files
        file_exporter = FileExporter()
        files = file_exporter.export_all_formats(
            measurement_id,
            measurement['type'],
            data_points,
            measurement
        )
        
        logger.info(f"📁 Exported {len(files)} files for measurement {measurement_id}")
        return jsonify({"success": True, "files": files})
    
    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({"success": False, "error": str(e)})

# ===== LEGACY SUPPORT (for compatibility) =====

@app.route('/cv/start', methods=['POST'])
def cv_start_legacy():
    """Legacy CV start endpoint - redirects to streaming"""
    logger.info("🔄 Legacy CV start - redirecting to streaming")
    return cv_stream_start()

@app.route('/cv/data')
def cv_data_legacy():
    """Legacy CV data endpoint"""
    if scpi_server.streaming_data:
        return jsonify({
            "success": True,
            "data": scpi_server.streaming_data,
            "count": len(scpi_server.streaming_data)
        })
    else:
        return jsonify({"success": True, "data": [], "count": 0})

@app.route('/cv/stop', methods=['POST'])
def cv_stop_legacy():
    """Legacy CV stop endpoint"""
    return cv_stream_stop()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced H743 SCPI Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8081, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--device', default='/dev/ttyACM1', help='Serial device path')
    
    args = parser.parse_args()
    
    # Update device path
    scpi_server.port = args.device
    
    logger.info(f"🚀 Starting Enhanced SCPI Server on http://{args.host}:{args.port}")
    logger.info(f"🔌 STM32 device: {args.device}")
    logger.info("🔬 Features: Streaming Commands, Clean SCPI, Database Integration")
    
    # Auto-connect on startup
    logger.info("🔗 Attempting auto-connect to STM32...")
    result = scpi_server.connect()
    if result.get("success"):
        logger.info("✅ Auto-connect successful")
    else:
        logger.warning(f"⚠️ Auto-connect failed: {result.get('message')}")
    
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()