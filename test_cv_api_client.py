#!/usr/bin/env python3
"""
Simple API Test Client for STM32 CV Web API
Tests all endpoints and provides basic CV scan functionality
"""

import requests
import json
import time
import sys
from datetime import datetime

class STM32CVAPITester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        
    def test_connection(self):
        """Test if API server is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API server is running")
                return True
            else:
                print(f"❌ API server returned status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to API server: {e}")
            return False
    
    def get_status(self):
        """Get CV scan status"""
        try:
            response = requests.get(f"{self.base_url}/api/cv/status")
            if response.status_code == 200:
                status = response.json()
                print("📊 CV Status:")
                print(f"  Connected: {status.get('connected', False)}")
                print(f"  Running: {status.get('running', False)}")
                print(f"  Data Points: {status.get('dataPoints', 0)}")
                return status
            else:
                print(f"❌ Status check failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Status check error: {e}")
            return None
    
    def check_stm32_connection(self):
        """Check STM32 connection"""
        try:
            response = requests.get(f"{self.base_url}/api/stm32/status")
            if response.status_code == 200:
                status = response.json()
                print("🔗 STM32 Connection:")
                print(f"  Connected: {status.get('connected', False)}")
                print(f"  Message: {status.get('message', 'No message')}")
                return status.get('connected', False)
            else:
                print(f"❌ STM32 status check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ STM32 status error: {e}")
            return False
    
    def start_cv_scan(self, config=None):
        """Start CV scan with given configuration"""
        if config is None:
            config = {
                "beginVoltage": -1.0,
                "upperVoltage": 1.0,
                "lowerVoltage": -1.0,
                "scanRate": 0.05,
                "cycles": 3,
                "enableAutoRangeDebug": True
            }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/cv/start",
                json=config,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success', False):
                    print("✅ CV scan started successfully")
                    print(f"Config: {json.dumps(config, indent=2)}")
                    return True
                else:
                    print(f"❌ Failed to start CV scan: {result.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Start scan request failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Start scan error: {e}")
            return False
    
    def stop_cv_scan(self):
        """Stop CV scan"""
        try:
            response = requests.post(f"{self.base_url}/api/cv/stop")
            if response.status_code == 200:
                result = response.json()
                print("🛑 CV scan stopped")
                return True
            else:
                print(f"❌ Stop scan failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Stop scan error: {e}")
            return False
    
    def get_data(self, all_data=False):
        """Get CV data"""
        endpoint = "/api/cv/data/all" if all_data else "/api/cv/data"
        try:
            response = requests.get(f"{self.base_url}{endpoint}")
            if response.status_code == 200:
                result = response.json()
                data_points = result.get('dataPoints', [])
                count = result.get('count', len(data_points))
                
                print(f"📈 Data points: {count}")
                if count > 0 and data_points:
                    # Show sample data
                    sample = data_points[0]
                    print(f"Sample: V={sample.get('voltage', 0):.3f}V, I={sample.get('currentUA', 0):.2f}µA")
                
                return data_points
            else:
                print(f"❌ Get data failed: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Get data error: {e}")
            return []
    
    def clear_data(self):
        """Clear all CV data"""
        try:
            response = requests.post(f"{self.base_url}/api/cv/clear")
            if response.status_code == 200:
                print("🧹 Data cleared")
                return True
            else:
                print(f"❌ Clear data failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Clear data error: {e}")
            return False
    
    def run_test_scan(self, duration=30):
        """Run a test CV scan for specified duration"""
        print(f"\n🧪 Running test CV scan for {duration} seconds...")
        
        # Check connection first
        if not self.check_stm32_connection():
            print("❌ STM32 not connected - using simulation mode")
        
        # Start scan
        config = {
            "beginVoltage": -0.5,
            "upperVoltage": 0.5,
            "lowerVoltage": -0.5,
            "scanRate": 0.1,  # Faster for testing
            "cycles": 1,
            "enableAutoRangeDebug": True
        }
        
        if not self.start_cv_scan(config):
            return False
        
        # Monitor progress
        start_time = time.time()
        last_count = 0
        
        while time.time() - start_time < duration:
            status = self.get_status()
            if status and not status.get('running', False):
                print("✅ Scan completed naturally")
                break
            
            data_points = self.get_data()
            current_count = len(data_points)
            
            if current_count > last_count:
                print(f"  Progress: {current_count} points collected")
                last_count = current_count
            
            time.sleep(2)
        
        # Stop scan if still running
        if self.get_status() and self.get_status().get('running', False):
            self.stop_cv_scan()
        
        # Get final data
        final_data = self.get_data(all_data=True)
        print(f"✅ Test completed - Total points: {len(final_data)}")
        
        return True

def main():
    print("🔬 STM32 CV API Test Client")
    print("==========================")
    
    # Check if API server URL is provided
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    print(f"API Server: {api_url}")
    
    tester = STM32CVAPITester(api_url)
    
    # Test connection
    if not tester.test_connection():
        print("❌ Cannot connect to API server. Please start the server first.")
        print("Run: dotnet run --project STM32CVWebAPI.csproj")
        return 1
    
    try:
        while True:
            print("\n" + "="*50)
            print("📋 Test Menu:")
            print("1. Check Status")
            print("2. Check STM32 Connection")
            print("3. Start CV Scan")
            print("4. Stop CV Scan")
            print("5. Get Data")
            print("6. Clear Data")
            print("7. Run Test Scan (30s)")
            print("8. Open Web Interface")
            print("0. Exit")
            
            choice = input("\nSelect option (0-8): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                tester.get_status()
            elif choice == "2":
                tester.check_stm32_connection()
            elif choice == "3":
                tester.start_cv_scan()
            elif choice == "4":
                tester.stop_cv_scan()
            elif choice == "5":
                tester.get_data(all_data=True)
            elif choice == "6":
                tester.clear_data()
            elif choice == "7":
                tester.run_test_scan()
            elif choice == "8":
                print(f"🌐 Open in browser: {api_url}")
                try:
                    import webbrowser
                    webbrowser.open(api_url)
                except:
                    print("Cannot open browser automatically")
            else:
                print("❌ Invalid option")
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    
    return 0

if __name__ == "__main__":
    exit(main())