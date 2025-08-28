#!/usr/bin/env python3
"""
LabPlot2 Data Extractor for PLS Analysis
========================================
สกัดข้อมูลจากการวิเคราะห์ PLS เป็นไฟล์ CSV แยกตามรูปย่อย
เพื่อนำเข้า LabPlot2 โดยตรง

Author: AI Assistant
Date: 2025-08-28
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import requests
import warnings
warnings.filterwarnings('ignore')

def load_comprehensive_data(results_dir):
    """โหลดข้อมูลครบถ้วนจากการวิเคราะห์ PLS"""
    
    # อ่านข้อมูลหลัก
    data_file = None
    report_file = None
    
    for file in os.listdir(results_dir):
        if file.startswith('comprehensive_dataset') and file.endswith('.csv'):
            data_file = os.path.join(results_dir, file)
        elif file.startswith('comprehensive_pls_report') and file.endswith('.json'):
            report_file = os.path.join(results_dir, file)
    
    if not data_file or not report_file:
        raise FileNotFoundError("ไม่พบไฟล์ข้อมูลหรือรายงาน")
    
    # อ่านข้อมูล
    df = pd.read_csv(data_file)
    
    with open(report_file, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    return df, report

def create_device_classification_data(df, report, output_dir):
    """สร้างข้อมูลสำหรับ Device Classification Plot"""
    
    predictions = report['analysis_results']['device_classification']['predictions']
    
    # สร้างข้อมูลสำหรับ scatter plot
    scatter_data = []
    
    for i, (_, row) in enumerate(df.iterrows()):
        if i < len(predictions):
            predicted = predictions[i]
            actual = 0 if row['device'] == 'Palmsens' else 1  # Palmsens=0, STM32=1
            
            scatter_data.append({
                'Sample_ID': i + 1,
                'Device': row['device'],
                'Actual_Class': actual,
                'Predicted_Class': predicted,
                'Concentration_mM': row['concentration'],
                'Scan_Rate_mVs': row['scan_rate'],
                'OX_Voltage_V': row['ox_voltage'],
                'OX_Current_A': row['ox_current'],
                'RED_Voltage_V': row['red_voltage'],
                'RED_Current_A': row['red_current'],
                'Peak_Separation_V': row['peak_separation']
            })
    
    scatter_df = pd.DataFrame(scatter_data)
    
    # แยกข้อมูลตามเครื่อง
    palmsens_data = scatter_df[scatter_df['Device'] == 'Palmsens'].copy()
    stm32_data = scatter_df[scatter_df['Device'] == 'STM32'].copy()
    
    # บันทึกไฟล์
    scatter_df.to_csv(os.path.join(output_dir, 'device_classification_all.csv'), index=False)
    palmsens_data.to_csv(os.path.join(output_dir, 'device_classification_palmsens.csv'), index=False)
    stm32_data.to_csv(os.path.join(output_dir, 'device_classification_stm32.csv'), index=False)
    
    # สร้างข้อมูลสำหรับ Feature Importance
    feature_importance = report['analysis_results']['device_classification']['feature_importance']
    importance_df = pd.DataFrame([
        {'Feature': feature, 'Importance': importance, 'Abs_Importance': abs(importance)}
        for feature, importance in feature_importance.items()
    ]).sort_values('Abs_Importance', ascending=True)
    
    importance_df.to_csv(os.path.join(output_dir, 'device_classification_feature_importance.csv'), index=False)
    
    return {
        'scatter_all': 'device_classification_all.csv',
        'scatter_palmsens': 'device_classification_palmsens.csv', 
        'scatter_stm32': 'device_classification_stm32.csv',
        'feature_importance': 'device_classification_feature_importance.csv'
    }

def create_concentration_prediction_data(df, report, output_dir):
    """สร้างข้อมูลสำหรับ Concentration Prediction Plot"""
    
    predictions = report['analysis_results']['concentration_prediction']['predictions']
    
    # สร้างข้อมูลสำหรับ scatter plot
    prediction_data = []
    
    for i, (_, row) in enumerate(df.iterrows()):
        if i < len(predictions):
            predicted = predictions[i]
            actual = row['concentration']
            
            prediction_data.append({
                'Sample_ID': i + 1,
                'Device': row['device'],
                'Actual_Concentration_mM': actual,
                'Predicted_Concentration_mM': predicted,
                'Prediction_Error_mM': predicted - actual,
                'Absolute_Error_mM': abs(predicted - actual),
                'Relative_Error_Percent': abs(predicted - actual) / actual * 100 if actual > 0 else 0,
                'Scan_Rate_mVs': row['scan_rate'],
                'OX_Voltage_V': row['ox_voltage'],
                'OX_Current_A': row['ox_current'],
                'RED_Voltage_V': row['red_voltage'],
                'RED_Current_A': row['red_current'],
                'Peak_Separation_V': row['peak_separation']
            })
    
    prediction_df = pd.DataFrame(prediction_data)
    
    # แยกข้อมูลตามเครื่อง
    palmsens_pred = prediction_df[prediction_df['Device'] == 'Palmsens'].copy()
    stm32_pred = prediction_df[prediction_df['Device'] == 'STM32'].copy()
    
    # บันทึกไฟล์
    prediction_df.to_csv(os.path.join(output_dir, 'concentration_prediction_all.csv'), index=False)
    palmsens_pred.to_csv(os.path.join(output_dir, 'concentration_prediction_palmsens.csv'), index=False)
    stm32_pred.to_csv(os.path.join(output_dir, 'concentration_prediction_stm32.csv'), index=False)
    
    # สร้างข้อมูลสำหรับ Perfect Prediction Line (y=x)
    min_conc = prediction_df['Actual_Concentration_mM'].min()
    max_conc = prediction_df['Actual_Concentration_mM'].max()
    perfect_line = pd.DataFrame({
        'Actual_Concentration_mM': [min_conc, max_conc],
        'Predicted_Concentration_mM': [min_conc, max_conc],
        'Line_Type': ['Perfect Prediction', 'Perfect Prediction']
    })
    perfect_line.to_csv(os.path.join(output_dir, 'concentration_perfect_line.csv'), index=False)
    
    # สร้างข้อมูลสำหรับ Feature Importance
    feature_importance = report['analysis_results']['concentration_prediction']['feature_importance']
    importance_df = pd.DataFrame([
        {'Feature': feature, 'Importance': importance, 'Abs_Importance': abs(importance)}
        for feature, importance in feature_importance.items()
    ]).sort_values('Abs_Importance', ascending=True)
    
    importance_df.to_csv(os.path.join(output_dir, 'concentration_prediction_feature_importance.csv'), index=False)
    
    return {
        'scatter_all': 'concentration_prediction_all.csv',
        'scatter_palmsens': 'concentration_prediction_palmsens.csv',
        'scatter_stm32': 'concentration_prediction_stm32.csv',
        'perfect_line': 'concentration_perfect_line.csv',
        'feature_importance': 'concentration_prediction_feature_importance.csv'
    }

def create_bland_altman_data(df, report, output_dir):
    """สร้างข้อมูลสำหรับ Bland-Altman Plot"""
    
    predictions = report['analysis_results']['concentration_prediction']['predictions']
    
    bland_altman_data = []
    
    for i, (_, row) in enumerate(df.iterrows()):
        if i < len(predictions):
            predicted = predictions[i]
            actual = row['concentration']
            
            mean_value = (actual + predicted) / 2
            difference = predicted - actual
            
            bland_altman_data.append({
                'Sample_ID': i + 1,
                'Device': row['device'],
                'Mean_Concentration_mM': mean_value,
                'Difference_mM': difference,
                'Actual_Concentration_mM': actual,
                'Predicted_Concentration_mM': predicted,
                'Scan_Rate_mVs': row['scan_rate']
            })
    
    bland_altman_df = pd.DataFrame(bland_altman_data)
    
    # คำนวณสถิติสำหรับ Bland-Altman
    mean_diff = bland_altman_df['Difference_mM'].mean()
    std_diff = bland_altman_df['Difference_mM'].std()
    
    # สร้างเส้น reference lines
    reference_lines = pd.DataFrame({
        'X_Start': [bland_altman_df['Mean_Concentration_mM'].min()] * 3,
        'X_End': [bland_altman_df['Mean_Concentration_mM'].max()] * 3,
        'Y_Value': [mean_diff, mean_diff + 1.96*std_diff, mean_diff - 1.96*std_diff],
        'Line_Type': ['Bias', 'Upper Limit (+1.96 SD)', 'Lower Limit (-1.96 SD)'],
        'Line_Label': [f'Bias = {mean_diff:.3f} mM', 
                      f'+1.96 SD = {mean_diff + 1.96*std_diff:.3f} mM',
                      f'-1.96 SD = {mean_diff - 1.96*std_diff:.3f} mM']
    })
    
    # แยกข้อมูลตามเครื่อง
    palmsens_ba = bland_altman_df[bland_altman_df['Device'] == 'Palmsens'].copy()
    stm32_ba = bland_altman_df[bland_altman_df['Device'] == 'STM32'].copy()
    
    # บันทึกไฟล์
    bland_altman_df.to_csv(os.path.join(output_dir, 'bland_altman_all.csv'), index=False)
    palmsens_ba.to_csv(os.path.join(output_dir, 'bland_altman_palmsens.csv'), index=False)
    stm32_ba.to_csv(os.path.join(output_dir, 'bland_altman_stm32.csv'), index=False)
    reference_lines.to_csv(os.path.join(output_dir, 'bland_altman_reference_lines.csv'), index=False)
    
    return {
        'scatter_all': 'bland_altman_all.csv',
        'scatter_palmsens': 'bland_altman_palmsens.csv',
        'scatter_stm32': 'bland_altman_stm32.csv',
        'reference_lines': 'bland_altman_reference_lines.csv'
    }

def create_error_analysis_data(df, report, output_dir):
    """สร้างข้อมูลสำหรับ Error Analysis by Concentration"""
    
    predictions = report['analysis_results']['concentration_prediction']['predictions']
    
    # คำนวณ error ตามความเข้มข้น
    error_data = []
    
    for i, (_, row) in enumerate(df.iterrows()):
        if i < len(predictions):
            predicted = predictions[i]
            actual = row['concentration']
            error = abs(predicted - actual)
            
            error_data.append({
                'Sample_ID': i + 1,
                'Device': row['device'],
                'Concentration_mM': actual,
                'Absolute_Error_mM': error,
                'Relative_Error_Percent': error / actual * 100 if actual > 0 else 0,
                'Scan_Rate_mVs': row['scan_rate']
            })
    
    error_df = pd.DataFrame(error_data)
    
    # คำนวณสถิติตามความเข้มข้นและเครื่อง
    concentration_summary = error_df.groupby(['Concentration_mM', 'Device']).agg({
        'Absolute_Error_mM': ['mean', 'std', 'count'],
        'Relative_Error_Percent': ['mean', 'std']
    }).round(4)
    
    concentration_summary.columns = ['MAE_Mean_mM', 'MAE_Std_mM', 'N_Samples', 'REP_Mean_Percent', 'REP_Std_Percent']
    concentration_summary = concentration_summary.reset_index()
    
    # แยกข้อมูลตามเครื่อง
    palmsens_error = error_df[error_df['Device'] == 'Palmsens'].copy()
    stm32_error = error_df[error_df['Device'] == 'STM32'].copy()
    
    palmsens_summary = concentration_summary[concentration_summary['Device'] == 'Palmsens'].copy()
    stm32_summary = concentration_summary[concentration_summary['Device'] == 'STM32'].copy()
    
    # บันทึกไฟล์
    error_df.to_csv(os.path.join(output_dir, 'error_analysis_all.csv'), index=False)
    palmsens_error.to_csv(os.path.join(output_dir, 'error_analysis_palmsens.csv'), index=False)
    stm32_error.to_csv(os.path.join(output_dir, 'error_analysis_stm32.csv'), index=False)
    concentration_summary.to_csv(os.path.join(output_dir, 'error_summary_by_concentration.csv'), index=False)
    palmsens_summary.to_csv(os.path.join(output_dir, 'error_summary_palmsens.csv'), index=False)
    stm32_summary.to_csv(os.path.join(output_dir, 'error_summary_stm32.csv'), index=False)
    
    return {
        'raw_errors_all': 'error_analysis_all.csv',
        'raw_errors_palmsens': 'error_analysis_palmsens.csv',
        'raw_errors_stm32': 'error_analysis_stm32.csv',
        'summary_all': 'error_summary_by_concentration.csv',
        'summary_palmsens': 'error_summary_palmsens.csv',
        'summary_stm32': 'error_summary_stm32.csv'
    }

def create_precision_analysis_data(df, report, output_dir):
    """สร้างข้อมูลสำหรับ Precision Analysis (CV%))"""
    
    # คำนวณ CV% ตามความเข้มข้น scan rate และเครื่อง
    precision_data = []
    
    # Group by concentration, scan_rate, device
    groups = df.groupby(['concentration', 'scan_rate', 'device'])
    
    for (conc, scan_rate, device), group in groups:
        if len(group) > 1:  # ต้องมีข้อมูลมากกว่า 1 ตัวอย่างเพื่อคำนวณ CV
            for feature in ['ox_voltage', 'ox_current', 'red_voltage', 'red_current', 'peak_separation']:
                values = group[feature].dropna()
                if len(values) > 1:
                    mean_val = values.mean()
                    std_val = values.std()
                    cv_percent = (std_val / abs(mean_val)) * 100 if mean_val != 0 else 0
                    
                    precision_data.append({
                        'Concentration_mM': conc,
                        'Scan_Rate_mVs': scan_rate,
                        'Device': device,
                        'Feature': feature,
                        'Mean_Value': mean_val,
                        'Std_Value': std_val,
                        'CV_Percent': cv_percent,
                        'N_Replicates': len(values),
                        'Precision_Category': 'Excellent' if cv_percent < 2 else 
                                            'Good' if cv_percent < 5 else
                                            'Acceptable' if cv_percent < 10 else 'Poor'
                    })
    
    precision_df = pd.DataFrame(precision_data)
    
    if not precision_df.empty:
        # แยกข้อมูลตามเครื่อง
        palmsens_precision = precision_df[precision_df['Device'] == 'Palmsens'].copy()
        stm32_precision = precision_df[precision_df['Device'] == 'STM32'].copy()
        
        # สร้างสรุปโดยรวม
        precision_summary = precision_df.groupby(['Device', 'Feature']).agg({
            'CV_Percent': ['mean', 'std', 'min', 'max', 'count']
        }).round(4)
        
        precision_summary.columns = ['CV_Mean', 'CV_Std', 'CV_Min', 'CV_Max', 'N_Measurements']
        precision_summary = precision_summary.reset_index()
        
        # บันทึกไฟล์
        precision_df.to_csv(os.path.join(output_dir, 'precision_analysis_all.csv'), index=False)
        palmsens_precision.to_csv(os.path.join(output_dir, 'precision_analysis_palmsens.csv'), index=False)
        stm32_precision.to_csv(os.path.join(output_dir, 'precision_analysis_stm32.csv'), index=False)
        precision_summary.to_csv(os.path.join(output_dir, 'precision_summary.csv'), index=False)
        
        # สร้างข้อมูลสำหรับ CV% threshold lines
        cv_thresholds = pd.DataFrame({
            'Threshold_Percent': [2, 5, 10],
            'Quality_Level': ['Excellent', 'Good', 'Acceptable'],
            'Color_Code': ['green', 'yellow', 'orange']
        })
        cv_thresholds.to_csv(os.path.join(output_dir, 'cv_threshold_lines.csv'), index=False)
    
    return {
        'precision_all': 'precision_analysis_all.csv',
        'precision_palmsens': 'precision_analysis_palmsens.csv',
        'precision_stm32': 'precision_analysis_stm32.csv',
        'precision_summary': 'precision_summary.csv',
        'cv_thresholds': 'cv_threshold_lines.csv'
    }

def create_labplot2_import_guide(output_dir, file_mapping):
    """สร้างคู่มือการนำเข้าข้อมูลใน LabPlot2"""
    
    guide_content = """# LabPlot2 Import Guide for PLS Analysis Data
