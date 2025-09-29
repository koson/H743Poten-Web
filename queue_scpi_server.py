#!/usr/bin/env python3
"""
Queue-Based SCPI Server - Shower Idea Implementation 🚿💡
========================================================

Brilliant architecture:
- STM32 sends data continuously → Stream Manager Queue
- Web polls at any rate → Gets new data via pointer
- No blocking, no data loss, perfect performance!

Author: GitHub Copilot + User's Brilliant Shower Insight
Date: September 30, 2025
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
    from data_stream_manager import stream_manager, parse_stm32_response, DataPoint
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QueueBasedSCPIServer:
    """Queue-Based SCPI Server - The Shower Idea Implementation"""
    
    def __init__(self, port=None, baudrate=115200):
        # Auto-detect STM32 port if not specified
        if port is None:
            port = self._find_stm32_port()
        self.port = port
        self.baud_rate = baudrate
        self.serial_conn = None
        self.is_connected = False
        
        # Database and file management
        try:
            self.measurement_db = MeasurementDatabase()
            self.file_exporter = FileExporter()
            logger.info("✅ Database and file exporter ready")
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
        
        # Streaming control
        self.current_session_id = None
        self.streaming_active = False
        self.stream_thread = None
        self.measurement_type = None
        self.measurement_id = None
        
        # Initialize connection
        self.connect()
    
    def _find_stm32_port(self):
        """Auto-detect STM32 device port"""
        import glob
        
        # Check common STM32 ports
        possible_ports = [
            '/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2',
            '/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2'
        ]
        
        # Also check using glob
        acm_ports = glob.glob('/dev/ttyACM*')
        usb_ports = glob.glob('/dev/ttyUSB*')
        possible_ports.extend(acm_ports + usb_ports)
        
        # Remove duplicates and test each port
        for port in list(set(possible_ports)):
            if os.path.exists(port):
                try:
                    # Try to connect and send *IDN? to verify it's STM32
                    test_conn = serial.Serial(port, 115200, timeout=1)
                    test_conn.write(b'*IDN?\n')
                    time.sleep(0.5)
                    response = test_conn.readline().decode().strip()
                    test_conn.close()
                    
                    if 'MANUFACTURE' in response or 'INSTR' in response:
                        logger.info(f"✅ Found STM32 at {port}: {response}")
                        return port
                except Exception as e:
                    continue
        
        logger.warning("⚠️ STM32 not found, using default /dev/ttyACM0")
        return '/dev/ttyACM0'
    
    def connect(self):
        """Connect to STM32 H743 using proven method"""
        try:
            possible_ports = [self.port, '/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0']
            
            for port in possible_ports:
                if os.path.exists(port):
                    try:
                        logger.info(f"🔌 Trying to connect to {port}...")
                        
                        # USE EXACT SAME PARAMETERS AS WORKING DIRECT TEST
                        self.serial_conn = serial.Serial(
                            port=port,
                            baudrate=self.baud_rate,
                            timeout=3,
                            parity=serial.PARITY_NONE,
                            stopbits=serial.STOPBITS_ONE,
                            bytesize=serial.EIGHTBITS
                        )
                        
                        time.sleep(2)  # Let it settle
                        
                        # Test connection with *IDN?
                        self.serial_conn.write(b'*IDN?\r\n')
                        time.sleep(2)
                        
                        response = self.serial_conn.read(1000)
                        
                        if response:
                            device_info = response.decode('utf-8', errors='ignore').strip()
                            logger.info(f"📋 Device response: {device_info}")
                            
                            if "MANUFACTURE" in device_info:
                                self.is_connected = True
                                self.port = port
                                logger.info(f"✅ Connected to STM32 H743 on {port}")
                                return True
                        
                        self.serial_conn.close()
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to connect to {port}: {e}")
                        if self.serial_conn:
                            self.serial_conn.close()
                        continue
            
            logger.error("❌ No STM32 H743 found on any port")
            return False
            
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False
    
    def start_streaming(self, measurement_type: str, measurement_id: int, parameters: dict):
        """Start continuous data streaming from STM32"""
        if not self.is_connected:
            return {"success": False, "error": "Device not connected"}
        
        if self.streaming_active:
            return {"success": False, "error": "Streaming already active"}
        
        try:
            # Create stream session
            self.current_session_id = stream_manager.create_session(
                measurement_id=measurement_id,
                measurement_type=measurement_type,
                parameters=parameters
            )
            
            self.measurement_type = measurement_type
            self.measurement_id = measurement_id
            self.streaming_active = True
            
            # Start background streaming thread
            self.stream_thread = threading.Thread(
                target=self._streaming_worker,
                daemon=True
            )
            self.stream_thread.start()
            
            logger.info(f"🎬 Started streaming session: {self.current_session_id}")
            return {
                "success": True,
                "session_id": self.current_session_id,
                "message": "Streaming started"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to start streaming: {e}")
            return {"success": False, "error": str(e)}
    
    def _streaming_worker(self):
        """Background worker for continuous STM32 data collection"""
        logger.info(f"🔄 Streaming worker started for {self.measurement_type}")
        
        try:
            while self.streaming_active and self.is_connected:
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    try:
                        # Read available data
                        raw_data = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                        
                        if raw_data:
                            logger.debug(f"📥 Raw data: {raw_data}")
                            
                            # Parse STM32 response
                            data_point = parse_stm32_response(raw_data, self.measurement_type)
                            
                            if data_point:
                                # Add to stream queue
                                stream_manager.add_data_point(self.current_session_id, data_point)
                                logger.debug(f"📊 Added data point: V={data_point.voltage}, I={data_point.current}")
                            else:
                                # Handle configuration messages or other responses
                                logger.debug(f"📝 Config message: {raw_data}")
                            
                            # 🎯 AUTO-STOP DETECTION: Check for completion signals
                            if any(signal in raw_data.upper() for signal in 
                                  ["COMPLETE", "DONE", "FINISHED", "CV DONE", "SCAN COMPLETE", 
                                   "DPV COMPLETE", "SWV COMPLETE", "CA COMPLETE", "MEASUREMENT COMPLETE"]):
                                logger.info(f"🏁 Measurement completed detected: {raw_data}")
                                self.streaming_active = False
                                stream_manager.update_session_status(self.current_session_id, "completed")
                                logger.info(f"✅ Auto-stopped streaming for session: {self.current_session_id}")
                                break
                    
                    except Exception as e:
                        logger.warning(f"⚠️ Error processing data: {e}")
                
                time.sleep(0.01)  # Small delay to prevent CPU overload
                
        except Exception as e:
            logger.error(f"❌ Streaming worker error: {e}")
        finally:
            logger.info("🛑 Streaming worker stopped")
    
    def stop_streaming(self):
        """Stop data streaming"""
        if not self.streaming_active:
            return {"success": False, "error": "No active streaming"}
        
        try:
            self.streaming_active = False
            
            if self.current_session_id:
                stream_manager.update_session_status(self.current_session_id, "completed")
            
            # Wait for thread to finish
            if self.stream_thread and self.stream_thread.is_alive():
                self.stream_thread.join(timeout=5)
            
            logger.info(f"🛑 Stopped streaming session: {self.current_session_id}")
            
            session_id = self.current_session_id
            self.current_session_id = None
            self.stream_thread = None
            
            return {
                "success": True,
                "session_id": session_id,
                "message": "Streaming stopped"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to stop streaming: {e}")
            return {"success": False, "error": str(e)}
    
    def get_stream_data(self, session_id: str = None, client_id: str = "default"):
        """Get new streaming data for client"""
        if not session_id:
            session_id = self.current_session_id
            
        if not session_id:
            return {"success": False, "error": "No active session"}
        
        try:
            new_data = stream_manager.get_new_data(session_id, client_id)
            session_status = stream_manager.get_session_status(session_id)
            
            return {
                "success": True,
                "session_id": session_id,
                "new_data_points": len(new_data),
                "data": new_data,
                "status": session_status
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get stream data: {e}")
            return {"success": False, "error": str(e)}
    
    def send_command(self, command: str, wait_time: float = 2.0):
        """Send command to STM32 and get response"""
        if not self.is_connected or not self.serial_conn:
            return {"success": False, "error": "Device not connected"}
        
        try:
            # Send command
            cmd_bytes = f"{command}\r\n".encode('utf-8')
            self.serial_conn.write(cmd_bytes)
            time.sleep(wait_time)
            
            # Read response
            response = self.serial_conn.read(1000).decode('utf-8', errors='ignore').strip()
            
            return {
                "success": True,
                "command": command,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"❌ Command failed: {e}")
            return {"success": False, "error": str(e)}

# Create Flask app
app = Flask(__name__)
CORS(app)

# Initialize SCPI server
scpi_server = QueueBasedSCPIServer()

@app.route('/status', methods=['GET'])
def get_status():
    """Get server and device status"""
    return jsonify({
        "server": "Queue-Based SCPI Server - Shower Idea! 🚿💡",
        "device_connected": scpi_server.is_connected,
        "port": scpi_server.port,
        "streaming_active": scpi_server.streaming_active,
        "current_session": scpi_server.current_session_id,
        "all_sessions": stream_manager.get_all_sessions(),
        "timestamp": time.time()
    })

@app.route('/cv/stream/start', methods=['POST'])
def start_cv_stream():
    """Start CV measurement streaming"""
    try:
        data = request.get_json()
        parameters = data.get('parameters', {})
        notes = data.get('notes', '')
        
        # Create measurement record
        measurement_id = scpi_server.measurement_db.create_measurement(
            measurement_type='CV',
            parameters=json.dumps(parameters),
            notes=notes
        )
        
        # Send CV command to STM32
        # CV command format: POTEn:CV:Stream:START <start_v>,<end_v>,<begin_v>,<scan_rate>,<cycles>
        start_v = parameters.get('start_voltage', -1.0)
        end_v = parameters.get('end_voltage', 1.0)
        begin_v = parameters.get('begin_voltage', start_v)  # Default begin to start_v
        scan_rate = parameters.get('scan_rate', 0.05)
        cycles = parameters.get('cycles', 1)
        
        cv_command = f"POTEn:CV:Stream:START {start_v},{end_v},{begin_v},{scan_rate},{cycles}"
        cmd_result = scpi_server.send_command(cv_command)
        
        if not cmd_result["success"]:
            return jsonify(cmd_result), 500
        
        # Start streaming
        stream_result = scpi_server.start_streaming("CV", measurement_id, parameters)
        
        if stream_result["success"]:
            return jsonify({
                "success": True,
                "measurement_id": measurement_id,
                "session_id": stream_result["session_id"],
                "message": "CV streaming started",
                "stm32_response": cmd_result["response"]
            })
        else:
            return jsonify(stream_result), 500
            
    except Exception as e:
        logger.error(f"❌ CV stream start error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/stream/data/<session_id>', methods=['GET'])
def get_stream_data(session_id):
    """Get new streaming data for session"""
    client_id = request.args.get('client_id', 'default')
    result = scpi_server.get_stream_data(session_id, client_id)
    return jsonify(result)

@app.route('/stream/stop', methods=['POST'])
def stop_stream():
    """Stop current streaming"""
    result = scpi_server.stop_streaming()
    
    # Send stop command to STM32
    if scpi_server.is_connected:
        scpi_server.send_command("POTEn:CV:Stream:STOP")
    
    return jsonify(result)

@app.route('/command', methods=['POST'])
def send_command():
    """Send raw command to STM32"""
    try:
        data = request.get_json()
        command = data.get('command', '')
        wait_time = data.get('wait_time', 2.0)
        
        result = scpi_server.send_command(command, wait_time)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Queue-Based SCPI Server...")
    logger.info("🚿💡 Shower Idea Implementation - No more blocking!")
    
    # Test stream manager
    logger.info("🧪 Testing Stream Manager...")
    test_session = stream_manager.create_session(0, "TEST", {})
    test_point = DataPoint(time.time(), 1.0, -0.001, "TEST")
    stream_manager.add_data_point(test_session, test_point)
    test_data = stream_manager.get_new_data(test_session, "test_client")
    logger.info(f"✅ Stream Manager working: {len(test_data)} points")
    
    app.run(host='0.0.0.0', port=8094, debug=False, threaded=True)