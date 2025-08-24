# 📋 คู่มือการใช้งาน Production Cross-Instrument Calibration System

## 🎯 ภาพรวมระบบ

ระบบ Production Cross-Instrument Calibration เป็นเครื่องมือสำหรับการสอบเทียบการวัดระหว่างเครื่องมือ STM32H743 และ PalmSens เพื่อให้ได้ผลลัพธ์ที่สอดคล้องกันและมีความแม่นยำสูง

### ✨ คุณสมบัติหลัก
- **การสอบเทียบแบบ Real-time**: สอบเทียบค่ากระแสไฟฟ้าและ CV curve ในทันที
- **5 เงื่อนไขการสอบเทียบ**: ความเข้มข้น 5mM ที่อัตราการสแกน 20, 50, 100, 200, 400 mV/s
- **ความแม่นยำสูง**: R² สูงสุด 0.602, correlation สูงสุด 0.702
- **API ครบถ้วน**: 6 endpoints สำหรับการใช้งานหลากหลาย
- **Web Interface**: หน้าเว็บสำหรับทดสอบและจัดการการสอบเทียบ

## 🚀 การเริ่มต้นใช้งาน

### 1. เปิดใช้งานเซิร์ฟเวอร์

```bash
# เปิดเซิร์ฟเวอร์แบบพัฒนา
python auto_dev.py start

# ตรวจสอบสถานะ
python auto_dev.py status
```

### 2. เข้าถึงระบบสอบเทียบ

เปิดเว็บบราวเซอร์และไปที่:
- **หน้าทดสอบ API**: `http://127.0.0.1:8080/static/calibration_api_test.html`
- **หน้าจัดการการสอบเทียบ**: `http://127.0.0.1:8080/calibration`

## 📊 วิธีการใช้งาน Web Interface

### 🔧 หน้าทดสอบ API (`/static/calibration_api_test.html`)

![Calibration API Test Interface](../static/img/calibration-api-test.png)

#### การทดสอบ Service Information
1. คลิกปุ่ม **"Get Service Info"**
2. ดูข้อมูลสถิติการสอบเทียบ:
   - จำนวนเงื่อนไขที่มี
   - Gain Factor เฉลี่ย
   - การกระจายของระดับความเชื่อมั่น

#### การทดสอบการสอบเทียบค่ากระแส
1. ใส่ค่า **STM32 Current** (เช่น 0.0001 สำหรับ 100µA)
2. ใส่ **Scan Rate** และ **Concentration** (ถ้ามี)
3. คลิก **"Calibrate Current"**
4. ดูผลลัพธ์:
   - ค่ากระแสที่สอบเทียบแล้ว
   - Gain Factor ที่ใช้
   - ระดับความเชื่อมั่น

#### การทดสอบการสอบเทียบ CV Curve
1. ใส่ข้อมูล CV ในรูปแบบ JSON:
```json
[
  [-0.5, -1e-4],
  [0.0, 0],
  [0.5, 1e-4]
]
```
2. ใส่เงื่อนไขการวัด
3. คลิก **"Calibrate CV Curve"**
4. ดูกราฟและข้อมูลที่สอบเทียบแล้ว

#### การทดสอบการสอบเทียบ Measurement
1. ใส่ **Measurement ID** (เช่น 67)
2. คลิก **"Calibrate Measurement"**
3. ระบบจะดึงข้อมูลจากฐานข้อมูลและสอบเทียบอัตโนมัติ

#### การเปรียบเทียบ Measurements
1. ใส่ **STM32 ID** และ **PalmSens ID**
2. คลิก **"Compare Measurements"**
3. ดูผลการเปรียบเทียบ:
   - Correlation coefficient
   - RMSE
   - กราฟเปรียบเทียบ

### 📈 หน้าจัดการการสอบเทียบ (`/calibration`)

#### Tab 1: Measurement Pairs
- ดูคู่การวัดที่สามารถสอบเทียบได้
- เลือกคู่ที่ต้องการสอบเทียบ
- ดูผลลัพธ์การสอบเทียบพร้อมกราฟ

