#!/usr/bin/env python3
"""Serial Connection Tester for H743 Potentiostat"""

import serial.tools.list_ports
import subprocess
import os

def list_windows_ports():
    """Get COM ports from Windows"""
    try:
        result = subprocess.run(['powershell.exe', '-c', '[System.IO.Ports.SerialPort]::getportnames()'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            ports = [port.strip() for port in result.stdout.strip().split('\n') if port.strip()]
            return ports
    except:
        return []

def test_serial_connection():
    """Test serial connection"""
    print("🔌 H743 Potentiostat Serial Connection Test")
    print("=" * 45)
    
    # Get Windows COM ports
    windows_ports = list_windows_ports()
    print(f"📋 Windows COM Ports: {windows_ports}")
    
    # Get pyserial ports
    pyserial_ports = [port.device for port in serial.tools.list_ports.comports()]
    print(f"📋 PySerial Ports: {pyserial_ports}")
    
    if not windows_ports and not pyserial_ports:
        print("❌ No COM ports found!")
        print("\n💡 Solutions:")
        print("   1. Connect H743 device via USB")
        print("   2. Check Windows Device Manager")
        print("   3. Use Mock mode for testing")
        enable_mock_mode()
        return
    
    # Test connection to each port
    all_ports = set(windows_ports + pyserial_ports)
    print(f"\n🔄 Testing {len(all_ports)} ports...")
    
    for port in all_ports:
        test_single_port(port)

def test_single_port(port):
    """Test connection to a single port"""
    print(f"\n🔌 Testing {port}...")
    
    try:
        import serial
        
        # Try different WSL mappings
        test_ports = [port]
        if port.startswith('COM'):
            com_num = int(port[3:])
            wsl_port = f"/dev/ttyS{com_num-1}"
            test_ports.append(wsl_port)
        
        for test_port in test_ports:
            try:
                print(f"  🔍 Trying: {test_port}")
                ser = serial.Serial(test_port, 115200, timeout=1)
                print(f"  ✅ Connected to {test_port}")
                
                # Test basic communication
                ser.write(b"*IDN?\r\n")
                import time
                time.sleep(0.1)
                
                if ser.in_waiting > 0:
                    response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                    print(f"  �� Response: {response.strip()}")
                else:
                    print("  ⚠️  No response (might not be H743)")
                
                ser.close()
                print(f"  🎯 Recommend using: {test_port}")
                create_env_file(test_port)
                return True
                
            except Exception as e:
                print(f"  ❌ Failed {test_port}: {e}")
                continue
    
    except ImportError:
        print("  ❌ pyserial not installed")
    
    return False

def create_env_file(port):
    """Create environment file with working port"""
    env_content = f"""# H743 Potentiostat Serial Configuration
SERIAL_PORT={port}
SERIAL_BAUDRATE=115200
WEB_HOST=0.0.0.0
WEB_PORT=8080
FLASK_ENV=development
"""
    
    with open('.env.serial', 'w') as f:
        f.write(env_content)
    print(f"  📝 Created .env.serial with {port}")

def enable_mock_mode():
    """Enable mock mode for testing"""
    print("\n🎭 Setting up Mock Mode...")
    
    mock_content = """# H743 Potentiostat Mock Configuration
SERIAL_PORT=MOCK
SERIAL_BAUDRATE=115200
WEB_HOST=0.0.0.0
WEB_PORT=8080
FLASK_ENV=development
USE_MOCK_HANDLER=true
"""
    
    with open('.env.mock', 'w') as f:
        f.write(mock_content)
    
    print("✅ Created .env.mock")
    print("\n🔄 To use Mock mode:")
    print("   cp .env.mock .env")
    print("   python auto_dev.py restart")

if __name__ == "__main__":
    test_serial_connection()
