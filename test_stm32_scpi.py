#!/usr/bin/env python3
"""
STM32 H743 SCPI Command Test Tool
Test SCPI commands directly on Windows to find working DPV commands
"""

import serial
import time
import sys
from typing import Optional, List

class STM32SCPITester:
    def __init__(self):
        self.ser: Optional[serial.Serial] = None
        self.port = None
        
    def find_stm32_ports(self) -> List[str]:
        """Find available COM ports that might be STM32"""
        import serial.tools.list_ports
        
        ports = []
        for port in serial.tools.list_ports.comports():
            print(f"Found port: {port.device} - {port.description}")
            if any(keyword in port.description.lower() for keyword in ['stm32', 'usb', 'serial']):
                ports.append(port.device)
        
        return ports
    
    def connect(self, port: str, baudrate: int = 115200) -> bool:
        """Connect to STM32 via serial port"""
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=2.0
            )
            self.port = port
            
            # Wait for connection to stabilize
            time.sleep(1)
            
            # Clear input buffer
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            print(f"✅ Connected to {port} at {baudrate} baud")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to {port}: {e}")
            return False
    
    def send_command(self, command: str, wait_response: bool = True) -> str:
        """Send SCPI command and get response"""
        if not self.ser:
            return "ERROR: Not connected"
        
        try:
            # Send command
            cmd_bytes = (command + '\n').encode('utf-8')
            print(f"📤 Sending: {command}")
            self.ser.write(cmd_bytes)
            self.ser.flush()
            
            if not wait_response:
                return "OK"
            
            # Wait for response
            time.sleep(0.1)
            response = ""
            
            # Read response with timeout
            start_time = time.time()
            while time.time() - start_time < 2.0:
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                    response += data
                    if '\n' in response or '\r' in response:
                        break
                time.sleep(0.01)
            
            response = response.strip()
            print(f"📥 Response: {response if response else '(no response)'}")
            return response
            
        except Exception as e:
            print(f"❌ Command error: {e}")
            return f"ERROR: {e}"
    
    def test_basic_commands(self):
        """Test basic SCPI commands"""
        print("\n🔍 Testing Basic SCPI Commands:")
        print("-" * 40)
        
        basic_commands = [
            "*IDN?",
            "*TST?", 
            "SYSTem:ERRor?",
            "SYSTem:VERSion?",
        ]
        
        for cmd in basic_commands:
            self.send_command(cmd)
            time.sleep(0.5)
    
    def test_dpv_commands(self):
        """Test DPV-specific commands"""
        print("\n🧪 Testing DPV Commands:")
        print("-" * 40)
        
        # Test different DPV command formats
        dpv_commands = [
            # Basic DPV commands
            "POTEn:DPV:VOLT:INIT -0.5",
            "POTEn:DPV:VOLT:FINAl 0.5", 
            "POTEn:DPV:VOLT:PULSe:HEIGht 0.05",
            "POTEn:DPV:VOLT:PULSe:INCR 0.01",
            "POTEn:DPV:TIME:PULSe:WIDTH 0.05",
            "POTEn:DPV:TIME:PULSe:PERIod 0.1",
            
            # DPV Start commands (test different formats)
            "POTEn:DPV:Start:ALL -0.5,0.5,0.05,0.01,0.05,0.1",
            "POTEn:DPV:Start -0.5,0.5,0.05,0.01,0.05,0.1",
            
            # DPV Data query
            "POTEn:DPV:DATA?",
            "POTEn:DPV:STATUS?",
            
            # DPV Abort
            "POTEn:DPV:ABORt",
        ]
        
        for cmd in dpv_commands:
            self.send_command(cmd)
            time.sleep(0.5)
    
    def test_cv_commands(self):
        """Test CV commands for comparison"""
        print("\n📈 Testing CV Commands (for comparison):")
        print("-" * 40)
        
        cv_commands = [
            "POTEn:CV:Start:ALL -1.0,1.0,-1.0,0.1,1",
            "POTEn:ABORt",
        ]
        
        for cmd in cv_commands:
            self.send_command(cmd)
            time.sleep(0.5)
    
    def interactive_mode(self):
        """Interactive command testing"""
        print("\n💬 Interactive Mode (type 'quit' to exit):")
        print("-" * 40)
        
        while True:
            try:
                cmd = input("SCPI> ").strip()
                if cmd.lower() in ['quit', 'exit', 'q']:
                    break
                if cmd:
                    self.send_command(cmd)
            except KeyboardInterrupt:
                break
    
    def disconnect(self):
        """Close serial connection"""
        if self.ser:
            self.ser.close()
            self.ser = None
            print(f"✅ Disconnected from {self.port}")

def main():
    print("🔬 STM32 H743 SCPI Command Tester")
    print("=" * 50)
    
    tester = STM32SCPITester()
    
    try:
        # Find available ports
        ports = tester.find_stm32_ports()
        
        if not ports:
            print("❌ No suitable COM ports found!")
            print("Please check STM32 connection and drivers.")
            return
        
        # Try to connect to each port
        connected = False
        for port in ports:
            if tester.connect(port):
                connected = True
                break
        
        if not connected:
            print("❌ Could not connect to any COM port!")
            return
        
        # Run tests
        tester.test_basic_commands()
        tester.test_dpv_commands()
        tester.test_cv_commands()
        
        # Interactive mode
        tester.interactive_mode()
        
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
    
    finally:
        tester.disconnect()

if __name__ == "__main__":
    main()