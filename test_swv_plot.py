#!/usr/bin/env python3
"""
SWV Real-time Plotting Engine
============================
Square Wave Voltammetry with Real-time Matplotlib Plotting
"""

import os
import sys
import time
import serial
import threading
import numpy as np
import matplotlib
matplotlib.use('TkAgg')  # Use tkinter backend for GUI compatibility
import matplotlib.pyplot as plt

def find_stm32_port():
    """Find the STM32 port automatically"""
    possible_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2']
    
    for port in possible_ports:
        if os.path.exists(port):
            print(f"✓ Found STM32 at {port}")
            return port
    
    print("✗ No STM32 port found")
    return None

def get_swv_parameters_from_env():
    """Get SWV parameters from environment variables with defaults"""
    params = {
        'start_voltage': float(os.environ.get('SWV_START_V', -0.5)),
        'end_voltage': float(os.environ.get('SWV_END_V', 0.5)),
        'step_voltage': float(os.environ.get('SWV_STEP_V', 0.005)),
        'sw_amplitude': float(os.environ.get('SWV_AMP', 0.025)),
        'sw_frequency': float(os.environ.get('SWV_FREQ', 50)),
        'enable_precon': int(os.environ.get('SWV_ENABLE_PRECON', 1)),
        'precon_pot1': float(os.environ.get('SWV_PRECON_POT1', -1.9)),
        'precon_pot2': float(os.environ.get('SWV_PRECON_POT2', -0.5)),
        'precon_time': int(float(os.environ.get('SWV_PRECON_TIME', 10))),
        'equil_time': int(float(os.environ.get('SWV_EQUIL_TIME', 10)))
    }
    return params

class SWVPlotter:
    def __init__(self):
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        self.fig.suptitle('SWV Real-time Analysis', fontsize=16, fontweight='bold')
        
        # SWV Net Current vs Potential
        self.ax1.set_title('SWV Net Current vs Potential')
        self.ax1.set_xlabel('Potential (V)')
        self.ax1.set_ylabel('SWV Net Current (µA)')
        self.ax1.grid(True, alpha=0.3)
        
        # Forward and Reverse Currents vs Time
        self.ax2.set_title('Forward & Reverse Currents vs Time')
        self.ax2.set_xlabel('Time (s)')
        self.ax2.set_ylabel('Current (µA)')
        self.ax2.grid(True, alpha=0.3)
        
        # Initialize data arrays
        self.potentials = []
        self.net_currents = []
        self.times = []
        self.forward_currents = []
        self.reverse_currents = []
        self.step_numbers = []  # Add step numbers for x-axis
        
        # Initialize plot lines
        self.line1, = self.ax1.plot([], [], 'r-', linewidth=2, label='SWV Net Current')
        self.line2, = self.ax2.plot([], [], 'g-', linewidth=1, label='Forward Current', alpha=0.7)
        self.line3, = self.ax2.plot([], [], 'b-', linewidth=1, label='Reverse Current', alpha=0.7)
        
        self.ax1.legend()
        self.ax2.legend()
        
        plt.tight_layout()
        
    def update_plot(self):
        """Update the plot with new data"""
        if len(self.potentials) > 0:
            # Sort data by potential for proper plotting
            if len(self.potentials) > 1:
                # Create pairs and sort by potential
                data_pairs = list(zip(self.potentials, self.net_currents))
                data_pairs.sort(key=lambda x: x[0])  # Sort by potential
                sorted_potentials, sorted_currents = zip(*data_pairs)
                
                # Update SWV net current plot with sorted data
                self.line1.set_data(sorted_potentials, sorted_currents)
            else:
                self.line1.set_data(self.potentials, self.net_currents)
            
            self.ax1.relim()
            self.ax1.autoscale_view()
            
            # Update forward/reverse current plots
            if len(self.times) > 0:
                self.line2.set_data(self.times, self.forward_currents)
                self.line3.set_data(self.times, self.reverse_currents)
                self.ax2.relim()
                self.ax2.autoscale_view()
        
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

