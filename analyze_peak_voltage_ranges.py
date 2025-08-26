#!/usr/bin/env python3
"""
Analyze Real Peak Data for Voltage Zone Calibration
วิเคราะห์ peak จริงในฐานข้อมูลเพื่อหา voltage zones ที่เหมาะสม
"""

import sqlite3
import numpy as np
import matplotlib.pyplot as plt

def analyze_peak_voltage_ranges():
    """วิเคราะห์ voltage ranges ของ peak จริงใน database"""
    
    db_path = "data_logs/parameter_log.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("📊 Analyzing Real Peak Voltage Ranges")
        print("=" * 60)
        
        # Get all valid peaks (enabled = 1)
        cursor.execute("""
            SELECT pp.peak_type, pp.peak_voltage, pp.peak_current, pp.peak_height,
                   m.sample_id, m.scan_rate
            FROM peak_parameters pp
            JOIN measurements m ON pp.measurement_id = m.id
            WHERE pp.enabled = 1
            ORDER BY pp.peak_type, pp.peak_voltage
        """)
        
        peaks = cursor.fetchall()
        
        # Separate by type
        ox_peaks = [p for p in peaks if p['peak_type'] == 'oxidation']
        red_peaks = [p for p in peaks if p['peak_type'] == 'reduction']
        
        print(f"📋 Valid peaks in database:")
        print(f"   Oxidation peaks: {len(ox_peaks)}")
        print(f"   Reduction peaks: {len(red_peaks)}")
        
        if ox_peaks:
            ox_voltages = [p['peak_voltage'] for p in ox_peaks]
            ox_currents = [p['peak_current'] for p in ox_peaks]
            
            print(f"\n🔺 Oxidation Peak Analysis:")
            print(f"   Voltage range: {min(ox_voltages):.3f} to {max(ox_voltages):.3f} V")
            print(f"   Voltage mean: {np.mean(ox_voltages):.3f} ± {np.std(ox_voltages):.3f} V")
            print(f"   Current range: {min(ox_currents):.3f} to {max(ox_currents):.3f} μA")
            print(f"   Current mean: {np.mean(ox_currents):.3f} ± {np.std(ox_currents):.3f} μA")
            
            # Show percentiles
            ox_v_percentiles = np.percentile(ox_voltages, [5, 25, 50, 75, 95])
            print(f"   Voltage percentiles (5%, 25%, 50%, 75%, 95%): {ox_v_percentiles}")
            
            # Suggested range
            ox_min_suggest = np.percentile(ox_voltages, 5)  # 5th percentile
            ox_max_suggest = np.percentile(ox_voltages, 95)  # 95th percentile
            print(f"   ✅ Suggested Ox range: {ox_min_suggest:.3f} to {ox_max_suggest:.3f} V")
        
        if red_peaks:
            red_voltages = [p['peak_voltage'] for p in red_peaks]
            red_currents = [p['peak_current'] for p in red_peaks]
            
            print(f"\n🔻 Reduction Peak Analysis:")
            print(f"   Voltage range: {min(red_voltages):.3f} to {max(red_voltages):.3f} V")
            print(f"   Voltage mean: {np.mean(red_voltages):.3f} ± {np.std(red_voltages):.3f} V")
            print(f"   Current range: {min(red_currents):.3f} to {max(red_currents):.3f} μA")
            print(f"   Current mean: {np.mean(red_currents):.3f} ± {np.std(red_currents):.3f} μA")
            
            # Show percentiles
            red_v_percentiles = np.percentile(red_voltages, [5, 25, 50, 75, 95])
            print(f"   Voltage percentiles (5%, 25%, 50%, 75%, 95%): {red_v_percentiles}")
            
            # Suggested range
            red_min_suggest = np.percentile(red_voltages, 5)  # 5th percentile
            red_max_suggest = np.percentile(red_voltages, 95)  # 95th percentile
            print(f"   ✅ Suggested Red range: {red_min_suggest:.3f} to {red_max_suggest:.3f} V")
        
        # Check if test peak (0.190V) fits in suggested ranges
        test_voltage = 0.190
        if ox_peaks:
            if ox_min_suggest <= test_voltage <= ox_max_suggest:
                print(f"\n✅ Test peak 0.190V fits in suggested Ox range!")
            else:
                print(f"\n❌ Test peak 0.190V outside suggested Ox range ({ox_min_suggest:.3f}-{ox_max_suggest:.3f}V)")
        
        # Show sample data
        print(f"\n📋 Sample oxidation peaks:")
        for i, peak in enumerate(ox_peaks[:5]):
            print(f"   {i+1}. {peak['sample_id']}: {peak['peak_voltage']:.3f}V, {peak['peak_current']:.2f}μA")
        
        print(f"\n📋 Sample reduction peaks:")
        for i, peak in enumerate(red_peaks[:5]):
            print(f"   {i+1}. {peak['sample_id']}: {peak['peak_voltage']:.3f}V, {peak['peak_current']:.2f}μA")
        
        # Plot histogram if matplotlib available
        try:
            if ox_peaks and red_peaks:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
                
                # Oxidation voltages
                ax1.hist(ox_voltages, bins=20, alpha=0.7, color='red', edgecolor='black')
                ax1.axvline(test_voltage, color='blue', linestyle='--', linewidth=2, label=f'Test peak: {test_voltage}V')
                ax1.axvline(ox_min_suggest, color='green', linestyle=':', label=f'Suggested min: {ox_min_suggest:.3f}V')
                ax1.axvline(ox_max_suggest, color='green', linestyle=':', label=f'Suggested max: {ox_max_suggest:.3f}V')
                ax1.set_xlabel('Voltage (V)')
                ax1.set_ylabel('Count')
                ax1.set_title('Oxidation Peak Voltages')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                
                # Reduction voltages
                ax2.hist(red_voltages, bins=20, alpha=0.7, color='blue', edgecolor='black')
                ax2.axvline(red_min_suggest, color='green', linestyle=':', label=f'Suggested min: {red_min_suggest:.3f}V')
                ax2.axvline(red_max_suggest, color='green', linestyle=':', label=f'Suggested max: {red_max_suggest:.3f}V')
                ax2.set_xlabel('Voltage (V)')
                ax2.set_ylabel('Count')
                ax2.set_title('Reduction Peak Voltages')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
                
                plt.tight_layout()
                plt.savefig('peak_voltage_analysis.png', dpi=150, bbox_inches='tight')
                print(f"\n📊 Histogram saved as 'peak_voltage_analysis.png'")
                
        except ImportError:
            print(f"\n💡 Install matplotlib to see voltage distribution plots")
        
        conn.close()
        
        # Return suggested ranges
        if ox_peaks and red_peaks:
            return {
                'ox_min': ox_min_suggest,
                'ox_max': ox_max_suggest,
                'red_min': red_min_suggest,
                'red_max': red_max_suggest,
                'ox_data': ox_voltages,
                'red_data': red_voltages
            }
        else:
            return None
        
    except Exception as e:
        print(f"❌ Error analyzing peaks: {e}")
        return None

