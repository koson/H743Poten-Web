#!/usr/bin/env python3
"""
Cross-platform STM32 Device Finder
Finds available serial ports and identifies likely STM32 devices
"""

import sys
import os
import platform

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from hardware.port_scanner import get_available_ports, find_stm32_ports, test_port_connection
except ImportError:
    # Fallback implementation if module not available
    import serial.tools.list_ports
    
    def get_available_ports():
        """Fallback: Get list of available serial ports"""
        ports = list(serial.tools.list_ports.comports())
        available_ports = []
        
        for port in ports:
            port_info = {
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid,
                'manufacturer': getattr(port, 'manufacturer', None),
                'vid': getattr(port, 'vid', None),
                'pid': getattr(port, 'pid', None)
            }
            available_ports.append(port_info)
            
        return available_ports
    
    def find_stm32_ports():
        """Fallback: Find ports that are likely STM32 devices"""
        all_ports = get_available_ports()
        stm32_ports = []
        
        for port in all_ports:
            desc = port['description'].lower()
            hwid = port.get('hwid', '').lower()
            
            # Check for known STM32 identifiers
            is_stm32 = (
                any(x in desc for x in ['stm32', 'stlink', 'virtual com port', 'usb serial']) or
                ('vid:pid=0483:5740' in hwid) or  # Common STM32 VID:PID
                ('vid:pid=0483:374b' in hwid) or  # Another STM32 VID:PID
                (port.get('vid') == 1155 and port.get('pid') == 22336)  # 0x0483:0x5740 in decimal
            )
            
            if is_stm32:
                stm32_ports.append(port)
                
        return stm32_ports
    
    def test_port_connection(port, baud_rate=115200):
        """Fallback: Test if we can open a connection to the port"""
        try:
            import serial
            ser = serial.Serial(port, baud_rate, timeout=1)
            ser.close()
            return True
        except Exception:
            return False

def print_port_info(port_info):
    """Print formatted port information"""
    print(f"📍 {port_info['device']}")
    print(f"   Description: {port_info['description']}")
    if port_info['manufacturer']:
        print(f"   Manufacturer: {port_info['manufacturer']}")
    if port_info['vid'] and port_info['pid']:
        print(f"   VID:PID: {port_info['vid']:04X}:{port_info['pid']:04X}")
    print(f"   Hardware ID: {port_info['hwid']}")
    print()

def main():
    """Main function to scan and display available ports"""
    print("🔍 H743Poten Device Scanner")
    print("=" * 50)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print()
    
    # Get all available ports
    print("📡 Scanning for serial ports...")
    all_ports = get_available_ports()
    
    if not all_ports:
        print("❌ No serial ports found!")
        print("\n💡 Troubleshooting tips:")
        print("   1. Make sure your STM32 device is connected via USB")
        print("   2. Check that drivers are installed")
        print("   3. On WSL, COM ports may not be directly accessible")
        print("   4. Try running this from Windows PowerShell or Command Prompt")
        return
    
    print(f"✅ Found {len(all_ports)} total serial port(s)")
    print()
    
    # Display all ports
    print("📋 All Available Ports:")
    print("-" * 30)
    for port in all_ports:
        print_port_info(port)
    
    # Find likely STM32 devices
    print("🎯 Likely STM32 Devices:")
    print("-" * 30)
    stm32_ports = find_stm32_ports()
    
    if stm32_ports:
        for port in stm32_ports:
            print(f"✅ STM32 Device Found!")
            print_port_info(port)
            
            # Test connection
            if test_port_connection(port['device']):
                print(f"   🔗 Connection test: PASSED")
            else:
                print(f"   ❌ Connection test: FAILED")
            print()
        
        # Provide usage recommendation
        recommended_port = stm32_ports[0]['device']
        print(f"🚀 Recommended port to use: {recommended_port}")
        print(f"   Update your script to use: serial.Serial('{recommended_port}', 115200)")
        
    else:
        print("⚠️  No obvious STM32 devices found")
        print("   But you can try any of the ports listed above")
        if all_ports:
            print(f"   Try starting with: {all_ports[0]['device']}")
    
    print("\n📝 Next Steps:")
    print("   1. Update your test script with the correct COM port")
    print("   2. Make sure your STM32 firmware is running")
    print("   3. Test SCPI communication")

if __name__ == "__main__":
    main()