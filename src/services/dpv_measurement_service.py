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
        
        Parameters (matching STM32 firmware exactly):
        - InitialPotential: Starting potential (V)
        - FinalPotential: End potential (V)  
        - PulseHeight: Differential pulse amplitude (V)
        - PulseIncrement: Step size between pulses (V)
        - PulseWidth: Pulse duration (s)
        - PulsePeriod: Time between pulses (s)
        """
        # ✅ CONFIRMED: POTEn:DPV:Start:ALL format works with real STM32 hardware
        # Tested working command: POTEn:DPV:Start:ALL -0.5,0.5,0.05,0.01,0.05,0.1
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
        self.current_range: int = 1  # Current range setting (0-3)
        
        # DPV specific settings
        self.enable_data_filtering = True
        self.debug_mode = False

    def setup_measurement(self, params_dict: Dict) -> bool:
        """Setup DPV measurement with parameters"""
        
        try:
            # 🚨 DEBUG: Log received DPV parameters
            logger.info(f"🚨 DPV SETUP - Received parameters: {params_dict}")
            
            # ✅ HARDWARE CHECK - Allow both real and mock hardware for testing
            handler_type = type(self.scpi_handler).__name__
            logger.info(f"🔧 DPV Handler type: {handler_type}")
            
            # Check if hardware is available (connected or mock for testing)
            if self.scpi_handler and hasattr(self.scpi_handler, 'is_connected'):
                if not self.scpi_handler.is_connected:
                    logger.warning("⚠️ Hardware not connected - continuing with mock data for testing")
                else:
                    logger.info("✅ Hardware connected - using real data")
            else:
                logger.warning("⚠️ SCPI handler not available - using mock data for testing")
            
            # Extract current range setting
            current_range_val = params_dict.get('currentRange', 1)
            self.current_range = int(current_range_val)
            logger.info(f"⚡ DPV Current range set to: {self.current_range}")
            
            # Convert dict to DPVParameters (handle both frontend and legacy parameter names)
            params = DPVParameters(
                initial_potential=float(params_dict.get('start_potential', params_dict.get('initial', -0.5))),
                final_potential=float(params_dict.get('end_potential', params_dict.get('final', 0.5))),
                pulse_height=float(params_dict.get('pulse_height', params_dict.get('amplitude', 0.05))),
                pulse_increment=float(params_dict.get('pulse_increment', params_dict.get('step', 0.01))),
                pulse_width=float(params_dict.get('pulse_width', params_dict.get('pulseWidth', 0.05))),
                pulse_period=float(params_dict.get('pulse_period', params_dict.get('pulsePeriod', 0.1)))
            )
            
            # 🔍 DEBUG: Log parsed DPV parameters
            logger.info(f"🚨 FINAL DPV PARAMS: {params}")
            
            # Validate parameters
            is_valid, message = params.validate()
            if not is_valid:
                logger.error(f"Invalid DPV parameters: {message}")
                return False
                
            self.current_params = params
            self.current_potential = params.initial_potential
            
            # 🎯 SEND CURRENT RANGE COMMAND FIRST (BEFORE MEASUREMENT START)
            if hasattr(self, 'current_range') and self.current_range is not None and self.current_range != 'auto':
                try:
                    current_range_cmd = f"POTEn:CURRent:RANGe {self.current_range}"
                    logger.info(f"📡 DPV Sending current range command FIRST: {current_range_cmd}")
                    range_result = self.scpi_handler.send_custom_command(current_range_cmd)
                    if range_result and range_result.get('success', False):
                        logger.info(f"✅ DPV Current range set to {self.current_range}")
                    else:
                        logger.warning(f"⚠️ DPV No response to current range command")
                except Exception as e:
                    logger.error(f"❌ DPV Failed to send current range command: {e}")
            elif hasattr(self, 'current_range') and self.current_range == 'auto':
                logger.info(f"🤖 DPV Using AUTO range mode - STM32 will handle range selection automatically")
            
            # Send DPV SCPI command to STM32
            command = self.current_params.to_scpi_command()
            logger.info(f"🚨 DPV SCPI COMMAND: {command}")
            logger.info(f"🚨 DPV COMMAND LENGTH: {len(command)} chars")
            logger.info(f"🚨 DPV PARAMS: {self.current_params}")
            
            result = self.scpi_handler.send_custom_command(command)
            logger.info(f"🚨 DPV SCPI RESULT: {result}")
            
            if not result['success']:
                logger.error(f"❌ DPV SETUP FAILED: {result['error']}")
                return False
            else:
                logger.info(f"✅ DPV SETUP SUCCESS: {result}")
            
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
            
            # DPV uses Start:ALL command (already sent in setup with current range)
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
        """Get current DPV measurement data with stability improvements"""
        try:
            # 🔧 STABILITY: Add request throttling
            import time
            current_time = time.time()
            if hasattr(self, '_last_data_request'):
                time_since_last = current_time - self._last_data_request
                if time_since_last < 0.3:  # Minimum 300ms between requests
                    return {
                        'points': {'time': [], 'potential': [], 'current': []},
                        'completed': False,
                        'status': 'throttled'
                    }
            self._last_data_request = current_time
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
            logger.debug(f"🔍 DPV Sending data query: {command}")
            result = self.scpi_handler.send_custom_command(command)
            logger.debug(f"🔍 DPV Data query result: success={result['success']}, response_len={len(result.get('response', ''))}")

            if not result['success']:
                logger.warning(f"❌ DPV data query failed: {result['error']}")
                return {'points': [], 'completed': False, 'status': 'collecting'}
            
            # Log raw response for debugging
            if result.get('response'):
                response_preview = result['response'][:200] + "..." if len(result['response']) > 200 else result['response']
                logger.info(f"📄 DPV Raw response preview: {response_preview}")
            else:
                logger.warning(f"⚠️ DPV Empty response from STM32")

            # Parse the data response
            data = self._parse_measurement_data(result['response'])
            logger.debug(f"📊 DPV Parsed data: {len(data.get('points', []))} points, completed={data.get('completed', False)}")
            
            # 🚨 ALTERNATIVE DATA RETRIEVAL - Try multiple methods if no data
            if not data.get('points') and self.is_measuring:
                logger.info("🔄 DPV No data from standard query, trying alternative methods...")
                
                # Method 1: Try getting all available serial data
                alternative_data = self.scpi_handler.get_all_available_data()
                if alternative_data:
                    logger.info(f"📡 DPV Alternative data found: {len(alternative_data)} chars")
                    alt_parsed = self._parse_measurement_data(alternative_data)
                    if alt_parsed.get('points'):
                        logger.info(f"✅ DPV Alternative parsing successful: {len(alt_parsed['points'])} points")
                        data = alt_parsed
                
                # Method 2: Try simple readline approach
                if not data.get('points'):
                    try:
                        simple_data = self.scpi_handler.read_raw_data(timeout=1.0)
                        if simple_data:
                            logger.info(f"📡 DPV Simple read data: {len(simple_data)} chars")
                            simple_parsed = self._parse_measurement_data(simple_data)
                            if simple_parsed.get('points'):
                                logger.info(f"✅ DPV Simple parsing successful: {len(simple_parsed['points'])} points")
                                data = simple_parsed
                    except Exception as e:
                        logger.debug(f"Simple read failed: {e}")
            
            # 🏁 ENHANCED COMPLETION DETECTION for DPV
            if self.is_measuring:
                # Method 1: Check if data parsing found completion indicator
                if data.get('completed', False):
                    logger.info("🏁 DPV completed via data parsing")
                    self.is_measuring = False
                    return data
                
                # Method 2: Check STATUS command
                status_command = "POTEn:DPV:STATUS?"
                status_result = self.scpi_handler.send_custom_command(status_command)
                if status_result['success']:
                    status_response = status_result['response'].upper()
                    if 'COMPLETE' in status_response or 'FINISHED' in status_response or 'IDLE' in status_response:
                        logger.info(f"🏁 DPV completed via status: {status_result['response']}")
                        self.is_measuring = False
                        completed_data = dict(data)
                        completed_data['completed'] = True
                        return completed_data
                
                # Method 3: Check if no new data for extended time (timeout detection)
                current_time = time.time()
                if hasattr(self, 'last_data_time') and self.last_data_time:
                    time_since_last_data = current_time - self.last_data_time
                    # If DPV parameters suggest completion time, use that for timeout
                    if hasattr(self, 'current_params') and self.current_params:
                        voltage_range = abs(self.current_params.final_potential - self.current_params.initial_potential)
                        expected_points = int(voltage_range / self.current_params.pulse_increment) + 1
                        expected_duration = expected_points * self.current_params.pulse_period
                        timeout_threshold = max(expected_duration + 10, 30)  # At least 30s timeout
                        
                        if time_since_last_data > timeout_threshold:
                            logger.info(f"🏁 DPV completed via timeout: {time_since_last_data:.1f}s > {timeout_threshold:.1f}s")
                            self.is_measuring = False
                            completed_data = dict(data)
                            completed_data['completed'] = True
                            return completed_data
            
            return data

        except Exception as e:
            logger.error(f"Error in DPV get_measurement_data: {e}")
            return {'points': [], 'completed': False, 'error': str(e)}

    def _parse_measurement_data(self, response: str) -> Dict:
        """Parse DPV measurement data from SCPI response
        Expected format: DPV, Point, Time, Potential, Current_i1, Current_i2, DPVCurrent
        Example: DPV, 1, 0.000, -0.500, -6.737e-04, -6.708e-04, 2.903e-06
        """
        try:
            if not response or not response.strip():
                logger.debug("📄 DPV Empty or no response to parse")
                return {'points': [], 'completed': False}

            logger.debug(f"📄 DPV Parsing response: {len(response)} chars, {response.count(chr(10))} lines")
            
            points = []
            lines = response.strip().split('\n')
            completed = False
            data_processed = False
            line_count = 0
            valid_dpv_lines = 0
            
            for line in lines:
                line_count += 1
                line = line.strip()
                
                if not line:
                    continue
                    
                if line.startswith('#'):
                    logger.debug(f"📝 DPV Comment line {line_count}: {line}")
                    continue
                
                # 🏁 ENHANCED COMPLETION DETECTION - Check for various completion indicators
                line_upper = line.upper()
                completion_keywords = [
                    'OPERATION FINISHED', 'COMPLETE', 'END', 'DONE', 'FINISHED',
                    'DPV COMPLETE', 'DPV FINISHED', 'DPV END', 'DPV DONE',
                    'MEASUREMENT COMPLETE', 'SCAN COMPLETE', 'SWEEP COMPLETE'
                ]
                
                if any(keyword in line_upper for keyword in completion_keywords):
                    completed = True
                    logger.info(f"🏁 DPV measurement completed - detected: {line.strip()}")
                    continue
                
                # Skip header line
                if 'Point, Time, Potential' in line:
                    logger.debug("📋 Found DPV header line")
                    continue
                
                try:
                    parts = [part.strip() for part in line.split(',')]
                    logger.debug(f"🔍 Line {line_count}: {len(parts)} parts: {parts[:3]}...")
                    
                    # Real STM32 DPV format: "DPV, Point, Time, Potential, Current_i1, Current_i2, DPVCurrent"
                    # Example: DPV, 1, 0.000, -0.500, -6.737e-04, -6.708e-04, 2.903e-06
                    if len(parts) >= 7 and parts[0].strip().upper() == 'DPV':
                        valid_dpv_lines += 1
                        point_num = int(parts[1].strip())            # Point number
                        time_s = float(parts[2].strip())             # Time in seconds
                        potential = float(parts[3].strip())          # Potential in V
                        current_i1 = float(parts[4].strip())         # Current_i1 in A
                        current_i2 = float(parts[5].strip())         # Current_i2 in A  
                        dpv_current = float(parts[6].strip())        # DPV difference current in A
                        
                        # Convert current from A to µA for display
                        current_ua = dpv_current * 1e6
                        
                        if valid_dpv_lines <= 3 or valid_dpv_lines % 10 == 0:  # Log first 3 and every 10th
                            logger.info(f"✅ DPV Point {point_num}: V={potential:.3f}V, I={current_ua:.2f}µA, T={time_s:.1f}s")
                        
                        # Data validation and filtering
                        should_filter = False
                        
                        if self.enable_data_filtering and not self.debug_mode:
                            if hasattr(self, 'last_validated_current') and self.last_validated_current is not None:
                                current_jump = abs(current_ua - self.last_validated_current)
                                if current_jump > 1000:  # 1000µA = 1mA threshold
                                    logger.warning(f"Filtered EXTREME DPV current spike: {current_jump:.1f}µA")
                                    should_filter = True
                                elif current_jump > 100:  # 100µA threshold
                                    logger.debug(f"Large DPV current spike detected: {current_jump:.1f}µA (allowing)")
                        
                        if not should_filter:
                            # Create data point using corrected variable names
                            timestamp = time_s if self.start_time else time.time()
                            
                            data_point = DPVDataPoint(
                                timestamp=timestamp,
                                potential=potential,
                                current=current_ua,
                                pulse_number=point_num,
                                measurement_phase='pulse'  # DPV always pulse measurement
                            )
                            
                            self.data_points.append(data_point)
                            logger.info(f"✅ ADDED DPV data point #{len(self.data_points)}: V={potential:.3f}V, I={current_ua:.1f}µA")
                            
                            # Convert to dict for JSON serialization
                            points.append({
                                'timestamp': timestamp,
                                'potential': potential,
                                'current': current_ua,
                                'pulse_number': point_num,
                                'measurement_phase': 'pulse',
                                'mode': 'DPV'
                            })
                            
                            self.last_validated_current = current_ua
                            self.last_data_time = time.time()
                            self.pulse_number = point_num
                            
                            # 🎯 CHECK IF WE'VE REACHED THE END POTENTIAL
                            if hasattr(self, 'current_params') and self.current_params:
                                # Check if we're close to final potential (within one increment)
                                final_pot = self.current_params.final_potential
                                increment = self.current_params.pulse_increment
                                
                                if abs(potential - final_pot) <= increment * 1.1:  # Allow 10% tolerance
                                    logger.info(f"🏁 DPV approaching end potential: {potential:.3f}V ≈ {final_pot:.3f}V")
                                    # Don't set completed here, let it finish naturally
                        
                        data_processed = True
                        
                    else:
                        # Log various line types for debugging
                        if line.upper().startswith('DPV') and len(parts) < 7:
                            logger.warning(f"⚠️ DPV Incomplete DPV line: {line}")
                        elif 'ERROR' in line.upper():
                            logger.error(f"❌ DPV Error line: {line}")
                        elif any(word in line.upper() for word in ['STATUS', 'READY', 'BUSY']):
                            logger.info(f"📊 DPV Status line: {line}")
                        else:
                            logger.debug(f"❓ DPV Unknown line format: {line}")
                        continue
                        
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse DPV data line '{line}': {e}")
                    continue

            # Summary logging
            if valid_dpv_lines > 0:
                logger.info(f"📊 DPV Parse summary: {valid_dpv_lines} valid points from {line_count} lines, completed={completed}")
            elif line_count > 0:
                logger.warning(f"⚠️ DPV Parse summary: No valid DPV points found in {line_count} lines")

            result = {
                'points': points,
                'completed': completed
            }
                
            if points:
                logger.info(f"✅ DPV Parsed {len(points)} data points from STM32")
            elif line_count > 0:
                logger.warning(f"⚠️ DPV No data processed from {line_count} lines")
            
            return result

        except Exception as e:
            logger.error(f"Error parsing DPV measurement data: {e}")
            return {'points': [], 'completed': False, 'error': str(e)}

    def get_status(self) -> Dict:
        """Get current DPV measurement status with completion estimation"""
        total_pulses = 0
        progress_info = {}
        
        if self.current_params:
            voltage_range = abs(self.current_params.final_potential - self.current_params.initial_potential)
            total_pulses = int(voltage_range / self.current_params.pulse_increment) + 1
            expected_duration = total_pulses * self.current_params.pulse_period
            
            # Add progress information if measurement is active
            if self.is_measuring and hasattr(self, 'start_time') and self.start_time:
                elapsed_time = time.time() - self.start_time
                progress_percent = min((self.pulse_number / total_pulses) * 100, 100) if total_pulses > 0 else 0
                estimated_remaining = max(0, expected_duration - elapsed_time)
                
                progress_info = {
                    'progress_percent': round(progress_percent, 1),
                    'elapsed_time': round(elapsed_time, 1),
                    'expected_duration': round(expected_duration, 1),
                    'estimated_remaining': round(estimated_remaining, 1)
                }
                
                # Check if we should be completed by now
                if elapsed_time > expected_duration * 1.2:  # 20% overtime tolerance
                    progress_info['overtime'] = True
                    progress_info['overtime_seconds'] = round(elapsed_time - expected_duration, 1)
            
        status = {
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
        
        # Add progress info if available
        status.update(progress_info)
        
        return status

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