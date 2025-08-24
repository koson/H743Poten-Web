#!/usr/bin/env python3
"""
Check database contents
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.services.parameter_logging import parameter_logger
except ImportError:
    from services.parameter_logging import parameter_logger

def check_database():
    """Check database contents"""
    print("📊 DATABASE CONTENTS")
    print("=" * 40)
    
    # Get all measurements
    measurements = parameter_logger.get_measurements()
    
    print(f"Total measurements: {len(measurements)}")
    print()
    
    for m in measurements:
        print(f"ID: {m['id']}")
        print(f"Sample ID: '{m['sample_id']}'")
        print(f"Instrument: {m['instrument_type']}")
        print(f"Scan Rate: {m['scan_rate']} mV/s")
        print(f"Filename: {m['original_filename']}")
        print("-" * 30)
    
    # Check for calibration pairs
    sample_ids = list(set(m['sample_id'] for m in measurements))
    print(f"\nUnique sample IDs: {sample_ids}")
    
    for sample_id in sample_ids:
        pairs = parameter_logger.get_calibration_pairs(sample_id)
        print(f"Sample '{sample_id}': {len(pairs)} pairs")

if __name__ == '__main__':
    check_database()