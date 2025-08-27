# Precision Peak & Baseline Detection + PLS Analysis System

## ภาพรวมของระบบ

ระบบนี้ได้รับการพัฒนาเพื่อให้การตรวจสอบ **peak** และ **baseline** ที่แม่นยำที่สุด สำหรับการทำ **PLS (Partial Least Squares)** analysis และการคำนวณ **พื้นที่ใต้กราฟ (Area Under Curve)** อย่างแม่นยำ

### ส่วนประกอบหลักของระบบ

1. **Precision Peak & Baseline Analyzer** - ระบบตรวจสอบ peak และ baseline ที่แม่นยำ
2. **Advanced PLS Analyzer** - ระบบ PLS สำหรับการวิเคราะห์เชิงปริมาณ
3. **Web API Integration** - การรวมเข้ากับ web interface
4. **Test Suite** - ระบบทดสอบความถูกต้อง

---

## 1. Precision Peak & Baseline Analyzer

### Features หลัก

#### 🔍 Multi-Stage Baseline Detection
- **Stage 1**: ตรวจหา baseline regions ด้วย derivative analysis
- **Stage 2**: ตรวจสอบความถูกต้องด้วย statistical tests
- **Stage 3**: สร้าง baseline model ที่เหมาะสม
- **Stage 4**: ประเมิน quality score

#### 🎯 Enhanced Peak Detection
- **Method 1**: SciPy find_peaks ด้วยพารามิเตอร์ที่ optimize แล้ว
- **Method 2**: Derivative analysis สำหรับการหา peak ที่ละเอียด
- **Method 3**: Template matching สำหรับ analyte ที่ทราบ
- **Validation**: รวมผลลัพธ์และตรวจสอบความถูกต้อง

#### 📐 Precise Area Calculation
- **Simpson's Rule**: สำหรับความแม่นยำสูง
- **Trapezoidal Rule**: สำหรับข้อมูลทั่วไป
- **Baseline-corrected area**: พื้นที่หลังจากลบ baseline
- **Separate positive/negative areas**: แยกพื้นที่ oxidation/reduction

### การใช้งาน

```python
from precision_peak_baseline_analyzer import PrecisionPeakBaselineAnalyzer

# สร้าง analyzer
analyzer = PrecisionPeakBaselineAnalyzer({
    'analyte': 'ferrocene',
    'confidence_threshold': 85.0,
    'quality_threshold': 80.0,
    'area_calculation_method': 'simpson'
})

# วิเคราะห์ข้อมูล CV
results = analyzer.analyze_cv_data(voltage, current, filename="sample.csv")

if results['success']:
    print(f"พบ peaks: {len(results['peaks'])}")
    print(f"คุณภาพ baseline: {results['baseline']['quality_score']:.1f}%")
    print(f"พื้นที่รวม: {results['areas']['total_area']:.3f} μA⋅V")
    print(f"พื้นที่ oxidation: {results['areas']['oxidation_area']:.3f} μA⋅V")
    print(f"พื้นที่ reduction: {results['areas']['reduction_area']:.3f} μA⋅V")
```

### ผลลัพธ์ที่ได้

```json
{
  "success": true,
  "baseline": {
    "quality_score": 92.5,
    "r_squared": 0.95,
    "slope": 0.001,
    "noise_level": 0.12
  },
  "peaks": [
    {
      "voltage": 0.185,
      "current": 15.2,
      "peak_type": "oxidation",
      "height": 14.8,
      "area": 0.245,
      "confidence": 94.2,
      "quality_score": 91.8
    }
  ],
  "areas": {
    "total_area": 0.567,
    "oxidation_area": 0.245,
    "reduction_area": 0.198,
    "area_ratio": 1.24
  },
  "pls_features": {
    "oxidation_height": 14.8,
    "reduction_height": 11.9,
    "peak_separation": 0.095,
    "total_area": 0.567
  },
  "quality_metrics": {
    "overall_quality": 89.5,
    "pls_readiness": 92.1
  }
}
```

---

## 2. Advanced PLS Analyzer

### Features หลัก

#### 🧬 Feature Extraction
- **Peak-based features**: height, separation, ratio
- **Area-based features**: total area, oxidation/reduction areas
- **Shape-based features**: symmetry, signal-to-noise ratio
- **Advanced features**: charge transfer resistance, diffusion coefficient

#### 🏗️ Model Building
- **Automatic component optimization**: Cross-validation สำหรับหาจำนวน components ที่เหมาะสม
- **Feature selection**: เลือกเฉพาะ features ที่มีประโยชน์
- **Quality assessment**: ประเมินคุณภาพ model ด้วยหลายเกณฑ์

#### 🔮 Concentration Prediction
- **Real-time prediction**: ทำนายความเข้มข้นแบบ real-time
- **Confidence intervals**: ช่วงความเชื่อมั่น 95%
- **Quality-based confidence**: ความเชื่อมั่นตาม data quality

### การใช้งาน

