#!/usr/bin/env python3
"""
Quick test of calibration functionality without server
"""

import sys
import os
sys.path.append('src')

def test_calibration_without_server():
    """Test calibration functionality directly without web server"""
    
    print("🔬 Testing Calibration System (Direct Mode)\n")
    
    try:
        # Import calibration components
        from services.cross_instrument_calibrator import cross_instrument_calibrator
        from services.parameter_logging import parameter_logger
        from services.hybrid_data_manager import hybrid_manager
        
        print("✅ All modules imported successfully")
        
        # Test 1: Get measurements
        print("\n1. Testing measurement access...")
        measurements = parameter_logger.get_measurements()
        print(f"   📊 Found {len(measurements)} measurements")
        
        # Find STM32 and PalmSens measurements
        stm32_measurements = [m for m in measurements if 
                            m.get('instrument_type') == 'stm32' or 
                            (not m.get('instrument_type') and m['id'] >= 1000)]
        palmsens_measurements = [m for m in measurements if 
                               m.get('instrument_type') == 'palmsens' or 
                               (not m.get('instrument_type') and m['id'] < 1000)]
        
        print(f"   🔧 STM32 measurements: {len(stm32_measurements)}")
        print(f"   📱 PalmSens measurements: {len(palmsens_measurements)}")
        
        if stm32_measurements and palmsens_measurements:
            # Test 2: Get CV data
            print("\n2. Testing CV data access...")
            stm32_id = stm32_measurements[0]['id']
            palmsens_id = palmsens_measurements[0]['id']
            
            print(f"   Testing STM32 ID {stm32_id}...")
            stm32_data = hybrid_manager.get_measurement_data(stm32_id)
            print(f"   📈 STM32 data points: {len(stm32_data)}")
            
            print(f"   Testing PalmSens ID {palmsens_id}...")
            palmsens_data = hybrid_manager.get_measurement_data(palmsens_id)
            print(f"   📊 PalmSens data points: {len(palmsens_data)}")
            
            if stm32_data and palmsens_data:
                # Test 3: Create datasets for calibration
                print("\n3. Testing calibration datasets...")
                
                from services.cross_instrument_calibrator import CalibrationDataSet
                from datetime import datetime
                
                # Create PalmSens dataset
                palmsens_dataset = CalibrationDataSet(
                    measurement_mode='CV',
                    sample_id='test_sample',
                    instrument_type='palmsens',
                    timestamp=datetime.now(),
                    cv_data=palmsens_data
                )
                print(f"   ✅ PalmSens dataset created: {len(palmsens_dataset.cv_data)} points")
                
                # Simulate STM32 CSV for parsing
                csv_lines = ["Mode,TimeStamp(us),REVoltage,WEVoltage,WECurrentRange,CycleNo,DAC_CH1,DAC_CH2,counter,LUTData"]
                for i, point in enumerate(stm32_data[:100]):
                    csv_lines.append(f"CV,{i*1000},{point['voltage']:.6f},{point['voltage']:.6f},1,1,2048,2048,{i},1024")
                
                test_csv = "\n".join(csv_lines)
                
                # Parse STM32 data
                stm32_dataset = cross_instrument_calibrator.parse_stm32_data(test_csv, 'test_sample')
                print(f"   ✅ STM32 dataset parsed: {len(stm32_dataset.cv_data)} points")
                
                # Test 4: Perform calibration
                print("\n4. Testing calibration algorithm...")
                try:
                    result = cross_instrument_calibrator.calibrate_stm32_to_palmsens(
                        stm32_dataset, palmsens_dataset
                    )
                    
                    print(f"   ✅ Calibration successful!")
                    print(f"   📈 R² Value: {result['r_squared']:.4f}")
                    print(f"   🔧 Current Slope: {result['current_slope']:.6f}")
                    print(f"   ⚡ Current Offset: {result['current_offset']:.3e}")
                    print(f"   📊 Data Points: {result['data_points']}")
                    
                    quality = ('excellent' if result['r_squared'] > 0.95 else 
                             'good' if result['r_squared'] > 0.8 else 'fair')
                    print(f"   🏆 Quality: {quality.upper()}")
                    
                    # Test 5: Model storage
                    print("\n5. Testing model storage...")
                    models_file = "data_logs/calibration_models.json"
                    os.makedirs("data_logs", exist_ok=True)
                    cross_instrument_calibrator.save_calibration_models(models_file)
                    
                    model_count = len(cross_instrument_calibrator.calibration_models)
                    print(f"   ✅ Models saved: {model_count}")
                    
                    return True
                    
                except Exception as e:
                    print(f"   ❌ Calibration failed: {e}")
                    return False
            else:
                print("   ⚠️  Missing CV data for calibration")
                return False
        else:
            print("   ⚠️  Missing STM32 or PalmSens measurements")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_calibration_without_server()
    print(f"\n🎯 Direct Calibration Test {'✅ PASSED' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)