# STM32 Unit Conversion & Enhanced CV Analysis Guide

## 📋 Overview
คู่มือนี้จะแนะนำการใช้งานระบบแปลงหน่วยและวิเคราะห์ CV ที่ปรับปรุงแล้ว สำหรับไฟล์ STM32 ที่มีหน่วยเป็น A (แอมแปร์) แทนที่จะเป็น µA (ไมโครแอมแปร์)

## 🗂️ Folder Structure
```
H743Poten-Web/
├── stm32_unit_converter.py     # สคริปต์แปลงหน่วย A → µA  
├── enhanced_cv_calibration.py  # วิเคราะห์ CV แบบขยาย
├── test_unit_converter.py      # ทดสอบการแปลงหน่วย
└── test_data/
    ├── raw_stm32/              # ไฟล์ STM32 ต้นฉบับ (A units)
    └── converted_stm32/        # ไฟล์ที่แปลงแล้ว (µA units)
```

## 🚀 Quick Start Guide

### วิธีที่ 1: ใช้งานอัตโนมัติ (แนะนำ)
```bash
# 1. Copy ไฟล์ STM32 ที่มีหน่วย A ไปที่ test_data/raw_stm32/
cp your_stm32_files_with_A_units/* test_data/raw_stm32/

# 2. รันการวิเคราะห์แบบ Enhanced (จะแปลงหน่วยอัตโนมัติ)
python3 enhanced_cv_calibration.py
```

### วิธีที่ 2: แปลงหน่วยแยกต่างหาก
```bash
# 1. Copy ไฟล์ไปที่ test_data/raw_stm32/
cp your_stm32_files/* test_data/raw_stm32/

# 2. แปลงหน่วยแยก
python3 stm32_unit_converter.py

# 3. รันการวิเคราะห์ปกติ
python3 cv_calibration_simple.py
```

## 🔧 ไฟล์ที่ระบบรองรับ

### ✅ ไฟล์ที่ต้องการแปลงหน่วย (A → µA):
- Headers ที่มี: `Current (A)`, `I (A)`, `current(A)`
- ค่าในหน่วย ampere (A) เช่น 1.23e-6
- จะถูกแปลงเป็น microampere (µA) โดยคูณด้วย 1e6

### ⏭️ ไฟล์ที่ไม่ต้องแปลง:
- Headers ที่มี: `Current (µA)`, `I (µA)`, `current(uA)`  
- ค่าในหน่วย µA อยู่แล้ว

## 📊 ตัวอย่างการแปลงหน่วย

### ก่อนแปลง (A units):
```csv
Voltage (V),Current (A),Time (s)
-0.5,-1.23e-06,0.0
0.0,2.45e-06,1.0  
0.5,1.89e-06,2.0
```

### หลังแปลง (µA units):
```csv
Voltage (V),Current (µA),Time (s)
-0.5,-1.23,0.0
0.0,2.45,1.0
0.5,1.89,2.0
```

## 🧪 การทดสอบระบบ

### ทดสอบการแปลงหน่วย:
```bash
python3 test_unit_converter.py
```
ผลลัพธ์ที่ควรได้:
```
INFO: ✅ Conversion successful!
INFO: Conversion ratio for Current (A): 1000000 (should be ~1e6)
```

## 📈 Features ของ Enhanced CV Analysis

### 🔄 Auto Unit Conversion:
- ตรวจจับไฟล์ที่มีหน่วย A อัตโนมัติ
- แปลงเป็น µA โดยไม่ต้องแก้ไขไฟล์ต้นฉบับ
- บันทึก conversion log สำหรับตรวจสอบ

### 📊 Enhanced Plotting:
- แยกกราฟตาม scan rate
- แสดงค่า R² สำหรับแต่ละเส้น calibration
- แยกแสดงไฟล์ที่แปลงแล้วและไฟล์ต้นฉบับ
- รองรับ Palmsens และ STM32 ในกราฟเดียวกัน

### 🔍 File Detection:
- ตรวจจับ source อัตโนมัติ (Palmsens/STM32)
- Extract concentration และ scan rate จากชื่อไฟล์
- รองรับรูปแบบชื่อไฟล์หลากหลาย

## 📝 Conversion Log

ระบบจะสร้าง `conversion_log.json` ที่บันทึก:
- ไฟล์ต้นฉบับและไฟล์ที่แปลงแล้ว
- columns ที่ถูกแปลง
- ช่วงข้อมูลก่อนและหลังแปลง
- timestamp ของการแปลง

ตัวอย่าง:
```json
{
  "conversion_timestamp": "2025-08-26T18:45:55",
  "total_conversions": 2,
  "conversions": [
    {
      "original_file": "test_data/raw_stm32/sample.csv",
      "converted_file": "test_data/converted_stm32/sample.csv",
      "converted_columns": ["Current (A)"],
      "data_range_before": {"Current (A)": {"min": -1.12e-06, "max": 1.14e-06}},
      "data_range_after": {"Current (A)": {"min": -1.12, "max": 1.14}}
    }
  ]
}
```

## ⚠️ สิ่งที่ควรระวัง

1. **Backup ไฟล์ต้นฉบับ**: ระบบจะไม่แก้ไขไฟล์ต้นฉบับ แต่ควร backup ไว้
2. **ตรวจสอบหน่วย**: ตรวจสอบว่าไฟล์มีหน่วยเป็น A จริงๆ ก่อนแปลง
3. **ชื่อไฟล์**: ตรวจสอบให้แน่ใจว่าชื่อไฟล์มี concentration และ scan rate

## 🎯 การใช้งานต่อไป

หลังจากที่แปลงหน่วยแล้ว คุณสามารถ:
1. ใช้ไฟล์ที่แปลงแล้วร่วมกับไฟล์เดิม
2. รวมเข้ากับ Test_data/Stm32 สำหรับการวิเคราะห์
3. เปรียบเทียบผลลัพธ์ระหว่าง Palmsens และ STM32

## 📞 Troubleshooting

### ปัญหา: "No A units detected"
**แก้ไข**: ตรวจสอบ header ของ CSV file ว่ามี "(A)" หรือไม่

### ปัญหา: "Could not extract concentration"  
**แก้ไข**: ตรวจสอบชื่อไฟล์ว่ามีรูปแบบ เช่น "1.0mM" หรือ "Ferro_10mM"

### ปัญหา: R² ต่ำ
**แก้ไข**: ตรวจสอบว่าข้อมูลถูกแปลงหน่วยถูกต้องหรือไม่ และลองแยก scan rate