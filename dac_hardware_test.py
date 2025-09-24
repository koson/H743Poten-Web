"""
Simple DAC Hardware Test Script
Tests DAC channels directly via hardware measurement
"""

import pyvisa
import serial
import time
import sys

def test_dac_hardware():
    """Test DAC hardware output with direct measurement"""
    
    # Initialize VISA for Keysight DMM
    try:
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()
        print(f"Available VISA resources: {resources}")
        
        # Find Keysight DMM
        keysight_resource = None
        for resource in resources:
            if 'USB' in resource and '2A8D' in resource:
                keysight_resource = resource
                break
        
        if not keysight_resource:
            print("❌ Keysight 34461A not found!")
            return False
            
        dmm = rm.open_resource(keysight_resource)
        dmm.timeout = 5000
        
        # Configure DMM for DC voltage measurement
        dmm.write("*RST")
        dmm.write("CONF:VOLT:DC 10,0.001")  # 10V range, 1mV resolution
        dmm.write("VOLT:DC:NPLC 10")        # High precision
        
        print(f"✅ Keysight DMM connected: {dmm.query('*IDN?').strip()}")
        
    except Exception as e:
        print(f"❌ DMM connection failed: {e}")
        return False
    
    # Initialize STM32 serial connection
    try:
        stm32 = serial.Serial('COM9', 115200, timeout=2)
        time.sleep(2)  # Wait for connection
        
        # Test communication
        stm32.write(b'*IDN?\r\n')
        response = stm32.readline().decode().strip()
        print(f"✅ STM32 connected: {response}")
        
    except Exception as e:
        print(f"❌ STM32 connection failed: {e}")
        return False
    
    print("\n" + "="*60)
    print("🔬 DAC HARDWARE TEST")
    print("="*60)
    
    # Test sequence
    test_voltages = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    
    print("\n📋 Manual measurement instructions:")
    print("1. Connect DMM probe to PA4 (DAC Channel 1)")
    print("2. Press Enter to start test")
    input("Press Enter to continue...")
    
    print("\n🔍 Testing DAC Channel 1 (PA4):")
    print("Voltage_Set | DMM_Reading | Difference")
    print("-" * 40)
    
    for voltage in test_voltages:
        # Send SCPI command
        cmd = f'SOUR:VOLT:DC {voltage}\r\n'
        stm32.write(cmd.encode())
        time.sleep(0.5)
        
        # Read response
        response = stm32.readline().decode().strip()
        print(f"STM32 response: {response}")
        
        # Measure with DMM
        try:
            dmm_reading = float(dmm.query("READ?"))
            difference = dmm_reading - voltage
            
            print(f"{voltage:8.3f}V | {dmm_reading:10.6f}V | {difference:+8.6f}V")
            
        except Exception as e:
            print(f"DMM read error: {e}")
        
        time.sleep(1)
    
    print("\n" + "="*60)
    print("Now move DMM probe to PA5 (DAC Channel 2)")
    input("Press Enter when ready...")
    
    print("\n🔍 Testing DAC Channel 2 (PA5):")
    print("Voltage_Set | DMM_Reading | Difference")
    print("-" * 40)
    
    for voltage in test_voltages:
        # Note: Need to check if there's a separate command for Channel 2
        cmd = f'SOUR:VOLT:DC {voltage}\r\n'  # May need different command
        stm32.write(cmd.encode())
        time.sleep(0.5)
        
        response = stm32.readline().decode().strip()
        print(f"STM32 response: {response}")
        
        try:
            dmm_reading = float(dmm.query("READ?"))
            difference = dmm_reading - voltage
            
            print(f"{voltage:8.3f}V | {dmm_reading:10.6f}V | {difference:+8.6f}V")
            
        except Exception as e:
            print(f"DMM read error: {e}")
        
        time.sleep(1)
    
    # Check if DAC is stuck at a fixed voltage
    print("\n🔍 Quick voltage stability test:")
    for i in range(5):
        dmm_reading = float(dmm.query("READ?"))
        print(f"Reading {i+1}: {dmm_reading:.6f}V")
        time.sleep(0.5)
    
    # Cleanup
    stm32.close()
    dmm.close()
    rm.close()
    
    print("\n✅ Hardware test completed")
    return True

if __name__ == "__main__":
    test_dac_hardware()