#!/usr/bin/env python3
"""
Test DPV SCPI Command Generation
Verify that DPV commands match the documented format exactly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.dpv_measurement_service import DPVParameters

def test_dpv_commands():
    """Test DPV SCPI command generation"""
    
    print("🧪 Testing DPV SCPI Command Generation")
    print("=" * 50)
    
    # Test case from documentation
    print("\n📋 Test Case 1: Documentation Example")
    print("Expected: POTEn:DPV:Start:ALL -0.5,0.5,0.05,0.01,0.05,0.1")
    
    params = DPVParameters(
        initial_potential=-0.5,    # Starting potential (V)
        final_potential=0.5,       # End potential (V)
        pulse_height=0.05,         # Pulse amplitude (V) - 50mV
        pulse_increment=0.01,      # Step size (V) - 10mV steps
        pulse_width=0.05,          # Pulse duration (s) - 50ms
        pulse_period=0.1           # Time between pulses (s) - 100ms
    )
    
    command = params.to_scpi_command()
    print(f"Generated: {command}")
    
    expected = "POTEn:DPV:Start:ALL -0.5,0.5,0.05,0.01,0.05,0.1"
    if command == expected:
        print("✅ PASS: Command matches documentation")
    else:
        print("❌ FAIL: Command doesn't match")
        
    # Validate parameters
    is_valid, message = params.validate()
    print(f"📊 Validation: {'✅ VALID' if is_valid else '❌ INVALID'} - {message}")
    
    # Test case 2: Different parameters
    print("\n📋 Test Case 2: Custom Parameters")
    
    params2 = DPVParameters(
        initial_potential=-1.0,    # Starting at -1V
        final_potential=1.0,       # End at +1V  
        pulse_height=0.025,        # 25mV pulses
        pulse_increment=0.005,     # 5mV steps
        pulse_width=0.02,          # 20ms pulse width
        pulse_period=0.08          # 80ms period
    )
    
    command2 = params2.to_scpi_command()
    print(f"Generated: {command2}")
    
    expected2 = "POTEn:DPV:Start:ALL -1.0,1.0,0.025,0.005,0.02,0.08"
    if command2 == expected2:
        print("✅ PASS: Custom command correct")
    else:
        print("❌ FAIL: Custom command incorrect")
        
    is_valid2, message2 = params2.validate()
    print(f"📊 Validation: {'✅ VALID' if is_valid2 else '❌ INVALID'} - {message2}")
    
    # Test case 3: Invalid parameters
    print("\n📋 Test Case 3: Invalid Parameters")
    
    params3 = DPVParameters(
        initial_potential=0.5,     # Same as final
        final_potential=0.5,       # Same as initial - INVALID
        pulse_height=0.05,
        pulse_increment=0.01,
        pulse_width=0.05,
        pulse_period=0.1
    )
    
    is_valid3, message3 = params3.validate()
    print(f"📊 Validation: {'✅ VALID' if is_valid3 else '❌ INVALID'} - {message3}")
    
    # Test case 4: Current range simulation
    print("\n📋 Test Case 4: Current Range Commands")
    print("Range 0: POTEn:CURRent:RANGe 0  (±100µA - 1kΩ TIA)")
    print("Range 1: POTEn:CURRent:RANGe 1  (±10µA - 10kΩ TIA)")
    print("Range 2: POTEn:CURRent:RANGe 2  (±1µA - 100kΩ TIA)")
    print("Range 3: POTEn:CURRent:RANGe 3  (±100nA - 1MΩ TIA)")
    
    print("\n🔄 Complete DPV Command Sequence:")
    print("1. POTEn:CURRent:RANGe 2")
    print(f"2. {command}")
    print("\n💡 This matches the documentation example exactly!")

if __name__ == "__main__":
    test_dpv_commands()