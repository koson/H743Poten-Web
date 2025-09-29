#!/usr/bin/env python3
"""
DPV STM32 Communication Test
Test if STM32 is sending DPV data correctly
"""

import sys
import os
import time
import json
from datetime import datetime

# Add project path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from hardware.scpi_handler import SCPIHandler
    from services.dpv_measurement_service import DPVMeasurementService, DPVParameters
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

def test_stm32_connection():
    """Test basic STM32 connection"""
    
    print("🔌 Testing STM32 Connection...")
    print("=" * 50)
    
    # Try different common ports
    ports_to_try = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']
    
    scpi_handler = None
    
    for port in ports_to_try:
        try:
            print(f"🔍 Trying port: {port}")
            scpi_handler = SCPIHandler(port, 115200)
            
            # Test basic communication
            result = scpi_handler.send_custom_command("*IDN?")
            if result['success']:
                print(f"✅ Connected to STM32 on {port}")
                print(f"📝 Device ID: {result['response']}")
                return scpi_handler
            else:
                print(f"❌ No response from {port}")
                
        except Exception as e:
            print(f"❌ Error with {port}: {e}")
            continue
    
    print("❌ No STM32 found on any port")
    return None

def test_dpv_commands(scpi_handler):
    """Test DPV SCPI commands"""
    
    print("\n🧪 Testing DPV Commands...")
    print("=" * 50)
    
    # Test current range command
    print("📡 Setting current range...")
    range_result = scpi_handler.send_custom_command("POTEn:CURRent:RANGe 2")
    print(f"Current range result: {range_result}")
    
    # Test DPV setup command
    print("📡 Sending DPV setup command...")
    dpv_command = "POTEn:DPV:Start:ALL -0.5,0.5,0.05,0.01,0.05,0.1"
    setup_result = scpi_handler.send_custom_command(dpv_command)
    print(f"DPV setup result: {setup_result}")
    
    if not setup_result['success']:
        print("❌ DPV setup failed, stopping test")
        return False
        
    print("✅ DPV setup successful")
    return True

def test_dpv_data_collection(scpi_handler):
    """Test DPV data collection"""
    
    print("\n📊 Testing DPV Data Collection...")
    print("=" * 50)
    
    data_received = False
    max_attempts = 20
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"🔍 Attempt {attempt}/{max_attempts} - Checking for data...")
        
        # Check for data
        data_result = scpi_handler.send_custom_command("POTEn:DPV:DATA?")
        
        if data_result['success'] and data_result['response'].strip():
            print(f"✅ Data received!")
            print(f"📄 Raw data (first 200 chars): {data_result['response'][:200]}...")
            
            # Try to parse the data
            lines = data_result['response'].strip().split('\n')
            valid_lines = 0
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and 'Point, Time' not in line:
                    parts = [part.strip() for part in line.split(',')]
                    if len(parts) >= 7 and parts[0].upper() == 'DPV':
                        valid_lines += 1
                        if valid_lines <= 3:  # Show first 3 data points
                            print(f"📈 Data point: {line}")
            
            print(f"📊 Found {valid_lines} valid DPV data points")
            data_received = True
            break
            
        else:
            print(f"⏳ No data yet... (waiting 2s)")
            time.sleep(2)
    
    if not data_received:
        print("❌ No data received after maximum attempts")
        
        # Check status
        status_result = scpi_handler.send_custom_command("POTEn:DPV:STATUS?")
        if status_result['success']:
            print(f"📋 DPV Status: {status_result['response']}")
    
    return data_received

def test_dpv_service_integration(scpi_handler):
    """Test DPV service integration"""
    
    print("\n🔧 Testing DPV Service Integration...")
    print("=" * 50)
    
    try:
        # Create DPV service
        dpv_service = DPVMeasurementService(scpi_handler)
        
        # Setup measurement parameters
        params = {
            'start_potential': -0.5,
            'end_potential': 0.5,
            'pulse_height': 0.05,
            'pulse_increment': 0.01,
            'pulse_width': 0.05,
            'pulse_period': 0.1,
            'current_range': 2
        }
        
        print("🔧 Setting up DPV measurement...")
        setup_success = dpv_service.setup_measurement(params)
        
        if not setup_success:
            print("❌ DPV service setup failed")
            return False
        
        print("✅ DPV service setup successful")
        
        # Start measurement
        print("🚀 Starting DPV measurement...")
        start_success = dpv_service.start_measurement()
        
        if not start_success:
            print("❌ DPV service start failed")
            return False
            
        print("✅ DPV measurement started")
        
        # Check for data through service
        print("📊 Checking for data through service...")
        for i in range(10):
            data = dpv_service.get_measurement_data()
            
            if data['points']:
                print(f"✅ Service received {len(data['points'])} data points")
                if len(data['points']) > 0:
                    first_point = data['points'][0]
                    print(f"📈 First point: V={first_point.get('potential', 'N/A')}V, I={first_point.get('current', 'N/A')}µA")
                return True
            else:
                print(f"⏳ No data yet (attempt {i+1}/10)...")
                time.sleep(2)
        
        print("❌ No data received through service")
        return False
        
    except Exception as e:
        print(f"❌ Service integration error: {e}")
        return False

def main():
    """Main test function"""
    
    print("🧪 STM32 DPV Communication Test")
    print("=" * 50)
    print(f"📅 Test started at: {datetime.now()}")
    
    # Test 1: Connection
    scpi_handler = test_stm32_connection()
    if not scpi_handler:
        print("\n❌ Cannot proceed without STM32 connection")
        return
    
    # Test 2: Commands
    commands_ok = test_dpv_commands(scpi_handler)
    if not commands_ok:
        print("\n❌ Cannot proceed with failed commands")
        return
    
    # Test 3: Data collection  
    data_ok = test_dpv_data_collection(scpi_handler)
    
    # Test 4: Service integration
    service_ok = test_dpv_service_integration(scpi_handler)
    
    # Summary
    print("\n📋 Test Summary:")
    print("=" * 50)
    print(f"🔌 Connection: {'✅ PASS' if scpi_handler else '❌ FAIL'}")
    print(f"📡 Commands: {'✅ PASS' if commands_ok else '❌ FAIL'}")
    print(f"📊 Data Collection: {'✅ PASS' if data_ok else '❌ FAIL'}")
    print(f"🔧 Service Integration: {'✅ PASS' if service_ok else '❌ FAIL'}")
    
    if data_ok and service_ok:
        print("\n🎉 All tests passed! STM32 is sending DPV data correctly.")
    else:
        print("\n⚠️ Some tests failed. Check STM32 connection and firmware.")

if __name__ == "__main__":
    main()