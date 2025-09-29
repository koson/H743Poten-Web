#!/usr/bin/env python3
"""
Test the new CV SCPI commands integration
"""

import sys
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cv_scpi_commands():
    """Test CV SCPI commands with real hardware"""
    
    print("🔬 Testing New CV SCPI Commands")
    print("=" * 50)
    
    try:
        # Import required modules
        sys.path.append('src')
        try:
            from hardware.scpi_handler import SCPIHandler
        except ImportError:
            from src.hardware.scpi_handler import SCPIHandler
        
        # Try to connect to STM32
        ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0']
        scpi_handler = None
        
        for port in ports:
            try:
                print(f"Trying to connect to {port}...")
                scpi_handler = SCPIHandler(port, 115200)
                if scpi_handler.connect():
                    print(f"✅ Connected to STM32 at {port}")
                    break
            except Exception as e:
                print(f"❌ Failed to connect to {port}: {e}")
                continue
        
        if not scpi_handler or not scpi_handler.is_connected:
            print("❌ Could not connect to STM32")
            return
            
        # Test identity
        result = scpi_handler.send_custom_command("*IDN?")
        if result['success']:
            print(f"📡 STM32 Identity: {result['response']}")
        
        # Test CV commands in the correct sequence
        print("\n🔍 Testing CV Command Sequence")
        print("-" * 30)
        
        # 1. Check initial status
        print("1. Initial Status Check:")
        result = scpi_handler.send_custom_command("POTEn:CV:STATUS?")
        if result['success']:
            print(f"   Status: {result['response']}")
        else:
            print(f"   Error: {result['error']}")
            
        # 2. Start CV measurement
        print("\n2. Starting CV Measurement:")
        cv_command = "POTEn:CV:Start:ALL -1.0,1.0,-1.0,0.05,1"
        print(f"   Command: {cv_command}")
        result = scpi_handler.send_custom_command(cv_command)
        if result['success']:
            print(f"   Response: {result['response']}")
        else:
            print(f"   Error: {result['error']}")
            return
            
        # 3. Check status during measurement
        print("\n3. Status During Measurement:")
        for i in range(5):
            time.sleep(2)
            result = scpi_handler.send_custom_command("POTEn:CV:STATUS?")
            if result['success']:
                status = result['response'].strip()
                print(f"   Check {i+1}: {status}")
                if status == "COMPLETE":
                    break
            else:
                print(f"   Error: {result['error']}")
                
        # 4. Get measurement data
        print("\n4. Getting Measurement Data:")
        result = scpi_handler.send_custom_command("POTEn:CV:DATA?")
        if result['success']:
            data = result['response'].strip()
            if data:
                lines = data.split('\n')
                print(f"   Data lines received: {len(lines)}")
                print(f"   First few lines:")
                for line in lines[:5]:
                    print(f"     {line}")
                if len(lines) > 5:
                    print(f"   ... (showing 5 of {len(lines)} lines)")
            else:
                print("   No data received")
        else:
            print(f"   Error: {result['error']}")
            
        # 5. Final status check
        print("\n5. Final Status Check:")
        result = scpi_handler.send_custom_command("POTEn:CV:STATUS?")
        if result['success']:
            print(f"   Status: {result['response']}")
        else:
            print(f"   Error: {result['error']}")
            
        scpi_handler.disconnect()
        print("\n✅ CV SCPI test completed")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cv_scpi_commands()