def run_swv_measurement():
    """Run SWV measurement with real-time plotting"""
    port = find_stm32_port()
    if not port:
        return
    
    params = get_swv_parameters_from_env()
    
    print("⚡ SWV Real-time Measurement")
    print("=" * 50)
    print(f"📊 SWV Parameters:")
    print(f"   Start Voltage: {params['start_voltage']} V")
    print(f"   End Voltage: {params['end_voltage']} V")
    print(f"   Step Voltage: {params['step_voltage']} V")
    print(f"   SW Amplitude: {params['sw_amplitude']} V")
    print(f"   SW Frequency: {params['sw_frequency']} Hz")
    print(f"   Enable Precondition: {params['enable_precon']}")
    print(f"   Precon Pot1: {params['precon_pot1']} V")
    print(f"   Precon Pot2: {params['precon_pot2']} V")
    print(f"   Precon Time: {params['precon_time']} s")
    print(f"   Equilibration Time: {params['equil_time']} s")
    
    # Create plotter
    plotter = SWVPlotter()
    plt.show(block=False)
    
    try:
        # Open serial connection
        ser = serial.Serial(port, 115200, timeout=2)
        time.sleep(1)
        
        # Clear STM32 (send ABORT commands)
        for i in range(3):
            ser.write(b'POTEn:ABORt\n')
            print(f"  Sent ABORT #{i+1}")
            time.sleep(0.3)
        
        # Clear buffer
        while ser.in_waiting > 0:
            ser.readline()
        
        time.sleep(1)
        
        # Check connection
        ser.write(b'*IDN?\n')
        time.sleep(0.5)
        if ser.in_waiting > 0:
            response = ser.readline().decode().strip()
            print(f"✅ STM32 connected: {response}")
        else:
            print("❌ No response from STM32")
            return
        
        # Build SWV command (10 parameters)
        swv_cmd = (f'POTEn:SWV:Start:ALL {params["start_voltage"]},{params["end_voltage"]},'
                  f'{params["step_voltage"]},{params["sw_amplitude"]},{params["sw_frequency"]},'
                  f'{params["enable_precon"]},{params["precon_pot1"]},{params["precon_pot2"]},'
                  f'{params["precon_time"]},{params["equil_time"]}')
        
        print(f"\n📡 Sending: {swv_cmd}")
        print(f"\n📊 SWV Response:")
        
        ser.write(f'{swv_cmd}\n'.encode())
        
        # Read response and plot in real-time
        start_time = time.time()
        data_count = 0
        update_count = 0
        
        while time.time() - start_time < 120:  # 2 minute timeout for SWV
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode().strip()
                    if line:
                        elapsed = time.time() - start_time
                        print(f"  [{elapsed:6.1f}s] {line}")
                        
                        if line.startswith('SWV,'):
                            try:
                                # Parse SWV data: SWV,Point,Time,Potential,Forward_i,Reverse_i,Net_i
                                parts = line.split(',')
                                if len(parts) >= 7:
                                    point_num = int(parts[1])
                                    time_val = float(parts[2])
                                    potential = float(parts[3])
                                    forward_current = float(parts[4]) * 1e6  # Convert to µA
                                    reverse_current = float(parts[5]) * 1e6  # Convert to µA
                                    net_current = float(parts[6]) * 1e6  # Convert to µA
                                    
                                    # Add to plotter data
                                    plotter.potentials.append(potential)
                                    plotter.net_currents.append(net_current)
                                    plotter.times.append(time_val)
                                    plotter.forward_currents.append(forward_current)
                                    plotter.reverse_currents.append(reverse_current)
                                    plotter.step_numbers.append(point_num)  # Add step number
                                    
                                    data_count += 1
                                    
                                    # Show progress for first few and every 20th point
                                    if data_count <= 5 or data_count % 20 == 0:
                                        print(f"    Point {point_num}: V={potential:.3f}V, "
                                              f"Forward={forward_current:.2f}µA, "
                                              f"Reverse={reverse_current:.2f}µA, "
                                              f"Net={net_current:.2f}µA")
                                    
                                    # Update plot every 5 points
                                    if data_count % 5 == 0:
                                        plotter.update_plot()
                                        update_count += 1
                                
                            except (ValueError, IndexError) as e:
                                print(f"    Parse error: {e}")
                        
                        if 'Operation Finished' in line or 'SWV Finished' in line:
                            print(f"  --> SWV completed at {elapsed:.1f}s")
                            break
                            
                except UnicodeDecodeError:
                    continue
            
            time.sleep(0.01)
        
        # Final plot update
        plotter.update_plot()
        
        # Calculate and display results
        if data_count > 0:
            voltage_range = max(plotter.potentials) - min(plotter.potentials)
            current_range_net = max(plotter.net_currents) - min(plotter.net_currents)
            current_range_forward = max(plotter.forward_currents) - min(plotter.forward_currents)
            current_range_reverse = max(plotter.reverse_currents) - min(plotter.reverse_currents)
            
            # Find peak in net current
            max_idx = np.argmax(np.abs(plotter.net_currents))
            peak_voltage = plotter.potentials[max_idx]
            peak_current = plotter.net_currents[max_idx]
            
            print(f"\n✅ SWV measurement completed!")
            print(f"📊 Data Summary:")
            print(f"  Total data points: {data_count}")
            print(f"  Potential range: {min(plotter.potentials):.3f}V to {max(plotter.potentials):.3f}V")
            print(f"  Net Current range: {min(plotter.net_currents):.2f}µA to {max(plotter.net_currents):.2f}µA")
            print(f"  Forward Current range: {min(plotter.forward_currents):.2f}µA to {max(plotter.forward_currents):.2f}µA")
            print(f"  Reverse Current range: {min(plotter.reverse_currents):.2f}µA to {max(plotter.reverse_currents):.2f}µA")
            print(f"  Peak: V={peak_voltage:.3f}V, I={peak_current:.2f}µA")
            
            measurement_duration = plotter.times[-1] if plotter.times else 0
            print(f"  Measurement duration: {measurement_duration:.1f}s")
            print(f"  Plot updates: {update_count}")
        
        print(f"\n🎯 SWV Analysis Complete - Close plot window to exit")
        
        # Keep plot open
        plt.show(block=True)
        
        ser.close()
        
    except KeyboardInterrupt:
        print("\n⚠️ Measurement interrupted by user")
        if 'ser' in locals():
            ser.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'ser' in locals():
            ser.close()

def main():
    """Main function"""
    print("🚀 Starting SWV Real-time Measurement...")
    run_swv_measurement()

if __name__ == "__main__":
    main()
