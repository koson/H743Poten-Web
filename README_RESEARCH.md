# 🔬 H743 Potentiostat Research Platform

## 🎯 **สำหรับนักวิจัย: All-in-One Offline Research Tool**

ระบบ Potentiostat H743 ที่ออกแบบมาเพื่อการวิจัยในห้องปฏิบัติการ **ทำงานได้แบบ offline** และมีระบบจัดการข้อมูลครบครัน

### ✨ **คุณสมบัติเด่น**

- 🔬 **4 เครื่องมือหลัก**: CV, SWV, DPV + ระบบจัดการไฟล์
- 📱 **Card-based UI**: Interface สวยงาม ใช้งานง่าย
- 💾 **Offline Mode**: ใช้งานได้โดยไม่ต้องต่อเน็ต
- 📊 **Auto Export**: บันทึกข้อมูลแบบอัตโนมัติ (CSV, PNG, JSON)
- 🌐 **Web File Browser**: ดูและดาวน์โหลดไฟล์ผ่านเว็บ
- 🗄️ **Database Storage**: เก็บข้อมูลอย่างเป็นระบบ

---

## 🚀 **เริ่มต้นใช้งาน (Quick Start)**

### 1. **เปิดระบบแบบ One-Click**
```bash
chmod +x quick_start.sh
./quick_start.sh
```

### 2. **เลือกโหมดการใช้งาน**
- **Full Online Mode**: ครบครัน เชื่อมต่อฮาร์ดแวร์
- **Offline Research Mode**: สำหรับสถานที่ไม่มีเน็ต ใช้ mock data
- **SCPI Server Only**: เฉพาะตัวควบคุมฮาร์ดแวร์
- **File Browser Only**: เฉพาะระบบจัดการไฟล์

---

## 🔧 **การติดตั้งแบบ Manual**

### **สำหรับ Raspberry Pi**
```bash
# 1. สร้าง virtual environment
python3 -m venv poten-env
source poten-env/bin/activate

# 2. ติดตั้ง dependencies
pip install -r requirements-pi.txt
pip install -r requirements-enhanced.txt

# 3. เช็คฮาร์ดแวร์
ls -la /dev/ttyACM* /dev/ttyUSB*

# 4. เริ่มระบบ
python research_platform_offline.py
```

### **สำหรับเครื่อง Development**
```bash
# 1. สร้าง virtual environment
python3 -m venv poten-env
source poten-env/bin/activate

# 2. ติดตั้ง dependencies
pip install -r requirements-enhanced.txt

# 3. เริ่มระบบ (Offline Mode)
python research_platform_offline.py --port 8080
```

---

## 🌐 **การเข้าใช้งาน**

### **หน้าเว็บหลัก**
- **URL**: `http://[ip-address]:8080`
- **Local**: `http://localhost:8080`

### **File Browser (ถ้ามีเน็ต)**
- **URL**: `http://[ip-address]:8080/files`
- **ดาวน์โหลดไฟล์**: `http://[ip-address]:8080/api/files/download/[filename]`

---

## 📊 **การใช้งาน 4 เครื่องมือหลัก**

### 1. **🌊 Cyclic Voltammetry (CV)**
- ตั้งค่า: Start Voltage, End Voltage, Scan Rate
- แสดงผล: กราฟ Voltage vs Current แบบ real-time
- Export: CSV, PNG, JSON อัตโนมัติ

### 2. **📈 Square Wave Voltammetry (SWV)**  
- ตั้งค่า: Start Voltage, End Voltage, Frequency
- สำหรับการวิเคราะห์ความเข้มข้นต่ำ

### 3. **⚡ Differential Pulse Voltammetry (DPV)**
- ตั้งค่า: Start Voltage, End Voltage, Pulse Height  
- ความไวสูง เหมาะกับ trace analysis

### 4. **⚙️ System & Data Export**
- สถิติการทำงาน: จำนวน measurements, data points, files
- ส่งออกข้อมูล: หลายรูปแบบพร้อมกัน
- จัดการไฟล์: ดู, ดาวน์โหลด, organize

