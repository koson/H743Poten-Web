#!/usr/bin/env python3
"""
DPV Test with STM32 H743
========================
Test command: POTEn:DPV:Start:ALL -0.5,0.5,0.05,0.01,0.05,0.1
"""

import serial
import time
import os

def find_stm32_port():
    """Find STM32 port - prioritize /dev/ttyACM0"""
    possible_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2']
    
    for port in possible_ports:
        if os.path.exists(port):
            print(f"🔍 Found STM32 at {port}")
            return port
    
    print("❌ No STM32 port found")
    return None

def test_dpv():
    """Test DPV command"""
    port = find_stm32_port()
    if not port:
        return
    
    # Get parameters from environment or use defaults
    start_v = float(os.environ.get('DPV_START_V', -0.5))
    end_v = float(os.environ.get('DPV_END_V', 0.5))
    pulse_amp = float(os.environ.get('DPV_PULSE_AMP', 0.05))
    step_size = float(os.environ.get('DPV_STEP_V', 0.01))
    pulse_width = float(os.environ.get('DPV_PULSE_WIDTH', 0.05))
    sample_time = float(os.environ.get('DPV_SAMPLE_WIDTH', 0.1))
    
    try:
        ser = serial.Serial(port, 115200, timeout=2)
        time.sleep(1)
        
        print("🔬 Testing DPV Command")
        print("=" * 40)
        
        # Clear any pending data and reset STM32
        for i in range(3):
            ser.write(b'POTEn:ABORt\n')
            time.sleep(0.3)
            print(f"  Sent ABORT #{i+1}")
        
        # Clear buffer
        while ser.in_waiting > 0:
            ser.readline()
        
        time.sleep(1)  # Wait for reset
        
        # Check connection
        ser.write(b'*IDN?\n')
        time.sleep(0.5)
        if ser.in_waiting > 0:
            response = ser.readline().decode().strip()
            print(f"✅ STM32 connected: {response}")
        
        print(f"\n📊 DPV Parameters:")
        print(f"   Start Voltage: {start_v} V")
        print(f"   End Voltage: {end_v} V")
        print(f"   Pulse Amplitude: {pulse_amp} V")
        print(f"   Step Size: {step_size} V")
        print(f"   Pulse Width: {pulse_width} s")
        print(f"   Sample Time: {sample_time} s")
        
        # Send DPV command
        dpv_cmd = f"POTEn:DPV:Start:ALL {start_v},{end_v},{pulse_amp},{step_size},{pulse_width},{sample_time}"
        print(f"\n📡 Sending: {dpv_cmd}")
        
        ser.write(f"{dpv_cmd}\n".encode())
        
        # Read response for 30 seconds
        print("\n📊 DPV Response:")
        start_time = time.time()
        data_count = 0
        
        while time.time() - start_time < 30:
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode().strip()
                    if line:
                        elapsed = time.time() - start_time
                        print(f"  [{elapsed:6.1f}s] {line}")
                        
                        # Count data lines
                        if line.startswith('DPV,'):
                            data_count += 1
                            
                        # Check for completion
                        if "Operation Finished" in line or "DPV Finished" in line:
                            print(f"  --> DPV completed at {elapsed:.1f}s")
                            break
                            
                except UnicodeDecodeError:
                    continue
                    
            time.sleep(0.01)
        
        print(f"\n✅ DPV test completed!")
        print(f"📊 Data lines received: {data_count}")
        
        ser.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_dpv()
