#!/usr/bin/env python3
"""
Debug script to test STM32 connection issues
"""
import serial
import serial.tools.list_ports
import time
import os

def test_direct_connection():
    """Test direct serial connection"""
    port = "/dev/ttyACM1"
    baud = 115200
    
    print(f"=== Direct Connection Test ===")
    print(f"Port: {port}")
    print(f"Baud: {baud}")
    
    # Check if port exists
    if not os.path.exists(port):
        print(f"❌ Port {port} does not exist")
        return False
    
    # Check permissions
    if not os.access(port, os.R_OK | os.W_OK):
        print(f"❌ Port {port} is not accessible")
        return False
    
    print(f"✅ Port {port} exists and is accessible")
    
    try:
        # Try to open port
        ser = serial.Serial(
            port=port,
            baudrate=baud,
            timeout=1,
            write_timeout=1,
            rtscts=False,
            dsrdtr=False
        )
        
        if ser.is_open:
            print(f"✅ Port opened successfully")
            
            # Test communication
            ser.write(b"*IDN?\n")
            time.sleep(0.1)
            response = ser.read(100)
            print(f"Response: {response}")
            
            ser.close()
            print(f"✅ Connection test successful")
            return True
        else:
            print(f"❌ Port failed to open")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_port_listing():
    """Test port listing"""
    print(f"\n=== Port Listing Test ===")
    try:
        ports = list(serial.tools.list_ports.comports())
        print(f"Available ports:")
        for port in ports:
            print(f"  - {port.device}: {port.description}")
        return True
    except Exception as e:
        print(f"❌ Port listing failed: {e}")
        return False

def test_scpi_handler():
    """Test SCPI handler connection"""
    print(f"\n=== SCPI Handler Test ===")
    try:
        import sys
        sys.path.append('/home/ben/h743poten-web/src')
        
        from hardware.scpi_handler import SCPIHandler
        
        handler = SCPIHandler("/dev/ttyACM1", 115200)
        success = handler.connect()
        
        if success:
            print(f"✅ SCPI Handler connected successfully")
            handler.disconnect()
            return True
        else:
            print(f"❌ SCPI Handler connection failed")
            return False
            
    except Exception as e:
        print(f"❌ SCPI Handler test failed: {e}")
        return False

if __name__ == "__main__":
    print("STM32 Connection Debug Script")
    print("=" * 40)
    
    test_port_listing()
    test_direct_connection()
    test_scpi_handler()