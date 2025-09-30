# SCPI Server Design for Raspberry Pi

**Document Version:** 1.0  
**Date:** October 1, 2025  
**Concept:** Independent SCPI Server with automated data management  

---

## 🎯 **แนวคิด: SCPI Server เป็น Independent Service**

### **Security Camera Analogy**
```
📹 กล้องวงจรปิด          ⚡ SCPI Server
├── บันทึกตลอดเวลา      ├── รับ measurement commands
├── เก็บไฟล์ชั่วคราว     ├── เก็บข้อมูลชั่วคราว (circular buffer)
├── Auto overwrite      ├── Auto cleanup old data
└── Backup เหตุสำคัญ     └── Export/backup เมื่อสำคัญ

🏠 เจ้าของบ้าน           🌐 Web Application  
├── ดูภาพสด             ├── ดูข้อมูลแบบ real-time
├── ดูประวัติย้อนหลัง    ├── ดูข้อมูลที่เก็บไว้
└── Export คลิปสำคัญ     └── Export measurement data
```

---

## 🏗️ **SCPI Server Architecture**

### **System Overview**
```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 4/5                        │
├─────────────────────────────────────────────────────────────┤
│  Web Application Layer                                      │
│  ├── Flask Web UI (Port 5000)                              │
│  ├── Real-time Dashboard                                    │
│  └── Data Export Interface                                  │
├─────────────────────────────────────────────────────────────┤
│  Communication Layer                                        │
│  ├── HTTP REST API (Web ↔ SCPI Server)                     │
│  ├── WebSocket (Real-time data streaming)                  │
│  └── Unix Domain Socket (Optional, faster IPC)             │
├─────────────────────────────────────────────────────────────┤
│  SCPI Server (Independent Process)                         │
│  ├── Serial Port Management (/dev/ttyUSB0)                 │
│  ├── Command Queue & Execution                             │
│  ├── Data Collection & Buffering                           │
│  ├── Automatic Data Management                             │
│  └── HTTP API Server (Port 6000)                           │
├─────────────────────────────────────────────────────────────┤
│  Data Storage Layer                                         │
│  ├── Circular Buffer (RAM, recent data)                    │
│  ├── Temporary Files (/tmp/measurements/)                  │
│  ├── Important Data (/home/pi/important_data/)             │
│  └── Configuration (/etc/scpi-server/)                     │
├─────────────────────────────────────────────────────────────┤
│  Hardware Layer                                             │
│  └── STM32H743 (via /dev/ttyUSB0)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 💾 **Data Management Strategy (เหมือนกล้องวงจรปิด)**

### **Circular Buffer System**
```python
class CircularDataBuffer:
    """เหมือน HDD ของกล้องวงจรปิด - เขียนทับเมื่อเต็ม"""
    
    def __init__(self, max_size_mb=100):  # 100MB buffer
        self.max_size = max_size_mb * 1024 * 1024
        self.data_files = deque(maxlen=50)  # เก็บไฟล์ล่าสุด 50 ไฟล์
        self.current_size = 0
        self.temp_dir = "/tmp/scpi_measurements"
        
    def add_measurement_file(self, filepath: str, is_important=False):
        """เพิ่มไฟล์ measurement ใหม่"""
        file_size = os.path.getsize(filepath)
        
        if is_important:
            # Important data -> backup to permanent storage
            self._backup_important_file(filepath)
        
        # Add to circular buffer
        self.data_files.append({
            'path': filepath,
            'timestamp': time.time(),
            'size': file_size,
            'is_important': is_important
        })
        
        self.current_size += file_size
        
        # Auto cleanup when buffer full
        while self.current_size > self.max_size and self.data_files:
            oldest = self.data_files.popleft()
            if not oldest['is_important']:  # ไม่ลบไฟล์สำคัญ
                os.remove(oldest['path'])
                self.current_size -= oldest['size']
    
    def _backup_important_file(self, filepath: str):
        """Backup ไฟล์สำคัญไปที่ปลอดภัย"""
        backup_dir = "/home/pi/important_measurements"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"important_{timestamp}.csv")
        shutil.copy2(filepath, backup_path)
        
        # Optional: compress old backups
        self._compress_old_backups(backup_dir)
