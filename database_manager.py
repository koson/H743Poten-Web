#!/usr/bin/env python3
"""
Database Backup/Restore Utility for H743Poten

Usage:
    python database_manager.py --export backup.json
    python database_manager.py --import backup.json
    python database_manager.py --migrate-to-files
"""

import argparse
import json
import os
import shutil
from datetime import datetime
from src.services.parameter_logging import ParameterLogger

def export_database(output_file: str):
    """Export database to JSON file with CV data"""
    logger = ParameterLogger()
    
    print(f"🔄 Exporting database to {output_file}...")
    
    # Get all measurements
    measurements = logger.get_measurements()
    
    export_data = {
        "exported_timestamp": datetime.now().isoformat(),
        "measurements": [],
        "cv_data": {},
        "peak_parameters": {}
    }
    
    for measurement in measurements:
        measurement_id = measurement['id']
        
        # Get CV data
        cv_data = logger.get_measurement_cv_data(measurement_id)
        if cv_data:
            export_data["cv_data"][str(measurement_id)] = cv_data
        
        # Get peak parameters
        peaks = logger.get_peak_parameters(measurement_id)
        if peaks:
            export_data["peak_parameters"][str(measurement_id)] = peaks
        
        # Add measurement metadata
        export_data["measurements"].append(measurement)
    
    # Write to file
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"✅ Exported {len(measurements)} measurements to {output_file}")
    print(f"   - CV data: {len(export_data['cv_data'])} measurements")
    print(f"   - Peak data: {len(export_data['peak_parameters'])} measurements")

def import_database(input_file: str):
    """Import database from JSON file"""
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return False
    
    logger = ParameterLogger()
    
    print(f"🔄 Importing database from {input_file}...")
    
    with open(input_file, 'r') as f:
        import_data = json.load(f)
    
    success_count = 0
    
    # Import measurements
    for measurement in import_data.get('measurements', []):
        try:
            # Save measurement metadata
            measurement_id = logger.save_measurement(measurement)
            
            # Import CV data if available
            cv_data = import_data.get('cv_data', {}).get(str(measurement['id']))
            if cv_data:
                logger.update_measurement_cv_data(measurement_id, cv_data)
            
            # Import peak parameters if available
            peaks = import_data.get('peak_parameters', {}).get(str(measurement['id']))
            if peaks:
                logger.save_peak_parameters(measurement_id, peaks)
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ Failed to import measurement {measurement.get('id', 'unknown')}: {e}")
    
    print(f"✅ Successfully imported {success_count} measurements")
    return True

def migrate_to_file_based():
    """Migrate current database to file-based system"""
    logger = ParameterLogger()
    measurements = logger.get_measurements()
    
    print(f"🔄 Migrating {len(measurements)} measurements to file-based system...")
    
    # Create data directory structure
    data_dir = "cv_data"
    os.makedirs(data_dir, exist_ok=True)
    
    mapping = {
        "measurements": {},
        "metadata": {
            "created": datetime.now().isoformat(),
            "version": "1.0",
            "description": "File-based CV data mapping"
        }
    }
    
    for measurement in measurements:
        measurement_id = measurement['id']
        
        # Get CV data from database
        cv_data = logger.get_measurement_cv_data(measurement_id)
        
        if cv_data:
            # Create filename
            scan_rate = measurement.get('scan_rate', 'unknown')
            timestamp = measurement.get('timestamp', '').replace(':', '-').replace(' ', 'T')
            filename = f"measurement_{measurement_id}_{scan_rate}mVs_{timestamp}.csv"
            file_path = os.path.join(data_dir, filename)
            
            # Write CV data to CSV
            with open(file_path, 'w') as f:
                f.write("Voltage(V),Current(uA)\\n")
                for point in cv_data:
                    f.write(f"{point['voltage']},{point['current']}\\n")
            
            # Add to mapping
            mapping["measurements"][str(measurement_id)] = {
                "scan_rate": measurement.get('scan_rate'),
                "filename": filename,
                "file_path": file_path,
                "timestamp": measurement.get('timestamp'),
                "original_filename": measurement.get('original_filename'),
                "notes": f"Migrated from database on {datetime.now().isoformat()}"
            }
            
            print(f"✅ Migrated measurement {measurement_id} to {filename}")
    
    # Save mapping file
    mapping_file = "cv_data_mapping.json"
    with open(mapping_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"✅ Migration complete! Files saved in '{data_dir}' directory")
    print(f"   Mapping file: {mapping_file}")
    print(f"   Total files: {len(mapping['measurements'])}")

def main():
    parser = argparse.ArgumentParser(description='Database backup/restore utility')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--export', type=str, help='Export database to JSON file')
    group.add_argument('--import', dest='import_file', type=str, help='Import database from JSON file')
    group.add_argument('--migrate-to-files', action='store_true', help='Migrate to file-based system')
    
    args = parser.parse_args()
    
    if args.export:
        export_database(args.export)
    elif args.import_file:
        import_database(args.import_file)
    elif args.migrate_to_files:
        migrate_to_file_based()

if __name__ == '__main__':
    main()