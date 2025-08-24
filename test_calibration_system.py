#!/usr/bin/env python3
"""
Test cross-instrument calibration functionality
"""

import sys
import os
sys.path.append('src')

from services.cross_instrument_calibrator import cross_instrument_calibrator, CalibrationDataSet
from services.parameter_logging import parameter_logger
from datetime import datetime
import json

def test_calibration_system():
    """Test the complete calibration system"""
    
    print("=== Cross-Instrument Calibration Test ===\n")
    
    # 1. Test measurement pair detection
    print("1. Testing measurement pair detection...")
    try:
        measurements = parameter_logger.get_measurements()
        print(f"   Found {len(measurements)} total measurements")
        
        # Group by sample_id and instrument
        samples = {}
        for m in measurements:
            sample_id = m['sample_id']
            if sample_id not in samples:
                samples[sample_id] = {'stm32': [], 'palmsens': []}
            
            # Determine instrument type
            instrument = m.get('instrument_type', 'unknown')
            if instrument == 'unknown':
                # Guess based on ID range (lower IDs are typically PalmSens)
                instrument = 'palmsens' if m['id'] < 1000 else 'stm32'
            
            if instrument in samples[sample_id]:
                samples[sample_id][instrument].append(m)
        
        # Find pairs
        pairs = []
        for sample_id, instruments in samples.items():
            if instruments['stm32'] and instruments['palmsens']:
                pairs.append({
                    'sample_id': sample_id,
                    'stm32_count': len(instruments['stm32']),
                    'palmsens_count': len(instruments['palmsens'])
                })
        
        print(f"   Found {len(pairs)} sample pairs available for calibration:")
        for pair in pairs:
            print(f"     - {pair['sample_id']}: {pair['stm32_count']} STM32, {pair['palmsens_count']} PalmSens")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # 2. Test STM32 data parsing
    print("\n2. Testing STM32 CSV parsing...")
    try:
        # Find a recent STM32 measurement with data
        stm32_measurements = [m for m in measurements if 
                            m.get('instrument_type') == 'stm32' or 
                            (not m.get('instrument_type') and m['id'] >= 1000)]
        
        if stm32_measurements:
            test_measurement = stm32_measurements[-1]  # Most recent
            print(f"   Testing with measurement ID {test_measurement['id']}")
            
            # Try to get CV data (this would normally be CSV content)
            try:
                from services.hybrid_data_manager import hybrid_manager
                cv_data = hybrid_manager.get_measurement_data(test_measurement['id'])
                print(f"   Found {len(cv_data)} CV data points")
                
                # Convert to CSV format for testing
                csv_lines = ["Mode,TimeStamp(us),REVoltage,WEVoltage,WECurrentRange,CycleNo,DAC_CH1,DAC_CH2,counter,LUTData"]
                for i, point in enumerate(cv_data[:100]):  # Limit for testing
                    # Simulate STM32 CSV format with proper columns
                    csv_lines.append(f"CV,{i*1000},{point['voltage']:.6f},{point['voltage']:.6f},1,1,2048,2048,{i},1024")
                
                test_csv = "\n".join(csv_lines)
                
                # Parse with calibrator
                dataset = cross_instrument_calibrator.parse_stm32_data(test_csv, test_measurement['sample_id'])
                data_points_count = len(dataset.data_points) if dataset.data_points else 0
                cv_data_count = len(dataset.cv_data) if dataset.cv_data else 0
                print(f"   Parsed dataset: {data_points_count} raw points, {cv_data_count} CV points")
                print(f"   Mode: {dataset.measurement_mode}, Instrument: {dataset.instrument_type}")
                
            except Exception as e:
                print(f"   Could not get CV data: {e}")
        else:
            print("   No STM32 measurements found")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # 3. Test calibration models storage
    print("\n3. Testing calibration models...")
    try:
        # Create a dummy calibration result
        dummy_model = {
            'current_slope': 1.234567,
            'current_offset': 1.23e-9,
            'voltage_slope': 0.987654,
            'voltage_offset': 0.001234,
            'r_squared': 0.9876,
            'timestamp': datetime.now()
        }
        
        # Store model
        model_key = "test_CV_sample"
        cross_instrument_calibrator.calibration_models[model_key] = dummy_model
        
        # Save to file
        models_file = "data_logs/calibration_models.json"
        os.makedirs("data_logs", exist_ok=True)
        cross_instrument_calibrator.save_calibration_models(models_file)
        
        # Load back
        cross_instrument_calibrator.load_calibration_models(models_file)
        
        if model_key in cross_instrument_calibrator.calibration_models:
            print("   ✓ Calibration model save/load works correctly")
            print(f"   Model: R²={dummy_model['r_squared']}, slope={dummy_model['current_slope']}")
        else:
            print("   ✗ Model save/load failed")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # 4. Test API routes (simulate)
    print("\n4. Testing API route compatibility...")
    try:
        from routes.calibration_api import calibration_api_bp
        print("   ✓ Calibration API blueprint imported successfully")
        
        # Check route registration
        routes = [rule.rule for rule in calibration_api_bp.url_map.iter_rules()]
        print(f"   Available routes: {len(routes)}")
        for route in routes:
            print(f"     - {route}")
            
    except Exception as e:
        print(f"   Error importing API: {e}")
    
    print("\n=== Calibration Test Complete ===")

if __name__ == "__main__":
    test_calibration_system()