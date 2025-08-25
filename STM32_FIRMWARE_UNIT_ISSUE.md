# 🔧 STM32 Firmware Enhancement Issue

## 📋 Issue Summary
**Current**: STM32 firmware outputs CSV with header `V,A` but actual current values are in microampere (µA) scale  
**Desired**: STM32 firmware should output CSV with correct header `V,uA` to match the actual unit scale

## 🔍 Current Behavior
```csv
FileName: Pipot_Ferro-1_0mM_50mVpS_E1_scan_6.csv
V,A
-0.3805,-2.3585e-06
-0.3903,-2.6922e-06
```

**Issue**: Header says "A" (Ampere) but values are actually in µA scale (-2.3585e-06 A = -2.36 µA)

## ✅ Desired Behavior
```csv
FileName: Pipot_Ferro-1_0mM_50mVpS_E1_scan_6.csv
V,uA
-0.3805,-2.3585
-0.3903,-2.6922
```

**Benefits**:
- Header matches actual unit scale
- No need for backend unit conversion workarounds
- Consistent with PalmSens format
- Clearer for users

## 🛠️ Current Workaround
Backend now detects STM32/Pipot files and applies 1e6 scaling factor:
```python
# Detect STM32 files and treat 'A' as µA
is_stm32_file = (
    'pipot' in file_path.lower() or 
    'stm32' in file_path.lower() or
    (current_unit == 'a' and lines[0].strip().startswith('FileName:'))
)

if current_unit == 'a' and is_stm32_file:
    current_scale = 1e6  # Convert A to µA for STM32 files
```

## 🎯 Implementation Requirements
1. **Change CSV header** from `V,A` to `V,uA`
2. **Change current values** from scientific notation (e-6) to regular µA values
3. **Maintain compatibility** with existing data analysis tools
4. **Update documentation** and examples

## 📊 Impact
- **Users**: Clearer understanding of units
- **Backend**: Simplified unit handling
- **Data Analysis**: Consistent format across instruments
- **Future Maintenance**: Reduced complexity

## 🔗 Related Files
- STM32 firmware CSV output generation
- Backend: `src/routes/peak_detection.py` (current workaround)
- Test data: `Test_data/Stm32/Pipot_Ferro_*/`

---
**Priority**: Medium  
**Category**: Enhancement  
**Affects**: STM32 firmware, CSV output format