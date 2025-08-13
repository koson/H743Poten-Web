# CSV Data Emulation System

ระบบจำลองข้อมูล CV จากไฟล์ CSV สำหรับ H743Poten-Web

## ภาพรวม

ระบบนี้ช่วยให้คุณสามารถ:
- โหลดข้อมูล CV จากไฟล์ CSV 
- จำลองการทำงานของเครื่องจริงทั้งด้าน timing และข้อมูล
- ควบคุมความเร็วในการเล่นข้อมูล (1x, 2x, 0.5x ฯลฯ)
- เล่นข้อมูลแบบวนลูป
- ข้ามไปยังจุดเวลาที่ต้องการ
- ใช้งานร่วมกับ Web Interface

## รูปแบบไฟล์ CSV

ไฟล์ CSV ต้องมีคอลัมน์อย่างน้อย:
- **Time/Timestamp/T**: เวลา (วินาที)
- **Voltage/V/Potential**: แรงดันไฟฟ้า (โวลต์) 
- **Current/I/Current_A**: กระแสไฟฟ้า (แอมแปร์)

### ตัวอย่างไฟล์ CSV:
```csv
time,voltage,current
0.000,0.000,0.000000000
0.100,-0.050,0.000000123
0.200,-0.100,0.000000245
0.300,-0.150,0.000000367
...
```

## การใช้งาน

### 1. ผ่าน Web API

#### โหลดไฟล์ CSV:
```bash
curl -X POST http://localhost:5000/api/emulation/csv/load \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/path/to/your/data.csv"}'
```

#### เริ่มการจำลอง:
```bash
# เล่นที่ความเร็วปกติ
curl -X POST http://localhost:5000/api/emulation/csv/start \
  -H "Content-Type: application/json" \
  -d '{"speed": 1.0, "loop": false}'

# เล่นที่ความเร็ว 2 เท่า และวนลูป
curl -X POST http://localhost:5000/api/emulation/csv/start \
  -H "Content-Type: application/json" \
  -d '{"speed": 2.0, "loop": true}'
```

#### ตรวจสอบสถานะ:
```bash
curl http://localhost:5000/api/emulation/csv/status
```

#### หยุดการจำลอง:
```bash
curl -X POST http://localhost:5000/api/emulation/csv/stop
```

#### ข้ามไปยังเวลาที่ต้องการ:
```bash
curl -X POST http://localhost:5000/api/emulation/csv/seek \
  -H "Content-Type: application/json" \
  -d '{"time": 10.5}'
```

### 2. ผ่าน SCPI Commands

#### โหลดข้อมูล:
```
csv:load /path/to/your/data.csv
```

#### เริ่มการจำลอง:
```
csv:start 1.5 true  # ความเร็ว 1.5x, วนลูป
```

#### ตรวจสอบข้อมูล:
```
csv:info?           # ข้อมูลไฟล์
csv:progress?       # ความคืบหน้า
```

#### ข้ามไปยังเวลา:
```
csv:seek 25.0       # ข้ามไปที่ 25 วินาที
```

#### หยุดการจำลอง:
```
csv:stop
```

#### ดึงข้อมูล:
```
poten:csv:data?     # ดึงข้อมูลปัจจุบัน
```

### 3. การใช้งานในโค้ด Python

```python
from hardware.mock_scpi_handler import MockSCPIHandler

# สร้าง handler
handler = MockSCPIHandler()
handler.connect()

# โหลดข้อมูล CSV
success = handler.load_csv_data('/path/to/data.csv')

# เริ่มการจำลองที่ความเร็ว 1.5 เท่า
success = handler.start_csv_emulation(speed=1.5, loop=True)

# ดูข้อมุล
info = handler.get_csv_info()
progress = handler.get_csv_progress()

# หยุด
handler.stop_csv_emulation()
```

## คุณสมบัติพิเศษ

### 1. การตรวจจับคอลัมน์อัตโนมัติ
ระบบจะตรวจจับชื่อคอลัมน์อัตโนมัติ รองรับ:
- Time: `time`, `timestamp`, `t`
- Voltage: `voltage`, `v`, `potential`  
- Current: `current`, `i`, `current_a`, `current_ma`

### 2. การควบคุมความเร็ว
- `1.0` = ความเร็วปกติ (real-time)
- `2.0` = เร็วขึ้น 2 เท่า
- `0.5` = ช้าลง 2 เท่า

### 3. การวนลูป
เมื่อข้อมูลเล่นจบ สามารถกลับไปเริ่มใหม่อัตโนมัติ

### 4. การข้ามเวลา (Seek)
สามารถข้ามไปยังจุดเวลาใดก็ได้ในข้อมูล

## การทดสอบ

รันไฟล์ทดสอบ:
```bash
python test_csv_emulation.py
```

ทดสอบจะครอบคลุม:
- การโหลดไฟล์ CSV
- การเล่นข้อมูลตาม timing
- การควบคุมผ่าน SCPI commands
- การทำงานปกติของ mock simulation

## ข้อมูลตัวอย่าง

ไฟล์ `sample_data/cv_sample.csv` มีข้อมูลตัวอย่างสำหรับทดสอบ:
- ช่วงแรงดัน: -0.5V ถึง +0.5V
- ระยะเวลา: 4 วินาที
- 41 จุดข้อมูล

## Integration กับระบบเดิม

ระบบ CSV emulation ทำงานผ่าน `MockSCPIHandler` และใช้ได้เฉพาะเมื่อ:
1. ใช้ Mock handler (สำหรับการพัฒนา/ทดสอบ)
2. ไม่เชื่อมต่อกับเครื่องจริง

เมื่อใช้ CSV emulation:
- ข้อมูลจาก CSV จะแทนที่ mock data
- Timing จะเป็นไปตามข้อมูลจริง
- สามารถใช้ Web Interface ปกติได้

## ข้อจำกัด

1. ใช้ได้เฉพาะกับ Mock handler
2. ไฟล์ CSV ต้องมีรูปแบบที่ถูกต้อง
3. ข้อมูลทั้งหมดจะโหลดเข้า memory
4. การ seek อาจไม่แม่นยำ 100% ขึ้นกับ sampling rate

## การ Troubleshooting

### ปัญหาการโหลดไฟล์
- ตรวจสอบ path ไฟล์
- ตรวจสอบรูปแบบ CSV
- ตรวจสอบสิทธิ์การอ่านไฟล์

### ปัญหาการเล่นข้อมูล
- ตรวจสอบว่าโหลดข้อมูลแล้ว
- ตรวจสอบ progress ผ่าน API
- ดู log สำหรับ error messages

### การปรับแต่งประสิทธิภาพ
- ลดขนาดไฟล์ CSV หากใหญ่เกินไป
- ปรับ sleep time ใน emulation worker
- ใช้ความเร็วที่เหมาะสม
