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
    """Create Flask app with mock SCPI handler"""
    try:
        from app import create_app
        from hardware.mock_scpi_handler import MockSCPIHandler
        from services.measurement_service import MeasurementService
        from services.data_service import DataService
        
        # Create the base app
        app = create_app()
        
        # Replace the real SCPI handler with mock version
        app.scpi_handler = MockSCPIHandler()
        app.measurement_service = MeasurementService(app.scpi_handler)
        app.data_service = DataService()
        
        logger.info("Created development app with mock hardware")
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
        logger.info("Using mock SCPI handler for testing")
        
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
