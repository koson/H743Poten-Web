#!/usr/bin/env python3
"""
SWV Test Final - Complete 10-Parameter Format
============================================
Test Square Wave Voltammetry with proper STM32 parameter format
"""

import serial
import time
import os
import matplotlib
matplotlib.use('Qt5Agg')  # Set backend before importing pyplot
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import threading

def find_stm32_port():
    """Find STM32 port - prioritize /dev/ttyACM0"""
    possible_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2']
    
    for port in possible_ports:
        if os.path.exists(port):
            print(f"🔍 Found STM32 at {port}")
            return port
    
    print("❌ No STM32 port found")
    return None

def get_swv_parameters_from_env():
    """Get SWV parameters from environment variables"""
    try:
        initial_pot = float(os.environ.get('SWV_START_V', '-0.5'))
        final_pot = float(os.environ.get('SWV_END_V', '0.5'))
        step_pot = float(os.environ.get('SWV_STEP_V', '0.005'))
        amplitude = float(os.environ.get('SWV_AMPLITUDE', '0.05'))
        frequency = float(os.environ.get('SWV_FREQUENCY', '5'))
        enable_precon = int(os.environ.get('SWV_ENABLE_PRECON', '0'))  # 0=disabled, 1=enabled
        precon_pot1 = float(os.environ.get('SWV_PRECON_POT1', '-1.9'))
        precon_pot2 = float(os.environ.get('SWV_PRECON_POT2', '-0.5'))
        precon_time = float(os.environ.get('SWV_PRECON_TIME', '60'))
        equil_time = float(os.environ.get('SWV_EQUIL_TIME', '10'))
        
        return initial_pot, final_pot, step_pot, amplitude, frequency, enable_precon, precon_pot1, precon_pot2, precon_time, equil_time
    except (ValueError, TypeError) as e:
        print(f"Error reading SWV parameters: {e}")
        return -0.5, 0.5, 0.005, 0.05, 5, 0, -1.9, -0.5, 60, 10

class SWVPlotter:
    def __init__(self):
        self.voltages = []
        self.currents = []
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.line, = self.ax.plot([], [], 'b-', linewidth=2, label='SWV Current')
        self.ax.set_xlabel('Potential (V)')
        self.ax.set_ylabel('Current (A)')
        self.ax.set_title('Square Wave Voltammetry - Real-time')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend()
        
    def update_plot(self, frame=None):
        if len(self.voltages) > 0 and len(self.currents) > 0:
            self.line.set_data(self.voltages, self.currents)
            self.ax.relim()
            self.ax.autoscale_view()
        return self.line,
    
    def add_point(self, voltage, current):
        self.voltages.append(voltage)
        self.currents.append(current)

