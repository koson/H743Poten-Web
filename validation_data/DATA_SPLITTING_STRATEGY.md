# 📊 Data Splitting Strategy for Peak Detection Framework

## 🎯 Overview
เอกสารนี้อธิบายกลยุทธ์การแบ่งข้อมูลสำหรับ H743Poten Peak Detection Framework เพื่อให้การเปรียบเทียบ 3 วิธีการ peak detection มีความน่าเชื่อถือและไม่เกิด data leakage

## 📁 ข้อมูลที่มี

### 📊 จำนวนข้อมูล
- **PalmSens**: 1,650 ไฟล์ (Reference Commercial Instrument)
- **STM32H743**: 1,682 ไฟล์ (Our Custom Potentiostat)
- **รวม**: 3,332 ไฟล์ CV data

### 🧪 เงื่อนไขการทดลอง
| Parameter | PalmSens | STM32H743 |
|-----------|----------|-----------|
| **Concentrations** | 6 levels (0.5, 1.0, 5, 10, 20, 50 mM) | 6+ levels |
| **Scan Rates** | 5 levels (20, 50, 100, 200, 400 mV/s) | 5 levels |
| **Electrodes** | 5 electrodes (E1-E5) | 5 electrodes (E1-E5) |
| **Repetitions** | 11 scans per condition | 11 scans per condition |
| **Samples/Condition** | ~11.0 | ~3.4 |

### 📈 ข้อมูลสำคัญ
- **Current Magnitude**: PalmSens (~36 µA) vs STM32H743 (~285 µA) = ใกล้เคียงกัน (STM32 สูงกว่าประมาณ 8 เท่า)
- **Voltage Range**: ใกล้เคียงกัน (-0.4 to 0.7V)
- **Data Points**: ~220 จุดต่อไฟล์

## 🎲 กลยุทธ์การแบ่งข้อมูล

### 1. **Primary Split: 70/15/15 Strategy**
```
📚 Training Set   : 70% = 2,332 ไฟล์
🔍 Validation Set : 15% =   499 ไฟล์  
🧪 Test Set      : 15% =   501 ไฟล์
```

#### เหตุผล:
- **Training (70%)**: ข้อมูลเพียงพอสำหรับการเรียนรู้ pattern ที่ซับซ้อน
- **Validation (15%)**: สำหรับ hyperparameter tuning และ model selection
- **Test (15%)**: สำหรับประเมินประสิทธิภาพจริงแบบ unbiased

### 2. **Stratified Splitting** 📊
แบ่งข้อมูลโดยรักษาสัดส่วนของแต่ละเงื่อนไข:
- แต่ละ **concentration** มีข้อมูลใน train/val/test
- แต่ละ **scan rate** มีข้อมูลใน train/val/test
- แต่ละ **electrode** มีข้อมูลใน train/val/test
- รักษาสมดุลระหว่าง **PalmSens** และ **STM32H743**

### 3. **Cross-Instrument Validation** 🔄
```
Strategy A: Train บน PalmSens → Test บน STM32H743
Strategy B: Train บน STM32H743 → Test บน PalmSens
```
**วัตถุประสงค์**: ทดสอบ transferability ของ peak detection algorithms ระหว่างเครื่องมือ

### 4. **Leave-One-Condition-Out (LOCO)** 🌟
```
• Leave-One-Concentration-Out: ทดสอบกับความเข้มข้นที่ไม่เคยเห็น
• Leave-One-ScanRate-Out: ทดสอบกับ scan rate ที่ไม่เคยเห็น
• Leave-One-Electrode-Out: ทดสอบกับ electrode ที่ไม่เคยเห็น
```

## 🏆 การประยุกต์ใช้กับ 3-Method Comparison

### Method 1: Baseline Detection (การลากเส้น)
- **Data Usage**: ใช้ทุกข้อมูล (statistical method)
- **Approach**: Manual/visual baseline detection
- **No Training Required**: ใช้หลักการทางสถิติ

### Method 2: Statistical Peak Detection  
- **Data Usage**: Training data สำหรับ parameter optimization
- **Parameters**: threshold values, smoothing parameters
- **Validation**: ใช้ validation set เพื่อ fine-tune parameters

### Method 3: Machine Learning Peak Detection
- **Data Usage**: Full train/validation/test split
- **Training**: Learn peak patterns from training data
- **Validation**: Hyperparameter tuning และ model selection
- **Testing**: Final unbiased performance evaluation

## 📊 Expected Benefits

### 1. **Robust Validation**
- ข้อมูล 3,332 ไฟล์เพียงพอสำหรับ robust statistical analysis
- Multiple experimental conditions ให้ความมั่นใจในการ generalize

### 2. **Unbiased Comparison**
- Test set ที่แยกออกมาให้ประเมินผลที่ไม่เอนเอียง
- Cross-instrument validation ทดสอบ real-world applicability

### 3. **Clinical Relevance**
- LOCO validation simulates การใช้งานกับ conditions ใหม่
- ทดสอบความทนทานของ algorithms

## ⚠️ ข้อควรระวัง

### 1. **Data Imbalance**
- STM32H743 มี samples/condition น้อยกว่า PalmSens
- **Solution**: ใช้ stratified sampling และ weighted evaluation

### 2. **Magnitude Similarity**
- Current magnitude ใกล้เคียงกัน (STM32H743 สูงกว่า PalmSens ประมาณ 8 เท่า)
- **Analysis**: ทั้งสองเครื่องให้ผลที่เปรียบเทียบได้ใน order of magnitude เดียวกัน

### 3. **Temporal Effects**
- ถ้ามีผลจากเวลา ต้องพิจารณา temporal splitting
- **Monitor**: scan order effects

## 📁 File Organization

```
validation_data/
├── splits/
│   ├── train_files.txt          # 70% training files
│   ├── val_files.txt            # 15% validation files  
│   ├── test_files.txt           # 15% test files
│   ├── cross_instrument/
│   │   ├── palmsens_train_stm32_test.txt
│   │   └── stm32_train_palmsens_test.txt
│   └── loco_splits/
│       ├── leave_concentration_out/
│       ├── leave_scanrate_out/
│       └── leave_electrode_out/
└── metadata/
    ├── split_statistics.json    # สถิติการแบ่ง
    ├── condition_distribution.json
    └── split_strategy.md        # เอกสารนี้
```

## 🔄 Implementation Plan

1. **Phase 1**: สร้าง primary 70/15/15 split
2. **Phase 2**: สร้าง cross-instrument splits  
3. **Phase 3**: สร้าง LOCO validation splits
4. **Phase 4**: Validate split quality และ balance
5. **Phase 5**: Generate metadata และ documentation

## 📈 Success Metrics

- **Balance Check**: แต่ละ condition มีการกระจายที่เหมาะสมใน train/val/test
- **No Leakage**: ไม่มี overlap ระหว่าง sets
- **Representative**: แต่ละ set representative ของ population
- **Reproducible**: สามารถ reproduce ได้ด้วย random seed

---

*Last Updated: August 16, 2025*  
*H743Poten Peak Detection Framework v1.3*
