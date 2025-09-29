import serial
import time
try:
    ser = serial.Serial('/dev/ttyACM1', 115200, timeout=3)
    time.sleep(1.5)
    
    ser.write(b'*IDN?\r\n')
    ser.flush()
    time.sleep(1.2)
    
    response = ser.read_all().decode('utf-8', errors='ignore').strip()
    ser.close()
    
    print('SCPI_RESPONSE:', response)
except Exception as e:
    print('SCPI_ERROR:', str(e))
