#!/usr/bin/env python3
"""
CV Scan Test Script - ทดสอบ CV Scan โดยตรงกับ STM32
ใช้ Python เพื่อทดสอบ STM32 CV functionality อย่างรวดเร็ว
"""

import serial
import time
import json
import sys
from datetime import datetime

class SimpleSTM32CVTester:
    def __init__(self, port="/dev/ttyACM0", baud=115200):
        self.port = port
        self.serial_conn = None
        
    def connect(self):
        """เชื่อมต่อกับ STM32"""
        try:
            print(f"🔌 Connecting to STM32 at {self.port}...")
            self.serial_conn = serial.Serial(
                self.port, 115200, 
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=5
            )
            print("✅ Serial connection established")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def send_command(self, command):
        """ส่งคำสั่งและรอ response"""
        if not self.serial_conn:
            return "ERROR: Not connected"
            
        try:
            self.serial_conn.write((command + '\n').encode())
            time.sleep(0.1)
            
            if self.serial_conn.in_waiting > 0:
                response = self.serial_conn.readline().decode().strip()
                return response
            else:
                return "NO_RESPONSE"
        except Exception as e:
            return f"ERROR: {e}"
    
    def clear_stm32_state(self):
        """ล้าง STM32 state (ported from Python)"""
        print("🧹 Clearing STM32 state...")
        
        # Send ABORT commands
        for i in range(1, 4):
            response = self.send_command("ABORT")
            print(f"  ABORT #{i}: {response}")
            time.sleep(0.1)
        
        # Clear buffer
        discarded = 0
        while self.serial_conn.in_waiting > 0:
            self.serial_conn.readline()
            discarded += 1
        print(f"  Discarded {discarded} lines")
        
        # Status check
        status = self.send_command("*IDN?")
        print(f"  Status: {status}")
        
        if "MANUFACTURE,INSTR2013" in status:
            print("✅ STM32 state cleared successfully!")
            return True
        else:
            print("❌ STM32 state clear failed")
            return False
    
    def test_cv_scan(self, begin_v=-0.5, upper_v=0.5, lower_v=-0.5, scan_rate=0.1, cycles=1, duration=30):
        """ทดสอบ CV scan"""
        print(f"\n🧪 Starting CV Scan Test:")
        print(f"  Begin: {begin_v}V, Upper: {upper_v}V, Lower: {lower_v}V")
        print(f"  Scan Rate: {scan_rate}V/s, Cycles: {cycles}")
        print(f"  Test Duration: {duration}s")
        
        # Calculate expected scan time
        voltage_range = abs(upper_v - lower_v) * 2  # up and down
        expected_time = (voltage_range / scan_rate) * cycles
        print(f"  Expected scan time: {expected_time:.1f}s")
        
        # Send CV start command
        cv_command = f"POTEn:CV:Start:ALL {begin_v},{upper_v},{lower_v},{scan_rate},{cycles}"
        print(f"\n📤 Sending: {cv_command}")
        
        response = self.send_command(cv_command)
        print(f"Response: {response}")
        
        if "ERROR" in response:
            print("❌ CV start command failed")
            return False
        
        # Collect data
        print("\n📊 Collecting CV data...")
        data_points = []
        start_time = time.time()
        last_log_time = start_time
        
        while time.time() - start_time < duration:
            try:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode().strip()
                    
                    if line and line.startswith("CV,"):
                        # Parse CV data
                        try:
                            parts = line.split(',')
                            if len(parts) >= 10:
                                data_point = {
                                    'type': parts[0],
                                    'time_us': int(parts[1]),
                                    'voltage': float(parts[2]),
                                    'current_ua': float(parts[3]) * 1e6,
                                    'tia_gain_index': int(parts[4]),
                                    'cycle': int(parts[5]),
                                    'dac1': int(parts[6]),
                                    'dac2': int(parts[7]),
                                    'sequence': int(parts[8]),
                                    'adc': int(parts[9]),
                                    'timestamp': datetime.now().isoformat()
                                }
                                data_points.append(data_point)
                                
                                # Debug output every 20 points
                                if len(data_points) % 20 == 0:
                                    elapsed = time.time() - start_time
                                    print(f"  [{elapsed:.1f}s] Points: {len(data_points)}, V={data_point['voltage']:.3f}V, I={data_point['current_ua']:.2f}µA")
                        
                        except (ValueError, IndexError) as e:
                            print(f"⚠️ Parse error: {e} for line: {line}")
                    
                    elif line and not line.startswith("CV,"):
                        # Non-CV data (could be status or error)
                        current_time = time.time()
                        if current_time - last_log_time > 5:  # Log every 5 seconds
                            print(f"  Info: {line}")
                            last_log_time = current_time
                
                else:
                    time.sleep(0.01)  # Small delay to prevent busy waiting
                    
            except Exception as e:
                print(f"❌ Data collection error: {e}")
                break
        
        print(f"\n✅ CV scan test completed!")
        print(f"📈 Total data points collected: {len(data_points)}")
        
        if data_points:
            # Show summary
            voltages = [p['voltage'] for p in data_points]
            currents = [p['current_ua'] for p in data_points]
            
            print(f"📊 Data Summary:")
            print(f"  Voltage range: {min(voltages):.3f}V to {max(voltages):.3f}V")
            print(f"  Current range: {min(currents):.2f}µA to {max(currents):.2f}µA")
            print(f"  Cycles detected: {max([p['cycle'] for p in data_points])}")
            
            # Save data
            filename = f"cv_test_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(data_points, f, indent=2)
            print(f"💾 Data saved to: {filename}")
            
            return True
        else:
            print("❌ No data collected")
            return False
    
    def disconnect(self):
        """ปิดการเชื่อมต่อ"""
        if self.serial_conn:
            self.serial_conn.close()
            print("🔌 Disconnected from STM32")

def main():
    print("🔬 STM32 CV Scan Test")
    print("=====================")
    
    # Auto-detect STM32 port
    ports_to_try = ["/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyUSB0", "/dev/ttyUSB1"]
    tester = None
    
    for port in ports_to_try:
        try:
            print(f"Trying port: {port}")
            tester = SimpleSTM32CVTester(port)
            if tester.connect():
                break
        except:
            continue
    
    if not tester or not tester.serial_conn:
        print("❌ Could not connect to STM32. Check USB connection.")
        return 1
    
    try:
        # Clear STM32 state
        if not tester.clear_stm32_state():
            print("❌ Failed to clear STM32 state")
            return 1
        
        # Run CV scan test
        success = tester.test_cv_scan(
            begin_v=-0.5,
            upper_v=0.5, 
            lower_v=-0.5,
            scan_rate=0.2,  # Faster for testing
            cycles=1,
            duration=30  # 30 second test
        )
        
        if success:
            print("\n🎉 CV scan test PASSED!")
            return 0
        else:
            print("\n❌ CV scan test FAILED!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return 1
    finally:
        tester.disconnect()

if __name__ == "__main__":
    exit(main())