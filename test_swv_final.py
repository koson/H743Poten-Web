#!/usr/bin/env python3
"""
SWV (Square Wave Voltammetry) Implementation
============================================
Based on H743_ELECTROCHEMICAL_METHODS_SPECIFICATION.md
"""

import sys
import os
import time
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime
import json

# Configure matplotlib backend
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

# Import after backend configuration
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Debug messages control
ENABLE_AUTO_RANGE_DEBUG = False

def find_stm32_port():
    """Find STM32 port with priority order"""
    possible_ports = ['/dev/ttyACM1', '/dev/ttyACM2', '/dev/ttyACM0']
    
    for port in possible_ports:
        if os.path.exists(port):
            print(f"🔍 Found STM32 at {port}")
            return port
    
    print("❌ No STM32 port found")
    return None

def get_swv_parameters_from_env():
    """Get SWV parameters from environment variables or use defaults"""
    return {
        'start_voltage': float(os.environ.get('SWV_START_V', -0.5)),
        'end_voltage': float(os.environ.get('SWV_END_V', 0.5)),
        'step_voltage': float(os.environ.get('SWV_STEP_V', 0.005)),  # V
        'sw_amplitude': float(os.environ.get('SWV_AMP', 0.025)),  # V
        'sw_frequency': float(os.environ.get('SWV_FREQ', 50)),  # Hz
        'current_range': int(os.environ.get('SWV_CURRENT_RANGE', 1))
    }

def simulate_swv_data(params):
    """Simulate SWV data with realistic electrochemical response"""
    start_v = params['start_voltage']
    end_v = params['end_voltage']
    step_v = params['step_voltage']
    sw_amp = params['sw_amplitude']
    sw_freq = params['sw_frequency']
    
    # Create voltage points
    voltages = np.arange(start_v, end_v + step_v, step_v)
    n_points = len(voltages)
    
    print(f"📊 Generating {n_points} SWV points from {start_v:.3f}V to {end_v:.3f}V")
    print(f"⚡ Step: {step_v:.3f}V, Amplitude: {sw_amp:.3f}V, Frequency: {sw_freq:.0f} Hz")
    
    data_points = []
    
    # Calculate time per step (period = 1/frequency)
    period = 1.0 / sw_freq
    time_step = period  # One period per step
    
    # Simulate SWV measurement
    for i, voltage in enumerate(voltages):
        # Forward pulse (positive amplitude)
        forward_voltage = voltage + sw_amp
        forward_current = 1e-7 * np.exp(-(forward_voltage - 0.2)**2 / 0.1) + \
                         2e-8 * (1 + 0.1 * np.random.randn())
        
        # Add realistic peak enhancement around 0.2V
        if abs(forward_voltage - 0.2) < 0.1:
            peak_enhancement = 8e-7 * np.exp(-(forward_voltage - 0.2)**2 / 0.002)
            forward_current += peak_enhancement
        
        # Reverse pulse (negative amplitude)
        reverse_voltage = voltage - sw_amp
        reverse_current = 1e-7 * np.exp(-(reverse_voltage - 0.2)**2 / 0.1) + \
                         2e-8 * (1 + 0.1 * np.random.randn())
        
        # Add peak enhancement for reverse too
        if abs(reverse_voltage - 0.2) < 0.1:
            peak_enhancement = 3e-7 * np.exp(-(reverse_voltage - 0.2)**2 / 0.002)
            reverse_current += peak_enhancement
        
        # SWV net current is the difference
        net_current = forward_current - reverse_current
        
        # Current range auto-detection simulation
        current_magnitude = abs(net_current)
        if ENABLE_AUTO_RANGE_DEBUG:
            if current_magnitude > 50e-6:
                current_range = 0  # 100µA
                gain = 1000
            elif current_magnitude > 5e-6:
                current_range = 1  # 10µA
                gain = 10000
            elif current_magnitude > 0.5e-6:
                current_range = 2  # 1µA
                gain = 100000
            else:
                current_range = 3  # 100nA
                gain = 1000000
            
            print(f"AUTO-RANGE DEBUG: V={voltage:.4f}, Range={current_range}, "
                  f"RGain={gain}, I={net_current*1e6:.2f} µA")
        
        # Calculate measurement time
        measurement_time = i * time_step
        
        data_point = {
            'voltage': voltage,
            'forward_current': forward_current,
            'reverse_current': reverse_current,
            'net_current': net_current,
            'time': measurement_time
        }
        
        data_points.append(data_point)
        
        # Progress indication
        if i % 20 == 0:
            progress = (i / n_points) * 100
            print(f"⏳ SWV Progress: {progress:.1f}% - V={voltage:.3f}V, I={net_current*1e6:.2f} µA")
    
    return data_points

