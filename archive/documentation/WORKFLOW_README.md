# H743Poten Workflow Visualization System

## 🎯 Overview

ระบบ Workflow Visualization เป็นหน้าเว็บแสดงการทำงานเป็น step-by-step สำหรับการวิเคราะห์ข้อมูล CV (Cyclic Voltammetry) ของเครื่องมือ H743 Potentiostat ให้ผู้ใช้มั่นใจและเข้าใจขั้นตอนการวิเคราะห์

## 🚀 Quick Start

### เข้าใช้งาน
```bash
# เริ่มเซิร์ฟเวอร์
python src/run_dev.py

# เปิดเว็บเบราว์เซอร์ไปที่
http://localhost:8080/workflow
```

## 📋 Step-by-Step Workflow

### Step 1: File Selection & Upload
- **วัตถุประสงค์**: เลือกและอัปโหลดไฟล์ข้อมูล CV
- **รองรับไฟล์**: CSV, TXT, XLSX, JSON
- **ขีดจำกัด**: 
  - ไฟล์เดี่ยว: สูงสุด 50MB
  - รวมทั้งหมด: สูงสุด 100MB
- **การทำงาน**: ระบบจะตรวจสอบและแสดงข้อมูลไฟล์ที่ถูกต้อง

### Step 2: Instrument Selection
- **วัตถุประสงค์**: เลือกประเภทเครื่องมือวัด
- **ตัวเลือก**: 
  - H743 Potentiostat (แนะนำ)
  - Generic CV Instrument
  - Custom Configuration
- **การทำงาน**: ระบบจะปรับการตั้งค่าตามเครื่องมือที่เลือก

### Step 3: Data Preprocessing
- **วัตถุประสงค์**: ทำความสะอาดและเตรียมข้อมูล
- **การประมวลผล**:
  - ลบ noise และ outliers
  - ปรับ baseline
  - Smoothing ข้อมูล
  - Normalize ค่า
- **ผลลัพธ์**: ข้อมูลที่พร้อมสำหรับการวิเคราะห์

### Step 4: Peak Detection
- **วัตถุประสงค์**: ตรวจหา peak ใน CV curve
- **เทคนิค**:
  - AI-powered peak detection
  - Signal processing algorithms
  - Multi-scale analysis
- **ผลลัพธ์**: ตำแหน่งและความสูงของ peaks

### Step 5: Cross-Instrument Calibration
- **วัตถุประสงค์**: ปรับเทียบข้อมูลระหว่างเครื่องมือ
- **การทำงาน**:
  - ใช้ Machine Learning สำหรับ calibration
  - เปรียบเทียบกับ reference data
  - แก้ไข systematic errors
- **ผลลัพธ์**: ข้อมูลที่ปรับเทียบแล้ว

### Step 6: Visualization & Export
- **วัตถุประสงค์**: แสดงผลและส่งออกข้อมูล
- **การแสดงผล**:
  - Interactive CV plots
  - Peak analysis charts
  - Statistical summaries
- **การส่งออก**: JSON, CSV, PNG formats

## ⚙️ Technical Features

### File Upload Management
- **Error Handling**: จัดการ 413 Request Entity Too Large
- **Progress Tracking**: แสดง progress bar สำหรับไฟล์ขนาดใหญ่
- **Validation**: ตรวจสอบ file type และขนาด
- **User Feedback**: แสดงข้อความแจ้งเตือนที่เข้าใจง่าย

### Real-time Processing
- **Session Management**: เก็บสถานะ workflow ระหว่างขั้นตอน
- **API Communication**: RESTful API สำหรับแต่ละขั้นตอน
- **Error Recovery**: จัดการ error และ retry mechanisms

### AI Integration
- **Electrochemical Intelligence**: ใช้ AI สำหรับการวิเคราะห์
- **Peak Classification**: Neural network สำหรับจำแนก peaks
- **Concentration Prediction**: พยากรณ์ความเข้มข้น

## 🛠️ Configuration

### File Size Limits (Flask Config)
```python
# src/app.py
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
```

### Error Handlers
```python
# 413 Request Entity Too Large
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'error': 'File too large',
        'message': 'Maximum file size is 100MB',
        'max_size_mb': 100
    }), 413
```

## 📊 Supported Data Formats

### CSV Format
```csv
Potential (V),Current (A),Time (s)
-0.5,-1.2e-6,0.0
-0.4,-1.0e-6,0.1
...
```

### JSON Format
```json
{
  "data": [
    {"potential": -0.5, "current": -1.2e-6, "time": 0.0},
    {"potential": -0.4, "current": -1.0e-6, "time": 0.1}
  ],
  "metadata": {
    "instrument": "H743",
    "scan_rate": "100 mV/s"
  }
}
```

## 🔧 Troubleshooting

### File Upload Issues
1. **413 Error**: ลดขนาดไฟล์หรือแบ่งไฟล์
2. **Timeout**: ตรวจสอบการเชื่อมต่อเครือข่าย
3. **Invalid Format**: ตรวจสอบ format ของไฟล์

### Performance Optimization
1. **Large Files**: ใช้ chunked upload
2. **Memory Usage**: ปิดบราว์เซอร์แท็บอื่น
3. **Processing Speed**: เลือกไฟล์ที่จำเป็นเท่านั้น

## 📁 File Structure

```
workflow_system/
├── templates/
│   └── workflow_visualization.html    # Main UI
├── static/js/
│   └── workflow_visualization.js      # Frontend logic
├── src/routes/
│   └── workflow_routes.py            # Backend API
└── static/css/
    └── workflow_styles.css           # Styling
```

## 🔄 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/workflow` | GET | Main workflow page |
| `/api/workflow/status` | GET | Get workflow status |
| `/api/workflow/scan-files` | POST | Upload and scan files |
| `/api/workflow/preprocess` | POST | Data preprocessing |
| `/api/workflow/detect-peaks` | POST | Peak detection |
| `/api/workflow/calibrate` | POST | Cross-instrument calibration |
| `/api/workflow/generate-visualization` | POST | Generate plots |
| `/api/workflow/export` | POST | Export results |

## ✅ Success Indicators

ระบบทำงานสำเร็จเมื่อ:
- ✅ ไฟล์อัปโหลดได้โดยไม่มี 413 error
- ✅ แต่ละ step แสดง progress และผลลัพธ์
- ✅ สามารถเปลี่ยนระหว่าง step ได้
- ✅ Visualization แสดงผลถูกต้อง
- ✅ Export ได้ไฟล์ผลลัพธ์

## 🎨 User Experience

### Visual Feedback
- **Progress Bars**: แสดงความคืบหน้า
- **Step Indicators**: แสดงขั้นตอนปัจจุบัน
- **Success/Error Messages**: ข้อความแจ้งเตือนชัดเจอ
- **Interactive Elements**: ปุ่มและฟอร์มที่ตอบสนอง

### Confidence Building
- **Step-by-step Guide**: แนะนำทุกขั้นตอน
- **Real-time Validation**: ตรวจสอบข้อมูลทันที
- **Clear Error Messages**: อธิบายปัญหาและวิธีแก้ไข
- **Progress Tracking**: แสดงความคืบหน้าอย่างชัดเจอ

---

## 📞 Support

หากพบปัญหาหรือต้องการความช่วยเหลือ:
1. ตรวจสอบ browser console สำหรับ error messages
2. ดู server logs ใน terminal
3. ทดลองใช้ไฟล์ทดสอบขนาดเล็กก่อน
4. ตรวจสอบการเชื่อมต่อเครือข่าย

**Status**: ✅ Production Ready
**Last Updated**: August 2025
**Version**: 1.0.0
