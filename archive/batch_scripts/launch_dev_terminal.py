#!/usr/bin/env python3
"""
Quick Terminal Launcher for H743Poten
เปิด terminal ใหม่และรัน dev command อัตโนมัติ
"""

import subprocess
import sys
import os

def launch_dev_terminal():
    """เปิด terminal ใหม่ที่มี dev environment พร้อม"""
    print("🚀 Opening H743Poten Development Terminal...")
    
    if os.name == 'nt':
        # Windows
        subprocess.Popen([
            'cmd', '/k', 
            'title H743Poten Development && dev && echo Terminal ready!'
        ], creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        # Linux/Mac
        subprocess.Popen([
            'gnome-terminal', '--', 'bash', '-c', 
            'echo "H743Poten Development"; ./dev.sh; exec bash'
        ])
    
    print("✅ Development terminal launched!")

if __name__ == "__main__":
    launch_dev_terminal()
