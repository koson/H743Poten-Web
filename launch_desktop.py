#!/usr/bin/env python3
"""
Desktop App Launcher Script
Quick launcher with dependency auto-install
"""

import subprocess
import sys
import os

def install_desktop_deps():
    """Install desktop app dependencies"""
    print("📦 Installing desktop app dependencies...")
    
    packages = [
        'pywebview',
        'requests',
        'flask',
        'pyserial'
    ]
    
    for pkg in packages:
        try:
            print(f"   Installing {pkg}...")
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', pkg,
                '--quiet', '--disable-pip-version-check'
            ])
        except Exception as e:
            print(f"   ⚠️ {pkg} install failed: {e}")

def launch_desktop():
    """Launch desktop application"""
    print("🚀 Launching H743 Potentiostat Desktop...")
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Launch desktop app
    try:
        subprocess.run([sys.executable, 'desktop_app.py'])
    except KeyboardInterrupt:
        print("\n✅ Desktop app closed")
    except Exception as e:
        print(f"❌ Launch error: {e}")

if __name__ == "__main__":
    print("⚡ H743 Potentiostat Desktop Launcher")
    print("🕐 2-Hour Speed Build Edition")
    print("="*50)
    
    # Install dependencies
    install_desktop_deps()
    
    print("✅ Dependencies ready!")
    print("🖥️ Starting desktop application...")
    
    # Launch
    launch_desktop()