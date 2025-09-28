#!/usr/bin/env python3
"""
SWV Command Test Script for STM32
Test Square Wave Voltammetry with enhanced parameters including preconcentration
"""

import serial
import time

def test_swv_commands(com_port: str):
    """Test different SWV command formats and parameters"""
    try:
        print(f"🔌 Connecting to {com_port} for SWV testing...")
        ser = serial.Serial(com_port, 115200, timeout=3)
        time.sleep(2)
        
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print("✅ Connected!")
        
        # Test SWV command formats
        swv_tests = [
            {
                "name": "Basic SWV Test",
                "command": "POTEn:SWV:Start:ALL -0.5,0.5,0.01,0.05,10,0,0,0,0",
                "description": "Simple SWV without preconcentration"
            },
            {
                "name": "SWV with Preconcentration (Short)",
                "command": "POTEn:SWV:Start:ALL -0.5,0.5,0.005,0.05,5,1,-1.0,30,5",
                "description": "SWV with 30s preconcentration (test mode)"
            },
            {
                "name": "SWV with Full Preconcentration", 
                "command": "POTEn:SWV:Start:ALL -1.0,0.5,0.005,0.05,5,1,-1.9,240,10",
                "description": "Full SWV with 240s preconcentration (lab mode)"
            },
            {
                "name": "High Frequency SWV",
                "command": "POTEn:SWV:Start:ALL -0.3,0.3,0.01,0.025,25,0,0,0,2",
                "description": "Fast SWV scan for quick testing"
            }
        ]
        
        for i, test in enumerate(swv_tests, 1):
            print(f"\n🧪 Test {i}: {test['name']}")
            print(f"📋 {test['description']}")
            print(f"📤 Command: {test['command']}")
            
            # Send command
            ser.write((test['command'] + '\n').encode())
            ser.flush()
            
            # Wait and collect initial response
            time.sleep(1)
            initial_response = ""
            if ser.in_waiting > 0:
                initial_response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                print(f"📥 Initial Response: {initial_response.strip()}")
            
            # Check for data over time (SWV with preconcentration takes time)
            if "preconc" in test['name'].lower():
                print("⏳ Preconcentration phase - checking for data...")
                
                for check in range(5):
                    time.sleep(2)
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                        if data.strip():
                            print(f"📊 Data chunk {check+1}: {data.strip()[:100]}...")
                            if 'Operation Finished' in data:
                                print("🏁 SWV completed!")
                                break
                
                # Send abort to stop if still running
                print("🛑 Sending abort...")
                ser.write(b'POTEn:SWV:ABORt\n')
                ser.flush()
                time.sleep(0.5)
            
            else:
                # For non-preconcentration tests, check data briefly
                print("📊 Checking for measurement data...")
                for check in range(3):
                    time.sleep(1)
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                        if data.strip():
                            print(f"📊 Data: {data.strip()[:200]}...")
                
                # Send abort
                ser.write(b'POTEn:SWV:ABORt\n')
                ser.flush()
            
            print("-" * 50)
        
        # Test individual SWV parameter commands
        print("\n🔧 Testing Individual SWV Parameter Commands:")
        individual_commands = [
            "POTEn:SWV:VOLT:INIT -0.5",
            "POTEn:SWV:VOLT:FINAl 0.5", 
            "POTEn:SWV:VOLT:STEP 0.01",
            "POTEn:SWV:VOLT:PULSe:HEIGht 0.05",
            "POTEn:SWV:FREQ 10",
            "POTEn:SWV:PREConc:ENABle 1",
            "POTEn:SWV:PREConc:POT1 -1.5",
            "POTEn:SWV:PREConc:TIME1 60",
            "POTEn:SWV:EQUIl:TIME 5",
            "POTEn:SWV:Start"
        ]
        
        for cmd in individual_commands:
            print(f"📤 {cmd}")
            ser.write((cmd + '\n').encode())
            ser.flush()
            time.sleep(0.3)
            
            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                print(f"📥 {response.strip()}")
        
        # Final abort
        ser.write(b'POTEn:SWV:ABORt\n')
        ser.flush()
        
        ser.close()
        print("\n✅ SWV Command Testing Complete!")
        
        # Summary
        print("\n📋 SWV Command Summary:")
        print("✅ POTEn:SWV:Start:ALL <begin>,<end>,<step>,<amp>,<freq>,<preconc_en>,<preconc_pot>,<preconc_time>,<equil_time>")
        print("✅ Individual parameter commands available")
        print("✅ Preconcentration support (0=disabled, 1=enabled)")
        print("✅ Configurable timing parameters")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def show_swv_parameters():
    """Show SWV parameter explanations"""
    print("📊 SWV Parameters Explained:")
    print("=" * 50)
    
    params = [
        ("begin", "Starting potential (V)", "-1.0"),
        ("end", "Ending potential (V)", "0.5"), 
        ("step", "Step potential (V)", "0.005"),
        ("amplitude", "Square wave amplitude (V)", "0.05"),
        ("frequency", "Frequency (Hz)", "5"),
        ("preconc_en", "Preconcentration enable (0/1)", "1"),
        ("preconc_pot", "Preconcentration potential (V)", "-1.9"),
        ("preconc_time", "Preconcentration time (s)", "240"),
        ("equil_time", "Equilibration time (s)", "5")
    ]
    
    for param, desc, example in params:
        print(f"  {param:12} - {desc:30} (e.g., {example})")
    
    print("\n🧪 Example Commands:")
    print("  Quick Test: POTEn:SWV:Start:ALL -0.5,0.5,0.01,0.05,10,0,0,0,0")
    print("  With Preconc: POTEn:SWV:Start:ALL -1.0,0.5,0.005,0.05,5,1,-1.9,240,10")
    print("  Test Mode: POTEn:SWV:Start:ALL -0.5,0.5,0.005,0.05,5,1,-1.0,30,5")

if __name__ == "__main__":
    print("🔬 SWV Parameter Testing Tool")
    print("=" * 50)
    
    show_swv_parameters()
    
    print(f"\n💡 To test with your STM32:")
    print(f"1. Find COM port in Device Manager")
    print(f"2. Edit this script: test_swv_commands('COMx')")
    print(f"3. Run the test")
    
    # Uncomment and modify this line with your COM port:
    # test_swv_commands('COM3')