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
        self.data_buffer = []  # Buffer for incoming CV data

    def connect(self):
        """Connect to the device"""
        try:
            # Check if already connected
            if self.is_connected:
                return True

            # Check if port exists
            import serial.tools.list_ports
            available_ports = [p.device for p in serial.tools.list_ports.comports()]
            if self.port not in available_ports:
                raise Exception(f"Port {self.port} not found")

            # Check if port is in use
            try:
                temp_serial = serial.Serial(self.port)
                temp_serial.close()
            except:
                raise Exception(f"Port {self.port} is in use")

            # Try to connect with timeout and retries
            max_retries = 3
            retry_delay = 1  # seconds
            
            for attempt in range(max_retries):
                try:
                    self.serial = serial.Serial(
                        port=self.port,
                        baudrate=self.baud_rate,
                        timeout=1
                    )
                    self.is_connected = True
                    logger.info(f"Connected to {self.port} at {self.baud_rate} baud")
                    return True
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                        time.sleep(retry_delay)
                    else:
                        raise

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Disconnect from the device"""
        try:
            if self.serial and self.serial.is_open:
                # Flush buffers before closing
                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
                self.serial.close()

            self.is_connected = False
            self.serial = None

            # Wait for port to be fully released
            time.sleep(1)
            logger.info("Disconnected from device")

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            # Even if there's an error, mark as disconnected
            self.is_connected = False 
            self.serial = None
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
    
    def get_buffered_data(self):
        """Get any buffered data that came from STM32 automatically"""
        try:
            if not self.is_connected or not self.serial or not self.serial.is_open:
                return None
                
            # Check if there's any data waiting in the serial buffer
            if self.serial.in_waiting > 0:
                # Read all available data
                raw_data = self.serial.read_all()
                if raw_data:
                    incoming_data = raw_data.decode('utf-8', errors='ignore')
                    if incoming_data.strip():
                        logger.debug(f"Received buffered data: '{incoming_data.strip()}'")
                        return incoming_data
                    
            return None
            
        except Exception as e:
            logger.error(f"Error reading buffered data: {e}")
            return None
    
    def clear_buffer(self):
        """Clear the serial input buffer"""
        try:
            if self.serial and self.serial.is_open:
                self.serial.reset_input_buffer()
                self.data_buffer.clear()
        except Exception as e:
            logger.error(f"Error clearing buffer: {e}")
    
    def has_data_available(self):
        """Check if there's data available in the buffer"""
        try:
            if self.serial and self.serial.is_open:
                return self.serial.in_waiting > 0
            return False
        except Exception as e:
            logger.error(f"Error checking data availability: {e}")
            return False
