"""
Cross-Instrument Calibration Service
Calibrates STM32H743 measurements to match PalmSens reference standard
Supports KEYSIGHT 33461A calibrated data and raw STM32 data
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class CalibrationPoint:
    """Single calibration data point"""
    # STM32 data (KEYSIGHT calibrated)
    timestamp_us: float
    re_voltage: float           # REVoltage (KEYSIGHT calibrated)
    we_voltage: float           # WEVoltage from TIA (KEYSIGHT calibrated) 
    we_current_range: int       # TIA range (1=1kΩ, 2=10kΩ, 3=100kΩ, 4=1MΩ)
    cycle_no: int
    
    # STM32 raw data (for future raw calibration)
    dac_ch1: int               # Raw DAC value for RE
    dac_ch2: int               # Raw DAC value for virtual ground
    counter: int               # Data sequence number
    lut_data: int              # LUT data for DAC_CH1
    
    # Calculated current from TIA
    we_current: float          # Calculated from WE voltage and TIA resistance

@dataclass
class CalibrationDataSet:
    """Complete calibration dataset for one measurement"""
    measurement_mode: str      # CV, SWV, DPV, CA
    sample_id: str
    instrument_type: str       # 'stm32' or 'palmsens'
    timestamp: datetime
    scan_rate: Optional[float] = None
    voltage_start: Optional[float] = None
    voltage_end: Optional[float] = None
    
    # Data points
    data_points: List[CalibrationPoint] = None
    
    # Processed CV data (voltage, current pairs)
    cv_data: List[Dict[str, float]] = None

class CrossInstrumentCalibrator:
    """Main calibration service for cross-instrument calibration"""
    
    # TIA resistances for current calculation (Ohms)
    TIA_RESISTANCES = {
        1: 1000,      # 1kΩ
        2: 10000,     # 10kΩ  
        3: 100000,    # 100kΩ
        4: 1000000    # 1MΩ
    }
    
    def __init__(self):
        self.calibration_models = {}
        self.calibration_history = []
        
    def parse_stm32_data(self, csv_data: str, sample_id: str) -> CalibrationDataSet:
        """
        Parse STM32 CSV data format into CalibrationDataSet
        
        Args:
            csv_data: CSV string with STM32 measurement data
            sample_id: Sample identifier
            
        Returns:
            CalibrationDataSet with parsed data
        """
        try:
            # Parse CSV data
            lines = csv_data.strip().split('\n')
            header = lines[0].split(',')
            
            # Validate header format
            expected_columns = ['Mode', 'TimeStamp(us)', 'REVoltage', 'WEVoltage', 
                               'WECurrentRange', 'CycleNo', 'DAC_CH1', 'DAC_CH2', 
                               'counter', 'LUTData']
            
            if header != expected_columns:
                raise ValueError(f"Invalid CSV header. Expected: {expected_columns}, Got: {header}")
            
            data_points = []
            measurement_mode = None
            
            for line in lines[1:]:
                if not line.strip():
                    continue
                    
                values = line.split(',')
                if len(values) != len(header):
                    continue
                
                # Parse data point
                mode = values[0].strip()
                if measurement_mode is None:
                    measurement_mode = mode
                    
                timestamp_us = float(values[1])
                re_voltage = float(values[2])
                we_voltage = float(values[3])
                we_current_range = int(values[4])
                cycle_no = int(values[5])
                dac_ch1 = int(values[6])
                dac_ch2 = int(values[7])
                counter = int(values[8])
                lut_data = int(values[9])
                
                # Calculate current from TIA output voltage
                tia_resistance = self.TIA_RESISTANCES.get(we_current_range, 1000)
                we_current = we_voltage / tia_resistance  # I = V/R
                
                point = CalibrationPoint(
                    timestamp_us=timestamp_us,
                    re_voltage=re_voltage,
                    we_voltage=we_voltage,
                    we_current_range=we_current_range,
                    cycle_no=cycle_no,
                    dac_ch1=dac_ch1,
                    dac_ch2=dac_ch2,
                    counter=counter,
                    lut_data=lut_data,
                    we_current=we_current
                )
                
                data_points.append(point)
            
            # Convert to CV data format (voltage, current pairs)
            cv_data = []
            for point in data_points:
                cv_data.append({
                    'voltage': point.re_voltage,
                    'current': point.we_current
                })
            
            # Create dataset
            dataset = CalibrationDataSet(
                measurement_mode=measurement_mode,
                sample_id=sample_id,
                instrument_type='stm32',
                timestamp=datetime.now(),
                data_points=data_points,
                cv_data=cv_data
            )
            
            # Detect scan parameters
            if cv_data:
                voltages = [d['voltage'] for d in cv_data]
                dataset.voltage_start = min(voltages)
                dataset.voltage_end = max(voltages)
                
                # Estimate scan rate from time and voltage change
                if len(data_points) > 1:
                    time_diff = (data_points[-1].timestamp_us - data_points[0].timestamp_us) / 1e6  # Convert to seconds
                    voltage_diff = abs(dataset.voltage_end - dataset.voltage_start)
                    if time_diff > 0:
                        dataset.scan_rate = (voltage_diff / time_diff) * 1000  # mV/s
            
            logger.info(f"Parsed STM32 data: {len(data_points)} points, mode={measurement_mode}")
            return dataset
            
        except Exception as e:
            logger.error(f"Error parsing STM32 data: {e}")
            raise
    
    def calibrate_stm32_to_palmsens(self, stm32_dataset: CalibrationDataSet, 
                                   palmsens_reference: CalibrationDataSet) -> Dict[str, Any]:
        """
        Calibrate STM32 measurement to match PalmSens reference
        
        Args:
            stm32_dataset: STM32 measurement data
            palmsens_reference: PalmSens reference measurement
            
        Returns:
            Calibration results with calibrated data and statistics
        """
        try:
            if stm32_dataset.cv_data is None or palmsens_reference.cv_data is None:
                raise ValueError("Both datasets must have CV data")
            
            # Extract voltage and current arrays
            stm32_voltages = np.array([d['voltage'] for d in stm32_dataset.cv_data])
            stm32_currents = np.array([d['current'] for d in stm32_dataset.cv_data])
            
            palmsens_voltages = np.array([d['voltage'] for d in palmsens_reference.cv_data])
            palmsens_currents = np.array([d['current'] for d in palmsens_reference.cv_data])
            
            # Align data points by interpolating to common voltage grid
            common_voltages = np.linspace(
                max(min(stm32_voltages), min(palmsens_voltages)),
                min(max(stm32_voltages), max(palmsens_voltages)),
                min(len(stm32_voltages), len(palmsens_voltages))
            )
            
            # Interpolate both datasets to common voltage grid
            stm32_currents_interp = np.interp(common_voltages, stm32_voltages, stm32_currents)
            palmsens_currents_interp = np.interp(common_voltages, palmsens_voltages, palmsens_currents)
            
            # Calculate calibration factors
            # Linear calibration: I_calibrated = slope * I_stm32 + offset
            if len(stm32_currents_interp) > 1:
                # Use least squares fitting
                A = np.vstack([stm32_currents_interp, np.ones(len(stm32_currents_interp))]).T
                slope, offset = np.linalg.lstsq(A, palmsens_currents_interp, rcond=None)[0]
            else:
                slope = 1.0
                offset = 0.0
            
            # Apply calibration to original STM32 data
            calibrated_cv_data = []
            for point in stm32_dataset.cv_data:
                calibrated_current = slope * point['current'] + offset
                calibrated_cv_data.append({
                    'voltage': point['voltage'],
                    'current': calibrated_current
                })
            
            # Calculate calibration statistics
            stm32_calibrated_interp = slope * stm32_currents_interp + offset
            mse = np.mean((stm32_calibrated_interp - palmsens_currents_interp) ** 2)
            mae = np.mean(np.abs(stm32_calibrated_interp - palmsens_currents_interp))
            r_squared = 1 - (np.sum((palmsens_currents_interp - stm32_calibrated_interp) ** 2) / 
                            np.sum((palmsens_currents_interp - np.mean(palmsens_currents_interp)) ** 2))
            
            # Calculate current range and percentage errors
            current_range_palmsens = np.max(palmsens_currents_interp) - np.min(palmsens_currents_interp)
            current_range_error = (mae / current_range_palmsens) * 100 if current_range_palmsens > 0 else 0
            
            calibration_result = {
                'calibration_type': 'keysight_calibrated',
                'calibration_timestamp': datetime.now().isoformat(),
                'sample_id': stm32_dataset.sample_id,
                'measurement_mode': stm32_dataset.measurement_mode,
                
                # Calibration parameters
                'current_slope': float(slope),
                'current_offset': float(offset),
                'voltage_slope': 1.0,  # Assuming voltage is already calibrated by KEYSIGHT
                'voltage_offset': 0.0,
                
                # Calibrated data
                'calibrated_cv_data': calibrated_cv_data,
                
                # Statistics
                'mse': float(mse),
                'mae': float(mae),
                'r_squared': float(r_squared),
                'current_range_error_percent': float(current_range_error),
                'data_points_compared': len(common_voltages),
                
                # Original data info
                'stm32_data_points': len(stm32_dataset.cv_data),
                'palmsens_data_points': len(palmsens_reference.cv_data),
                'common_voltage_range': [float(min(common_voltages)), float(max(common_voltages))],
                
                # Quality metrics
                'calibration_quality': 'excellent' if r_squared > 0.95 else 'good' if r_squared > 0.8 else 'fair',
                'recommended_for_use': r_squared > 0.7 and current_range_error < 15
            }
            
            # Store calibration model for future use
            model_key = f"{stm32_dataset.measurement_mode}_{stm32_dataset.sample_id}"
            self.calibration_models[model_key] = {
                'current_slope': slope,
                'current_offset': offset,
                'voltage_slope': 1.0,
                'voltage_offset': 0.0,
                'timestamp': datetime.now(),
                'r_squared': r_squared
            }
            
            logger.info(f"Calibration completed: R²={r_squared:.3f}, MAE={mae:.2e}, Error={current_range_error:.1f}%")
            return calibration_result
            
        except Exception as e:
            logger.error(f"Error in calibration: {e}")
            raise
    
    def apply_calibration(self, stm32_data: List[Dict[str, float]], 
                         calibration_params: Dict[str, float]) -> List[Dict[str, float]]:
        """
        Apply calibration parameters to STM32 data
        
        Args:
            stm32_data: Raw STM32 CV data
            calibration_params: Calibration parameters
            
        Returns:
            Calibrated CV data
        """
        calibrated_data = []
        
        current_slope = calibration_params.get('current_slope', 1.0)
        current_offset = calibration_params.get('current_offset', 0.0)
        voltage_slope = calibration_params.get('voltage_slope', 1.0)
        voltage_offset = calibration_params.get('voltage_offset', 0.0)
        
        for point in stm32_data:
            calibrated_voltage = voltage_slope * point['voltage'] + voltage_offset
            calibrated_current = current_slope * point['current'] + current_offset
            
            calibrated_data.append({
                'voltage': calibrated_voltage,
                'current': calibrated_current
            })
        
        return calibrated_data
    
    def get_calibration_model(self, measurement_mode: str, sample_id: str) -> Optional[Dict[str, Any]]:
        """Get stored calibration model"""
        model_key = f"{measurement_mode}_{sample_id}"
        return self.calibration_models.get(model_key)
    
    def save_calibration_models(self, filepath: str):
        """Save calibration models to file"""
        try:
            # Convert datetime objects to strings for JSON serialization
            models_for_json = {}
            for key, model in self.calibration_models.items():
                model_copy = model.copy()
                if 'timestamp' in model_copy:
                    model_copy['timestamp'] = model_copy['timestamp'].isoformat()
                models_for_json[key] = model_copy
            
            with open(filepath, 'w') as f:
                json.dump(models_for_json, f, indent=2)
                
            logger.info(f"Saved {len(self.calibration_models)} calibration models to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving calibration models: {e}")
    
    def load_calibration_models(self, filepath: str):
        """Load calibration models from file"""
        try:
            with open(filepath, 'r') as f:
                models_from_json = json.load(f)
            
            # Convert timestamp strings back to datetime objects
            for key, model in models_from_json.items():
                if 'timestamp' in model:
                    model['timestamp'] = datetime.fromisoformat(model['timestamp'])
                self.calibration_models[key] = model
                
            logger.info(f"Loaded {len(self.calibration_models)} calibration models from {filepath}")
            
        except FileNotFoundError:
            logger.info(f"No calibration models file found at {filepath}")
        except Exception as e:
            logger.error(f"Error loading calibration models: {e}")

# Global instance
cross_instrument_calibrator = CrossInstrumentCalibrator()

# Load existing models on startup
models_file = Path("data_logs/calibration_models.json")
if models_file.exists():
    cross_instrument_calibrator.load_calibration_models(str(models_file))