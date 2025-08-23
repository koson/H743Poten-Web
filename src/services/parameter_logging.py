"""
Parameter Logging Service for Transfer Calibration
Handles storage and retrieval of peak analysis parameters
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class ParameterLogger:
    def __init__(self, db_path: str = "data_logs/parameter_log.db"):
        """Initialize parameter logger with SQLite database"""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Create directory for database if it doesn't exist"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def _init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sample_id TEXT NOT NULL,
                    instrument_type TEXT NOT NULL,  -- 'palmsens' or 'stm32'
                    timestamp DATETIME NOT NULL,
                    analysis_timestamp DATETIME NOT NULL,
                    
                    -- Measurement conditions
                    scan_rate REAL,
                    voltage_start REAL,
                    voltage_end REAL,
                    step_potential REAL,
                    cycle_number INTEGER,
                    
                    -- File information
                    original_filename TEXT,
                    data_points INTEGER,
                    
                    -- User notes
                    user_notes TEXT,
                    
                    -- Raw data storage (for STM32)
                    raw_data_json TEXT,  -- Store full raw data if needed
                    
                    UNIQUE(sample_id, instrument_type, timestamp)
                );
                
                CREATE TABLE IF NOT EXISTS peak_parameters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    measurement_id INTEGER NOT NULL,
                    peak_index INTEGER NOT NULL,
                    peak_type TEXT NOT NULL,  -- 'oxidation' or 'reduction'
                    enabled BOOLEAN NOT NULL DEFAULT 1,
                    
                    -- Peak position and intensity
                    peak_voltage REAL NOT NULL,
                    peak_current REAL NOT NULL,
                    peak_height REAL NOT NULL,  -- Height from baseline
                    
                    -- Peak characteristics
                    peak_area REAL,
                    peak_width_half_max REAL,
                    peak_prominence REAL,
                    
                    -- Baseline information
                    baseline_current REAL,
                    baseline_slope REAL,
                    baseline_r2 REAL,
                    baseline_voltage_start REAL,
                    baseline_voltage_end REAL,
                    
                    -- STM32 specific (raw ADC values)
                    raw_dac_ch1 INTEGER,
                    raw_dac_ch2 INTEGER,
                    raw_timestamp_us INTEGER,
                    raw_counter INTEGER,
                    raw_lut_data INTEGER,
                    
                    FOREIGN KEY (measurement_id) REFERENCES measurements (id),
                    UNIQUE(measurement_id, peak_index)
                );
                
                CREATE TABLE IF NOT EXISTS calibration_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_name TEXT NOT NULL,
                    reference_measurement_id INTEGER NOT NULL,
                    target_measurement_id INTEGER NOT NULL,
                    created_timestamp DATETIME NOT NULL,
                    calibration_method TEXT NOT NULL,
                    calibration_parameters_json TEXT,
                    
                    -- Calibration results
                    rmse_voltage REAL,
                    rmse_current REAL,
                    r2_voltage REAL,
                    r2_current REAL,
                    
                    -- Status
                    status TEXT DEFAULT 'pending',  -- 'pending', 'completed', 'failed'
                    notes TEXT,
                    
                    FOREIGN KEY (reference_measurement_id) REFERENCES measurements (id),
                    FOREIGN KEY (target_measurement_id) REFERENCES measurements (id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_measurements_sample_instrument 
                ON measurements(sample_id, instrument_type);
                
                CREATE INDEX IF NOT EXISTS idx_peaks_measurement 
                ON peak_parameters(measurement_id);
                
                CREATE INDEX IF NOT EXISTS idx_calibration_reference 
                ON calibration_sessions(reference_measurement_id);
            """)
            logger.info("Database initialized successfully")
    
    def save_measurement(self, measurement_data: Dict[str, Any]) -> int:
        """
        Save measurement metadata and return measurement ID
        
        Args:
            measurement_data: Dictionary containing measurement information
            
        Returns:
            int: measurement_id for linking peak parameters
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO measurements (
                    sample_id, instrument_type, timestamp, analysis_timestamp,
                    scan_rate, voltage_start, voltage_end, step_potential, cycle_number,
                    original_filename, data_points, user_notes, raw_data_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                measurement_data.get('sample_id'),
                measurement_data.get('instrument_type'),
                measurement_data.get('timestamp'),
                datetime.now(),
                measurement_data.get('scan_rate'),
                measurement_data.get('voltage_start'),
                measurement_data.get('voltage_end'),
                measurement_data.get('step_potential'),
                measurement_data.get('cycle_number'),
                measurement_data.get('original_filename'),
                measurement_data.get('data_points'),
                measurement_data.get('user_notes'),
                json.dumps(measurement_data.get('raw_data', {}))
            ))
            
            measurement_id = cursor.lastrowid
            logger.info(f"Saved measurement {measurement_id} for sample {measurement_data.get('sample_id')}")
            return measurement_id
    
    def save_peak_parameters(self, measurement_id: int, peaks: List[Dict[str, Any]]) -> int:
        """
        Save peak parameters for a measurement
        
        Args:
            measurement_id: ID of the measurement
            peaks: List of peak parameter dictionaries
            
        Returns:
            int: Number of peaks saved
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Clear existing peaks for this measurement
            cursor.execute("DELETE FROM peak_parameters WHERE measurement_id = ?", (measurement_id,))
            
            saved_count = 0
            for i, peak in enumerate(peaks):
                if peak.get('enabled', True):  # Only save enabled peaks
                    cursor.execute("""
                        INSERT INTO peak_parameters (
                            measurement_id, peak_index, peak_type, enabled,
                            peak_voltage, peak_current, peak_height,
                            peak_area, peak_width_half_max, peak_prominence,
                            baseline_current, baseline_slope, baseline_r2,
                            baseline_voltage_start, baseline_voltage_end,
                            raw_dac_ch1, raw_dac_ch2, raw_timestamp_us, raw_counter, raw_lut_data
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        measurement_id, i, peak.get('type'),
                        peak.get('enabled', True),
                        peak.get('voltage') or peak.get('x'),
                        peak.get('current') or peak.get('y'),
                        peak.get('height'),
                        peak.get('area'),
                        peak.get('width_half_max'),
                        peak.get('prominence'),
                        peak.get('baseline_current'),
                        peak.get('baseline_slope'),
                        peak.get('baseline_r2'),
                        peak.get('baseline_voltage_start'),
                        peak.get('baseline_voltage_end'),
                        peak.get('raw_dac_ch1'),
                        peak.get('raw_dac_ch2'),
                        peak.get('raw_timestamp_us'),
                        peak.get('raw_counter'),
                        peak.get('raw_lut_data')
                    ))
                    saved_count += 1
            
            logger.info(f"Saved {saved_count} peak parameters for measurement {measurement_id}")
            return saved_count
    
    def get_measurements(self, sample_id: Optional[str] = None, 
                        instrument_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get measurements with optional filtering"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM measurements WHERE 1=1"
            params = []
            
            if sample_id:
                query += " AND sample_id = ?"
                params.append(sample_id)
                
            if instrument_type:
                query += " AND instrument_type = ?"
                params.append(instrument_type)
                
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_peak_parameters(self, measurement_id: int) -> List[Dict[str, Any]]:
        """Get peak parameters for a measurement"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM peak_parameters 
                WHERE measurement_id = ? 
                ORDER BY peak_index
            """, (measurement_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def create_calibration_session(self, session_data: Dict[str, Any]) -> int:
        """Create a new calibration session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO calibration_sessions (
                    session_name, reference_measurement_id, target_measurement_id,
                    created_timestamp, calibration_method, calibration_parameters_json,
                    notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_data.get('session_name'),
                session_data.get('reference_measurement_id'),
                session_data.get('target_measurement_id'),
                datetime.now(),
                session_data.get('calibration_method', 'linear'),
                json.dumps(session_data.get('calibration_parameters', {})),
                session_data.get('notes')
            ))
            
            session_id = cursor.lastrowid
            logger.info(f"Created calibration session {session_id}")
            return session_id
    
    def get_calibration_pairs(self, sample_id: str) -> List[Dict[str, Any]]:
        """Get available calibration pairs for a sample"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    ref.id as reference_id,
                    ref.instrument_type as reference_instrument,
                    ref.timestamp as reference_timestamp,
                    target.id as target_id,
                    target.instrument_type as target_instrument,
                    target.timestamp as target_timestamp
                FROM measurements ref
                JOIN measurements target ON ref.sample_id = target.sample_id
                WHERE ref.sample_id = ? 
                AND ref.instrument_type = 'palmsens'
                AND target.instrument_type = 'stm32'
                ORDER BY ref.timestamp DESC, target.timestamp DESC
            """, (sample_id,))
            
            return [dict(row) for row in cursor.fetchall()]

# Global instance
parameter_logger = ParameterLogger()