#!/usr/bin/env python3
"""
Direct entry point for running H743Poten Web Interface in development mode
This script uses REAL H743 hardware by leveraging create_app()
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
    """Create Flask app with REAL SCPI handler"""
    try:
        from app import create_app

        # Create the base app (this already creates SCPIHandler and all services)
        app = create_app()

        # The app already has real SCPIHandler from create_app()
        # Just verify it's connected
        scpi_handler = app.config.get('scpi_handler')
        if scpi_handler and hasattr(scpi_handler, 'connect'):
            if not scpi_handler.is_connected:
                logger.info(f"Attempting to connect to H743 at {scpi_handler.port}")
                if scpi_handler.connect():
                    logger.info("✅ Successfully connected to H743")
                else:
                    logger.warning("⚠️ Could not connect to H743 - check connection")

        logger.info("Created development app with REAL hardware")
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
        logger.info("Using REAL SCPI handler for testing")

        # Find a free port
        port = find_free_port(8080, 10)
        if port is None:
            logger.error("No free ports available (tried 8080-8090)")
            sys.exit(1)

        logger.info(f"Using port {port}")

        # Create the Flask app with REAL hardware
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