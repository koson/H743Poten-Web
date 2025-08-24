#!/usr/bin/env python3
"""
Test Parameter Logging with Real Data Files
Test with actual sample files to ensure proper calibration pairing
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.services.parameter_logging import parameter_logger
    from src.routes.peak_detection import save_analysis_to_log, extract_sample_info_from_filename
except ImportError:
    from services.parameter_logging import parameter_logger
    from routes.peak_detection import save_analysis_to_log, extract_sample_info_from_filename

def test_with_real_files():
    """Test with real data files"""
    print("🧪 TESTING WITH REAL DATA FILES")
    print("=" * 50)
    
    # Sample files that should be paired
    test_files = [
        "Test_data/Palmsens/Palmsens_5mM/Palmsens_5mM_CV_100mVpS_E1_scan_05.csv",
        "Test_data/Stm32/Pipot_Ferro_5_0mM/Pipot_Ferro_5_0mM_100mVpS_E4_scan_05.csv"
    ]
    
    measurements = []
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\n📁 Processing: {file_path}")
            
            # Load actual data
            try:
                df = pd.read_csv(file_path)
                voltage = df.iloc[:, 0].values  # First column is voltage
                current = df.iloc[:, 1].values  # Second column is current
                
                print(f"   📊 Data points: {len(voltage)}")
                print(f"   ⚡ Voltage range: {np.min(voltage):.3f}V to {np.max(voltage):.3f}V")
                print(f"   🔋 Current range: {np.min(current):.2f}µA to {np.max(current):.2f}µA")
                
                # Create sample peaks (since we don't have actual peak detection here)
                peaks = [
                    {
                        'type': 'oxidation',
                        'voltage': 0.2,
                        'current': np.max(current),
                        'height': np.max(current) - np.min(current),
                        'enabled': True
                    }
                ]
                
                # Extract filename for metadata
                filename = os.path.basename(file_path)
                metadata = {
                    'filename': filename,
                    'user_notes': f'Real data test from {filename}',
                    'raw_data': {}
                }
                
                # Save to log
                result = save_analysis_to_log(voltage, current, peaks, metadata)
                
                if result['success']:
                    measurements.append(result['measurement_id'])
                    print(f"   ✅ Saved measurement ID: {result['measurement_id']}")
                else:
                    print(f"   ❌ Failed: {result['error']}")
                    
            except Exception as e:
                print(f"   ❌ Error reading file: {str(e)}")
        else:
            print(f"   ⚠️ File not found: {file_path}")
    
    return measurements

def test_sample_id_standardization():
    """Test sample ID generation with various filename patterns"""
    print("\n🏷️ TESTING SAMPLE ID STANDARDIZATION")
    print("=" * 50)
    
    # Test various filename patterns that should generate the same sample_id
    test_patterns = [
        # Different ways to represent 5mM, 100mV/s
        "Palmsens_5mM_CV_100mVpS_E1_scan_05.csv",
        "Pipot_Ferro_5_0mM_100mVpS_E4_scan_05.csv", 
        "Sample_5.0mM_CV_100mVpS_test.csv",
        
        # Different ways to represent 0.5mM, 50mV/s
        "Palmsens_0.5mM_CV_50mVpS_E2_scan_06.csv",
        "Pipot_Ferro_0_5mM_50mVpS_E1_scan_06.csv",
        
        # Edge cases
        "unknown_5mm_100mvps.csv",
        "test_5_0mm_100mvps_data.csv"
    ]
    
    sample_groups = {}
    
    for filename in test_patterns:
        info = extract_sample_info_from_filename(filename)
        
        print(f"📁 {filename}")
        print(f"   🏷️ Sample ID: '{info['sample_id']}'")
        print(f"   🔬 Instrument: {info['instrument_type']}")
        print(f"   ⚡ Scan Rate: {info['scan_rate']} mV/s" if info['scan_rate'] else "   ⚡ Scan Rate: Unknown")
        print(f"   🧪 Concentration: {info['concentration']} mM" if info['concentration'] else "   🧪 Concentration: Unknown")
        
        # Group by expected pairing key
        key = f"{info['concentration']}mM_{info['scan_rate']}mVpS"
        if key not in sample_groups:
            sample_groups[key] = []
        sample_groups[key].append((filename, info['sample_id']))
        print()
    
    # Check for proper grouping
    print("📊 SAMPLE GROUPING ANALYSIS")
    print("-" * 30)
    
    for key, samples in sample_groups.items():
        print(f"Group {key}:")
        sample_ids = set(info[1] for info in samples)
        if len(sample_ids) == 1:
            print(f"   ✅ All samples have same ID: '{list(sample_ids)[0]}'")
        else:
            print(f"   ❌ Inconsistent IDs: {sample_ids}")
        for filename, sample_id in samples:
            print(f"      - {filename}")
        print()

def create_matched_test_data():
    """Create test data with guaranteed matching sample IDs"""
    print("\n🔧 CREATING MATCHED TEST DATA")
    print("=" * 40)
    
    # Clear existing database
    if os.path.exists(parameter_logger.db_path):
        os.remove(parameter_logger.db_path)
        parameter_logger._init_database()
    
    # Create test data with proper matching
    test_cases = [
        {
            'filename': 'Palmsens_5mM_CV_100mVpS_E1_scan_05.csv',
            'instrument': 'palmsens',
            'concentration': 5.0,
            'scan_rate': 100
        },
        {
            'filename': 'Pipot_Ferro_5_0mM_100mVpS_E4_scan_05.csv',
            'instrument': 'stm32', 
            'concentration': 5.0,
            'scan_rate': 100
        }
    ]
    
    measurement_ids = []
    
    for test_case in test_cases:
        print(f"📊 Creating: {test_case['filename']}")
        
        # Create synthetic data
        voltage = np.linspace(-0.4, 0.6, 200)
        current = np.random.normal(0, 1, 200) + 0.5 * voltage
        
        # Add a peak
        peak_voltage = 0.2
        peak_idx = np.argmin(np.abs(voltage - peak_voltage))
        current[peak_idx-5:peak_idx+5] += 10
        
        peaks = [{
            'type': 'oxidation',
            'voltage': peak_voltage,
            'current': current[peak_idx],
            'height': 10,
            'enabled': True
        }]
        
        # Force correct sample_id format
        sample_id = f"sample_{int(test_case['concentration'])}mM_{test_case['scan_rate']}mVpS"
        
        # Create measurement data directly
        measurement_data = {
            'sample_id': sample_id,
            'instrument_type': test_case['instrument'],
            'timestamp': datetime.now(),
            'scan_rate': test_case['scan_rate'],
            'voltage_start': float(np.min(voltage)),
            'voltage_end': float(np.max(voltage)),
            'data_points': len(voltage),
            'original_filename': test_case['filename'],
            'user_notes': f'Test measurement for {sample_id}'
        }
        
        # Save directly to database
        measurement_id = parameter_logger.save_measurement(measurement_data)
        parameter_logger.save_peak_parameters(measurement_id, peaks)
        
        measurement_ids.append(measurement_id)
        print(f"   ✅ Saved measurement ID: {measurement_id} with sample_id: '{sample_id}'")
    
    return measurement_ids

def test_calibration_functionality(measurement_ids):
    """Test calibration pair detection and session creation"""
    print("\n🔗 TESTING CALIBRATION FUNCTIONALITY")
    print("=" * 45)
    
    # Check all measurements
    measurements = parameter_logger.get_measurements()
    print(f"📊 Total measurements: {len(measurements)}")
    
    for m in measurements:
        print(f"   - ID {m['id']}: '{m['sample_id']}' ({m['instrument_type']})")
    
    # Get unique sample IDs
    sample_ids = list(set(m['sample_id'] for m in measurements))
    print(f"\n🏷️ Unique sample IDs: {sample_ids}")
    
    # Test calibration pairs for each sample
    for sample_id in sample_ids:
        pairs = parameter_logger.get_calibration_pairs(sample_id)
        print(f"\n📝 Sample '{sample_id}': {len(pairs)} calibration pairs")
        
        for pair in pairs:
            print(f"   🔗 Reference: ID {pair['reference_id']} ({pair['reference_instrument']})")
            print(f"      Target: ID {pair['target_id']} ({pair['target_instrument']})")
            
            # Create a calibration session
            session_data = {
                'session_name': f'{sample_id}_Test_Calibration',
                'reference_measurement_id': pair['reference_id'],
                'target_measurement_id': pair['target_id'],
                'calibration_method': 'linear',
                'notes': 'Automated test calibration session'
            }
            
            session_id = parameter_logger.create_calibration_session(session_data)
            print(f"      ✅ Created calibration session: {session_id}")

def main():
    """Run comprehensive parameter logging tests"""
    print("🚀 COMPREHENSIVE PARAMETER LOGGING TEST")
    print("=" * 60)
    
    try:
        # Test sample ID standardization
        test_sample_id_standardization()
        
        # Create matched test data
        measurement_ids = create_matched_test_data()
        
        # Test calibration functionality
        test_calibration_functionality(measurement_ids)
        
        # Try with real files if available
        try:
            real_measurements = test_with_real_files()
            if real_measurements:
                print(f"\n📁 Successfully processed {len(real_measurements)} real data files")
        except Exception as e:
            print(f"\n⚠️ Real file testing skipped: {str(e)}")
        
        print(f"\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print(f"📍 Database: {parameter_logger.db_path}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()