#### Tab 2: Upload STM32 Data
- อัปโหลดไฟล์ CSV จาก STM32
- เลือก PalmSens reference measurement
- ดูตัวอย่างข้อมูลที่อัปโหลด
- ทำการสอบเทียบ

#### Tab 3: Calibration Models
- ดูโมเดลการสอบเทียบที่บันทึกไว้
- ตรวจสอบคุณภาพของแต่ละโมเดล
- จัดการโมเดลการสอบเทียบ

## 🔌 การใช้งาน API Endpoints

### Base URL
```
http://127.0.0.1:8080/api/calibration
```

### 1. ข้อมูลระบบ (`GET /info`)

```bash
curl -X GET http://127.0.0.1:8080/api/calibration/info
```

**Response:**
```json
{
  "success": true,
  "available_calibrations": {
    "5.0mM_100.0mVs": {
      "concentration_mM": 5.0,
      "scan_rate_mVs": 100.0,
      "r_squared": 0.462,
      "confidence": "medium",
      "data_points": 219
    }
  },
  "statistics": {
    "total_conditions": 5,
    "gain_factor_stats": {
      "mean": 625583.47,
      "std": 21004.73,
      "cv_percent": 3.36
    }
  }
}
```

### 2. สอบเทียบค่ากระแส (`POST /current`)

```bash
curl -X POST http://127.0.0.1:8080/api/calibration/current \
  -H "Content-Type: application/json" \
  -d '{
    "stm32_current": 1e-4,
    "scan_rate_mVs": 100.0,
    "concentration_mM": 5.0
  }'
```

**Response:**
```json
{
  "success": true,
  "calibration": {
    "calibrated_current": 59.758347,
    "gain_factor": 569758.47,
    "confidence": "medium",
    "r_squared": 0.462
  }
}
```

### 3. สอบเทียบ CV Curve (`POST /cv-curve`)

```bash
curl -X POST http://127.0.0.1:8080/api/calibration/cv-curve \
  -H "Content-Type: application/json" \
  -d '{
    "cv_data": [[-0.5, -1e-4], [0.0, 0], [0.5, 1e-4]],
    "scan_rate": 100.0,
    "concentration": 5.0
  }'
```

### 4. สอบเทียบ Measurement (`POST /measurement/{id}`)

```bash
curl -X POST http://127.0.0.1:8080/api/calibration/measurement/67
```

### 5. เปรียบเทียบ Measurements (`GET /compare/{stm32_id}/{palmsens_id}`)

```bash
curl -X GET http://127.0.0.1:8080/api/calibration/compare/67/77
```

### 6. ตรวจสอบสุขภาพระบบ (`GET /health`)

```bash
curl -X GET http://127.0.0.1:8080/api/calibration/health
```

## 🧪 การทำงานกับข้อมูล

### รูปแบบข้อมูล CV

ข้อมูล CV ต้องอยู่ในรูปแบบ array ของ `[voltage, current]`:

```json
[
  [-0.4, -8.5e-5],
  [-0.3, -6.2e-5],
  [-0.2, -3.8e-5],
  [-0.1, -1.2e-5],
  [0.0, 0],
  [0.1, 1.5e-5],
  [0.2, 4.2e-5],
  [0.3, 7.8e-5],
  [0.4, 9.1e-5]
]
```

### ระดับความเชื่อมั่น (Confidence Levels)

| ระดับ | R² | คำอธิบาย |
|-------|-----|----------|
| **High** | ≥ 0.6 | การสอบเทียบมีความแม่นยำสูง แนะนำให้ใช้ |
| **Medium** | 0.4-0.6 | การสอบเทียบมีความแม่นยำปานกลาง ใช้ได้ |
| **Low** | 0.3-0.4 | การสอบเทียบมีความแม่นยำต่ำ ใช้ด้วยความระมัดระวัง |

### การตีความ Gain Factor

