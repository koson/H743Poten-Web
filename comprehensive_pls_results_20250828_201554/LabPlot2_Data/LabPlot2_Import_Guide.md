# LabPlot2 Import Guide for PLS Analysis Data
# ================================================

## ไฟล์ข้อมูลที่สร้างขึ้น:

### 1. Device Classification Plots

### Device Classification
- **scatter_all**: device_classification_all.csv
- **scatter_palmsens**: device_classification_palmsens.csv
- **scatter_stm32**: device_classification_stm32.csv
- **feature_importance**: device_classification_feature_importance.csv


### Concentration Prediction
- **scatter_all**: concentration_prediction_all.csv
- **scatter_palmsens**: concentration_prediction_palmsens.csv
- **scatter_stm32**: concentration_prediction_stm32.csv
- **perfect_line**: concentration_perfect_line.csv
- **feature_importance**: concentration_prediction_feature_importance.csv


### Bland Altman
- **scatter_all**: bland_altman_all.csv
- **scatter_palmsens**: bland_altman_palmsens.csv
- **scatter_stm32**: bland_altman_stm32.csv
- **reference_lines**: bland_altman_reference_lines.csv


### Error Analysis
- **raw_errors_all**: error_analysis_all.csv
- **raw_errors_palmsens**: error_analysis_palmsens.csv
- **raw_errors_stm32**: error_analysis_stm32.csv
- **summary_all**: error_summary_by_concentration.csv
- **summary_palmsens**: error_summary_palmsens.csv
- **summary_stm32**: error_summary_stm32.csv


### Precision Analysis
- **precision_all**: precision_analysis_all.csv
- **precision_palmsens**: precision_analysis_palmsens.csv
- **precision_stm32**: precision_analysis_stm32.csv
- **precision_summary**: precision_summary.csv
- **cv_thresholds**: cv_threshold_lines.csv


## วิธีการนำเข้าใน LabPlot2:

### 🎨 การแยกสีตาม Device Column (ทุกกราฟ):

#### **วิธีที่ 1: ใช้ Conditional Formatting**
1. **Import CSV** ที่มี Device column
2. **สร้าง XY-Plot** ตามปกติ
3. **คลิกขวาที่ data series** > Properties
4. **ไปที่ Tab "Symbol"**
5. **เลือก "Use conditional formatting"**
6. **ตั้งค่า Condition:**
   - **Column**: Device
   - **Value**: Palmsens → สี #2E86AB (น้ำเงิน)
   - **Value**: STM32 → สี #A23B72 (ม่วงแดง)

#### **วิธีที่ 2: แยกเป็น Data Series**
1. **Import CSV ที่แยกแล้ว:**
   - `*_palmsens.csv` และ `*_stm32.csv`
2. **สร้าง 2 Data Series ในกราฟเดียวกัน:**
   - **Series 1**: Palmsens data (สีน้ำเงิน)
   - **Series 2**: STM32 data (สีม่วงแดง)

#### **วิธีที่ 3: ใช้ Filter**
1. **Import data ทั้งหมด**
2. **สร้าง XY-Plot**
3. **ใช้ Filter ใน Data tab:**
   - **Filter 1**: Device = "Palmsens" → สีน้ำเงิน
   - **Filter 2**: Device = "STM32" → สีม่วงแดง

### 1. Device Classification Scatter Plot
1. เปิด LabPlot2
2. File > Import > CSV
3. เลือกไฟล์ device_classification_all.csv
4. สร้าง XY-Plot:
   - X axis: Actual_Class
   - Y axis: Predicted_Class
   - Symbol: ใช้วิธีข้างต้นแยกสีตาม Device column

### 2. Concentration Prediction Plot
#### **ตัวอย่างโดยละเอียด:**
1. **Import**: concentration_prediction_all.csv
2. **สร้าง XY-Plot**:
   - X axis: Actual_Concentration_mM
   - Y axis: Predicted_Concentration_mM
3. **แยกสีตาม Device (เลือก 1 วิธี):**
   
   **วิธี A - Conditional Formatting:**
   - คลิกขวาที่ data points > Properties
   - Symbol Tab > Use conditional formatting
   - Condition: Device = "Palmsens" → Color: #2E86AB
   - Condition: Device = "STM32" → Color: #A23B72
   
   **วิธี B - แยก Series:**
   - Import concentration_prediction_palmsens.csv (Series 1)
   - Import concentration_prediction_stm32.csv (Series 2)
   - ตั้งสีแต่ละ Series แยกกัน

