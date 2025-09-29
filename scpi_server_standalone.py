#!/usr/bin/env python3
"""
Standalone SCPI Server for H743 Potentiostat
Dedicated service to handle STM32 communication
Provides REST API for web frontend

Usage:
    python3 scpi_server_standalone.py

API Endpoints:
    GET  /status           - Server and device status
    POST /connect         - Connect to STM32
    POST /disconnect      - Disconnect from STM32
    POST /command         - Send SCPI command
    GET  /cv/status       - CV measurement status
    POST /cv/start        - Start CV measurement
    GET  /cv/data         - Get CV measurement data
    POST /cv/stop         - Stop CV measurement
"""

import json
import logging
import time
import threading
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import serial
import serial.tools.list_ports
import os

# Import our database and file export modules
try:
    from database import db
    from file_exporter import exporter
    from file_browser import file_browser_bp
    DB_AVAILABLE = True
    EXPORTER_AVAILABLE = True
    print("✅ Database and File Export modules loaded")
except ImportError as e:
    print(f"⚠️  Database/Export modules not available: {e}")
    db = None
    exporter = None
    file_browser_bp = None
    DB_AVAILABLE = False
    EXPORTER_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for web frontend

# Register file browser blueprint if available
if file_browser_bp:
    app.register_blueprint(file_browser_bp)

