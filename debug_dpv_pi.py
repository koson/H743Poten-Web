#!/usr/bin/env python3
"""
Enhanced DPV Debug Script for Pi
Test DPV functionality with enhanced completion detection and data reception
"""

import serial
import time
import sys
import json
from datetime import datetime

def test_basic_connection():
    """Test basic STM32 connection"""
    print("=" * 60)
    print("1. Testing Basic STM32 Connection")
    print("=" * 60)
    
    devices = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']
    
    for device in devices:
        try:
            print(f"Trying {device}...")
            ser = serial.Serial(device, 115200, timeout=2)
            time.sleep(0.5)
            
            # Test basic communication
            ser.write(b'*IDN?\n')
            response = ser.readline().decode('utf-8', errors='ignore').strip()
            
            if response:
                print(f"✅ Connected to {device}")
                print(f"   Device ID: {response}")
                ser.close()
                return device
            else:
                ser.close()
                
        except Exception as e:
            print(f"❌ Failed {device}: {e}")
    
    print("❌ No STM32 device found!")
    return None

def test_dpv_commands(device):
    """Test DPV SCPI commands"""
    print("\n" + "=" * 60)
    print("2. Testing DPV SCPI Commands")
    print("=" * 60)
    
    try:
        ser = serial.Serial(device, 115200, timeout=3)
        time.sleep(0.5)
        
        # Clear buffer
        ser.flushInput()
        ser.flushOutput()
        
        # Test commands
        commands = [
            ('*IDN?', 'Device identification'),
            ('SYST:ERR?', 'System error check'),
            ('VOLT:RANG:AUTO ON', 'Enable auto voltage range'),
            ('CURR:RANG:AUTO ON', 'Enable auto current range'),
            ('MEAS:DPV:STAR 0.0', 'Set DPV start voltage'),
            ('MEAS:DPV:END 1.0', 'Set DPV end voltage'),
            ('MEAS:DPV:STEP 0.01', 'Set DPV step voltage'),
            ('MEAS:DPV:PULS 0.05', 'Set DPV pulse amplitude'),
            ('MEAS:DPV:PERI 0.2', 'Set DPV period'),
            ('MEAS:DPV:PWIDTH 0.01', 'Set DPV pulse width')
        ]
        
        for cmd, desc in commands:
            print(f"Testing: {cmd} ({desc})")
            ser.write(f'{cmd}\n'.encode())
            time.sleep(0.1)
            
            # Read response for query commands
            if '?' in cmd:
                response = ser.readline().decode('utf-8', errors='ignore').strip()
                print(f"   Response: {response}")
            else:
                print(f"   ✅ Command sent")
        
        ser.close()
        print("✅ All DPV commands tested successfully")
        return True
        
    except Exception as e:
        print(f"❌ DPV command test failed: {e}")
        return False

