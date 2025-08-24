"""
Hybrid Data Manager - Support both database and file-based CV data

This module provides seamless access to CV data from multiple sources:
1. Database (SQLite) - for current session
2. File mapping (JSON) - for portable data
3. Direct file access - for legacy data
"""

import json
import os
import pandas as pd
from typing import List, Dict, Any, Optional
from src.services.parameter_logging import ParameterLogger
import logging

logger = logging.getLogger(__name__)

class HybridDataManager:
    def __init__(self):
        self.db_logger = ParameterLogger()
        self.mapping_file = "cv_data_mapping.json"
        self.data_directory = "cv_data"
        
    def get_cv_data(self, measurement_id: int) -> List[Dict[str, float]]:
        """
        Get CV data from multiple sources with priority:
        1. Database
        2. File mapping
        3. Sample files fallback
        """
        
        # Try database first
        cv_data = self.db_logger.get_measurement_cv_data(measurement_id)
        if cv_data:
            logger.info(f"✅ Found {len(cv_data)} CV data points in database for measurement {measurement_id}")
            return cv_data
        
        # Try file mapping
        cv_data = self._get_cv_data_from_mapping(measurement_id)
        if cv_data:
            logger.info(f"✅ Found {len(cv_data)} CV data points in file mapping for measurement {measurement_id}")
            return cv_data
        
        # Try sample files fallback
        cv_data = self._get_cv_data_from_samples(measurement_id)
        if cv_data:
            logger.info(f"⚠️  Using sample data fallback for measurement {measurement_id}")
            return cv_data
        
        logger.warning(f"❌ No CV data found for measurement {measurement_id}")
        return []
    
    def get_measurement_data(self, measurement_id: int) -> List[Dict[str, float]]:
        """
        Alias for get_cv_data() - for compatibility with calibration system
        """
        return self.get_cv_data(measurement_id)
    
    def _get_cv_data_from_mapping(self, measurement_id: int) -> List[Dict[str, float]]:
        """Load CV data using file mapping"""
        try:
            if not os.path.exists(self.mapping_file):
                return []
            
            with open(self.mapping_file, 'r') as f:
                mapping = json.load(f)
            
            measurement_info = mapping.get('measurements', {}).get(str(measurement_id))
            if not measurement_info:
                return []
            
            file_path = measurement_info.get('file_path')
            if not file_path or not os.path.exists(file_path):
                return []
            
            # Load CSV file
            return self._load_csv_file(file_path)
            
        except Exception as e:
            logger.error(f"Error loading CV data from mapping for measurement {measurement_id}: {e}")
            return []
    
    def _get_cv_data_from_samples(self, measurement_id: int) -> List[Dict[str, float]]:
        """Fallback to sample files"""
        try:
            # Get measurement info for scan rate matching
            measurements = self.db_logger.get_measurements()
            measurement = next((m for m in measurements if m['id'] == measurement_id), None)
            
            if not measurement:
                return []
            
            scan_rate = measurement.get('scan_rate')
            
            # Map scan rates to sample files
            sample_files = {
                20: 'sample_data/Palmsens_0.5mM_CV_20mVpS_E3_scan_08.csv',
                100: 'sample_data/Palmsens_0.5mM_CV_100mVpS_E1_scan_05.csv',
                200: 'sample_data/Palmsens_0.5mM_CV_200mVpS_E2_scan_06.csv',
                400: 'sample_data/Pipot_Ferro_0_5mM_50mVpS_E4_scan_05.csv'
            }
            
            file_path = sample_files.get(scan_rate, 'sample_data/cv_sample.csv')
            
            if os.path.exists(file_path):
                return self._load_csv_file(file_path)
            
            return []
            
        except Exception as e:
            logger.error(f"Error loading sample data for measurement {measurement_id}: {e}")
            return []
    
    def _load_csv_file(self, file_path: str) -> List[Dict[str, float]]:
        """Load CV data from CSV file"""
        try:
            # First try with header
            df = pd.read_csv(file_path)
            
            # Check if first row is a filename (legacy format)
            if len(df.columns) == 1 and len(df) > 1:
                # Skip first row and reload
                df = pd.read_csv(file_path, skiprows=1)
            
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
                logger.warning(f"Could not find voltage/current columns in {file_path}, columns: {list(df.columns)}")
                logger.info(f"Trying with first 2 columns as voltage/current...")
                
                # Fallback: use first two columns
                if len(df.columns) >= 2:
                    voltage_col = df.columns[0]
                    current_col = df.columns[1]
                else:
                    logger.error(f"Insufficient columns in {file_path}")
                    return []
            
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
            
            logger.info(f"✅ Loaded {len(cv_data)} CV data points from {file_path}")
            return cv_data
            
        except Exception as e:
            logger.error(f"Error loading CSV file {file_path}: {e}")
            return []
    
    def save_cv_data_to_files(self, measurement_id: int, cv_data: List[Dict[str, float]], 
                              filename: Optional[str] = None) -> bool:
        """Save CV data to file system with mapping"""
        try:
            # Ensure data directory exists
            os.makedirs(self.data_directory, exist_ok=True)
            
            # Handle different CV data formats
            if not cv_data:
                logger.warning(f"No CV data to save for measurement {measurement_id}")
                return False
            
            # Convert list of lists to list of dicts if needed
            processed_data = []
            if isinstance(cv_data[0], (list, tuple)):
                # Convert [[v1, i1], [v2, i2]] to [{'voltage': v1, 'current': i1}, ...]
                for point in cv_data:
                    if len(point) >= 2:
                        processed_data.append({'voltage': float(point[0]), 'current': float(point[1])})
            else:
                # Assume it's already in dict format
                processed_data = cv_data
            
            # Generate filename if not provided
            if not filename:
                measurement = next((m for m in self.db_logger.get_measurements() 
                                 if m['id'] == measurement_id), None)
                if measurement:
                    scan_rate = measurement.get('scan_rate', 'unknown')
                    timestamp = measurement.get('timestamp', '').replace(':', '-').replace(' ', 'T')
                    filename = f"measurement_{measurement_id}_{scan_rate}mVs_{timestamp}.csv"
                else:
                    filename = f"measurement_{measurement_id}.csv"
            
            file_path = os.path.join(self.data_directory, filename)
            
            # Write CSV file
            with open(file_path, 'w') as f:
                f.write("Voltage(V),Current(uA)\n")
                for point in processed_data:
                    voltage = point.get('voltage', 0)
                    current = point.get('current', 0)
                    f.write(f"{voltage},{current}\n")
            
            # Update mapping file
            self._update_mapping_file(measurement_id, filename, file_path, len(processed_data))
            
            logger.info(f"✅ Saved {len(processed_data)} CV data points for measurement {measurement_id} to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving CV data to files for measurement {measurement_id}: {e}")
            return False
    
    def get_cv_data_info(self, measurement_id: int) -> Dict[str, Any]:
        """Get information about CV data availability and sources"""
        info = {
            'measurement_id': measurement_id,
            'database_available': False,
            'file_available': False,
            'mapping_entry': None,
            'data_points': 0,
            'source_used': None,
            'file_path': None
        }
        
        try:
            # Check database
            db_data = self.db_logger.get_measurement_cv_data(measurement_id)
            if db_data and len(db_data) > 0:
                info['database_available'] = True
                info['data_points'] = len(db_data)
                info['source_used'] = 'database'
            
            # Check mapping/files
            if os.path.exists(self.mapping_file):
                with open(self.mapping_file, 'r') as f:
                    mapping = json.load(f)
                
                measurement_info = mapping.get('measurements', {}).get(str(measurement_id))
                if measurement_info:
                    info['mapping_entry'] = measurement_info
                    file_path = measurement_info.get('file_path')
                    
                    if file_path and os.path.exists(file_path):
                        info['file_available'] = True
                        info['file_path'] = file_path
                        
                        if not info['database_available']:
                            # Count file data points
                            try:
                                file_data = self._load_csv_file(file_path)
                                info['data_points'] = len(file_data)
                                info['source_used'] = 'file'
                            except:
                                pass
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting CV data info for measurement {measurement_id}: {e}")
            return info
    
    def _update_mapping_file(self, measurement_id: int, filename: str, file_path: str, data_points: int = 0):
        """Update the mapping file"""
        try:
            # Load existing mapping
            mapping = {"measurements": {}, "metadata": {}}
            if os.path.exists(self.mapping_file):
                with open(self.mapping_file, 'r') as f:
                    mapping = json.load(f)
            
            # Get measurement details
            measurement = next((m for m in self.db_logger.get_measurements() 
                             if m['id'] == measurement_id), None)
            
            # Update mapping
            mapping["measurements"][str(measurement_id)] = {
                "filename": filename,
                "file_path": file_path,
                "data_points": data_points,
                "scan_rate": measurement.get('scan_rate') if measurement else None,
                "timestamp": measurement.get('timestamp') if measurement else None,
                "original_filename": measurement.get('original_filename') if measurement else None,
                "exported_at": pd.Timestamp.now().isoformat(),
                "source": "auto_export"
            }
            
            mapping["metadata"] = {
                "version": "1.0",
                "description": "Hybrid CV data mapping system",
                "last_updated": pd.Timestamp.now().isoformat(),
                "total_measurements": len(mapping["measurements"])
            }
            
            # Save mapping
            with open(self.mapping_file, 'w') as f:
                json.dump(mapping, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating mapping file: {e}")
    
    def delete_measurement_data(self, measurement_id: int) -> bool:
        """Delete measurement data files and remove from mapping"""
        try:
            measurement_id_str = str(measurement_id)
            
            # Load current mapping
            mapping = self._load_mapping()
            
            # Check if measurement exists in mapping
            if measurement_id_str not in mapping:
                logger.info(f"Measurement {measurement_id} not found in mapping (no file to delete)")
                return True
            
            # Get file path and delete file
            file_path = mapping[measurement_id_str]['file_path']
            full_path = os.path.join(self.data_directory, file_path)
            
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.info(f"Deleted CV data file: {full_path}")
            else:
                logger.warning(f"CV data file not found: {full_path}")
            
            # Remove from mapping
            del mapping[measurement_id_str]
            
            # Save updated mapping
            with open(self.mapping_file, 'w') as f:
                json.dump(mapping, f, indent=2)
            
            logger.info(f"Removed measurement {measurement_id} from mapping")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting measurement data for {measurement_id}: {e}")
            return False

# Global instance
hybrid_manager = HybridDataManager()