#!/usr/bin/env python3
"""
Production entry point for H743Poten Web Interface
Uses Gunicorn for better performance and stability
"""

import os
import sys
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/h743poten_prod.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_application():
    """Create the Flask application for Gunicorn"""
    try:
        from src.app import create_app
        app = create_app()
        logger.info("H743Poten Web Interface created successfully for production")
        return app
    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        raise

# Create application instance for Gunicorn
application = create_application()

if __name__ == '__main__':
    # Direct execution - use development server
    logger.warning("Running with development server. Use Gunicorn for production.")
    application.run(
        host='0.0.0.0',
        port=int(os.getenv('WEB_PORT', 8080)),
        debug=False
    )
