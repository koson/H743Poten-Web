#!/usr/bin/env python3
"""
Multi-Device Laboratory Management System
=========================================

🌅 Morning Research Lab Vision:
- Multiple STM32 devices (up to 10+) connected via USB Hub
- Command queue management for all-day automation
- Researchers setup experiments in the morning
- System runs autonomously throughout the day

🎯 Advanced Features:
- Auto-device discovery and registration
- Intelligent command routing and load balancing
- Real-time queue management with priority system
- Multi-researcher support with isolation
- Comprehensive monitoring and logging

Author: GitHub Copilot + User's Laboratory Vision
Date: September 30, 2025
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import serial
import serial.tools.list_ports
import time
import json
import logging
import threading
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Import our modules
try:
    from database import MeasurementDatabase
    from file_exporter import FileExporter
    from data_stream_manager import stream_manager, parse_stm32_response, DataPoint
    from command_queue_manager import queue_manager, Priority, CommandStatus
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiDeviceSCPIServer:
    """Multi-Device Laboratory Management System"""
    
    def __init__(self):
        self.devices: Dict[str, serial.Serial] = {}
        self.device_info: Dict[str, Dict] = {}
        self.execution_threads: Dict[str, threading.Thread] = {}
        
        # Database and file management
        try:
            self.measurement_db = MeasurementDatabase()
            self.file_exporter = FileExporter()
            logger.info("✅ Database and file exporter ready")
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
        
        # Auto-discovery and management
        self.auto_discovery_enabled = True
        self.discovery_interval = 30  # seconds
        self.discovery_thread = None
        
        # Start systems
        self._start_auto_discovery()
        self._start_queue_executor()
    
    def _start_auto_discovery(self):
        """Start automatic device discovery"""
        if self.discovery_thread and self.discovery_thread.is_alive():
            return
            
        self.discovery_thread = threading.Thread(
            target=self._auto_discovery_worker,
            daemon=True
        )
        self.discovery_thread.start()
        logger.info("🔍 Auto-discovery started")
    
    def _auto_discovery_worker(self):
        """Background worker for device discovery"""
        while self.auto_discovery_enabled:
            try:
                self._discover_stm32_devices()
                time.sleep(self.discovery_interval)
            except Exception as e:
                logger.error(f"❌ Discovery error: {e}")
                time.sleep(5)
    
    def _discover_stm32_devices(self):
        """Discover and register STM32 devices"""
        logger.debug("🔍 Scanning for STM32 devices...")
        
        # List all available ports
        available_ports = serial.tools.list_ports.comports()
        
        for port_info in available_ports:
            port = port_info.device
            
            # Skip if already connected
            if any(info.get('port') == port for info in self.device_info.values()):
                continue
            
            # Try to connect and identify STM32
            if self._try_connect_stm32(port):
                logger.info(f"🆕 Discovered new STM32 device: {port}")
    
    def _try_connect_stm32(self, port: str) -> bool:
        """Try to connect to STM32 device"""
        try:
            # Test connection
            ser = serial.Serial(
                port=port,
                baudrate=115200,
                timeout=3,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            time.sleep(2)  # Let it settle
            
            # Test with *IDN?
            ser.write(b'*IDN?\r\n')
            time.sleep(2)
            
            response = ser.read(1000).decode('utf-8', errors='ignore').strip()
            
            if "MANUFACTURE" in response:
                # Extract device info
                device_id = f"STM32_{port.split('/')[-1]}"
                serial_number = self._extract_serial_number(response)
                
                # Register device
                self.devices[device_id] = ser
                self.device_info[device_id] = {
                    'port': port,
                    'serial_number': serial_number,
                    'device_response': response,
                    'connected_at': time.time(),
                    'status': 'connected'
                }
                
                # Register with queue manager
                capabilities = ["CV", "DPV", "SWV", "CA"]  # Default capabilities
                queue_manager.register_device(device_id, port, serial_number, capabilities)
                
                logger.info(f"✅ Connected STM32: {device_id} on {port}")
                return True
            
            ser.close()
            
        except Exception as e:
            logger.debug(f"⚠️ Failed to connect to {port}: {e}")
            
        return False
    
    def _extract_serial_number(self, response: str) -> str:
        """Extract serial number from device response"""
        # Parse STM32 response to get serial number
        # Format: MANUFACTURE,INSTR2013,0,01-02
        parts = response.split(',')
        if len(parts) >= 4:
            return parts[3].strip()
        return "UNKNOWN"
    
    def _start_queue_executor(self):
        """Start automatic queue execution"""
        executor_thread = threading.Thread(
            target=self._queue_executor_worker,
            daemon=True
        )
        executor_thread.start()
        logger.info("🤖 Queue executor started")
    
    def _queue_executor_worker(self):
        """Background worker for executing queued commands"""
        while True:
            try:
                if not queue_manager.auto_execution_enabled:
                    time.sleep(5)
                    continue
                
                # Check for available devices and pending commands
                self._execute_next_commands()
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"❌ Queue executor error: {e}")
                time.sleep(5)
    
    def _execute_next_commands(self):
        """Execute next available commands"""
        queue_status = queue_manager.get_queue_status()
        
        # Find available devices
        for device_id, device_status in queue_status['devices'].items():
            if (device_status['status'] == 'connected' and 
                device_status['current_command'] is None and
                device_id in self.devices):
                
                # Find next command for this device
                next_command = self._get_next_command_for_device(device_id)
                if next_command:
                    self._start_command_execution(device_id, next_command)
    
    def _get_next_command_for_device(self, device_id: str) -> Optional[str]:
        """Get next command ID for specific device"""
        # This is a simplified version - in practice, you'd need to 
        # properly interface with the priority queue
        with queue_manager.lock:
            for command_id, command in queue_manager.commands.items():
                if (command.device_id == device_id and 
                    command.status == CommandStatus.QUEUED):
                    return command_id
        return None
    
    def _start_command_execution(self, device_id: str, command_id: str):
        """Start executing a command on a device"""
        try:
            with queue_manager.lock:
                command = queue_manager.commands.get(command_id)
                if not command:
                    return
                
                # Update command status
                command.status = CommandStatus.RUNNING
                command.started_at = time.time()
                
                # Update device status
                device = queue_manager.devices.get(device_id)
                if device:
                    device.status = "busy"
                    device.current_command_id = command_id
                    device.last_activity = time.time()
            
            # Start execution thread
            execution_thread = threading.Thread(
                target=self._execute_command_worker,
                args=(device_id, command_id),
                daemon=True
            )
            execution_thread.start()
            self.execution_threads[command_id] = execution_thread
            
            logger.info(f"🚀 Started executing command {command_id} on {device_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to start command execution: {e}")
    
    def _execute_command_worker(self, device_id: str, command_id: str):
        """Worker thread for executing a single command"""
        try:
            with queue_manager.lock:
                command = queue_manager.commands.get(command_id)
                if not command:
                    return
            
            # Create measurement record
            measurement_id = self.measurement_db.create_measurement(
                measurement_type=command.command_type,
                parameters=json.dumps(command.parameters),
                notes=f"Auto-execution for {command.researcher_id}: {command.notes}"
            )
            
            # Start streaming session
            session_id = stream_manager.create_session(
                measurement_id=measurement_id,
                measurement_type=command.command_type,
                parameters=command.parameters
            )
            
            # Update command with session info
            with queue_manager.lock:
                command.session_id = session_id
            
            # Send command to STM32
            success = self._send_command_to_device(device_id, command)
            
            if success:
                # Start data collection
                self._collect_data_from_device(device_id, command_id, session_id)
                
                # Mark as completed
                with queue_manager.lock:
                    command.status = CommandStatus.COMPLETED
                    command.completed_at = time.time()
                    queue_manager.total_completed += 1
                    
                logger.info(f"✅ Completed command {command_id}")
                
            else:
                # Mark as failed
                with queue_manager.lock:
                    command.status = CommandStatus.FAILED
                    command.completed_at = time.time()
                    command.error_message = "Failed to send command to device"
                    queue_manager.total_failed += 1
                    
                logger.error(f"❌ Failed command {command_id}")
            
        except Exception as e:
            logger.error(f"❌ Command execution error: {e}")
            with queue_manager.lock:
                command = queue_manager.commands.get(command_id)
                if command:
                    command.status = CommandStatus.FAILED
                    command.completed_at = time.time()
                    command.error_message = str(e)
                    queue_manager.total_failed += 1
        
        finally:
            # Clean up
            self._cleanup_command_execution(device_id, command_id)
    
    def _send_command_to_device(self, device_id: str, command) -> bool:
        """Send measurement command to STM32 device"""
        try:
            device_serial = self.devices.get(device_id)
            if not device_serial:
                return False
            
            # Build SCPI command based on type
            if command.command_type == "CV":
                params = command.parameters
                scpi_cmd = f"POTEn:CV:Stream:START {params.get('start_voltage', -1.0)},{params.get('end_voltage', 1.0)},{params.get('begin_voltage', 0.0)},{params.get('scan_rate', 0.05)},{params.get('cycles', 1)}"
            
            elif command.command_type == "DPV":
                params = command.parameters
                scpi_cmd = f"POTEn:DPV:START {params.get('start_voltage', -1.0)},{params.get('end_voltage', 1.0)},{params.get('step_voltage', 0.004)},{params.get('pulse_amplitude', 0.05)},{params.get('pulse_width', 0.05)},{params.get('sampling_width', 0.017)},{params.get('pulse_period', 0.2)}"
            
            else:
                logger.error(f"Unsupported command type: {command.command_type}")
                return False
            
            # Send command
            device_serial.write(f"{scpi_cmd}\r\n".encode('utf-8'))
            time.sleep(2)
            
            # Read response
            response = device_serial.read(1000).decode('utf-8', errors='ignore')
            logger.info(f"📤 Sent to {device_id}: {scpi_cmd}")
            logger.info(f"📥 Response: {response}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send command to {device_id}: {e}")
            return False
    
    def _collect_data_from_device(self, device_id: str, command_id: str, session_id: str):
        """Collect streaming data from device"""
        device_serial = self.devices.get(device_id)
        if not device_serial:
            return
        
        # Collect data for a reasonable time
        collection_start = time.time()
        max_collection_time = 300  # 5 minutes max
        
        with queue_manager.lock:
            command = queue_manager.commands.get(command_id)
            measurement_type = command.command_type if command else "UNKNOWN"
        
        while (time.time() - collection_start) < max_collection_time:
            try:
                if device_serial.in_waiting > 0:
                    raw_data = device_serial.readline().decode('utf-8', errors='ignore').strip()
                    
                    if raw_data:
                        # Parse and add to stream
                        data_point = parse_stm32_response(raw_data, measurement_type)
                        if data_point:
                            stream_manager.add_data_point(session_id, data_point)
                        
                        # Check for completion signals
                        if any(signal in raw_data.upper() for signal in 
                              ["COMPLETE", "DONE", "FINISHED"]):
                            logger.info(f"📊 Data collection completed for {command_id}")
                            break
                
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Data collection error: {e}")
                break
        
        # Mark stream as completed
        stream_manager.update_session_status(session_id, "completed")
    
    def _cleanup_command_execution(self, device_id: str, command_id: str):
        """Clean up after command execution"""
        try:
            # Update device status
            with queue_manager.lock:
                device = queue_manager.devices.get(device_id)
                if device:
                    device.status = "connected"
                    device.current_command_id = None
                    device.last_activity = time.time()
                    device.queue_size = max(0, device.queue_size - 1)
            
            # Remove execution thread
            if command_id in self.execution_threads:
                del self.execution_threads[command_id]
                
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        queue_status = queue_manager.get_queue_status()
        
        return {
            "system_info": {
                "total_devices": len(self.devices),
                "connected_devices": len([d for d in self.device_info.values() 
                                        if d.get('status') == 'connected']),
                "auto_discovery": self.auto_discovery_enabled,
                "uptime": time.time() - (min(d.get('connected_at', time.time()) 
                                           for d in self.device_info.values()) 
                                        if self.device_info else time.time())
            },
            "devices": {
                device_id: {
                    **info,
                    "queue_info": queue_status['devices'].get(device_id, {})
                }
                for device_id, info in self.device_info.items()
            },
            "queue_status": queue_status,
            "active_streams": len(stream_manager.get_all_sessions())
        }

# Create Flask app
app = Flask(__name__)
CORS(app)

# Initialize multi-device server
multi_device_server = MultiDeviceSCPIServer()

@app.route('/system/status', methods=['GET'])
def get_system_status():
    """Get comprehensive system status"""
    return jsonify(multi_device_server.get_system_status())

@app.route('/queue/add', methods=['POST'])
def add_to_queue():
    """Add command to execution queue"""
    try:
        data = request.get_json()
        
        command_id = queue_manager.queue_command(
            command_type=data.get('command_type'),
            parameters=data.get('parameters', {}),
            researcher_id=data.get('researcher_id'),
            sample_info=data.get('sample_info', {}),
            device_id=data.get('device_id'),
            priority=Priority[data.get('priority', 'NORMAL').upper()],
            notes=data.get('notes', ''),
            estimated_duration=data.get('estimated_duration')
        )
        
        return jsonify({
            "success": True,
            "command_id": command_id,
            "message": "Command added to queue"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/queue/status', methods=['GET'])
def get_queue_status():
    """Get queue status"""
    return jsonify(queue_manager.get_queue_status())

@app.route('/queue/command/<command_id>', methods=['GET'])
def get_command_details(command_id):
    """Get detailed command information"""
    details = queue_manager.get_command_details(command_id)
    if details:
        return jsonify(details)
    else:
        return jsonify({"error": "Command not found"}), 404

@app.route('/queue/command/<command_id>', methods=['PUT'])
def modify_command(command_id):
    """Modify a queued command"""
    try:
        data = request.get_json()
        success = queue_manager.modify_command(command_id, **data)
        
        if success:
            return jsonify({"success": True, "message": "Command modified"})
        else:
            return jsonify({"success": False, "error": "Cannot modify command"}), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/queue/command/<command_id>', methods=['DELETE'])
def cancel_command(command_id):
    """Cancel a command"""
    try:
        reason = request.args.get('reason', 'User cancelled')
        success = queue_manager.cancel_command(command_id, reason)
        
        if success:
            return jsonify({"success": True, "message": "Command cancelled"})
        else:
            return jsonify({"success": False, "error": "Cannot cancel command"}), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/researcher/<researcher_id>/commands', methods=['GET'])
def get_researcher_commands(researcher_id):
    """Get all commands for a researcher"""
    commands = queue_manager.get_researcher_commands(researcher_id)
    return jsonify({"researcher_id": researcher_id, "commands": commands})

@app.route('/stream/data/<session_id>', methods=['GET'])
def get_stream_data(session_id):
    """Get streaming data"""
    client_id = request.args.get('client_id', 'default')
    new_data = stream_manager.get_new_data(session_id, client_id)
    session_status = stream_manager.get_session_status(session_id)
    
    return jsonify({
        "success": True,
        "session_id": session_id,
        "new_data_points": len(new_data),
        "data": new_data,
        "status": session_status
    })

if __name__ == '__main__':
    logger.info("🚀 Starting Multi-Device Laboratory Management System...")
    logger.info("🌅 Morning Research Lab Vision - Automated All-Day Execution!")
    logger.info("📱 Supporting up to 10+ STM32 devices via USB Hub")
    
    app.run(host='0.0.0.0', port=8095, debug=False, threaded=True)