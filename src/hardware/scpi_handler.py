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
                logger.info(f"Already connected to {self.port}")
                return True

            # Debug: Check available ports
            import serial.tools.list_ports
            import os
            
            available_ports = [p.device for p in serial.tools.list_ports.comports()]
            logger.info(f"Available ports: {available_ports}")
            logger.info(f"Trying to connect to: {self.port}")
            
            # Check if port file exists (more reliable than port enumeration)
            if not os.path.exists(self.port):
                raise Exception(f"Port device file {self.port} not found")
            
            # Check if port is accessible
            if not os.access(self.port, os.R_OK | os.W_OK):
                raise Exception(f"Port {self.port} is not accessible (permission denied)")

            # Skip slow port availability check - connect directly
            logger.info(f"🚀 Fast connect to {self.port}...")
            
            # Direct connection with minimal timeout
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=0.5,  # Reduced timeout for faster response
                write_timeout=0.5,  # Write timeout to prevent hanging
                rtscts=False,  # Disable flow control for speed
                dsrdtr=False   # Disable DTR/DSR for speed
            )
            
            # Quick connection verification
            if self.serial.is_open:
                self.is_connected = True
                print(f"⚡ FAST connect to {self.port} at {self.baud_rate} baud - Ready!")
                logger.info(f"Fast connected to {self.port} at {self.baud_rate} baud")
                
                # Quick flush to clear any old data
                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
                return True
            else:
                raise Exception("Serial port failed to open")

        except Exception as e:
            logger.error(f"Failed to connect to {self.port}: {e}")
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
            # Don't raise - allow graceful disconnect even with errors

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

            # Add proper SCPI termination if not present
            # STM32 requires \r\n termination for SCPI commands
            if not command.endswith('\r\n'):
                if command.endswith('\n'):
                    command = command[:-1] + '\r\n'
                elif command.endswith('\r'):
                    command = command + '\n'
                else:
                    command += '\r\n'

            # Send command
            logger.debug(f"Sending SCPI command: '{command.strip()}' (with \\r\\n)")
            self.serial.write(command.encode())
            
            # Read response if command ends with '?'
            if '?' in command:
                # Quick response read with short timeout
                self.serial.timeout = 0.2  # Very short timeout for fast response
                response = self.serial.readline().decode().strip()
                self.serial.timeout = 0.5  # Reset to default
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
            try:
                if self.serial.in_waiting > 0:
                    # Read all available data with timeout protection
                    raw_data = self.serial.read_all()
                    if raw_data:
                        incoming_data = raw_data.decode('utf-8', errors='ignore')
                        if incoming_data.strip():
                            logger.debug(f"Received buffered data: '{incoming_data.strip()}'")
                            return incoming_data
            except (OSError, PermissionError) as com_error:
                # Windows COM port access errors - don't spam logs
                if "ClearCommError" in str(com_error) or "The device does not recognize the command" in str(com_error):
                    logger.debug(f"COM port access issue (suppressed): {com_error}")
                else:
                    logger.warning(f"COM port error: {com_error}")
                return None
                    
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
