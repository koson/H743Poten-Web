# 🧪 Peak Detection Validation Framework

## 📁 โครงสร้าง Folder

### 📊 reference_cv_data/
ข้อมูล CV จากเครื่องมือต่างๆ สำหรับการเปรียบเทียบ

#### palmsens/
- ข้อมูล CV จากเครื่อง PalmSens (มาตรฐานอุตสาหกรรม)
- รูปแบบไฟล์: .csv, .txt หรือรูปแบบที่ PalmSens export
- ตั้งชื่อไฟล์: `YYYYMMDD_sample_description_scan_rate.csv`
- ตัวอย่าง: `20250816_ferrocyanide_50mvs.csv`

#### stm32h743/
- ข้อมูล CV จากระบบ STM32H743 ของเราเอง
- รูปแบบไฟล์: .csv ตาม format ของระบบ
- ตั้งชื่อไฟล์: `CV_YYYYMMDD_sample_description.csv`
- ตัวอย่าง: `CV_20250816_ferrocyanide_50mvs.csv`

### 👨‍🔬 expert_annotations/
การวิเคราะห์ peak ด้วยตาและประสบการณ์ของผู้เชี่ยวชาญ

#### รูปแบบ JSON:
```json
{
  "file_reference": "20250816_ferrocyanide_50mvs.csv",
  "instrument": "palmsens",
  "sample_info": {
    "analyte": "ferrocyanide",
    "concentration": "1 mM",
    "electrolyte": "0.1 M KCl",
    "scan_rate": "50 mV/s"
  },
  "expert_analysis": {
    "annotator": "ชื่อผู้วิเคราะห์",
    "date": "2025-08-16",
    "peaks_detected": [
      {
        "peak_id": 1,
        "type": "anodic",
        "potential": 0.245,
        "current": 1.25e-5,
        "baseline_start": 0.180,
        "baseline_end": 0.320,
        "peak_width_fwhm": 0.065,
        "confidence": "high"
      }
    ],
    "overall_quality": "excellent",
    "notes": "Clear reversible peak, minimal noise"
  }
}
```

### 🤖 synthetic_data/
ข้อมูลจำลองที่ทราบคำตอบแน่นอน สำหรับการทดสอบ algorithm

### 📈 analysis_results/
ผลการเปรียบเทียบจาก 3 วิธี (Baseline, Statistical, ML)

---

## 🎯 Data Collection Guidelines

### สำหรับ PalmSens Data:
1. **Export เป็น CSV** พร้อม headers (Potential, Current)
2. **บันทึก metadata**: sample, concentration, scan rate, electrolyte
3. **ใช้ตัวอย่างเดียวกัน** กับ STM32H743 เพื่อการเปรียบเทียบ
4. **หลายๆ scan rate**: 25, 50, 100, 200 mV/s (ถ้าทำได้)

### สำหรับ STM32H743 Data:
1. **ใช้ autosave feature** ที่เราพึ่งสร้าง
2. **Same experimental conditions** กับ PalmSens
3. **Multiple measurements** สำหรับ statistical analysis
4. **บันทึกพารามิเตอร์** ทั้งหมดที่ใช้

### การตั้งชื่อไฟล์แนะนำ:
```
Format: YYYYMMDD_sample_concentration_scanrate_cycle_instrument
ตัวอย่าง:
- 20250816_FeCN_1mM_50mvs_3cyc_palmsens.csv
- 20250816_FeCN_1mM_50mvs_3cyc_stm32.csv
- 20250816_dopamine_10uM_100mvs_5cyc_palmsens.csv
```

---

## 🔬 Recommended Test Samples

### 1. Standard Electrochemical Systems:
- **Ferrocyanide/Ferricyanide** - reversible system, clear peaks
- **Dopamine** - irreversible, physiological relevance
- **Ascorbic Acid** - common interferent
- **Mixture of analytes** - overlapping peaks

### 2. Different Conditions:
- **Various concentrations**: 10 μM, 100 μM, 1 mM
- **Different scan rates**: 25, 50, 100, 200 mV/s
- **pH variations**: 6, 7, 8 (if applicable)
- **Different electrolytes**: KCl, PBS, NaCl

### 3. Challenging Cases:
- **Low SNR data** - dilute samples
- **Overlapping peaks** - multi-analyte systems
- **Irreversible systems** - asymmetric peaks
- **Noisy data** - realistic conditions

---

## 📊 Next Steps

1. **วางข้อมูล PalmSens และ STM32H743** ใน folders ที่เกี่ยวข้อง
2. **สร้าง expert annotations** สำหรับข้อมูลที่สำคัญ
3. **Implement baseline detection algorithm** เป็นอันดับแรก
4. **สร้าง comparison framework** สำหรับการเปรียบเทียบ
5. **Generate synthetic data** สำหรับการทดสอบ algorithm

---

## 📝 Documentation Standards

- **เก็บ log การทดลอง** ทุกครั้ง
- **Record experimental conditions** ให้ครบถ้วน
- **Document any anomalies** หรือปัญหาที่พบ
- **Version control** สำหรับข้อมูลทุกชุด

Ready for data collection! 🚀
