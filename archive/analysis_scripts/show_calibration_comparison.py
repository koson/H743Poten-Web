#!/usr/bin/env python3
"""
Interactive Calibration Comparison Visualization
Shows before/after calibration graphs for STM32 and PalmSens data
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import sqlite3
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.production_calibration_service import ProductionCalibrationService
from config.parameter_logging import ParameterLogger

class CalibrationVisualizer:
    def __init__(self):
        """Initialize the calibration visualizer"""
        self.calibration_service = ProductionCalibrationService()
        self.param_logger = ParameterLogger()
        
        # Set up matplotlib for better display
        plt.style.use('seaborn-v0_8')
        plt.rcParams['figure.figsize'] = (15, 10)
        plt.rcParams['font.size'] = 10
        
    def get_available_measurements(self):
        """Get available STM32 and PalmSens measurements"""
        try:
            # Get recent measurements from both instruments
            conn = sqlite3.connect('data_logs/parameter_log.db')
            cursor = conn.cursor()
            
            # Get STM32 measurements
            cursor.execute("""
                SELECT id, sample_id, scan_rate, concentration, timestamp 
                FROM measurements 
                WHERE instrument_type = 'stm32' 
                AND id >= 60
                ORDER BY id DESC
                LIMIT 10
            """)
            stm32_measurements = cursor.fetchall()
            
            # Get PalmSens measurements  
            cursor.execute("""
                SELECT id, sample_id, scan_rate, concentration, timestamp 
                FROM measurements 
                WHERE instrument_type = 'palmsens' 
                AND id >= 60
                ORDER BY id DESC
                LIMIT 10
            """)
            palmsens_measurements = cursor.fetchall()
            
            conn.close()
            
            return stm32_measurements, palmsens_measurements
            
        except Exception as e:
            print(f"❌ Error getting measurements: {e}")
            return [], []
    
    def get_measurement_data(self, measurement_id):
        """Get CV data for a specific measurement"""
        try:
            data = self.param_logger.get_measurement_data(measurement_id)
            if data and len(data) > 0:
                # Convert to numpy arrays
                voltages = np.array([point[0] for point in data])
                currents = np.array([point[1] for point in data])
                return voltages, currents
            return None, None
        except Exception as e:
            print(f"❌ Error getting data for measurement {measurement_id}: {e}")
            return None, None
    
    def calibrate_measurement(self, measurement_id, scan_rate=None, concentration=None):
        """Calibrate a measurement using the production service"""
        try:
            voltages, currents = self.get_measurement_data(measurement_id)
            if voltages is None or currents is None:
                return None, None, None
            
            # Prepare CV data for calibration
            cv_data = list(zip(voltages.tolist(), currents.tolist()))
            
            # Apply calibration
            result = self.calibration_service.calibrate_cv_curve(
                cv_data, 
                scan_rate=scan_rate, 
                concentration=concentration
            )
            
            if result['success']:
                calibrated_data = result['calibrated_data']
                cal_voltages = np.array([point[0] for point in calibrated_data])
                cal_currents = np.array([point[1] for point in calibrated_data])
                return cal_voltages, cal_currents, result['calibration_info']
            
            return None, None, None
            
        except Exception as e:
            print(f"❌ Error calibrating measurement {measurement_id}: {e}")
            return None, None, None
    
    def plot_comparison(self, stm32_id, scan_rate=None, concentration=None):
        """Create comparison plot for a single STM32 measurement"""
        print(f"\n🔍 Creating comparison plot for STM32 measurement {stm32_id}")
        
        # Get original data
        voltages, currents = self.get_measurement_data(stm32_id)
        if voltages is None:
            print(f"❌ No data found for measurement {stm32_id}")
            return
        
        # Get calibrated data
        cal_voltages, cal_currents, cal_info = self.calibrate_measurement(
            stm32_id, scan_rate, concentration
        )
        
        if cal_voltages is None:
            print(f"❌ Calibration failed for measurement {stm32_id}")
            return
        
        # Create comparison plot
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
        
        # Plot 1: Original STM32 data
        ax1.plot(voltages, currents * 1e6, 'b-', linewidth=2, label='STM32 Original')
        ax1.set_xlabel('Voltage (V)')
        ax1.set_ylabel('Current (µA)')
        ax1.set_title(f'STM32 Original Data\nMeasurement ID: {stm32_id}')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Add statistics
        current_range = (np.min(currents) * 1e6, np.max(currents) * 1e6)
        ax1.text(0.02, 0.98, f'Range: {current_range[0]:.2f} to {current_range[1]:.2f} µA', 
                transform=ax1.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
        
        # Plot 2: Calibrated data
        ax2.plot(cal_voltages, cal_currents, 'r-', linewidth=2, label='Calibrated to PalmSens')
        ax2.set_xlabel('Voltage (V)')
        ax2.set_ylabel('Current (µA)')
        ax2.set_title(f'Calibrated Data\nGain: {cal_info["gain_factor"]:.0f}')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Add calibration info
        cal_range = (np.min(cal_currents), np.max(cal_currents))
        info_text = f'Range: {cal_range[0]:.2f} to {cal_range[1]:.2f} µA\n'
        info_text += f'R²: {cal_info["r_squared"]:.3f}\n'
        info_text += f'Method: {cal_info["method"]}\n'
        info_text += f'Confidence: {cal_info["confidence"]}'
        
        ax2.text(0.02, 0.98, info_text, 
                transform=ax2.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.7))
        
        # Plot 3: Overlay comparison
        ax3.plot(voltages, currents * 1e6, 'b-', linewidth=2, alpha=0.7, label='STM32 Original')
        ax3.plot(cal_voltages, cal_currents, 'r-', linewidth=2, alpha=0.7, label='Calibrated')
        ax3.set_xlabel('Voltage (V)')
        ax3.set_ylabel('Current (µA)')
        ax3.set_title('Before vs After Calibration')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        
        # Add gain factor annotation
        gain_factor = cal_info["gain_factor"]
        ax3.text(0.02, 0.98, f'Gain Factor: {gain_factor:.0f}×', 
                transform=ax3.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
        
        plt.tight_layout()
        
        # Add main title
        fig.suptitle(f'Calibration Comparison - STM32 ID {stm32_id}', 
                    fontsize=16, fontweight='bold', y=1.02)
        
        plt.show()
        
        # Print summary
        print(f"\n📊 Calibration Summary:")
        print(f"   • Original current range: {current_range[0]:.3f} to {current_range[1]:.3f} µA")
        print(f"   • Calibrated current range: {cal_range[0]:.3f} to {cal_range[1]:.3f} µA")
        print(f"   • Gain factor: {gain_factor:.0f}")
        print(f"   • R² value: {cal_info['r_squared']:.3f}")
        print(f"   • Confidence: {cal_info['confidence']}")
        
    def plot_instrument_comparison(self, stm32_id, palmsens_id):
        """Compare STM32 calibrated data with actual PalmSens data"""
        print(f"\n🔍 Comparing STM32 {stm32_id} (calibrated) vs PalmSens {palmsens_id}")
        
        # Get STM32 data and calibrate it
        stm32_v, stm32_i = self.get_measurement_data(stm32_id)
        if stm32_v is None:
            print(f"❌ No STM32 data found for measurement {stm32_id}")
            return
        
        # Get PalmSens reference data
        palmsens_v, palmsens_i = self.get_measurement_data(palmsens_id)
        if palmsens_v is None:
            print(f"❌ No PalmSens data found for measurement {palmsens_id}")
            return
        
        # Calibrate STM32 data
        cal_v, cal_i, cal_info = self.calibrate_measurement(stm32_id)
        if cal_v is None:
            print(f"❌ Calibration failed for STM32 measurement {stm32_id}")
            return
        
        # Create comparison plot
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Plot 1: STM32 Original
        ax1.plot(stm32_v, stm32_i * 1e6, 'b-', linewidth=2)
        ax1.set_xlabel('Voltage (V)')
        ax1.set_ylabel('Current (µA)')
        ax1.set_title(f'STM32 Original (ID: {stm32_id})')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: STM32 Calibrated
        ax2.plot(cal_v, cal_i, 'r-', linewidth=2)
        ax2.set_xlabel('Voltage (V)')
        ax2.set_ylabel('Current (µA)')
        ax2.set_title(f'STM32 Calibrated (Gain: {cal_info["gain_factor"]:.0f})')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: PalmSens Reference
        ax3.plot(palmsens_v, palmsens_i, 'g-', linewidth=2)
        ax3.set_xlabel('Voltage (V)')
        ax3.set_ylabel('Current (µA)')
        ax3.set_title(f'PalmSens Reference (ID: {palmsens_id})')
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Overlay Comparison
        ax4.plot(cal_v, cal_i, 'r-', linewidth=2, alpha=0.8, label='STM32 Calibrated')
        ax4.plot(palmsens_v, palmsens_i, 'g-', linewidth=2, alpha=0.8, label='PalmSens Reference')
        ax4.set_xlabel('Voltage (V)')
        ax4.set_ylabel('Current (µA)')
        ax4.set_title('Calibrated STM32 vs PalmSens')
        ax4.grid(True, alpha=0.3)
        ax4.legend()
        
        # Calculate correlation if possible
        try:
            # Interpolate to same voltage points for comparison
            common_v = np.linspace(max(np.min(cal_v), np.min(palmsens_v)), 
                                 min(np.max(cal_v), np.max(palmsens_v)), 100)
            cal_interp = np.interp(common_v, cal_v, cal_i)
            palm_interp = np.interp(common_v, palmsens_v, palmsens_i)
            
            correlation = np.corrcoef(cal_interp, palm_interp)[0, 1]
            rmse = np.sqrt(np.mean((cal_interp - palm_interp)**2))
            
            ax4.text(0.02, 0.98, f'Correlation: {correlation:.3f}\nRMSE: {rmse:.2f} µA', 
                    transform=ax4.transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
            
            print(f"\n📊 Comparison Statistics:")
            print(f"   • Correlation: {correlation:.3f}")
            print(f"   • RMSE: {rmse:.2f} µA")
            
        except Exception as e:
            print(f"Warning: Could not calculate comparison statistics: {e}")
        
        plt.tight_layout()
        fig.suptitle(f'Instrument Comparison - STM32 {stm32_id} vs PalmSens {palmsens_id}', 
                    fontsize=16, fontweight='bold', y=1.02)
        plt.show()
    
    def interactive_menu(self):
        """Interactive menu for selecting measurements to compare"""
        print("🔬 Calibration Comparison Visualizer")
        print("=" * 50)
        
        # Get available measurements
        stm32_measurements, palmsens_measurements = self.get_available_measurements()
        
        if not stm32_measurements:
            print("❌ No STM32 measurements found!")
            return
        
        while True:
            print("\n📋 Available Options:")
            print("1. Show single measurement calibration (before/after)")
            print("2. Compare STM32 calibrated vs PalmSens reference")
            print("3. List available measurements")
            print("4. Exit")
            
            choice = input("\n🎯 Select option (1-4): ").strip()
            
            if choice == '1':
                self._show_single_calibration_menu(stm32_measurements)
            elif choice == '2':
                self._show_comparison_menu(stm32_measurements, palmsens_measurements)
            elif choice == '3':
                self._list_measurements(stm32_measurements, palmsens_measurements)
            elif choice == '4':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option. Please try again.")
    
    def _show_single_calibration_menu(self, stm32_measurements):
        """Show menu for single measurement calibration"""
        print("\n📊 STM32 Measurements Available for Calibration:")
        for i, (id, sample_id, scan_rate, concentration, timestamp) in enumerate(stm32_measurements):
            print(f"   {i+1}. ID {id}: {sample_id} | {scan_rate}mV/s | {concentration}mM")
        
        try:
            choice = int(input("\n🎯 Select measurement (1-{}): ".format(len(stm32_measurements)))) - 1
            if 0 <= choice < len(stm32_measurements):
                measurement = stm32_measurements[choice]
                measurement_id, sample_id, scan_rate, concentration, timestamp = measurement
                print(f"\n🔄 Creating calibration comparison for {sample_id} (ID: {measurement_id})")
                self.plot_comparison(measurement_id, scan_rate, concentration)
            else:
                print("❌ Invalid selection!")
        except ValueError:
            print("❌ Please enter a valid number!")
    
    def _show_comparison_menu(self, stm32_measurements, palmsens_measurements):
        """Show menu for instrument comparison"""
        if not palmsens_measurements:
            print("❌ No PalmSens measurements available for comparison!")
            return
        
        print("\n📊 STM32 Measurements:")
        for i, (id, sample_id, scan_rate, concentration, timestamp) in enumerate(stm32_measurements):
            print(f"   {i+1}. ID {id}: {sample_id} | {scan_rate}mV/s | {concentration}mM")
        
        print("\n📊 PalmSens Measurements:")
        for i, (id, sample_id, scan_rate, concentration, timestamp) in enumerate(palmsens_measurements):
            print(f"   {i+1}. ID {id}: {sample_id} | {scan_rate}mV/s | {concentration}mM")
        
        try:
            stm32_choice = int(input(f"\n🎯 Select STM32 measurement (1-{len(stm32_measurements)}): ")) - 1
            palmsens_choice = int(input(f"🎯 Select PalmSens measurement (1-{len(palmsens_measurements)}): ")) - 1
            
            if (0 <= stm32_choice < len(stm32_measurements) and 
                0 <= palmsens_choice < len(palmsens_measurements)):
                
                stm32_id = stm32_measurements[stm32_choice][0]
                palmsens_id = palmsens_measurements[palmsens_choice][0]
                
                print(f"\n🔄 Comparing STM32 ID {stm32_id} vs PalmSens ID {palmsens_id}")
                self.plot_instrument_comparison(stm32_id, palmsens_id)
            else:
                print("❌ Invalid selection!")
        except ValueError:
            print("❌ Please enter valid numbers!")
    
    def _list_measurements(self, stm32_measurements, palmsens_measurements):
        """List all available measurements"""
        print("\n📊 STM32 Measurements:")
        if stm32_measurements:
            for id, sample_id, scan_rate, concentration, timestamp in stm32_measurements:
                print(f"   • ID {id}: {sample_id} | {scan_rate}mV/s | {concentration}mM | {timestamp}")
        else:
            print("   No STM32 measurements found")
        
        print("\n📊 PalmSens Measurements:")
        if palmsens_measurements:
            for id, sample_id, scan_rate, concentration, timestamp in palmsens_measurements:
                print(f"   • ID {id}: {sample_id} | {scan_rate}mV/s | {concentration}mM | {timestamp}")
        else:
            print("   No PalmSens measurements found")

def main():
    """Main function"""
    try:
        visualizer = CalibrationVisualizer()
        
        # Quick demo with specific measurements
        print("🚀 Quick Demo: Showing calibration for measurement ID 67")
        visualizer.plot_comparison(67, 100.0, 5.0)
        
        # Interactive menu
        print("\n" + "="*50)
        visualizer.interactive_menu()
        
    except KeyboardInterrupt:
        print("\n👋 Program interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()