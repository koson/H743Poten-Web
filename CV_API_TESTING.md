# 🔬 STM32 CV .NET API Testing Guide

ไกด์การทดสอบ STM32 CV Web API ที่ถูกย้ายจาก Python มาเป็น .NET

## 📋 Prerequisites

### Windows:
- .NET 8.0 SDK: https://dotnet.microsoft.com/download
- STM32 เชื่อมต่อผ่าน USB (COM port)

### Linux (Raspberry Pi):
```bash
sudo apt update
sudo apt install -y dotnet-sdk-8.0
```

## 🚀 วิธีการทดสอบ

### 1. **Quick Start (Windows)**
```cmd
# รันด้วย batch script
test_cv_api.bat
```

### 2. **Quick Start (Linux)**
```bash
# รันด้วย shell script
./test_cv_api.sh
```

### 3. **Manual Testing**

#### Build Project:
```bash
dotnet build STM32CVWebAPI.csproj
```

#### Run API Server:
```bash
dotnet run --project STM32CVWebAPI.csproj
```

#### Access Web Interface:
เปิดเบราว์เซอร์: http://localhost:5000

### 4. **API Testing with Python Client**
```bash
# เริ่ม API server ก่อน
dotnet run --project STM32CVWebAPI.csproj &

# รัน test client
python3 test_cv_api_client.py
```

### 5. **API Testing with curl**
```bash
# Check health
curl http://localhost:5000/health

# Check CV status
curl http://localhost:5000/api/cv/status

# Check STM32 connection
curl http://localhost:5000/api/stm32/status

# Start CV scan
curl -X POST http://localhost:5000/api/cv/start \
  -H "Content-Type: application/json" \
  -d '{
    "beginVoltage": -1.0,
    "upperVoltage": 1.0,
    "lowerVoltage": -1.0,
    "scanRate": 0.05,
    "cycles": 3,
    "enableAutoRangeDebug": true
  }'

# Get data
curl http://localhost:5000/api/cv/data/all

# Stop scan
curl -X POST http://localhost:5000/api/cv/stop
```

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API documentation |
| GET | `/health` | Server health check |
| GET | `/api/cv/status` | CV scan status |
| POST | `/api/cv/start` | Start CV scan |
| POST | `/api/cv/stop` | Stop CV scan |
| GET | `/api/cv/data` | Get new data points |
| GET | `/api/cv/data/all` | Get all data points |
| POST | `/api/cv/clear` | Clear all data |
| GET | `/api/stm32/status` | STM32 connection status |

## 📊 CV Scan Configuration

```json
{
  "beginVoltage": -1.0,      // Start voltage (V)
  "upperVoltage": 1.0,       // Upper limit (V)  
  "lowerVoltage": -1.0,      // Lower limit (V)
  "scanRate": 0.05,          // Scan rate (V/s)
  "cycles": 3,               // Number of cycles
  "enableAutoRangeDebug": true  // Debug output
}
```

## 🔌 STM32 Connection

### Windows COM Ports:
- Auto-detects: COM10, COM6, COM3, COM4, COM5

### Linux Serial Ports:
- Auto-detects: /dev/ttyACM0, /dev/ttyACM1, /dev/ttyUSB0, /dev/ttyUSB1

## 📈 Web Interface Features

- ✅ Real-time CV plot (Plotly.js)
- ✅ Parameter configuration
- ✅ Connection status monitoring
- ✅ Data export (JSON)
- ✅ System log with debug info

## 🧪 Test Scenarios

### 1. **Connection Test**
```bash
python3 test_cv_api_client.py
# Select option 2: Check STM32 Connection
```

### 2. **Quick CV Scan**
```bash
python3 test_cv_api_client.py  
# Select option 7: Run Test Scan (30s)
```

### 3. **Custom CV Scan**
```bash
python3 test_cv_api_client.py
# Select option 3: Start CV Scan
# Monitor with option 1: Check Status
# View data with option 5: Get Data
```

### 4. **Web Interface Test**
1. เปิด http://localhost:5000
2. กำหนดพารามิเตอร์ CV
3. กดปุ่ม "🚀 Start CV Scan"
4. ดู real-time plot
5. Export ข้อมูลเป็น JSON

## 🐛 Troubleshooting

### ❌ ".NET SDK not found"
- Windows: ติดตั้งจาก https://dotnet.microsoft.com/download
- Linux: `sudo apt install dotnet-sdk-8.0`

### ❌ "STM32 not connected"
- ตรวจสอบ USB cable
- Windows: ดู Device Manager สำหรับ COM port
- Linux: `ls /dev/ttyACM*` หรือ `lsusb`

### ❌ "Build failed"
- ตรวจสอบ .NET SDK version: `dotnet --version`
- ลบ bin/obj: `dotnet clean`

### ❌ "Port in use"
- Windows: `netstat -ano | findstr :5000`
- Linux: `sudo lsof -i :5000`

## 📋 Expected Output

### Successful CV Scan:
```
✅ STM32 ready for CV testing
🚀 Starting CV Scan: -1.0V to 1.0V, rate: 0.05V/s, cycles: 3
Collecting CV data...
AUTO-RANGE DEBUG: V=-0.9895, Range=0, RGain=1000, I=-0.00 µA, DAC1=425 (±1mA)
📈 Points collected: 50
📈 Points collected: 100
✅ CV scan complete: 240 data points collected
```

### Web Interface:
- 🟢 STM32: Connected
- 🟡 Scan: Running
- 📊 Data Points: 150
- Real-time CV plot updating

## 🎯 Performance Expectations

- **Connection Time**: < 2 seconds
- **Scan Start**: < 1 second  
- **Data Rate**: ~5-10 points/second
- **Memory Usage**: < 50MB
- **CPU Usage**: < 5%

## 📁 Generated Files

- `cv_data_TIMESTAMP.json` - Export ข้อมูล CV
- API logs ใน console output
- Web interface accessible ที่ port 5000

---

## 🔄 Migration from Python

ไฟล์นี้ถูกย้ายจาก Python `test_cv_final.py`:
- ✅ Serial communication porting
- ✅ CV data parsing  
- ✅ Auto-range debugging
- ✅ Real-time data streaming
- ✅ Web interface
- ✅ Cross-platform support

**Python Reference**: `test_cv_final.py` (สำหรับ reference เท่านั้น)