```

### **Auto Data Management**
```python
class DataManager:
    """จัดการข้อมูลอัตโนมัติเหมือนกล้องวงจรปิด"""
    
    def __init__(self):
        self.buffer = CircularDataBuffer(max_size_mb=200)  # 200MB สำหรับ Pi
        self.cleanup_scheduler = BackgroundScheduler()
        self.setup_auto_cleanup()
    
    def setup_auto_cleanup(self):
        """ตั้งเวลาทำความสะอาดอัตโนมัติ"""
        # ทำความสะอาดทุก 1 ชั่วโมง
        self.cleanup_scheduler.add_job(
            self._hourly_cleanup,
            'interval',
            hours=1,
            id='hourly_cleanup'
        )
        
        # Compress ไฟล์เก่าทุกวันเที่ยงคืน
        self.cleanup_scheduler.add_job(
            self._daily_compression,
            'cron', 
            hour=0,
            minute=0,
            id='daily_compression'
        )
        
        self.cleanup_scheduler.start()
    
    def _hourly_cleanup(self):
        """ทำความสะอาดไฟล์เก่าทุกชั่วโมง"""
        current_time = time.time()
        temp_dir = "/tmp/scpi_measurements"
        
        for filename in os.listdir(temp_dir):
            filepath = os.path.join(temp_dir, filename)
            file_age = current_time - os.path.getmtime(filepath)
            
            # ลบไฟล์ที่เก่ากว่า 6 ชั่วโมง (ยกเว้นไฟล์สำคัญ)
            if file_age > 6 * 3600 and not self._is_important_file(filepath):
                os.remove(filepath)
                print(f"🗑️ Cleaned up old file: {filename}")
    
    def mark_as_important(self, measurement_id: str, reason: str):
        """ทำเครื่องหมายข้อมูลว่าสำคัญ (เหมือนการบันทึกคลิปสำคัญ)"""
        # หาไฟล์ที่ตรงกับ measurement_id
        filepath = self._find_measurement_file(measurement_id)
        if filepath:
            # Backup ไปที่ปลอดภัย
            self.buffer._backup_important_file(filepath)
            
            # Log เหตุผล
            self._log_important_event(measurement_id, reason, filepath)
```

---

## 🖥️ **SCPI Server Implementation**

### **Core SCPI Server**
```python
#!/usr/bin/env python3
"""
SCPI Server - Independent process for H743 communication
Similar to IP camera recording system
"""

import asyncio
import logging
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import queue
import uuid

class SCPIServer:
    """Independent SCPI Server for STM32H743 communication"""
    
    def __init__(self, port=6000):
        self.port = port
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Core components
        self.serial_manager = SerialManager()
        self.command_queue = queue.Queue()
        self.data_manager = DataManager()
        self.measurement_sessions = {}  # active measurements
        
        # State
        self.is_running = False
        self.worker_thread = None
        
        self.setup_routes()
        self.setup_websocket()
        
    def setup_routes(self):
        """Setup HTTP API routes"""
        
        @self.app.route('/health')
        def health():
            return jsonify({
                'status': 'healthy',
                'service': 'scpi-server',
                'port': self.port,
                'connected': self.serial_manager.is_connected,
                'active_measurements': len(self.measurement_sessions),
                'queue_size': self.command_queue.qsize(),
                'uptime': time.time() - self.start_time if hasattr(self, 'start_time') else 0
            })
        
        @self.app.route('/api/connect', methods=['POST'])
        def connect_device():
            """Connect to STM32H743"""
            data = request.get_json()
            port = data.get('port', '/dev/ttyUSB0')
            baud_rate = data.get('baud_rate', 115200)
            
            success = self.serial_manager.connect(port, baud_rate)
            return jsonify({
                'success': success,
                'port': port,
                'baud_rate': baud_rate,
                'device_info': self.serial_manager.get_device_info() if success else None
            })
        
        @self.app.route('/api/measurement/start', methods=['POST'])
        def start_measurement():
            """Start new measurement (like starting camera recording)"""
            data = request.get_json()
            technique = data.get('technique')  # CV, DPV, SWV, CA
            params = data.get('params')
            
            # Generate unique session ID
            session_id = str(uuid.uuid4())
            
            # Create measurement session
            session = MeasurementSession(
                session_id=session_id,
                technique=technique,
                params=params,
                data_manager=self.data_manager
            )
            
            # Queue command for execution
            command = {
                'type': 'start_measurement',
                'session_id': session_id,
                'session': session
            }
            self.command_queue.put(command)
            
            self.measurement_sessions[session_id] = session
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'message': f'{technique} measurement started'
            })
        
        @self.app.route('/api/measurement/<session_id>/data')
        def get_measurement_data(session_id):
            """Get live measurement data (like viewing camera feed)"""
            if session_id not in self.measurement_sessions:
                return jsonify({'error': 'Session not found'}), 404
            
            session = self.measurement_sessions[session_id]
            return jsonify({
                'session_id': session_id,
                'technique': session.technique,
                'status': session.status,
                'data_points': len(session.data_points),
                'latest_data': session.get_recent_data(limit=100),
                'file_path': session.current_file_path
            })
        
        @self.app.route('/api/measurement/<session_id>/stop', methods=['POST'])
        def stop_measurement(session_id):
            """Stop measurement (like stopping recording)"""
            if session_id not in self.measurement_sessions:
                return jsonify({'error': 'Session not found'}), 404
            
            # Queue stop command
            command = {
                'type': 'stop_measurement',
                'session_id': session_id
            }
            self.command_queue.put(command)
            
            return jsonify({'success': True, 'message': 'Stop command queued'})
        
        @self.app.route('/api/measurement/<session_id>/mark_important', methods=['POST'])
        def mark_important(session_id):
            """Mark measurement as important (like saving important camera footage)"""
            data = request.get_json()
            reason = data.get('reason', 'User marked as important')
            
            if session_id in self.measurement_sessions:
                self.data_manager.mark_as_important(session_id, reason)
                return jsonify({'success': True, 'message': 'Marked as important'})
            else:
                return jsonify({'error': 'Session not found'}), 404
        
        @self.app.route('/api/data/recent')
        def get_recent_data():
            """Get recent measurement files (like recent camera recordings)"""
            recent_files = self.data_manager.get_recent_files(limit=20)
            return jsonify({
                'files': recent_files,
                'buffer_usage': self.data_manager.get_buffer_usage()
            })

