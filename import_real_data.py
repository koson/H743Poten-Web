#!/usr/bin/env python3
"""
Utility script to import real CV data from files into the database

Usage:
    python import_real_data.py --measurement-id 41 --file sample_data/Palmsens_0.5mM_CV_100mVpS_E1_scan_05.csv
    python import_real_data.py --auto-import  # Auto-import all sample files to existing measurements
"""

import argparse
import os
import sys
from src.services.parameter_logging import ParameterLogger

def import_single_file(measurement_id: int, file_path: str):
    """Import CV data from a single file to a measurement"""
    logger = ParameterLogger()
    
    print(f"🔄 Importing CV data from {file_path} to measurement {measurement_id}...")
    
    success = logger.import_cv_data_from_file(measurement_id, file_path)
    
    if success:
        print(f"✅ Successfully imported CV data to measurement {measurement_id}")
    else:
        print(f"❌ Failed to import CV data to measurement {measurement_id}")
    
    return success

def auto_import_sample_data():
    """Auto-import sample files to existing measurements based on scan rates"""
    logger = ParameterLogger()
    
    # Get all measurements that don't have CV data
    measurements = logger.get_measurements()
    
    # Map scan rates to sample files
    scan_rate_files = {
        20: 'sample_data/Palmsens_0.5mM_CV_20mVpS_E3_scan_08.csv',
        100: 'sample_data/Palmsens_0.5mM_CV_100mVpS_E1_scan_05.csv', 
        200: 'sample_data/Palmsens_0.5mM_CV_200mVpS_E2_scan_06.csv',
        400: 'sample_data/Pipot_Ferro_0_5mM_50mVpS_E4_scan_05.csv'
    }
    
    success_count = 0
    total_count = 0
    
    for measurement in measurements:
        measurement_id = measurement['id']
        scan_rate = measurement.get('scan_rate')
        
        # Check if measurement already has CV data
        cv_data = logger.get_measurement_cv_data(measurement_id)
        if cv_data:
            print(f"⏭️  Measurement {measurement_id} already has CV data, skipping...")
            continue
        
        # Find appropriate file for scan rate
        file_path = None
        if scan_rate in scan_rate_files:
            file_path = scan_rate_files[scan_rate]
        else:
            # Use default file
            file_path = 'sample_data/cv_sample.csv'
        
        if not os.path.exists(file_path):
            print(f"⚠️  File not found: {file_path} for measurement {measurement_id} (scan rate: {scan_rate})")
            continue
        
        print(f"🔄 Importing {file_path} to measurement {measurement_id} (scan rate: {scan_rate} mV/s)...")
        
        success = logger.import_cv_data_from_file(measurement_id, file_path)
        total_count += 1
        
        if success:
            success_count += 1
            print(f"✅ Successfully imported to measurement {measurement_id}")
        else:
            print(f"❌ Failed to import to measurement {measurement_id}")
    
    print(f"\n📊 Import Summary:")
    print(f"   Total measurements processed: {total_count}")
    print(f"   Successful imports: {success_count}")
    print(f"   Failed imports: {total_count - success_count}")
    
    return success_count > 0

def list_measurements():
    """List all measurements and their CV data status"""
    logger = ParameterLogger()
    measurements = logger.get_measurements()
    
    print("📋 Current Measurements:")
    print("=" * 80)
    
    for measurement in measurements:
        measurement_id = measurement['id']
        scan_rate = measurement.get('scan_rate', 'Unknown')
        scan_rate_str = f"{scan_rate}" if scan_rate != 'Unknown' else 'Unknown'
        filename = measurement.get('original_filename', 'No filename')
        timestamp = measurement.get('timestamp', 'Unknown')
        
        # Check CV data status
        cv_data = logger.get_measurement_cv_data(measurement_id)
        cv_status = f"{len(cv_data)} points" if cv_data else "No CV data"
        
        print(f"ID: {measurement_id:3d} | Scan Rate: {scan_rate_str:>8} mV/s | CV Data: {cv_status:12} | File: {filename}")
        print(f"         | Timestamp: {timestamp}")
        print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description='Import real CV data into measurement database')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--measurement-id', type=int, help='Measurement ID to import data to')
    group.add_argument('--auto-import', action='store_true', help='Auto-import sample data to all measurements')
    group.add_argument('--list', action='store_true', help='List all measurements and their status')
    
    parser.add_argument('--file', type=str, help='Path to CSV file to import (required with --measurement-id)')
    
    args = parser.parse_args()
    
    if args.list:
        list_measurements()
        return
    
    if args.measurement_id:
        if not args.file:
            print("❌ --file is required when using --measurement-id")
            sys.exit(1)
        
        success = import_single_file(args.measurement_id, args.file)
        sys.exit(0 if success else 1)
    
    if args.auto_import:
        success = auto_import_sample_data()
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()