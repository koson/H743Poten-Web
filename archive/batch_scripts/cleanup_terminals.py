#!/usr/bin/env python3
"""
Terminal Cleanup Utility
สำหรับแก้ปัญหา terminal lock และจัดการ processes ที่ค้างอยู่
"""

import psutil
import subprocess
import sys
import time
from typing import List, Dict

class TerminalCleanup:
    def __init__(self):
        self.processes_to_check = [
            'python.exe',
            'flask.exe', 
            'gunicorn.exe',
            'waitress-serve.exe',
            'node.exe',
            'npm.exe'
        ]
        
    def find_python_processes(self) -> List[Dict]:
        """หา Python processes ที่เกี่ยวข้องกับโปรเจค"""
        project_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status']):
            try:
                if proc.info['name'] in self.processes_to_check:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    
                    # ตรวจสอบว่าเป็น process ของโปรเจคเราหรือไม่
                    if any(keyword in cmdline.lower() for keyword in [
                        'h743poten', 'main.py', 'app.py', 'flask', 'poten'
                    ]):
                        project_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': cmdline,
                            'status': proc.info['status'],
                            'process': proc
                        })
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        return project_processes
    
    def kill_process_safe(self, proc_info: Dict) -> bool:
        """ปิด process อย่างปลอดภัย"""
        try:
            proc = proc_info['process']
            print(f"🔄 Terminating {proc_info['name']} (PID: {proc_info['pid']})")
            
            # ลองปิดแบบสุภาพก่อน
            proc.terminate()
            
            # รอ 3 วินาที
            try:
                proc.wait(timeout=3)
                print(f"✅ Successfully terminated {proc_info['name']}")
                return True
            except psutil.TimeoutExpired:
                # ถ้าไม่ปิด ใช้ force kill
                print(f"⚠️ Process didn't terminate gracefully, force killing...")
                proc.kill()
                proc.wait()
                print(f"✅ Force killed {proc_info['name']}")
                return True
                
        except Exception as e:
            print(f"❌ Failed to kill {proc_info['name']}: {e}")
            return False
    
    def cleanup_flask_processes(self):
        """ปิด Flask/Python processes ที่เกี่ยวข้อง"""
        print("🔍 Scanning for Flask/Python processes...")
        
        processes = self.find_python_processes()
        
        if not processes:
            print("✅ No Flask/Python processes found")
            return
        
        print(f"📋 Found {len(processes)} processes:")
        for proc in processes:
            print(f"  - {proc['name']} (PID: {proc['pid']}) - {proc['status']}")
            print(f"    Command: {proc['cmdline'][:100]}...")
        
        print("\n🛑 Terminating processes...")
        for proc in processes:
            self.kill_process_safe(proc)
    
    def check_port_usage(self, port: int = 8080):
        """ตรวจสอบการใช้งาน port"""
        print(f"\n🔍 Checking port {port} usage...")
        
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                try:
                    proc = psutil.Process(conn.pid)
                    print(f"📍 Port {port} is used by: {proc.name()} (PID: {conn.pid})")
                    return conn.pid
                except psutil.NoSuchProcess:
                    print(f"📍 Port {port} is used by unknown process")
                    return conn.pid
        
        print(f"✅ Port {port} is free")
        return None
    
    def cleanup_port(self, port: int = 8080):
        """ปิด process ที่ใช้ port นี้"""
        pid = self.check_port_usage(port)
        if pid:
            try:
                proc = psutil.Process(pid)
                print(f"🛑 Killing process using port {port}: {proc.name()} (PID: {pid})")
                proc.terminate()
                proc.wait(timeout=3)
                print(f"✅ Successfully freed port {port}")
            except Exception as e:
                print(f"❌ Failed to kill process on port {port}: {e}")
    
    def full_cleanup(self):
        """ทำ cleanup ทั้งหมด"""
        print("🧹 Starting full terminal/process cleanup...")
        print("=" * 50)
        
        # ปิด Flask processes
        self.cleanup_flask_processes()
        
        # ปิด process ที่ใช้ port 8080
        self.cleanup_port(8080)
        
        # รอสักครู่
        print("\n⏳ Waiting for cleanup to complete...")
        time.sleep(2)
        
        # ตรวจสอบอีกครั้ง
        remaining = self.find_python_processes()
        if remaining:
            print(f"⚠️ {len(remaining)} processes still running:")
            for proc in remaining:
                print(f"  - {proc['name']} (PID: {proc['pid']})")
        else:
            print("✅ All processes cleaned up successfully!")
        
        print("=" * 50)
        print("🎉 Cleanup completed!")

def main():
    """Main function"""
    cleanup = TerminalCleanup()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'processes':
            cleanup.cleanup_flask_processes()
        elif command == 'port':
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
            cleanup.cleanup_port(port)
        elif command == 'check':
            processes = cleanup.find_python_processes()
            port_pid = cleanup.check_port_usage()
            print(f"Found {len(processes)} processes, port 8080 usage: {port_pid}")
        else:
            print("Unknown command. Use: processes, port, check, or no argument for full cleanup")
    else:
        cleanup.full_cleanup()

if __name__ == "__main__":
    main()
