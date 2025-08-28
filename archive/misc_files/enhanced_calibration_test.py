#!/usr/bin/env python3
"""
Enhanced Cross-Instrument Calibration with Cross-Sample Support
Supports calibration between similar samples when exact matches are not available
"""

import sys
import os
sys.path.append('src')

from services.cross_instrument_calibrator import cross_instrument_calibrator, CalibrationDataSet
from services.parameter_logging import parameter_logger
from services.hybrid_data_manager import hybrid_manager
from datetime import datetime
import json

def find_similar_samples(measurements):
    """Find similar samples for cross-calibration"""
    
    # Group by instrument and scan rate
    grouped = {}
    for m in measurements:
        instrument = m.get('instrument_type', 'palmsens' if m['id'] < 1000 else 'stm32')
        scan_rate = m.get('scan_rate', 0)
        concentration = m['sample_id'].split()[0]  # Extract concentration (e.g., '5mM')
        
        key = f"{concentration}_{scan_rate}mVs"
        if key not in grouped:
            grouped[key] = {'stm32': [], 'palmsens': []}
        
        grouped[key][instrument].append(m)
    
    # Find groups with both instruments
    calibration_opportunities = []
    for key, data in grouped.items():
        if data['stm32'] and data['palmsens']:
            concentration, scan_rate = key.split('_')
            scan_rate = scan_rate.replace('mVs', '')
            
            calibration_opportunities.append({
                'key': key,
                'concentration': concentration,
                'scan_rate': float(scan_rate),
                'stm32_samples': data['stm32'],
                'palmsens_samples': data['palmsens']
            })
    
    return calibration_opportunities

