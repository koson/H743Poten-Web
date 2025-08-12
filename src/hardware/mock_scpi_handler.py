"""
Mock SCPI Handler for development and testing
"""

import logging
import time
import random
import math
import sys
import os

# Add the parent directory to the Python path to handle imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    # Try relative imports first (when run as module)
    from ..config.settings import Config
except ImportError:
    # Fall back to absolute imports (when run directly)
    from config.settings import Config

logger = logging.getLogger(__name__)

class MockSCPIHandler:
    def __init__(self, port=None, baud_rate=None):
        self.port = port or Config.SERIAL_PORT
        self.baud_rate = baud_rate or Config.BAUD_RATE
        self.is_connected = False
        self._measurement_running = False
        self._measurement_data = []
        self._time_start = None

    def connect(self):
        """Simulate connecting to the device"""
        try:
            self.is_connected = True
            logger.info(f"[MOCK] Connected to {self.port} at {self.baud_rate} baud")
            return True
        except Exception as e:
            logger.error(f"[MOCK] Failed to connect: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Simulate disconnecting from the device"""
        try:
            self.is_connected = False
            logger.info("[MOCK] Disconnected from device")
        except Exception as e:
            logger.error(f"[MOCK] Error during disconnect: {e}")
            raise

    def send_custom_command(self, command):
        """Simulate sending a custom SCPI command"""
        try:
            if not self.is_connected:
                return {
                    'success': False,
                    'command': command,
                    'response': None,
                    'error': 'Device not connected'
                }

            # Handle different command types
            command = command.strip().lower()
            
            if command == '*idn?':
                response = "H743Poten,MOCK,v1.0"
            elif 'poten:info?' in command:
                response = "H743Poten Mock Device,HW:v1.0,FW:v1.0,SN:MOCK001"
            elif 'poten:stat?' in command:
                if self._measurement_running:
                    response = "RUNNING"
                else:
                    response = "IDLE"
            elif ':start' in command:
                self._start_mock_measurement()
                response = "OK"
            elif ':stop' in command:
                self._measurement_running = False
                response = "OK"
            elif ':data?' in command:
                response = self._generate_mock_data()
            else:
                response = "OK"

            return {
                'success': True,
                'command': command,
                'response': response,
                'error': None
            }

        except Exception as e:
            logger.error(f"[MOCK] Error sending command '{command}': {e}")
            return {
                'success': False,
                'command': command,
                'response': None,
                'error': str(e)
            }

    def query(self, command):
        """Simulate sending a query command and return the response"""
        result = self.send_custom_command(command)
        if result['success']:
            return result['response']
        raise Exception(result['error'])

    def _start_mock_measurement(self):
        """Start generating mock measurement data"""
        self._measurement_running = True
        self._time_start = time.time()
        self._measurement_data = []

    def _generate_mock_data(self):
        """Generate mock measurement data"""
        if not self._measurement_running or not self._time_start:
            return ""

        current_time = time.time()
        elapsed_time = current_time - self._time_start
        num_points = int(elapsed_time * 10)  # Generate 10 points per second

        data = []
        for i in range(num_points):
            t = i / 10.0
            voltage = 0.5 * math.sin(2 * math.pi * 0.1 * t)
            current = voltage * 0.001 + random.uniform(-0.0001, 0.0001)
            data.append(f"{t:.3f},{voltage:.6f},{current:.9f}")

        return "\n".join(data)
