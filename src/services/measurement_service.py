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

            # For CV, DPV, SWV: setup_measurement already sent the Start:ALL command
            if self.current_mode in ['CV', 'DPV', 'SWV']:
                # The Start:ALL command was already sent in setup, just mark as measuring
                self.is_measuring = True
                logger.info(f"Started {self.current_mode} measurement (via Start:ALL command)")
                return True
                
            elif self.current_mode == 'CA':
                # CA requires multiple setup commands then start
                params = self.current_params
                
                # Send all CA setup commands
                commands = [
                    f"POTEn:CA:VOLT:INIT {params.get('initial_voltage', 0.0)}",
                    f"POTEn:CA:VOLT:STEP {params.get('voltage', 0.5)}",
                    f"POTEn:CA:TIME:DURation {params.get('duration', 10.0)}",
                    f"POTEn:CA:TIME:INTerval {params.get('interval', 0.01)}",
                    "POTEn:CA:STARt"
                ]
                
                for cmd in commands:
                    result = self.scpi_handler.send_custom_command(cmd)
                    if not result['success']:
                        raise Exception(f"Failed to send CA command '{cmd}': {result['error']}")
                        
                self.is_measuring = True
                logger.info(f"Started {self.current_mode} measurement with multiple commands")
                return True
            else:
                # Fallback for other modes
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
            # Use ABORT command that hardware actually supports
            if self.current_mode == 'CV':
                command = "POTEn:ABORt"  # CV uses generic abort
            elif self.current_mode == 'DPV':
                command = "POTEn:DPV:ABORt"
            elif self.current_mode == 'SWV':
                command = "POTEn:SWV:ABORt"
            else:
                # Fallback to generic abort
                command = "POTEn:ABORt"
                
            result = self.scpi_handler.send_custom_command(command)

            if not result['success']:
                raise Exception(f"Failed to stop measurement: {result['error']}")

            self.is_measuring = False
            logger.info(f"Stopped {self.current_mode} measurement using {command}")
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
        """Build SCPI command for measurement setup based on real hardware SCPI commands"""
        if mode == 'CV':
            # Use POTEn:CV:Start:ALL command that hardware actually supports
            # Format: POTEn:CV:Start:ALL {LowerVoltage},{UpperVoltage},{BeginVoltage},{SweepRate},{NumCycles}
            lower_v = params.get('start_voltage', -0.5)
            upper_v = params.get('end_voltage', 0.5) 
            begin_v = lower_v  # Start from lower voltage
            rate = params.get('scan_rate', 0.05)
            cycles = params.get('cycles', 1)
            return f"POTEn:CV:Start:ALL {lower_v},{upper_v},{begin_v},{rate},{cycles}"
            
        elif mode == 'DPV':
            # Use POTEn:DPV:Start:ALL command that hardware actually supports
            # Format: POTEn:DPV:Start:ALL {InitialPotential},{FinalPotential},{PulseHeight},{PulseIncrement},{PulseWidth},{PulsePeriod}
            init_v = params.get('start_voltage', -0.5)
            final_v = params.get('end_voltage', 0.5)
            pulse_height = params.get('pulse_amplitude', 0.05)
            pulse_incr = params.get('step_size', 0.01)
            pulse_width = params.get('pulse_width', 0.05)
            pulse_period = params.get('period', 0.1)
            return f"POTEn:DPV:Start:ALL {init_v},{final_v},{pulse_height},{pulse_incr},{pulse_width},{pulse_period}"
            
        elif mode == 'SWV':
            # Use POTEn:SWV:Start:ALL command that hardware actually supports  
            # Format: POTEn:SWV:Start:ALL {Frequency},{Amplitude},{StepPotential},{StartPotential},{EndPotential}
            freq = params.get('frequency', 100)
            amplitude = params.get('amplitude', 0.05)
            step = params.get('step_size', 0.01)
            start_v = params.get('start_voltage', -0.5)
            end_v = params.get('end_voltage', 0.5)
            return f"POTEn:SWV:Start:ALL {freq},{amplitude},{step},{start_v},{end_v}"
            
        elif mode == 'CA':
            # For CA mode, use individual parameter setup commands then start
            # This requires multiple commands since there's no Start:ALL for CA
            init_v = params.get('initial_voltage', 0.0)
            step_v = params.get('voltage', 0.5) 
            duration = params.get('duration', 10.0)
            interval = params.get('interval', 0.01)
            
            # Return first command, we'll need to handle multiple commands differently
            return f"POTEn:CA:VOLT:INIT {init_v}"
            
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