# ================================================

## ไฟล์ข้อมูลที่สร้างขึ้น:

### 1. Device Classification Plots
"""
    
    for category, files in file_mapping.items():
        guide_content += f"\n### {category.replace('_', ' ').title()}\n"
        for plot_type, filename in files.items():
            guide_content += f"- **{plot_type}**: {filename}\n"
        guide_content += "\n"
    
    guide_content += """
## วิธีการนำเข้าใน LabPlot2:

### 1. Device Classification Scatter Plot
1. เปิด LabPlot2
2. File > Import > CSV
3. เลือกไฟล์ device_classification_all.csv
4. สร้าง XY-Plot:
   - X axis: Actual_Class
   - Y axis: Predicted_Class
   - Symbol: แยกสีตาม Device column

### 2. Concentration Prediction Plot
1. Import: concentration_prediction_all.csv
2. สร้าง XY-Plot:
   - X axis: Actual_Concentration_mM
   - Y axis: Predicted_Concentration_mM
   - Symbol: แยกสีตาม Device column
3. เพิ่ม Perfect Line:
   - Import: concentration_perfect_line.csv
   - เพิ่มเป็น Line plot บนกราฟเดียวกัน

### 3. Bland-Altman Plot
1. Import: bland_altman_all.csv
2. สร้าง XY-Plot:
   - X axis: Mean_Concentration_mM
   - Y axis: Difference_mM
   - Symbol: แยกสีตาม Device column