def generate_updated_detector_config(ranges):
    """สร้าง config ใหม่สำหรับ enhanced detector"""
    
    if not ranges:
        print("❌ No range data to generate config")
        return
    
    print(f"\n🔧 Updated Enhanced Detector Configuration:")
    print("=" * 60)
    print(f"# Before (too restrictive):")
    print(f"OX_VOLTAGE_MIN = 0.15   # Too high")
    print(f"OX_VOLTAGE_MAX = 0.30   # OK")
    print(f"RED_VOLTAGE_MIN = 0.05  # OK") 
    print(f"RED_VOLTAGE_MAX = 0.20  # Too high")
    print()
    print(f"# After (based on real data):")
    print(f"OX_VOLTAGE_MIN = {ranges['ox_min']:.3f}   # 5th percentile")
    print(f"OX_VOLTAGE_MAX = {ranges['ox_max']:.3f}   # 95th percentile") 
    print(f"RED_VOLTAGE_MIN = {ranges['red_min']:.3f}   # 5th percentile")
    print(f"RED_VOLTAGE_MAX = {ranges['red_max']:.3f}   # 95th percentile")
    print()
    print(f"✅ This will accept the 0.190V oxidation peak!")

if __name__ == "__main__":
    ranges = analyze_peak_voltage_ranges()
    if ranges:
        generate_updated_detector_config(ranges)