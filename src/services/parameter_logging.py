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
        self.conn = None
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Create directory for database if it doesn't exist"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def _init_database(self):
        """Initialize database tables"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
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
    
    def get_connection(self):
        """Get database connection, creating new one if needed"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
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
                    # Ensure required fields have values
                    peak_voltage = peak.get('voltage') or peak.get('x') or 0.0
                    peak_current = peak.get('current') or peak.get('y') or 0.0
                    peak_type = peak.get('type', 'unknown')
                    peak_height = peak.get('height')
                    baseline_current = peak.get('baseline_current')
                    
                    # Calculate height if not provided using correct CV peak height calculation
                    if peak_height is None and baseline_current is not None:
                        if peak_type == 'reduction':
                            # For reduction peaks, use absolute value (negative peaks below baseline)
                            peak_height = abs(peak_current - baseline_current)
                        else:
                            # For oxidation peaks, use direct difference (positive peaks above baseline)
                            peak_height = peak_current - baseline_current
                    elif peak_height is None:
                        # Fallback: if no baseline info, estimate height as absolute current
                        peak_height = abs(peak_current) if peak_current else 0.0
                    
                    # Ensure peak_height is not None and is positive
                    if peak_height is None or peak_height < 0:
                        peak_height = abs(peak_current) if peak_current else 0.0
                    
                    logger.debug(f"Peak {i}: type={peak_type}, voltage={peak_voltage:.3f}V, current={peak_current:.3f}μA, baseline={baseline_current}μA, height={peak_height:.3f}μA")
                    
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
                        measurement_id, i, peak_type,
                        peak.get('enabled', True),
                        peak_voltage,
                        peak_current,
                        peak_height,
                        peak.get('area'),
                        peak.get('width_half_max'),
                        peak.get('prominence'),
                        baseline_current,
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
    
    def get_measurement_cv_data(self, measurement_id: int) -> List[Dict[str, Any]]:
        """Get CV data for a measurement from raw_data_json"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT raw_data_json FROM measurements 
                WHERE id = ?
            """, (measurement_id,))
            
            row = cursor.fetchone()
            if not row or not row['raw_data_json']:
                return []
            
            try:
                raw_data = json.loads(row['raw_data_json'])
                
                # Extract CV data from raw data
                # Check for new structure first (from update_measurement_cv_data)
                if isinstance(raw_data, dict) and 'cv_data' in raw_data:
                    cv_data = raw_data['cv_data']
                    if isinstance(cv_data, list) and len(cv_data) > 0:
                        logger.info(f"✅ Found {len(cv_data)} CV data points in database for measurement {measurement_id}")
                        return cv_data
                
                # Legacy structure support
                if isinstance(raw_data, dict):
                    voltage_data = raw_data.get('voltage', [])
                    current_data = raw_data.get('current', [])
                    
                    if len(voltage_data) == len(current_data) and len(voltage_data) > 0:
                        return [{'voltage': v, 'current': c} for v, c in zip(voltage_data, current_data)]
                    
                    # Alternative legacy structure
                    data_points = raw_data.get('data_points', [])
                    if data_points and isinstance(data_points, list):
                        cv_data = []
                        for point in data_points:
                            if isinstance(point, dict) and 'voltage' in point and 'current' in point:
                                cv_data.append({
                                    'voltage': point['voltage'],
                                    'current': point['current']
                                })
                        return cv_data
                
                return []
                
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.error(f"Error parsing CV data for measurement {measurement_id}: {e}")
                return []
    
    def update_measurement_cv_data(self, measurement_id: int, cv_data: List[Dict[str, float]]) -> bool:
        """
        Update measurement with raw CV data
        
        Args:
            measurement_id: ID of the measurement to update
            cv_data: List of dictionaries with 'voltage' and 'current' keys
            
        Returns:
            bool: Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Store CV data as JSON
                raw_data_json = json.dumps({
                    'cv_data': cv_data,
                    'data_points': len(cv_data),
                    'updated_timestamp': datetime.now().isoformat()
                })
                
                cursor.execute("""
                    UPDATE measurements 
                    SET raw_data_json = ?, data_points = ?
                    WHERE id = ?
                """, (raw_data_json, len(cv_data), measurement_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"✅ Updated measurement {measurement_id} with {len(cv_data)} CV data points")
                    return True
                else:
                    logger.warning(f"❌ No measurement found with ID {measurement_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating CV data for measurement {measurement_id}: {e}")
            return False
    
    def import_cv_data_from_file(self, measurement_id: int, file_path: str) -> bool:
        """
        Import CV data from a CSV file and store in database
        
        Args:
            measurement_id: ID of the measurement to update
            file_path: Path to the CSV file containing CV data
            
        Returns:
            bool: Success status
        """
        try:
            import pandas as pd
            
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return False
            
            # Read CSV file
            df = pd.read_csv(file_path, skiprows=1)  # Skip filename header
            
            # Try different column name variations
            voltage_col = None
            current_col = None
            
            for col in df.columns:
                col_lower = col.lower().strip()
                if col_lower in ['v', 'voltage', 'voltage(v)']:
                    voltage_col = col
                elif col_lower in ['ua', 'µa', 'current', 'current(ua)', 'i', 'a', 'current(a)']:
                    current_col = col
            
            if not voltage_col or not current_col:
                logger.error(f"Could not find voltage/current columns in {file_path}")
                logger.error(f"Available columns: {list(df.columns)}")
                return False
            
            # Extract CV data
            cv_data = []
            for _, row in df.iterrows():
                try:
                    voltage = float(row[voltage_col])
                    current = float(row[current_col])
                    
                    # Convert units if necessary
                    current_col_lower = current_col.lower().strip()
                    if current_col_lower in ['a', 'current(a)']:
                        # Convert Amps to microAmps
                        current = current * 1_000_000
                    
                    cv_data.append({'voltage': voltage, 'current': current})
                except (ValueError, TypeError):
                    continue
            
            if not cv_data:
                logger.error(f"No valid CV data found in {file_path}")
                return False
            
            # Update measurement with CV data
            success = self.update_measurement_cv_data(measurement_id, cv_data)
            
            if success:
                logger.info(f"✅ Successfully imported {len(cv_data)} CV data points from {file_path}")
                
                # Also update filename if it's empty
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE measurements 
                        SET original_filename = ?
                        WHERE id = ? AND (original_filename IS NULL OR original_filename = '')
                    """, (os.path.basename(file_path), measurement_id))
                    conn.commit()
            
            return success
            
        except Exception as e:
            logger.error(f"Error importing CV data from {file_path}: {e}")
            return False
    
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
    
    def get_measurement_by_id(self, measurement_id: int) -> Optional[Dict[str, Any]]:
        """Get a single measurement by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM measurements WHERE id = ?
        """, (measurement_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def delete_measurement(self, measurement_id: int) -> bool:
        """Delete a measurement and all associated data"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # First delete associated peak parameters (foreign key constraint)
            cursor.execute("DELETE FROM peak_parameters WHERE measurement_id = ?", (measurement_id,))
            deleted_peaks = cursor.rowcount
            
            # Delete the measurement itself
            cursor.execute("DELETE FROM measurements WHERE id = ?", (measurement_id,))
            deleted_measurement = cursor.rowcount
            
            if deleted_measurement > 0:
                conn.commit()
                logger.info(f"Deleted measurement {measurement_id}: "
                           f"{deleted_peaks} peak parameters, "
                           f"1 measurement record")
                return True
            else:
                logger.warning(f"No measurement found with ID {measurement_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting measurement {measurement_id}: {e}")
            conn.rollback()
            return False

# Global instance
parameter_logger = ParameterLogger()