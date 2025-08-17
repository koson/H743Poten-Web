#!/usr/bin/env python3
"""
Universal Terminal Manager for H743Poten Development
รองรับทั้ง Windows และ Linux/WSL
แก้ปัญหา VS Code terminal lock
"""

import subprocess
import sys
import time
import os
import signal
import platform

class UniversalTerminalManager:
    def __init__(self):
        self.server_process = None
        self.is_windows = platform.system() == "Windows"
        self.python_cmd = "python" if self.is_windows else "python3"
        
    def start_dev_server(self):
        """เริ่ม development server แบบไม่ล็อก terminal"""
        print("🚀 Starting H743Poten Development Server...")
        
        if self.is_windows:
            print("📝 Server logs จะถูกบันทึกใน logs\\server_dev.log")
        else:
            print("📝 Server logs จะถูกบันทึกใน logs/server_dev.log")
        
        # สร้าง log directory ถ้าไม่มี
        os.makedirs("logs", exist_ok=True)
        
        # เริ่ม server ใน subprocess แยก
        log_file_path = "logs/server_dev.log"
        
        try:
            with open(log_file_path, "w", encoding="utf-8") as log_file:
                if self.is_windows:
                    self.server_process = subprocess.Popen(
                        [self.python_cmd, "src/run_dev.py"],
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    )
                else:
                    self.server_process = subprocess.Popen(
                        [self.python_cmd, "src/run_dev.py"],
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        preexec_fn=os.setsid
                    )
        except Exception as e:
            print(f"❌ ไม่สามารถเริ่ม server: {e}")
            return False
        
        # รอให้ server เริ่มต้น
        time.sleep(3)
        
        if self.server_process.poll() is None:
            print("✅ Server เริ่มทำงานแล้ว!")
            print("🌐 URL: http://127.0.0.1:8080")
            if self.is_windows:
                print("📋 ดู logs: dev logs หรือ type logs\\server_dev.log")
                print("🛑 หยุด server: dev stop")
            else:
                print("📋 ดู logs: ./dev.sh logs หรือ tail -f logs/server_dev.log")
                print("🛑 หยุด server: ./dev.sh stop")
            return True
        else:
            print("❌ Server ไม่สามารถเริ่มได้")
            return False
    
    def stop_dev_server(self):
        """หยุด development server"""
        print("🛑 Stopping development server...")
        
        if self.is_windows:
            # ใช้ taskkill บน Windows
            try:
                subprocess.run(["taskkill", "/F", "/IM", "python.exe"], 
                             capture_output=True, check=False)
                print("✅ Server stopped!")
            except Exception as e:
                print(f"❌ Error stopping server: {e}")
        else:
            # ใช้ pkill บน Linux/WSL
            try:
                subprocess.run(["pkill", "-f", "run_dev.py"], check=False)
                print("✅ Server stopped!")
            except Exception as e:
                print(f"❌ Error stopping server: {e}")
    
    def status(self):
        """ตรวจสอบสถานะ server"""
        try:
            # ลองใช้ urllib แทน requests เพื่อลดการพึ่งพา library
            import urllib.request
            import urllib.error
            
            try:
                response = urllib.request.urlopen("http://127.0.0.1:8080", timeout=2)
                if response.getcode() == 200:
                    print("✅ Server กำลังทำงาน - http://127.0.0.1:8080")
                    return True
            except urllib.error.URLError:
                pass
        except ImportError:
            # ถ้าไม่มี urllib ให้ลองใช้ requests
            try:
                import requests
                response = requests.get("http://127.0.0.1:8080", timeout=2)
                if response.status_code == 200:
                    print("✅ Server กำลังทำงาน - http://127.0.0.1:8080")
                    return True
            except:
                pass
        
        print("❌ Server ไม่ทำงาน")
        return False
    
    def show_logs(self, lines=50, filter_text=None):
        """แสดง server logs"""
        log_file = "logs/server_dev.log"
        if os.path.exists(log_file):
            filter_msg = f" (กรอง: {filter_text})" if filter_text else ""
            print(f"📋 Server Logs (ล่าสุด {lines} บรรทัด{filter_msg}):")
            print("-" * 50)
            
            # อ่าน logs ย้อนหลัง
            encodings_to_try = ['utf-8', 'cp1252', 'latin-1', 'cp874']
            
            for encoding in encodings_to_try:
                try:
                    with open(log_file, "r", encoding=encoding, errors='ignore') as f:
                        lines_list = f.readlines()
                        
                        # แสดงผลในลำดับที่ถูกต้อง
                        filtered_lines = []
                        displayed_lines = 0
                        
                        for line in reversed(lines_list):
                            if displayed_lines >= lines:
                                break
                                
                            clean_line = line.rstrip().encode('utf-8', errors='ignore').decode('utf-8')
                            
                            if filter_text and filter_text.lower() not in clean_line.lower():
                                continue
                                
                            filtered_lines.append(clean_line)
                            displayed_lines += 1
                        
                        # แสดงผลในลำดับที่ถูกต้อง
                        for line in reversed(filtered_lines):
                            print(line)
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"❌ ไม่สามารถอ่าน logs ด้วย encoding {encoding}: {e}")
                    continue
            else:
                # ถ้าทุก encoding ล้มเหลว
                try:
                    print("🔄 พยายามอ่านไฟล์แบบ binary...")
                    with open(log_file, "rb") as f:
                        content = f.read()
                        text_content = content.decode('utf-8', errors='replace')
                        lines_list = text_content.split('\n')
                        for line in lines_list[-lines:]:
                            if line.strip():
                                print(line)
                except Exception as e:
                    print(f"❌ ไม่สามารถอ่าน logs: {e}")
        else:
            print("❌ ไม่พบไฟล์ logs")

def main():
    manager = UniversalTerminalManager()
    
    if len(sys.argv) < 2:
        print("🔧 H743Poten Universal Terminal Manager")
        if manager.is_windows:
            print("การใช้งาน (Windows):")
            print("  python universal_terminal_manager.py start         - เริ่ม server")
            print("  python universal_terminal_manager.py stop          - หยุด server")
            print("  python universal_terminal_manager.py status        - ตรวจสอบสถานะ")
            print("  python universal_terminal_manager.py logs          - แสดง logs")
            print("  หรือใช้: dev start, dev stop, dev status, dev logs")
        else:
            print("การใช้งาน (Linux/WSL):")
            print("  python3 universal_terminal_manager.py start        - เริ่ม server")
            print("  python3 universal_terminal_manager.py stop         - หยุด server")
            print("  python3 universal_terminal_manager.py status       - ตรวจสอบสถานะ")
            print("  python3 universal_terminal_manager.py logs         - แสดง logs")
            print("  หรือใช้: ./dev.sh start, ./dev.sh stop, ./dev.sh status, ./dev.sh logs")
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        manager.start_dev_server()
    elif command == "stop":
        manager.stop_dev_server()
    elif command == "status":
        manager.status()
    elif command == "logs":
        lines = 50
        filter_text = None
        
        if len(sys.argv) > 2:
            try:
                lines = int(sys.argv[2])
            except ValueError:
                filter_text = sys.argv[2]
                
        if len(sys.argv) > 3:
            filter_text = sys.argv[3]
            
        manager.show_logs(lines, filter_text)
    else:
        print(f"❌ ไม่รู้จักคำสั่ง: {command}")

if __name__ == "__main__":
    main()
