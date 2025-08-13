"""
Configuration settings for H743Poten Web Application
"""

class Config:
    # Web server settings
    WEB_HOST = '0.0.0.0'
    WEB_PORT = 8080
    DEBUG = False

    # Serial connection settings
    # Detect OS and set appropriate port
    import platform
    if platform.system() == 'Windows':
        SERIAL_PORT = 'COM3'  # Default Windows port, adjust if needed
    else:
        SERIAL_PORT = '/dev/ttyACM0'  # Default for Linux/RPi
    BAUD_RATE = 115200

    # Default measurement parameters
    DEFAULT_PARAMS = {
        'CV': {
            'start_voltage': -0.5,
            'end_voltage': 0.5,
            'scan_rate': 0.05,
            'step_size': 0.01
        },
        'DPV': {
            'start_voltage': -0.5,
            'end_voltage': 0.5,
            'pulse_amplitude': 0.05,
            'pulse_width': 0.01,
            'step_size': 0.01,
            'period': 0.1
        },
        'SWV': {
            'start_voltage': -0.5,
            'end_voltage': 0.5,
            'amplitude': 0.05,
            'frequency': 10,
            'step_size': 0.01
        },
        'CA': {
            'voltage': 0.5,
            'duration': 10
        }
    }
