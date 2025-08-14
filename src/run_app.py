#!/usr/bin/env python3
"""
Direct entry point for running H743Poten Web Interface
This script handles imports correctly when run from within Docker or different directory structures
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

# Set up logging with DEBUG level for troubleshooting
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point"""
    try:
        # Import the app creation function
        from app import create_app
        
        logger.info("Starting H743Poten Web Interface")
        
        # Create the Flask app
        app = create_app()
        
        # Run the app
        app.run(
            host='0.0.0.0',
            port=8080,
            debug=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

if __name__ == "__main__":
    main()
