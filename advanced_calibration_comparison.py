#!/usr/bin/env python3
"""
Advanced Calibration Techniques for STM32 vs PalmSens
Technique 1: Voltage + Current calibration (existing)
Technique 2: Current-only calibration (voltage preserved)
"""

import sqlite3
import numpy as np
import matplotlib.pyplot as plt
import json
from datetime import datetime
import os
from pathlib import Path

class AdvancedCalibrationComparison:
    def __init__(self):
        """Initialize the advanced calibration comparison"""
        self.db_path = 'data_logs/parameter_log.db'
        
        # Set up matplotlib for better display
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = (20, 15)
        plt.rcParams['font.size'] = 10
        
    def get_measurement_data(self, measurement_id):
        """Get CV data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT raw_data_json, instrument_type, 
                       sample_id, scan_rate, timestamp
                FROM measurements 
                WHERE id = ?
            """, (measurement_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                raw_data = json.loads(result[0])
                
                if 'cv_data' in raw_data:
                    cv_data = raw_data['cv_data']
                    if isinstance(cv_data, list) and len(cv_data) > 0:
                        voltage_data = [point[0] for point in cv_data]
                        current_data = [point[1] for point in cv_data]
                    else:
                        return None
                else:
                    return None
                
                return {
                    'voltage': np.array(voltage_data),
                    'current': np.array(current_data),
                    'instrument_type': result[1],
                    'sample_id': result[2],
                    'scan_rate': result[3],
                    'concentration': 0.001,
                    'timestamp': result[4]
                }
            return None
            
        except Exception as e:
            print(f"Error getting measurement data: {e}")
            return None

    def find_peaks(self, voltage, current):
        """Find oxidation and reduction peaks"""
        try:
            # Find oxidation peak (positive current)
            pos_current = current[current > 0]
            if len(pos_current) > 0:
                pos_idx = np.where(current > 0)[0]
                ox_peak_idx = pos_idx[np.argmax(pos_current)]
                ox_peak_v = voltage[ox_peak_idx]
                ox_peak_i = current[ox_peak_idx]
            else:
                ox_peak_v, ox_peak_i = 0, 0
                ox_peak_idx = 0
            
            # Find reduction peak (negative current)
            neg_current = current[current < 0]
            if len(neg_current) > 0:
                neg_idx = np.where(current < 0)[0]
                red_peak_idx = neg_idx[np.argmin(neg_current)]  # Most negative
                red_peak_v = voltage[red_peak_idx]
                red_peak_i = current[red_peak_idx]
            else:
                red_peak_v, red_peak_i = 0, 0
                red_peak_idx = 0
            
            return {
                'oxidation': {'voltage': ox_peak_v, 'current': ox_peak_i, 'index': ox_peak_idx},
                'reduction': {'voltage': red_peak_v, 'current': red_peak_i, 'index': red_peak_idx}
            }
            
        except Exception as e:
            print(f"Error finding peaks: {e}")
            return None

    def calibrate_technique1_voltage_current(self, stm32_voltage, stm32_current, ref_voltage, ref_current):
        """Technique 1: Calibrate both voltage and current (existing method)"""
        try:
            # Find peaks for alignment
            stm32_peaks = self.find_peaks(stm32_voltage, stm32_current)
            ref_peaks = self.find_peaks(ref_voltage, ref_current)
            
            if not stm32_peaks or not ref_peaks:
                # Fallback to simple calibration
                voltage_offset = 0.001
                current_gain = 1.02
            else:
                # Calculate voltage offset from peak alignment (using reduction peak)
                voltage_offset = ref_peaks['reduction']['voltage'] - stm32_peaks['reduction']['voltage']
                
                # Calculate current scaling from peak ratios
                stm32_peak_current = stm32_peaks['reduction']['current']
                ref_peak_current = ref_peaks['reduction']['current']
                
                if stm32_peak_current != 0:
                    current_gain = ref_peak_current / stm32_peak_current
                else:
                    current_gain = 1.02
            
            # Apply calibration
            calibrated_voltage = stm32_voltage + voltage_offset
            calibrated_current = stm32_current * current_gain
            
            return calibrated_voltage, calibrated_current, voltage_offset, current_gain
            
        except Exception as e:
            print(f"Error in technique 1 calibration: {e}")
            return stm32_voltage, stm32_current, 0, 1

    def calibrate_technique2_current_only(self, stm32_voltage, stm32_current, ref_voltage, ref_current):
        """Technique 2: Calibrate current only, preserve voltage"""
        try:
            # Find peaks for current scaling
            stm32_peaks = self.find_peaks(stm32_voltage, stm32_current)
            ref_peaks = self.find_peaks(ref_voltage, ref_current)
            
            if not stm32_peaks or not ref_peaks:
                # Fallback to simple current scaling
                current_offset = 0
                current_gain = 1.02
            else:
                # Calculate current offset and gain from both peaks
                stm32_ox_current = stm32_peaks['oxidation']['current']
                stm32_red_current = stm32_peaks['reduction']['current']
                ref_ox_current = ref_peaks['oxidation']['current']
                ref_red_current = ref_peaks['reduction']['current']
                
                # Calculate gain from reduction peak (usually more prominent)
                if stm32_red_current != 0:
                    current_gain = ref_red_current / stm32_red_current
                else:
                    current_gain = 1.02
                
                # Calculate offset to match oxidation peak after scaling
                scaled_stm32_ox = stm32_ox_current * current_gain
                current_offset = ref_ox_current - scaled_stm32_ox
            
            # Apply current-only calibration (voltage unchanged)
            calibrated_voltage = stm32_voltage.copy()  # Keep original voltage
            calibrated_current = (stm32_current * current_gain) + current_offset
            
            return calibrated_voltage, calibrated_current, current_offset, current_gain
            
        except Exception as e:
            print(f"Error in technique 2 calibration: {e}")
            return stm32_voltage, stm32_current, 0, 1

    def calculate_statistics(self, stm32_current, reference_current, calibrated_current):
        """Calculate comparison statistics"""
        try:
            # Ensure same length arrays
            min_len = min(len(stm32_current), len(reference_current), len(calibrated_current))
            stm32_current = stm32_current[:min_len]
            reference_current = reference_current[:min_len]
            calibrated_current = calibrated_current[:min_len]
            
            # Calculate correlation coefficients
            corr_before = np.corrcoef(stm32_current, reference_current)[0, 1]
            corr_after = np.corrcoef(calibrated_current, reference_current)[0, 1]
            
            # Calculate RMSE
            rmse_before = np.sqrt(np.mean((stm32_current - reference_current)**2))
            rmse_after = np.sqrt(np.mean((calibrated_current - reference_current)**2))
            
            # Calculate R²
            ss_res_before = np.sum((stm32_current - reference_current)**2)
            ss_tot = np.sum((reference_current - np.mean(reference_current))**2)
            r2_before = 1 - (ss_res_before / ss_tot) if ss_tot != 0 else 0
            
            ss_res_after = np.sum((calibrated_current - reference_current)**2)
            r2_after = 1 - (ss_res_after / ss_tot) if ss_tot != 0 else 0
            
            return {
                'correlation_before': corr_before,
                'correlation_after': corr_after,
                'rmse_before': rmse_before,
                'rmse_after': rmse_after,
                'r2_before': r2_before,
                'r2_after': r2_after
            }
            
        except Exception as e:
            print(f"Error calculating statistics: {e}")
            return None

    def plot_advanced_comparison(self, stm32_id, palmsens_id):
        """Plot comparison between both calibration techniques"""
        try:
            # Get data
            print(f"Loading STM32 measurement ID: {stm32_id}")
            stm32_data = self.get_measurement_data(stm32_id)
            
            print(f"Loading PalmSens measurement ID: {palmsens_id}")
            palmsens_data = self.get_measurement_data(palmsens_id)
            
            if not stm32_data or not palmsens_data:
                print("Error: Could not load measurement data")
                return
            
            # Extract data
            stm32_voltage = stm32_data['voltage']
            stm32_current = stm32_data['current']
            palmsens_voltage = palmsens_data['voltage']
            palmsens_current = palmsens_data['current']
            
            # Apply both calibration techniques
            print("Applying Technique 1: Voltage + Current calibration...")
            cal1_voltage, cal1_current, voltage_offset, current_gain1 = \
                self.calibrate_technique1_voltage_current(stm32_voltage, stm32_current, 
                                                        palmsens_voltage, palmsens_current)
            
            print("Applying Technique 2: Current-only calibration...")
            cal2_voltage, cal2_current, current_offset, current_gain2 = \
                self.calibrate_technique2_current_only(stm32_voltage, stm32_current, 
                                                     palmsens_voltage, palmsens_current)
            
            # Calculate statistics for both techniques
            stats1 = self.calculate_statistics(stm32_current, palmsens_current, cal1_current)
            stats2 = self.calculate_statistics(stm32_current, palmsens_current, cal2_current)
            
            # Find peaks for analysis
            stm32_peaks = self.find_peaks(stm32_voltage, stm32_current)
            palmsens_peaks = self.find_peaks(palmsens_voltage, palmsens_current)
            cal1_peaks = self.find_peaks(cal1_voltage, cal1_current)
            cal2_peaks = self.find_peaks(cal2_voltage, cal2_current)
            
            # Create subplot layout (2x3)
            fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3, figsize=(20, 15))
            fig.suptitle('Advanced Calibration Techniques Comparison', fontsize=16, fontweight='bold')
            
            # Plot 1: Original STM32
            ax1.plot(stm32_voltage, stm32_current * 1e6, 'r-', linewidth=2, label='STM32 Original')
            if stm32_peaks:
                ax1.plot(stm32_peaks['oxidation']['voltage'], stm32_peaks['oxidation']['current'] * 1e6, 'ro', markersize=8, label='Ox Peak')
                ax1.plot(stm32_peaks['reduction']['voltage'], stm32_peaks['reduction']['current'] * 1e6, 'rs', markersize=8, label='Red Peak')
            ax1.set_xlabel('Voltage (V)')
            ax1.set_ylabel('Current (μA)')
            ax1.set_title('STM32 Original Data', fontweight='bold', color='red')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # Plot 2: PalmSens Reference
            ax2.plot(palmsens_voltage, palmsens_current * 1e6, 'b-', linewidth=2, label='PalmSens Reference')
            if palmsens_peaks:
                ax2.plot(palmsens_peaks['oxidation']['voltage'], palmsens_peaks['oxidation']['current'] * 1e6, 'bo', markersize=8, label='Ox Peak')
                ax2.plot(palmsens_peaks['reduction']['voltage'], palmsens_peaks['reduction']['current'] * 1e6, 'bs', markersize=8, label='Red Peak')
            ax2.set_xlabel('Voltage (V)')
            ax2.set_ylabel('Current (μA)')
            ax2.set_title('PalmSens Reference', fontweight='bold', color='blue')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            # Plot 3: Technique 1 (Voltage + Current)
            ax3.plot(cal1_voltage, cal1_current * 1e6, 'g-', linewidth=2, label='Technique 1')
            if cal1_peaks:
                ax3.plot(cal1_peaks['oxidation']['voltage'], cal1_peaks['oxidation']['current'] * 1e6, 'go', markersize=8, label='Ox Peak')
                ax3.plot(cal1_peaks['reduction']['voltage'], cal1_peaks['reduction']['current'] * 1e6, 'gs', markersize=8, label='Red Peak')
            ax3.set_xlabel('Voltage (V)')
            ax3.set_ylabel('Current (μA)')
            ax3.set_title('Technique 1: Voltage + Current Cal', fontweight='bold', color='green')
            ax3.grid(True, alpha=0.3)
            ax3.legend()
            
            # Plot 4: Technique 2 (Current Only)
            ax4.plot(cal2_voltage, cal2_current * 1e6, 'm-', linewidth=2, label='Technique 2')
            if cal2_peaks:
                ax4.plot(cal2_peaks['oxidation']['voltage'], cal2_peaks['oxidation']['current'] * 1e6, 'mo', markersize=8, label='Ox Peak')
                ax4.plot(cal2_peaks['reduction']['voltage'], cal2_peaks['reduction']['current'] * 1e6, 'ms', markersize=8, label='Red Peak')
            ax4.set_xlabel('Voltage (V)')
            ax4.set_ylabel('Current (μA)')
            ax4.set_title('Technique 2: Current-Only Cal', fontweight='bold', color='magenta')
            ax4.grid(True, alpha=0.3)
            ax4.legend()
            
            # Plot 5: Overlay Comparison
            ax5.plot(stm32_voltage, stm32_current * 1e6, 'r--', alpha=0.7, linewidth=1.5, label='STM32 Original')
            ax5.plot(cal1_voltage, cal1_current * 1e6, 'g-', linewidth=2, label='Technique 1')
            ax5.plot(cal2_voltage, cal2_current * 1e6, 'm-', linewidth=2, label='Technique 2')
            ax5.plot(palmsens_voltage, palmsens_current * 1e6, 'b-', linewidth=2, alpha=0.8, label='PalmSens Ref')
            ax5.set_xlabel('Voltage (V)')
            ax5.set_ylabel('Current (μA)')
            ax5.set_title('Techniques Comparison', fontweight='bold', color='purple')
            ax5.grid(True, alpha=0.3)
            ax5.legend()
            
            # Plot 6: Statistics Comparison
            ax6.axis('off')
            if stats1 and stats2:
                stats_text = f"""CALIBRATION TECHNIQUES COMPARISON

Technique 1 (Voltage + Current):
  Voltage Offset: {voltage_offset*1000:.2f} mV
  Current Gain: {current_gain1:.3f}x
  Correlation: {stats1['correlation_before']:.3f} → {stats1['correlation_after']:.3f}
  RMSE: {stats1['rmse_before']*1e6:.0f} → {stats1['rmse_after']*1e6:.0f} μA
  R²: {stats1['r2_before']:.3f} → {stats1['r2_after']:.3f}

Technique 2 (Current Only):
  Voltage: PRESERVED (no change)
  Current Offset: {current_offset*1e6:.2f} μA
  Current Gain: {current_gain2:.3f}x
  Correlation: {stats2['correlation_before']:.3f} → {stats2['correlation_after']:.3f}
  RMSE: {stats2['rmse_before']*1e6:.0f} → {stats2['rmse_after']*1e6:.0f} μA
  R²: {stats2['r2_before']:.3f} → {stats2['r2_after']:.3f}

IMPROVEMENTS:
Technique 1 R² improvement: {((stats1['r2_after']-stats1['r2_before'])/abs(stats1['r2_before'])*100):+.1f}%
Technique 2 R² improvement: {((stats2['r2_after']-stats2['r2_before'])/abs(stats2['r2_before'])*100):+.1f}%
"""
                
                ax6.text(0.05, 0.95, stats_text, transform=ax6.transAxes, 
                        fontsize=10, verticalalignment='top', fontfamily='monospace',
                        bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
            
            plt.tight_layout()
            
            # Save plot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"advanced_calibration_comparison_{stm32_id}_vs_{palmsens_id}_{timestamp}.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            print(f"\nGraph saved as: {filename}")
            
            plt.show()
            
            # Print detailed comparison
            self.print_detailed_comparison(stm32_data, palmsens_data, stats1, stats2, 
                                         voltage_offset, current_gain1, current_offset, current_gain2,
                                         stm32_peaks, palmsens_peaks, cal1_peaks, cal2_peaks)
            
        except Exception as e:
            print(f"Error plotting advanced comparison: {e}")
            import traceback
            traceback.print_exc()

    def print_detailed_comparison(self, stm32_data, palmsens_data, stats1, stats2, 
                                voltage_offset, current_gain1, current_offset, current_gain2,
                                stm32_peaks, palmsens_peaks, cal1_peaks, cal2_peaks):
        """Print detailed comparison results"""
        
        print("\n" + "="*80)
        print("ADVANCED CALIBRATION TECHNIQUES COMPARISON")
        print("="*80)
        
        print(f"STM32 Sample: {stm32_data['sample_id']}")
        print(f"PalmSens Sample: {palmsens_data['sample_id']}")
        print(f"Scan Rate: {stm32_data['scan_rate']} V/s")
        
        if stm32_peaks and palmsens_peaks:
            print(f"\nPEAK ANALYSIS:")
            print("-" * 50)
            print(f"STM32 Original:")
            print(f"  Oxidation Peak: {stm32_peaks['oxidation']['voltage']:.3f} V, {stm32_peaks['oxidation']['current']*1e6:.1f} μA")
            print(f"  Reduction Peak: {stm32_peaks['reduction']['voltage']:.3f} V, {stm32_peaks['reduction']['current']*1e6:.1f} μA")
            
            print(f"\nPalmSens Reference:")
            print(f"  Oxidation Peak: {palmsens_peaks['oxidation']['voltage']:.3f} V, {palmsens_peaks['oxidation']['current']*1e6:.1f} μA")
            print(f"  Reduction Peak: {palmsens_peaks['reduction']['voltage']:.3f} V, {palmsens_peaks['reduction']['current']*1e6:.1f} μA")
            
            if cal1_peaks:
                print(f"\nTechnique 1 Result:")
                print(f"  Oxidation Peak: {cal1_peaks['oxidation']['voltage']:.3f} V, {cal1_peaks['oxidation']['current']*1e6:.1f} μA")
                print(f"  Reduction Peak: {cal1_peaks['reduction']['voltage']:.3f} V, {cal1_peaks['reduction']['current']*1e6:.1f} μA")
            
            if cal2_peaks:
                print(f"\nTechnique 2 Result:")
                print(f"  Oxidation Peak: {cal2_peaks['oxidation']['voltage']:.3f} V, {cal2_peaks['oxidation']['current']*1e6:.1f} μA")
                print(f"  Reduction Peak: {cal2_peaks['reduction']['voltage']:.3f} V, {cal2_peaks['reduction']['current']*1e6:.1f} μA")
        
        print(f"\nCALIBRATION PARAMETERS:")
        print("-" * 50)
        print(f"Technique 1 (Voltage + Current):")
        print(f"  Voltage Offset: {voltage_offset*1000:+.2f} mV")
        print(f"  Current Gain: {current_gain1:.3f}x")
        
        print(f"\nTechnique 2 (Current Only):")
        print(f"  Voltage: PRESERVED")
        print(f"  Current Offset: {current_offset*1e6:+.2f} μA")
        print(f"  Current Gain: {current_gain2:.3f}x")
        
        if stats1 and stats2:
            print(f"\nSTATISTICAL COMPARISON:")
            print("-" * 50)
            print(f"Technique 1 Results:")
            print(f"  R² improvement: {stats1['r2_before']:.3f} → {stats1['r2_after']:.3f} ({((stats1['r2_after']-stats1['r2_before'])/abs(stats1['r2_before'])*100):+.1f}%)")
            print(f"  RMSE improvement: {stats1['rmse_before']*1e6:.0f} → {stats1['rmse_after']*1e6:.0f} μA ({((stats1['rmse_before']-stats1['rmse_after'])/stats1['rmse_before']*100):+.1f}%)")
            print(f"  Correlation: {stats1['correlation_before']:.3f} → {stats1['correlation_after']:.3f}")
            
            print(f"\nTechnique 2 Results:")
            print(f"  R² improvement: {stats2['r2_before']:.3f} → {stats2['r2_after']:.3f} ({((stats2['r2_after']-stats2['r2_before'])/abs(stats2['r2_before'])*100):+.1f}%)")
            print(f"  RMSE improvement: {stats2['rmse_before']*1e6:.0f} → {stats2['rmse_after']*1e6:.0f} μA ({((stats2['rmse_before']-stats2['rmse_after'])/stats2['rmse_before']*100):+.1f}%)")
            print(f"  Correlation: {stats2['correlation_before']:.3f} → {stats2['correlation_after']:.3f}")
            
            print(f"\nRECOMMENDATION:")
            print("-" * 50)
            if stats1['r2_after'] > stats2['r2_after']:
                print("✅ Technique 1 (Voltage + Current) shows better overall performance")
            elif stats2['r2_after'] > stats1['r2_after']:
                print("✅ Technique 2 (Current Only) shows better overall performance")
            else:
                print("⚖️  Both techniques show similar performance")
            
            print(f"Choose Technique 2 if voltage preservation is critical for your application")
        
        print("="*80)

def main():
    """Main function"""
    print("Advanced Calibration Techniques Comparison")
    print("="*50)
    
    # Check if database exists
    db_path = 'data_logs/parameter_log.db'
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        print("Please run measurements first")
        return
    
    visualizer = AdvancedCalibrationComparison()
    
    # Run comparison with both techniques
    print("Comparing calibration techniques for STM32 ID 75 vs PalmSens ID 90")
    visualizer.plot_advanced_comparison(75, 90)

if __name__ == "__main__":
    main()