def run_swv_measurement():
    """Run SWV measurement with STM32"""
    port = find_stm32_port()
    if not port:
        return
    
    # Get parameters
    initial_pot, final_pot, step_pot, amplitude, frequency, enable_precon, precon_pot1, precon_pot2, precon_time, equil_time = get_swv_parameters_from_env()
    
    print("⚡ Starting SWV Measurement")
    print("=" * 50)
    print(f"📊 SWV Parameters:")
    print(f"   Initial Potential: {initial_pot} V")
    print(f"   Final Potential: {final_pot} V")
    print(f"   Step Potential: {step_pot} V")
    print(f"   SW Amplitude: {amplitude} V")
    print(f"   SW Frequency: {frequency} Hz")
    print(f"   Enable Preconcentration: {enable_precon}")
    if enable_precon:
        print(f"   Precon Pot1: {precon_pot1} V")
        print(f"   Precon Pot2: {precon_pot2} V")
        print(f"   Precon Time: {precon_time} s")
        print(f"   Equilibration Time: {equil_time} s")
    
    # Initialize plotter
    plotter = SWVPlotter()
    
    try:
        ser = serial.Serial(port, 115200, timeout=2)
        time.sleep(1)
        
        # Clear any pending data and reset STM32
        for i in range(3):
            ser.write(b'POTEn:ABORt\n')
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
        
        # Build SWV command with all 10 parameters
        swv_cmd = f"POTEn:SWV:Start:ALL {initial_pot},{final_pot},{step_pot},{amplitude},{frequency},{enable_precon},{precon_pot1},{precon_pot2},{precon_time},{equil_time}"
        
        print(f"\n📡 Sending SWV command:")
        print(f"   {swv_cmd}")
        
        ser.write(f"{swv_cmd}\n".encode())
        
        # Setup animation
        ani = FuncAnimation(plotter.fig, plotter.update_plot, interval=100, blit=False)
        
        # Start plot in separate thread
        def show_plot():
            plt.show()
        
        plot_thread = threading.Thread(target=show_plot)
        plot_thread.daemon = True
        plot_thread.start()
        
        # Read SWV data
        print(f"\n📊 SWV Data:")
        start_time = time.time()
        data_count = 0
        precon_active = False
        
        # Extended timeout for preconcentration (add 60s buffer to precon_time)
        max_time = (precon_time + equil_time + 120) if enable_precon else 60
        
        print(f"⏱️  Maximum wait time: {max_time:.0f} seconds")
        if enable_precon:
            print(f"    Expected preconcentration: {precon_time}s + equilibration: {equil_time}s")
        
        last_progress_time = 0
        
        while time.time() - start_time < max_time:
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode().strip()
                    if line:
                        elapsed = time.time() - start_time
                        
                        # Show selective responses to avoid spam
                        show_line = True
                        if "PRECON_PROGRESS" in line and elapsed - last_progress_time < 10:
                            show_line = False  # Only show progress every 10 seconds
                        
                        if show_line:
                            print(f"  [{elapsed:6.1f}s] {line}")
                        
                        # Handle preconcentration progress with better feedback
                        if "PRECONCENTRATION_START" in line:
                            precon_active = True
                            print(f"    🔄 Starting preconcentration sequence ({precon_time}s + {equil_time}s)")
                        elif "PRECON_PROGRESS" in line:
                            if elapsed - last_progress_time >= 10:  # Update every 10 seconds
                                try:
                                    parts = line.split(',')
                                    if len(parts) >= 4:
                                        current_time = float(parts[2])
                                        total_time = float(parts[3])
                                        progress = (current_time / total_time) * 100
                                        remaining = total_time - current_time
                                        print(f"    ⏳ Preconcentration: {progress:.1f}% ({current_time:.0f}/{total_time:.0f}s, {remaining:.0f}s remaining)")
                                        last_progress_time = elapsed
                                except (ValueError, IndexError):
                                    print(f"    ⏳ Preconcentration in progress... ({elapsed:.0f}s)")
                                    last_progress_time = elapsed
                        elif "PRECON_FINISHED" in line:
                            precon_active = False
                            print(f"    ✅ Preconcentration completed! Starting SWV measurement...")
                        
                        # Parse SWV data points
                        if line.startswith('SWV,'):
                            try:
                                parts = line.split(',')
                                voltage = float(parts[1])
                                current = float(parts[2])
                                
                                # Add to plot
                                plotter.add_point(voltage, current)
                                
                                data_count += 1
                                if data_count <= 5 or data_count % 20 == 0:
                                    print(f"    📈 Data #{data_count}: V={voltage:.3f}V, I={current:.6e}A")
                                    
                            except (ValueError, IndexError):
                                continue
                        
                        # Check for completion
                        if any(x in line for x in ["Operation Finished", "SWV Finished"]):
                            print(f"  ✅ SWV completed at {elapsed:.1f}s")
                            break
                            
                except UnicodeDecodeError:
                    continue
                    
            time.sleep(0.01)
        
        print(f"\n📈 SWV Results:")
        print(f"   Total data points: {data_count}")
        print(f"   Voltage range: {min(plotter.voltages):.3f} to {max(plotter.voltages):.3f} V" if plotter.voltages else "No data")
        print(f"   Current range: {min(plotter.currents):.2e} to {max(plotter.currents):.2e} A" if plotter.currents else "No data")
        
        if data_count > 0:
            print("✅ SWV measurement successful! Plot window should be showing.")
            input("Press Enter to close...")
        else:
            print("❌ No SWV data received")
        
        ser.close()
        
    except Exception as e:
        print(f"❌ Error during SWV: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_swv_measurement()
