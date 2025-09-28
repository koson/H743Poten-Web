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
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/h743poten_dev.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_dev_app():
    """Create Flask app with REAL SCPI handler and ALL measurement modes"""
    from hardware.scpi_handler import SCPIHandler  # REAL HARDWARE
    from services.measurement_service import MeasurementService
    from services.cv_measurement_service import CVMeasurementService
    from services.dpv_measurement_service import DPVMeasurementService
    from services.swv_measurement_service import SWVMeasurementService
    from services.ca_measurement_service import CAMeasurementService
    from services.data_service import DataService
    
    # Import the create_app function and modify it for production
    app = create_app()
    
    # Use REAL SCPI handler (NOT mock)
    app.scpi_handler = SCPIHandler("/dev/ttyACM1", 115200)  # REAL STM32 CONNECTION
    
    # Initialize ALL measurement services
    app.measurement_service = MeasurementService(app.scpi_handler)  # Legacy/fallback
    app.cv_service = CVMeasurementService(app.scpi_handler)
    app.dpv_service = DPVMeasurementService(app.scpi_handler)
    app.swv_service = SWVMeasurementService(app.scpi_handler)
    app.ca_service = CAMeasurementService(app.scpi_handler)
    app.data_service = DataService()
    
    # Enable auto-save for all measurement modes
    app.config['auto_save_enabled'] = True
    app.config['scpi_handler'] = app.scpi_handler
    
    return app

def main():
    """Main entry point for development"""
    try:
        # Create and run Flask app with mock handler
        app = create_dev_app()
        
        logger.info("🚀 Starting H743Poten Web Interface (FULL PRODUCTION MODE)")
        logger.info("🔴 Using REAL SCPI handler - Will connect to STM32H743")
        logger.info("📡 ALL MEASUREMENT MODES: CV ✅ DPV ✅ SWV ✅ CA ✅")
        logger.info("📊 Full features: Real-time plotting, Data export, Hardware debugging")
        logger.info(f"🌐 Web server: http://localhost:{Config.WEB_PORT}")
        
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
