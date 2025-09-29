#!/usr/bin/env python3
"""
Fixed Enhanced SCPI Server - Based on Working Direct Test
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

class FixedSCPIServer:
    """Fixed SCPI Server using the same logic as working direct test"""
    
    def __init__(self, port='/dev/ttyACM0', baud_rate=115200):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.is_connected = False
        
        # Streaming state management
        self.streaming_active = False
        self.streaming_type = None
        self.streaming_progress = 0
        self.streaming_data = []
        self.current_measurement_id = None
        
        # Database and file export
        self.database = None
        self.file_exporter = None
        self.setup_database()
        
        logger.info("🔬 Fixed SCPI Server initialized")
    
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
        """Connect to STM32 H743 using WORKING direct test method"""
        try:
            # Try multiple possible ports
            possible_ports = [self.port, '/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0']
            
            for port in possible_ports:
                if os.path.exists(port):
                    try:
                        logger.info(f"🔌 Trying to connect to {port}...")
                        
                        # USE EXACT SAME PARAMETERS AS WORKING DIRECT TEST
                        self.serial_conn = serial.Serial(
                            port=port,
                            baudrate=self.baud_rate,
                            timeout=3,  # SAME AS WORKING TEST
                            write_timeout=1.0
                        )
                        
                        self.port = port
                        logger.info(f"✅ Serial port opened: {port}")
                        break
                        
                    except Exception as e:
                        logger.debug(f"Failed to open {port}: {e}")
                        continue
            
            if not self.serial_conn:
                raise Exception("No STM32 device found on any port")
            
            # EXACT SAME CONNECTION TEST AS WORKING DIRECT TEST
            logger.info("⏳ Waiting for device initialization...")
            time.sleep(2)  # SAME AS WORKING TEST
            
            logger.info("📤 Testing connection with *IDN?...")
            self.serial_conn.write(b'*IDN?\r\n')
            time.sleep(2)  # SAME AS WORKING TEST
            
            # READ RESPONSE EXACTLY LIKE WORKING TEST
            logger.info("📥 Reading response...")
            response = self.serial_conn.read(1000)  # SAME AS WORKING TEST
            
            if response:
                device_info = response.decode('utf-8', errors='ignore').strip()
                logger.info(f"Raw response: {response}")
                logger.info(f"Decoded response: {device_info}")
                
                if "MANUFACTURE" in device_info:
                    self.is_connected = True
                    logger.info(f"✅ Connected to STM32 H743 on {self.port}")
                    logger.info(f"📋 Device: {device_info}")
                    return {
                        "success": True, 
                        "message": f"Connected to {self.port}", 
                        "device_info": device_info
                    }
                else:
                    raise Exception(f"Invalid device response: {device_info}")
            else:
                raise Exception("No response from device")
                
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
        """Send SCPI command using WORKING direct test method"""
        if not self.is_connected or not self.serial_conn:
            return None
        
        try:
            logger.debug(f"📤 Sending: {command.strip()}")
            
            # ADD TERMINATION SAME AS WORKING TEST
            if not command.endswith('\r\n'):
                command = command.strip() + '\r\n'
            
            # SEND COMMAND
            self.serial_conn.write(command.encode())
            
            # FOR QUERIES - READ RESPONSE EXACTLY LIKE WORKING TEST
            if '?' in command:
                logger.debug("📥 Reading query response...")
                time.sleep(1)  # SAME DELAY AS WORKING TEST
                response = self.serial_conn.read(1000)  # SAME SIZE AS WORKING TEST
                
                if response:
                    decoded = response.decode('utf-8', errors='ignore').strip()
                    logger.debug(f"📥 Received: {decoded}")
                    return decoded
                else:
                    logger.debug("📥 No response received")
                    return ""
            else:
                # FOR NON-QUERIES - BRIEF DELAY THEN READ ANY RESPONSE
                time.sleep(0.5)
                response = self.serial_conn.read(100)  # READ ANY RESPONSE
                if response:
                    decoded = response.decode('utf-8', errors='ignore').strip()
                    logger.debug(f"📥 Command response: {decoded}")
                    return decoded
                return "OK"  # ASSUME SUCCESS
                
        except Exception as e:
            logger.error(f"❌ SCPI command error: {e}")
            return None
    
    # ===== STREAMING COMMANDS USING FIXED SERIAL METHOD =====
    
    def start_cv_streaming(self, parameters, notes=""):
        """Start CV measurement with fixed streaming protocol"""
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
            
            # Use new streaming command
            stream_cmd = f"POTEn:CV:Stream:START {start_v},{end_v},{begin_v},{scan_rate},{cycles}"
            response = self.send_scpi_command(stream_cmd)
            logger.info(f"🔄 Stream start response: {response}")
            
            if response:
                # STM32 sends configuration info, look for successful setup
                if "CV:" in response and ("Begin:" in response or "Cycles" in response):
                    # Set streaming state
                    self.streaming_active = True
                    self.streaming_type = 'cv'
                    self.streaming_progress = 0
                    self.streaming_data = []
                    
                    logger.info("✅ CV streaming started successfully")
                    logger.info(f"🔧 STM32 config: {response[:100]}...")
                    return {
                        "success": True,
                        "measurement_id": measurement_id,
                        "message": "CV streaming started",
                        "config": response
                    }
                else:
                    raise Exception(f"Unexpected response: {response}")
            else:
                raise Exception("No response from STM32")
            
        except Exception as e:
            logger.error(f"❌ CV streaming start failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_streaming_status(self):
        """Get streaming status using fixed method"""
        if not self.streaming_active:
            return {"state": "IDLE", "progress": 0}
        
        try:
            status_response = self.send_scpi_command("POTEn:CV:Stream:STATUS?")
            logger.debug(f"📊 Status response: {status_response}")
            
            if status_response:
                # Parse response: "MEASURING 75" or "COMPLETE 100" or "IDLE 0"
                parts = status_response.split()
                if len(parts) >= 2:
                    state = parts[0]
                    progress = int(parts[1])
                    self.streaming_progress = progress
                    
                    if state == "COMPLETE":
                        self.streaming_active = False
                    
                    logger.info(f"📊 Status: {state} {progress}%")
                    return {"state": state, "progress": progress}
            
            # Fallback
            return {"state": "MEASURING", "progress": self.streaming_progress}
            
        except Exception as e:
            logger.error(f"❌ Status query failed: {e}")
            return {"state": "ERROR", "progress": 0}
    
    def get_streaming_data(self):
        """Get complete streaming data using fixed method"""
        try:
            logger.info("📊 Requesting streaming data...")
            data_response = self.send_scpi_command("POTEn:CV:Stream:DATA?")
            logger.info(f"📊 Data response length: {len(data_response) if data_response else 0}")
            
            if not data_response:
                return {"success": False, "error": "No data received"}
            
            # Parse CSV data
            lines = data_response.split('\n')
            data_points = []
            
            logger.info(f"📊 Parsing {len(lines)} lines...")
            for i, line in enumerate(lines):
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
                        
                        if i < 3:  # Log first few points
                            logger.debug(f"📊 Point {i}: V={voltage:.3f}, I={current:.6e}")
                            
                except ValueError as e:
                    logger.debug(f"Parse error line {i}: {line} -> {e}")
                    continue
            
            self.streaming_data = data_points
            logger.info(f"✅ Parsed {len(data_points)} data points")
            
            # Store in database
            if self.database and self.current_measurement_id and data_points:
                try:
                    self.database.store_data_points(self.current_measurement_id, data_points)
                    self.database.update_measurement_status(self.current_measurement_id, 'COMPLETE')
                    logger.info(f"💾 Stored {len(data_points)} data points in database")
                    
                    # Auto-export files
                    if self.file_exporter:
                        export_result = self.file_exporter.export_all_formats(
                            self.current_measurement_id, 
                            'cv', 
                            data_points
                        )
                        logger.info(f"📁 Auto-exported files: {[f['filename'] for f in export_result]}")
                        
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
            response = self.send_scpi_command("POTEn:CV:Stream:STOP")
            logger.info(f"⏹️ Stop response: {response}")
            
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
scpi_server = FixedSCPIServer()

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
        "name": "Fixed H743 SCPI Server",
        "version": "2.1-fixed",
        "features": ["streaming_commands", "clean_scpi", "database_integration", "fixed_serial"],
        "status": "ready"
    })

@app.route('/connect', methods=['POST'])
def connect():
    logger.info("🔗 Manual connect requested")
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

# ===== STREAMING ENDPOINTS =====

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

# ===== LEGACY SUPPORT =====

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
    
    parser = argparse.ArgumentParser(description='Fixed H743 SCPI Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8081, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--device', default='/dev/ttyACM0', help='Serial device path')
    
    args = parser.parse_args()
    
    # Update device path
    scpi_server.port = args.device
    
    logger.info(f"🚀 Starting Fixed SCPI Server on http://{args.host}:{args.port}")
    logger.info(f"🔌 STM32 device: {args.device}")
    logger.info("🔬 Features: Fixed Serial Communication, Streaming Commands, Database Integration")
    
    # Auto-connect on startup
    logger.info("🔗 Attempting auto-connect to STM32...")
    result = scpi_server.connect()
    if result.get("success"):
        logger.info("✅ Auto-connect successful!")
        logger.info(f"📋 Device info: {result.get('device_info')}")
    else:
        logger.warning(f"⚠️ Auto-connect failed: {result.get('message')}")
        logger.info("💡 Try manual connect via API: POST /connect")
    
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()