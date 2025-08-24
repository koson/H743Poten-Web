#!/usr/bin/env python3
"""
Simple Cross-Sample Calibration Test
Direct statistical calibration between STM32 and PalmSens measurements
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.hybrid_data_manager import HybridDataManager
import numpy as np
from scipy import stats
from collections import defaultdict
import json

def main():
    print("🔄 Simple Cross-Sample Calibration Test")
    print("=" * 50)
    
    hybrid_manager = HybridDataManager()
    
    # Get all measurements using ParameterLogger
    from src.services.parameter_logging import ParameterLogger
    
    logger = ParameterLogger()
    all_measurements = logger.get_measurements()
    
    # Filter to ID range 60-90
    measurements = [m for m in all_measurements if 60 <= m['id'] <= 90]
    
    stm32_measurements = []
    palmsens_measurements = []
    
    for measurement in measurements:
        # Handle lowercase instrument types
        instrument_type = measurement['instrument_type'].lower()
        if instrument_type == 'stm32':
            stm32_measurements.append(measurement)
        elif instrument_type in ['palmsens', 'ps']:  # Handle variations
            palmsens_measurements.append(measurement)
    
    print(f"📊 Found {len(stm32_measurements)} STM32 measurements")
    print(f"📊 Found {len(palmsens_measurements)} PalmSens measurements")
    
    # Group by concentration and scan rate
    def extract_conditions(measurement):
        sample_id = measurement['sample_id']
        # Parse concentration (e.g., "5mM E4S5" -> 5mM)
        conc = None
        scan_rate = measurement.get('scan_rate')
        
        if 'mM' in sample_id:
            try:
                conc_str = sample_id.split('mM')[0].strip()
                conc = float(conc_str) if conc_str.replace('.', '').isdigit() else None
            except:
                pass
        
        return conc, scan_rate
    
    # Group measurements by conditions
    stm32_by_conditions = defaultdict(list)
    palmsens_by_conditions = defaultdict(list)
    
    for m in stm32_measurements:
        conc, rate = extract_conditions(m)
        if conc is not None and rate is not None:
            stm32_by_conditions[(conc, rate)].append(m)
    
    for m in palmsens_measurements:
        conc, rate = extract_conditions(m)
        if conc is not None and rate is not None:
            palmsens_by_conditions[(conc, rate)].append(m)
    
    print(f"📈 STM32 condition groups: {len(stm32_by_conditions)}")
    print(f"📈 PalmSens condition groups: {len(palmsens_by_conditions)}")
    
    # Find matching conditions
    matching_conditions = set(stm32_by_conditions.keys()) & set(palmsens_by_conditions.keys())
    print(f"🎯 Matching conditions: {len(matching_conditions)}")
    
    successful_calibrations = 0
    all_results = {}
    
    for conc, scan_rate in sorted(matching_conditions):
        print(f"\n📍 Testing {conc}mM at {scan_rate} mV/s:")
        
        stm32_options = stm32_by_conditions[(conc, scan_rate)]
        palmsens_options = palmsens_by_conditions[(conc, scan_rate)]
        
        # Use first available measurement from each instrument
        stm32_measurement = stm32_options[0]
        palmsens_measurement = palmsens_options[0]
        
        print(f"   STM32: ID {stm32_measurement['id']} ({stm32_measurement['sample_id']})")
        print(f"   PalmSens: ID {palmsens_measurement['id']} ({palmsens_measurement['sample_id']})")
        
        try:
            # Get CV data - should be [[voltage, current], ...] format
            stm32_cv = hybrid_manager.get_cv_data(stm32_measurement['id'])
            palmsens_cv = hybrid_manager.get_cv_data(palmsens_measurement['id'])
            
            if not stm32_cv or not palmsens_cv:
                print(f"   ❌ Missing CV data")
                continue
                
            print(f"   📊 STM32: {len(stm32_cv)} points")
            print(f"   📊 PalmSens: {len(palmsens_cv)} points")
            
            # Extract current arrays
            stm32_currents = np.array([point[1] for point in stm32_cv])
            palmsens_currents = np.array([point[1] for point in palmsens_cv])
            
            # Align data lengths
            min_len = min(len(stm32_currents), len(palmsens_currents))
            stm32_i = stm32_currents[:min_len]
            palmsens_i = palmsens_currents[:min_len]
            
            # Filter out very small currents for better calibration
            current_threshold = max(1e-9, np.std(stm32_i) * 0.01)  # Adaptive threshold
            valid_mask = (np.abs(stm32_i) > current_threshold) & (np.abs(palmsens_i) > current_threshold)
            
            if np.sum(valid_mask) < 10:
                print(f"   ❌ Insufficient valid data points: {np.sum(valid_mask)}")
                continue
                
            stm32_valid = stm32_i[valid_mask]
            palmsens_valid = palmsens_i[valid_mask]
            
            # Perform linear regression: palmsens_current = slope * stm32_current + intercept
            slope, intercept, r_value, p_value, std_err = stats.linregress(stm32_valid, palmsens_valid)
            
            # Calculate quality metrics
            predicted = slope * stm32_valid + intercept
            rmse = np.sqrt(np.mean((palmsens_valid - predicted) ** 2))
            r_squared = r_value ** 2
            
            # Create result
            test_key = f"{conc}mM_{scan_rate}mVs"
            result = {
                'success': True,
                'concentration_mM': conc,
                'scan_rate_mVs': scan_rate,
                'stm32_id': stm32_measurement['id'],
                'palmsens_id': palmsens_measurement['id'],
                'gain_factor': float(slope),
                'offset': float(intercept),
                'r_squared': float(r_squared),
                'correlation': float(r_value),
                'p_value': float(p_value),
                'std_error': float(std_err),
                'rmse': float(rmse),
                'data_points_used': int(np.sum(valid_mask)),
                'stm32_current_range': [float(np.min(stm32_valid)), float(np.max(stm32_valid))],
                'palmsens_current_range': [float(np.min(palmsens_valid)), float(np.max(palmsens_valid))],
                'calibration_equation': f"I_palmsens = {slope:.6f} * I_stm32 + {intercept:.2e}"
            }
            
            print(f"   ✅ Calibration successful!")
            print(f"      Gain Factor: {slope:.6f}")
            print(f"      Offset: {intercept:.2e} A") 
            print(f"      R²: {r_squared:.4f}")
            print(f"      Correlation: {r_value:.4f}")
            print(f"      RMSE: {rmse:.2e} A")
            print(f"      Valid Points: {np.sum(valid_mask)}/{min_len}")
            
            successful_calibrations += 1
            all_results[test_key] = result
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎯 Cross-Sample Calibration Complete!")
    print(f"✅ Successful calibrations: {successful_calibrations}")
    print(f"❌ Failed calibrations: {len(matching_conditions) - successful_calibrations}")
    
    if successful_calibrations > 0:
        print(f"\n📋 Summary of Results:")
        for key, result in all_results.items():
            print(f"   {key}: Gain={result['gain_factor']:.4f}, R²={result['r_squared']:.3f}")
        
        # Save results
        output_file = 'cross_sample_calibration_results.json'
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\n💾 Results saved to {output_file}")
        
        # Calculate average calibration factor
        gains = [r['gain_factor'] for r in all_results.values()]
        avg_gain = np.mean(gains)
        std_gain = np.std(gains)
        print(f"\n📊 Average gain factor: {avg_gain:.6f} ± {std_gain:.6f}")
        
        if std_gain / avg_gain < 0.1:  # Less than 10% relative error
            print(f"🎯 Consistent calibration found! Use gain factor ≈ {avg_gain:.4f}")
        else:
            print(f"⚠️  Variable calibration factors - condition-specific calibration recommended")

if __name__ == "__main__":
    main()