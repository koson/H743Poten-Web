#!/usr/bin/env python3
"""
LabPlot2 Export Functions for PLS Analysis
สำหรับการ export ข้อมูล PLS ในรูปแบบที่ LabPlot2 สามารถใช้งานได้
"""

import pandas as pd
import numpy as np
import json
import h5py
from datetime import datetime
from pathlib import Path

def export_labplot2_csv(data, filename, metadata=None):
    """
    Export data ในรูปแบบ CSV ที่ LabPlot2 สามารถอ่านได้
    พร้อม metadata comments
    """
    
    # สร้าง metadata header
    header_lines = [
        "# LabPlot2 Compatible Data File",
        f"# Generated: {datetime.now().isoformat()}",
        "# Dataset: PLS Analysis - Palmsens vs STM32 Potentiostat",
        "# Method: Enhanced Detector V4 Improved",
        "#",
        "# Data Description:",
        "# This dataset contains electrochemical peak analysis results",
        "# for Partial Least Squares (PLS) regression modeling",
        "#",
        "# Reference: Palmsens EmStat4S potentiostat",
        "# Target: STM32-based custom potentiostat", 
        "# Analyte: Potassium ferrocyanide K4[Fe(CN)6]",
        "# Method: Cyclic Voltammetry (CV)",
        "#"
    ]
    
    # เพิ่ม column descriptions
    if isinstance(data, pd.DataFrame):
        header_lines.extend([
            "# Column Descriptions:",
            "# filename: Original data filename",
            "# device: Potentiostat device (Palmsens/STM32)",
            "# concentration: K4[Fe(CN)6] concentration (mM)",
            "# scan_rate: CV scan rate (mV/s)",
            "# electrode: Working electrode identifier",
            "# ox_voltage: Oxidation peak potential (V vs ref)",
            "# ox_current: Oxidation peak current (µA)",
            "# ox_confidence: Oxidation peak detection confidence (%)",
            "# red_voltage: Reduction peak potential (V vs ref)",
            "# red_current: Reduction peak current (µA)", 
            "# red_confidence: Reduction peak detection confidence (%)",
            "# peak_separation: Peak-to-peak voltage separation (V)",
            "# current_ratio: Anodic/cathodic current ratio",
            "# midpoint_potential: Formal potential E₀' (V)",
            "#"
        ])
    
    # เพิ่ม custom metadata
    if metadata:
        header_lines.extend([
            "# Analysis Metadata:",
            f"# Total samples: {metadata.get('total_samples', 'unknown')}",
            f"# Successful detections: {metadata.get('success_rate', 'unknown')}%",
            f"# Peak detection method: {metadata.get('method', 'Enhanced V4 Improved')}",
            f"# Processing date: {metadata.get('date', datetime.now().date())}",
            "#"
        ])
    
    # เขียนไฟล์
    with open(filename, 'w', encoding='utf-8') as f:
        # เขียน header
        f.write('\n'.join(header_lines) + '\n')
        
        # เขียนข้อมูล
        if isinstance(data, pd.DataFrame):
            data.to_csv(f, index=False, float_format='%.6f')
        else:
            # สำหรับ dict หรือ list
            pd.DataFrame(data).to_csv(f, index=False, float_format='%.6f')
    
    print(f"✅ LabPlot2 CSV exported: {filename}")
    return filename

def export_labplot2_hdf5(data, filename, dataset_name="pls_analysis"):
    """
    Export data ในรูปแบบ HDF5 สำหรับ LabPlot2
    เหมาะสำหรับข้อมูลขนาดใหญ่
    """
    
    with h5py.File(filename, 'w') as hf:
        # สร้าง main dataset
        if isinstance(data, pd.DataFrame):
            # สำหรับ pandas DataFrame
            grp = hf.create_group(dataset_name)
            
            # เก็บข้อมูลแต่ละ column
            for col in data.columns:
                if data[col].dtype == 'object':
                    # สำหรับ string data
                    grp.create_dataset(col, data=data[col].astype('S'))
                else:
                    # สำหรับ numeric data
                    grp.create_dataset(col, data=data[col].values)
            
            # เพิ่ม attributes (metadata)
            grp.attrs['description'] = 'PLS Analysis Data - Palmsens vs STM32'
            grp.attrs['method'] = 'Enhanced Detector V4 Improved'
            grp.attrs['created'] = datetime.now().isoformat()
            grp.attrs['columns'] = list(data.columns)
            grp.attrs['shape'] = data.shape
            
        else:
            # สำหรับ numpy array
            hf.create_dataset(dataset_name, data=data)
            hf.attrs['description'] = 'PLS Analysis Data'
            hf.attrs['created'] = datetime.now().isoformat()
    
    print(f"✅ LabPlot2 HDF5 exported: {filename}")
    return filename

