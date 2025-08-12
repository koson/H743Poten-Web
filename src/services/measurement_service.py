"""
Measurement service for handling potentiostat measurements
"""

import logging
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

class MeasurementService:
    def __init__(self, scpi_handler):
        self.scpi_handler = scpi_handler
        self.current_mode = None
        self.current_params = {}
        self.is_measuring = False

    def setup_measurement(self, mode, params):
        """Setup measurement with given mode and parameters"""
        try:
            mode = mode.upper()
            if mode not in Config.DEFAULT_PARAMS:
                raise ValueError(f"Invalid measurement mode: {mode}")

            self.current_mode = mode
            self.current_params = params

            # Construct and send SCPI command based on mode
            command = self._build_setup_command(mode, params)
            result = self.scpi_handler.send_custom_command(command)

            if not result['success']:
                raise Exception(f"Failed to setup measurement: {result['error']}")

            logger.info(f"Measurement setup successful: {mode} with params {params}")
            return True

        except Exception as e:
            logger.error(f"Error in setup_measurement: {e}")
            return False

    def start_measurement(self):
        """Start the current measurement"""
        try:
            if not self.current_mode:
                raise ValueError("No measurement mode set")

            command = f"POTEn:{self.current_mode}:START"
            result = self.scpi_handler.send_custom_command(command)

            if not result['success']:
                raise Exception(f"Failed to start measurement: {result['error']}")

            self.is_measuring = True
            logger.info(f"Started {self.current_mode} measurement")
            return True

        except Exception as e:
            logger.error(f"Error in start_measurement: {e}")
            return False

    def stop_measurement(self):
        """Stop the current measurement"""
        try:
            command = f"POTEn:{self.current_mode}:STOP"
            result = self.scpi_handler.send_custom_command(command)

            if not result['success']:
                raise Exception(f"Failed to stop measurement: {result['error']}")

            self.is_measuring = False
            logger.info(f"Stopped {self.current_mode} measurement")
            return True

        except Exception as e:
            logger.error(f"Error in stop_measurement: {e}")
            return False

    def get_status(self):
        """Get current measurement status"""
        return {
            'mode': self.current_mode,
            'params': self.current_params,
            'is_measuring': self.is_measuring
        }

    def get_measurement_data(self):
        """Get current measurement data"""
        try:
            if not self.current_mode:
                return {'points': []}

            command = f"POTEn:{self.current_mode}:DATA?"
            result = self.scpi_handler.send_custom_command(command)

            if not result['success']:
                raise Exception(f"Failed to get measurement data: {result['error']}")

            # Parse the data response
            # Implement parsing logic based on your data format
            data = self._parse_measurement_data(result['response'])
            return data

        except Exception as e:
            logger.error(f"Error in get_measurement_data: {e}")
            return {'points': []}

    def _build_setup_command(self, mode, params):
        """Build SCPI command for measurement setup"""
        if mode == 'CV':
            return (f"POTEn:CV:SETUP "
                   f"{params.get('start_voltage', -0.5)},"
                   f"{params.get('end_voltage', 0.5)},"
                   f"{params.get('scan_rate', 0.05)},"
                   f"{params.get('step_size', 0.01)}")
        elif mode == 'DPV':
            return (f"POTEn:DPV:SETUP "
                   f"{params.get('start_voltage', -0.5)},"
                   f"{params.get('end_voltage', 0.5)},"
                   f"{params.get('pulse_amplitude', 0.05)},"
                   f"{params.get('pulse_width', 0.01)},"
                   f"{params.get('step_size', 0.01)},"
                   f"{params.get('period', 0.1)}")
        elif mode == 'SWV':
            return (f"POTEn:SWV:SETUP "
                   f"{params.get('start_voltage', -0.5)},"
                   f"{params.get('end_voltage', 0.5)},"
                   f"{params.get('amplitude', 0.05)},"
                   f"{params.get('frequency', 10)},"
                   f"{params.get('step_size', 0.01)}")
        elif mode == 'CA':
            return (f"POTEn:CA:SETUP "
                   f"{params.get('voltage', 0.5)},"
                   f"{params.get('duration', 10)}")
        else:
            raise ValueError(f"Invalid measurement mode: {mode}")

    def _parse_measurement_data(self, response):
        """Parse measurement data from SCPI response"""
        try:
            if not response:
                return {'points': []}

            # Basic CSV parsing (adjust based on your data format)
            points = []
            lines = response.strip().split('\n')
            for line in lines:
                values = line.split(',')
                if len(values) >= 2:
                    points.append({
                        'timestamp': float(values[0]),
                        'voltage': float(values[1]),
                        'current': float(values[2]) if len(values) > 2 else 0,
                        'mode': self.current_mode
                    })

            return {'points': points}

        except Exception as e:
            logger.error(f"Error parsing measurement data: {e}")
            return {'points': []}
