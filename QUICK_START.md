# Quick Start: CSV Data Emulation

## การเริ่มต้นใช้งาน CSV Emulation สำหรับ H743Poten-Web

### 1. การติดตั้งและเริ่มต้น

```bash
# Clone repository และเข้าไปในโฟลเดอร์
cd H743Poten-Web

# ติดตั้ง dependencies
pip install flask pyserial

# เริ่ม web application
python src/app.py
```

เปิดเบราว์เซอร์ไปที่: http://localhost:5000

### 2. การใช้งาน CSV Emulation ผ่าน Web Interface

#### ขั้นตอนที่ 1: เชื่อมต่อ Mock Device
1. คลิก **"Connect"** ที่มุมขวาบน
2. ตรวจสอบสถานะเป็น "Connected"

#### ขั้นตอนที่ 2: โหลดไฟล์ CSV
1. ในส่วน **"CSV Data Emulation"** (sidebar)
2. คลิก **"Choose File"** และเลือกไฟล์ CSV
3. คลิก **"Load CSV"**
4. ตรวจสอบข้อมูลในส่วน **"CSV Status"**

#### ขั้นตอนที่ 3: เริ่มการจำลอง
1. ตั้งค่าความเร็ว (Speed): 1.0 = เวลาจริง, 2.0 = เร็ว 2 เท่า
2. เลือก **"Loop"** หากต้องการเล่นวนลูป
3. คลิก **"Start Emulation"**
4. ดู progress bar และข้อมูลที่เปลี่ยนแปลง

#### ขั้นตอนที่ 4: ควบคุมการเล่น
- **Seek**: กรอกเวลา (วินาที) และคลิก "Seek" เพื่อข้ามไป
- **Stop**: คลิก "Stop Emulation" เพื่อหยุด

### 3. การใช้งานผ่าน UART Console

#### คำสั่งพื้นฐาน:
```
# โหลดไฟล์ CSV
csv:load sample_data/cv_sample.csv

# ตรวจสอบข้อมูล
csv:info?

# เริ่มการจำลองที่ความเร็ว 1.5 เท่า
csv:start 1.5 false

# ตรวจสอบความคืบหน้า
csv:progress?

# ข้ามไปที่ 10 วินาที
csv:seek 10.0

# หยุดการจำลอง
csv:stop
```

#### การดึงข้อมูล:
```
# ดึงข้อมูลปัจจุบัน
poten:csv:data?

# ตรวจสอบสถานะเครื่อง
poten:stat?
```

### 4. รูปแบบไฟล์ CSV ที่รองรับ

#### Header ที่รองรับ:
- **Time**: `time`, `timestamp`, `t`
- **Voltage**: `voltage`, `v`, `potential`
- **Current**: `current`, `i`, `current_a`, `current_ma`

#### ตัวอย่างไฟล์ CSV:
```csv
time,voltage,current
0.000,0.000,0.000000000
0.100,-0.050,0.000000123
0.200,-0.100,0.000000245
...
```

### 5. ทดสอบระบบ

```bash
# รันการทดสอบทั้งระบบ
python test_csv_emulation.py
```

### 6. คุณสมบัติพิเศษ

#### การควบคุมความเร็ว:
- `0.5x`: ช้าลง 2 เท่า
- `1.0x`: ความเร็วปกติ (real-time)
- `2.0x`: เร็วขึ้น 2 เท่า

#### การวนลูป:
เมื่อเปิด Loop ข้อมูลจะเล่นซ้ำอัตโนมัติ

#### การ Seek:
สามารถข้ามไปยังจุดเวลาใดก็ได้

### 7. Integration กับระบบเดิม

CSV Emulation ทำงานแทน mock data เมื่อ:
- ใช้ Mock SCPI Handler
- โหลดข้อมูล CSV เรียบร้อยแล้ว
- เริ่มการจำลอง

ข้อมูลจะแสดงใน:
- Graph ปกติ (Plotly)
- Export ข้อมูลเป็น CSV
- UART Console responses

### 8. การ Troubleshooting

#### ปัญหาโหลดไฟล์:
- ตรวจสอบรูปแบบ CSV
- ตรวจสอบ path ไฟล์
- ดู error message ใน Console

#### ปัญหาการเล่น:
- ตรวจสอบว่าโหลดข้อมูลแล้ว
- ตรวจสอบ connection status
- ดู progress bar

#### Performance:
- ไฟล์ CSV ไม่ควรใหญ่เกิน 10MB
- ใช้ความเร็วที่เหมาะสม
- ปิด loop หากไม่จำเป็น

### 9. การพัฒนาเพิ่มเติม

#### เพิ่มรูปแบบไฟล์ใหม่:
แก้ไขใน `csv_data_emulator.py`:
```python
self.expected_columns = {
    'time': ['time', 'timestamp', 't', 'your_time_column'],
    # เพิ่มรูปแบบใหม่
}
```

#### เพิ่ม API endpoints:
แก้ไขใน `app.py`:
```python
@app.route('/api/emulation/csv/your_endpoint')
def your_function():
    # เพิ่มฟังก์ชันใหม่
```

### 10. ข้อมูลตัวอย่าง

ใช้ไฟล์ `sample_data/cv_sample.csv` เพื่อทดสอบ:
- 41 จุดข้อมูล
- ช่วงแรงดัน: -0.5V ถึง +0.5V
- ระยะเวลา: 4 วินาที
- รูปแบบ CV แบบ cyclic

---

## สรุป

ระบบ CSV Emulation ช่วยให้คุณสามารถ:
✅ จำลองข้อมูลจริงจากไฟล์ CSV  
✅ ควบคุม timing และความเร็วได้  
✅ ทำงานร่วมกับ Web Interface  
✅ ใช้งานผ่าน SCPI commands  
✅ Export และวิเคราะห์ข้อมูลได้  

เหมาะสำหรับ:
- การทดสอบ algorithm
- การพัฒนา Web Interface
- การนำเสนอข้อมูล
- การทดสอบระบบโดยไม่ต้องมีเครื่องจริง