if __name__ == '__main__':
    server = SCPIServer(port=6000)
    server.start_server()
```

---

## 🚀 **Pi Performance Analysis**

### **Resource Usage Estimation**

```python
# SCPI Server Resource Requirements
Process Memory: ~50-80MB
Data Buffer: ~100-200MB (configurable)
File I/O: Minimal (streaming write)
CPU Usage: 5-15% (mostly I/O bound)
Network: <1MB/s (measurement data)

# Total System Usage
SCPI Server: 250MB RAM, 10% CPU
Web App: 150MB RAM, 5% CPU  
OS + Services: 500MB RAM, 5% CPU
Total: 900MB RAM, 20% CPU

# Raspberry Pi 4 (4GB) - ✅ Comfortable
# Raspberry Pi 4 (2GB) - ⚠️ Tight but possible
```

### **Performance Benefits**
```
1. 🚀 Dedicated Serial Management
   - No interference from web app
   - Consistent data collection
   - Better error handling

2. 💾 Automatic Data Management  
   - No manual file cleanup needed
   - Intelligent storage allocation
   - Important data preservation

3. 🔄 Process Isolation
   - Web app crash ≠ measurement lost
   - Independent restart/update
   - Better debugging

4. 📡 Real-time Streaming
   - WebSocket for live data
   - Multiple client support
   - No polling overhead
```

---

## 🛠️ **Integration with Web App**

### **Web App ส่วนที่เหลือ**
```python
# simplified_web_app.py
from flask import Flask, render_template, request, jsonify
import requests

class SimplifiedWebApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.scpi_server_url = 'http://localhost:6000'
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard.html')
        
        @self.app.route('/api/start_measurement', methods=['POST'])
        def start_measurement():
            """Proxy request to SCPI Server"""
            data = request.get_json()
            
            # Forward to SCPI Server
            response = requests.post(
                f'{self.scpi_server_url}/api/measurement/start',
                json=data,
                timeout=30
            )
            
            return response.json(), response.status_code
        
        @self.app.route('/api/measurement/<session_id>/data')  
        def get_data(session_id):
            """Get measurement data from SCPI Server"""
            response = requests.get(
                f'{self.scpi_server_url}/api/measurement/{session_id}/data'
            )
            return response.json(), response.status_code

if __name__ == '__main__':
    app = SimplifiedWebApp()
    app.app.run(host='0.0.0.0', port=5000)
```

---

## ✅ **คำตอบ: Pi จะไหวไหม?**

### **Pi 4 (4GB+): ✅ ไหวสบาย**
- RAM: 900MB/4GB = 22.5% usage
- CPU: 20% average usage  
- Storage: SSD แนะนำ, SD card ก็ใช้ได้
- Network: ไม่เป็นปัญหา

### **Pi 4 (2GB): ⚠️ ไหวแต่ต้องระวัง**
- RAM: 900MB/2GB = 45% usage
- ลด buffer size เหลือ 50MB
- ปิด debug mode
- Monitor memory usage

### **ข้อดีของแนวทางนี้:**
1. **🎯 Single Responsibility**: SCPI Server ดูแลแต่ serial communication
2. **🔄 Auto Management**: ไม่ต้องจัดการไฟล์เอง
3. **📡 Real-time**: WebSocket streaming เร็วกว่า polling
4. **🛡️ Fault Tolerance**: Web app crash ไม่กระทบการวัด
5. **🔧 Easy Maintenance**: อัพเดท/restart แยกกันได้

### **ข้อเสีย:**
1. **🔗 Network Dependency**: ต้องมี HTTP communication
2. **⚙️ Complexity**: ระบบซับซ้อนขึ้น  
3. **🐛 Debugging**: ต้อง debug 2 processes
4. **💾 Storage**: ต้องจัดการ disk space

คุณคิดว่าแนวทางนี้เหมาะกับโปรเจคไหมครับ? 🚀