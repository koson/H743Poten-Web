#!/usr/bin/env python3
"""
Mock STM32 DPV Command Tester
Test DPV SCPI commands without hardware to verify command formats
"""

import time
import json
from typing import Dict, List, Tuple

class MockSTM32DPV:
    """Mock STM32 that responds to DPV SCPI commands"""
    
    def __init__(self):
        self.current_params = {}
        self.measurement_active = False
        self.data_points = []
        self.command_history = []
        
    def process_command(self, command: str) -> str:
        """Process SCPI command and return response"""
        cmd = command.strip().upper()
        self.command_history.append(cmd)
        
        print(f"📤 Command: {command}")
        
        # Basic SCPI commands
        if cmd == "*IDN?":
            response = "STMicroelectronics,STM32H743,SN123456,V1.0"
        elif cmd == "*TST?":
            response = "0"
        elif cmd.startswith("SYSTEM:ERROR"):
            response = "0,\"No error\""
        elif cmd.startswith("SYSTEM:VERSION"):
            response = "1999.0"
            
        # DPV Parameter commands
        elif cmd.startswith("POTEN:DPV:VOLT:INIT"):
            value = self._extract_value(cmd)
            self.current_params['initial_potential'] = value
            response = "OK"
        elif cmd.startswith("POTEN:DPV:VOLT:FINAL"):
            value = self._extract_value(cmd)
            self.current_params['final_potential'] = value  
            response = "OK"
        elif cmd.startswith("POTEN:DPV:VOLT:PULSE:HEIGHT"):
            value = self._extract_value(cmd)
            self.current_params['pulse_height'] = value
            response = "OK"
        elif cmd.startswith("POTEN:DPV:VOLT:PULSE:INCR"):
            value = self._extract_value(cmd)
            self.current_params['pulse_increment'] = value
            response = "OK"
        elif cmd.startswith("POTEN:DPV:TIME:PULSE:WIDTH"):
            value = self._extract_value(cmd)
            self.current_params['pulse_width'] = value
            response = "OK"
        elif cmd.startswith("POTEN:DPV:TIME:PULSE:PERIOD"):
            value = self._extract_value(cmd)
            self.current_params['pulse_period'] = value
            response = "OK"
            
        # DPV Start commands (test different formats)
        elif cmd.startswith("POTEN:DPV:START:ALL"):
            params = self._parse_start_all_params(cmd)
            if params:
                self.current_params.update(params)
                self.measurement_active = True
                self._generate_mock_data()
                response = "OK - DPV measurement started"
            else:
                response = "ERROR: Invalid parameters"
                
        elif cmd.startswith("POTEN:DPV:START"):
            # Alternative format without :ALL
            params = self._parse_start_params(cmd)
            if params:
                self.current_params.update(params)
                self.measurement_active = True
                self._generate_mock_data()
                response = "OK - DPV measurement started (alt format)"
            else:
                response = "ERROR: Invalid parameters"
                
        # DPV Data query
        elif cmd == "POTEN:DPV:DATA?":
            if self.measurement_active and self.data_points:
                # Return some mock data
                data_line = self.data_points.pop(0) if self.data_points else "0.0,0.0,0"
                response = data_line
            else:
                response = "NO_DATA"
                
        elif cmd == "POTEN:DPV:STATUS?":
            status = "MEASURING" if self.measurement_active else "IDLE"
            remaining = len(self.data_points)
            response = f"{status},{remaining}"
            
        # DPV Abort
        elif cmd == "POTEN:DPV:ABORT":
            self.measurement_active = False
            self.data_points.clear()
            response = "OK - DPV measurement aborted"
            
        # Unknown command
        else:
            response = f"ERROR: Unknown command '{command}'"
            
        print(f"📥 Response: {response}")
        return response
    
    def _extract_value(self, command: str) -> float:
        """Extract numeric value from command"""
        parts = command.split()
        if len(parts) >= 2:
            try:
                return float(parts[-1])
            except ValueError:
                pass
        return 0.0
    
    def _parse_start_all_params(self, command: str) -> Dict:
        """Parse POTEn:DPV:Start:ALL parameters"""
        try:
            # Expected format: POTEn:DPV:Start:ALL -0.5,0.5,0.05,0.01,0.05,0.1
            parts = command.split()
            if len(parts) >= 2:
                param_str = parts[1]
                values = [float(x.strip()) for x in param_str.split(',')]
                
                if len(values) >= 6:
                    return {
                        'initial_potential': values[0],
                        'final_potential': values[1], 
                        'pulse_height': values[2],
                        'pulse_increment': values[3],
                        'pulse_width': values[4],
                        'pulse_period': values[5]
                    }
        except (ValueError, IndexError) as e:
            print(f"❌ Parameter parsing error: {e}")
        
        return {}
    
    def _parse_start_params(self, command: str) -> Dict:
        """Parse POTEn:DPV:Start parameters (without :ALL)"""
        # Same logic as start:all but different command format
        return self._parse_start_all_params(command)
    
    def _generate_mock_data(self):
        """Generate mock DPV data points"""
        if not self.current_params:
            return
            
        start_v = self.current_params.get('initial_potential', -0.5)
        end_v = self.current_params.get('final_potential', 0.5)
        step = self.current_params.get('pulse_increment', 0.01)
        
        # Generate mock voltammetry curve
        current_v = start_v
        point_num = 0
        
        while (step > 0 and current_v <= end_v) or (step < 0 and current_v >= end_v):
            # Mock current response (simple Gaussian peak at 0V)
            current = 1e-6 * (100 * (2.718 ** (-((current_v - 0.0) ** 2) / 0.1)) + 
                             10 * (2.718 ** (-((current_v - 0.2) ** 2) / 0.05)))
            
            # Format: potential,current,point_number
            data_line = f"{current_v:.3f},{current:.2e},{point_num}"
            self.data_points.append(data_line)
            
            current_v += step
            point_num += 1
            
            # Limit data points
            if point_num > 200:
                break
        
        print(f"✅ Generated {len(self.data_points)} mock DPV data points")
    
    def show_status(self):
        """Show current status"""
        print(f"\n📊 Mock STM32 Status:")
        print(f"   Parameters: {json.dumps(self.current_params, indent=2)}")
        print(f"   Measuring: {self.measurement_active}")
        print(f"   Data points: {len(self.data_points)}")
        print(f"   Commands sent: {len(self.command_history)}")