```python
from advanced_pls_analyzer import AdvancedPLSAnalyzer

# สร้าง PLS analyzer
pls = AdvancedPLSAnalyzer({
    'quality_threshold': 80.0,
    'min_calibration_points': 5
})

# เพิ่ม calibration points
concentrations = [0.5e-6, 1.0e-6, 2.0e-6, 5.0e-6, 10.0e-6]  # μM
for conc in concentrations:
    # voltage, current = load_cv_data(...)
    success = pls.add_calibration_point(voltage, current, conc)

# สร้าง PLS model
model = pls.build_pls_model("ferrocene_model")

if model:
    print(f"Model R²: {model.model_metrics['r2_score']:.4f}")
    print(f"RMSE: {model.model_metrics['rmse']:.6f} M")
    print(f"Components: {model.optimal_components}")

# ทำนายความเข้มข้น
prediction = pls.predict_concentration(voltage, current)
if prediction:
    print(f"ความเข้มข้นที่ทำนาย: {prediction.predicted_concentration*1e6:.2f} μM")
    print(f"ความเชื่อมั่น: {prediction.prediction_confidence:.1f}%")
```

### Model Performance

```json
{
  "model_id": "ferrocene_model_20250827",
  "optimal_components": 3,
  "r2_score": 0.9845,
  "rmse": 2.15e-7,
  "relative_rmse_percent": 4.2,
  "feature_importance": {
    "oxidation_height": 0.35,
    "reduction_height": 0.28,
    "total_area": 0.22,
    "peak_separation": 0.15
  }
}
```

---

## 3. Web API Integration

### Available Endpoints

#### 📊 System Status
```
GET /api/precision/status
```

#### 🔬 Precision Analysis
```
POST /api/precision/analyze
{
  "voltage": [array],
  "current": [array],
  "filename": "optional",
  "analyte": "ferrocene"
}
```

#### 📈 Calibration Management
```
POST /api/precision/calibration/add
{
  "voltage": [array],
  "current": [array],
  "concentration": 1.0e-6,
  "filename": "optional"
}

GET /api/precision/calibration/status
```

#### 🏗️ Model Building
```
POST /api/precision/model/build
{
  "model_id": "optional",
  "features": ["optional feature list"]
}

GET /api/precision/model/list
```

#### 🔮 Concentration Prediction
```
POST /api/precision/predict
{
  "voltage": [array],
  "current": [array],
  "model_id": "optional"
}
```

#### 📦 Batch Processing
```
POST /api/precision/batch/analyze
{
  "datasets": [
    {
      "voltage": [array],
      "current": [array],
      "concentration": 1.0e-6
    }
  ],
  "mode": "calibration"
}
```

### การใช้งาน API

```javascript
// Precision analysis
const analysisResponse = await fetch('/api/precision/analyze', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        voltage: voltageData,
        current: currentData,
        analyte: 'ferrocene'
    })
});

const results = await analysisResponse.json();
if (results.success) {
    console.log(`พบ ${results.peaks.length} peaks`);
    console.log(`คุณภาพ: ${results.quality_metrics.overall_quality}%`);
}

// Build PLS model
const modelResponse = await fetch('/api/precision/model/build', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        model_id: 'my_model'
    })
});

// Predict concentration
const predictionResponse = await fetch('/api/precision/predict', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        voltage: unknownVoltage,
        current: unknownCurrent
    })
});
```

---

## 4. การทดสอบระบบ

### Test Suite

```bash
# รันการทดสอบทั้งหมด
python test_precision_pls_system.py
```

### ผลลัพธ์การทดสอบ

```
🧪 PRECISION PEAK/BASELINE DETECTION + PLS ANALYSIS TEST SUITE
================================================================================
📅 Started: 2025-08-27 15:30:00

🐍 Checking Python environment...
   ✅ numpy
   ✅ pandas  
   ✅ matplotlib
   ✅ scipy
   ✅ sklearn

🧪 Running precision_analyzer test...
✅ Precision analyzer imported successfully
🧪 Testing with synthetic CV data
✅ Synthetic data analysis successful:
   Peaks detected: 2
   Quality score: 89.5%
   Oxidation peaks: 1
   Reduction peaks: 1
✅ Both oxidation and reduction peaks detected correctly

🧪 Running pls_analyzer test...
✅ PLS analyzer imported successfully
✅ Scikit-learn available
🧪 Testing PLS with synthetic calibration data
   ✅ Added synthetic point: 0.5 μM
   ✅ Added synthetic point: 1.0 μM
   ✅ Added synthetic point: 2.0 μM
   ✅ Added synthetic point: 5.0 μM
   ✅ Added synthetic point: 10.0 μM
🏗️ Building synthetic PLS model...
✅ Synthetic PLS model built successfully
🔮 Testing concentration prediction...
🎯 Prediction test results:
   True concentration: 3.0 μM
   Predicted concentration: 2.9 μM
   Prediction error: 3.3%
   Confidence: 91.2%
✅ Prediction accuracy test PASSED

📊 TEST SUMMARY
================================================================================
✅ precision_analyzer: PASSED
✅ pls_analyzer: PASSED  
✅ integration: PASSED

🎉 OVERALL RESULT: PASSED

🚀 System is ready for precision peak/baseline detection and PLS analysis!
   • Peak detection accuracy validated
   • Baseline correction working properly
   • Area under curve calculation precise
   • PLS models building and predicting correctly
   • Integration between components successful
```

