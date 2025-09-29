#!/usr/bin/env python3
"""
Test STM32 H743 Streaming Commands
"""
import serial
import time

def test_streaming():
    try:
        print("🔌 Connecting to STM32 H743...")
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=3)
        time.sleep(2)
        
        print("=== Testing STM32 H743 Streaming Commands ===")
        
        # Test stream start
        print("📤 Sending: POTEn:CV:Stream:START -0.5,0.5,-0.5,0.1,1")
        ser.write(b'POTEn:CV:Stream:START -0.5,0.5,-0.5,0.1,1\r\n')
        time.sleep(3)  # More time for processing
        response = ser.read(2000)
        print(f"📥 Stream start response ({len(response)} bytes):")
        print(f"   Raw: {response}")
        print(f"   Decoded: {response.decode('utf-8', errors='ignore')}")
        
        # Wait for measurement to complete
        print("\n⏳ Waiting for measurement...")
        time.sleep(5)
        
        # Test status
        print("📤 Sending: POTEn:CV:Stream:STATUS?")
        ser.write(b'POTEn:CV:Stream:STATUS?\r\n')
        time.sleep(1)
        response = ser.read(1000)
        print(f"📥 Status response ({len(response)} bytes):")
        print(f"   Raw: {response}")
        print(f"   Decoded: {response.decode('utf-8', errors='ignore')}")
        
        # Test data retrieval
        print("📤 Sending: POTEn:CV:Stream:DATA?")
        ser.write(b'POTEn:CV:Stream:DATA?\r\n')
        time.sleep(2)
        response = ser.read(5000)  # Larger buffer for data
        print(f"📥 Data response ({len(response)} bytes):")
        decoded = response.decode('utf-8', errors='ignore')
        print(f"   First 200 chars: {decoded[:200]}...")
        if "voltage,current" in decoded:
            lines = decoded.split('\n')
            print(f"   Total lines: {len(lines)}")
            data_lines = [l for l in lines if ',' in l and not l.startswith('voltage')]
            print(f"   Data points: {len(data_lines)}")
            if data_lines:
                print(f"   First point: {data_lines[0]}")
                print(f"   Last point: {data_lines[-1]}")
        
        ser.close()
        print("✅ Test completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_streaming()