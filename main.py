"""
Main application entry point for H743Poten Web Interface
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

# Load environment variables
load_dotenv()

# Create logs directory if it doesn't exist
Path('logs').mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce log level for cleaner terminal during Git operations
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/h743poten.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point"""
    try:
        # Create and run Flask app
        app = create_app()
        
        logger.info("Starting H743Poten Web Interface")
        logger.info(f"Serial port: {Config.SERIAL_PORT}")
        logger.info(f"Baud rate: {Config.BAUD_RATE}")
        logger.info(f"Web server: http://localhost:{Config.WEB_PORT}")
        
        app.run(
            host=Config.WEB_HOST,
            port=Config.WEB_PORT,
            debug=Config.DEBUG
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

if __name__ == "__main__":
    main()