---

## 5. คุณสมบัติพิเศษ

### 🎯 ความแม่นยำสูง
- **Multi-method peak detection**: รวมหลายวิธีเพื่อความแม่นยำสูงสุด
- **Statistical validation**: ตรวจสอบทุก peak ด้วยเกณฑ์ทางสถิติ
- **Quality scoring**: ให้คะแนนคุณภาพทุกขั้นตอน

### 📐 การคำนวณพื้นที่ที่แม่นยำ
- **Simpson's rule integration**: แม่นยำกว่า trapezoidal rule
- **Baseline-corrected areas**: พื้นที่จริงหลังลบ baseline
- **Separate positive/negative areas**: แยกการคำนวณ oxidation/reduction

### 🧬 PLS Features ครบถ้วน
- **14 electrochemical features**: ครอบคลุมทุกด้านของ CV analysis
- **Automatic feature selection**: เลือกเฉพาะ features ที่มีประโยชน์
- **Cross-validation optimization**: หา parameters ที่ดีที่สุดอัตโนมัติ

### 🔮 การทำนายที่เชื่อถือได้
- **Confidence intervals**: ช่วงความเชื่อมั่น 95%
- **Quality-based confidence**: ความเชื่อมั่นตาม data quality
- **Model validation**: Leave-one-out cross-validation

---

## 6. การติดตั้งและใช้งาน

### Prerequisites

```bash
pip install numpy pandas matplotlib scipy scikit-learn
```

### การรวมเข้ากับ Web Application

```python
# ใน main Flask app
from src.routes.precision_pls_api import register_blueprint

# Register the API blueprint
register_blueprint(app)
```

### การใช้งานใน Production

1. **เพิ่ม calibration data**: ใช้ `/api/precision/calibration/add`
2. **สร้าง PLS model**: ใช้ `/api/precision/model/build`
3. **ทำนายความเข้มข้น**: ใช้ `/api/precision/predict`
4. **ตรวจสอบคุณภาพ**: ใช้ `/api/precision/model/validate`

---

## 7. Best Practices

### การเตรียม Calibration Data
- ใช้ความเข้มข้นที่หลากหลาย (อย่างน้อย 5 จุด)
- ตรวจสอบ data quality > 80%
- ใช้เงื่อนไขการวัดที่เหมือนกัน

### การสร้าง PLS Model
- ตรวจสอบ R² > 0.95 สำหรับ calibration ที่ดี
- ใช้ cross-validation เพื่อหลีกเลี่ยง overfitting
- เลือก features ที่เหมาะสมกับ analyte

### การทำนายความเข้มข้น
- ตรวจสอบ prediction confidence > 85%
- ใช้ confidence interval ในการตีความผล
- validate กับ known samples เป็นระยะ

---

## 8. Troubleshooting

### ปัญหาที่พบบ่อย

#### Peak Detection ไม่แม่นยำ
```python
# ปรับ config parameters
analyzer.config.update({
    'peak_prominence_factor': 0.2,  # เพิ่มสำหรับ peaks ที่ชัดเจน
    'confidence_threshold': 80.0,   # ลดสำหรับ data ที่มี noise
    'smoothing_window': 7            # เพิ่มสำหรับ noise reduction
})
```

#### Baseline Quality ต่ำ
```python
# ใช้ baseline method ที่เหมาะสม
analyzer.config['baseline_method'] = 'multi_stage'
analyzer.config['baseline_window_size'] = 30  # เพิ่มขนาด window
```

#### PLS Model R² ต่ำ
- เพิ่ม calibration points มากขึ้น
- ตรวจสอบ data quality ของแต่ละจุด
- ลองใช้ feature subset ที่เหมาะสม

---

## สรุป

ระบบ **Precision Peak & Baseline Detection + PLS Analysis** นี้ได้รับการออกแบบเพื่อให้ความแม่นยำสูงสุดในการ:

1. **ตรวจสอบ peak และ baseline** ด้วย multi-stage validation
2. **คำนวณพื้นที่ใต้กราฟ** ด้วย Simpson's rule integration  
3. **สร้าง PLS models** ที่เชื่อถือได้สำหรับการทำนายความเข้มข้น
4. **รวมเข้ากับ web interface** สำหรับการใช้งานจริง

ระบบนี้พร้อมสำหรับการใช้งาน production และจะช่วยให้การวิเคราะห์ทางเคมีไฟฟ้าแม่นยำและเชื่อถือได้มากขึ้น 🚀
