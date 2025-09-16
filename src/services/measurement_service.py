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
        """Get current measurement data with improved STM32 handling"""
        try:
            if not self.current_mode:
                logger.debug("No measurement mode set, returning empty data")
                return {'points': [], 'completed': False}

            # First check if there's buffered data from STM32
            buffered_data = self.scpi_handler.get_buffered_data()
            if buffered_data:
                logger.info(f"Found buffered data from STM32: {len(buffered_data)} characters")
                # Parse buffered data if available
                parsed_data = self._parse_measurement_data(buffered_data)
                if parsed_data['points']:
                    logger.info(f"Parsed {len(parsed_data['points'])} points from buffered data")
                    return parsed_data
            
            # If no buffered data, try regular query
            command = f"POTEn:{self.current_mode}:DATA?"
            result = self.scpi_handler.send_custom_command(command)

            if not result['success']:
                logger.debug(f"Data query failed: {result['error']}")
                # Don't treat this as an error - STM32 might still be collecting data
                return {'points': [], 'completed': False, 'status': 'collecting'}

            # Parse the data response
            data = self._parse_measurement_data(result['response'])
            
            # Check if measurement is completed
            if not data['points'] and self.is_measuring:
                # Try to check measurement status
                status_command = f"POTEn:{self.current_mode}:STATUS?"
                status_result = self.scpi_handler.send_custom_command(status_command)
                if status_result['success'] and 'COMPLETE' in status_result['response'].upper():
                    logger.info(f"Measurement {self.current_mode} completed")
                    self.is_measuring = False
                    # Create new dict to avoid type issues
                    completed_data = dict(data)
                    completed_data['completed'] = True
                    return completed_data
            
            return data

        except Exception as e:
            logger.error(f"Error in get_measurement_data: {e}")
            # Return empty data instead of failing completely
            return {'points': [], 'completed': False, 'error': str(e)}

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
        """Parse measurement data from SCPI response with improved STM32 handling"""
        try:
            if not response or not response.strip():
                return {'points': [], 'completed': False}

            # Basic CSV parsing (adjust based on your data format)
            points = []
            lines = response.strip().split('\n')
            completed = False
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):  # Skip empty lines and comments
                    continue
                    
                # Check for completion indicators
                if 'COMPLETE' in line.upper() or 'END' in line.upper():
                    completed = True
                    continue
                    
                values = line.split(',')
                if len(values) >= 2:
                    try:
                        point = {
                            'timestamp': float(values[0]) if len(values) > 0 else 0,
                            'voltage': float(values[1]) if len(values) > 1 else 0,
                            'current': float(values[2]) if len(values) > 2 else 0,
                            'mode': self.current_mode or 'UNKNOWN'
                        }
                        points.append(point)
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse data line '{line}': {e}")
                        continue

            result = {
                'points': points,
                'completed': completed
            }
                
            if points:
                logger.debug(f"Parsed {len(points)} data points from STM32")
            
            return result

        except Exception as e:
            logger.error(f"Error parsing measurement data: {e}")
            return {'points': [], 'completed': False, 'error': str(e)}