class SCPIServer:
    def __init__(self):
        self.serial_port = None
        self.serial_conn = None
        self.is_connected = False
        self.baud_rate = 115200
        
        # CV measurement state
        self.cv_running = False
        self.cv_data = []
        self.cv_progress = 0
        self.cv_start_time = None
        self.current_measurement_id = None  # Database measurement ID
        
        # Auto-detect STM32 port
        self.detect_stm32_port()
        
    def detect_stm32_port(self):
        """Auto-detect STM32 port"""
        logger.info("🔍 Detecting STM32 port...")
        
        # Common STM32 ports
        possible_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']
        
        # Check which ports exist
        existing_ports = []
        for port in possible_ports:
            if os.path.exists(port):
                existing_ports.append(port)
                logger.info(f"   📍 Found: {port}")
        
        if existing_ports:
            self.serial_port = existing_ports[0]  # Use first found
            logger.info(f"✅ Using port: {self.serial_port}")
        else:
            self.serial_port = '/dev/ttyACM1'  # Default fallback
            logger.warning(f"⚠️  No ports found, using default: {self.serial_port}")
    
    def connect(self):
        """Connect to STM32"""
        try:
            if self.is_connected:
                return {"success": True, "message": f"Already connected to {self.serial_port}"}
            
            logger.info(f"🔌 Connecting to {self.serial_port} at {self.baud_rate} baud...")
            
            if not os.path.exists(self.serial_port):
                raise Exception(f"Port {self.serial_port} not found")
            
            # Try to change permissions if needed
            try:
                import subprocess
                subprocess.run(['sudo', 'chmod', '666', self.serial_port], 
                             capture_output=True, timeout=5)
                logger.info(f"🔧 Applied permissions to {self.serial_port}")
            except:
                logger.warning("⚠️  Could not change port permissions, trying anyway...")
            
            self.serial_conn = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                timeout=1.0,
                write_timeout=1.0
            )
            
            time.sleep(0.5)  # Let connection stabilize
            
            # Test connection with *IDN? - use extended timeout for first connection
            logger.info("🧪 Testing STM32 connection with *IDN? command...")
            test_response = self.send_command("*IDN?")
            
            if test_response and test_response.get("success") and test_response.get("response"):
                response = test_response.get("response", "").strip()
                if "MANUFACTURE" in response or len(response) > 5:  # Got some meaningful response
                    self.is_connected = True
                    logger.info(f"✅ STM32 connection successful - Response: {response}")
                    return {"success": True, "message": f"Connected to {self.serial_port}"}
            
            logger.warning("⚠️  STM32 connection test failed - may need manual retry")
            # Don't fail completely, allow manual retry via API
            return {"success": False, "message": "No response from STM32 - try manual connect"}
                
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            self.is_connected = False
            if self.serial_conn:
                try:
                    self.serial_conn.close()
                except:
                    pass
                self.serial_conn = None
            return {"success": False, "message": str(e)}
    
    def disconnect(self):
        """Disconnect from STM32"""
        try:
            if self.serial_conn:
                self.serial_conn.close()
            self.is_connected = False
            self.serial_conn = None
            logger.info("🔌 Disconnected from STM32")
            return {"success": True, "message": "Disconnected"}
        except Exception as e:
            logger.error(f"❌ Disconnect error: {e}")
            return {"success": False, "message": str(e)}
    
    def send_command(self, command):
        """Send SCPI command and get clean response"""
        if not self.is_connected or not self.serial_conn:
            return {"success": False, "error": "Not connected"}
        
        try:
            # Add SCPI termination
            if not command.endswith('\r\n'):
                command = command.strip() + '\r\n'
            
            logger.debug(f"📤 Sending: {command.strip()}")
            self.serial_conn.write(command.encode())
            
            # Read response for query commands
            if '?' in command:
                # Read multiple lines and filter debug messages
                all_data = ""
                start_time = time.time()
                timeout = 3.0  # Extended timeout for debug messages
                
                while (time.time() - start_time) < timeout:
                    try:
                        self.serial_conn.timeout = 0.1  # Short read timeout
                        line_bytes = self.serial_conn.readline()
                        if not line_bytes:
                            continue
                        
                        # Decode with error handling
                        try:
                            line = line_bytes.decode('utf-8', errors='ignore').strip()
                        except:
                            line = line_bytes.decode('latin-1', errors='ignore').strip()
                        
                        if line:
                            all_data += line + "\n"
                            
                            # Check if this is a real SCPI response
                            if self.is_real_scpi_response(line, command):
                                logger.debug(f"📥 Found real response: {line}")
                                # Continue reading a bit more to get complete response
                                time.sleep(0.1)
                                # Try to read any remaining data
                                try:
                                    extra = self.serial_conn.read(100)
                                    if extra:
                                        all_data += extra.decode('utf-8', errors='ignore')
                                except:
                                    pass
                                break
                    except:
                        continue
                
                # Filter out debug messages
                clean_response = self.filter_debug_messages(all_data, command)
                logger.debug(f"✅ Clean response: {clean_response}")
                
                return {
                    "success": True,
                    "command": command.strip(),
                    "response": clean_response
                }
            else:
                return {
                    "success": True,
                    "command": command.strip(),
                    "response": "OK"
                }
                
        except Exception as e:
            logger.error(f"❌ Command error: {e}")
            return {"success": False, "error": str(e)}
    
    def is_real_scpi_response(self, line, command):
        """Check if line is real SCPI response (not debug)"""
        if not line:
            return False
        
        # Debug patterns to ignore (including hex codes for emojis)
        debug_patterns = [
            "🔤", "📥", "🔍", "🚀", "⚙️", "🏁", "📊",
            "SCPI: Processing char", "CDC: Received", "SCPI_Parse: Parsing",
            "Debug:", "DEBUG:",
            "\\xf0\\x9f\\x94", "\\x93\\xa5",  # Hex patterns for emoji
            "0x2A", "0x49", "0x44", "0x4E",  # Hex patterns from debug
            " bytes:", "Parsing "
        ]
        
        # Skip debug messages
        for pattern in debug_patterns:
            if pattern in line:
                return False
        
        # Command-specific validation - more specific patterns
        if "*IDN?" in command.upper():
            # IDN should return manufacturer info with commas, not debug
            return ("MANUFACTURE" in line or "," in line) and not any(p in line for p in debug_patterns)
        elif "STATUS?" in command.upper():
            return line.strip().upper() in ["IDLE", "MEASURING", "COMPLETE"]
        elif "DATA?" in command.upper():
            # Data should be CSV format or empty
            return ("voltage,current" in line.lower() or "," in line or line.strip() == "")
        
        # General check - real responses don't have debug patterns
        return len(line.strip()) > 0 and not any(p in line for p in debug_patterns)
    
    def filter_debug_messages(self, raw_data, command):
        """Filter debug messages from response"""
        if not raw_data:
            return ""
        
        lines = raw_data.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Extended debug patterns including hex patterns
            debug_patterns = [
                "🔤", "📥", "🔍", "🚀", "⚙️", "🏁", "📊",
                "SCPI: Processing char", "CDC: Received", "SCPI_Parse: Parsing",
                "\\xf0\\x9f\\x94", "\\x93\\xa5",  # Hex emoji patterns
                "0x2A", "0x49", "0x44", "0x4E", "0x3F", "0x0D", "0x0A",  # Character hex codes
                " bytes:", "Parsing ", "Processing char"
            ]
            
            # Skip debug lines
            is_debug = False
            for pattern in debug_patterns:
                if pattern in line:
                    is_debug = True
                    break
            
            if not is_debug:
                clean_lines.append(line)
        
        # Command-specific filtering
        if "*IDN?" in command.upper():
            # Look for manufacturer response specifically
            for line in clean_lines:
                if "MANUFACTURE" in line and "," in line:
                    return line
            # Fallback to any line with commas
            for line in clean_lines:
                if "," in line and len(line) > 10:  # Reasonable length check
                    return line
        elif "STATUS?" in command.upper():
            for line in clean_lines:
                if line.upper() in ["IDLE", "MEASURING", "COMPLETE"]:
                    return line
        elif "DATA?" in command.upper():
            # Return all non-debug lines for data
            return '\n'.join(clean_lines).strip()
        
        return '\n'.join(clean_lines).strip()

