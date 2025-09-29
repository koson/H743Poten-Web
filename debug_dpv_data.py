#!/usr/bin/env python3
"""
DPV Data Debug Script
Monitor and debug DPV data reception from STM32
"""

import sys
import os
import time
import json
from datetime import datetime

# Add project path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def debug_dpv_data_flow():
    """Debug DPV data flow step by step"""
    
    print("🔍 DPV Data Flow Debug")
    print("=" * 50)
    print(f"📅 Started at: {datetime.now()}")
    
    try:
        from hardware.scpi_handler import SCPIHandler
        from services.dpv_measurement_service import DPVMeasurementService
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Run this script from Pi in the project directory")
        return
    
    # Step 1: Test STM32 connection
    print("\n🔌 Step 1: Testing STM32 Connection")
    print("-" * 30)
    
    ports_to_try = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0']
    scpi_handler = None
    
    for port in ports_to_try:
        try:
            print(f"Trying {port}...")
            scpi_handler = SCPIHandler(port, 115200)
            
            if scpi_handler.connect():
                print(f"✅ Connected to {port}")
                break
            else:
                print(f"❌ Failed to connect to {port}")
        except Exception as e:
            print(f"❌ Error with {port}: {e}")
    
    if not scpi_handler or not scpi_handler.is_connected:
        print("❌ Cannot connect to STM32")
        return
    
    # Step 2: Test basic communication
    print("\n📡 Step 2: Testing Basic Communication")
    print("-" * 30)
    
    idn_result = scpi_handler.send_custom_command("*IDN?")
    print(f"ID Query: {idn_result}")
    
    # Step 3: Setup DPV
    print("\n🔧 Step 3: Setting up DPV")
    print("-" * 30)
    
    # Set current range
    range_result = scpi_handler.send_custom_command("POTEn:CURRent:RANGe 2")
    print(f"Current Range: {range_result}")
    
    # Send DPV command
    dpv_cmd = "POTEn:DPV:Start:ALL -0.5,0.5,0.05,0.01,0.05,0.1"
    print(f"DPV Command: {dpv_cmd}")
    dpv_result = scpi_handler.send_custom_command(dpv_cmd)
    print(f"DPV Setup: {dpv_result}")
    
    if not dpv_result.get('success', False):
        print("❌ DPV setup failed, stopping debug")
        return
    
    # Step 4: Monitor data reception methods
    print("\n📊 Step 4: Monitoring Data Reception")
    print("-" * 30)
    
    methods_tested = {
        'buffered_data': False,
        'data_query': False,
        'all_available': False,
        'raw_read': False
    }
    
    for attempt in range(20):  # 20 attempts over ~40 seconds
        print(f"\n🔍 Attempt {attempt + 1}/20:")
        
        # Method 1: Buffered data
        buffered = scpi_handler.get_buffered_data()
        if buffered and buffered.strip():
            print(f"✅ Buffered data: {len(buffered)} chars")
            print(f"   Preview: {buffered[:100]}...")
            methods_tested['buffered_data'] = True
        
        # Method 2: Data query
        data_result = scpi_handler.send_custom_command("POTEn:DPV:DATA?")
        if data_result.get('success') and data_result.get('response', '').strip():
            print(f"✅ Data query: {len(data_result['response'])} chars")
            print(f"   Preview: {data_result['response'][:100]}...")
            methods_tested['data_query'] = True
        
        # Method 3: All available data
        all_data = scpi_handler.get_all_available_data()
        if all_data and all_data.strip():
            print(f"✅ All available: {len(all_data)} chars")
            print(f"   Preview: {all_data[:100]}...")
            methods_tested['all_available'] = True
        
        # Method 4: Raw read
        raw_data = scpi_handler.read_raw_data(timeout=0.5)
        if raw_data and raw_data.strip():
            print(f"✅ Raw read: {len(raw_data)} chars")
            print(f"   Preview: {raw_data[:100]}...")
            methods_tested['raw_read'] = True
        
        # Check status
        status_result = scpi_handler.send_custom_command("POTEn:DPV:STATUS?")
        if status_result.get('success'):
            status = status_result['response'].strip()
            print(f"📊 Status: {status}")
            
            if 'COMPLETE' in status.upper() or 'FINISHED' in status.upper():
                print("🏁 DPV measurement completed")
                break
        
        if not any([buffered, 
                   data_result.get('response', '').strip(), 
                   all_data, 
                   raw_data]):
            print("❌ No data from any method")
        
        time.sleep(2)
    
    # Step 5: Test DPV service integration
    print("\n🔧 Step 5: Testing DPV Service")
    print("-" * 30)
    
    try:
        dpv_service = DPVMeasurementService(scpi_handler)
        
        # Setup parameters
        params = {
            'start_potential': -0.5,
            'end_potential': 0.5,
            'pulse_height': 0.05,
            'pulse_increment': 0.01, 
            'pulse_width': 0.05,
            'pulse_period': 0.1,
            'current_range': 2
        }
        
        print("Setting up DPV service...")
        setup_ok = dpv_service.setup_measurement(params)
        print(f"Setup result: {setup_ok}")
        
        if setup_ok:
            print("Starting measurement...")
            start_ok = dpv_service.start_measurement() 
            print(f"Start result: {start_ok}")
            
            if start_ok:
                print("Getting measurement data...")
                for i in range(5):
                    data = dpv_service.get_measurement_data()
                    print(f"Data attempt {i+1}: {len(data.get('points', []))} points, completed={data.get('completed', False)}")
                    if data.get('points'):
                        break
                    time.sleep(2)
        
    except Exception as e:
        print(f"❌ Service test error: {e}")
    
    # Summary
    print("\n📋 Debug Summary")
    print("=" * 50)
    print("Data reception methods tested:")
    for method, worked in methods_tested.items():
        status = "✅ WORKED" if worked else "❌ FAILED"
        print(f"  {method}: {status}")
    
    working_methods = sum(methods_tested.values())
    print(f"\nWorking methods: {working_methods}/4")
    
    if working_methods == 0:
        print("\n💡 Troubleshooting suggestions:")
        print("- Check STM32 firmware is running DPV correctly")
        print("- Verify serial connection is stable")
        print("- Check if STM32 is sending data to serial")
        print("- Try different baud rates or ports")
    elif working_methods < 4:
        print(f"\n💡 Some methods working ({working_methods}/4)")
        print("- System is partially functional")
        print("- May need to optimize data retrieval timing")
    else:
        print("\n🎉 All methods working!")
        print("- Data reception is functioning correctly")
        print("- Issue may be in the web interface or timing")

if __name__ == "__main__":
    debug_dpv_data_flow()