3. เพิ่ม Reference Lines:
   - Import: bland_altman_reference_lines.csv
   - เพิ่มเป็น Horizontal lines

### 4. Error Analysis
1. Import: error_summary_by_concentration.csv
2. สร้าง XY-Plot with Error Bars:
   - X axis: Concentration_mM
   - Y axis: MAE_Mean_mM
   - Error bars: MAE_Std_mM
   - แยกสีตาม Device column

### 5. Precision Analysis (CV%)
1. Import: precision_analysis_all.csv
2. สร้าง Box Plot หรือ Scatter Plot:
   - X axis: Feature
   - Y axis: CV_Percent
   - แยกสีตาม Device column
3. เพิ่ม Threshold Lines:
   - Import: cv_threshold_lines.csv
   - เพิ่มเป็น Horizontal lines ที่ 2%, 5%, 10%

### 6. Feature Importance
1. Import: device_classification_feature_importance.csv
2. สร้าง Bar Plot:
   - X axis: Feature
   - Y axis: Abs_Importance
3. Import: concentration_prediction_feature_importance.csv
   - สร้าง Bar Plot แยกต่างหาก

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
1. นำเข้าไฟล์ที่ต้องการ
2. เลือกประเภทกราฟที่เหมาะสม
3. ตั้งค่าสีและสัญลักษณ์
4. เพิ่ม Labels และ Legends
5. ปรับแต่งแกนและขนาดข้อความ
6. Export เป็น PDF หรือ PNG สำหรับ Publication