def export_labplot2_json(data, filename):
    """
    Export data ในรูปแบบ JSON ที่มี structure ชัดเจน
    สำหรับการ import ใน LabPlot2 หรือเครื่องมืออื่น
    """
    
    # สร้าง JSON structure
    export_data = {
        "metadata": {
            "title": "PLS Analysis: Palmsens vs STM32 Potentiostat Comparison",
            "description": "Electrochemical peak analysis for PLS regression modeling",
            "method": "Enhanced Detector V4 Improved",
            "reference_device": "Palmsens EmStat4S",
            "target_device": "STM32 Custom Potentiostat",
            "analyte": "Potassium ferrocyanide K4[Fe(CN)6]",
            "technique": "Cyclic Voltammetry",
            "created": datetime.now().isoformat(),
            "format_version": "1.0"
        },
        "column_info": {
            "concentration": {"unit": "mM", "description": "Analyte concentration"},
            "scan_rate": {"unit": "mV/s", "description": "CV scan rate"},
            "ox_voltage": {"unit": "V", "description": "Oxidation peak potential"},
            "ox_current": {"unit": "µA", "description": "Oxidation peak current"},
            "red_voltage": {"unit": "V", "description": "Reduction peak potential"},
            "red_current": {"unit": "µA", "description": "Reduction peak current"},
            "peak_separation": {"unit": "V", "description": "Peak-to-peak separation"},
            "current_ratio": {"unit": "dimensionless", "description": "Anodic/cathodic ratio"},
            "midpoint_potential": {"unit": "V", "description": "Formal potential E₀'"}
        },
        "data": data.to_dict('records') if isinstance(data, pd.DataFrame) else data
    }
    
    # เขียน JSON file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ LabPlot2 JSON exported: {filename}")
    return filename

def create_labplot2_project_template(data_file, project_name="PLS_Analysis"):
    """
    สร้างไฟล์ template สำหรับ LabPlot2 project
    ปรับแต่งได้ตามต้องการ
    """
    
    template = f"""<?xml version="1.0" encoding="UTF-8"?>
<project version="2.8.0" fileName="{project_name}.lml">
    <folder name="Data">
        <spreadsheet name="PLS_Data" fileName="{data_file}">
            <comment>PLS Analysis Data - Palmsens vs STM32 Comparison</comment>
            <column name="concentration" type="Numeric"/>
            <column name="device" type="Text"/>
            <column name="ox_voltage" type="Numeric"/>
            <column name="ox_current" type="Numeric"/>
            <column name="red_voltage" type="Numeric"/>
            <column name="red_current" type="Numeric"/>
            <column name="peak_separation" type="Numeric"/>
            <column name="current_ratio" type="Numeric"/>
        </spreadsheet>
    </folder>
    
    <folder name="Plots">
        <worksheet name="PLS_Visualization">
            <comment>Standard PLS analysis plots</comment>
            <!-- Plot configurations would go here -->
        </worksheet>
    </folder>
    
    <folder name="Analysis">
        <!-- Statistical analysis configurations -->
    </folder>
</project>"""
    
    template_file = f"{project_name}_template.lml"
    with open(template_file, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"✅ LabPlot2 project template: {template_file}")
    return template_file

def export_all_labplot2_formats(data, base_filename="pls_analysis", metadata=None):
    """
    Export ข้อมูลในทุกรูปแบบที่ LabPlot2 รองรับ
    """
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exports = {}
    
    # CSV format
    csv_file = f"{base_filename}_{timestamp}.csv"
    exports['csv'] = export_labplot2_csv(data, csv_file, metadata)
    
    # HDF5 format  
    hdf5_file = f"{base_filename}_{timestamp}.h5"
    exports['hdf5'] = export_labplot2_hdf5(data, hdf5_file)
    
    # JSON format
    json_file = f"{base_filename}_{timestamp}.json"
    exports['json'] = export_labplot2_json(data, json_file)
    
    # Project template
    template_file = create_labplot2_project_template(csv_file, base_filename)
    exports['template'] = template_file
    
    print(f"\n📦 LabPlot2 Export Summary:")
    print(f"  CSV Data: {exports['csv']}")
    print(f"  HDF5 Data: {exports['hdf5']}")
    print(f"  JSON Data: {exports['json']}")
    print(f"  Project Template: {exports['template']}")
    
    return exports

# Example usage
if __name__ == "__main__":
    # สร้างข้อมูลตัวอย่าง
    sample_data = pd.DataFrame({
        'filename': ['Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv', 'STM32_0.5mM_CV_100mVpS_E1_scan_01.csv'],
        'device': ['Palmsens', 'STM32'],
        'concentration': [0.5, 0.5],
        'scan_rate': [100, 100],
        'electrode': ['E1', 'E1'],
        'ox_voltage': [0.190, 0.185],
        'ox_current': [15.38, 14.92],
        'ox_confidence': [78.5, 82.1],
        'red_voltage': [0.100, 0.095],
        'red_current': [-17.50, -16.85],
        'red_confidence': [100.0, 95.3],
        'peak_separation': [0.090, 0.090],
        'current_ratio': [0.88, 0.89],
        'midpoint_potential': [0.145, 0.140]
    })
    
    # Export ทุกรูปแบบ
    metadata = {
        'total_samples': len(sample_data),
        'success_rate': 100,
        'method': 'Enhanced Detector V4 Improved',
        'date': datetime.now().date()
    }
    
    exports = export_all_labplot2_formats(sample_data, "pls_demo", metadata)
    print(f"\n🎉 LabPlot2 exports complete!")
