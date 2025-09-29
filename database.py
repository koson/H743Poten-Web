"""
Database models for H743 Potentiostat measurements
Handles CV, SWV, DPV measurement storage and retrieval
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MeasurementDatabase:
    def __init__(self, db_path: str = "measurements.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Measurements table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS measurements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        measurement_type TEXT NOT NULL,
                        parameters TEXT NOT NULL,
                        status TEXT DEFAULT 'PENDING',
                        data_points INTEGER DEFAULT 0,
                        duration_seconds REAL DEFAULT 0,
                        notes TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Data points table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_points (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        measurement_id INTEGER,
                        point_index INTEGER,
                        voltage REAL,
                        current REAL,
                        timestamp_offset REAL DEFAULT 0,
                        FOREIGN KEY (measurement_id) REFERENCES measurements (id)
                    )
                ''')
                
                # Files table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exported_files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        measurement_id INTEGER,
                        file_type TEXT NOT NULL,
                        file_name TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_size INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (measurement_id) REFERENCES measurements (id)
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_measurements_type ON measurements(measurement_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_measurements_timestamp ON measurements(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_points_measurement ON data_points(measurement_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_measurement ON exported_files(measurement_id)')
                
                conn.commit()
                logger.info("✅ Database initialized successfully")
                
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def create_measurement(self, measurement_type: str, parameters: Dict[str, Any], notes: str = "") -> int:
        """Create new measurement record"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO measurements (measurement_type, parameters, notes)
                    VALUES (?, ?, ?)
                ''', (measurement_type, json.dumps(parameters), notes))
                
                measurement_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"✅ Created measurement {measurement_id} ({measurement_type})")
                return measurement_id
                
        except Exception as e:
            logger.error(f"❌ Failed to create measurement: {e}")
            raise
    
    def update_measurement_status(self, measurement_id: int, status: str, data_points: int = 0, duration: float = 0):
        """Update measurement status and statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE measurements 
                    SET status = ?, data_points = ?, duration_seconds = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, data_points, duration, measurement_id))
                
                conn.commit()
                logger.info(f"✅ Updated measurement {measurement_id}: {status} ({data_points} points)")
                
        except Exception as e:
            logger.error(f"❌ Failed to update measurement {measurement_id}: {e}")
            raise
    
    def store_data_points(self, measurement_id: int, data_points: List[Dict[str, float]]):
        """Store measurement data points"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clear existing data points
                cursor.execute('DELETE FROM data_points WHERE measurement_id = ?', (measurement_id,))
                
                # Insert new data points
                for i, point in enumerate(data_points):
                    cursor.execute('''
                        INSERT INTO data_points (measurement_id, point_index, voltage, current, timestamp_offset)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        measurement_id, 
                        i, 
                        point.get('voltage', 0), 
                        point.get('current', 0),
                        point.get('time', i * 0.1)  # Default 0.1s per point
                    ))
                
                conn.commit()
                logger.info(f"✅ Stored {len(data_points)} data points for measurement {measurement_id}")
                
        except Exception as e:
            logger.error(f"❌ Failed to store data points for measurement {measurement_id}: {e}")
            raise
    
    def get_measurement(self, measurement_id: int) -> Optional[Dict[str, Any]]:
        """Get measurement by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM measurements WHERE id = ?
                ''', (measurement_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                measurement = dict(row)
                measurement['parameters'] = json.loads(measurement['parameters'])
                
                return measurement
                
        except Exception as e:
            logger.error(f"❌ Failed to get measurement {measurement_id}: {e}")
            return None
    
    def get_measurement_data(self, measurement_id: int) -> List[Dict[str, float]]:
        """Get data points for measurement"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT voltage, current, timestamp_offset
                    FROM data_points 
                    WHERE measurement_id = ?
                    ORDER BY point_index
                ''', (measurement_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"❌ Failed to get data for measurement {measurement_id}: {e}")
            return []
    
    def list_measurements(self, measurement_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List recent measurements"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if measurement_type:
                    cursor.execute('''
                        SELECT id, timestamp, measurement_type, status, data_points, duration_seconds, notes
                        FROM measurements 
                        WHERE measurement_type = ?
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    ''', (measurement_type, limit))
                else:
                    cursor.execute('''
                        SELECT id, timestamp, measurement_type, status, data_points, duration_seconds, notes
                        FROM measurements 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    ''', (limit,))
                
                measurements = []
                for row in cursor.fetchall():
                    measurement = dict(row)
                    measurements.append(measurement)
                
                return measurements
                
        except Exception as e:
            logger.error(f"❌ Failed to list measurements: {e}")
            return []
    
    def register_exported_file(self, measurement_id: int, file_type: str, file_name: str, file_path: str) -> int:
        """Register exported file in database"""
        try:
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO exported_files (measurement_id, file_type, file_name, file_path, file_size)
                    VALUES (?, ?, ?, ?, ?)
                ''', (measurement_id, file_type, file_name, file_path, file_size))
                
                file_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"✅ Registered exported file {file_id}: {file_name}")
                return file_id
                
        except Exception as e:
            logger.error(f"❌ Failed to register exported file: {e}")
            raise
    
    def get_exported_files(self, measurement_id: int) -> List[Dict[str, Any]]:
        """Get exported files for measurement"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM exported_files 
                    WHERE measurement_id = ?
                    ORDER BY created_at DESC
                ''', (measurement_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"❌ Failed to get exported files for measurement {measurement_id}: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count measurements by type
                cursor.execute('''
                    SELECT measurement_type, COUNT(*) as count
                    FROM measurements 
                    GROUP BY measurement_type
                ''')
                measurements_by_type = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Total data points
                cursor.execute('SELECT COUNT(*) FROM data_points')
                total_data_points = cursor.fetchone()[0]
                
                # Total exported files
                cursor.execute('SELECT COUNT(*) FROM exported_files')
                total_files = cursor.fetchone()[0]
                
                # Database file size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                return {
                    "measurements_by_type": measurements_by_type,
                    "total_data_points": total_data_points,
                    "total_exported_files": total_files,
                    "database_size_bytes": db_size
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get database stats: {e}")
            return {}

# Global database instance
db = MeasurementDatabase()