"""
CSV Data Emulator for simulating real measurement data from CSV files
This module allows simulation of measurement timing and data from pre-recorded CSV files
"""

import csv
import time
import threading
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys
import os

# Add the parent directory to the Python path to handle imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from ..config.settings import Config
except ImportError:
    from config.settings import Config

logger = logging.getLogger(__name__)

class CSVDataEmulator:
    """
    Emulates measurement data playback from CSV files with real timing simulation
    """
    
    def __init__(self):
        self.csv_data: List[Dict] = []
        self.current_index = 0
        self.is_playing = False
        self.start_time = None
        self.emulation_thread = None
        self.data_lock = threading.Lock()
        self.csv_file_path = None
        self.playback_speed = 1.0  # 1.0 = real time, 2.0 = 2x speed, etc.
        self.loop_playback = False
        
        # Data format settings
        self.expected_columns = {
            'time': ['time', 'timestamp', 't'],
            'voltage': ['voltage', 'v', 'potential'],
            'current': ['current', 'i', 'current_a', 'current_ma']
        }
        
    def load_csv_file(self, file_path: str) -> bool:
        """
        Load CV data from CSV file
        
        Args:
            file_path: Path to CSV file containing measurement data
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            self.csv_file_path = Path(file_path)
            if not self.csv_file_path.exists():
                logger.error(f"CSV file not found: {file_path}")
                return False
                
            self.csv_data = []
            
            with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                # Detect CSV dialect
                sample = file.read(1024)
                file.seek(0)
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                
                reader = csv.DictReader(file, dialect=dialect)
                
                # Detect column mapping
                column_mapping = self._detect_columns(reader.fieldnames)
                if not column_mapping:
                    logger.error("Could not detect required columns in CSV file")
                    return False
                
                logger.info(f"Detected columns: {column_mapping}")
                
                # Load data
                for row_num, row in enumerate(reader, start=2):
                    try:
                        data_point = self._parse_row(row, column_mapping)
                        if data_point:
                            self.csv_data.append(data_point)
                    except Exception as e:
                        logger.warning(f"Error parsing row {row_num}: {e}")
                        continue
                
            if not self.csv_data:
                logger.error("No valid data points found in CSV file")
                return False
                
            # Sort by timestamp to ensure proper ordering
            self.csv_data.sort(key=lambda x: x['timestamp'])
            
            # Calculate relative timestamps if needed
            if self.csv_data:
                start_time = self.csv_data[0]['timestamp']
                for point in self.csv_data:
                    point['relative_time'] = point['timestamp'] - start_time
            
            logger.info(f"Loaded {len(self.csv_data)} data points from {file_path}")
            logger.info(f"Time range: {self.csv_data[0]['timestamp']:.3f} to {self.csv_data[-1]['timestamp']:.3f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading CSV file {file_path}: {e}")
            return False
    
    def _detect_columns(self, fieldnames: List[str]) -> Optional[Dict[str, str]]:
        """
        Detect which columns contain time, voltage, and current data
        """
        if not fieldnames:
            return None
            
        mapping = {}
        fieldnames_lower = [name.lower().strip() for name in fieldnames]
        
        # Find time column
        for time_variant in self.expected_columns['time']:
            for i, field in enumerate(fieldnames_lower):
                if time_variant in field:
                    mapping['time'] = fieldnames[i]
                    break
            if 'time' in mapping:
                break
                
        # Find voltage column
        for voltage_variant in self.expected_columns['voltage']:
            for i, field in enumerate(fieldnames_lower):
                if voltage_variant in field:
                    mapping['voltage'] = fieldnames[i]
                    break
            if 'voltage' in mapping:
                break
                
        # Find current column
        for current_variant in self.expected_columns['current']:
            for i, field in enumerate(fieldnames_lower):
                if current_variant in field:
                    mapping['current'] = fieldnames[i]
                    break
            if 'current' in mapping:
                break
        
        # Check if we have at least time and one measurement
        if 'time' not in mapping:
            logger.error("Could not find time column")
            return None
            
        if 'voltage' not in mapping and 'current' not in mapping:
            logger.error("Could not find voltage or current column")
            return None
            
        return mapping
    
    def _parse_row(self, row: Dict[str, str], column_mapping: Dict[str, str]) -> Optional[Dict]:
        """
        Parse a single CSV row into a data point
        """
        try:
            data_point = {}
            
            # Parse timestamp
            time_str = row[column_mapping['time']].strip()
            data_point['timestamp'] = float(time_str)
            
            # Parse voltage
            if 'voltage' in column_mapping:
                voltage_str = row[column_mapping['voltage']].strip()
                data_point['voltage'] = float(voltage_str)
            else:
                data_point['voltage'] = 0.0
                
            # Parse current
            if 'current' in column_mapping:
                current_str = row[column_mapping['current']].strip()
                data_point['current'] = float(current_str)
            else:
                data_point['current'] = 0.0
                
            return data_point
            
        except (ValueError, KeyError) as e:
            logger.warning(f"Error parsing row: {e}")
            return None
    
    def start_emulation(self, playback_speed: float = 1.0, loop: bool = False) -> bool:
        """
        Start emulating measurement data playback
        
        Args:
            playback_speed: Speed multiplier (1.0 = real time, 2.0 = 2x speed)
            loop: Whether to loop the data when it reaches the end
            
        Returns:
            bool: True if started successfully
        """
        try:
            if not self.csv_data:
                logger.error("No CSV data loaded")
                return False
                
            if self.is_playing:
                logger.warning("Emulation already running")
                return False
                
            self.playback_speed = playback_speed
            self.loop_playback = loop
            self.current_index = 0
            self.start_time = time.time()
            self.is_playing = True
            
            # Start emulation thread
            self.emulation_thread = threading.Thread(target=self._emulation_worker, daemon=True)
            self.emulation_thread.start()
            
            logger.info(f"Started CSV emulation with {len(self.csv_data)} points at {playback_speed}x speed")
            return True
            
        except Exception as e:
            logger.error(f"Error starting emulation: {e}")
            return False
    
    def stop_emulation(self):
        """Stop the emulation"""
        self.is_playing = False
        if self.emulation_thread and self.emulation_thread.is_alive():
            self.emulation_thread.join(timeout=1.0)
        logger.info("Stopped CSV emulation")
    
    def _emulation_worker(self):
        """
        Worker thread that manages timing and data playback
        """
        try:
            while self.is_playing and self.current_index < len(self.csv_data):
                current_point = self.csv_data[self.current_index]
                
                # Calculate when this point should be available
                target_time = current_point['relative_time'] / self.playback_speed
                elapsed_time = time.time() - self.start_time
                
                # Wait if we're ahead of schedule
                if elapsed_time < target_time:
                    sleep_time = target_time - elapsed_time
                    time.sleep(min(sleep_time, 0.1))  # Cap sleep time
                
                # Advance to next point
                with self.data_lock:
                    self.current_index += 1
                
                # Check for loop
                if self.current_index >= len(self.csv_data) and self.loop_playback:
                    self.current_index = 0
                    self.start_time = time.time()
                    logger.info("Looping CSV data playback")
                    
        except Exception as e:
            logger.error(f"Error in emulation worker: {e}")
        finally:
            if not self.loop_playback:
                self.is_playing = False
    
    def get_current_data(self) -> List[Dict]:
        """
        Get all data points that should be available at the current time
        """
        with self.data_lock:
            if not self.is_playing or not self.csv_data:
                return []
                
            # Return all points up to current index
            current_data = []
            for i in range(min(self.current_index, len(self.csv_data))):
                point = self.csv_data[i].copy()
                # Add mode information
                point['mode'] = 'CSV_EMULATION'
                current_data.append(point)
                
            return current_data
    
    def get_latest_point(self) -> Optional[Dict]:
        """
        Get the most recent data point
        """
        with self.data_lock:
            if not self.is_playing or not self.csv_data or self.current_index == 0:
                return None
                
            point = self.csv_data[self.current_index - 1].copy()
            point['mode'] = 'CSV_EMULATION'
            return point
    
    def get_progress(self) -> Dict:
        """
        Get current playback progress
        """
        with self.data_lock:
            if not self.csv_data:
                return {
                    'current_index': 0,
                    'total_points': 0,
                    'progress_percent': 0.0,
                    'elapsed_time': 0.0,
                    'total_time': 0.0
                }
                
            total_time = self.csv_data[-1]['relative_time'] if self.csv_data else 0
            elapsed = (time.time() - self.start_time) if self.start_time else 0
            
            return {
                'current_index': self.current_index,
                'total_points': len(self.csv_data),
                'progress_percent': (self.current_index / len(self.csv_data)) * 100,
                'elapsed_time': elapsed,
                'total_time': total_time / self.playback_speed,
                'is_playing': self.is_playing,
                'playback_speed': self.playback_speed,
                'csv_file': str(self.csv_file_path) if self.csv_file_path else None
            }
    
    def seek_to_time(self, target_time: float) -> bool:
        """
        Seek to a specific time in the data
        
        Args:
            target_time: Target relative time to seek to
            
        Returns:
            bool: True if seek was successful
        """
        try:
            with self.data_lock:
                if not self.csv_data:
                    return False
                    
                # Find the closest data point
                for i, point in enumerate(self.csv_data):
                    if point['relative_time'] >= target_time:
                        self.current_index = i
                        # Adjust start time to maintain timing
                        if self.is_playing:
                            self.start_time = time.time() - (target_time / self.playback_speed)
                        logger.info(f"Seeked to time {target_time:.3f}s (index {i})")
                        return True
                        
                # If target time is beyond data, go to end
                self.current_index = len(self.csv_data)
                return True
                
        except Exception as e:
            logger.error(f"Error seeking to time {target_time}: {e}")
            return False
    
    def get_data_info(self) -> Dict:
        """
        Get information about the loaded CSV data
        """
        if not self.csv_data:
            return {'loaded': False}
            
        voltages = [point['voltage'] for point in self.csv_data]
        currents = [point['current'] for point in self.csv_data]
        
        return {
            'loaded': True,
            'file_path': str(self.csv_file_path) if self.csv_file_path else None,
            'total_points': len(self.csv_data),
            'time_range': {
                'start': self.csv_data[0]['timestamp'],
                'end': self.csv_data[-1]['timestamp'],
                'duration': self.csv_data[-1]['relative_time']
            },
            'voltage_range': {
                'min': min(voltages),
                'max': max(voltages)
            },
            'current_range': {
                'min': min(currents),
                'max': max(currents)
            }
        }
