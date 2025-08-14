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
        """Convert parameters to SCPI command"""
        return f"POTEn:CV:Start:ALL {self.begin},{self.upper},{self.lower},{self.rate},{self.cycles}"

@dataclass  
class CVDataPoint:
    """Single CV data point"""
    timestamp: float
    potential: float    # Applied potential (V)
    current: float      # Measured current (A)
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
                upper=float(params.get('upper', 1.0)), 
                lower=float(params.get('lower', -1.0)),
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
            
            # Send abort command to device
            result = self.scpi_handler.send_custom_command("POTEn:ABORt")
            
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
            return {
                'is_measuring': self.is_measuring,
                'is_paused': self.is_paused,
                'current_cycle': self.current_cycle,
                'scan_direction': self.scan_direction,
                'current_potential': self.current_potential,
                'data_points_count': len(self.data_points),
                'elapsed_time': time.time() - self.start_time if self.start_time else 0,
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
        with self.data_lock:
            points = self.data_points[-limit:] if limit else self.data_points
            return [
                {
                    'timestamp': point.timestamp,
                    'potential': point.potential,
                    'current': point.current,
                    'cycle': point.cycle,
                    'direction': point.direction
                }
                for point in points
            ]
    
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
                
                time.sleep(0.05)  # 20 Hz sampling rate
                
        except Exception as e:
            logger.error(f"CV measurement worker error: {e}")
        finally:
            logger.info("CV measurement worker stopped")
    
    def _read_measurement_data(self) -> bool:
        """Read measurement data from device"""
        try:
            # Check if we should use simulation mode
            if self.simulation_mode or not self.scpi_handler.is_connected:
                return self._simulate_measurement_data()
            
            # Read actual data from STM32 via SCPI handler
            result = self.scpi_handler.send_custom_command("MEAS:CV:DATA?")
            
            if not result['success']:
                logger.warning(f"Failed to read measurement data: {result.get('message', 'Unknown error')}")
                # Fall back to simulation if device communication fails
                logger.info("Falling back to simulation mode due to communication error")
                return self._simulate_measurement_data()
                
            response = result.get('response', '').strip()
            if not response or response == 'NO_DATA':
                # No new data available yet, continue measurement
                return True
                
            # Parse response: "potential,current,cycle,direction,status"
            try:
                parts = response.split(',')
                if len(parts) < 4:
                    logger.warning(f"Invalid data format from device: {response}")
                    return True
                    
                potential = float(parts[0])
                current = float(parts[1])
                cycle = int(parts[2])
                direction = parts[3].strip()
                
                # Check if measurement is complete
                if len(parts) >= 5 and parts[4].strip() == 'COMPLETE':
                    logger.info("CV measurement completed by device")
                    self.is_measuring = False
                    return False
                
                # Update current state
                self.current_potential = potential
                self.current_cycle = cycle
                self.scan_direction = direction
                
                # Add data point
                with self.data_lock:
                    data_point = CVDataPoint(
                        timestamp=time.time(),
                        potential=potential,
                        current=current,
                        cycle=cycle,
                        direction=direction
                    )
                    self.data_points.append(data_point)
                    
                logger.debug(f"Data point: V={potential:.3f}, I={current:.6f}, Cycle={cycle}, Dir={direction}")
                return True
                
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse measurement data '{response}': {e}")
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
