#!/usr/bin/env python3
"""
🚀 CV Peak Validation Web UI Launcher
====================================

Quick launcher for the CV Peak Validation Web Interface.
This script will start the Flask web server and open the browser.

Usage:
python launch_cv_validation_ui.py

Author: H743Poten Research Team
Date: October 4, 2025
"""

import os
import sys
import webbrowser
import time
import threading
from pathlib import Path

# Add validation_data to path
sys.path.append('validation_data')

def open_browser(url, delay=2):
    """Open browser after a delay"""
    time.sleep(delay)
    webbrowser.open(url)

def main():
    """Main launcher function"""
    print("🚀 CV PEAK VALIDATION WEB UI LAUNCHER")
    print("=" * 50)
    
    # Check if Test_Data_CV exists
    test_data_path = "Test_Data_CV"
    if not os.path.exists(test_data_path):
        print(f"⚠️  Warning: {test_data_path} directory not found")
        print("Creating dummy directory for demo...")
        os.makedirs(test_data_path, exist_ok=True)
    else:
        # Count CSV files
        csv_count = 0
        for root, dirs, files in os.walk(test_data_path):
            csv_count += len([f for f in files if f.endswith('.csv')])
        print(f"📁 Found {csv_count} CSV files in {test_data_path}")
    
    # Check for validation database
    db_path = "validation_data/peak_validation.db"
    if os.path.exists(db_path):
        print(f"💾 Database found: {db_path}")
    else:
        print("💾 Database will be created on first use")
    
    print()
    print("🌐 Starting Web Server...")
    print("📱 The browser will open automatically")
    print("⚠️  Press Ctrl+C to stop the server")
    print()
    
    try:
        # Import and start the app
        from validation_data.cv_validation_app import CVPeakValidationApp
        
        app = CVPeakValidationApp()
        
        # Open browser in a separate thread
        url = "http://127.0.0.1:5001"
        browser_thread = threading.Thread(target=open_browser, args=(url,))
        browser_thread.daemon = True
        browser_thread.start()
        
        # Start the Flask app
        app.run(host='127.0.0.1', port=5001, debug=False)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running from the project root directory")
        print("💡 And that all dependencies are installed")
    except KeyboardInterrupt:
        print("\\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()