def perform_cross_sample_calibration():
    """Perform calibration using similar samples"""
    
    print("🔬 Enhanced Cross-Sample Calibration System")
    print("=" * 60)
    
    # Get new dataset
    measurements = parameter_logger.get_measurements()
    new_data = [m for m in measurements if 60 <= m['id'] <= 90]
    
    print(f"📊 Analyzing {len(new_data)} new measurements...")
    
    # Find calibration opportunities
    opportunities = find_similar_samples(new_data)
    
    print(f"\n🎯 Found {len(opportunities)} calibration opportunities:")
    
    calibration_results = []
    
    for opp in opportunities:
        print(f"\n📈 Testing {opp['key']}:")
        print(f"   Concentration: {opp['concentration']}")
        print(f"   Scan Rate: {opp['scan_rate']} mV/s")
        print(f"   STM32 samples: {len(opp['stm32_samples'])}")
        print(f"   PalmSens samples: {len(opp['palmsens_samples'])}")
        
        # Select representative samples (first one from each)
        stm32_sample = opp['stm32_samples'][0]
        palmsens_sample = opp['palmsens_samples'][0]
        
        print(f"   Selected STM32 ID {stm32_sample['id']} ({stm32_sample['sample_id']})")
        print(f"   Selected PalmSens ID {palmsens_sample['id']} ({palmsens_sample['sample_id']})")
        
        try:
            # Get CV data
            stm32_data_raw = hybrid_manager.get_measurement_data(stm32_sample['id'])
            palmsens_data_raw = hybrid_manager.get_measurement_data(palmsens_sample['id'])
            
            if not stm32_data_raw or not palmsens_data_raw:
                print(f"   ❌ Missing CV data")
                continue
            
            # Convert to dict format if needed
            def convert_to_dict_format(data):
                if data and isinstance(data[0], list):
                    return [{'voltage': point[0], 'current': point[1]} for point in data]
                return data
            
            stm32_data = convert_to_dict_format(stm32_data_raw)
            palmsens_data = convert_to_dict_format(palmsens_data_raw)
            
            print(f"   📊 STM32 data points: {len(stm32_data)}")
            print(f"   📊 PalmSens data points: {len(palmsens_data)}")
            
            # Create datasets
            palmsens_dataset = CalibrationDataSet(
                measurement_mode='CV',
                sample_id=f"{opp['concentration']}_reference",
                instrument_type='palmsens',
                timestamp=datetime.fromisoformat(palmsens_sample['timestamp']),
                scan_rate=opp['scan_rate'],
                cv_data=palmsens_data
            )
            
            # Create STM32 CSV simulation
            csv_lines = ["Mode,TimeStamp(us),REVoltage,WEVoltage,WECurrentRange,CycleNo,DAC_CH1,DAC_CH2,counter,LUTData"]
            for i, point in enumerate(stm32_data):
                # Simulate realistic STM32 values
                timestamp_us = i * 1000
                re_voltage = point['voltage']
                we_voltage = point['voltage'] + (point['current'] * 1000)  # Simulate TIA output
                we_current_range = 1  # 1kΩ TIA
                cycle_no = 1
                dac_ch1 = int(2048 + (point['voltage'] / 3.3) * 2048)  # Simulate DAC
                dac_ch2 = 2048  # Virtual ground
                counter = i
                lut_data = dac_ch1
                
                csv_lines.append(f"CV,{timestamp_us},{re_voltage:.6f},{we_voltage:.6f},{we_current_range},{cycle_no},{dac_ch1},{dac_ch2},{counter},{lut_data}")
            
            stm32_csv = "\\n".join(csv_lines)
            
            # Parse STM32 data
            stm32_dataset = cross_instrument_calibrator.parse_stm32_data(
                stm32_csv, f"{opp['concentration']}_stm32"
            )
            
            print(f"   ✅ STM32 dataset parsed: {len(stm32_dataset.cv_data)} points")
            
            # Perform calibration
            result = cross_instrument_calibrator.calibrate_stm32_to_palmsens(
                stm32_dataset, palmsens_dataset
            )
            
            # Store result
            calibration_key = f"CV_{opp['key']}"
            result['calibration_key'] = calibration_key
            result['stm32_sample_id'] = stm32_sample['sample_id']
            result['palmsens_sample_id'] = palmsens_sample['sample_id']
            result['scan_rate'] = opp['scan_rate']
            
            calibration_results.append(result)
            
            # Display results
            quality = ('excellent' if result['r_squared'] > 0.95 else 
                     'good' if result['r_squared'] > 0.8 else 'fair')
            print(f"   ✅ Calibration successful!")
            print(f"   📈 R² Value: {result['r_squared']:.4f} ({quality})")
            print(f"   🔧 Current Slope: {result['current_slope']:.6f}")
            print(f"   ⚡ Current Offset: {result['current_offset']:.3e}")
            print(f"   📊 Data Points: {result['data_points']}")
            
        except Exception as e:
            print(f"   ❌ Calibration failed: {e}")
            continue
    
    # Save calibration models
    if calibration_results:
        print(f"\n💾 Saving {len(calibration_results)} calibration models...")
        
        models_file = "data_logs/calibration_models.json"
        os.makedirs("data_logs", exist_ok=True)
        cross_instrument_calibrator.save_calibration_models(models_file)
        
        # Create summary report
        summary_file = "data_logs/cross_sample_calibration_report.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'calibration_timestamp': datetime.now().isoformat(),
                'calibration_type': 'cross_sample',
                'total_calibrations': len(calibration_results),
                'results': calibration_results,
                'data_range': '60-90',
                'summary_statistics': {
                    'average_r_squared': sum(r['r_squared'] for r in calibration_results) / len(calibration_results),
                    'best_r_squared': max(r['r_squared'] for r in calibration_results),
                    'worst_r_squared': min(r['r_squared'] for r in calibration_results)
                }
            }, f, indent=2)
        
        print(f"   ✅ Models saved to {models_file}")
        print(f"   📋 Report saved to {summary_file}")
        
        # Summary statistics
        avg_r2 = sum(r['r_squared'] for r in calibration_results) / len(calibration_results)
        best_r2 = max(r['r_squared'] for r in calibration_results)
        
        print(f"\n📊 Calibration Summary:")
        print(f"   🎯 Total calibrations: {len(calibration_results)}")
        print(f"   📈 Average R²: {avg_r2:.4f}")
        print(f"   🏆 Best R²: {best_r2:.4f}")
        
        excellent_count = sum(1 for r in calibration_results if r['r_squared'] > 0.95)
        good_count = sum(1 for r in calibration_results if 0.8 < r['r_squared'] <= 0.95)
        fair_count = len(calibration_results) - excellent_count - good_count
        
        print(f"   🌟 Quality distribution:")
        print(f"      Excellent (R²>0.95): {excellent_count}")
        print(f"      Good (R²>0.8): {good_count}")
        print(f"      Fair (R²≤0.8): {fair_count}")
        
    else:
        print("❌ No successful calibrations performed")
    
    print("\n🎯 Cross-Sample Calibration Complete!")
    return len(calibration_results) > 0

if __name__ == "__main__":
    success = perform_cross_sample_calibration()
    sys.exit(0 if success else 1)