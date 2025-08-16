# 🧪 Peak Detection Methods Implementation Guide

## 🎯 Overview
เอกสารนี้อธิบายการ implement 3 วิธีการ peak detection และการใช้งานข้อมูลที่แบ่งแล้วสำหรับการเปรียบเทียบที่มีคุณภาพ

## 📊 Data Splits Available

### ✅ ข้อมูลที่แบ่งแล้ว (seed=42):
- **📚 Training**: 2,114 files (63.4%)
- **🔍 Validation**: 302 files (9.1%)  
- **🧪 Test**: 916 files (27.5%)

### 🔄 Cross-Instrument Splits:
- **PalmSens→STM32**: Train=1,650, Test=1,682
- **STM32→PalmSens**: Train=1,682, Test=1,650

### 🌟 LOCO (Leave-One-Condition-Out):
- **Leave-Concentration-Out**: 24 splits
- **Leave-ScanRate-Out**: 11 splits
- **Leave-Electrode-Out**: 11 splits

## 🏆 3-Method Peak Detection Framework

### Method 1: 📏 Baseline Detection (การลากเส้น)

#### 📖 Theory:
- Manual หรือ semi-automatic baseline correction
- ใช้หลักการทางสถิติและ signal processing
- ไม่ต้องการ training data

#### 💻 Implementation Strategy:
```python
def baseline_peak_detection(cv_data):
    """
    1. Load CV data (V, uA)
    2. Apply smoothing (Savitzky-Golay, moving average)
    3. Find baseline (linear, polynomial, or adaptive)
    4. Subtract baseline
    5. Detect peaks (prominence, height thresholds)
    6. Return peak positions and properties
    """
    pass
```

#### 📊 Data Usage:
- **All Data**: ใช้ทุกไฟล์ (3,332 files) เพื่อ statistical robustness
- **No Training**: ไม่แบ่ง train/test เพราะเป็น deterministic method
- **Parameter Tuning**: ใช้ validation set เพื่อ optimize parameters

#### 📈 Expected Output:
- Peak positions (V)
- Peak heights (uA)
- Peak widths
- Peak areas
- Signal-to-noise ratio

---

### Method 2: 📊 Statistical Peak Detection

#### 📖 Theory:
- Advanced statistical methods
- Adaptive thresholding
- Multi-scale peak detection
- Noise characterization

#### 💻 Implementation Strategy:
```python
def statistical_peak_detection(cv_data, params):
    """
    1. Noise estimation (MAD, robust statistics)
    2. Multi-scale smoothing
    3. Derivative-based peak detection
    4. Statistical significance testing
    5. Peak clustering and refinement
    6. Confidence intervals
    """
    pass
```

#### 📊 Data Usage:
- **Training Set**: 2,114 files สำหรับ parameter optimization
- **Validation Set**: 302 files สำหรับ hyperparameter tuning
- **Test Set**: 916 files สำหรับ final evaluation

#### 🎛️ Parameters to Optimize:
- Smoothing window size
- Peak prominence threshold  
- Noise estimation method
- Clustering parameters

---

### Method 3: 🤖 Machine Learning Peak Detection

#### 📖 Theory:
- Deep learning หรือ classical ML
- Feature extraction from CV curves
- Pattern recognition
- Transfer learning ระหว่างเครื่องมือ

#### 💻 Implementation Strategy:
```python
def ml_peak_detection(cv_data, model):
    """
    1. Feature extraction (shape, derivatives, transforms)
    2. Data preprocessing and normalization
    3. Model prediction (CNN, LSTM, SVM, etc.)
    4. Post-processing and peak refinement
    5. Uncertainty quantification
    """
    pass
```

#### 📊 Data Usage:
- **Training Set**: 2,114 files สำหรับ model training
- **Validation Set**: 302 files สำหรับ model selection & hyperparameters
- **Test Set**: 916 files สำหรับ unbiased evaluation

#### 🎯 ML Approaches:
1. **CNN-based**: Direct peak detection from CV curves
2. **Feature-based**: Extract features → classical ML
3. **Transfer Learning**: Pre-train on PalmSens → adapt to STM32
4. **Ensemble Methods**: Combine multiple approaches

## 🔄 Validation Strategies

### 1. **Primary Validation (70/15/15)**
```python
# Train algorithms
train_data = load_file_list('validation_data/splits/train_files.txt')
val_data = load_file_list('validation_data/splits/validation_files.txt')

# Final evaluation
test_data = load_file_list('validation_data/splits/test_files.txt')
```

