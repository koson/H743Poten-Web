#!/usr/bin/env python3
"""
Auto-detect และใช้ terminal manager ที่เหมาะสม
"""

import os
import sys
import platform
import subprocess

def is_wsl():
    """ตรวจสอบว่าอยู่ใน WSL หรือไม่"""
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower()
    except:
        return False

def get_manager_command():
    """หาคำสั่ง terminal manager ที่เหมาะสม"""
    system = platform.system()
    
    if system == "Windows":
        return ["python", "terminal_manager.py"]
    elif system == "Linux":
        if is_wsl():
            return ["python3", "universal_terminal_manager.py"]
        else:
            return ["python3", "universal_terminal_manager.py"]
    else:
        return ["python3", "universal_terminal_manager.py"]

def main():
    """รันคำสั่งที่เหมาะสมกับระบบปฏิบัติการ"""
    
    if len(sys.argv) < 2:
        print("🔧 H743Poten Smart Terminal Manager")
        print("ตรวจสอบระบบอัตโนมัติและใช้ manager ที่เหมาะสม")
        print("")
        
        system = platform.system()
        wsl_status = " (WSL)" if is_wsl() else ""
        print(f"ระบบปัจจุบัน: {system}{wsl_status}")
        
        manager_cmd = get_manager_command()
        print(f"Manager ที่ใช้: {' '.join(manager_cmd)}")
        print("")
        print("คำสั่งที่ใช้ได้:")
        print("  python auto_dev.py start   - เริ่ม server")
        print("  python auto_dev.py stop    - หยุด server")
        print("  python auto_dev.py status  - ตรวจสอบสถานะ")
        print("  python auto_dev.py logs    - แสดง logs")
        return
    
    # รันคำสั่งด้วย manager ที่เหมาะสม
    manager_cmd = get_manager_command()
    manager_cmd.extend(sys.argv[1:])  # เพิ่ม arguments
    
    try:
        subprocess.run(manager_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ ไม่พบไฟล์ manager: {' '.join(manager_cmd)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
