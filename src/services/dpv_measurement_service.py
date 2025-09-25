"""
DPV Measurement Service for H743Poten Web Interface
Handles Differential Pulse Voltammetry measurements with real-time data streaming
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
class DPVParameters:
    """DPV measurement parameters"""
    initial_potential: float    # Starting potential (V)
    final_potential: float      # End potential (V) 
    pulse_height: float         # Pulse amplitude (V)
    pulse_increment: float      # Step size between pulses (V)
    pulse_width: float          # Pulse duration (s)
    pulse_period: float         # Time between pulses (s)
    
    def validate(self) -> Tuple[bool, str]:
        """Validate DPV parameters"""
        if self.final_potential == self.initial_potential:
            return False, "Final potential must be different from initial potential"
            
        if self.pulse_height <= 0:
            return False, "Pulse height must be positive"
            
        if self.pulse_increment <= 0:
            return False, "Pulse increment must be positive"
            
        if self.pulse_width <= 0:
            return False, "Pulse width must be positive"
            
        if self.pulse_period <= self.pulse_width:
            return False, "Pulse period must be greater than pulse width"
            
        return True, "Parameters valid"
    
    def to_scpi_command(self) -> str:
        """Convert parameters to SCPI command for STM32
        
        Format: POTEn:DPV:Start:ALL {InitialPotential},{FinalPotential},{PulseHeight},{PulseIncrement},{PulseWidth},{PulsePeriod}
        Example: POTEn:DPV:Start:ALL -0.5,0.5,0.05,0.01,0.05,0.1
        
        Parameters:
        - InitialPotential: Starting potential (V)
        - FinalPotential: End potential (V)
        - PulseHeight: Differential pulse amplitude (V)
        - PulseIncrement: Step size between pulses (V)
        - PulseWidth: Pulse duration (s)
        - PulsePeriod: Time between pulses (s)
        """
        return f"POTEn:DPV:Start:ALL {self.initial_potential},{self.final_potential},{self.pulse_height},{self.pulse_increment},{self.pulse_width},{self.pulse_period}"

@dataclass  
class DPVDataPoint:
    """Single DPV data point"""
    timestamp: float
    potential: float    # Applied potential (V)
    current: float      # Measured current (µA)
    pulse_number: int   # Current pulse number
    measurement_phase: str  # 'baseline' or 'pulse'

class DPVMeasurementService:
    """Service for managing DPV measurements"""
    
    def __init__(self, scpi_handler):
        self.scpi_handler = scpi_handler
        self.is_measuring = False
        self.is_paused = False
        self.measurement_thread = None
        self.data_points: List[DPVDataPoint] = []
        self.current_params: Optional[DPVParameters] = None
        self.start_time: Optional[float] = None
        self.last_data_time: Optional[float] = None
        self.data_timeout = 30.0  # seconds
        self.current_potential = 0.0
        self.last_validated_current = None
        self.pulse_number = 0
        
        # DPV specific settings
        self.enable_data_filtering = True
        self.debug_mode = False

    def setup_measurement(self, params_dict: Dict) -> bool:
        """Setup DPV measurement with parameters"""
        try:
            # Convert dict to DPVParameters
            params = DPVParameters(
                initial_potential=float(params_dict.get('initial_potential', -0.5)),
                final_potential=float(params_dict.get('final_potential', 0.5)),
                pulse_height=float(params_dict.get('pulse_height', 0.05)),
                pulse_increment=float(params_dict.get('pulse_increment', 0.01)),
                pulse_width=float(params_dict.get('pulse_width', 0.05)),
                pulse_period=float(params_dict.get('pulse_period', 0.1))
            )
            
            # Validate parameters
            is_valid, message = params.validate()
            if not is_valid:
                logger.error(f"Invalid DPV parameters: {message}")
                return False
                
            self.current_params = params
            self.current_potential = params.initial_potential
            
            # Send SCPI command to STM32
            command = self.current_params.to_scpi_command()
            logger.info(f"Sending DPV command to STM32: {command}")
            
            result = self.scpi_handler.send_custom_command(command)
            if not result['success']:
                logger.error(f"Failed to setup DPV measurement: {result['error']}")
                return False
            
            logger.info(f"DPV measurement setup successful: {params}")
            return True
            
        except Exception as e:
            logger.error(f"Error in DPV setup_measurement: {e}")
            return False

    def start_measurement(self) -> bool:
        """Start DPV measurement"""
        try:
            if not self.current_params:
                raise ValueError("No DPV parameters set")

            # Clear previous data
            self.data_points.clear()
            self.start_time = time.time()
            self.last_data_time = None
            self.pulse_number = 0
            
            # DPV uses Start:ALL command (already sent in setup)
            self.is_measuring = True
            logger.info(f"Started DPV measurement")
            
            return True

        except Exception as e:
            logger.error(f"Error in DPV start_measurement: {e}")
            return False

    def stop_measurement(self) -> bool:
        """Stop DPV measurement"""
        try:
            # Use DPV abort command
            command = "POTEn:DPV:ABORt"
            result = self.scpi_handler.send_custom_command(command)

            if not result['success']:
                raise Exception(f"Failed to stop DPV measurement: {result['error']}")

            self.is_measuring = False
            logger.info(f"Stopped DPV measurement using {command}")
            return True

        except Exception as e:
            logger.error(f"Error in DPV stop_measurement: {e}")
            return False

    def get_measurement_data(self) -> Dict:
        """Get current DPV measurement data"""
        try:
            if not self.current_params:
                logger.debug("No DPV measurement mode set, returning empty data")
                return {'points': [], 'completed': False}

            # Check for buffered data from STM32
            buffered_data = self.scpi_handler.get_buffered_data()
            if buffered_data:
                logger.info(f"Found buffered DPV data from STM32: {len(buffered_data)} characters")
                parsed_data = self._parse_measurement_data(buffered_data)
                if parsed_data['points']:
                    logger.info(f"Parsed {len(parsed_data['points'])} DPV points from buffered data")
                    return parsed_data
            
            # If no buffered data, try regular query
            command = "POTEn:DPV:DATA?"
            result = self.scpi_handler.send_custom_command(command)

            if not result['success']:
                logger.debug(f"DPV data query failed: {result['error']}")
                return {'points': [], 'completed': False, 'status': 'collecting'}

            # Parse the data response
            data = self._parse_measurement_data(result['response'])
            
            # Check if measurement is completed
            if not data['points'] and self.is_measuring:
                status_command = "POTEn:DPV:STATUS?"
                status_result = self.scpi_handler.send_custom_command(status_command)
                if status_result['success'] and 'COMPLETE' in status_result['response'].upper():
                    logger.info(f"DPV measurement completed")
                    self.is_measuring = False
                    completed_data = dict(data)
                    completed_data['completed'] = True
                    return completed_data
            
            return data

        except Exception as e:
            logger.error(f"Error in DPV get_measurement_data: {e}")
            return {'points': [], 'completed': False, 'error': str(e)}

    def _parse_measurement_data(self, response: str) -> Dict:
        """Parse DPV measurement data from SCPI response"""
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
                    logger.debug(f"Parsed DPV data parts: {parts}")
                    
                    # DPV format: "DPV, time_ms, voltage, current, pulse_number, phase, ..."
                    if len(parts) >= 6 and parts[0].strip() == 'DPV':
                        time_ms = float(parts[1].strip())
                        potential = float(parts[2].strip())
                        current_ua = float(parts[3].strip())
                        current = current_ua  # Keep in µA (no conversion)
                        pulse_num = int(parts[4].strip())
                        phase = parts[5].strip()  # 'baseline' or 'pulse'
                        
                        logger.info(f"STM32 DPV Data: V={potential:.3f}V, I={current:.1f}µA, Pulse={pulse_num}, Phase={phase}, Time={time_ms}ms")
                        
                        # Data validation and filtering
                        should_filter = False
                        
                        if self.enable_data_filtering and not self.debug_mode:
                            if hasattr(self, 'last_validated_current') and self.last_validated_current is not None:
                                current_jump = abs(current - self.last_validated_current)
                                if current_jump > 1000:  # 1000µA = 1mA threshold
                                    logger.warning(f"Filtered EXTREME DPV current spike: {current_jump:.1f}µA")
                                    should_filter = True
                                elif current_jump > 100:  # 100µA threshold
                                    logger.debug(f"Large DPV current spike detected: {current_jump:.1f}µA (allowing)")
                        
                        if not should_filter:
                            # Create data point
                            timestamp = time_ms / 1000.0 if self.start_time else time.time()
                            
                            data_point = DPVDataPoint(
                                timestamp=timestamp,
                                potential=potential,
                                current=current,
                                pulse_number=pulse_num,
                                measurement_phase=phase
                            )
                            
                            self.data_points.append(data_point)
                            logger.info(f"✅ ADDED DPV data point #{len(self.data_points)}: V={potential:.3f}V, I={current:.1f}µA")
                            
                            # Convert to dict for JSON serialization
                            points.append({
                                'timestamp': timestamp,
                                'potential': potential,
                                'current': current,
                                'pulse_number': pulse_num,
                                'measurement_phase': phase,
                                'mode': 'DPV'
                            })
                            
                            self.last_validated_current = current
                            self.last_data_time = time.time()
                            self.pulse_number = pulse_num
                        
                        data_processed = True
                        
                    else:
                        logger.warning(f"Invalid DPV data format: {line}")
                        continue
                        
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse DPV data line '{line}': {e}")
                    continue

            result = {
                'points': points,
                'completed': completed
            }
                
            if points:
                logger.debug(f"Parsed {len(points)} DPV data points from STM32")
            
            return result

        except Exception as e:
            logger.error(f"Error parsing DPV measurement data: {e}")
            return {'points': [], 'completed': False, 'error': str(e)}

    def get_status(self) -> Dict:
        """Get current DPV measurement status"""
        total_pulses = 0
        if self.current_params:
            voltage_range = abs(self.current_params.final_potential - self.current_params.initial_potential)
            total_pulses = int(voltage_range / self.current_params.pulse_increment) + 1
            
        return {
            'mode': 'DPV',
            'is_measuring': self.is_measuring,
            'is_paused': self.is_paused,
            'data_points': len(self.data_points),
            'current_pulse': self.pulse_number,
            'total_pulses': total_pulses,
            'current_potential': self.current_potential,
            'parameters': {
                'initial_potential': self.current_params.initial_potential if self.current_params else None,
                'final_potential': self.current_params.final_potential if self.current_params else None,
                'pulse_height': self.current_params.pulse_height if self.current_params else None,
                'pulse_increment': self.current_params.pulse_increment if self.current_params else None,
                'pulse_width': self.current_params.pulse_width if self.current_params else None,
                'pulse_period': self.current_params.pulse_period if self.current_params else None,
            }
        }

    def export_data(self) -> Dict:
        """Export DPV measurement data"""
        if not self.data_points:
            return {'success': False, 'message': 'No data to export'}
        
        try:
            # Prepare export data
            export_data = {
                'measurement_type': 'DPV',
                'timestamp': datetime.now().isoformat(),
                'parameters': self.get_status()['parameters'],
                'data_points': len(self.data_points),
                'data': []
            }
            
            for point in self.data_points:
                export_data['data'].append({
                    'timestamp': point.timestamp,
                    'potential_V': point.potential,
                    'current_uA': point.current,
                    'pulse_number': point.pulse_number,
                    'measurement_phase': point.measurement_phase
                })
            
            return {'success': True, 'data': export_data}
            
        except Exception as e:
            logger.error(f"Error exporting DPV data: {e}")
            return {'success': False, 'message': str(e)}