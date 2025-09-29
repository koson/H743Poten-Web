"""
SWV Measurement Service for H743Poten Web Interface
Handles Square Wave Voltammetry measurements with real-time data streaming
"""

import time
import threading
import logging
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)

@dataclass
class SWVParameters:
    """SWV measurement parameters"""
    start_potential: float      # Starting potential (V)
    end_potential: float        # End potential (V)
    frequency: float            # Square wave frequency (Hz)
    amplitude: float            # Square wave amplitude (V)
    step_potential: float       # Step size between measurements (V)
    
    def validate(self) -> Tuple[bool, str]:
        """Validate SWV parameters"""
        if self.end_potential == self.start_potential:
            return False, "End potential must be different from start potential"
            
        if self.frequency <= 0:
            return False, "Frequency must be positive"
            
        if self.amplitude <= 0:
            return False, "Amplitude must be positive"
            
        if self.step_potential <= 0:
            return False, "Step potential must be positive"
            
        if self.frequency > 1000:  # Reasonable upper limit
            return False, "Frequency too high (max 1000 Hz)"
            
        return True, "Parameters valid"
    
    def to_scpi_command(self) -> str:
        """Convert parameters to SCPI command for STM32
        
        Format: POTEn:SWV:Start:ALL {Frequency},{Amplitude},{StepPotential},{StartPotential},{EndPotential}
        Example: POTEn:SWV:Start:ALL 100,0.05,0.01,-0.5,0.5
        
        Parameters:
        - Frequency: Square wave frequency (Hz)
        - Amplitude: Square wave amplitude (V)
        - StepPotential: Step size between measurements (V)
        - StartPotential: Starting potential (V)
        - EndPotential: End potential (V)
        """
        return f"POTEn:SWV:Start:ALL {self.frequency},{self.amplitude},{self.step_potential},{self.start_potential},{self.end_potential}"

@dataclass  
class SWVDataPoint:
    """Single SWV data point"""
    timestamp: float
    potential: float        # Applied potential (V)
    forward_current: float  # Forward pulse current (µA)
    reverse_current: float  # Reverse pulse current (µA)
    net_current: float      # Differential current (forward - reverse) (µA)
    step_number: int        # Current step number

