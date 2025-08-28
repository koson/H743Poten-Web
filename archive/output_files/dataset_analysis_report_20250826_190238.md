
# STM32 CV Dataset Analysis Report
Generated: 2025-08-26 19:02:38

## 📊 Dataset Overview
- **Total Files**: 1,685
- **File Size Range**: 3.9 KB - 8.6 KB
- **Average File Size**: 4.3 KB

## 🧪 Experimental Conditions Found

### Concentrations (mM):
  - 20.0: 330 files\n  - 10.0: 280 files\n  - 50.0: 275 files\n  - 5.0: 275 files

### Scan Rates (mV/s):
  - 200.0: 343 files\n  - 20.0: 343 files\n  - 50.0: 343 files\n  - 100.0: 332 files\n  - 400.0: 321 files

### Electrodes:
  - E1: 395 files\n  - E4: 330 files\n  - E5: 330 files\n  - E3: 319 files\n  - E2: 308 files

### Scan Numbers:
  - 5: 162 files\n  - 1: 152 files\n  - 2: 152 files\n  - 3: 152 files\n  - 4: 152 files\n  - 6: 152 files\n  - 7: 152 files\n  - 8: 152 files\n  - 9: 152 files\n  - 10: 152 files

## 📈 Data Completeness Analysis
- **Concentration Levels**: 4
- **Scan Rates**: 5  
- **Electrodes**: 5
- **Scans per Condition**: 11
- **Expected Combinations**: 1,100
- **Actual Files**: 1,685
- **Completeness Ratio**: 153.2%

## 🔧 Unit Conversion Analysis
- **Files Needing Conversion**: ~0 (0.0%)
- **Unit Distribution**: {}

## 🎯 Data Quality Assessment

### ✅ Strengths:
1. **Large Dataset**: 1,685 files provide excellent statistical power
2. **Systematic Naming**: Consistent filename patterns enable automatic processing
3. **Multiple Conditions**: 4 concentration levels × 5 scan rates
4. **Replication**: Average 84.2 replicates per condition

### ⚠️ Potential Issues:
1. **Unit Inconsistency**: Some files may have A units instead of µA
2. **File Size Variation**: CV range 0.3 KB suggests potential data quality differences

## 💡 Recommendations for Enhanced Analysis:

### 🚀 Immediate Actions:
1. **Run Unit Conversion**: Convert 0 files from A to µA
2. **Quality Check**: Validate files with unusual sizes
3. **Batch Processing**: Use enhanced CV calibration system for all 1,685 files

### 📊 Statistical Power:
- **Concentration Range**: 5.0 - 50.0 mM
- **Scan Rate Range**: 20.0 - 400.0 mV/s
- **Expected R² Improvement**: High confidence calibration curves with 84+ replicates per point

### 🎯 Confidence Enhancement:
1. **Cross-Validation**: Use multiple electrodes for robustness testing
2. **Outlier Detection**: Systematic identification of anomalous measurements
3. **Baseline Consistency**: Apply advanced baseline detection across all conditions
