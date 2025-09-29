"""
Port Scanner for H743Poten
Scans available serial ports and identifies STM32 devices
"""

import serial.tools.list_ports
import logging

logger = logging.getLogger(__name__)
# Set logging level to DEBUG
logger.setLevel(logging.DEBUG)

# Add console handler if not already added
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def get_available_ports():
    """Get list of available serial ports"""
    try:
        logger.debug("Starting port scan...")
        ports = list(serial.tools.list_ports.comports())
        logger.info(f"Found {len(ports)} ports in total")
        
        available_ports = []
        
        for port in ports:
            logger.debug(f"Processing port: {port.device}")
            # Add port info including hardware ID and description
            port_info = {
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid,
                'manufacturer': port.manufacturer if hasattr(port, 'manufacturer') else None,
                'vid': port.vid if hasattr(port, 'vid') else None,
                'pid': port.pid if hasattr(port, 'pid') else None
            }
            available_ports.append(port_info)
            
            # Log detailed port info
            logger.info(f"Found port: {port.device} - {port.description}")
            logger.debug(f"Port details: {port_info}")
            
        logger.debug(f"Port scan complete. Found {len(available_ports)} available ports")
        return available_ports
        
    except Exception as e:
        logger.error(f"Error scanning ports: {e}")
        return []

def find_stm32_ports():
    """Find ports that are likely STM32 devices"""
    try:
        all_ports = get_available_ports()
        stm32_ports = []
        
        for port in all_ports:
            # Check various indicators that this might be an STM32 device
            desc = port['description'].lower()
            hwid = port.get('hwid', '').lower()
            
            # Check for known STM32 identifiers
            is_stm32 = (
                # Description-based detection
                any(x in desc for x in ['stm32', 'stlink', 'virtual com port']) or
                # Hardware ID-based detection for STM32
                ('vid:pid=0483:5740' in hwid) or  # Common STM32 VID:PID
                ('vid:pid=0483:374b' in hwid) or  # Another STM32 VID:PID
                # USB Serial Device with STM32 VID
                (port.get('vid') == 1155 and port.get('pid') == 22336)  # 0x0483:0x5740 in decimal
            )
            
            if is_stm32:
                stm32_ports.append(port)
                logger.info(f"Found potential STM32 device: {port['device']}")
                
        return stm32_ports
        
    except Exception as e:
        logger.error(f"Error finding STM32 ports: {e}")
        return []

def test_port_connection(port, baud_rate=115200):
    """Test if we can open a connection to the port"""
    try:
        ser = serial.Serial(port, baud_rate, timeout=1)
        ser.close()
        logger.info(f"Successfully tested connection to {port}")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to {port}: {e}")
        return False