### 2. **Cross-Instrument Validation**
```python
# PalmSens → STM32 transfer
palmsens_train = load_file_list('validation_data/splits/cross_instrument/palmsens_train_stm32_test_train.txt')
stm32_test = load_file_list('validation_data/splits/cross_instrument/palmsens_train_stm32_test_test.txt')

# STM32 → PalmSens transfer  
stm32_train = load_file_list('validation_data/splits/cross_instrument/stm32_train_palmsens_test_train.txt')
palmsens_test = load_file_list('validation_data/splits/cross_instrument/stm32_train_palmsens_test_test.txt')
```

### 3. **LOCO Validation**
```python
# Leave-One-Concentration-Out example
for conc_split in glob('validation_data/splits/loco_splits/leave_concentration_out/*_train.txt'):
    train_data = load_file_list(conc_split)
    test_data = load_file_list(conc_split.replace('_train.txt', '_test.txt'))
    # Train and evaluate
```

## 📏 Evaluation Metrics

### 1. **Peak Detection Accuracy**
- **Precision**: True peaks detected / Total peaks detected
- **Recall**: True peaks detected / Total true peaks  
- **F1-Score**: Harmonic mean of precision and recall
- **mAP**: Mean Average Precision

### 2. **Peak Characterization Accuracy**
- **Position Error**: |detected_position - true_position|
- **Height Error**: |detected_height - true_height| / true_height
- **Area Error**: |detected_area - true_area| / true_area

### 3. **Cross-Instrument Performance**
- **Transfer Accuracy**: Performance when trained on one instrument, tested on another
- **Magnitude Robustness**: Performance across different current magnitudes
- **Consistency**: Std dev of results across conditions

### 4. **Computational Metrics**
- **Processing Time**: Time per CV curve
- **Memory Usage**: Peak memory consumption
- **Scalability**: Performance vs dataset size

## 📁 Implementation File Structure

```
validation_data/
├── peak_detection/
│   ├── __init__.py
│   ├── baseline_detection.py       # Method 1
│   ├── statistical_detection.py   # Method 2  
│   ├── ml_detection.py            # Method 3
│   ├── evaluation_metrics.py      # Evaluation tools
│   └── utils.py                   # Common utilities
├── experiments/
│   ├── experiment_1_baseline.py
│   ├── experiment_2_statistical.py
│   ├── experiment_3_ml.py
│   └── experiment_4_comparison.py
├── results/
│   ├── baseline_results/
│   ├── statistical_results/
│   ├── ml_results/
│   └── comparison_analysis/
└── notebooks/
    ├── data_exploration.ipynb
    ├── method_development.ipynb
    └── results_visualization.ipynb
```

## 🎯 Expected Research Questions

### 1. **Method Comparison**
- Which method performs best overall?
- How do methods perform across different conditions?
- What are the trade-offs (accuracy vs speed vs complexity)?

### 2. **Cross-Instrument Transferability**  
- Can we train on PalmSens and deploy on STM32H743?
- How much performance degradation occurs?
- What adaptation strategies work best?

### 3. **Condition Robustness**
- How do methods perform on unseen concentrations?
- Are methods robust to different scan rates?
- Do electrode differences affect performance?

### 4. **Practical Deployment**
- Which method is most suitable for real-time analysis?
- What are the computational requirements?
- How should we handle edge cases?

## 🔄 Implementation Timeline

### Phase 1: Baseline Implementation (Week 1)
- [x] Data splitting completed
- [ ] Implement Method 1 (Baseline Detection)
- [ ] Basic evaluation pipeline

### Phase 2: Statistical Methods (Week 2)  
- [ ] Implement Method 2 (Statistical Detection)
- [ ] Parameter optimization framework
- [ ] Cross-validation setup

### Phase 3: Machine Learning (Week 3)
- [ ] Implement Method 3 (ML Detection)
- [ ] Feature engineering
- [ ] Model training and validation

### Phase 4: Comparison & Analysis (Week 4)
- [ ] Comprehensive comparison
- [ ] Cross-instrument analysis
- [ ] LOCO validation
- [ ] Final report and visualization

## 🎉 Success Criteria

- **Technical**: All 3 methods implemented and evaluated
- **Scientific**: Clear ranking of methods with statistical significance
- **Practical**: Deployment recommendations for STM32H743
- **Reproducible**: All results reproducible with provided data splits

---

*Next: Implement Method 1 - Baseline Peak Detection*  
*Last Updated: August 16, 2025*