4. **เพิ่ม Perfect Line:**
   - Import: concentration_perfect_line.csv
   - เพิ่มเป็น Line plot บนกราฟเดียวกัน (สี #F18F01)

### 3. Bland-Altman Plot
#### **ขั้นตอนโดยละเอียด:**
1. **Import**: bland_altman_all.csv
2. **สร้าง XY-Plot**:
   - X axis: Mean_Concentration_mM
   - Y axis: Difference_mM
3. **แยกสีตาม Device:**
   - ใช้ Conditional Formatting (แนะนำ):
     - Device = "Palmsens" → สี #2E86AB + Symbol ●
     - Device = "STM32" → สี #A23B72 + Symbol ▲
4. **เพิ่ม Reference Lines:**
   - Import: bland_altman_reference_lines.csv
   - สร้าง Horizontal lines:
     - Bias line: Y = 0.000 (สี #C73E1D, dashed)
     - Upper limit: Y = +1.303 (สี #C73E1D, dotted)
     - Lower limit: Y = -1.303 (สี #C73E1D, dotted)

### 4. Error Analysis
#### **สร้างกราฟ Error vs Concentration:**
1. **Import**: error_summary_by_concentration.csv
2. **สร้าง XY-Plot with Error Bars:**
   - X axis: Concentration_mM
   - Y axis: MAE_Mean_mM
   - Error bars: MAE_Std_mM (Vertical error bars)
3. **แยกสีตาม Device:**
   
   **วิธีแนะนำ - ใช้ไฟล์แยก:**
   - Import error_summary_palmsens.csv → Series 1 (สี #2E86AB)
   - Import error_summary_stm32.csv → Series 2 (สี #A23B72)
   
   **หรือใช้ Conditional Formatting:**
   - Device = "Palmsens" → สี #2E86AB
   - Device = "STM32" → สี #A23B72

### 5. Precision Analysis (CV%)
#### **สร้างกราฟ CV% by Feature:**
1. **Import**: precision_analysis_all.csv
2. **สร้าง Box Plot หรือ Scatter Plot:**
   - X axis: Feature
   - Y axis: CV_Percent
3. **แยกสีตาม Device:**
   
   **สำหรับ Scatter Plot:**
   - ใช้ Conditional Formatting
   - Device = "Palmsens" → สี #2E86AB + Symbol ●
   - Device = "STM32" → สี #A23B72 + Symbol ▲
   
   **สำหรับ Box Plot:**
   - สร้าง 2 Box plots แยกกัน
   - Import precision_analysis_palmsens.csv
   - Import precision_analysis_stm32.csv

4. **เพิ่ม Threshold Lines:**
   - Import: cv_threshold_lines.csv
   - เพิ่มเป็น Horizontal lines ที่:
     - 2% (Excellent) → สีเขียว
     - 5% (Good) → สีเหลือง  
     - 10% (Acceptable) → สีส้ม

### 6. Feature Importance
1. Import: device_classification_feature_importance.csv
2. สร้าง Bar Plot:
   - X axis: Feature
   - Y axis: Abs_Importance
3. Import: concentration_prediction_feature_importance.csv
   - สร้าง Bar Plot แยกต่างหาก

## 🎨 **การแยกสีตาม Device ใน LabPlot2 (คู่มือฉบับสมบูรณ์)**

### **📋 วิธีที่ 1: Conditional Formatting (แนะนำ)**

#### **ขั้นตอนโดยละเอียด:**
1. **Import CSV** ที่มี Device column
2. **สร้าง XY-Plot** ตามปกติ
3. **คลิกขวาที่ data points** → Properties
4. **ไปที่ Tab "Symbol"**
5. **เช็ค "Use conditional formatting"**
6. **กด Add** เพื่อเพิ่ม condition
7. **ตั้งค่า Condition 1:**
   - **Column**: Device
   - **Operator**: equals
   - **Value**: Palmsens
   - **Color**: #2E86AB (น้ำเงิน)
   - **Symbol**: ● (Circle, filled)
8. **กด Add** อีกครั้งสำหรับ Condition 2:**
   - **Column**: Device  
   - **Operator**: equals
   - **Value**: STM32
   - **Color**: #A23B72 (ม่วงแดง)
   - **Symbol**: ▲ (Triangle, filled)

### **📊 วิธีที่ 2: แยกเป็น Data Series (วิธีง่าย)**

#### **ขั้นตอน:**
1. **Import 2 ไฟล์แยกกัน:**
   - `*_palmsens.csv` สำหรับข้อมูล Palmsens
   - `*_stm32.csv` สำหรับข้อมูล STM32

2. **สร้าง Plot และเพิ่ม 2 Series:**
   - **Series 1**: เลือกข้อมูล Palmsens
     - X column: เลือกคอลัมน์ X
     - Y column: เลือกคอลัมน์ Y
     - Color: #2E86AB
     - Symbol: ●

   - **Series 2**: เลือกข้อมูล STM32  
     - X column: เลือกคอลัมน์ X
     - Y column: เลือกคอลัมน์ Y
     - Color: #A23B72
     - Symbol: ▲

### **🔧 วิธีที่ 3: ใช้ Data Filter**

#### **ขั้นตอน:**
1. **Import data ทั้งหมด**
2. **สร้าง XY-Plot**
3. **ในแท็บ Data:**
   - **คลิก Filter icon**
   - **เพิ่ม Filter 1**: Device = "Palmsens"
   - **เพิ่ม Filter 2**: Device = "STM32"
4. **แต่ละ Filter สามารถตั้งสีแยกได้**

### **⚡ เทคนิคเพิ่มเติม:**

#### **การปรับแต่งสัญลักษณ์:**
- **Size**: 8-12 pixels (เหมาะสำหรับ publication)
- **Border**: เพิ่ม border สีดำบางๆ เพื่อความชัดเจน
- **Transparency**: 0-20% ถ้าข้อมูลทับซ้อนกัน

#### **การสร้าง Legend:**
1. **คลิกขวาในพื้นที่กราฟ** → Insert Legend
2. **ปรับตำแหน่ง** ให้เหมาะสม
3. **ตั้งชื่อ**:
   - Palmsens (●)
   - STM32 (▲)

## การตั้งค่าสำหรับกราฟที่สวยงาม:

### Colors (แนะนำ):
- Palmsens: #2E86AB (สีน้ำเงิน)
- STM32: #A23B72 (สีม่วงแดง)
- Perfect Line: #F18F01 (สีส้ม)
- Reference Lines: #C73E1D (สีแดง)

### Symbols:
- Palmsens: ● (Circle, filled)
- STM32: ▲ (Triangle, filled)

### Line Styles:
- Perfect Prediction: ——— (Solid line)
- Bias Line: - - - (Dashed)
- Limits of Agreement: ∙∙∙∙∙ (Dotted)

## การประยุกต์ใช้:

### **📝 ตัวอย่าง Step-by-Step: Concentration Prediction Plot**

#### **ขั้นตอนที่ 1: เตรียมข้อมูล**
1. เปิด LabPlot2
2. File > Import Data > CSV
3. เลือก `concentration_prediction_all.csv`
4. กด Import

#### **ขั้นตอนที่ 2: สร้างกราฟพื้นฐาน**
1. คลิกขวาใน Project Tree > Insert > Worksheet
2. คลิกขวาใน Worksheet > Insert > XY-Plot
3. เลือก data source: concentration_prediction_all
4. กำหนดแกน:
   - X column: Actual_Concentration_mM
   - Y column: Predicted_Concentration_mM

#### **ขั้นตอนที่ 3: แยกสีตาม Device**
1. **คลิกขวาที่ data points** > Properties
2. **ไปที่ tab "Symbol"**
3. **เช็ค "Use conditional formatting"**
4. **กด "Add"** เพื่อเพิ่ม condition
5. **Condition 1:**
   ```
   Column: Device
   Condition: equals  
   Value: Palmsens
   Color: #2E86AB (น้ำเงิน)
   Symbol: circle (●)
   Size: 10
   ```
6. **กด "Add"** อีกครั้ง
7. **Condition 2:**
   ```
   Column: Device
   Condition: equals
   Value: STM32  
   Color: #A23B72 (ม่วงแดง)
   Symbol: triangle (▲)
   Size: 10
   ```

#### **ขั้นตอนที่ 4: เพิ่ม Perfect Prediction Line**
1. **Import** `concentration_perfect_line.csv`
2. **เพิ่ม XY-Curve ใหม่**:
   - X: Actual_Concentration_mM
   - Y: Predicted_Concentration_mM  
   - Line style: Solid
   - Color: #F18F01 (ส้ม)
   - Width: 2

#### **ขั้นตอนที่ 5: ปรับแต่งกราฟ**
1. **แกน X**: 
   - Title: "Actual Concentration (mM)"
   - Range: 0 - 25
2. **แกน Y**:
   - Title: "Predicted Concentration (mM)"  
   - Range: 0 - 25
3. **Legend**:
   - คลิกขวาในกราฟ > Insert Legend
   - ตำแหน่ง: Top Right
   - ข้อความ: Palmsens, STM32, Perfect Prediction

### **💡 เคล็ดลับสำหรับกราฟที่สวยงาม:**

1. **นำเข้าไฟล์ที่ต้องการ**
2. **เลือกประเภทกราฟที่เหมาะสม**
3. **ตั้งค่าสีและสัญลักษณ์ตามมาตรฐาน**
4. **เพิ่ม Labels และ Legends ที่ชัดเจน**
5. **ปรับแต่งแกนและขนาดข้อความให้อ่านง่าย**
6. **Export เป็น PDF หรือ PNG สำหรับ Publication**

### **🔍 การตรวจสอบผลลัพธ์:**
- ✅ Palmsens points เป็นสีน้ำเงิน (●)
- ✅ STM32 points เป็นสีม่วงแดง (▲)
- ✅ Perfect line เป็นสีส้ม
- ✅ Legend แสดงครบถ้วน
- ✅ แกนมีหน่วยและชื่อที่ถูกต้อง

