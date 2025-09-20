"""
Simple STM32 DAC Test without VISA
Tests DAC functionality via SCPI commands
"""

import serial
import time

def test_scpi_dac():
    """Test SCPI DAC commands without requiring DMM"""
    
    print("="*60)
    print("🔬 STM32 H743 DAC SCPI Test")
    print("="*60)
    
    try:
        # Connect to STM32 (based on web logs, might be COM8)
        ports_to_try = ['COM8', 'COM9', 'COM7']
        ser = None
        
        for port in ports_to_try:
            try:
                print(f"🔗 Trying to connect to {port}...")
                ser = serial.Serial(port, 115200, timeout=3)
                time.sleep(2)
                
                # Test communication
                ser.write(b'*IDN?\r\n')
                response = ser.readline().decode().strip()
                
                if response and len(response) > 0:
                    print(f"✅ Connected to {port}: {response}")
                    break
                else:
                    ser.close()
                    
            except Exception as e:
                print(f"❌ {port} failed: {e}")
                if ser:
                    ser.close()
                continue
        
        if not ser or not ser.is_open:
            print("❌ Could not connect to any STM32 port!")
            return False
        
        def send_command(cmd, expect_response=True):
            print(f"📤 Sending: {cmd}")
            ser.write(f"{cmd}\r\n".encode())
            time.sleep(0.2)
            
            if expect_response:
                response = ser.readline().decode().strip()
                print(f"📥 Response: '{response}'")
                return response
            return None
        
        print("\n" + "="*60)
        print("🧪 TESTING SCPI COMMANDS")
        print("="*60)
        
        # Test basic commands
        print("\n1️⃣ Testing basic SCPI communication:")
        send_command("*IDN?")
        send_command("*RST")
        
        print("\n2️⃣ Testing voltage source commands:")
        
        # Test different voltage levels
        test_voltages = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        
        for voltage in test_voltages:
            print(f"\n🎯 Setting voltage to {voltage}V:")
            response = send_command(f"SOUR:VOLT:DC {voltage}")
            
            # Check if we got an acknowledgment
            if response is None or len(response) == 0:
                print("⚠️  No response received")
            elif "Error" in response or "error" in response:
                print(f"❌ Error response: {response}")
            else:
                print(f"✅ Command accepted: {response}")
            
            time.sleep(1)
        
        print("\n3️⃣ Testing DAC status queries:")
        send_command("SOUR:VOLT:DC?")
        send_command("SYST:ERR?")
        
        print("\n4️⃣ Testing Virtual Ground (if supported):")
        # Try to test VG commands
        vg_commands = [
            "SOUR:VOLT:VG 1.25",
            "SOUR:VOLT:VG?",
            "DAC:CH2:VOLT 1.25",
            "DAC:CH2:VOLT?"
        ]
        
        for cmd in vg_commands:
            try:
                response = send_command(cmd)
                if response and len(response) > 0:
                    print(f"✅ VG command worked: {cmd} -> {response}")
                else:
                    print(f"⚠️  VG command no response: {cmd}")
            except:
                print(f"❌ VG command failed: {cmd}")
        
        print("\n" + "="*60)
        print("📋 TEST INSTRUCTIONS FOR MANUAL VERIFICATION:")
        print("="*60)
        print("1. Connect multimeter to PA4 (DAC Channel 1)")
        print("2. Run a CV scan from web interface")
        print("3. Observe if voltage changes during scan")
        print("")
        print("4. Connect multimeter to PA5 (DAC Channel 2)")
        print("5. Check if voltage is around 1.25V (Virtual Ground)")
        print("")
        print("Expected behavior:")
        print("- PA4: Should change voltage during CV operations")
        print("- PA5: Should be stable at ~1.25V (Virtual Ground)")
        
        # Cleanup
        ser.close()
        
        print("\n✅ SCPI communication test completed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_scpi_dac()