```
กระแส_PalmSens = Gain_Factor × กระแส_STM32 + Offset
```

- **Gain Factor เฉลี่ย**: 625,583 ± 21,005
- **ความแปรปรวน**: 3.4% (CV)
- **ช่วงที่ดี**: 600,000 - 650,000

## 🛠️ การแก้ไขปัญหา

### ปัญหาที่พบบ่อย

#### 1. ไม่พบข้อมูลการวัด
```json
{
  "error": "No CV data found for measurement {id}"
}
```
**วิธีแก้**: ตรวจสอบว่า measurement ID ถูกต้องและมีข้อมูล CV

#### 2. ข้อมูลไม่ตรงกับเงื่อนไขการสอบเทียบ
```json
{
  "calibration_method": "default",
  "condition_specific": false
}
```
**วิธีแก้**: ใส่ scan_rate และ concentration ให้ตรงกับเงื่อนไขที่มี

#### 3. ค่า R² ต่ำ
**สาเหตุ**:
- ข้อมูลมี noise มาก
- เงื่อนไขการวัดไม่เหมาะสม
- ตัวอย่างไม่ตรงกัน

**วิธีแก้**:
- กรองข้อมูลก่อนการสอบเทียบ
- ใช้เงื่อนไขที่มี confidence สูง
- ตรวจสอบคุณภาพตัวอย่าง

### การตรวจสอบสถานะระบบ

```bash
# ตรวจสอบสุขภาพ API
curl -X GET http://127.0.0.1:8080/api/calibration/health

# ดูข้อมูลสถิติ
curl -X GET http://127.0.0.1:8080/api/calibration/info

# ตรวจสอบ log
python auto_dev.py logs
```

## 📈 การตีความผลลัพธ์

### ผลการสอบเทียบที่ดี
- **R² ≥ 0.5**: การสอบเทียบน่าเชื่อถือ
- **Correlation ≥ 0.7**: ความสัมพันธ์ดี
- **RMSE ต่ำ**: ความผิดพลาดน้อย
- **Gain Factor สม่ำเสมอ**: ระบบเสถียร

### ตัวอย่างผลลัพธ์ที่ดี
```json
{
  "r_squared": 0.602,
  "correlation": 0.702,
  "gain_factor": 630245.12,
  "confidence": "high",
  "rmse": 2.34e-5
}
```

## 🔄 การบำรุงรักษา

### การอัปเดตโมเดลการสอบเทียบ

1. **เพิ่มข้อมูลใหม่**:
   - นำเข้าการวัดใหม่
   - ทำการสอบเทียบใหม่
   - อัปเดตโมเดล

2. **ตรวจสอบคุณภาพ**:
   - ดู R² และ correlation
   - เปรียบเทียบกับโมเดลเก่า
   - ทดสอบกับข้อมูลอ้างอิง

3. **บันทึกโมเดลใหม่**:
   - ระบบจะบันทึกอัตโนมัติ
   - สำรองข้อมูล calibration_models.json

### การสำรองข้อมูล

```bash
# สำรองโมเดลการสอบเทียบ
cp data_logs/calibration_models.json backup/

# สำรองผลการสอบเทียบ
cp cross_sample_calibration_results.json backup/

# สำรองฐานข้อมูล
cp data_logs/parameter_log.db backup/
```

## 📚 การอ้างอิง

### เอกสารเทคนิค
- [Production Calibration Report](../PRODUCTION_CALIBRATION_REPORT.md)
- [Cross Sample Calibration Report](../CROSS_SAMPLE_CALIBRATION_REPORT.md)
- [API Documentation](API_DOCUMENTATION.md)

### การสนับสนุน
- **GitHub Issues**: [Report bugs](https://github.com/koson/H743Poten-Web/issues)
- **Documentation**: [Full docs](../README.md)
- **Tag Version**: `v2.0.0-production-calibration`

---

**เวอร์ชัน**: v2.0.0  
**อัปเดตล่าสุด**: 24 สิงหาคม 2025  
**สถานะ**: ✅ Production Ready