#!/usr/bin/env python3
"""
Calibration Comparison Visualization
แสดงกราฟเปรียบเทียบ STM32 ก่อน-หลัง calibrate พร้อม PalmSens reference
"""

import sqlite3
import numpy as np
import matplotlib.pyplot as plt
import json
from datetime import datetime
import os
from pathlib import Path

class CalibrationGraphComparison:
    def __init__(self):
        """Initialize the calibration graph comparison"""
        self.db_path = 'data_logs/parameter_log.db'
        
        # Set up matplotlib for better display
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = (16, 12)
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
                
                # Extract voltage and current from raw data
                if 'voltage' in raw_data and 'current' in raw_data:
                    voltage_data = raw_data['voltage']
                    current_data = raw_data['current']
                elif 'data' in raw_data:
                    # Alternative format
                    data = raw_data['data']
                    voltage_data = [point[0] for point in data]
                    current_data = [point[1] for point in data]
                elif 'cv_data' in raw_data:
                    # CV data format
                    cv_data = raw_data['cv_data']
                    if isinstance(cv_data, list) and len(cv_data) > 0:
                        # Extract voltage and current arrays
                        voltage_data = [point[0] for point in cv_data]
                        current_data = [point[1] for point in cv_data]
                    else:
                        print(f"Invalid cv_data format in measurement {measurement_id}")
                        return None
                else:
                    print(f"Unknown data format in measurement {measurement_id}")
                    print(f"Available keys: {list(raw_data.keys())}")
                    return None
                
                return {
                    'voltage': np.array(voltage_data),
                    'current': np.array(current_data),
                    'instrument_type': result[1],
                    'sample_id': result[2],
                    'scan_rate': result[3],
                    'concentration': 0.001,  # Default concentration
                    'timestamp': result[4]
                }
            return None
            
        except Exception as e:
            print(f"Error getting measurement data: {e}")
            return None

    def calibrate_stm32_data(self, voltage, current, reference_voltage=None, reference_current=None):
        """Simple calibration using linear scaling"""
        try:
            # Basic calibration parameters (can be improved with ML models)
            voltage_offset = 0.001  # 1mV offset correction
            current_gain = 1.02     # 2% current gain correction
            
            # If reference data provided, calculate better calibration
            if reference_voltage is not None and reference_current is not None:
                # Find peak positions for alignment
                stm32_peak_idx = np.argmax(np.abs(current))
                ref_peak_idx = np.argmax(np.abs(reference_current))
                
                # Calculate voltage offset from peak alignment
                voltage_offset = reference_voltage[ref_peak_idx] - voltage[stm32_peak_idx]
                
                # Calculate current scaling from peak ratios
                stm32_peak_current = current[stm32_peak_idx]
                ref_peak_current = reference_current[ref_peak_idx]
                
                if stm32_peak_current != 0:
                    current_gain = ref_peak_current / stm32_peak_current
            
            # Apply calibration
            calibrated_voltage = voltage + voltage_offset
            calibrated_current = current * current_gain
            
            return calibrated_voltage, calibrated_current, voltage_offset, current_gain
            
        except Exception as e:
            print(f"Error in calibration: {e}")
            return voltage, current, 0, 1

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

    def plot_comparison(self, stm32_id, palmsens_id):
        """Plot before/after calibration comparison"""
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
            
            # Calibrate STM32 data
            print("Performing calibration...")
            calibrated_voltage, calibrated_current, voltage_offset, current_gain = \
                self.calibrate_stm32_data(stm32_voltage, stm32_current, 
                                        palmsens_voltage, palmsens_current)
            
            # Calculate statistics
            stats = self.calculate_statistics(stm32_current, palmsens_current, calibrated_current)
            
            # Create subplot layout
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle('STM32 Calibration Comparison vs PalmSens Reference', fontsize=16, fontweight='bold')
            
            # Plot 1: STM32 Before Calibration
            ax1.plot(stm32_voltage, stm32_current * 1e6, 'r-', linewidth=2, label='STM32 Original')
            ax1.set_xlabel('Voltage (V)')
            ax1.set_ylabel('Current (μA)')
            ax1.set_title('STM32 Before Calibration (Raw Data)', fontweight='bold', color='red')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # Add peak markers
            peak_idx = np.argmax(np.abs(stm32_current))
            ax1.plot(stm32_voltage[peak_idx], stm32_current[peak_idx] * 1e6, 'ro', markersize=8)
            
            # Plot 2: STM32 After Calibration
            ax2.plot(calibrated_voltage, calibrated_current * 1e6, 'g-', linewidth=2, label='STM32 Calibrated')
            ax2.set_xlabel('Voltage (V)')
            ax2.set_ylabel('Current (μA)')
            ax2.set_title('STM32 After Calibration', fontweight='bold', color='green')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            # Add peak markers
            cal_peak_idx = np.argmax(np.abs(calibrated_current))
            ax2.plot(calibrated_voltage[cal_peak_idx], calibrated_current[cal_peak_idx] * 1e6, 'go', markersize=8)
            
            # Plot 3: PalmSens Reference
            ax3.plot(palmsens_voltage, palmsens_current * 1e6, 'b-', linewidth=2, label='PalmSens Reference')
            ax3.set_xlabel('Voltage (V)')
            ax3.set_ylabel('Current (μA)')
            ax3.set_title('PalmSens Reference (Standard)', fontweight='bold', color='blue')
            ax3.grid(True, alpha=0.3)
            ax3.legend()
            
            # Add peak markers
            ref_peak_idx = np.argmax(np.abs(palmsens_current))
            ax3.plot(palmsens_voltage[ref_peak_idx], palmsens_current[ref_peak_idx] * 1e6, 'bo', markersize=8)
            
            # Plot 4: Overlay Comparison
            ax4.plot(stm32_voltage, stm32_current * 1e6, 'r--', alpha=0.7, linewidth=1.5, label='STM32 Before')
            ax4.plot(calibrated_voltage, calibrated_current * 1e6, 'g-', linewidth=2, label='STM32 After')
            ax4.plot(palmsens_voltage, palmsens_current * 1e6, 'b-', linewidth=2, label='PalmSens Ref')
            ax4.set_xlabel('Voltage (V)')
            ax4.set_ylabel('Current (μA)')
            ax4.set_title('Overall Comparison', fontweight='bold', color='purple')
            ax4.grid(True, alpha=0.3)
            ax4.legend()
            
            # Add statistics text box
            if stats:
                stats_text = f"""Calibration Statistics:
Correlation (Before): {stats['correlation_before']:.3f}
Correlation (After): {stats['correlation_after']:.3f}
RMSE (Before): {stats['rmse_before']*1e6:.2f} μA
RMSE (After): {stats['rmse_after']*1e6:.2f} μA
R² (Before): {stats['r2_before']:.3f}
R² (After): {stats['r2_after']:.3f}

Calibration Parameters:
Voltage Offset: {voltage_offset*1000:.2f} mV
Current Gain: {current_gain:.3f}x"""
                
                # Add text box to the overlay plot
                ax4.text(0.02, 0.98, stats_text, transform=ax4.transAxes, 
                        fontsize=9, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            plt.tight_layout()
            
            # Save plot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"calibration_comparison_{stm32_id}_vs_{palmsens_id}_{timestamp}.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            print(f"\nGraph saved as: {filename}")
            
            plt.show()
            
            # Print summary
            print("\n" + "="*60)
            print("Calibration Comparison Summary")
            print("="*60)
            print(f"STM32 Measurement ID: {stm32_id}")
            print(f"PalmSens Reference ID: {palmsens_id}")
            print(f"Sample ID: {stm32_data['sample_id']}")
            print(f"Scan Rate: {stm32_data['scan_rate']} V/s")
            
            if stats:
                print(f"\nAccuracy Metrics:")
                print(f"Correlation improved from {stats['correlation_before']:.3f} to {stats['correlation_after']:.3f}")
                print(f"RMSE improved from {stats['rmse_before']*1e6:.2f} μA to {stats['rmse_after']*1e6:.2f} μA")
                print(f"R² improved from {stats['r2_before']:.3f} to {stats['r2_after']:.3f}")
                
                improvement = ((stats['correlation_after'] - stats['correlation_before']) / 
                              abs(stats['correlation_before']) * 100) if stats['correlation_before'] != 0 else 0
                print(f"\nOverall improvement: {improvement:+.1f}%")
            
            print("="*60)
            
        except Exception as e:
            print(f"Error plotting comparison: {e}")
            import traceback
            traceback.print_exc()

    def list_available_measurements(self):
        """List available measurements for comparison"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            print("\nAvailable Measurements List:")
            print("="*80)
            
            # STM32 measurements
            print("\nSTM32 Measurements:")
            cursor.execute("""
                SELECT id, sample_id, scan_rate, timestamp 
                FROM measurements 
                WHERE instrument_type = 'stm32' 
                AND id >= 60
                ORDER BY id DESC
                LIMIT 10
            """)
            stm32_results = cursor.fetchall()
            
            for row in stm32_results:
                print(f"  ID: {row[0]:3d} | Sample: {row[1]:8s} | {row[2]:6.3f} V/s | {row[3]}")
            
            print("\nPalmSens Measurements:")
            cursor.execute("""
                SELECT id, sample_id, scan_rate, timestamp 
                FROM measurements 
                WHERE instrument_type = 'palmsens' 
                AND id >= 60
                ORDER BY id DESC
                LIMIT 10
            """)
            palmsens_results = cursor.fetchall()
            
            for row in palmsens_results:
                print(f"  ID: {row[0]:3d} | Sample: {row[1]:8s} | {row[2]:6.3f} V/s | {row[3]}")
            
            conn.close()
            print("="*80)
            
        except Exception as e:
            print(f"Error listing measurements: {e}")

    def interactive_menu(self):
        """Interactive menu for calibration comparison"""
        while True:
            print("\n" + "="*60)
            print("Calibration Comparison Menu")
            print("="*60)
            print("1. Show STM32 vs PalmSens comparison graph")
            print("2. List available measurements")
            print("3. Custom comparison")
            print("4. Exit")
            print("="*60)
            
            choice = input("Select option (1-4): ").strip()
            
            if choice == '1':
                # Default comparison with recent measurements
                self.plot_comparison(67, 77)
                
            elif choice == '2':
                self.list_available_measurements()
                
            elif choice == '3':
                try:
                    stm32_id = int(input("Enter STM32 Measurement ID: "))
                    palmsens_id = int(input("Enter PalmSens Measurement ID: "))
                    self.plot_comparison(stm32_id, palmsens_id)
                except ValueError:
                    print("Please enter valid numbers")
                    
            elif choice == '4':
                print("Exiting program")
                break
                
            else:
                print("Please select option 1-4")

def main():
    """Main function"""
    print("Calibration Graph Comparison Tool")
    
    # Check if database exists
    db_path = 'data_logs/parameter_log.db'
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        print("Please run measurements first")
        return
    
    visualizer = CalibrationGraphComparison()
    
    # Show available measurements first
    visualizer.list_available_measurements()
    
    # Then show interactive menu
    visualizer.interactive_menu()

if __name__ == "__main__":
    main()