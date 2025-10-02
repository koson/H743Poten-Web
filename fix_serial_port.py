import re
import sys

def find_serial_port():
    """ค้นหา serial port ที่ใช้ได้"""
    import glob
    import platform
    
    if platform.system() == "Windows":
        # Windows
        ports = ['COM{}'.format(i) for i in range(1, 20)]
        for port in ports:
            try:
                import serial
                ser = serial.Serial(port, 115200, timeout=1)
                ser.close()
                return port
            except:
                continue
    else:
        # Linux/Pi
        ports = glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')
        for port in ports:
            try:
                import serial
                ser = serial.Serial(port, 115200, timeout=1)
                ser.close()
                return port
            except:
                continue
    return None

# Read the file
with open('test_cv_final.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find available port
available_port = find_serial_port()
if available_port:
    print(f"Found available port: {available_port}")
    # Replace all COM ports with the available port
    content = re.sub(r"serial\.Serial\('COM\d+',", f"serial.Serial('{available_port}',", content)
    
    # Write back
    with open('test_cv_final.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated serial port configuration successfully!")
else:
    print("No available serial port found!")
    sys.exit(1)