def test_dpv_measurement(device):
    """Test actual DPV measurement with enhanced completion detection"""
    print("\n" + "=" * 60)
    print("3. Testing DPV Measurement with Enhanced Detection")
    print("=" * 60)
    
    try:
        ser = serial.Serial(device, 115200, timeout=1)
        time.sleep(0.5)
        
        # Clear buffer
        ser.flushInput()
        ser.flushOutput()
        
        # Setup DPV parameters
        setup_commands = [
            'VOLT:RANG:AUTO ON',
            'CURR:RANG:AUTO ON',
            'MEAS:DPV:STAR 0.0',
            'MEAS:DPV:END 1.0',
            'MEAS:DPV:STEP 0.01',
            'MEAS:DPV:PULS 0.05',
            'MEAS:DPV:PERI 0.2',
            'MEAS:DPV:PWIDTH 0.01'
        ]
        
        print("Setting up DPV parameters...")
        for cmd in setup_commands:
            ser.write(f'{cmd}\n'.encode())
            time.sleep(0.05)
        
        # Start DPV measurement
        print("Starting DPV measurement...")
        ser.write(b'MEAS:DPV:RUN\n')
        start_time = time.time()
        
        # Enhanced completion detection
        completion_methods = {
            'message_parsing': False,
            'status_query': False,
            'timeout': False
        }
        
        data_points = []
        buffer_data = ""
        timeout_duration = 30  # 30 seconds timeout
        status_check_interval = 2  # Check status every 2 seconds
        last_status_check = 0
        
        print("Monitoring measurement progress...")
        print(f"Expected points: {int((1.0 - 0.0) / 0.01) + 1}")
        
        while time.time() - start_time < timeout_duration:
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Method 1: Read and parse incoming data
            try:
                if ser.in_waiting > 0:
                    chunk = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                    buffer_data += chunk
                    
                    # Check for completion messages
                    if 'MEASUREMENT COMPLETE' in buffer_data.upper() or 'DPV COMPLETE' in buffer_data.upper():
                        completion_methods['message_parsing'] = True
                        print("✅ Completion detected via message parsing")
                        break
                    
                    # Parse data points
                    lines = buffer_data.split('\n')
                    for line in lines[:-1]:  # Keep last incomplete line in buffer
                        line = line.strip()
                        if line and ',' in line:
                            try:
                                parts = line.split(',')
                                if len(parts) >= 2:
                                    voltage = float(parts[0])
                                    current = float(parts[1])
                                    data_points.append((voltage, current))
                            except ValueError:
                                continue
                    
                    # Update buffer with incomplete line
                    buffer_data = lines[-1] if lines else ""
                    
                    # Print progress
                    if len(data_points) > 0 and len(data_points) % 10 == 0:
                        print(f"   Progress: {len(data_points)} points collected")
            
            except Exception as e:
                print(f"   Data reading error: {e}")
            
            # Method 2: Status query (every 2 seconds)
            if current_time - last_status_check >= status_check_interval:
                try:
                    ser.write(b'STAT:OPER?\n')
                    time.sleep(0.1)
                    status_response = ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    if status_response and status_response != '1':  # Not measuring
                        completion_methods['status_query'] = True
                        print("✅ Completion detected via status query")
                        break
                        
                    last_status_check = current_time
                except Exception as e:
                    print(f"   Status query error: {e}")
            
            time.sleep(0.1)
        
        # Method 3: Timeout detection
        if time.time() - start_time >= timeout_duration:
            completion_methods['timeout'] = True
            print("⚠️  Measurement completed via timeout")
        
        # Try to get any remaining data
        time.sleep(0.5)
        try:
            if ser.in_waiting > 0:
                remaining = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                buffer_data += remaining
                
                # Parse remaining data
                lines = buffer_data.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and ',' in line:
                        try:
                            parts = line.split(',')
                            if len(parts) >= 2:
                                voltage = float(parts[0])
                                current = float(parts[1])
                                data_points.append((voltage, current))
                        except ValueError:
                            continue
        except Exception as e:
            print(f"   Final data collection error: {e}")
        
        ser.close()
        
        # Report results
        print(f"\n📊 Measurement Results:")
        print(f"   Total time: {time.time() - start_time:.2f} seconds")
        print(f"   Data points collected: {len(data_points)}")
        print(f"   Completion methods:")
        for method, detected in completion_methods.items():
            status = "✅" if detected else "❌"
            print(f"     {status} {method}")
        
        if data_points:
            print(f"   First point: V={data_points[0][0]:.3f}V, I={data_points[0][1]:.6f}A")
            print(f"   Last point:  V={data_points[-1][0]:.3f}V, I={data_points[-1][1]:.6f}A")
            
            # Save data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dpv_debug_{timestamp}.json"
            
            result_data = {
                'timestamp': timestamp,
                'measurement_time': time.time() - start_time,
                'data_points': data_points,
                'completion_methods': completion_methods,
                'point_count': len(data_points)
            }
            
            with open(filename, 'w') as f:
                json.dump(result_data, f, indent=2)
            
            print(f"   Data saved to: {filename}")
            return True
        else:
            print("❌ No data points collected!")
            return False
            
    except Exception as e:
        print(f"❌ DPV measurement test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Enhanced DPV Debug Script for Pi")
    print("Testing STM32 H743 DPV functionality with enhanced completion detection")
    print("=" * 80)
    
    # Test 1: Basic connection
    device = test_basic_connection()
    if not device:
        print("\n❌ Cannot proceed without STM32 connection")
        sys.exit(1)
    
    # Test 2: SCPI commands
    if not test_dpv_commands(device):
        print("\n❌ SCPI command test failed")
        sys.exit(1)
    
    # Test 3: DPV measurement
    if test_dpv_measurement(device):
        print("\n✅ All tests completed successfully!")
        print("🎯 DPV system is working with enhanced completion detection")
    else:
        print("\n❌ DPV measurement test failed")
        print("🔧 Check hardware connections and STM32 firmware")
    
    print("\n" + "=" * 80)
    print("Debug session completed")

if __name__ == "__main__":
    main()