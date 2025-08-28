#!/usr/bin/env python3
"""
Test Parameter Logging System
Test the parameter logging functionality with sample data
"""

import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.services.parameter_logging import parameter_logger
    from src.routes.peak_detection import save_analysis_to_log, extract_sample_info_from_filename
except ImportError:
    from services.parameter_logging import parameter_logger
    from routes.peak_detection import save_analysis_to_log, extract_sample_info_from_filename

import numpy as np

def create_sample_data():
    """Create sample CV data for testing"""
    # Create sample voltage sweep (CV)
    voltage = np.linspace(-0.4, 0.6, 220)  # 220 points like real data
    
    # Create current with some peaks
    current = np.zeros_like(voltage)
    
    # Add oxidation peak around 0.2V
    ox_peak_idx = np.argmin(np.abs(voltage - 0.2))
    current += 15 * np.exp(-((voltage - 0.2) / 0.05)**2)  # Gaussian peak
    
    # Add reduction peak around 0.1V  
    red_peak_idx = np.argmin(np.abs(voltage - 0.1))
    current -= 12 * np.exp(-((voltage - 0.1) / 0.04)**2)  # Negative Gaussian peak
    
    # Add baseline slope and noise
    current += 0.5 * voltage + 2.0  # Linear baseline
    current += np.random.normal(0, 0.3, len(voltage))  # Noise
    
    return voltage, current

def create_sample_peaks(voltage, current):
    """Create sample peak data for testing"""
    peaks = [
        {
            'type': 'reduction',
            'voltage': 0.1,
            'current': -9.5,
            'height': 12.3,
            'enabled': True,
            'baseline_current': 2.05,
            'baseline_slope': 0.5,
            'baseline_r2': 0.98,
            'baseline_voltage_start': 0.05,
            'baseline_voltage_end': 0.15
        },
        {
            'type': 'oxidation', 
            'voltage': 0.2,
            'current': 17.2,
            'height': 15.1,
            'enabled': True,
            'baseline_current': 2.10,
            'baseline_slope': 0.5,
            'baseline_r2': 0.97,
            'baseline_voltage_start': 0.15,
            'baseline_voltage_end': 0.25
        }
    ]
    return peaks

def test_sample_info_extraction():
    """Test filename parsing"""
    print("🧪 Testing Sample Info Extraction...")
    
    test_files = [
        "Palmsens_5mM_CV_100mVpS_E1_scan_05.csv",
        "Pipot_Ferro_0_5mM_50mVpS_E4_scan_05.csv", 
        "unknown_file.csv",
        ""
    ]
    
    for filename in test_files:
        info = extract_sample_info_from_filename(filename)
        print(f"  📁 {filename}")
        print(f"     Sample ID: {info['sample_id']}")
        print(f"     Instrument: {info['instrument_type']}")
        print(f"     Scan Rate: {info['scan_rate']} mV/s" if info['scan_rate'] else "     Scan Rate: Unknown")
        print(f"     Concentration: {info['concentration']} mM" if info['concentration'] else "     Concentration: Unknown")
        print()

def test_parameter_logging():
    """Test the parameter logging system"""
    print("🗂️ Testing Parameter Logging System...")
    
    # Test measurements data
    test_cases = [
        {
            'filename': 'Palmsens_5mM_CV_100mVpS_E1_scan_05.csv',
            'instrument': 'palmsens',
            'user_notes': 'Test reference measurement'
        },
        {
            'filename': 'Pipot_Ferro_5_0mM_100mVpS_E4_scan_05.csv',  # Same concentration and scan rate
            'instrument': 'stm32',
            'user_notes': 'Test target measurement',
            'raw_data': {
                'dac_ch1': [100, 110, 120],
                'dac_ch2': [200, 210, 220],
                'timestamp_us': [1000, 2000, 3000]
            }
        }
    ]
    
    measurement_ids = []
    
    for i, test_case in enumerate(test_cases):
        print(f"\n📊 Test Case {i+1}: {test_case['filename']}")
        
        # Create sample data
        voltage, current = create_sample_data()
        peaks = create_sample_peaks(voltage, current)
        
        # Add raw data to peaks if STM32
        if test_case['instrument'] == 'stm32':
            for j, peak in enumerate(peaks):
                peak['raw'] = {
                    'dac_ch1': 100 + j * 10,
                    'dac_ch2': 200 + j * 10, 
                    'timestamp_us': 1000 + j * 1000,
                    'counter': j,
                    'lut_data': 50 + j * 5
                }
        
        # Test saving
        metadata = {
            'filename': test_case['filename'],
            'user_notes': test_case['user_notes'],
            'raw_data': test_case.get('raw_data', {})
        }
        
        result = save_analysis_to_log(voltage, current, peaks, metadata)
        
        if result['success']:
            measurement_id = result['measurement_id']
            measurement_ids.append(measurement_id)
            print(f"  ✅ Saved measurement ID: {measurement_id}")
            print(f"  📈 Peaks saved: {result['peaks_saved']}")
        else:
            print(f"  ❌ Failed: {result['error']}")
    
    return measurement_ids

