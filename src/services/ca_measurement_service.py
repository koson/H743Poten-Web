"""
CA Measurement Service for H743Poten Web Interface
Handles Chronoamperometry measurements with real-time data streaming
"""

import time
import threading
import logging
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class CAParameters:
    """CA measurement parameters"""
    initial_potential: float    # Initial potential before step (V)
    step_potential: float       # Step potential to apply (V)
    duration: float             # Total measurement duration (s)
    sampling_interval: float    # Time between data points (s)
    
    def validate(self) -> Tuple[bool, str]:
        """Validate CA parameters"""
        if self.duration <= 0:
            return False, "Duration must be positive"
            
        if self.sampling_interval <= 0:
            return False, "Sampling interval must be positive"
            
        if self.sampling_interval >= self.duration:
            return False, "Sampling interval must be less than duration"
            
        if self.duration > 3600:  # 1 hour max
            return False, "Duration too long (max 1 hour)"
            
        return True, "Parameters valid"
    
    def get_scpi_commands(self) -> List[str]:
        """Get multiple SCPI commands needed for CA setup
        
        CA requires multiple commands:
        1. POTEn:CA:VOLT:INIT {initial_potential}
        2. POTEn:CA:VOLT:STEP {step_potential}
        3. POTEn:CA:TIME:DURation {duration}
        4. POTEn:CA:TIME:INTerval {sampling_interval}
        5. POTEn:CA:STARt
        """
        return [
            f"POTEn:CA:VOLT:INIT {self.initial_potential}",
            f"POTEn:CA:VOLT:STEP {self.step_potential}",
            f"POTEn:CA:TIME:DURation {self.duration}",
            f"POTEn:CA:TIME:INTerval {self.sampling_interval}",
            "POTEn:CA:STARt"
        ]

@dataclass  
class CADataPoint:
    """Single CA data point"""
    timestamp: float
    time_elapsed: float     # Time since step applied (s)
    potential: float        # Applied potential (V)
    current: float          # Measured current (µA)
    sample_number: int      # Sample number in sequence