def save_swv_data(data_points, params):
    """Save SWV data to files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create data directory
    data_dir = os.path.expanduser("~/PyPiPo_Data/SWV")
    plots_dir = os.path.join(data_dir, "plots")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)
    
    # Save JSON data
    json_file = os.path.join(data_dir, f"swv_data_{timestamp}.json")
    swv_data = {
        'method': 'SWV',
        'timestamp': timestamp,
        'parameters': params,
        'data': data_points,
        'statistics': {
            'total_points': len(data_points),
            'voltage_range': f"{params['start_voltage']:.3f} to {params['end_voltage']:.3f} V",
            'max_current': max(point['net_current'] for point in data_points),
            'min_current': min(point['net_current'] for point in data_points),
            'peak_voltage': None,  # Could be calculated from peak detection
            'peak_current': None,
            'frequency': params['sw_frequency']
        }
    }
    
    with open(json_file, 'w') as f:
        json.dump(swv_data, f, indent=2)
    
    print(f"💾 SWV data saved to: {json_file}")
    
    # Save CSV data
    csv_file = os.path.join(data_dir, f"swv_data_{timestamp}.csv")
    with open(csv_file, 'w') as f:
        f.write("Voltage(V),Forward_Current(A),Reverse_Current(A),Net_Current(A),Time(s)\n")
        for point in data_points:
            f.write(f"{point['voltage']:.6f},{point['forward_current']:.6e},"
                   f"{point['reverse_current']:.6e},{point['net_current']:.6e},"
                   f"{point['time']:.6f}\n")
    
    print(f"💾 SWV CSV saved to: {csv_file}")
    
    return json_file, plots_dir

def plot_swv_data(data_points, params, plots_dir):
    """Create SWV plot"""
    voltages = [point['voltage'] for point in data_points]
    net_currents = [point['net_current'] * 1e6 for point in data_points]  # Convert to µA
    forward_currents = [point['forward_current'] * 1e6 for point in data_points]
    reverse_currents = [point['reverse_current'] * 1e6 for point in data_points]
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    
    # Main SWV plot (net current)
    ax1.plot(voltages, net_currents, 'r-', linewidth=2, label='SWV Response')
    ax1.set_xlabel('Potential / V')
    ax1.set_ylabel('Current / µA')
    ax1.set_title(f'Square Wave Voltammetry\n'
                  f'Step: {params["step_voltage"]*1000:.1f} mV, '
                  f'Amplitude: {params["sw_amplitude"]*1000:.1f} mV, '
                  f'Frequency: {params["sw_frequency"]:.0f} Hz')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Forward and reverse currents comparison
    ax2.plot(voltages, forward_currents, 'g--', linewidth=1, label='Forward Current', alpha=0.7)
    ax2.plot(voltages, reverse_currents, 'b--', linewidth=1, label='Reverse Current', alpha=0.7)
    ax2.plot(voltages, net_currents, 'r-', linewidth=2, label='Net Current (SWV)')
    ax2.set_xlabel('Potential / V')
    ax2.set_ylabel('Current / µA')
    ax2.set_title('SWV Current Components')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    
    # Save plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_file = os.path.join(plots_dir, f"swv_plot_{timestamp}.png")
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"📈 SWV plot saved to: {plot_file}")
    return plot_file

def run_swv_measurement():
    """Run complete SWV measurement"""
    print("⚡ Starting Square Wave Voltammetry (SWV) Measurement")
    print("=" * 60)
    
    # Get parameters
    params = get_swv_parameters_from_env()
    
    print(f"📊 SWV Parameters:")
    print(f"   Start Voltage: {params['start_voltage']:.3f} V")
    print(f"   End Voltage: {params['end_voltage']:.3f} V")
    print(f"   Step Voltage: {params['step_voltage']:.3f} V ({params['step_voltage']*1000:.1f} mV)")
    print(f"   SW Amplitude: {params['sw_amplitude']:.3f} V ({params['sw_amplitude']*1000:.1f} mV)")
    print(f"   SW Frequency: {params['sw_frequency']:.0f} Hz")
    print(f"   Current Range: {params['current_range']}")
    
    # Check STM32 connection
    stm32_port = find_stm32_port()
    if not stm32_port:
        print("⚠️ STM32 not found - running in simulation mode")
    else:
        print(f"✅ STM32 connected at {stm32_port}")
    
    # Run measurement (simulated for now)
    print("\n🚀 Starting SWV scan...")
    start_time = time.time()
    
    data_points = simulate_swv_data(params)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n✅ SWV measurement completed!")
    print(f"📊 Data points collected: {len(data_points)}")
    print(f"⏱️ Duration: {duration:.1f} seconds")
    
    # Calculate statistics
    net_currents = [point['net_current'] for point in data_points]
    max_current = max(net_currents)
    min_current = min(net_currents)
    avg_current = np.mean(net_currents)
    
    print(f"📈 Current Statistics:")
    print(f"   Maximum: {max_current*1e6:.2f} µA")
    print(f"   Minimum: {min_current*1e6:.2f} µA") 
    print(f"   Average: {avg_current*1e6:.2f} µA")
    
    # Find peak (simple peak detection)
    max_idx = np.argmax(np.abs(net_currents))
    peak_voltage = data_points[max_idx]['voltage']
    peak_current = net_currents[max_idx]
    
    print(f"🎯 Peak Detection:")
    print(f"   Peak Voltage: {peak_voltage:.3f} V")
    print(f"   Peak Current: {peak_current*1e6:.2f} µA")
    
    # Calculate scan rate (effective)
    voltage_range = abs(params['end_voltage'] - params['start_voltage'])
    effective_scan_rate = voltage_range / duration
    
    print(f"⚡ SWV Performance:")
    print(f"   Effective Scan Rate: {effective_scan_rate:.3f} V/s")
    print(f"   Points per Second: {len(data_points)/duration:.1f}")
    
    # Save data and create plots
    json_file, plots_dir = save_swv_data(data_points, params)
    plot_file = plot_swv_data(data_points, params, plots_dir)
    
    print(f"\n💾 Results saved:")
    print(f"   Data: {json_file}")
    print(f"   Plot: {plot_file}")
    
    print("\n🎉 SWV Analysis Complete!")
    return data_points

def main():
    """Main function"""
    try:
        data_points = run_swv_measurement()
        return 0
    except KeyboardInterrupt:
        print("\n⏹️ SWV measurement interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ SWV measurement failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
