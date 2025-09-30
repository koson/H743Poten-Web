#!/usr/bin/env python3
"""
Real DPV Test with STM32 H743 Connection
========================================
Test Differential Pulse Voltammetry with actual hardware
"""

import sys
import os
import time
import serial
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime

# Configure matplotlib backend (same as CV)
def configure_matplotlib():
    """Configure matplotlib backend for different environments"""
    try:
        import tkinter
        matplotlib.use('TkAgg')
        print("📊 Using TkAgg backend for matplotlib")
    except ImportError:
        try:
            matplotlib.use('Qt5Agg')
            print("📊 Using Qt5Agg backend for matplotlib")
        except ImportError:
            matplotlib.use('Agg')
            print("📊 Using Agg backend for matplotlib (no display)")

configure_matplotlib()

def find_stm32_port():
    """Find STM32 port with priority order"""
    possible_ports = ['/dev/ttyACM2', '/dev/ttyACM1', '/dev/ttyACM0']
    
    for port in possible_ports:
        if os.path.exists(port):
            print(f"🔍 Found STM32 at {port}")
            return port
    
    print("❌ No STM32 port found")
    return None

def get_dpv_parameters_from_env():
    """Get DPV parameters from environment variables or use defaults"""
    return {
        'start_voltage': float(os.environ.get('DPV_START_V', -0.5)),
        'end_voltage': float(os.environ.get('DPV_END_V', 0.5)),
        'step_voltage': float(os.environ.get('DPV_STEP_V', 5)) / 1000.0,  # mV to V
        'pulse_amplitude': float(os.environ.get('DPV_PULSE_AMP', 50)) / 1000.0,  # mV to V
        'pulse_width': float(os.environ.get('DPV_PULSE_WIDTH', 100)) / 1000.0,  # ms to s
        'sample_width': float(os.environ.get('DPV_SAMPLE_WIDTH', 20)) / 1000.0,  # ms to s
        'current_range': int(os.environ.get('DPV_CURRENT_RANGE', 1))
    }

def clear_stm32_state(ser):
    """Clear STM32 state and stop any ongoing operations"""
    print("Clearing STM32 state...")
    
    try:
        # Send multiple ABORT commands
        for i in range(3):
            ser.write(b'POTEn:ABORt\n')
            time.sleep(0.2)
            print(f"  Sent ABORT command #{i+1}")
        
        # Clear buffer
        discarded_lines = 0
        start_clear = time.time()
        while time.time() - start_clear < 2:  # Clear for 2 seconds
            if ser.in_waiting > 0:
                line = ser.readline().decode().strip()
                if line:
                    discarded_lines += 1
            else:
                time.sleep(0.1)
        
        print(f"  Discarded {discarded_lines} lines of old data")
        
        # Verify connection
        ser.write(b'*IDN?\n')
        time.sleep(0.5)
        
        if ser.in_waiting > 0:
            response = ser.readline().decode().strip()
            print(f"  Status check response: {response}")
            print("  STM32 state cleared successfully!")
            return True
        else:
            print("  Warning: No response to status check")
            return False
            
    except Exception as e:
        print(f"  Error during state clearing: {e}")
        return False

def parse_dpv_data_line(line):
    """Parse DPV data line
    Expected format: DPV, Point, Time, Potential, Current_i1, Current_i2, DPVCurrent
    """
    try:
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 7 and parts[0].upper() == 'DPV':
            point_no = int(parts[1])
            time_ms = float(parts[2])
            voltage = float(parts[3])
            current_i1 = float(parts[4])
            current_i2 = float(parts[5])
            dpv_current = float(parts[6])
            
            return point_no, time_ms, voltage, current_i1, current_i2, dpv_current
    except (ValueError, IndexError) as e:
        print(f"Error parsing DPV line: {e}")
        print(f"Line: {line}")
    return None

