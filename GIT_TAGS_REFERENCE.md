# 🏷️ Git Tags Reference Guide

## Step 4: Cross-Instrument Calibration Tags

สร้างไว้เมื่อ: 6 กันยายน 2025  
Branch: Cross-Instrument-Calibration

---

## 🎯 Main Tags

### `v4.0-cross-instrument-calibration`
**ระบบหลักที่สมบูรณ์**
- ✅ Cross-Instrument Calibration system ครบถ้วน
- ✅ Database, API, Dashboard ทำงานได้
- ✅ Test data integration เสร็จสิ้น
- ✅ Documentation ครบถ้วน

```bash
git checkout v4.0-cross-instrument-calibration
```

### `step4-testdata-location`
**อ้างอิงตำแหน่ง Test Data**
- 📊 Test_data/ directory (1,682 CSV files)
- 📍 Source: commit ff90897394dbef885c9b887bcc6b58cf139f0637
- 📁 STM32 data structure และ file counts
- 🔍 Quick find commands

```bash
git show step4-testdata-location
```

### `step4-process-guide`
**คู่มือ Process ทั้งหมด**
- 🔧 8 ขั้นตอนการพัฒนา
- 🛠️ Development workflow
- 📝 Key documentation files
- 🎯 Replication steps

```bash
git show step4-process-guide
```

---

## 🔍 การใช้งาน Tags

### ดู Tag ทั้งหมด
```bash
git tag -l
```

### ดู Tag ที่เกี่ยวข้องกับ Step 4
```bash
git tag -l | grep step4
git tag -l | grep v4.0
```

### ดูข้อความใน Tag
```bash
git show step4-testdata-location
git show step4-process-guide
git tag -l -n10 "v4.0*"
```

### Checkout ไปยัง Tag
```bash
git checkout v4.0-cross-instrument-calibration
git checkout step4-testdata-location
```

---

## 📊 Test Data Quick Access

### ตำแหน่งข้อมูล
```
Test_data/
├── Stm32/ (1,682 CSV files)
│   ├── Pipot_Ferro_0_5mM/ (275 files)
│   ├── Pipot_Ferro_1_0mM/ (247 files) 
│   ├── Pipot_Ferro_5_0mM/ (275 files)
│   ├── Pipot_Ferro_10mM/ (280 files)
│   ├── Pipot_Ferro_20mM/ (330 files)
│   └── Pipot_Ferro_50mM/ (275 files)
├── Palmsens/
├── converted_stm32/
└── raw_stm32/
```

### คำสั่งเช็คข้อมูล
```bash
# นับไฟล์ CSV
find Test_data/Stm32/ -name "*.csv" | wc -l

# ดูโครงสร้างโฟลเดอร์
ls Test_data/Stm32/*/

# ดู commit ต้นทาง
git show ff90897394dbef885c9b887bcc6b58cf139f0637
```

---

## 🚀 Quick Start จาก Tag

### 1. Checkout Tag
```bash
git checkout v4.0-cross-instrument-calibration
```

### 2. Setup Environment
```bash
source test_env/bin/activate
pip install pandas scipy numpy flask
```

### 3. Run System
```bash
python test_flask_calibration.py
```

### 4. Access Dashboard
```
http://localhost:5002/api/calibration/dashboard
```

---

## 📝 Documentation Files

หลังจาก checkout tag แล้ว ดูเอกสารได้ที่:

### Jupyter Notebooks
- `Cross-Instrument-Calibration.ipynb` - Planning notebook
- `Step4_Cross_Instrument_Calibration_Summary.ipynb` - Complete guide

### Markdown Docs
- `STEP4_COMPLETE_GUIDE.md` - Detailed documentation
- `STEP4_SUCCESS.md` - Success summary

### Python Scripts
- `step4_summary.py` - Quick summary
- `test_stm32_integration.py` - Integration tests
- `test_flask_calibration.py` - Flask server

---

## 🎯 การค้นหาใน Future

### หา Test Data
```bash
git tag -l | grep testdata
git show step4-testdata-location
```

### หา Process Guide
```bash
git tag -l | grep process
git show step4-process-guide
```

### หา Complete System
```bash
git tag -l | grep v4.0
git checkout v4.0-cross-instrument-calibration
```

---

**สร้างโดย: GitHub Copilot**  
**วันที่: 6 กันยายน 2025**  
**Branch: Cross-Instrument-Calibration**