def test_data_retrieval(measurement_ids):
    """Test data retrieval functions"""
    print("\n📋 Testing Data Retrieval...")
    
    # Test getting all measurements
    measurements = parameter_logger.get_measurements()
    print(f"  📊 Total measurements in database: {len(measurements)}")
    
    # Test filtering by instrument
    palmsens_measurements = parameter_logger.get_measurements(instrument_type='palmsens')
    stm32_measurements = parameter_logger.get_measurements(instrument_type='stm32')
    print(f"  🔬 Palmsens measurements: {len(palmsens_measurements)}")
    print(f"  🖥️ STM32 measurements: {len(stm32_measurements)}")
    
    # Test getting peaks for each measurement
    for measurement_id in measurement_ids:
        peaks = parameter_logger.get_peak_parameters(measurement_id)
        print(f"  📈 Measurement {measurement_id}: {len(peaks)} peaks")
        
        # Show peak details
        for peak in peaks:
            print(f"    - Peak {peak['peak_index']}: {peak['peak_type']} at {peak['peak_voltage']:.3f}V")

def test_calibration_pairs():
    """Test calibration pair finding"""
    print("\n🔗 Testing Calibration Pairs...")
    
    # Get sample IDs
    measurements = parameter_logger.get_measurements()
    sample_ids = list(set(m['sample_id'] for m in measurements))
    
    for sample_id in sample_ids:
        pairs = parameter_logger.get_calibration_pairs(sample_id)
        print(f"  📝 Sample '{sample_id}': {len(pairs)} calibration pairs")
        
        for pair in pairs:
            print(f"    - Reference: ID {pair['reference_id']} ({pair['reference_instrument']})")
            print(f"      Target: ID {pair['target_id']} ({pair['target_instrument']})")

def test_calibration_session():
    """Test creating calibration session"""
    print("\n⚙️ Testing Calibration Session Creation...")
    
    # Get a sample with both instruments
    measurements = parameter_logger.get_measurements()
    sample_groups = {}
    
    for m in measurements:
        if m['sample_id'] not in sample_groups:
            sample_groups[m['sample_id']] = {'palmsens': [], 'stm32': []}
        sample_groups[m['sample_id']][m['instrument_type']].append(m)
    
    # Find a sample with both instruments
    for sample_id, groups in sample_groups.items():
        if groups['palmsens'] and groups['stm32']:
            ref_measurement = groups['palmsens'][0]
            target_measurement = groups['stm32'][0]
            
            session_data = {
                'session_name': f'{sample_id}_Test_Calibration',
                'reference_measurement_id': ref_measurement['id'],
                'target_measurement_id': target_measurement['id'],
                'calibration_method': 'linear',
                'notes': 'Test calibration session'
            }
            
            session_id = parameter_logger.create_calibration_session(session_data)
            print(f"  ✅ Created calibration session: {session_id}")
            print(f"     Sample: {sample_id}")
            print(f"     Reference: {ref_measurement['id']} ({ref_measurement['instrument_type']})")
            print(f"     Target: {target_measurement['id']} ({target_measurement['instrument_type']})")
            break
    else:
        print("  ⚠️ No samples with both Palmsens and STM32 measurements found")

def main():
    """Run all tests"""
    print("🚀 PARAMETER LOGGING SYSTEM TEST")
    print("=" * 50)
    
    try:
        # Test filename parsing
        test_sample_info_extraction()
        
        # Test logging system
        measurement_ids = test_parameter_logging()
        
        # Test data retrieval
        test_data_retrieval(measurement_ids)
        
        # Test calibration pairs
        test_calibration_pairs()
        
        # Test calibration session
        test_calibration_session()
        
        print("\n🎉 All tests completed successfully!")
        print(f"Database location: {parameter_logger.db_path}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()