def test_dpv_measurement():
    """Test DPV measurement with STM32"""
    ser = None
    try:
        # Get parameters
        params = get_dpv_parameters_from_env()
        
        print("🔬 Starting Differential Pulse Voltammetry (DPV) Test")
        print("=" * 60)
        
        # Find and connect to STM32
        port = find_stm32_port()
        if not port:
            print("❌ STM32 device not found!")
            return
        
        ser = serial.Serial(port, 115200, timeout=2)
        time.sleep(1)
        
        print(f'✅ Connected to STM32 at {port}')
        
        # Clear STM32 state
        if not clear_stm32_state(ser):
            print("Warning: Could not fully clear STM32 state, but continuing...")
        
        print("📊 DPV Parameters:")
        print(f"   Start Voltage: {params['start_voltage']:.3f} V")
        print(f"   End Voltage: {params['end_voltage']:.3f} V")
        print(f"   Step Voltage: {params['step_voltage']:.3f} V ({params['step_voltage']*1000:.1f} mV)")
        print(f"   Pulse Amplitude: {params['pulse_amplitude']:.3f} V ({params['pulse_amplitude']*1000:.1f} mV)")
        print(f"   Pulse Width: {params['pulse_width']:.3f} s ({params['pulse_width']*1000:.0f} ms)")
        print(f"   Sample Width: {params['sample_width']:.3f} s ({params['sample_width']*1000:.0f} ms)")
        
        # Calculate expected measurement time
        voltage_steps = int(abs(params['end_voltage'] - params['start_voltage']) / params['step_voltage'])
        expected_time = voltage_steps * (params['pulse_width'] + params['sample_width'])
        timeout_time = max(expected_time * 2, 30.0)  # At least 30s timeout
        
        print(f"📊 Expected steps: {voltage_steps}")
        print(f"⏱️ Expected time: {expected_time:.1f}s (timeout: {timeout_time:.1f}s)")
        
        # Send DPV command
        # Format: POTEn:DPV:Start:ALL start,end,step,pulse_amp,pulse_width,sample_width
        cmd = f"POTEn:DPV:Start:ALL {params['start_voltage']},{params['end_voltage']},{params['step_voltage']},{params['pulse_amplitude']},{params['pulse_width']},{params['sample_width']}"
        print(f"\n🚀 Sending: {cmd}")
        
        ser.write((cmd + '\n').encode())
        time.sleep(0.5)
        
        # Collect data
        print("📊 Collecting DPV data...")
        data_points = []
        start_time = time.time()
        last_progress_time = start_time
        
        try:
            while time.time() - start_time < timeout_time:
                if ser.in_waiting > 0:
                    line = ser.readline().decode().strip()
                    current_time = time.time() - start_time
                    
                    if line:
                        print(f"  [{current_time:6.1f}s] {line}")
                        
                        # Try to parse DPV data
                        dpv_data = parse_dpv_data_line(line)
                        if dpv_data:
                            point_no, time_ms, voltage, current_i1, current_i2, dpv_current = dpv_data
                            data_points.append({
                                'point': point_no,
                                'time': time_ms / 1000.0,  # Convert to seconds
                                'voltage': voltage,
                                'current_i1': current_i1,
                                'current_i2': current_i2,
                                'dpv_current': dpv_current
                            })
                            
                            # Progress indication
                            if time.time() - last_progress_time > 2.0:
                                print(f"  --> DPV data point {point_no}: V={voltage:.3f}V, I={dpv_current:.2f}µA")
                                last_progress_time = time.time()
                        
                        # Check for completion
                        if "DPV Operation Finished" in line or "FINISHED" in line.upper():
                            print("  --> DPV scan completed")
                            break
                            
                else:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\n⏹️ DPV measurement interrupted by user")
            ser.write(b'POTEn:ABORt\n')
            
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n✅ DPV measurement completed!")
        print(f"📊 Data points collected: {len(data_points)}")
        print(f"⏱️ Duration: {duration:.1f} seconds")
        
        if data_points:
            # Save and plot data
            save_dpv_data(data_points, params, duration)
            plot_dpv_data(data_points, params)
        else:
            print("⚠️ No data points collected")
            
    except Exception as e:
        print(f"❌ DPV test error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if ser:
            print("\nFinal cleanup...")
            ser.close()
            print("Serial connection closed.")
        print("DPV test finished.")

def save_dpv_data(data_points, params, duration):
    """Save DPV data to CSV file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create data directory
    data_dir = os.path.expanduser("~/PyPiPo_Data/DPV/data")
    date_dir = os.path.join(data_dir, datetime.now().strftime("%Y-%m-%d"))
    os.makedirs(date_dir, exist_ok=True)
    
    # Save CSV data
    csv_file = os.path.join(date_dir, f"dpv_data_{timestamp}.csv")
    with open(csv_file, 'w') as f:
        f.write("Point,Time(s),Voltage(V),Current_i1(uA),Current_i2(uA),DPV_Current(uA)\n")
        for point in data_points:
            f.write(f"{point['point']},{point['time']:.6f},{point['voltage']:.6f},"
                   f"{point['current_i1']:.6f},{point['current_i2']:.6f},{point['dpv_current']:.6f}\n")
    
    print(f"💾 DPV data saved to: {csv_file}")
    return csv_file

def plot_dpv_data(data_points, params):
    """Create DPV plot"""
    if not data_points:
        return
        
    voltages = [point['voltage'] for point in data_points]
    dpv_currents = [point['dpv_current'] for point in data_points]
    current_i1 = [point['current_i1'] for point in data_points]  
    current_i2 = [point['current_i2'] for point in data_points]
    
    # Create plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    
    # Main DPV plot
    ax1.plot(voltages, dpv_currents, 'r-', linewidth=2, label='DPV Current')
    ax1.set_xlabel('Potential / V')
    ax1.set_ylabel('DPV Current / µA')
    ax1.set_title(f'Differential Pulse Voltammetry\n'
                  f'Step: {params["step_voltage"]*1000:.1f} mV, '
                  f'Pulse: {params["pulse_amplitude"]*1000:.1f} mV')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Component currents
    ax2.plot(voltages, current_i1, 'b--', linewidth=1, label='Baseline Current (i1)', alpha=0.7)
    ax2.plot(voltages, current_i2, 'g--', linewidth=1, label='Pulse Current (i2)', alpha=0.7)
    ax2.plot(voltages, dpv_currents, 'r-', linewidth=2, label='DPV Current (i2-i1)')
    ax2.set_xlabel('Potential / V')
    ax2.set_ylabel('Current / µA')
    ax2.set_title('DPV Current Components')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    
    # Save plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plots_dir = os.path.expanduser("~/PyPiPo_Data/DPV/plots")
    date_dir = os.path.join(plots_dir, datetime.now().strftime("%Y-%m-%d"))
    os.makedirs(date_dir, exist_ok=True)
    
    plot_file = os.path.join(date_dir, f"dpv_plot_{timestamp}.png")
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"📈 DPV plot saved to: {plot_file}")
    
    # Show plot
    plt.show()
    
    return plot_file

def main():
    """Main function"""
    try:
        test_dpv_measurement()
        return 0
    except KeyboardInterrupt:
        print("\n⏹️ DPV test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ DPV test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
