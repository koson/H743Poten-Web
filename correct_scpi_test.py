"""
STM32 DAC Test with Correct SCPI Commands
Based on actual SCPI command definitions from firmware
"""

import serial
import time

def test_correct_scpi():
    """Test DAC with correct SCPI commands"""
    
    print("="*60)
    print("🔬 STM32 H743 DAC Test - Correct SCPI Commands")
    print("="*60)
    
    try:
        # Connect to STM32
        ser = serial.Serial('COM9', 115200, timeout=3)
        time.sleep(2)
        
        def send_command(cmd, expect_response=True):
            print(f"📤 {cmd}")
            ser.write(f"{cmd}\r\n".encode())
            time.sleep(0.3)
            
            if expect_response:
                response = ser.readline().decode().strip()
                print(f"📥 '{response}'")
                return response
            return None
        
        # Test basic communication
        print("\n🔗 Basic Communication:")
        send_command("*IDN?")
        send_command("*RST")
        
        print("\n🎯 Testing CV Configuration Commands:")
        
        # Try CV configuration (this might trigger DAC via Timer2)
        send_command("POTEn:VOLTage:UPPEr 2.0")  # Upper voltage 2.0V
        send_command("POTEn:VOLTage:LOWEr -1.0") # Lower voltage -1.0V  
        send_command("POTEn:VOLTage:BEGIn 0.0")  # Begin voltage 0.0V
        send_command("POTEn:VOLTage:IDLE 0.0")   # Idle voltage 0.0V
        send_command("POTEn:RATE:SWEEp 0.1")     # Sweep rate 0.1 V/s
        send_command("POTEn:PPS 100")            # Points per second
        send_command("POTEn:NUMCycles 1")        # Number of cycles
        
        print("\n⚡ Testing Source Voltage Commands:")
        
        # Try source voltage commands (these might control DAC directly)
        test_voltages = [0.0, 0.5, 1.0, 1.5, 2.0]
        
        for voltage in test_voltages:
            # Try different voltage source command formats
            commands_to_try = [
                f"SOURce:VOLTage {voltage}",
                f"SOUR:VOLT {voltage}",
                f"SOURce:VOLTage:LEVel {voltage}",
            ]
            
            for cmd in commands_to_try:
                print(f"\n🎯 Testing: {cmd}")
                response = send_command(cmd)
                
                if response and "ERROR" not in response:
                    print(f"✅ Command accepted!")
                    break
                else:
                    print(f"❌ Command failed: {response}")
        
        print("\n🔋 Testing Potentiostat Idle Commands:")
        # Set idle state which might set DAC to a specific value
        send_command("POTEn:VOLTage:IDLE 1.25")  # VG voltage
        
        print("\n🧪 Testing CV Start (should activate Timer2 DAC control):")
        send_command("POTEn:CALCulate:SCANpattern")  # Calculate scan pattern
        print("⏳ Starting CV scan - DAC should be controlled by Timer2...")
        send_command("POTEn:CYCLic:Start")
        
        # Wait for CV scan to start
        time.sleep(2)
        
        print("🛑 Stopping CV scan...")
        send_command("POTEn:ABORt")
        
        print("\n📋 Manual Test Instructions:")
        print("="*60)
        print("1. Connect multimeter to PA4 (DAC Channel 1 - Drive)")
        print("   - Should be 0V when idle")
        print("   - Should change during CV scan")
        print("")
        print("2. Connect multimeter to PA5 (DAC Channel 2 - Virtual Ground)")
        print("   - Should be stable at ~1.25V")
        print("")
        print("3. Run CV scan from web interface and observe:")
        print("   - PA4 voltage should sweep between limits")
        print("   - PA5 should remain constant")
        
        print("\n✅ SCPI Test completed!")
        print("📊 Next steps:")
        print("   - Use web interface for CV scan")
        print("   - Monitor DAC outputs with multimeter")
        print("   - Check if voltages match expected values")
        
        ser.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_correct_scpi()