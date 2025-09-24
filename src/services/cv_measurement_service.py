"""
CV Measurement Service for H743Poten Web Interface
Handles Cyclic Voltammetry measurements with real-time data streaming
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
class CVParameters:
    """CV measurement parameters"""
    begin: float        # Starting potential (V)
    upper: float        # Upper potential limit (V) 
    lower: float        # Lower potential limit (V)
    rate: float         # Scan rate (V/s)
    cycles: int         # Number of cycles
    
    def validate(self) -> Tuple[bool, str]:
        """Validate CV parameters"""
        if self.upper <= self.lower:
            return False, "Upper potential must be greater than lower potential"
        
        if not (self.lower <= self.begin <= self.upper):
            return False, "Starting potential must be between lower and upper limits"
            
        if self.rate <= 0:
            return False, "Scan rate must be positive"
            
        if self.cycles <= 0:
            return False, "Number of cycles must be positive"
            
        return True, "Parameters valid"
    
    def to_scpi_command(self) -> str:
        """Convert parameters to SCPI command for STM32
        
        Format: POTEn:CV:Start:ALL <begin>,<upper>,<lower>,<rate>,<cycles>
        Example: POTEn:CV:Start:ALL 0.0,1.0,-1.0,0.1,1
        
        Parameters:
        - Begin: Starting potential (V)
        - Upper: Upper potential limit (V) 
        - Lower: Lower potential limit (V)
        - Rate: Scan rate (V/s)
        - Cycles: Number of cycles
        """
        return f"POTEn:CV:Start:ALL {self.begin},{self.upper},{self.lower},{self.rate},{self.cycles}"

@dataclass  
class CVDataPoint:
    """Single CV data point"""
    timestamp: float
    potential: float    # Applied potential (V)
    current: float      # Measured current (µA)
    cycle: int          # Current cycle number
    direction: str      # Scan direction: 'forward' or 'reverse'

class CVMeasurementService:
    """Service for managing CV measurements"""
    
    def __init__(self, scpi_handler):
        self.scpi_handler = scpi_handler
        self.is_measuring = False
        self.is_paused = False
        self.measurement_thread = None
        self.data_points: List[CVDataPoint] = []
        self.current_params: Optional[CVParameters] = None
        self.start_time = None
        self.current_cycle = 1
        self.scan_direction = 'forward'
        self.current_potential = 0.0
        self.data_lock = threading.Lock()
        
        # Real-time streaming
        self.streaming_enabled = False
        self.stream_callback = None
        
        # Simulation mode for development/testing
        self.simulation_mode = False
        
        # Debug mode - accept all data without filtering
        self.debug_mode = True  # Enable debug mode by default to fix filtering issue
        
        # Timeout handling
        self.last_data_time = None
        self.data_timeout = 10.0  # seconds without data before considering measurement complete
        
        # Data validation filters (similar to Desktop version)
        self.last_validated_potential = None
        self.last_validated_current = None
        self.last_potential = None  # For direction inference
        
    def set_simulation_mode(self, enabled: bool) -> None:
        """Enable or disable simulation mode"""
        self.simulation_mode = enabled
        logger.info(f"CV simulation mode {'enabled' if enabled else 'disabled'}")
    
    def setup_measurement(self, params: Dict) -> Tuple[bool, str]:
        """Setup CV measurement with parameters"""
        try:
            # Create CV parameters object
            cv_params = CVParameters(
                begin=float(params.get('begin', 0.0)),
                upper=float(params.get('upper', 0.7)), 
                lower=float(params.get('lower', -0.4)),
                rate=float(params.get('rate', 0.1)),
                cycles=int(params.get('cycles', 1))
            )
            
            # Validate parameters
            is_valid, message = cv_params.validate()
            if not is_valid:
                return False, message
                
            self.current_params = cv_params
            logger.info(f"CV measurement setup: {cv_params}")
            
            return True, "CV measurement configured successfully"
            
        except (ValueError, TypeError) as e:
            return False, f"Invalid parameter format: {e}"
        except Exception as e:
            logger.error(f"Failed to setup CV measurement: {e}")
            return False, f"Setup failed: {e}"
    
    def start_measurement(self) -> Tuple[bool, str]:
        """Start CV measurement"""
        try:
            if self.current_params is None:
                return False, "No measurement parameters configured"
                
            if self.is_measuring:
                return False, "Measurement already in progress"
            
            # Clear previous data
            with self.data_lock:
                self.data_points.clear()
                self.current_cycle = 1
                self.scan_direction = 'forward'
                self.current_potential = self.current_params.begin
                
            # Check if using real device or simulation
            if self.simulation_mode or not self.scpi_handler.is_connected:
                logger.info("Starting CV measurement in simulation mode")
                # Start simulation directly
                self.is_measuring = True
                self.is_paused = False
                self.start_time = time.time()
                self.measurement_thread = threading.Thread(
                    target=self._measurement_worker,
                    daemon=True
                )
                self.measurement_thread.start()
                return True, "CV measurement started (simulation mode)"
            else:
                # Send SCPI command to start measurement on real device
                command = self.current_params.to_scpi_command()
                result = self.scpi_handler.send_custom_command(command)
                
                if not result['success']:
                    logger.warning(f"Failed to start device measurement: {result.get('error')}")
                    logger.info("Falling back to simulation mode")
                    self.simulation_mode = True
                    self.is_measuring = True
                    self.is_paused = False
                    self.start_time = time.time()
                    self.measurement_thread = threading.Thread(
                        target=self._measurement_worker,
                        daemon=True
                    )
                    self.measurement_thread.start()
                    return True, "CV measurement started (simulation mode - device not responding)"
                
                # Device accepted command, start measurement worker
                self.is_measuring = True
                self.is_paused = False
                self.start_time = time.time()
                self.last_data_time = time.time()  # Initialize last data time
                self.measurement_thread = threading.Thread(
                    target=self._measurement_worker,
                    daemon=True
                )
                self.measurement_thread.start()
                
                logger.info("CV measurement started on device")
                return True, "CV measurement started successfully"
            
        except Exception as e:
            logger.error(f"Failed to start CV measurement: {e}")
            return False, f"Failed to start measurement: {e}"
    
    def stop_measurement(self) -> Tuple[bool, str]:
        """Stop CV measurement"""
        try:
            if not self.is_measuring:
                return False, "No measurement in progress"
            
            # Send abort command to device (like Desktop version)
            try:
                if self.scpi_handler and self.scpi_handler.is_connected:
                    # Send multiple ABORT commands for reliability
                    for i in range(3):
                        result = self.scpi_handler.send_custom_command("POTEn:ABORt")
                        logger.info(f"Sent ABORT command #{i+1}: {result}")
                        time.sleep(0.1)
            except Exception as e:
                logger.warning(f"Failed to send ABORT command: {e}")
            
            # Stop measurement thread
            self.is_measuring = False
            self.is_paused = False
            
            if self.measurement_thread and self.measurement_thread.is_alive():
                self.measurement_thread.join(timeout=2.0)
            
            logger.info("CV measurement stopped")
            return True, "CV measurement stopped successfully"
            
        except Exception as e:
            logger.error(f"Failed to stop CV measurement: {e}")
            return False, f"Stop failed: {e}"
    
    def pause_measurement(self) -> Tuple[bool, str]:
        """Pause CV measurement"""
        try:
            if not self.is_measuring:
                return False, "No measurement in progress"
                
            if self.is_paused:
                return False, "Measurement already paused"
            
            self.is_paused = True
            logger.info("CV measurement paused")
            return True, "CV measurement paused"
            
        except Exception as e:
            logger.error(f"Failed to pause CV measurement: {e}")
            return False, f"Pause failed: {e}"
    
    def resume_measurement(self) -> Tuple[bool, str]:
        """Resume CV measurement"""
        try:
            if not self.is_measuring:
                return False, "No measurement in progress"
                
            if not self.is_paused:
                return False, "Measurement not paused"
            
            self.is_paused = False
            logger.info("CV measurement resumed")
            return True, "CV measurement resumed"
            
        except Exception as e:
            logger.error(f"Failed to resume CV measurement: {e}")
            return False, f"Resume failed: {e}"
    
    def get_status(self) -> Dict:
        """Get current measurement status"""
        with self.data_lock:
            # Check for data timeout if measurement is running
            time_since_last_data = None
            if self.is_measuring and self.last_data_time:
                time_since_last_data = time.time() - self.last_data_time
                
            return {
                'is_measuring': self.is_measuring,
                'is_paused': self.is_paused,
                'current_cycle': self.current_cycle,
                'scan_direction': self.scan_direction,
                'current_potential': self.current_potential,
                'data_points_count': len(self.data_points),
                'elapsed_time': time.time() - self.start_time if self.start_time else 0,
                'time_since_last_data': time_since_last_data,
                'data_timeout': self.data_timeout,
                'device_connected': getattr(self.scpi_handler, 'is_connected', False),
                'parameters': {
                    'begin': self.current_params.begin,
                    'upper': self.current_params.upper,
                    'lower': self.current_params.lower, 
                    'rate': self.current_params.rate,
                    'cycles': self.current_params.cycles
                } if self.current_params else None
            }
    
    def get_data_points(self, limit: Optional[int] = None) -> List[Dict]:
        """Get measurement data points"""
        print(f"[CV SERVICE] get_data_points called with limit={limit}")
        with self.data_lock:
            total_points = len(self.data_points)
            print(f"[CV SERVICE] Total data points available: {total_points}")
            
            # Add debug info if no points
            if total_points == 0:
                print(f"[CV SERVICE] ⚠️ NO DATA POINTS! is_measuring={self.is_measuring}")
                if hasattr(self, 'last_validated_potential'):
                    print(f"[CV SERVICE] Last validated: V={self.last_validated_potential}, I={self.last_validated_current}")
            
            points = self.data_points[-limit:] if limit else self.data_points
            result_count = len(points)
            print(f"[CV SERVICE] Returning {result_count} points (limit={limit})")
            
            result = [
                {
                    'timestamp': point.timestamp,
                    'potential': point.potential,
                    'current': point.current,
                    'cycle': point.cycle,
                    'direction': point.direction
                }
                for point in points
            ]
            
            if result:
                voltages = [p['potential'] for p in result]
                print(f"[CV SERVICE] Voltage range: {min(voltages):.4f} to {max(voltages):.4f}")
            
            return result
    
    def enable_streaming(self, callback=None):
        """Enable real-time data streaming"""
        self.streaming_enabled = True
        self.stream_callback = callback
        
    def disable_streaming(self):
        """Disable real-time data streaming"""
        self.streaming_enabled = False
        self.stream_callback = None
    
    def export_data_csv(self) -> str:
        """Export data as CSV string"""
        with self.data_lock:
            if not self.data_points:
                return ""
            
            lines = ["Timestamp,Potential(V),Current(A),Cycle,Direction"]
            for point in self.data_points:
                lines.append(
                    f"{point.timestamp},{point.potential},{point.current},"
                    f"{point.cycle},{point.direction}"
                )
            
            return "\n".join(lines)
    
    def _measurement_worker(self):
        """Background thread for monitoring measurement progress"""
        logger.info("CV measurement worker started")
        
        try:
            while self.is_measuring:
                if self.is_paused:
                    time.sleep(0.1)
                    continue
                
                # Read data from device 
                # Note: This would typically involve reading serial data
                # For now, we'll simulate the measurement
                if self._read_measurement_data():
                    # Stream data if enabled
                    if self.streaming_enabled and self.stream_callback:
                        try:
                            self.stream_callback(self.get_data_points(limit=10))
                        except Exception as e:
                            logger.error(f"Streaming callback error: {e}")
                
                time.sleep(0.1)  # 10 Hz sampling rate to avoid queue overflow
                
        except Exception as e:
            logger.error(f"CV measurement worker error: {e}")
        finally:
            logger.info("CV measurement worker stopped")
    
    def _read_measurement_data(self) -> bool:
        """Read measurement data from device"""
        try:
            # Check for data timeout
            current_time = time.time()
            if self.last_data_time and (current_time - self.last_data_time) > self.data_timeout:
                logger.warning(f"No data received for {self.data_timeout} seconds, stopping measurement")
                
                # Try to send stop command to STM32
                try:
                    if self.scpi_handler and self.scpi_handler.is_connected:
                        # Use ABORT command like Desktop version
                        stop_result = self.scpi_handler.send_custom_command("POTEn:ABORt")
                        logger.info(f"Sent ABORT command to STM32: {stop_result}")
                except Exception as e:
                    logger.warning(f"Failed to send ABORT command to STM32: {e}")
                
                self.is_measuring = False
                return False
            
            # Check if we should use simulation mode
            if self.simulation_mode or not self.scpi_handler.is_connected:
                logger.debug("Using simulation mode for data reading")
                return self._simulate_measurement_data()
            
            # For STM32 CV measurements, we don't poll for data
            # STM32 sends data automatically after POTEn:CV:Start:ALL command
            # We just need to listen for incoming data from the SCPI handler
            
            # Check if there's any incoming data from STM32
            # The SCPI handler should buffer incoming data
            incoming_data = getattr(self.scpi_handler, 'get_buffered_data', lambda: None)()
            
            if not incoming_data:
                # No new data available, just continue
                return True
                
            logger.debug(f"STM32 incoming data: '{incoming_data.strip()}'")
            
            # Handle multiple lines of data if received
            lines = incoming_data.strip().split('\n')
            data_processed = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                logger.debug(f"Processing line: '{line}'")
                    
                # Handle SCPI error responses
                if line.startswith('**ERROR'):
                    logger.warning(f"STM32 SCPI error: {line}")
                    continue
                
                # Parse CV data: Expected format from STM32
                # Old format: "CV, timestamp, potential, current, cycle, direction, ..."
                # New format (Desktop compatible): "CV, time_ms, voltage, current, current_gain, cycle, adc0_raw, dac1_raw, point_no, dac0_raw"
                if line.startswith('CV,') or line.startswith('CV '):
                    try:
                        parts = line.split(',')
                        logger.debug(f"Parsed CV data parts: {parts}")
                        
                        # Desktop format with 10+ fields: "CV, time_ms, voltage, current, current_gain, cycle, adc0_raw, dac1_raw, point_no, dac0_raw"
                        if len(parts) >= 10 and parts[0].strip() == 'CV':
                            # Extract data from STM32 Desktop format
                            time_ms = float(parts[1].strip())           # STM32 timestamp (ms)
                            potential = float(parts[2].strip())         # Potential (V)
                            current_ua = float(parts[3].strip())        # Current from H743 (µA)
                            current = current_ua                        # Keep in µA (no conversion)
                            current_gain = float(parts[4].strip())      # Current gain
                            cycle = int(parts[5].strip())               # Cycle number
                            adc0_raw = int(parts[6].strip())            # ADC0 raw
                            dac1_raw = int(parts[7].strip())            # DAC1 raw
                            point_no = int(parts[8].strip())            # Point number
                            dac0_raw = int(parts[9].strip())            # DAC0 raw
                            
                            # Infer scan direction from voltage progression
                            if hasattr(self, 'last_potential') and self.last_potential is not None:
                                voltage_change = potential - self.last_potential
                                if abs(voltage_change) > 0.001:  # Threshold for direction change
                                    direction = 'forward' if voltage_change > 0 else 'reverse'
                                else:
                                    direction = self.scan_direction  # Keep current direction
                            else:
                                direction = 'forward'  # Default for first point
                            
                            self.last_potential = potential
                            
                        # Fallback to simple format: "CV, timestamp, potential, current, cycle, direction, ..."
                        elif len(parts) >= 6 and parts[0].strip() == 'CV':
                            time_ms = float(parts[1].strip())           # STM32 timestamp
                            potential = float(parts[2].strip())         # Potential (V)
                            current_ua = float(parts[3].strip())        # Current from H743 (µA)
                            current = current_ua                        # Keep in µA (no conversion)
                            cycle = int(parts[4].strip())               # Cycle number
                            direction_code = int(parts[5].strip())      # Direction (1=forward, 0=reverse)
                            direction = 'forward' if direction_code == 1 else 'reverse'
                        else:
                            logger.warning(f"Invalid CV data format: {line}")
                            continue
                        
                        # Enhanced hardware debug logging
                        if len(parts) >= 10:  # Desktop format with hardware info
                            logger.info(f"STM32 Data: V={potential:.3f}V, I={current:.1f}µA, Gain={current_gain}, ADC0={adc0_raw}, DAC1={dac1_raw}, Cycle={cycle}, Dir={direction}, Time={time_ms}ms")
                        else:
                            logger.info(f"STM32 Data: V={potential:.3f}V, I={current:.1f}µA, Cycle={cycle}, Dir={direction}, Time={time_ms}ms")
                        
                        # Data validation and filtering - CONDITIONAL
                        should_filter = False
                        
                        if not self.debug_mode:  # Only filter if NOT in debug mode
                            if hasattr(self, 'last_validated_potential') and self.last_validated_potential is not None:
                                voltage_jump = abs(potential - self.last_validated_potential)
                                # Only filter EXTREME voltage jumps (much more permissive)
                                if voltage_jump > 2.0:  # Increased from 0.5V to 2.0V
                                    logger.warning(f"Filtered EXTREME voltage jump: {voltage_jump:.3f}V")
                                    should_filter = True
                                elif voltage_jump > 0.5:
                                    # Log but don't filter moderate jumps
                                    logger.debug(f"Large voltage jump detected: {voltage_jump:.3f}V (allowing)")
                            
                            if hasattr(self, 'last_validated_current') and self.last_validated_current is not None:
                                current_jump = abs(current - self.last_validated_current)
                                # Only filter EXTREME current spikes - thresholds in µA scale
                                if current_jump > 1000:  # 1000µA = 1mA threshold
                                    logger.warning(f"Filtered EXTREME current spike: {current_jump:.1f}µA")
                                    should_filter = True
                                elif current_jump > 100:  # 100µA threshold
                                    # Log but don't filter moderate spikes
                                    logger.debug(f"Large current spike detected: {current_jump:.1f}µA (allowing)")
                        else:
                            # Debug mode - accept ALL data
                            logger.debug(f"🐛 DEBUG MODE: Accepting all data without filtering")
                        
                        # Only skip if we detected extreme values AND not in debug mode
                        if should_filter:
                            continue
                        
                        # Update validated values for next comparison
                        self.last_validated_potential = potential
                        self.last_validated_current = current
                        
                        # Update last data time when we receive valid data
                        self.last_data_time = time.time()
                        
                        # Update current state
                        self.current_potential = potential
                        self.current_cycle = cycle
                        self.scan_direction = direction
                        
                        # Add data point
                        with self.data_lock:
                            data_point = CVDataPoint(
                                timestamp=time.time(),  # Use system time for consistency
                                potential=potential,
                                current=current,
                                cycle=cycle,
                                direction=direction
                            )
                            self.data_points.append(data_point)
                            logger.info(f"✅ ADDED data point #{len(self.data_points)}: V={potential:.3f}V, I={current:.1f}µA")
                            
                        data_processed = True
                        
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse CV data '{line}': {e}")
                        continue
                
                # Check for measurement completion signals from STM32
                elif any(completion_signal in line for completion_signal in 
                        ['CV Operation Finished', 'CV Operation Complete', 'CV_COMPLETE', 'COMPLETE']):
                    logger.info(f"CV measurement completed by STM32: {line.strip()}")
                    self.is_measuring = False
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to read measurement data: {e}")
            # Fall back to simulation on any error
            logger.info("Falling back to simulation mode due to error")
            return self._simulate_measurement_data()
    
    def _simulate_measurement_data(self) -> bool:
        """Simulate CV measurement data for development/testing"""
        try:
            if not self.current_params or self.start_time is None:
                return False
                
            current_time = time.time()
            elapsed = current_time - self.start_time
            
            # Simulate potential progression for proper CV curve
            # Each cycle: begin -> upper -> lower -> begin
            cycle_duration = 2 * (abs(self.current_params.upper - self.current_params.begin) + 
                                abs(self.current_params.lower - self.current_params.begin)) / self.current_params.rate
            
            cycle_time = elapsed % cycle_duration
            half_cycle = cycle_duration / 2
            
            if cycle_time < half_cycle:
                # Forward scan: begin -> upper -> lower
                if cycle_time < half_cycle / 2:
                    # begin -> upper
                    progress = (cycle_time) / (half_cycle / 2)
                    self.current_potential = (
                        self.current_params.begin + 
                        progress * (self.current_params.upper - self.current_params.begin)
                    )
                else:
                    # upper -> lower
                    progress = (cycle_time - half_cycle / 2) / (half_cycle / 2)
                    self.current_potential = (
                        self.current_params.upper - 
                        progress * (self.current_params.upper - self.current_params.lower)
                    )
                self.scan_direction = 'forward'
            else:
                # Reverse scan: lower -> begin
                progress = (cycle_time - half_cycle) / half_cycle
                self.current_potential = (
                    self.current_params.lower + 
                    progress * (self.current_params.begin - self.current_params.lower)
                )
                self.scan_direction = 'reverse'
            
            # Update cycle number
            self.current_cycle = int(elapsed / cycle_duration) + 1
            
            # Stop if cycles completed
            if self.current_cycle > self.current_params.cycles:
                self.is_measuring = False
                return False
            
            # Simulate current response (more realistic CV curve)
            # Simple redox peak simulation
            peak_potential = (self.current_params.upper + self.current_params.lower) / 2
            peak_width = 0.1  # V
            peak_current = 0.001  # A
            
            # Gaussian peak simulation
            import math
            distance_from_peak = abs(self.current_potential - peak_potential)
            if distance_from_peak < peak_width:
                peak_factor = math.exp(-(distance_from_peak / peak_width) ** 2)
                simulated_current = peak_current * peak_factor
            else:
                simulated_current = 0.0001  # Background current
            
            # Add some noise
            noise = 0.00001 * (2 * (time.time() % 1) - 1)
            simulated_current += noise
            
            # Add data point
            with self.data_lock:
                data_point = CVDataPoint(
                    timestamp=current_time,
                    potential=self.current_potential,
                    current=simulated_current,
                    cycle=self.current_cycle,
                    direction=self.scan_direction
                )
                self.data_points.append(data_point)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to simulate measurement data: {e}")
            return False
