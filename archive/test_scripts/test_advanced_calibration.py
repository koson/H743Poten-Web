#!/usr/bin/env python3
"""
Quick Advanced Calibration Test
"""

from advanced_calibration_comparison import AdvancedCalibrationComparison
import matplotlib
matplotlib.use('Agg')

def main():
    print("🎯 Advanced Calibration Techniques Comparison")
    print("="*60)
    
    visualizer = AdvancedCalibrationComparison()
    
    # Get data
    stm32_data = visualizer.get_measurement_data(75)
    palmsens_data = visualizer.get_measurement_data(90)
    
    if not stm32_data or not palmsens_data:
        print("❌ Could not load data")
        return
    
    print(f"📊 Data loaded successfully:")
    print(f"  STM32: {stm32_data['sample_id']} - {len(stm32_data['current'])} points")
    print(f"  PalmSens: {palmsens_data['sample_id']} - {len(palmsens_data['current'])} points")
    
    # Apply calibrations
    stm32_voltage = stm32_data['voltage']
    stm32_current = stm32_data['current']
    palmsens_voltage = palmsens_data['voltage']
    palmsens_current = palmsens_data['current']
    
    print(f"\n🔧 Applying calibration techniques...")
    
    # Technique 1: Voltage + Current
    cal1_voltage, cal1_current, voltage_offset, current_gain1 = \
        visualizer.calibrate_technique1_voltage_current(stm32_voltage, stm32_current, 
                                                      palmsens_voltage, palmsens_current)
    
    # Technique 2: Current only
    cal2_voltage, cal2_current, current_offset, current_gain2 = \
        visualizer.calibrate_technique2_current_only(stm32_voltage, stm32_current, 
                                                   palmsens_voltage, palmsens_current)
    
    # Calculate statistics
    stats1 = visualizer.calculate_statistics(stm32_current, palmsens_current, cal1_current)
    stats2 = visualizer.calculate_statistics(stm32_current, palmsens_current, cal2_current)
    
    print(f"\n📈 RESULTS COMPARISON:")
    print("="*60)
    
    print(f"🔧 Technique 1 (Voltage + Current Calibration):")
    print(f"  Voltage Offset: {voltage_offset*1000:+.2f} mV")
    print(f"  Current Gain: {current_gain1:.3f}x")
    if stats1:
        print(f"  R² improvement: {stats1['r2_before']:.3f} → {stats1['r2_after']:.3f} ({((stats1['r2_after']-stats1['r2_before'])/abs(stats1['r2_before'])*100):+.1f}%)")
        print(f"  RMSE: {stats1['rmse_before']*1e6:.0f} → {stats1['rmse_after']*1e6:.0f} μA ({((stats1['rmse_before']-stats1['rmse_after'])/stats1['rmse_before']*100):+.1f}%)")
    
    print(f"\n⚡ Technique 2 (Current-Only Calibration, Voltage Preserved):")
    print(f"  Voltage: UNCHANGED (preserved)")
    print(f"  Current Offset: {current_offset*1e6:+.2f} μA")
    print(f"  Current Gain: {current_gain2:.3f}x")
    if stats2:
        print(f"  R² improvement: {stats2['r2_before']:.3f} → {stats2['r2_after']:.3f} ({((stats2['r2_after']-stats2['r2_before'])/abs(stats2['r2_before'])*100):+.1f}%)")
        print(f"  RMSE: {stats2['rmse_before']*1e6:.0f} → {stats2['rmse_after']*1e6:.0f} μA ({((stats2['rmse_before']-stats2['rmse_after'])/stats2['rmse_before']*100):+.1f}%)")
    
    print(f"\n🎯 RECOMMENDATION:")
    print("-" * 40)
    if stats1 and stats2:
        if stats1['r2_after'] > stats2['r2_after']:
            diff = stats1['r2_after'] - stats2['r2_after']
            print(f"✅ Technique 1 performs better (R² difference: +{diff:.3f})")
        elif stats2['r2_after'] > stats1['r2_after']:
            diff = stats2['r2_after'] - stats1['r2_after']
            print(f"✅ Technique 2 performs better (R² difference: +{diff:.3f})")
        else:
            print(f"⚖️  Both techniques show similar performance")
        
        print(f"\n💡 Use Technique 2 if:")
        print(f"   • Voltage preservation is critical")
        print(f"   • You need to maintain STM32 voltage reference")
        print(f"   • Only current scaling is acceptable")
        
        print(f"\n💡 Use Technique 1 if:")
        print(f"   • Overall accuracy is priority")
        print(f"   • Voltage shift is acceptable")
        print(f"   • Maximum correlation with reference")
    
    # Generate advanced comparison graph
    print(f"\n📊 Generating advanced comparison graph...")
    visualizer.plot_advanced_comparison(75, 90)
    
    print("="*60)
    print("✅ Advanced calibration comparison completed!")

if __name__ == "__main__":
    main()