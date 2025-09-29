#!/usr/bin/env python3
"""
Simple COM Port Scanner for STM32
Run this to find available COM ports on Windows
"""

import sys

def find_com_ports():
    """Find available COM ports"""
    try:
        import serial.tools.list_ports
        
        print("🔍 Scanning for COM ports...")
        print("-" * 40)
        
        ports = list(serial.tools.list_ports.comports())
        
        if not ports:
            print("❌ No COM ports found!")
            print("\nPlease check:")
            print("  1. STM32 is connected via USB")
            print("  2. USB drivers are installed") 
            print("  3. Check Device Manager > Ports (COM & LPT)")
            return []
        
        com_ports = []
        for port in ports:
            print(f"📡 {port.device}: {port.description}")
            
            # Check if it might be STM32
            desc_lower = port.description.lower()
            if any(keyword in desc_lower for keyword in ['stm32', 'usb serial', 'virtual com']):
                print(f"   ✅ Possible STM32 device!")
                com_ports.append(port.device)
            
        print(f"\n📋 Found {len(ports)} total ports, {len(com_ports)} potential STM32 ports")
        
        if com_ports:
            print(f"\n🎯 Try these COM ports for STM32:")
            for port in com_ports:
                print(f"   {port}")
        
        return com_ports
        
    except ImportError:
        print("❌ pyserial not installed!")
        print("Run: pip install pyserial")
        return []
    except Exception as e:
        print(f"❌ Error scanning ports: {e}")
        return []

if __name__ == "__main__":
    ports = find_com_ports()
    
    if ports:
        print(f"\n🚀 To test SCPI commands:")
        print(f"   python -c \"")
        print(f"import serial")
        print(f"ser = serial.Serial('{ports[0]}', 115200, timeout=2)")
        print(f"ser.write(b'*IDN?\\n')")
        print(f"print(ser.read(100))")  
        print(f"ser.close()\"")
    else:
        print("\n🔧 Manual check:")
        print("   Open Device Manager")
        print("   Look under 'Ports (COM & LPT)'")
        print("   Find STM32 Virtual COM Port")