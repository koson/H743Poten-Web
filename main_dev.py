"""
Development version of main.py using Mock SCPI Handler
Run this for development/testing without actual hardware
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import create_app
from config.settings import Config

# Load development environment variables
load_dotenv('.env.development')

# Create logs directory if it doesn't exist
Path('logs').mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/h743poten_dev.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_dev_app():
    """Create Flask app with REAL SCPI handler"""
    from hardware.scpi_handler import SCPIHandler  # REAL HARDWARE
    from services.measurement_service import MeasurementService
    from services.data_service import DataService
    
    # Import the create_app function and modify it for production
    app = create_app()
    
    # Use REAL SCPI handler (NOT mock)
    app.scpi_handler = SCPIHandler()  # REAL STM32 CONNECTION
    app.measurement_service = MeasurementService(app.scpi_handler)
    app.data_service = DataService()
    
    return app

def main():
    """Main entry point for development"""
    try:
        # Create and run Flask app with mock handler
        app = create_dev_app()
        
        logger.info("🚀 Starting H743Poten Web Interface (REAL HARDWARE MODE)")
        logger.info("🔴 Using REAL SCPI handler - Will connect to STM32H743")
        logger.info("📡 Full features: CV, SWV, Data logging, Browse - ALL with REAL hardware")
        logger.info(f"Web server: http://localhost:{Config.WEB_PORT}")
        
        app.run(
            host=Config.WEB_HOST,
            port=Config.WEB_PORT,
            debug=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start development server: {e}")
        raise

if __name__ == "__main__":
    main()
