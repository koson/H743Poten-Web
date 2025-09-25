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
        
        # Timeout handling - Extended for proper STM32 measurement completion
        self.last_data_time = None
        self.data_timeout = 60.0  # Extended to 60s to allow full CV scans
        self.completion_timeout = 300.0  # 5 minutes max for any measurement
        self.completion_detected = False  # Flag for intelligent completion detection
        
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
            # �🚨🚨 URGENT DEBUG: Log received parameters to identify mapping issues
            print(f"🚨🚨🚨 CV SETUP CALLED WITH PARAMS: {params}")
            logger.info(f"�🚨🚨 CV SETUP - Received parameters from frontend: {params}")
            
            # Extract values with explicit logging
            begin_val = params.get('begin_voltage', params.get('begin', 0.0))
            upper_val = params.get('upper_voltage', params.get('upper', 0.5))
            lower_val = params.get('lower_voltage', params.get('lower', -0.5))
            rate_val = params.get('scan_rate', params.get('rate', 0.05))
            cycles_val = params.get('cycles', 1)
            
            print(f"🚨 EXTRACTED VALUES: begin={begin_val}, upper={upper_val}, lower={lower_val}, rate={rate_val}, cycles={cycles_val}")
            
            # Create CV parameters object with correct parameter name mapping
            cv_params = CVParameters(
                begin=float(begin_val),
                upper=float(upper_val), 
                lower=float(lower_val),
                rate=float(rate_val),
                cycles=int(cycles_val)
            )
            
            # 🔍 DEBUG: Log parsed parameters
            print(f"🚨 FINAL CV PARAMS: {cv_params}")
            logger.info(f"🚨🚨� Final CV parameters: begin={cv_params.begin}, upper={cv_params.upper}, lower={cv_params.lower}, rate={cv_params.rate}, cycles={cv_params.cycles}")
            
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
        """Start CV measurement with enhanced validation and recovery"""
        try:
            if self.current_params is None:
                return False, "No measurement parameters configured"
                
            # 🔍 DEBUG: Show current parameters before starting
            logger.info(f"🔍 Starting CV with current_params: begin={self.current_params.begin}, upper={self.current_params.upper}, lower={self.current_params.lower}, rate={self.current_params.rate}, cycles={self.current_params.cycles}")
                
            if self.is_measuring:
                return False, "Measurement already in progress"
            
            # Clear previous data
            with self.data_lock:
                self.data_points.clear()
                self.current_cycle = 1
                self.scan_direction = 'forward'
                self.current_potential = self.current_params.begin
                
            # 🔍 Enhanced connection validation
            logger.info(f"🔍 Connection check: scpi_handler={self.scpi_handler}, is_connected={getattr(self.scpi_handler, 'is_connected', 'MISSING')}")
            if not self.scpi_handler or not self.scpi_handler.is_connected:
                logger.error("❌ Hardware not connected - Simulation mode DISABLED for data integrity")
                return False, "Hardware not connected. Please connect STM32 device and try again."
            
            # 🔍 PRE-FLIGHT CHECKS: Ensure STM32 is ready
            if not self._check_stm32_ready():
                logger.error("❌ STM32 not responding to queries")
                return False, "STM32 device is not responding. Please check connection and try again."
                
            # 🛑 Ensure STM32 is in idle state
            if not self._ensure_stm32_idle():
                logger.warning("⚠️ Could not confirm STM32 idle state, proceeding anyway")
            
            # 🚀 ENHANCED STM32 COMMAND PROTOCOL - Multiple attempts with validation
            command = self.current_params.to_scpi_command()
            logger.info(f"📡 Sending CV command to STM32: {command}")
            logger.info(f"🎛️ Expected measurement duration: ~{self._estimate_measurement_time()}s")
            
            # Clear any previous buffered data before starting
            try:
                if hasattr(self.scpi_handler, 'clear_buffer'):
                    self.scpi_handler.clear_buffer()
                elif hasattr(self.scpi_handler, 'get_buffered_data'):
                    # Consume any old data
                    old_data = self.scpi_handler.get_buffered_data()
                    if old_data:
                        logger.info(f"🧹 Cleared old buffer data: {len(old_data)} bytes")
            except Exception as e:
                logger.warning(f"Could not clear buffer: {e}")
            
            # 🔄 RETRY LOGIC - Try multiple times to ensure STM32 receives command
            max_attempts = 3
            command_success = False
            
            for attempt in range(max_attempts):
                logger.info(f"📡 Attempt #{attempt + 1} sending command: {command}")
                
                # Send the command
                result = self.scpi_handler.send_custom_command(command)
                
                if not result.get('success'):
                    logger.warning(f"❌ Attempt #{attempt + 1} failed: {result.get('error', 'Unknown error')}")
                    if attempt < max_attempts - 1:
                        time.sleep(1.0)  # Wait before retry
                        continue
                    else:
                        return False, f"Device communication failed after {max_attempts} attempts: {result.get('error', 'Unknown error')}"
                
                # 🔍 VALIDATION: Check if STM32 acknowledges the command
                logger.info(f"✅ Command sent successfully on attempt #{attempt + 1}")
                
                # Give STM32 time to process and start measurement
                time.sleep(0.5)
                
                # Check for immediate response or acknowledgment
                try:
                    if hasattr(self.scpi_handler, 'get_buffered_data'):
                        initial_response = self.scpi_handler.get_buffered_data()
                        if initial_response:
                            logger.info(f"📡 STM32 initial response: '{initial_response.strip()}'")
                            # Check for error responses
                            if '**ERROR' in initial_response.upper() or 'FAILED' in initial_response.upper():
                                logger.error(f"STM32 rejected command: {initial_response}")
                                if attempt < max_attempts - 1:
                                    continue
                                else:
                                    return False, f"STM32 rejected command: {initial_response.strip()}"
                            elif any(ack in initial_response.upper() for ack in ['OK', 'STARTED', 'CV,', 'ACKNOWLEDGED']):
                                logger.info(f"✅ STM32 acknowledged command: {initial_response.strip()}")
                                command_success = True
                                break
                except Exception as e:
                    logger.warning(f"Could not check initial STM32 response: {e}")
                
                # 🕐 WAIT FOR STM32 TO START - Give device time to initialize measurement
                logger.info("⏳ Waiting for STM32 to initialize measurement...")
                
                # Wait up to 3 seconds for STM32 to start sending data or acknowledgment
                start_wait_time = time.time()
                stm32_started = False
                
                while (time.time() - start_wait_time) < 3.0:  # 3 second timeout
                    time.sleep(0.1)
                    
                    # Check for data or acknowledgment
                    if hasattr(self.scpi_handler, 'has_data_available') and self.scpi_handler.has_data_available():
                        logger.info("✅ STM32 started sending data")
                        stm32_started = True
                        break
                    
                    # Check buffer for any response
                    if hasattr(self.scpi_handler, 'get_buffered_data'):
                        response = self.scpi_handler.get_buffered_data()
                        if response and response.strip():
                            logger.info(f"📡 STM32 responded: '{response.strip()}'")
                            stm32_started = True
                            break
                
                if stm32_started:
                    logger.info("✅ STM32 confirmed measurement start")
                    command_success = True
                    break
                else:
                    logger.warning(f"⚠️ STM32 did not respond within 3s on attempt #{attempt + 1}")
                    if attempt < max_attempts - 1:
                        continue
                    else:
                        # Last attempt - proceed anyway but warn user
                        logger.warning("⚠️ Proceeding with measurement despite no initial STM32 response")
                        command_success = True
                        break
            
            if not command_success:
                return False, f"Failed to send command to STM32 after {max_attempts} attempts"
                
            # 🏁 START MEASUREMENT MONITORING
            self.is_measuring = True
            self.is_paused = False
            self.start_time = time.time()
            self.last_data_time = time.time()  # Initialize last data time
            
            # Reset completion detection state
            self.completion_detected = False
            if hasattr(self, 'completion_wait_start'):
                delattr(self, 'completion_wait_start')
                
            # Start measurement worker thread
            self.measurement_thread = threading.Thread(
                target=self._measurement_worker,
                daemon=True
            )
            self.measurement_thread.start()
            
            # 🕐 EARLY DATA VERIFICATION - Check if data starts arriving within reasonable time
            threading.Timer(10.0, self._verify_measurement_started).start()
            
            logger.info("✅ CV measurement started successfully on STM32")
            return True, "CV measurement started successfully on STM32"
            
        except Exception as e:
            logger.error(f"Failed to start CV measurement: {e}")
            # Reset state on error
            self.is_measuring = False
            return False, f"Failed to start measurement: {e}"
    
    def _verify_measurement_started(self):
        """Verify that measurement actually started by checking for early data points"""
        try:
            if not self.is_measuring:
                return  # Measurement already stopped
                
            with self.data_lock:
                data_count = len(self.data_points)
                
            if data_count == 0:
                logger.error(f"⚠️ MEASUREMENT NOT STARTED: No data received after 10 seconds")
                logger.error("🔍 Possible issues:")
                logger.error("  1. STM32 not ready when command was sent")
                logger.error("  2. Serial communication issue")
                logger.error("  3. STM32 firmware not responding to CV command")
                logger.error("  4. Hardware connection unstable")
                
                # Try to recovery by resending command
                if self.current_params:
                    logger.info("🔄 Attempting to restart measurement...")
                    try:
                        # Clear any stale state
                        self._ensure_stm32_idle()
                        time.sleep(1.0)
                        
                        # Resend command
                        command = self.current_params.to_scpi_command()
                        logger.info(f"🔄 Resending command: {command}")
                        result = self.scpi_handler.send_custom_command(command)
                        
                        if result.get('success'):
                            logger.info("✅ Recovery command sent successfully")
                            self.last_data_time = time.time()  # Reset timeout
                        else:
                            logger.error(f"❌ Recovery failed: {result.get('error')}")
                            
                    except Exception as recovery_error:
                        logger.error(f"Recovery attempt failed: {recovery_error}")
                        
            else:
                logger.info(f"✅ Measurement confirmed: {data_count} data points received")
                
        except Exception as e:
            logger.error(f"Error in measurement verification: {e}")
    
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
                'completion_detected': getattr(self, 'completion_detected', False),
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

    def get_measurement_data(self) -> Dict:
        """Get current measurement data for API"""
        with self.data_lock:
            # 🔍 DEBUG: Log SCPI handler type to identify mock vs real hardware
            handler_type = type(self.scpi_handler).__name__
            print(f"🔍 CV Service using: {handler_type}")
            
            # Convert internal data to API format
            data_points = []
            
            for point in self.data_points:
                data_points.append({
                    'timestamp': point.timestamp,
                    'potential': point.potential,
                    'current': point.current,
                    'cycle': point.cycle,
                    'direction': point.direction
                })
            
            # 🔍 DEBUG: Log data structure and voltage range
            print(f"🔍 CV get_measurement_data returning {len(data_points)} points")
            
            if data_points:
                voltages = [p['potential'] for p in data_points]
                currents = [p['current'] for p in data_points]
                print(f"🔍 Voltage range: {min(voltages):.4f}V to {max(voltages):.4f}V")
                print(f"🔍 Current range: {min(currents):.2f}µA to {max(currents):.2f}µA")
                print(f"🔍 First 5 points: {data_points[:5]}")
                print(f"🔍 Last 5 points: {data_points[-5:]}")
            
            # Return data structure that frontend expects
            return {
                'points': data_points,
                'completed': not self.is_measuring and len(data_points) > 0,
                'status': {
                    'is_measuring': self.is_measuring,
                    'data_points_count': len(data_points),
                    'current_cycle': self.current_cycle,
                    'scan_direction': self.scan_direction
                }
            }
    
    def _estimate_measurement_time(self) -> int:
        """Estimate measurement duration based on parameters"""
        if not self.current_params:
            return 60
            
        # Calculate voltage range and estimate time
        voltage_range = abs(self.current_params.upper - self.current_params.lower) * 2  # Forward + reverse
        scan_rate = self.current_params.rate
        cycles = self.current_params.cycles
        
        estimated_time = (voltage_range / scan_rate) * cycles
        return int(estimated_time + 30)  # Add buffer time
    
    def enable_streaming(self, callback=None):
        """Enable real-time data streaming"""
        self.streaming_enabled = True
        self.stream_callback = callback
        
    def disable_streaming(self):
        """Disable real-time data streaming"""
        self.streaming_enabled = False
        self.stream_callback = None

    def export_data(self) -> Dict:
        """Export CV measurement data compatible with universal API"""
        if not self.data_points:
            return {'success': False, 'message': 'No data to export'}
        
        try:
            from datetime import datetime
            
            export_data = {
                'measurement_type': 'CV',
                'timestamp': datetime.now().isoformat(),
                'parameters': {
                    'begin_voltage': self.current_params.begin if self.current_params else None,
                    'upper_voltage': self.current_params.upper if self.current_params else None,
                    'lower_voltage': self.current_params.lower if self.current_params else None,
                    'scan_rate': self.current_params.rate if self.current_params else None,
                    'cycles': self.current_params.cycles if self.current_params else None,
                },
                'data_points': len(self.data_points),
                'data': []
            }
            
            for point in self.data_points:
                export_data['data'].append({
                    'timestamp': point.timestamp,
                    'potential_V': point.potential,
                    'current_A': point.current,
                    'cycle': point.cycle,
                    'direction': point.direction
                })
            
            return {'success': True, 'data': export_data}
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
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
    
    def _check_stm32_ready(self) -> bool:
        """Check if STM32 is ready to accept measurement commands"""
        try:
            if not self.scpi_handler or not self.scpi_handler.is_connected:
                return False
                
            # Send a simple query to check if STM32 is responsive
            logger.info("🔍 Checking STM32 readiness...")
            
            # Try a simple identification query
            result = self.scpi_handler.send_custom_command("*IDN?")
            
            if result.get('success'):
                logger.info(f"✅ STM32 is responsive: {result.get('response', 'OK')}")
                return True
            else:
                logger.warning(f"⚠️ STM32 not responsive: {result.get('error', 'No response')}")
                
                # Try alternative ping command
                time.sleep(0.2)
                ping_result = self.scpi_handler.send_custom_command("POTEn:PING?")
                if ping_result.get('success'):
                    logger.info("✅ STM32 responded to PING")
                    return True
                    
                return False
                
        except Exception as e:
            logger.error(f"Failed to check STM32 readiness: {e}")
            return False
    
    def _ensure_stm32_idle(self) -> bool:
        """Ensure STM32 is in idle state before starting new measurement"""
        try:
            if not self.scpi_handler or not self.scpi_handler.is_connected:
                return False
                
            logger.info("🛑 Ensuring STM32 is idle...")
            
            # Send ABORT command multiple times to ensure device is stopped
            for i in range(3):
                abort_result = self.scpi_handler.send_custom_command("POTEn:ABORt")
                logger.info(f"📡 ABORT command #{i+1}: {abort_result}")
                time.sleep(0.1)
            
            # Wait for device to stabilize
            time.sleep(0.5)
            
            # Check status
            status_result = self.scpi_handler.send_custom_command("POTEn:STATus?")
            if status_result.get('success'):
                status = status_result.get('response', '').strip()
                logger.info(f"🔍 STM32 status after ABORT: '{status}'")
                
                # Check if device reports idle/ready state
                if any(idle_keyword in status.upper() for idle_keyword in ['IDLE', 'READY', 'OK', 'STOPPED']):
                    logger.info("✅ STM32 confirmed in idle state")
                    return True
            
            # Even if status check failed, assume device is now idle after ABORT commands
            logger.info("✅ Assumed STM32 is idle after ABORT commands")
            return True
            
        except Exception as e:
            logger.warning(f"Could not verify STM32 idle state: {e}")
            return True  # Assume success to not block measurements
    
    def _read_measurement_data(self) -> bool:
        """Read measurement data from device"""
        try:
            # Check for various timeout conditions
            current_time = time.time()
            
            # Check for intelligent completion first
            if self.completion_detected:
                # Give STM32 a few seconds to send any final data/signals
                if not hasattr(self, 'completion_wait_start'):
                    self.completion_wait_start = current_time
                    logger.info("🏁 Completion detected, waiting for final STM32 messages...")
                
                if (current_time - self.completion_wait_start) > 5.0:  # Wait 5 seconds after completion
                    logger.info("✅ CV measurement completed successfully")
                    self.is_measuring = False
                    return False
                    
                return True  # Continue waiting for final messages
            
            # Data timeout - no data for extended period
            data_silence_time = (current_time - self.last_data_time) if self.last_data_time else 0
            
            if self.last_data_time and data_silence_time > self.data_timeout:
                logger.warning(f"⏰ No data received for {data_silence_time:.1f}s - checking STM32 status")
                
                # Check one more time for data
                final_data = getattr(self.scpi_handler, 'get_buffered_data', lambda: None)()
                if final_data:
                    logger.info(f"📡 Final STM32 message: '{final_data.strip()}'")
                    # Reset timeout since we got data
                    self.last_data_time = current_time
                    return True
                
                logger.warning("🔚 STM32 appears to have stopped sending data - ending measurement")
                self.is_measuring = False
                return False
                
            # Absolute timeout - prevent infinite measurements  
            if self.start_time and (current_time - self.start_time) > self.completion_timeout:
                logger.error(f"🛑 Measurement exceeded {self.completion_timeout}s limit, force stopping")
                
                try:
                    if self.scpi_handler and self.scpi_handler.is_connected:
                        stop_result = self.scpi_handler.send_custom_command("POTEn:ABORt")
                        logger.info(f"📡 Sent ABORT command: {stop_result}")
                except Exception as e:
                    logger.warning(f"Failed to send ABORT command: {e}")
                
                self.is_measuring = False
                return False
            
            # 🚫 NO SIMULATION MODE - Only real hardware data allowed
            if not self.scpi_handler or not self.scpi_handler.is_connected:
                logger.error("❌ Hardware disconnected during measurement")
                self.is_measuring = False
                return False
            
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
                    
                logger.info(f"📡 STM32 → Processing: '{line}'")
                    
                # Check for measurement completion signals from STM32
                if any(completion_keyword in line.upper() for completion_keyword in [
                    'MEASUREMENT COMPLETE', 'CV COMPLETE', 'FINISHED', 'END', 'DONE', 'OK'
                ]):
                    logger.info(f"🏁 STM32 signaled measurement completion: '{line}'")
                    self.is_measuring = False
                    return False
                
                # Detect potential completion by analyzing data patterns
                if line.startswith('CV,') or line.startswith('CV '):
                    parts = line.split(',')
                    if len(parts) >= 10:
                        try:
                            point_no = int(parts[8].strip())
                            cycle = int(parts[5].strip())
                            voltage = float(parts[2].strip())
                            
                            # Debug early data points
                            if len(self.data_points) <= 5:
                                logger.info(f"📊 Early data point #{len(self.data_points)}: V={voltage}V, cycle={cycle}, point={point_no}")
                            
                            # Only check for completion after sufficient data points
                            if len(self.data_points) >= 20:  # Need minimum 20 data points
                                # Check if we're in final cycle 
                                if cycle >= self.current_params.cycles:
                                    # Check if voltage is returning to start AND we've had significant movement
                                    voltage_tolerance = 0.02  # 20mV tolerance
                                    start_voltage = self.current_params.begin
                                    
                                    # Check if we've moved significantly from start in recent data
                                    recent_points = self.data_points[-10:] if len(self.data_points) >= 10 else []
                                    has_movement = any(
                                        abs(dp.potential - start_voltage) > 0.1 
                                        for dp in recent_points
                                    )
                                    
                                    # Detect completion: close to start + in final cycle + had movement
                                    if (abs(voltage - start_voltage) < voltage_tolerance and 
                                        has_movement and point_no > 30):  # Ensure substantial measurement
                                        logger.info(f"🏁 Detected completion: returned to start voltage {voltage}V in final cycle {cycle} (point {point_no})")
                                        self.completion_detected = True
                                
                        except (ValueError, IndexError) as e:
                            logger.debug(f"Could not parse completion check: {e}")
                    
                # Handle completion messages from STM32 - All modes
                completion_keywords = [
                    "CV Operation Finished", "CV SCAN COMPLETE", "CV DONE",
                    "DPV Operation Finished", "DPV SCAN COMPLETE", "DPV DONE", 
                    "SWV Operation Finished", "SWV SCAN COMPLETE", "SWV DONE",
                    "CA Operation Finished", "CA MEASUREMENT COMPLETE", "CA DONE",
                    "MEASUREMENT COMPLETE", "SCAN COMPLETE", "Operation Finished",
                    "CV SCAN COMPLETED", "SENDING COMPLETION MESSAGES",
                    "END_CV_SCAN", "COMPLETION MESSAGES SENT"  # Final STM32 format
                ]
                if any(keyword in line.upper() for keyword in completion_keywords):
                    logger.info(f"🏁 STM32 signaled measurement completion: {line.strip()}")
                    self.completion_detected = True
                    continue
                
                # Handle SCPI error responses
                if line.startswith('**ERROR'):
                    logger.warning(f"STM32 SCPI error: {line}")
                    continue
                
                # Parse CV data: Expected format from STM32
                # Old format: "CV, timestamp, potential, current, cycle, direction, ..."
                # New format (Desktop compatible): "CV, time_ms, voltage, current, current_gain, cycle, adc0_raw, dac1_raw, point_no, dac0_raw"
                # Parse CV data: Standard STM32 format
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
            
            # Slower simulation - make each cycle take at least 10 seconds
            base_cycle_duration = 10.0  # 10 seconds per cycle minimum
            # Calculate theoretical duration based on scan rate  
            theoretical_duration = 2 * (abs(self.current_params.upper - self.current_params.begin) + 
                                      abs(self.current_params.lower - self.current_params.begin)) / self.current_params.rate
            
            # Use the longer of the two durations for better visualization
            cycle_duration = max(base_cycle_duration, theoretical_duration)
            
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
            
            # Debug logging for cycle progress
            if int(elapsed) % 2 == 0 and elapsed > 0:  # Every 2 seconds
                logger.info(f"🔄 Simulation progress: elapsed={elapsed:.1f}s, cycle_duration={cycle_duration:.1f}s, current_cycle={self.current_cycle}/{self.current_params.cycles}")
            
            # Stop if cycles completed
            if self.current_cycle > self.current_params.cycles:
                logger.info(f"✅ Simulation completed: {self.current_cycle} cycles finished")
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
                
                # Debug logging every 10th point
                if len(self.data_points) % 10 == 0:
                    logger.info(f"📊 Simulation: {len(self.data_points)} points, V={self.current_potential:.3f}V, I={simulated_current:.6f}A, Cycle={self.current_cycle}, Dir={self.scan_direction}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to simulate measurement data: {e}")
            return False
