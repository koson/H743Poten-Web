#!/bin/bash
# Quick Remote SCPI Test
# Usage: ./quick_test.sh

echo "🧪 Quick Remote SCPI Test"
echo "=========================="

# Test basic SCPI commands
ssh koson@192.168.9.76 'cd h743poten-web && source poten-env/bin/activate && python -c "
import sys
sys.path.append(\"src\")
from hardware.scpi_handler import SCPIHandler

print(\"📡 Testing SCPI Commands\")
scpi = SCPIHandler(\"/dev/ttyACM0\", 115200)
if scpi.connect():
    print(\"✅ Connected\")
    
    # Basic test
    idn = scpi.send_custom_command(\"*IDN?\")
    print(f\"ID: {idn.get(\\\"response\\\", \\\"\\\")}\")
    
    # CV test
    cv_status = scpi.send_custom_command(\"POTEn:CV:STATUS?\")
    print(f\"CV STATUS: {cv_status.get(\\\"response\\\", \\\"\\\")}\")
    
    cv_start = scpi.send_custom_command(\"POTEn:CV:Start:ALL -0.5,0.5,0.1,1\")
    print(f\"CV START: {cv_start.get(\\\"response\\\", \\\"\\\")}\")
    
    import time
    time.sleep(2)
    
    cv_data = scpi.send_custom_command(\"POTEn:CV:DATA?\")
    cv_resp = cv_data.get(\\\"response\\\", \\\"\\\")
    print(f\"CV DATA: {len(cv_resp)} chars - {cv_resp[:50]}...\")
    
else:
    print(\"❌ Cannot connect\")
"'