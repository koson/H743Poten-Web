#!/usr/bin/env python3
"""
Simple Desktop App - No GUI Dependencies Required
===============================================
Opens H743 Potentiostat in default web browser
"""

import subprocess
import sys
import time
import requests
import threading
import os

class SimpleDesktopApp:
    def __init__(self):
        self.flask_process = None
        self.port = 5000
        
    def start_flask_server(self):
        """Start Flask server in background"""
        print("🚀 Starting Flask server...")
        
        # Run queue_scpi_server.py in background
        try:
            self.flask_process = subprocess.Popen([
                sys.executable, 'queue_scpi_server.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            
            # Wait for server to start (STM32 connection takes time)
            max_retries = 30
            for i in range(max_retries):
                try:
                    response = requests.get(f'http://127.0.0.1:{self.port}', timeout=2)
                    if response.status_code == 200:
                        print(f"✅ Flask server ready at http://127.0.0.1:{self.port}")
                        return True
                except:
                    if i < 10:
                        print(f"⏳ Starting server... ({i+1}/{max_retries})")
                    elif i == 10:
                        print("⏳ Connecting to STM32... (this may take a moment)")
                    elif i % 5 == 0:
                        print(f"⏳ Still connecting... ({i+1}/{max_retries})")
                    time.sleep(1)
            
            print("❌ Flask server failed to start")
            return False
            
        except Exception as e:
            print(f"❌ Error starting Flask: {e}")
            return False
    
    def open_browser(self):
        """Open default web browser"""
        url = f'http://127.0.0.1:{self.port}'
        print(f"🌐 Opening browser: {url}")
        
        # Try different browser opening methods
        try:
            # Linux
            subprocess.run(['xdg-open', url], check=True)
        except:
            try:
                # Alternative Linux
                subprocess.run(['firefox', url], check=True)
            except:
                try:
                    # Another alternative
                    subprocess.run(['google-chrome', url], check=True)
                except:
                    print(f"❌ Could not open browser automatically")
                    print(f"🔗 Please open manually: {url}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.flask_process:
            print("🛑 Stopping Flask server...")
            self.flask_process.terminate()
            self.flask_process.wait()
    
    def run(self):
        """Run the desktop app"""
        print("🧪 H743 Potentiostat Simple Desktop App")
        print("=" * 50)
        
        try:
            # Start Flask server
            if not self.start_flask_server():
                return 1
            
            # Open browser
            self.open_browser()
            
            print("\n✅ Desktop app is running!")
            print("📱 Access via web browser:")
            print(f"   🏠 Main Dashboard: http://127.0.0.1:{self.port}")
            print(f"   📊 System Status: http://127.0.0.1:{self.port}/status")
            print(f"   🔬 Research Platform: http://127.0.0.1:{self.port}/research_platform_v2.html")
            print("\n⌨️  Press Ctrl+C to stop")
            
            # Keep app running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping desktop app...")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
        finally:
            self.cleanup()
        
        return 0

if __name__ == '__main__':
    app = SimpleDesktopApp()
    sys.exit(app.run())