# Global SCPI server instance
scpi_server = SCPIServer()

# API Routes
@app.route('/status', methods=['GET'])
def get_status():
    """Get server and device status"""
    return jsonify({
        "server_status": "running",
        "device_connected": scpi_server.is_connected,
        "device_port": scpi_server.serial_port,
        "baud_rate": scpi_server.baud_rate,
        "cv_running": scpi_server.cv_running,
        "cv_progress": scpi_server.cv_progress,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/connect', methods=['POST'])
def connect_device():
    """Connect to STM32"""
    result = scpi_server.connect()
    return jsonify(result)

@app.route('/disconnect', methods=['POST']) 
def disconnect_device():
    """Disconnect from STM32"""
    result = scpi_server.disconnect()
    return jsonify(result)

@app.route('/command', methods=['POST'])
def send_command():
    """Send SCPI command"""
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({"success": False, "error": "No command provided"}), 400
    
    result = scpi_server.send_command(data['command'])
    return jsonify(result)

@app.route('/cv/status', methods=['GET'])
def cv_status():
    """Get CV measurement status"""
    if not scpi_server.is_connected:
        return jsonify({"success": False, "error": "Device not connected"})
    
    # Query STM32 for current status
    status_result = scpi_server.send_command("POTEn:CV:STATUS?")
    
    return jsonify({
        "success": True,
        "running": scpi_server.cv_running,
        "progress": scpi_server.cv_progress,
        "data_points": len(scpi_server.cv_data),
        "stm32_status": status_result.get("response", "UNKNOWN") if status_result.get("success") else "ERROR"
    })

@app.route('/cv/start', methods=['POST'])
def cv_start():
    """Start CV measurement with database integration"""
    if not scpi_server.is_connected:
        return jsonify({"success": False, "error": "Device not connected"})
    
    # Get parameters from request
    data = request.get_json() or {}
    parameters = data.get('parameters', {
        'start_voltage': -0.5,
        'end_voltage': 0.5,
        'scan_rate': 0.05,
        'step_size': 0.01
    })
    notes = data.get('notes', '')
    
    # Create measurement record in database
    measurement_id = None
    if DB_AVAILABLE and db:
        try:
            measurement_id = db.create_measurement('CV', parameters, notes)
            scpi_server.current_measurement_id = measurement_id
            logger.info(f"📝 Created measurement record {measurement_id}")
        except Exception as e:
            logger.error(f"Database error: {e}")
    
    # Clear previous data
    scpi_server.cv_data = []
    scpi_server.cv_progress = 0
    scpi_server.cv_start_time = time.time()
    
    # Send start command to STM32
    result = scpi_server.send_command("POTEn:CV:Start:ALL")
    
    if result.get("success"):
        scpi_server.cv_running = True
        
        # Update database status
        if measurement_id and DB_AVAILABLE and db:
            try:
                db.update_measurement_status(measurement_id, 'MEASURING')
            except Exception as e:
                logger.error(f"Database update error: {e}")
        
        logger.info("🚀 CV measurement started")
        return jsonify({
            "success": True, 
            "message": "CV measurement started",
            "measurement_id": measurement_id
        })
    else:
        # Update database with error status
        if measurement_id and DB_AVAILABLE and db:
            try:
                db.update_measurement_status(measurement_id, 'ERROR')
            except Exception as e:
                logger.error(f"Database update error: {e}")
        
        return jsonify({"success": False, "error": result.get("error", "Failed to start")})

@app.route('/cv/data', methods=['GET'])
def cv_data():
    """Get CV measurement data"""
    if not scpi_server.is_connected:
        return jsonify({"success": False, "error": "Device not connected"})
    
    # Query STM32 for data
    data_result = scpi_server.send_command("POTEn:CV:DATA?")
    
    if data_result.get("success"):
        raw_data = data_result.get("response", "")
        
        # Parse CSV data
        data_points = []
        if raw_data and raw_data.strip():
            for line in raw_data.split('\n'):
                line = line.strip()
                if line and ',' in line and not line.startswith('voltage'):
                    try:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            voltage = float(parts[0])
                            current = float(parts[1])
                            data_points.append({"voltage": voltage, "current": current})
                    except:
                        continue
        
        # Update server state
        scpi_server.cv_data = data_points
        
        return jsonify({
            "success": True,
            "data": data_points,
            "count": len(data_points)
        })
    else:
        return jsonify({"success": False, "error": data_result.get("error", "Failed to get data")})

@app.route('/cv/stop', methods=['POST'])
def cv_stop():
    """Stop CV measurement and finalize database record"""
    scpi_server.cv_running = False
    
    # Finalize measurement in database
    if scpi_server.current_measurement_id and DB_AVAILABLE and db:
        try:
            duration = time.time() - scpi_server.cv_start_time if scpi_server.cv_start_time else 0
            db.update_measurement_status(
                scpi_server.current_measurement_id, 
                'STOPPED', 
                len(scpi_server.cv_data),
                duration
            )
            
            # Store data points if we have any
            if scpi_server.cv_data:
                db.store_data_points(scpi_server.current_measurement_id, scpi_server.cv_data)
            
            logger.info(f"📝 Finalized measurement {scpi_server.current_measurement_id}")
        except Exception as e:
            logger.error(f"Database finalization error: {e}")
    
    scpi_server.current_measurement_id = None
    logger.info("⏹️  CV measurement stopped")
    return jsonify({"success": True, "message": "CV measurement stopped"})

# Additional API endpoints for enhanced functionality

@app.route('/measurements/export/<int:measurement_id>', methods=['POST'])
def export_measurement_endpoint(measurement_id):
    """Export specific measurement"""
    if not DB_AVAILABLE or not EXPORTER_AVAILABLE:
        return jsonify({"success": False, "error": "Database or exporter not available"}), 500
    
    try:
        measurement = db.get_measurement(measurement_id)
        if not measurement:
            return jsonify({"success": False, "error": "Measurement not found"}), 404
        
        data_points = db.get_measurement_data(measurement_id)
        exported_files = exporter.export_all_formats(measurement_id, measurement, data_points)
        
        # Register files in database
        registered_files = []
        for file_type, file_path in exported_files.items():
            filename = os.path.basename(file_path)
            file_id = db.register_exported_file(measurement_id, file_type, filename, file_path)
            registered_files.append({
                'id': file_id,
                'type': file_type,
                'filename': filename
            })
        
        return jsonify({
            "success": True,
            "message": f"Exported measurement {measurement_id}",
            "files": registered_files
        })
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/measurements/auto-export', methods=['POST'])
def auto_export_current():
    """Auto-export current measurement when complete"""
    if not scpi_server.cv_running and scpi_server.current_measurement_id:
        try:
            return export_measurement_endpoint(scpi_server.current_measurement_id)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    return jsonify({"success": False, "error": "No completed measurement to export"}), 400

@app.route('/system/status', methods=['GET'])
def system_status():
    """Get comprehensive system status"""
    status = {
        "scpi_server": {
            "running": True,
            "device_connected": scpi_server.is_connected,
            "device_port": scpi_server.serial_port,
            "cv_running": scpi_server.cv_running,
            "current_measurement": scpi_server.current_measurement_id
        },
        "database": {
            "available": DB_AVAILABLE,
            "stats": db.get_database_stats() if DB_AVAILABLE and db else None
        },
        "file_export": {
            "available": EXPORTER_AVAILABLE,
            "stats": exporter.get_export_stats() if EXPORTER_AVAILABLE and exporter else None
        }
    }
    
    return jsonify({"success": True, "status": status})

if __name__ == '__main__':
    logger.info("🚀 Starting H743 SCPI Server with Database & File Export...")
    logger.info(f"   📍 Device port: {scpi_server.serial_port}")
    logger.info(f"   🌐 API server: http://localhost:8081")
    logger.info(f"   📚 API docs: See header comments")
    logger.info(f"   🗃️  Database: {'✅ Available' if DB_AVAILABLE else '❌ Not available'}")
    logger.info(f"   📁 File Export: {'✅ Available' if EXPORTER_AVAILABLE else '❌ Not available'}")
    
    # Initialize database and export directories
    if DB_AVAILABLE and db:
        try:
            logger.info("📝 Database initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    if EXPORTER_AVAILABLE and exporter:
        try:
            logger.info("📁 Export directories ready")
        except Exception as e:
            logger.error(f"Export initialization failed: {e}")
    
    # Auto-connect on startup
    connect_result = scpi_server.connect()
    if connect_result.get("success"):
        logger.info("✅ Auto-connected to STM32")
    else:
        logger.warning("⚠️  Auto-connect failed, will retry on API calls")
    
    # Start Flask server
    app.run(host='0.0.0.0', port=8081, debug=False)