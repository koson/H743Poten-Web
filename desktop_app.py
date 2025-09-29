import webview
import flask
import threading
import time
import requests
import json
import os
import sys
from urllib.parse import urlparse

class H743DesktopApp:
    def __init__(self):
        self.flask_app = None
        self.flask_thread = None
        self.port = 5000
        
    def create_flask_app(self):
        """สร้าง Flask app สำหรับ desktop"""
        # Import แยกเพื่อไม่ให้ conflict
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        try:
            # ใช้ queue_scpi_server เป็นหลัก
            import queue_scpi_server
            app_instance = queue_scpi_server.app
            print("✅ ใช้ queue_scpi_server.py สำเร็จ")
            return app_instance
        except (ImportError, AttributeError):
            try:
                # ลองใช้ main.py สำรอง
                import main
                if hasattr(main, 'app'):
                    app_instance = main.app
                    print("✅ ใช้ main.py สำเร็จ")
                    return app_instance
                else:
                    raise AttributeError("main.py ไม่มี app attribute")
            except (ImportError, AttributeError):
                # สร้าง minimal Flask app
                app_instance = flask.Flask(__name__)
                
                @app_instance.route('/')
                def index():
                    return "<h1>H743 Potentiostat Desktop</h1><p>📡 STM32 Server กำลังโหลด...</p><a href='/test'>Test Connection</a>"
                
                @app_instance.route('/test')
                def test():
                    return {"status": "OK", "message": "Desktop app รันได้แล้ว"}
                
                print("⚠️ ใช้ minimal Flask app")
                return app_instance
    
    def start_flask_server(self):
        """เริ่ม Flask server ใน background thread"""
        self.flask_app = self.create_flask_app()
        self.flask_app.config['DEBUG'] = False
        
        def run_server():
            try:
                self.flask_app.run(host='127.0.0.1', port=self.port, debug=False, use_reloader=False)
            except Exception as e:
                print(f"❌ Flask server error: {e}")
        
        self.flask_thread = threading.Thread(target=run_server, daemon=True)
        self.flask_thread.start()
        
        # รอให้ server พร้อม
        max_retries = 10
        for i in range(max_retries):
            try:
                response = requests.get(f'http://127.0.0.1:{self.port}', timeout=1)
                if response.status_code == 200:
                    print(f"✅ Flask server พร้อมที่ port {self.port}")
                    return True
            except:
                time.sleep(0.5)
        
        print(f"❌ Flask server ไม่พร้อมหลัง {max_retries} ครั้ง")
        return False
    
    def create_window(self):
        """สร้าง desktop window"""
        window = webview.create_window(
            title='H743 Potentiostat Desktop',
            url=f'http://127.0.0.1:{self.port}',
            width=1200,
            height=800,
            min_size=(800, 600),
            resizable=True
        )
        return window
    
    def run(self):
        """เริ่มแอปพลิเคชัน"""
        print("🚀 เริ่ม H743 Desktop App...")
        
        # เริ่ม Flask server
        if not self.start_flask_server():
            print("❌ ไม่สามารถเริ่ม Flask server ได้")
            return
        
        # สร้างและแสดง window
        window = self.create_window()
        print("🖥️  กำลังแสดง desktop window...")
        
        # เริ่ม webview
        webview.start(debug=False)

if __name__ == '__main__':
    app = H743DesktopApp()
    app.run()
