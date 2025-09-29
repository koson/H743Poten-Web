#!/usr/bin/env python3
"""
Simple STM32 Serial Test
Check if STM32 is connected and responding to DPV commands
"""

import serial
import time
import sys

def find_stm32_port():
    """Find STM32 port"""
    
    ports_to_try = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']
    
    for port in ports_to_try:
        try:
            print(f"🔍 Trying {port}...")
            ser = serial.Serial(port, 115200, timeout=2)
            time.sleep(1)  # Wait for connection
            
            # Test basic communication
            ser.write(b"*IDN?\r\n")
            time.sleep(0.5)
            
            response = ""
            while ser.in_waiting:
                response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                time.sleep(0.1)
            
            if response.strip():
                print(f"✅ Found STM32 on {port}")
                print(f"📝 Response: {response.strip()}")
                return ser, port
            else:
                print(f"❌ No response from {port}")
                ser.close()
                
        except Exception as e:
            print(f"❌ Error with {port}: {e}")
            continue
    
    return None, None

def test_dpv_commands(ser):
    """Test DPV commands"""
    
    print("\n🧪 Testing DPV Commands...")
    print("=" * 40)
    
    # Set current range first
    print("📡 Setting current range to 2...")
    ser.write(b"POTEn:CURRent:RANGe 2\r\n")
    time.sleep(0.5)
    
    # Read response
    response = ""
    while ser.in_waiting:
        response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        time.sleep(0.1)
    
    if response:
        print(f"📄 Range response: {response.strip()}")
    
    # Send DPV command
    print("📡 Sending DPV command...")
    dpv_cmd = "POTEn:DPV:Start:ALL -0.5,0.5,0.05,0.01,0.05,0.1\r\n"
    print(f"Command: {dpv_cmd.strip()}")
    
    ser.write(dpv_cmd.encode())
    time.sleep(1)
    
    # Read response
    response = ""
    timeout = time.time() + 3  # 3 second timeout
    
    while time.time() < timeout:
        if ser.in_waiting:
            response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        time.sleep(0.1)
    
    if response:
        print(f"✅ DPV setup response: {response.strip()}")
        return True
    else:
        print("❌ No response to DPV command")
        return False

def monitor_dpv_data(ser, duration=30):
    """Monitor DPV data for specified duration"""
    
    print(f"\n📊 Monitoring DPV data for {duration} seconds...")
    print("=" * 40)
    
    start_time = time.time()
    data_count = 0
    last_data_time = start_time
    
    while (time.time() - start_time) < duration:
        # Check for incoming data
        if ser.in_waiting:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if line:
                    current_time = time.time()
                    elapsed = current_time - start_time
                    
                    # Check if it's DPV data
                    if line.startswith('DPV,') or 'DPV' in line:
                        data_count += 1
                        last_data_time = current_time
                        print(f"[{elapsed:6.1f}s] 📈 Data #{data_count}: {line}")
                        
                    elif 'Operation Finished' in line or 'COMPLETE' in line:
                        print(f"[{elapsed:6.1f}s] 🏁 Measurement completed: {line}")
                        break
                        
                    elif line and not line.startswith('#'):
                        print(f"[{elapsed:6.1f}s] 📄 Other: {line}")
                        
            except Exception as e:
                print(f"❌ Error reading data: {e}")
        
        time.sleep(0.1)
    
    # Summary
    total_time = time.time() - start_time
    data_gap = time.time() - last_data_time
    
    print(f"\n📋 Data Summary:")
    print(f"⏱️  Total time: {total_time:.1f}s")
    print(f"📊 Data points: {data_count}")
    print(f"⌛ Last data: {data_gap:.1f}s ago")
    
    if data_count > 0:
        print("✅ STM32 IS sending DPV data!")
    else:
        print("❌ No DPV data received")
        
        # Try to query data manually
        print("\n🔍 Trying manual data query...")
        ser.write(b"POTEn:DPV:DATA?\r\n")
        time.sleep(1)
        
        response = ""
        while ser.in_waiting:
            response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            time.sleep(0.1)
        
        if response:
            print(f"📄 Manual query response: {response[:200]}...")
        else:
            print("❌ No response to manual query")

def main():
    """Main test function"""
    
    print("🔌 STM32 DPV Serial Test")
    print("=" * 40)
    
    # Find STM32
    ser, port = find_stm32_port()
    
    if not ser:
        print("❌ No STM32 found!")
        print("💡 Make sure STM32 is connected and powered on")
        return
    
    try:
        # Test commands
        cmd_ok = test_dpv_commands(ser)
        
        if cmd_ok:
            # Monitor data
            monitor_dpv_data(ser, duration=30)
        else:
            print("❌ Commands failed, skipping data monitoring")
    
    finally:
        ser.close()
        print(f"\n🔌 Closed connection to {port}")

if __name__ == "__main__":
    main()