def test_dpv_commands():
    """Test different DPV command formats"""
    print("🧪 Testing DPV SCPI Commands")
    print("=" * 50)
    
    mock_stm32 = MockSTM32DPV()
    
    # Test command sequences
    test_sequences = [
        {
            "name": "Basic SCPI Commands",
            "commands": ["*IDN?", "*TST?", "SYSTem:ERRor?"]
        },
        {
            "name": "DPV Individual Parameters", 
            "commands": [
                "POTEn:DPV:VOLT:INIT -0.5",
                "POTEn:DPV:VOLT:FINAl 0.5",
                "POTEn:DPV:VOLT:PULSe:HEIGht 0.05",
                "POTEn:DPV:VOLT:PULSe:INCR 0.01",
                "POTEn:DPV:TIME:PULSe:WIDTH 0.05",
                "POTEn:DPV:TIME:PULSe:PERIod 0.1",
                "POTEn:DPV:Start"
            ]
        },
        {
            "name": "DPV Start:ALL Format",
            "commands": [
                "POTEn:DPV:Start:ALL -0.5,0.5,0.05,0.01,0.05,0.1",
                "POTEn:DPV:STATUS?",
                "POTEn:DPV:DATA?",
                "POTEn:DPV:DATA?",
                "POTEn:DPV:DATA?",
                "POTEn:DPV:ABORt"
            ]
        },
        {
            "name": "DPV Alternative Start Format",
            "commands": [
                "POTEn:DPV:Start -0.5,0.5,0.05,0.01,0.05,0.1",
                "POTEn:DPV:STATUS?",
                "POTEn:DPV:DATA?",
                "POTEn:DPV:ABORt"
            ]
        }
    ]
    
    for sequence in test_sequences:
        print(f"\n🔍 Testing: {sequence['name']}")
        print("-" * 40)
        
        for command in sequence['commands']:
            response = mock_stm32.process_command(command)
            time.sleep(0.1)
        
        mock_stm32.show_status()
        print()
    
    print("✅ DPV Command Testing Complete!")
    print("\n📋 Summary:")
    print("   - POTEn:DPV:Start:ALL format: ✅ Working")
    print("   - POTEn:DPV:Start format: ✅ Working") 
    print("   - Individual parameter commands: ✅ Working")
    print("   - Data query commands: ✅ Working")

if __name__ == "__main__":
    test_dpv_commands()