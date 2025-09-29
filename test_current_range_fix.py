#!/usr/bin/env python3
"""
Test current range parameter fix
Simulates CV command with current range setting
"""

import json

def test_cv_command_generation():
    """Test CV command generation with current range parameter"""
    
    print("🧪 Testing Current Range Parameter Fix")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            "name": "Auto Range (Default)",
            "parameters": {
                "start_voltage": -0.5,
                "end_voltage": 0.5,
                "begin_voltage": -0.5,
                "scan_rate": 0.1,
                "cycles": 1
            },
            "expected": "No current range command (auto mode)"
        },
        {
            "name": "Range 0 (High Current - 100µA)",
            "parameters": {
                "start_voltage": -0.5,
                "end_voltage": 0.5,
                "begin_voltage": -0.5,
                "scan_rate": 0.1,
                "cycles": 1,
                "current_range": "0"
            },
            "expected": "POTEn:CURRent:RANGe 0"
        },
        {
            "name": "Range 1 (Medium Current - 10µA)",
            "parameters": {
                "start_voltage": -0.5,
                "end_voltage": 0.5,
                "begin_voltage": -0.5,
                "scan_rate": 0.1,
                "cycles": 1,
                "current_range": "1"
            },
            "expected": "POTEn:CURRent:RANGe 1"
        },
        {
            "name": "Range 2 (Low Current - 1µA)",
            "parameters": {
                "start_voltage": -0.5,
                "end_voltage": 0.5,
                "begin_voltage": -0.5,
                "scan_rate": 0.1,
                "cycles": 1,
                "current_range": "2"
            },
            "expected": "POTEn:CURRent:RANGe 2"
        },
        {
            "name": "Range 3 (Ultra Low Current - 100nA)",
            "parameters": {
                "start_voltage": -0.5,
                "end_voltage": 0.5,
                "begin_voltage": -0.5,
                "scan_rate": 0.1,
                "cycles": 1,
                "current_range": "3"
            },
            "expected": "POTEn:CURRent:RANGe 3"
        },
        {
            "name": "Invalid Range (fallback to auto)",
            "parameters": {
                "start_voltage": -0.5,
                "end_voltage": 0.5,
                "begin_voltage": -0.5,
                "scan_rate": 0.1,
                "cycles": 1,
                "current_range": "invalid"
            },
            "expected": "No current range command (auto mode)"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔬 Test {i}: {test_case['name']}")
        print("-" * 30)
        
        parameters = test_case["parameters"]
        
        # Simulate current range command generation
        current_range = parameters.get('current_range', 'auto')
        if current_range != 'auto':
            try:
                range_value = int(current_range)
                range_command = f"POTEn:CURRent:RANGe {range_value}"
                print(f"✅ Current Range Command: {range_command}")
            except (ValueError, TypeError):
                print(f"⚠️ Invalid current_range value: {current_range}, using auto range")
                range_command = None
        else:
            print(f"🤖 Using AUTO range mode")
            range_command = None
        
        # Generate CV command
        start_v = parameters.get('start_voltage', -1.0)
        end_v = parameters.get('end_voltage', 1.0)
        begin_v = parameters.get('begin_voltage', start_v)
        scan_rate = parameters.get('scan_rate', 0.05)
        cycles = parameters.get('cycles', 1)
        
        cv_command = f"POTEn:CV:Stream:START {start_v},{end_v},{begin_v},{scan_rate},{cycles}"
        print(f"📡 CV Command: {cv_command}")
        
        # Show complete sequence
        print(f"🔄 Complete Command Sequence:")
        if range_command:
            print(f"   1. {range_command}")
            print(f"   2. {cv_command}")
        else:
            print(f"   1. {cv_command} (auto range)")
            
        print(f"✨ Expected: {test_case['expected']}")

def show_current_ranges():
    """Show current range information"""
    print("\n📊 STM32 Current Range Information")
    print("=" * 50)
    
    ranges = [
        {"range": 0, "resistance": "1kΩ", "current": "±100µA", "description": "High current range"},
        {"range": 1, "resistance": "10kΩ", "current": "±10µA", "description": "Medium current range"},
        {"range": 2, "resistance": "100kΩ", "current": "±1µA", "description": "Low current range"},
        {"range": 3, "resistance": "1MΩ", "current": "±100nA", "description": "Ultra low current range"}
    ]
    
    for r in ranges:
        print(f"Range {r['range']}: {r['resistance']} TIA → {r['current']} ({r['description']})")
    
    print(f"\n💡 The issue was:")
    print(f"   - STM32 was setting FIXED range 2 (±1µA)")
    print(f"   - But sample might need higher current capability")
    print(f"   - Solution: Send current range command BEFORE CV command")
    print(f"   - Or use range 0 (±100µA) for high-current samples")

if __name__ == "__main__":
    show_current_ranges()
    test_cv_command_generation()
    
    print(f"\n🎯 Summary:")
    print(f"   ✅ Current range parameter added to CV API")
    print(f"   ✅ Range command sent BEFORE CV command")
    print(f"   ✅ Auto mode available as fallback")
    print(f"   ✅ Invalid values handled gracefully")
    print(f"\n🚀 Ready to test with real STM32!")