#!/usr/bin/env python3
"""
Complete STM32 H743 Electrochemical Testing Suite
================================================

🎯 Mission: Test ALL measurement modes before morning!
- CV (Cyclic Voltammetry) ✅ WORKING
- DPV (Differential Pulse Voltammetry) 🧪 TESTING
- SWV (Square Wave Voltammetry) ✅ COMMANDS PARSED
- CA (Chronoamperometry) 🧪 TESTING

Author: GitHub Copilot + User's Focus Mission
Date: September 30, 2025 - Night Before Morning Deployment
"""

import requests
import time
import json
from typing import Dict, List, Any

class STM32CompleteTester:
    """Complete testing suite for STM32 H743 electrochemical modes"""
    
    def __init__(self, server_url: str = "http://192.168.9.76:8094"):
        self.server_url = server_url
        self.test_results = {}
        
    def send_command(self, command: str, wait_time: float = 3.0) -> Dict[str, Any]:
        """Send SCPI command to STM32 via server"""
        try:
            response = requests.post(
                f"{self.server_url}/command",
                json={
                    "command": command,
                    "wait_time": wait_time
                },
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def check_device_status(self) -> bool:
        """Check if STM32 is connected and ready"""
        try:
            response = requests.get(f"{self.server_url}/status", timeout=5)
            data = response.json()
            return data.get("device_connected", False)
        except:
            return False
    
    def test_cv_modes(self) -> Dict[str, Any]:
        """Test Cyclic Voltammetry variations"""
        print("🔬 Testing CV (Cyclic Voltammetry) Modes...")
        
        cv_tests = [
            {
                "name": "Basic CV",
                "command": "POTEn:CV:Stream:START -1.0,1.0,0.0,0.1,1",
                "description": "Standard CV scan"
            },
            {
                "name": "Fast CV",
                "command": "POTEn:CV:Stream:START -0.5,0.5,0.0,0.2,1",
                "description": "High scan rate CV"
            },
            {
                "name": "Multi-cycle CV",
                "command": "POTEn:CV:Stream:START -0.8,0.8,0.0,0.05,3",
                "description": "Multiple cycle CV"
            }
        ]
        
        results = {}
        for test in cv_tests:
            print(f"  📋 {test['name']}: {test['description']}")
            result = self.send_command(test['command'], wait_time=2.0)
            results[test['name']] = result
            
            if result.get('success'):
                print(f"    ✅ Command sent successfully")
                # Stop streaming after test
                stop_result = self.send_command("POTEn:CV:Stream:STOP", wait_time=1.0)
                time.sleep(1)
            else:
                print(f"    ❌ Failed: {result.get('error', 'Unknown error')}")
        
        return results
    
    def test_dpv_modes(self) -> Dict[str, Any]:
        """Test Differential Pulse Voltammetry variations"""
        print("🔬 Testing DPV (Differential Pulse Voltammetry) Modes...")
        
        dpv_tests = [
            {
                "name": "Basic DPV",
                "command": "POTEn:DPV:Start:ALL -0.5,0.5,0.004,0.05,0.05,0.017,0.2",
                "description": "Standard DPV parameters"
            },
            {
                "name": "High Resolution DPV",
                "command": "POTEn:DPV:Start:ALL -0.8,0.8,0.002,0.025,0.05,0.017,0.15",
                "description": "Fine step size DPV"
            },
            {
                "name": "Fast DPV",
                "command": "POTEn:DPV:Start:ALL -0.3,0.3,0.01,0.05,0.03,0.01,0.1",
                "description": "Quick DPV scan"
            }
        ]
        
        results = {}
        for test in dpv_tests:
            print(f"  📋 {test['name']}: {test['description']}")
            result = self.send_command(test['command'], wait_time=3.0)
            results[test['name']] = result
            
            if result.get('success'):
                print(f"    ✅ Command sent successfully")
                if result.get('response'):
                    print(f"    📥 Response: {result['response'][:100]}...")
            else:
                print(f"    ❌ Failed: {result.get('error', 'Unknown error')}")
            
            time.sleep(2)
        
        return results
    
    def test_swv_modes(self) -> Dict[str, Any]:
        """Test Square Wave Voltammetry variations"""
        print("🔬 Testing SWV (Square Wave Voltammetry) Modes...")
        
        swv_tests = [
            {
                "name": "Basic SWV",
                "command": "POTEn:SWV:Start:ALL -0.5,0.5,0.01,0.05,10,0,0,0,0",
                "description": "Simple SWV without preconcentration"
            },
            {
                "name": "SWV with Preconcentration",
                "command": "POTEn:SWV:Start:ALL -0.5,0.5,0.005,0.05,5,1,-1.0,30,5",
                "description": "SWV with 30s preconcentration"
            },
            {
                "name": "High Frequency SWV",
                "command": "POTEn:SWV:Start:ALL -0.3,0.3,0.01,0.025,25,0,0,0,2",
                "description": "Fast SWV scan"
            }
        ]
        
        results = {}
        for test in swv_tests:
            print(f"  📋 {test['name']}: {test['description']}")
            result = self.send_command(test['command'], wait_time=3.0)
            results[test['name']] = result
            
            if result.get('success'):
                print(f"    ✅ Command sent successfully")
                if result.get('response'):
                    print(f"    📥 Response: {result['response'][:150]}...")
            else:
                print(f"    ❌ Failed: {result.get('error', 'Unknown error')}")
            
            time.sleep(2)
        
        return results
    
    def test_ca_modes(self) -> Dict[str, Any]:
        """Test Chronoamperometry variations"""
        print("🔬 Testing CA (Chronoamperometry) Modes...")
        
        ca_tests = [
            {
                "name": "Short CA",
                "command": "POTEn:CA:START -0.5,10",
                "description": "10 second chronoamperometry"
            },
            {
                "name": "Standard CA",
                "command": "POTEn:CA:START -0.8,60",
                "description": "1 minute chronoamperometry"
            },
            {
                "name": "Positive Potential CA",
                "command": "POTEn:CA:START 0.5,30",
                "description": "Positive potential CA"
            },
            {
                "name": "CA Alternative Format",
                "command": "POTEn:CA -0.3,45",
                "description": "Alternative CA command format"
            }
        ]
        
        results = {}
        for test in ca_tests:
            print(f"  📋 {test['name']}: {test['description']}")
            result = self.send_command(test['command'], wait_time=3.0)
            results[test['name']] = result
            
            if result.get('success'):
                print(f"    ✅ Command sent successfully")
                if result.get('response'):
                    print(f"    📥 Response: {result['response'][:100]}...")
            else:
                print(f"    ❌ Failed: {result.get('error', 'Unknown error')}")
            
            time.sleep(2)
        
        return results
    
    def test_device_queries(self) -> Dict[str, Any]:
        """Test device information and status queries"""
        print("🔬 Testing Device Information Queries...")
        
        query_tests = [
            {
                "name": "Device ID",
                "command": "*IDN?",
                "description": "Device identification"
            },
            {
                "name": "System Status",
                "command": "*STATUS?",
                "description": "System status query"
            },
            {
                "name": "Error Check",
                "command": "*ERR?",
                "description": "Error status check"
            },
            {
                "name": "CV Status",
                "command": "POTEn:CV:Stream:STATUS?",
                "description": "CV streaming status"
            }
        ]
        
        results = {}
        for test in query_tests:
            print(f"  📋 {test['name']}: {test['description']}")
            result = self.send_command(test['command'], wait_time=2.0)
            results[test['name']] = result
            
            if result.get('success'):
                print(f"    ✅ Query successful")
                if result.get('response'):
                    print(f"    📥 Response: {result['response']}")
            else:
                print(f"    ❌ Failed: {result.get('error', 'Unknown error')}")
            
            time.sleep(1)
        
        return results
    
    def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run complete testing suite for all electrochemical modes"""
        print("🚀 Starting Complete STM32 H743 Electrochemical Testing Suite")
        print("=" * 60)
        
        # Check device status first
        if not self.check_device_status():
            print("❌ STM32 device not connected or not responding!")
            return {"error": "Device not available"}
        
        print("✅ STM32 H743 connected and ready")
        print()
        
        # Run all tests
        self.test_results = {
            "device_queries": self.test_device_queries(),
            "cv_modes": self.test_cv_modes(),
            "dpv_modes": self.test_dpv_modes(),
            "swv_modes": self.test_swv_modes(),
            "ca_modes": self.test_ca_modes()
        }
        
        # Generate summary
        self.generate_test_summary()
        
        return self.test_results
    
    def generate_test_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 COMPLETE TEST SUMMARY")
        print("=" * 60)
        
        total_tests = 0
        successful_tests = 0
        
        for category, tests in self.test_results.items():
            if isinstance(tests, dict):
                category_success = 0
                category_total = len(tests)
                total_tests += category_total
                
                print(f"\n🔬 {category.upper().replace('_', ' ')}:")
                
                for test_name, result in tests.items():
                    if result.get('success'):
                        print(f"  ✅ {test_name}")
                        category_success += 1
                        successful_tests += 1
                    else:
                        print(f"  ❌ {test_name}: {result.get('error', 'Unknown error')}")
                
                success_rate = (category_success / category_total) * 100 if category_total > 0 else 0
                print(f"  📊 Success Rate: {category_success}/{category_total} ({success_rate:.1f}%)")
        
        overall_success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"  📈 Total Tests: {total_tests}")
        print(f"  ✅ Successful: {successful_tests}")
        print(f"  ❌ Failed: {total_tests - successful_tests}")
        print(f"  📊 Success Rate: {overall_success_rate:.1f}%")
        
        if overall_success_rate >= 80:
            print("\n🎉 EXCELLENT! STM32 H743 ready for morning deployment!")
        elif overall_success_rate >= 60:
            print("\n👍 GOOD! Most functions working, minor issues to fix")
        else:
            print("\n⚠️ NEEDS WORK! Several issues need attention before deployment")
        
        print("=" * 60)

def main():
    """Main testing function"""
    tester = STM32CompleteTester()
    results = tester.run_complete_test_suite()
    
    # Save results to file
    with open('stm32_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: stm32_test_results.json")

if __name__ == "__main__":
    main()