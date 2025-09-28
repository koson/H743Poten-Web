#!/usr/bin/env python3
"""
Quick STM32 SCPI Test Script
Run this when you find the COM port to test real DPV commands
"""

import serial
import time

def test_real_stm32(com_port: str):
    """Test real STM32 with DPV commands"""
    try:
        # Connect to STM32
        print(f"🔌 Connecting to {com_port}...")
        ser = serial.Serial(com_port, 115200, timeout=2)
        time.sleep(2)  # Wait for connection
        
        # Clear buffers
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        print("✅ Connected!")
        
        # Test commands
        commands = [
            "*IDN?",
            "POTEn:DPV:Start:ALL -0.5,0.5,0.05,0.01,0.05,0.1",
            "POTEn:DPV:STATUS?",
            "POTEn:DPV:DATA?",
            "POTEn:DPV:ABORt"
        ]
        
        for cmd in commands:
            print(f"\n📤 Sending: {cmd}")
            ser.write((cmd + '\n').encode())
            ser.flush()
            
            time.sleep(0.5)
            
            # Read response
            response = ""
            while ser.in_waiting > 0:
                data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                response += data
                time.sleep(0.1)
            
            print(f"📥 Response: {response.strip() if response else '(no response)'}")
        
        ser.close()
        print("\n✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

# Usage example
if __name__ == "__main__":
    # Replace COMx with your actual COM port
    # Examples: "COM3", "COM4", "COM5", etc.
    
    print("🚀 STM32 Real Hardware Test")
    print("=" * 40)
    print("Replace 'COMx' with your actual COM port number")
    print("Example: test_real_stm32('COM3')")
    print()
    
    # Uncomment and modify this line with your COM port:
    # test_real_stm32('COM3')
    
    print("📋 To find your COM port:")
    print("1. Open Device Manager")
    print("2. Look under 'Ports (COM & LPT)'") 
    print("3. Find STM32 Virtual COM Port")
    print("4. Note the COM number (e.g., COM3)")
    print("5. Edit this script and run the test")