class CAMeasurementService:
    """Service for managing CA measurements"""
    
    def __init__(self, scpi_handler):
        self.scpi_handler = scpi_handler
        self.is_measuring = False
        self.is_paused = False
        self.measurement_thread = None
        self.data_points: List[CADataPoint] = []
        self.current_params: Optional[CAParameters] = None
        self.start_time: Optional[float] = None
        self.step_start_time: Optional[float] = None
        self.last_data_time: Optional[float] = None
        self.data_timeout = 30.0  # seconds
        self.current_potential = 0.0
        self.last_validated_current = None
        self.sample_number = 0
        
        # CA specific settings
        self.enable_data_filtering = True
        self.debug_mode = False

    def setup_measurement(self, params_dict: Dict) -> bool:
        """Setup CA measurement with parameters"""
        try:
            # Convert dict to CAParameters
            params = CAParameters(
                initial_potential=float(params_dict.get('initial_potential', 0.0)),
                step_potential=float(params_dict.get('step_potential', 0.5)),
                duration=float(params_dict.get('duration', 10.0)),
                sampling_interval=float(params_dict.get('sampling_interval', 0.01))
            )
            
            # Validate parameters
            is_valid, message = params.validate()
            if not is_valid:
                logger.error(f"Invalid CA parameters: {message}")
                return False
                
            self.current_params = params
            self.current_potential = params.initial_potential
            
            logger.info(f"CA measurement setup successful: {params}")
            return True
            
        except Exception as e:
            logger.error(f"Error in CA setup_measurement: {e}")
            return False

    def start_measurement(self) -> bool:
        """Start CA measurement"""
        try:
            if not self.current_params:
                raise ValueError("No CA parameters set")

            # Clear previous data
            self.data_points.clear()
            self.start_time = time.time()
            self.step_start_time = None
            self.last_data_time = None
            self.sample_number = 0
            
            # Send CA setup commands to STM32
            commands = self.current_params.get_scpi_commands()
            
            for i, cmd in enumerate(commands):
                logger.info(f"Sending CA command {i+1}/{len(commands)} to STM32: {cmd}")
                result = self.scpi_handler.send_custom_command(cmd)
                if not result['success']:
                    logger.error(f"Failed to send CA command '{cmd}': {result['error']}")
                    return False
                
                # Small delay between commands
                time.sleep(0.1)
            
            self.is_measuring = True
            self.step_start_time = time.time()  # Record when step was applied
            logger.info(f"Started CA measurement with {len(commands)} commands")
            
            return True

        except Exception as e:
            logger.error(f"Error in CA start_measurement: {e}")
            return False

    def stop_measurement(self) -> bool:
        """Stop CA measurement"""
        try:
            # Use generic abort command for CA
            command = "POTEn:ABORt"
            result = self.scpi_handler.send_custom_command(command)

            if not result['success']:
                raise Exception(f"Failed to stop CA measurement: {result['error']}")

            self.is_measuring = False
            logger.info(f"Stopped CA measurement using {command}")
            return True

        except Exception as e:
            logger.error(f"Error in CA stop_measurement: {e}")
            return False

    def get_measurement_data(self) -> Dict:
        """Get current CA measurement data"""
        try:
            if not self.current_params:
                logger.debug("No CA measurement mode set, returning empty data")
                return {'points': [], 'completed': False}

            # Check for buffered data from STM32
            buffered_data = self.scpi_handler.get_buffered_data()
            if buffered_data:
                logger.info(f"Found buffered CA data from STM32: {len(buffered_data)} characters")
                parsed_data = self._parse_measurement_data(buffered_data)
                if parsed_data['points']:
                    logger.info(f"Parsed {len(parsed_data['points'])} CA points from buffered data")
                    return parsed_data
            
            # If no buffered data, try regular query
            command = "POTEn:CA:DATA?"
            result = self.scpi_handler.send_custom_command(command)

            if not result['success']:
                logger.debug(f"CA data query failed: {result['error']}")
                return {'points': [], 'completed': False, 'status': 'collecting'}

            # Parse the data response
            data = self._parse_measurement_data(result['response'])
            
            # Check if measurement is completed by time
            if self.step_start_time and self.current_params:
                elapsed_time = time.time() - self.step_start_time
                if elapsed_time >= self.current_params.duration:
                    logger.info(f"CA measurement completed by duration: {elapsed_time:.1f}s >= {self.current_params.duration}s")
                    self.is_measuring = False
                    completed_data = dict(data)
                    completed_data['completed'] = True
                    return completed_data
            
            return data

        except Exception as e:
            logger.error(f"Error in CA get_measurement_data: {e}")
            return {'points': [], 'completed': False, 'error': str(e)}

    def _parse_measurement_data(self, response: str) -> Dict:
        """Parse CA measurement data from SCPI response"""
        try:
            if not response or not response.strip():
                return {'points': [], 'completed': False}

            points = []
            lines = response.strip().split('\n')
            completed = False
            data_processed = False
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                # Check for completion indicators
                if 'COMPLETE' in line.upper() or 'END' in line.upper():
                    completed = True
                    continue
                
                try:
                    parts = [part.strip() for part in line.split(',')]
                    logger.debug(f"Parsed CA data parts: {parts}")
                    
                    # CA format: "CA, time_ms, elapsed_time, voltage, current, sample_number, ..."
                    if len(parts) >= 6 and parts[0].strip() == 'CA':
                        time_ms = float(parts[1].strip())
                        elapsed_time = float(parts[2].strip())  # Time since step applied
                        potential = float(parts[3].strip())
                        current_ua = float(parts[4].strip())
                        sample_num = int(parts[5].strip())
                        
                        # Keep in µA (no conversion)
                        current = current_ua
                        
                        logger.info(f"STM32 CA Data: t={elapsed_time:.3f}s, V={potential:.3f}V, I={current:.1f}µA, Sample={sample_num}, Time={time_ms}ms")
                        
                        # Data validation and filtering
                        should_filter = False
                        
                        if self.enable_data_filtering and not self.debug_mode:
                            if hasattr(self, 'last_validated_current') and self.last_validated_current is not None:
                                current_jump = abs(current - self.last_validated_current)
                                if current_jump > 1000:  # 1000µA = 1mA threshold
                                    logger.warning(f"Filtered EXTREME CA current spike: {current_jump:.1f}µA")
                                    should_filter = True
                                elif current_jump > 100:  # 100µA threshold
                                    logger.debug(f"Large CA current spike detected: {current_jump:.1f}µA (allowing)")
                        
                        if not should_filter:
                            # Create data point
                            timestamp = time_ms / 1000.0 if self.start_time else time.time()
                            
                            data_point = CADataPoint(
                                timestamp=timestamp,
                                time_elapsed=elapsed_time,
                                potential=potential,
                                current=current,
                                sample_number=sample_num
                            )
                            
                            self.data_points.append(data_point)
                            logger.info(f"✅ ADDED CA data point #{len(self.data_points)}: t={elapsed_time:.3f}s, I={current:.1f}µA")
                            
                            # Convert to dict for JSON serialization
                            points.append({
                                'timestamp': timestamp,
                                'time_elapsed': elapsed_time,
                                'potential': potential,
                                'current': current,
                                'sample_number': sample_num,
                                'mode': 'CA'
                            })
                            
                            self.last_validated_current = current
                            self.last_data_time = time.time()
                            self.sample_number = sample_num
                        
                        data_processed = True
                        
                    else:
                        logger.warning(f"Invalid CA data format: {line}")
                        continue
                        
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse CA data line '{line}': {e}")
                    continue

            result = {
                'points': points,
                'completed': completed
            }
                
            if points:
                logger.debug(f"Parsed {len(points)} CA data points from STM32")
            
            return result

        except Exception as e:
            logger.error(f"Error parsing CA measurement data: {e}")
            return {'points': [], 'completed': False, 'error': str(e)}

    def get_status(self) -> Dict:
        """Get current CA measurement status"""
        elapsed_time = 0.0
        progress_percent = 0.0
        expected_samples = 0
        
        if self.step_start_time and self.current_params:
            elapsed_time = time.time() - self.step_start_time
            progress_percent = min(100.0, (elapsed_time / self.current_params.duration) * 100)
            expected_samples = int(self.current_params.duration / self.current_params.sampling_interval)
            
        return {
            'mode': 'CA',
            'is_measuring': self.is_measuring,
            'is_paused': self.is_paused,
            'data_points': len(self.data_points),
            'current_sample': self.sample_number,
            'expected_samples': expected_samples,
            'elapsed_time': elapsed_time,
            'progress_percent': progress_percent,
            'current_potential': self.current_potential,
            'parameters': {
                'initial_potential': self.current_params.initial_potential if self.current_params else None,
                'step_potential': self.current_params.step_potential if self.current_params else None,
                'duration': self.current_params.duration if self.current_params else None,
                'sampling_interval': self.current_params.sampling_interval if self.current_params else None,
            }
        }

    def export_data(self) -> Dict:
        """Export CA measurement data"""
        if not self.data_points:
            return {'success': False, 'message': 'No data to export'}
        
        try:
            # Prepare export data
            export_data = {
                'measurement_type': 'CA',
                'timestamp': datetime.now().isoformat(),
                'parameters': self.get_status()['parameters'],
                'data_points': len(self.data_points),
                'data': []
            }
            
            for point in self.data_points:
                export_data['data'].append({
                    'timestamp': point.timestamp,
                    'time_elapsed_s': point.time_elapsed,
                    'potential_V': point.potential,
                    'current_uA': point.current,
                    'sample_number': point.sample_number
                })
            
            return {'success': True, 'data': export_data}
            
        except Exception as e:
            logger.error(f"Error exporting CA data: {e}")
            return {'success': False, 'message': str(e)}