"""
    
    with open(os.path.join(output_dir, 'LabPlot2_Import_Guide.md'), 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    return 'LabPlot2_Import_Guide.md'

def main():
    """ฟังก์ชันหลักสำหรับสกัดข้อมูลทั้งหมด"""
    
    # ค้นหาโฟลเดอร์ผลลัพธ์ล่าสุด
    base_dir = "."
    results_dirs = [d for d in os.listdir(base_dir) if d.startswith('comprehensive_pls_results_')]
    
    if not results_dirs:
        print("❌ ไม่พบโฟลเดอร์ผลลัพธ์")
        return
    
    # เลือกโฟลเดอร์ล่าสุด
    latest_dir = max(results_dirs)
    results_path = os.path.join(base_dir, latest_dir)
    
    print(f"🔍 กำลังประมวลผลข้อมูลจาก: {latest_dir}")
    
    # สร้างโฟลเดอร์สำหรับไฟล์ LabPlot2
    labplot_dir = os.path.join(results_path, 'LabPlot2_Data')
    os.makedirs(labplot_dir, exist_ok=True)
    
    try:
        # โหลดข้อมูล
        df, report = load_comprehensive_data(results_path)
        print(f"✅ โหลดข้อมูลสำเร็จ: {len(df)} samples")
        
        # สร้างข้อมูลแต่ละประเภท
        file_mapping = {}
        
        print("📊 กำลังสร้างข้อมูล Device Classification...")
        file_mapping['device_classification'] = create_device_classification_data(df, report, labplot_dir)
        
        print("📈 กำลังสร้างข้อมูล Concentration Prediction...")
        file_mapping['concentration_prediction'] = create_concentration_prediction_data(df, report, labplot_dir)
        
        print("📉 กำลังสร้างข้อมูล Bland-Altman...")
        file_mapping['bland_altman'] = create_bland_altman_data(df, report, labplot_dir)
        
        print("📊 กำลังสร้างข้อมูล Error Analysis...")
        file_mapping['error_analysis'] = create_error_analysis_data(df, report, labplot_dir)
        
        print("📋 กำลังสร้างข้อมูล Precision Analysis...")
        file_mapping['precision_analysis'] = create_precision_analysis_data(df, report, labplot_dir)
        
        print("📖 กำลังสร้างคู่มือการใช้งาน...")
        guide_file = create_labplot2_import_guide(labplot_dir, file_mapping)
        
        # สรุปผลลัพธ์
        print("\n" + "="*60)
        print("🎉 สร้างไฟล์สำหรับ LabPlot2 เรียบร้อยแล้ว!")
        print("="*60)
        print(f"📁 ตำแหน่งไฟล์: {labplot_dir}")
        print("\n📋 ไฟล์ที่สร้างขึ้น:")
        
        total_files = 0
        for category, files in file_mapping.items():
            print(f"\n🔸 {category.replace('_', ' ').title()}:")
            for plot_type, filename in files.items():
                print(f"   • {filename}")
                total_files += 1
        
        print(f"\n📖 คู่มือการใช้งาน: {guide_file}")
        print(f"\n✅ สร้างไฟล์ทั้งหมด {total_files + 1} ไฟล์")
        print("\n🚀 พร้อมนำเข้า LabPlot2 แล้ว!")
        print("   อ่านคู่มือใน LabPlot2_Import_Guide.md สำหรับรายละเอียด")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
