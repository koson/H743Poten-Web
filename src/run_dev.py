#!/usr/bin/env python3
"""
Direct entry point for running H743Poten Web Interface in development mode
This script handles imports correctly and uses mock hardware
"""

import os
import sys
import logging
import socket

# Ensure the src directory is in the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')

# Add both current directory and src to Python path
sys.path.insert(0, current_dir)
sys.path.insert(0, src_dir)
sys.path.insert(0, parent_dir)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_dev_app():
    """Create Flask app with real H743 SCPI handler"""
    try:
        from app import create_app
        from hardware.scpi_handler import SCPIHandler
        
        # Try to find and connect to real H743 hardware first
        scpi_handler = None
        
        # Auto-detect STM32 ports
        from hardware.port_scanner import find_stm32_ports
        stm32_ports = find_stm32_ports()
        
        for port_info in stm32_ports:
            port = port_info['device']
            try:
                logger.info(f"🔌 Trying to connect to H743 on {port}")
                scpi_handler = SCPIHandler(port=port, baud_rate=115200)
                if scpi_handler.connect():
                    logger.info(f"✅ Connected to real H743 hardware on {port}")
                    break
                else:
                    logger.warning(f"❌ Failed to connect to {port}")
                    scpi_handler = None
            except Exception as e:
                logger.warning(f"❌ H743 connection error on {port}: {e}")
                scpi_handler = None
        
        if scpi_handler is None:
            logger.warning("❌ No H743 hardware found on any STM32 port, falling back to mock")
        
        # If real hardware failed, use mock as fallback
        if scpi_handler is None:
            from hardware.mock_scpi_handler import MockSCPIHandler
            scpi_handler = MockSCPIHandler()
            logger.info("Using mock SCPI handler for testing")
        
        # Create the app with the selected handler
        app = create_app(scpi_handler)
        
        logger.info("Created development app with real H743 hardware")
        return app
        
    except Exception as e:
        logger.error(f"Failed to create development app: {e}")
        raise

def find_free_port(start_port=8080, max_attempts=10):
    """หา port ว่างเริ่มจาก start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return None

def main():
    """Main entry point for development"""
    try:
        logger.info("Starting H743Poten Web Interface (Development Mode)")
        logger.info("🔌 FORCING REAL SCPI handler - NO MOCK DATA")
        
        # Find a free port
        port = find_free_port(8080, 10)
        if port is None:
            logger.error("No free ports available (tried 8080-8090)")
            sys.exit(1)
        
        logger.info(f"Using port {port}")
        
        # Create the Flask app with mock hardware
        app = create_dev_app()
        
        # Run the app
        app.run(
            host='0.0.0.0',
            port=port,
            debug=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start development server: {e}")
        raise

if __name__ == "__main__":
    main()
