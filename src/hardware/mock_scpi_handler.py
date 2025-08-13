"""
Mock SCPI Handler for development and testing
Enhanced with CSV data emulation support
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
    from .csv_data_emulator import CSVDataEmulator
except ImportError:
    # Fall back to absolute imports (when run directly)
    try:
        from config.settings import Config
        from hardware.csv_data_emulator import CSVDataEmulator
    except ImportError:
        # Last resort for test script
        import sys
        import os
        sys.path.insert(0, os.path.dirname(__file__))
        from csv_data_emulator import CSVDataEmulator
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
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
        self._measurement_mode = None
        
        # CSV Data Emulator
        self.csv_emulator = CSVDataEmulator()
        self._use_csv_data = False
        
        # Simulation parameters
        self._simulation_params = {
            'noise_level': 0.0001,
            'signal_amplitude': 0.5,
            'signal_frequency': 0.1
        }

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
        """Simulate sending a custom SCPI command with CSV emulation support"""
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
            
            # Basic device commands
            if command == '*idn?':
                response = "H743Poten,MOCK,v1.0"
            elif 'poten:info?' in command:
                response = "H743Poten Mock Device,HW:v1.0,FW:v1.0,SN:MOCK001"
            elif 'poten:stat?' in command:
                if self._measurement_running:
                    response = "RUNNING"
                else:
                    response = "IDLE"
                    
            # CSV Emulator commands
            elif 'csv:load' in command:
                # Command format: csv:load /path/to/file.csv
                parts = command.split(' ', 1)
                if len(parts) > 1:
                    file_path = parts[1].strip()
                    success = self.csv_emulator.load_csv_file(file_path)
                    response = "OK" if success else "ERROR: Failed to load CSV file"
                else:
                    response = "ERROR: File path required"
                    
            elif 'csv:start' in command:
                # Command format: csv:start [speed] [loop]
                parts = command.split()
                speed = 1.0
                loop = False
                
                if len(parts) > 1:
                    try:
                        speed = float(parts[1])
                    except ValueError:
                        pass
                        
                if len(parts) > 2:
                    loop = parts[2].lower() in ['true', '1', 'yes', 'loop']
                
                success = self.csv_emulator.start_emulation(speed, loop)
                if success:
                    self._measurement_running = True
                    self._use_csv_data = True
                    self._measurement_mode = 'CSV'
                    response = "OK"
                else:
                    response = "ERROR: Failed to start CSV emulation"
                    
            elif 'csv:stop' in command:
                self.csv_emulator.stop_emulation()
                self._measurement_running = False
                self._use_csv_data = False
                response = "OK"
                
            elif 'csv:info?' in command:
                info = self.csv_emulator.get_data_info()
                if info['loaded']:
                    response = f"CSV:{info['total_points']},{info['time_range']['duration']:.3f},{info['file_path']}"
                else:
                    response = "CSV:NOT_LOADED"
                    
            elif 'csv:progress?' in command:
                progress = self.csv_emulator.get_progress()
                response = (f"PROGRESS:{progress['current_index']},{progress['total_points']},"
                          f"{progress['progress_percent']:.1f},{progress['elapsed_time']:.3f}")
                          
            elif 'csv:seek' in command:
                # Command format: csv:seek 10.5 (seek to 10.5 seconds)
                parts = command.split()
                if len(parts) > 1:
                    try:
                        target_time = float(parts[1])
                        success = self.csv_emulator.seek_to_time(target_time)
                        response = "OK" if success else "ERROR: Seek failed"
                    except ValueError:
                        response = "ERROR: Invalid time format"
                else:
                    response = "ERROR: Time required"
                    
            # Measurement control commands
            elif ':start' in command:
                if 'csv' in command:
                    # CSV emulation start
                    success = self.csv_emulator.start_emulation()
                    if success:
                        self._measurement_running = True
                        self._use_csv_data = True
                        self._measurement_mode = 'CSV'
                    response = "OK" if success else "ERROR"
                else:
                    # Standard mock measurement
                    self._start_mock_measurement()
                    # Extract measurement mode from command
                    if 'cv' in command:
                        self._measurement_mode = 'CV'
                    elif 'dpv' in command:
                        self._measurement_mode = 'DPV'
                    elif 'swv' in command:
                        self._measurement_mode = 'SWV'
                    elif 'ca' in command:
                        self._measurement_mode = 'CA'
                    response = "OK"
                    
            elif ':stop' in command:
                if self._use_csv_data:
                    self.csv_emulator.stop_emulation()
                    self._use_csv_data = False
                self._measurement_running = False
                response = "OK"
                
            elif ':data?' in command:
                response = self._generate_data()
                
            # Setup commands  
            elif ':setup' in command:
                # Store measurement mode for data generation
                if 'cv' in command:
                    self._measurement_mode = 'CV'
                elif 'dpv' in command:
                    self._measurement_mode = 'DPV'
                elif 'swv' in command:
                    self._measurement_mode = 'SWV'
                elif 'ca' in command:
                    self._measurement_mode = 'CA'
                response = "OK"
                
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

    def _generate_data(self):
        """Generate measurement data - either from CSV or mock simulation"""
        if self._use_csv_data:
            return self._generate_csv_data()
        else:
            return self._generate_mock_data()
    
    def _generate_csv_data(self):
        """Generate data from CSV emulator"""
        if not self._measurement_running:
            return ""
            
        data_points = self.csv_emulator.get_current_data()
        if not data_points:
            return ""
            
        # Format data as CSV string
        data_lines = []
        for point in data_points:
            line = f"{point['timestamp']:.6f},{point['voltage']:.6f},{point['current']:.9f}"
            data_lines.append(line)
            
    def _generate_mock_data(self):
        """Generate mock measurement data based on measurement mode"""
        if not self._measurement_running or not self._time_start:
            return ""

        current_time = time.time()
        elapsed_time = current_time - self._time_start
        num_points = int(elapsed_time * 10)  # Generate 10 points per second

        data = []
        for i in range(num_points):
            t = i / 10.0
            
            # Generate data based on measurement mode
            if self._measurement_mode == 'CV':
                # Cyclic Voltammetry simulation
                voltage = self._simulation_params['signal_amplitude'] * math.sin(2 * math.pi * self._simulation_params['signal_frequency'] * t)
                current = voltage * 0.001 + random.uniform(-self._simulation_params['noise_level'], self._simulation_params['noise_level'])
            elif self._measurement_mode == 'DPV':
                # Differential Pulse Voltammetry simulation
                voltage = t * 0.1  # Linear ramp
                pulse = 0.05 * math.sin(2 * math.pi * 5 * t)  # Pulse component
                voltage += pulse
                current = voltage * 0.0005 + random.uniform(-self._simulation_params['noise_level'], self._simulation_params['noise_level'])
            elif self._measurement_mode == 'SWV':
                # Square Wave Voltammetry simulation
                voltage = t * 0.1 + 0.02 * math.copysign(1, math.sin(2 * math.pi * 10 * t))
                current = voltage * 0.0008 + random.uniform(-self._simulation_params['noise_level'], self._simulation_params['noise_level'])
            elif self._measurement_mode == 'CA':
                # Chronoamperometry simulation
                voltage = 0.5  # Constant voltage
                current = 0.001 * math.exp(-t * 0.1) + random.uniform(-self._simulation_params['noise_level'], self._simulation_params['noise_level'])
            else:
                # Default simulation
                voltage = self._simulation_params['signal_amplitude'] * math.sin(2 * math.pi * self._simulation_params['signal_frequency'] * t)
                current = voltage * 0.001 + random.uniform(-self._simulation_params['noise_level'], self._simulation_params['noise_level'])
            
            data.append(f"{t:.6f},{voltage:.6f},{current:.9f}")

        return "\n".join(data)

    # CSV Emulator convenience methods
    def load_csv_data(self, file_path: str) -> bool:
        """Load CSV data for emulation"""
        return self.csv_emulator.load_csv_file(file_path)
    
    def start_csv_emulation(self, speed: float = 1.0, loop: bool = False) -> bool:
        """Start CSV data emulation"""
        success = self.csv_emulator.start_emulation(speed, loop)
        if success:
            self._measurement_running = True
            self._use_csv_data = True
            self._measurement_mode = 'CSV'
        return success
    
    def stop_csv_emulation(self):
        """Stop CSV data emulation"""
        self.csv_emulator.stop_emulation()
        self._measurement_running = False
        self._use_csv_data = False
    
    def get_csv_info(self):
        """Get CSV data information"""
        return self.csv_emulator.get_data_info()
    
    def get_csv_progress(self):
        """Get CSV playback progress"""
        return self.csv_emulator.get_progress()