---

## 💾 **ระบบจัดเก็บข้อมูล**

### **โครงสร้างไฟล์**
```
H743Poten-Web/
├── exports/                 # ไฟล์ที่ส่งออก
│   ├── cv_20250930_143022.csv
│   ├── cv_20250930_143022.png  
│   └── cv_20250930_143022_metadata.json
├── measurements.db          # ฐานข้อมูล SQLite
└── research_platform.html  # หน้าเว็บหลัก
```

### **รูปแบบการส่งออก**
- **CSV**: ข้อมูลตัวเลข Voltage, Current
- **PNG**: กราฟแสดงผลด้วย matplotlib  
- **JSON**: Metadata + พารามิเตอร์การวัด

---

## 🔄 **โหมดการทำงาน**

### **Online Mode** (เชื่อมต่อ STM32)
```bash 
# Terminal 1: SCPI Server
python scpi_server_standalone.py --port 8081

# Terminal 2: Web Interface  
python research_platform_offline.py --port 8082
```

### **Offline Mode** (Mock Data)
```bash
python research_platform_offline.py --port 8080
```

### **File Browser Only**
```bash
python -c "from file_browser import create_app; create_app().run(port=8083)"
```

---

## 🛠️ **Architecture Overview**

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   Web Interface     │◄──►│   SCPI Server        │◄──►│   STM32 H743    │
│  (Port 8080/8082)   │    │   (Port 8081)        │    │  (Serial Port)  │
└─────────────────────┘    └──────────────────────┘    └─────────────────┘
           │                          │
           ▼                          ▼
┌─────────────────────┐    ┌──────────────────────┐
│   File Browser      │    │   SQLite Database    │
│   (Port 8083)       │    │   (measurements.db)  │  
└─────────────────────┘    └──────────────────────┘
```

---

## 📝 **การแก้ไขปัญหา**

### **ไม่เจอฮาร์ดแวร์**
```bash
# เช็ค USB devices
ls -la /dev/ttyACM* /dev/ttyUSB*

# เช็ค permissions
sudo usermod -a -G dialout $USER
# ต้อง logout/login ใหม่
```

### **Port ซ้ำ**
```bash
# หา process ที่ใช้ port
sudo netstat -tlnp | grep :8080

# ฆ่า process
sudo kill -9 [PID]
```

### **Dependencies ขาด**
```bash
# ติดตั้งใหม่
pip install -r requirements-enhanced.txt

# หรือติดตั้งทีละตัว
pip install flask flask-cors matplotlib numpy pandas
```

---

## 🎯 **สำหรับนักวิจัย**

### **การใช้งานในห้องแลป**
1. **เปิดเครื่อง**: `./quick_start.sh` → เลือก "Offline Research Mode"
2. **ทำการวัด**: ใช้ mock data หรือเชื่อมต่อ STM32 (ถ้ามี)
3. **ส่งออกข้อมูล**: กดปุ่ม Export → ได้ไฟล์ CSV, PNG, JSON
4. **นำข้อมูลไป**: คัดลอกไฟล์จาก `/exports/` หรือใช้ web file browser

### **การใช้งานแบบ Remote**
1. **ต่อเน็ต**: เข้า `http://[pi-ip]:8080/files`
2. **ดาวน์โหลด**: คลิกไฟล์ที่ต้องการ
3. **ดูข้อมูล**: Preview ไฟล์ผ่านเว็บ

---

## 📧 **การติดต่อ**

หากมีปัญหาหรือข้อแนะนำ:
- 📁 **เก็บ log**: ดูใน console ของเว็บ 
- 🐛 **รายงาน bug**: สร้าง GitHub issue
- 💡 **แนะนำฟีเจอร์**: Pull request ยินดีต้อนรับ

---

## 📄 **License**

MIT License - ใช้งานได้ฟรีสำหรับการวิจัยและการศึกษา

---

*H743 Potentiostat Research Platform - Professional Electrochemical Measurements Made Simple* 🔬✨