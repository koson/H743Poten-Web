#!/usr/bin/env python3
"""
Quick STM32 Serial Test
"""
import serial
import time

def test_stm32():
    try:
        print("🔌 Connecting to STM32...")
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=3)
        time.sleep(2)
        
        print("📤 Sending *IDN? command...")
        ser.write(b'*IDN?\r\n')
        time.sleep(2)
        
        print("📥 Reading response...")
        response = ser.read(1000)
        
        print(f"Raw response: {response}")
        print(f"Decoded: {response.decode('utf-8', errors='ignore')}")
        print(f"Length: {len(response)} bytes")
        
        # Test new streaming commands
        print("\n🚀 Testing new streaming status...")
        ser.write(b'POTEn:CV:Stream:STATUS?\r\n')
        time.sleep(1)
        status_response = ser.read(1000)
        print(f"Status response: {status_response.decode('utf-8', errors='ignore')}")
        
        ser.close()
        print("✅ Test completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_stm32()