class SWVMeasurementService:
    """Service for managing SWV measurements"""
    
    def __init__(self, scpi_handler):
        self.scpi_handler = scpi_handler
        self.is_measuring = False
        self.is_paused = False
        self.measurement_thread = None
        self.data_points: List[SWVDataPoint] = []
        self.current_params: Optional[SWVParameters] = None
        self.start_time: Optional[float] = None
        self.last_data_time: Optional[float] = None
        self.data_timeout = 30.0  # seconds
        self.current_potential = 0.0
        self.last_validated_current = None
        self.step_number = 0
        self.current_range: int = 1  # Current range setting (0-3)
        
        # SWV Progress tracking
        self.progress_data = {
            'phase': 'READY',
            'elapsed': 0,
            'total': 0,
            'potential': 0.0,
            'current_point': 0,
            'total_points': 200,
            'percentage': 0
        }
        
        # SWV specific settings
        self.enable_data_filtering = True
        self.debug_mode = False

    def setup_measurement(self, params_dict: Dict) -> bool:
        """Setup SWV measurement with enhanced parameters including preconcentration"""
        
        try:
            # 🚨 DEBUG: Log received SWV parameters
            logger.info(f"🚨 SWV Service received params: {params_dict}")
            
            # 🛡️ STRICT HARDWARE REQUIREMENT - No measurement without real hardware
            handler_type = type(self.scpi_handler).__name__
            if 'Mock' in handler_type or 'mock' in handler_type.lower():
                logger.error(f"❌ SWV Mock handler detected ({handler_type}) - Real hardware required")
                return False
            
            if not self.scpi_handler or not hasattr(self.scpi_handler, 'is_connected') or not self.scpi_handler.is_connected:
                logger.error("❌ SWV STM32 hardware not connected - No measurement allowed")
                return False
            
            # Extract current range setting
            current_range_val = params_dict.get('currentRange', 1)
            self.current_range = int(current_range_val)
            logger.info(f"⚡ SWV Current range set to: {self.current_range}")
            
            # Use CV service's SWV setup for enhanced parameters
            cv_service = current_app.cv_service
            if cv_service:
                # Set current range in CV service too
                cv_service.current_range = self.current_range
                
                # Setup using enhanced SWV parameters
                success, message = cv_service.setup_swv_measurement(params_dict)
                if success:
                    logger.info(f"✅ SWV setup successful via CV service: {message}")
                    return True
                else:
                    logger.error(f"❌ SWV setup failed via CV service: {message}")
                    return False
            
            # Fallback to original SWV parameters (legacy support)
            logger.warning("⚠️ Using legacy SWV parameter handling")
            params = SWVParameters(
                start_potential=float(params_dict.get('start_potential', params_dict.get('begin_voltage', -0.5))),
                end_potential=float(params_dict.get('end_potential', params_dict.get('end_voltage', 0.5))),
                frequency=float(params_dict.get('frequency', 5.0)),
                amplitude=float(params_dict.get('amplitude', 0.05)),
                step_potential=float(params_dict.get('step_potential', 0.005))
            )
            
            # Validate parameters
            is_valid, message = params.validate()
            if not is_valid:
                logger.error(f"Invalid SWV parameters: {message}")
                return False
                
            self.current_params = params
            self.current_potential = params.start_potential
            
            # Send SCPI command to STM32
            command = self.current_params.to_scpi_command()
            logger.info(f"Sending SWV command to STM32: {command}")
            
            result = self.scpi_handler.send_custom_command(command)
            if not result['success']:
                logger.error(f"Failed to setup SWV measurement: {result['error']}")
                return False
            
            logger.info(f"SWV measurement setup successful: {params}")
            return True
            
        except Exception as e:
            logger.error(f"Error in SWV setup_measurement: {e}")
            return False

    def start_measurement(self) -> bool:
        """Start SWV measurement"""
        
        try:
            if not self.current_params:
                raise ValueError("No SWV parameters set")

            # Clear previous data
            self.data_points.clear()
            self.start_time = time.time()
            self.last_data_time = None
            self.step_number = 0
            
            # SWV uses Start:ALL command (already sent in setup)
            self.is_measuring = True
            
            # 🎯 SEND CURRENT RANGE COMMAND (AFTER MEASUREMENT START) - ONLY IF NOT AUTO
            if hasattr(self, 'current_range') and self.current_range is not None and self.current_range != 'auto':
                try:
                    current_range_cmd = f"POTEn:CURRent:RANGe {self.current_range}"
                    logger.info(f"📡 SWV Sending current range command: {current_range_cmd} (Manual mode)")
                    range_result = self.scpi_handler.send_custom_command(current_range_cmd)
                    if range_result and range_result.get('success', False):
                        logger.info(f"✅ SWV Current range locked to {self.current_range}")
                    else:
                        logger.warning(f"⚠️ SWV No response to current range command")
                except Exception as e:
                    logger.error(f"❌ SWV Failed to send current range command: {e}")
            elif hasattr(self, 'current_range') and self.current_range == 'auto':
                logger.info(f"🤖 SWV Using AUTO range mode - STM32 will handle range selection automatically")
            
            logger.info(f"Started SWV measurement")
            
            return True

        except Exception as e:
            logger.error(f"Error in SWV start_measurement: {e}")
            return False

    def stop_measurement(self) -> bool:
        """Stop SWV measurement"""
        try:
            # Use SWV abort command
            command = "POTEn:SWV:ABORt"
            result = self.scpi_handler.send_custom_command(command)

            if not result['success']:
                raise Exception(f"Failed to stop SWV measurement: {result['error']}")

            self.is_measuring = False
            logger.info(f"Stopped SWV measurement using {command}")
            return True

        except Exception as e:
            logger.error(f"Error in SWV stop_measurement: {e}")
            return False
    
    def _update_progress_from_data(self, data_string: str):
        """Update progress tracking from STM32 data"""
        try:
            lines = data_string.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Parse preconcentration progress
                if 'PRECONCENTRATION_START' in line:
                    self.progress_data['phase'] = 'PRECONCENTRATION'
                    self.progress_data['elapsed'] = 0
                    logger.info("🚨 SWV Progress: Preconcentration started")
                    
                elif line.startswith('PRECON_PROGRESS'):
                    # Format: PRECON_PROGRESS,STEP1,30.0,240.0
                    parts = line.split(',')
                    if len(parts) >= 4:
                        elapsed = float(parts[2])
                        total = float(parts[3])
                        self.progress_data.update({
                            'phase': 'PRECONCENTRATION',
                            'elapsed': elapsed,
                            'total': total,
                            'percentage': int((elapsed / total) * 100),
                            'potential': -1.9  # Default preconc potential
                        })
                        logger.debug(f"🚨 Preconc progress: {elapsed}/{total}s ({self.progress_data['percentage']}%)")
                
                elif 'PRECONCENTRATION_COMPLETE' in line:
                    self.progress_data.update({
                        'phase': 'PRECONCENTRATION',
                        'percentage': 100,
                        'elapsed': self.progress_data.get('total', 240)
                    })
                    logger.info("🚨 SWV Progress: Preconcentration complete")
                
                elif 'EQUILIBRATION_START' in line:
                    # Format: EQUILIBRATION_START,-0.500,10.0
                    parts = line.split(',')
                    if len(parts) >= 3:
                        potential = float(parts[1])
                        total_time = float(parts[2])
                        self.progress_data.update({
                            'phase': 'EQUILIBRATION',
                            'elapsed': 0,
                            'total': total_time,
                            'potential': potential,
                            'percentage': 0
                        })
                    logger.info("🚨 SWV Progress: Equilibration started")
                
                elif line.startswith('EQUIL_PROGRESS'):
                    # Format: EQUIL_PROGRESS,1.0,10.0
                    parts = line.split(',')
                    if len(parts) >= 3:
                        elapsed = float(parts[1])
                        total = float(parts[2])
                        self.progress_data.update({
                            'phase': 'EQUILIBRATION',
                            'elapsed': elapsed,
                            'total': total,
                            'percentage': int((elapsed / total) * 100)
                        })
                        logger.debug(f"🚨 Equilibration progress: {elapsed}/{total}s")
                
                elif 'EQUILIBRATION_COMPLETE' in line:
                    self.progress_data.update({
                        'phase': 'EQUILIBRATION',
                        'percentage': 100
                    })
                    logger.info("🚨 SWV Progress: Equilibration complete")
                
                elif line.startswith('SWV,') and ',' in line:
                    # Parse SWV data points for scanning progress
                    parts = line.split(',')
                    if len(parts) >= 4:
                        try:
                            point_num = int(parts[1])
                            potential = float(parts[3])
                            
                            self.progress_data.update({
                                'phase': 'SCANNING',
                                'current_point': point_num,
                                'total_points': 200,  # Typical SWV scan points
                                'potential': potential,
                                'percentage': int((point_num / 200) * 100)
                            })
                            
                            if point_num % 20 == 0:  # Log every 20 points
                                logger.debug(f"🚨 SWV Scanning: Point {point_num}/200 at {potential}V")
                        except (ValueError, IndexError):
                            pass
                
                elif 'SWV Operation Finished' in line:
                    self.progress_data.update({
                        'phase': 'COMPLETE',
                        'percentage': 100
                    })
                    logger.info("🚨 SWV Progress: Complete!")
                    
        except Exception as e:
            logger.error(f"Error updating SWV progress: {e}")

    def get_measurement_data(self) -> Dict:
        """Get current SWV measurement data with progress tracking"""
        try:
            if not self.current_params:
                logger.debug("No SWV measurement mode set, returning empty data")
                return {'points': [], 'completed': False}

            # Check for buffered data from STM32
            buffered_data = self.scpi_handler.get_buffered_data()
            if buffered_data:
                logger.info(f"Found buffered SWV data from STM32: {len(buffered_data)} characters")
                
                # Update progress based on buffered data
                self._update_progress_from_data(buffered_data)
                
                parsed_data = self._parse_measurement_data(buffered_data)
                if parsed_data['points']:
                    logger.info(f"Parsed {len(parsed_data['points'])} SWV points from buffered data")
                    
                    # Add progress data to response
                    parsed_data['swv_progress'] = self.progress_data.copy()
                    return parsed_data
            
            # If no buffered data, try regular query
            command = "POTEn:SWV:DATA?"
            result = self.scpi_handler.send_custom_command(command)

            if not result['success']:
                logger.debug(f"SWV data query failed: {result['error']}")
                return {
                    'points': [], 
                    'completed': False, 
                    'status': 'collecting',
                    'swv_progress': self.progress_data.copy()
                }

            # Parse the data response
            data = self._parse_measurement_data(result['response'])
            
            # Update progress from parsed data
            if result['response']:
                self._update_progress_from_data(result['response'])
            
            # Check if measurement is completed
            if not data['points'] and self.is_measuring:
                status_command = "POTEn:SWV:STATUS?"
                status_result = self.scpi_handler.send_custom_command(status_command)
                if status_result['success'] and 'COMPLETE' in status_result['response'].upper():
                    logger.info(f"SWV measurement completed")
                    self.is_measuring = False
                    self.progress_data['phase'] = 'COMPLETE'
                    self.progress_data['percentage'] = 100
                    
                    completed_data = dict(data)
                    completed_data['completed'] = True
                    completed_data['swv_progress'] = self.progress_data.copy()
                    return completed_data
            
            # Always include progress data
            data['swv_progress'] = self.progress_data.copy()
            return data

        except Exception as e:
            logger.error(f"Error in SWV get_measurement_data: {e}")
            return {
                'points': [], 
                'completed': False, 
                'error': str(e),
                'swv_progress': self.progress_data.copy()
            }

    def _parse_measurement_data(self, response: str) -> Dict:
        """Parse SWV measurement data from SCPI response"""
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
                    logger.debug(f"Parsed SWV data parts: {parts}")
                    
                    # SWV format: "SWV, time_ms, voltage, forward_current, reverse_current, step_number, ..."
                    if len(parts) >= 6 and parts[0].strip() == 'SWV':
                        time_ms = float(parts[1].strip())
                        potential = float(parts[2].strip())         # Corrected potential from STM32
                        logger.debug(f"✅ SWV STM32 voltage: {potential:.4f}V (already corrected)")
                        forward_current_ua = float(parts[3].strip())
                        reverse_current_ua = float(parts[4].strip())
                        step_num = int(parts[5].strip())
                        
                        # Keep in µA (no conversion)
                        forward_current = forward_current_ua
                        reverse_current = reverse_current_ua
                        net_current = forward_current - reverse_current
                        
                        logger.info(f"STM32 SWV Data: V={potential:.3f}V, I_fw={forward_current:.1f}µA, I_rv={reverse_current:.1f}µA, I_net={net_current:.1f}µA, Step={step_num}, Time={time_ms}ms")
                        
                        # Data validation and filtering
                        should_filter = False
                        
                        if self.enable_data_filtering and not self.debug_mode:
                            if hasattr(self, 'last_validated_current') and self.last_validated_current is not None:
                                current_jump = abs(net_current - self.last_validated_current)
                                if current_jump > 1000:  # 1000µA = 1mA threshold
                                    logger.warning(f"Filtered EXTREME SWV current spike: {current_jump:.1f}µA")
                                    should_filter = True
                                elif current_jump > 100:  # 100µA threshold
                                    logger.debug(f"Large SWV current spike detected: {current_jump:.1f}µA (allowing)")
                        
                        if not should_filter:
                            # Create data point
                            timestamp = time_ms / 1000.0 if self.start_time else time.time()
                            
                            data_point = SWVDataPoint(
                                timestamp=timestamp,
                                potential=potential,
                                forward_current=forward_current,
                                reverse_current=reverse_current,
                                net_current=net_current,
                                step_number=step_num
                            )
                            
                            self.data_points.append(data_point)
                            logger.info(f"✅ ADDED SWV data point #{len(self.data_points)}: V={potential:.3f}V, I_net={net_current:.1f}µA")
                            
                            # ✅ STM32 already sends corrected voltages
                            potential_corrected = potential  # Use STM32 voltage as-is
                            logger.debug(f"✅ SWV API voltage: {potential:.4f}V (already corrected)")
                            
                            # Convert to dict for JSON serialization
                            points.append({
                                'timestamp': timestamp,
                                'potential': potential_corrected,  # Use corrected potential
                                'current': net_current,  # Use net current for plotting
                                'forward_current': forward_current,
                                'reverse_current': reverse_current,
                                'net_current': net_current,
                                'step_number': step_num,
                                'mode': 'SWV'
                            })
                            
                            self.last_validated_current = net_current
                            self.last_data_time = time.time()
                            self.step_number = step_num
                        
                        data_processed = True
                        
                    else:
                        logger.warning(f"Invalid SWV data format: {line}")
                        continue
                        
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse SWV data line '{line}': {e}")
                    continue

            result = {
                'points': points,
                'completed': completed
            }
                
            if points:
                logger.debug(f"Parsed {len(points)} SWV data points from STM32")
            
            return result

        except Exception as e:
            logger.error(f"Error parsing SWV measurement data: {e}")
            return {'points': [], 'completed': False, 'error': str(e)}

    def get_status(self) -> Dict:
        """Get current SWV measurement status"""
        total_steps = 0
        if self.current_params:
            voltage_range = abs(self.current_params.end_potential - self.current_params.start_potential)
            total_steps = int(voltage_range / self.current_params.step_potential) + 1
            
        return {
            'mode': 'SWV',
            'is_measuring': self.is_measuring,
            'is_paused': self.is_paused,
            'data_points': len(self.data_points),
            'current_step': self.step_number,
            'total_steps': total_steps,
            'current_potential': self.current_potential,
            'parameters': {
                'start_potential': self.current_params.start_potential if self.current_params else None,
                'end_potential': self.current_params.end_potential if self.current_params else None,
                'frequency': self.current_params.frequency if self.current_params else None,
                'amplitude': self.current_params.amplitude if self.current_params else None,
                'step_potential': self.current_params.step_potential if self.current_params else None,
            }
        }

    def export_data(self) -> Dict:
        """Export SWV measurement data"""
        if not self.data_points:
            return {'success': False, 'message': 'No data to export'}
        
        try:
            # Prepare export data
            export_data = {
                'measurement_type': 'SWV',
                'timestamp': datetime.now().isoformat(),
                'parameters': self.get_status()['parameters'],
                'data_points': len(self.data_points),
                'data': []
            }
            
            for point in self.data_points:
                export_data['data'].append({
                    'timestamp': point.timestamp,
                    'potential_V': point.potential,
                    'forward_current_uA': point.forward_current,
                    'reverse_current_uA': point.reverse_current,
                    'net_current_uA': point.net_current,
                    'step_number': point.step_number
                })
            
            return {'success': True, 'data': export_data}
            
        except Exception as e:
            logger.error(f"Error exporting SWV data: {e}")
            return {'success': False, 'message': str(e)}