#!/usr/bin/env python3
"""
Remote SCPI Testing Script
Test SCPI commands on Linux server via SSH
"""

import subprocess
import time
import sys

# Remote server configuration
REMOTE_HOST = "koson@192.168.9.76"
REMOTE_DIR = "h743poten-web"
PYTHON_ENV = "poten-env/bin/activate"

def run_remote_command(command, description=""):
    """Run command on remote server via SSH"""
    print(f"\n🔄 {description}")
    print(f"📡 Command: {command}")
    
    # Build SSH command
    ssh_cmd = [
        "ssh", REMOTE_HOST,
        f"cd {REMOTE_DIR} && source {PYTHON_ENV} && {command}"
    ]
    
    try:
        # Execute SSH command
        result = subprocess.run(ssh_cmd, 
                              capture_output=True, 
                              text=True, 
                              timeout=30)
        
        if result.returncode == 0:
            print(f"✅ Success:")
            print(result.stdout)
        else:
            print(f"❌ Error (code {result.returncode}):")
            print(result.stderr)
            
        return result.returncode == 0, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print("⏰ Command timed out (30s)")
        return False, "", "Timeout"
    except Exception as e:
        print(f"💥 Exception: {e}")
        return False, "", str(e)

def test_scpi_commands():
    """Test SCPI commands remotely"""
    print("🧪 Remote SCPI Testing")
    print("=" * 60)
    
    # Test 1: Basic connection
    python_test = """
import sys
sys.path.append('src')
from hardware.scpi_handler import SCPIHandler

scpi = SCPIHandler('/dev/ttyACM0', 115200)
if scpi.connect():
    print('✅ Connected to STM32')
    
    # Test ID
    idn = scpi.send_custom_command('*IDN?')
    print(f'Device: {idn.get("response", "")}')
    
    # Test CV STATUS
    cv_status = scpi.send_custom_command('POTEn:CV:STATUS?')
    print(f'CV STATUS: "{cv_status.get("response", "")}"')
    
    # Test CV START
    cv_start = scpi.send_custom_command('POTEn:CV:Start:ALL -0.5,0.5,0.1,1')
    print(f'CV START: {cv_start.get("response", "")}')
    
    import time
    time.sleep(2)
    
    # Test CV DATA after start
    cv_data = scpi.send_custom_command('POTEn:CV:DATA?')
    cv_response = cv_data.get('response', '')
    print(f'CV DATA: {len(cv_response)} chars')
    if len(cv_response) > 0:
        print(f'Preview: {cv_response[:100]}...')
    
else:
    print('❌ Cannot connect to STM32')
"""
    
    success, stdout, stderr = run_remote_command(
        f'python -c "{python_test}"',
        "Testing Basic SCPI Commands"
    )
    
    return success

def test_web_interface():
    """Test web interface"""
    print("\n🌐 Testing Web Interface")
    print("=" * 60)
    
    # Start web server in background
    start_server = "python main_dev.py &"
    run_remote_command(start_server, "Starting Web Server")
    
    time.sleep(5)  # Wait for server to start
    
    # Test API
    api_test = """
import requests
import time

try:
    # Connect to STM32
    connect_response = requests.post('http://localhost:8080/api/connection/connect', 
                                   json={'port': '/dev/ttyACM0', 'baud_rate': 115200}, 
                                   timeout=10)
    print(f'Connect Status: {connect_response.status_code}')
    
    if connect_response.status_code == 200:
        # Start CV measurement
        cv_params = {
            'initial_potential': -0.5,
            'final_potential': 0.5, 
            'switch_potential': 0.5,
            'scan_rate': 0.1,
            'current_range': 2,
            'cycles': 1
        }
        
        start_response = requests.post('http://localhost:8080/api/measurements/cv/start',
                                     json=cv_params, timeout=15)
        print(f'CV Start Status: {start_response.status_code}')
        
        if start_response.status_code == 200:
            print('✅ CV measurement started via web interface')
            
            # Check data
            time.sleep(3)
            data_response = requests.get('http://localhost:8080/api/measurements/cv/data', timeout=5)
            data = data_response.json()
            points = data.get('points', [])
            print(f'Data points received: {len(points)}')
            
        else:
            print(f'❌ CV start failed: {start_response.text}')
    else:
        print(f'❌ Connection failed: {connect_response.text}')
        
except Exception as e:
    print(f'❌ API test error: {e}')
"""
    
    success, stdout, stderr = run_remote_command(
        f'python -c "{api_test}"',
        "Testing Web API"
    )
    
    return success

def main():
    """Main test function"""
    print("🚀 Remote STM32 Testing Suite")
    print("=" * 60)
    print(f"🖥️  Remote Host: {REMOTE_HOST}")
    print(f"📁 Remote Directory: {REMOTE_DIR}")
    print("=" * 60)
    
    # Test SCPI commands
    scpi_success = test_scpi_commands()
    
    # Test web interface
    web_success = test_web_interface()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 60)
    print(f"SCPI Commands: {'✅ PASS' if scpi_success else '❌ FAIL'}")
    print(f"Web Interface: {'✅ PASS' if web_success else '❌ FAIL'}")
    
    if scpi_success and web_success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())