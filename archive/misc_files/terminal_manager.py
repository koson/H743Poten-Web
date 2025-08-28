#!/usr/bin/env python3
"""
Terminal Manager for H743Poten Development
แก้ปัญหา VS Code terminal lock เมื่อมี server รันอยู่
"""

import subprocess
import sys
import time
import os
import signal

class TerminalManager:
    def __init__(self):
        self.server_process = None
        
    def start_dev_server(self):
        """เริ่ม development server แบบไม่ล็อก terminal"""
        print("🚀 Starting H743Poten Development Server...")
        print("📝 Server logs จะถูกบันทึกใน logs/server_dev.log")
        
        # สร้าง log directory ถ้าไม่มี
        os.makedirs("logs", exist_ok=True)
        
        # เริ่ม server ใน subprocess แยก
        with open("logs/server_dev.log", "w", encoding="utf-8") as log_file:
            self.server_process = subprocess.Popen(
                [sys.executable, "src/run_dev.py"],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
        
        # รอให้ server เริ่มต้น
        time.sleep(3)
        
        if self.server_process.poll() is None:
            print("✅ Server เริ่มทำงานแล้ว!")
            print("🌐 URL: http://127.0.0.1:8080")
            print("📋 ดู logs: tail -f logs/server_dev.log")
            print("🛑 หยุด server: python terminal_manager.py stop")
            return True
        else:
            print("❌ Server ไม่สามารถเริ่มได้")
            return False
    
    def stop_dev_server(self):
        """หยุด development server"""
        print("🛑 Stopping development server...")
        
        # ใช้ taskkill บน Windows
        if os.name == 'nt':
            try:
                subprocess.run(["taskkill", "/F", "/IM", "python.exe"], 
                             capture_output=True, check=False)
                print("✅ Server stopped!")
            except Exception as e:
                print(f"❌ Error stopping server: {e}")
        else:
            # ใช้ pkill บน Linux/Mac
            try:
                subprocess.run(["pkill", "-f", "run_dev.py"], check=False)
                print("✅ Server stopped!")
            except Exception as e:
                print(f"❌ Error stopping server: {e}")
    
    def status(self):
        """ตรวจสอบสถานะ server"""
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
            encodings_to_try = ['utf-8', 'cp1252', 'latin-1', 'cp874']  # รองรับ encoding หลายแบบ
            
            for encoding in encodings_to_try:
                try:
                    with open(log_file, "r", encoding=encoding, errors='ignore') as f:
                        lines_list = f.readlines()
                        displayed_lines = 0
                        
                        for line in reversed(lines_list):
                            if displayed_lines >= lines:
                                break
                                
                            # ทำความสะอาดข้อมูลที่อาจมีปัญหา
                            clean_line = line.rstrip().encode('utf-8', errors='ignore').decode('utf-8')
                            
                            # กรองตาม filter_text ถ้ามี
                            if filter_text and filter_text.lower() not in clean_line.lower():
                                continue
                                
                            displayed_lines += 1
                            
                        # แสดงผลตามลำดับปกติ (ใหม่สุดอยู่ล่าง)
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
                    break  # ถ้าอ่านได้แล้วให้หยุด
                except UnicodeDecodeError:
                    continue  # ลอง encoding ถัดไป
                except Exception as e:
                    print(f"❌ ไม่สามารถอ่าน logs ด้วย encoding {encoding}: {e}")
                    continue
            else:
                # ถ้าทุก encoding ล้มเหลว ให้อ่านแบบ binary
                try:
                    print("🔄 พยายามอ่านไฟล์แบบ binary...")
                    with open(log_file, "rb") as f:
                        content = f.read()
                        # แปลงเป็น text โดยข้าม character ที่อ่านไม่ได้
                        text_content = content.decode('utf-8', errors='replace')
                        lines_list = text_content.split('\n')
                        for line in lines_list[-lines:]:
                            if line.strip():  # ข้าม empty lines
                                print(line)
                except Exception as e:
                    print(f"❌ ไม่สามารถอ่าน logs: {e}")
        else:
            print("❌ ไม่พบไฟล์ logs")

def main():
    manager = TerminalManager()
    
    if len(sys.argv) < 2:
        print("🔧 H743Poten Terminal Manager")
        print("การใช้งาน:")
        print("  python terminal_manager.py start         - เริ่ม server")
        print("  python terminal_manager.py stop          - หยุด server")
        print("  python terminal_manager.py status        - ตรวจสอบสถานะ")
        print("  python terminal_manager.py logs          - แสดง logs (50 บรรทัดล่าสุด)")
        print("  python terminal_manager.py logs 100      - แสดง logs (100 บรรทัดล่าสุด)")
        print("  python terminal_manager.py logs 50 error - แสดง logs ที่มีคำว่า error")
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        manager.start_dev_server()
    elif command == "stop":
        manager.stop_dev_server()
    elif command == "status":
        manager.status()
    elif command == "logs":
        lines = 50  # default
        filter_text = None
        
        # ตรวจสอบพารามิเตอร์เพิ่มเติม
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
