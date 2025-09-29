#!/usr/bin/env python3
"""
H743 Potentiostat Desktop Application
Lightning-fast desktop wrapper using existing codebase
"""

import sys
import os
import threading
import time
import webbrowser
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Try to import webview for desktop app
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    print("⚠️ pywebview not available, will use browser fallback")

# Import our existing Flask app
from queue_scpi_server import app, scpi_server

class H743DesktopApp:
    """Desktop wrapper for H743 Potentiostat"""
    
    def __init__(self):
        self.flask_thread = None
        self.server_running = False
        
    def start_flask_server(self):
        """Start Flask server in background thread"""
        print("🚀 Starting Flask server...")
        try:
            # Configure for local desktop use
            app.config['ENV'] = 'development'
            app.config['DEBUG'] = False
            
            # Start server
            app.run(host='127.0.0.1', port=8094, debug=False, use_reloader=False)
        except Exception as e:
            print(f"❌ Flask server error: {e}")
    
    def wait_for_server(self, timeout=30):
        """Wait for Flask server to be ready"""
        import requests
        
        for i in range(timeout):
            try:
                response = requests.get('http://127.0.0.1:8094/status', timeout=1)
                if response.status_code == 200:
                    print("✅ Server ready!")
                    return True
            except:
                pass
            time.sleep(1)
            print(f"⏳ Waiting for server... {i+1}/{timeout}")
        
        return False
    
    def run_desktop_app(self):
        """Run desktop application"""
        print("🖥️ Starting H743 Potentiostat Desktop Application")
        print("=" * 60)
        
        # Start Flask server in background
        self.flask_thread = threading.Thread(target=self.start_flask_server, daemon=True)
        self.flask_thread.start()
        
        # Wait for server to be ready
        print("⏳ Waiting for server to start...")
        if not self.wait_for_server():
            print("❌ Failed to start server")
            return False
        
        # Launch desktop app
        url = 'http://127.0.0.1:8094'
        
        if WEBVIEW_AVAILABLE:
            print("🖥️ Launching native desktop window...")
            try:
                webview.create_window(
                    'H743 Potentiostat Control Center',
                    url,
                    width=1200,
                    height=800,
                    resizable=True,
                    fullscreen=False,
                    minimized=False,
                    on_top=False,
                    shadow=True,
                )
                webview.start(debug=False)
                return True
            except Exception as e:
                print(f"❌ Webview error: {e}")
                print("🌐 Falling back to browser...")
        
        # Fallback to browser
        print("🌐 Opening in default browser...")
        webbrowser.open(url)
        
        # Keep alive
        try:
            print("\n" + "="*60)
            print("🎯 H743 Potentiostat Desktop is running!")
            print("📊 Access at: http://127.0.0.1:8094")
            print("🔌 STM32 Status:", "Connected" if scpi_server.is_connected else "Disconnected")
            if scpi_server.is_connected:
                print("📡 STM32 Port:", scpi_server.stm32_port)
            print("⚠️  Press Ctrl+C to quit")
            print("="*60)
            
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            return True

def install_dependencies():
    """Install required dependencies if missing"""
    import subprocess
    
    required_packages = [
        'pywebview',
        'requests'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            print(f"📦 Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def main():
    """Main entry point"""
    print("🔬 H743 Potentiostat Desktop Application")
    print("⚡ Lightning-fast desktop version")
    print("🕐 Time: 2-hour speed build!")
    print()
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required")
        return 1
    
    # Install dependencies
    try:
        install_dependencies()
    except Exception as e:
        print(f"⚠️ Dependency installation failed: {e}")
        print("🔄 Continuing with available packages...")
    
    # Start desktop app
    try:
        app_instance = H743DesktopApp()
        success = app_instance.run_desktop_app()
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())