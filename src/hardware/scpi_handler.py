"""
SCPI Handler for H743Poten
Handles serial communication with STM32H743 device
"""

import serial
import logging
import time
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

class SCPIHandler:
    def __init__(self, port=None, baud_rate=None):
        self.port = port or Config.SERIAL_PORT
        self.baud_rate = baud_rate or Config.BAUD_RATE
        self.serial = None
        self.is_connected = False

    def connect(self):
        """Connect to the device"""
        try:
            if self.is_connected:
                return True

            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=1
            )
            self.is_connected = True
            logger.info(f"Connected to {self.port} at {self.baud_rate} baud")
            return True

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Disconnect from the device"""
        try:
            if self.serial and self.serial.is_open:
                self.serial.close()
            self.is_connected = False
            logger.info("Disconnected from device")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            raise

    def send_custom_command(self, command):
        """Send a custom SCPI command"""
        try:
            if not self.is_connected or not self.serial:
                return {
                    'success': False,
                    'command': command,
                    'response': None,
                    'error': 'Device not connected'
                }

            # Add newline if not present
            if not command.endswith('\n'):
                command += '\n'

            # Send command
            self.serial.write(command.encode())
            
            # Read response if command ends with '?'
            if '?' in command:
                response = self.serial.readline().decode().strip()
                return {
                    'success': True,
                    'command': command.strip(),
                    'response': response,
                    'error': None
                }
            
            return {
                'success': True,
                'command': command.strip(),
                'response': 'OK',
                'error': None
            }

        except Exception as e:
            logger.error(f"Error sending command '{command}': {e}")
            return {
                'success': False,
                'command': command,
                'response': None,
                'error': str(e)
            }

    def query(self, command):
        """Send a query command and return the response"""
        result = self.send_custom_command(command)
        if result['success']:
            return result['response']
        raise Exception(result['error'])
