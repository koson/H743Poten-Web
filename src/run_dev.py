#!/usr/bin/env python3
"""
Direct entry point for running H743Poten Web Interface in development mode
This script handles imports correctly and uses mock hardware
"""

import os
import sys
import logging

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

def main():
    """Main entry point for development"""
    try:
        logger.info("Starting H743Poten Web Interface (Development Mode)")
        logger.info("Using mock SCPI handler for testing")
        
        # Create the Flask app with mock hardware
        app = create_dev_app()
        
        # Run the app
        app.run(
            host='0.0.0.0',
            port=8080,
            debug=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start development server: {e}")
        raise

if __name__ == "__main__":
    main()
