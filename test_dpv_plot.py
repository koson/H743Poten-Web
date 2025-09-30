#!/usr/bin/env python3
"""
DPV Measurement with Real-time Plotting for H743Poten-Web
=========================================================
Complete DPV measurement with matplotlib real-time plotting
Based on working test_dpv_simple.py but with visualization
"""

import serial
import time
import os
import sys
import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend for compatibility
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import threading
import queue
import numpy as np

def find_stm32_port():
    """Find STM32 port - prioritize /dev/ttyACM0"""
    possible_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2']
    
    for port in possible_ports:
        if os.path.exists(port):
            print(f"✓ Found STM32 at {port}")
            return port
    
    print("✗ No STM32 port found")
    return None

def get_dpv_parameters_from_env():
    """Get DPV parameters from environment variables"""
    start_v = float(os.environ.get('DPV_START_V', -0.5))
    end_v = float(os.environ.get('DPV_END_V', 0.5))
    pulse_amp = float(os.environ.get('DPV_PULSE_AMP', 0.05))
    step_v = float(os.environ.get('DPV_STEP_V', 0.01))
    pulse_width = float(os.environ.get('DPV_PULSE_WIDTH', 0.05))
    sample_width = float(os.environ.get('DPV_SAMPLE_WIDTH', 0.1))
    
    return start_v, end_v, pulse_amp, step_v, pulse_width, sample_width

class DPVPlotter:
    def __init__(self):
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        self.fig.suptitle('DPV Real-time Analysis', fontsize=16, fontweight='bold')
        
        # DPV Current vs Potential
        self.ax1.set_title('DPV Current vs Potential')
        self.ax1.set_xlabel('Potential (V)')
        self.ax1.set_ylabel('DPV Current (µA)')
        self.ax1.grid(True, alpha=0.3)
        
        # Raw Currents vs Time
        self.ax2.set_title('Raw Current Measurements vs Time')
        self.ax2.set_xlabel('Time (s)')
        self.ax2.set_ylabel('Current (µA)')
        self.ax2.grid(True, alpha=0.3)
        
        # Data storage
        self.potentials = []
        self.dpv_currents = []
        self.times = []
        self.current_i1 = []
        self.current_i2 = []
        
        # Plot lines
        self.line1, = self.ax1.plot([], [], 'b-', linewidth=2, label='DPV Current')
        self.line2, = self.ax2.plot([], [], 'r-', linewidth=1, label='Current i1', alpha=0.7)
        self.line3, = self.ax2.plot([], [], 'g-', linewidth=1, label='Current i2', alpha=0.7)
        
        self.ax1.legend()
        self.ax2.legend()
        
        plt.tight_layout()
        
    def update_plot(self):
        """Update the plot with new data"""
        if len(self.potentials) > 0:
            # Update DPV current plot
            self.line1.set_data(self.potentials, self.dpv_currents)
            self.ax1.relim()
            self.ax1.autoscale_view()
            
            # Update raw current plots
            if len(self.times) > 0:
                self.line2.set_data(self.times, self.current_i1)
                self.line3.set_data(self.times, self.current_i2)
                self.ax2.relim()
                self.ax2.autoscale_view()
        
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

def run_dpv_measurement():
    """Run DPV measurement with real-time plotting"""
    port = find_stm32_port()
    if not port:
        return
    
    # Get parameters
    start_v, end_v, pulse_amp, step_v, pulse_width, sample_width = get_dpv_parameters_from_env()
    
    print("🔬 DPV Real-time Measurement")
    print("=" * 50)
    print(f"📊 DPV Parameters:")
    print(f"   Start Voltage: {start_v} V")
    print(f"   End Voltage: {end_v} V")
    print(f"   Pulse Amplitude: {pulse_amp} V")
    print(f"   Step Size: {step_v} V")
    print(f"   Pulse Width: {pulse_width} s")
    print(f"   Sample Time: {sample_width} s")
    
    # Initialize plotter
    plotter = DPVPlotter()
    plt.show(block=False)
    
    try:
        ser = serial.Serial(port, 115200, timeout=2)
        time.sleep(1)
        
        # Clear any pending data and reset STM32
        for i in range(3):
            ser.write(b'POTEn:ABORt\n')
            time.sleep(0.3)
            print(f"  Sent ABORT #{i+1}")
        
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
        
        # Send DPV command
        dpv_cmd = f'POTEn:DPV:Start:ALL {start_v},{end_v},{pulse_amp},{step_v},{pulse_width},{sample_width}'
        print(f"\n📡 Sending: {dpv_cmd}")
        ser.write(f'{dpv_cmd}\n'.encode())
        
        print(f"\n📊 DPV Response:")
        start_time = time.time()
        data_count = 0
        measurement_start_time = None
        
        while time.time() - start_time < 30:
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode().strip()
                    if line:
                        elapsed = time.time() - start_time
                        print(f"  [{elapsed:6.1f}s] {line}")
                        
                        # Parse DPV data
                        if line.startswith('DPV,'):
                            data_count += 1
                            parts = line.split(',')
                            
                            if len(parts) >= 7:
                                try:
                                    point = int(parts[1])
                                    meas_time = float(parts[2])
                                    potential = float(parts[3])
                                    current_i1 = float(parts[4]) * 1e6  # Convert to µA
                                    current_i2 = float(parts[5]) * 1e6  # Convert to µA
                                    dpv_current = float(parts[6]) * 1e6  # Convert to µA
                                    
                                    # Store data
                                    plotter.potentials.append(potential)
                                    plotter.dpv_currents.append(dpv_current)
                                    plotter.times.append(meas_time)
                                    plotter.current_i1.append(current_i1)
                                    plotter.current_i2.append(current_i2)
                                    
                                    # Update plot every 5 points
                                    if data_count % 5 == 0:
                                        plotter.update_plot()
                                        
                                    if data_count <= 5:
                                        print(f"    Point {point}: V={potential:.3f}V, I1={current_i1:.2f}µA, I2={current_i2:.2f}µA, DPV={dpv_current:.2f}µA")
                                        
                                except (ValueError, IndexError) as e:
                                    print(f"    Parse error: {e}")
                        
                        # Mark measurement start
                        elif "DPV Operation Started" in line:
                            measurement_start_time = time.time()
                            
                        # Check for completion
                        elif "Operation Finished" in line or "DPV Finished" in line:
                            print(f"  --> DPV completed at {elapsed:.1f}s")
                            break
                            
                except UnicodeDecodeError:
                    continue
                    
            time.sleep(0.01)
        
        # Final plot update
        plotter.update_plot()
        
        print(f"\n✅ DPV measurement completed!")
        print(f"📊 Data Summary:")
        print(f"  Total data points: {data_count}")
        
        if len(plotter.potentials) > 0:
            print(f"  Potential range: {min(plotter.potentials):.3f}V to {max(plotter.potentials):.3f}V")
            print(f"  DPV Current range: {min(plotter.dpv_currents):.2f}µA to {max(plotter.dpv_currents):.2f}µA")
            
            if measurement_start_time:
                total_time = time.time() - measurement_start_time
                print(f"  Measurement duration: {total_time:.1f}s")
        
        print(f"\n🎯 DPV Analysis Complete - Close plot window to exit")
        
        # Keep plot open
        try:
            plt.show()
        except KeyboardInterrupt:
            print("\n⚠️ Measurement interrupted by user")
        
        ser.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting DPV Real-time Measurement...")
    run_dpv_measurement()
