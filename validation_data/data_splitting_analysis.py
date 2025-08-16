#!/usr/bin/env python3
"""
Data Splitting Strategy Analysis for Peak Detection Framework
วิเคราะห์และแนะนำการแบ่งข้อมูลสำหรับ validation
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from collections import defaultdict
import random

class DataSplittingAnalyzer:
    def __init__(self):
        self.base_path = Path("validation_data")
        self.palmsens_path = self.base_path / "reference_cv_data" / "palmsens"
        self.stm32_path = self.base_path / "reference_cv_data" / "stm32h743"
    
    def analyze_data_distribution(self):
        """วิเคราะห์การกระจายของข้อมูลเพื่อวางแผนการแบ่ง"""
        
        print("📊 การวิเคราะห์การกระจายข้อมูลสำหรับ Peak Detection")
        print("=" * 70)
        
        # นับไฟล์และวิเคราะห์ patterns
        palmsens_files = list(self.palmsens_path.glob("*.csv")) if self.palmsens_path.exists() else []
        stm32_files = list(self.stm32_path.glob("*.csv")) if self.stm32_path.exists() else []
        
        print(f"📁 ข้อมูลทั้งหมด:")
        print(f"   PalmSens: {len(palmsens_files)} ไฟล์")
        print(f"   STM32H743: {len(stm32_files)} ไฟล์")
        print(f"   รวม: {len(palmsens_files) + len(stm32_files)} ไฟล์")
        
        # วิเคราะห์ experimental conditions
        palmsens_conditions = self._extract_experimental_conditions(palmsens_files, "palmsens")
        stm32_conditions = self._extract_experimental_conditions(stm32_files, "stm32")
        
        print(f"\n🧪 เงื่อนไขการทดลอง:")
        print(f"   PalmSens:")
        self._print_conditions(palmsens_conditions)
        print(f"   STM32H743:")
        self._print_conditions(stm32_conditions)
        
        # คำนวณขนาดข้อมูลที่เหมาะสม
        self._recommend_splitting_strategy(palmsens_files, stm32_files, palmsens_conditions, stm32_conditions)
        
        return palmsens_conditions, stm32_conditions
    
    def _extract_experimental_conditions(self, files, instrument):
        """สกัดเงื่อนไขการทดลองจากชื่อไฟล์"""
        conditions = defaultdict(set)
        
        for file_path in files:
            try:
                name = file_path.name
                if instrument == "palmsens":
                    # Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv
                    parts = name.replace('.csv', '').split('_')
                    if len(parts) >= 6:
                        concentration = parts[1]
                        scan_rate = parts[3]
                        electrode = parts[4]
                        scan_num = parts[6]
                        
                        conditions['concentrations'].add(concentration)
                        conditions['scan_rates'].add(scan_rate)
                        conditions['electrodes'].add(electrode)
                        conditions['scan_numbers'].add(scan_num)
                        
                elif instrument == "stm32":
                    # Pipot_Ferro_0_5mM_100mVpS_E1_scan_01.csv หรือ Pipot_Ferro-10mM_100mVpS_E1_scan_01.csv
                    parts = name.replace('.csv', '').split('_')
                    if len(parts) >= 6:
                        # Handle different naming patterns
                        if 'Ferro-' in parts[1]:
                            # Pipot_Ferro-10mM_100mVpS_E1_scan_01.csv
                            concentration = parts[1].replace('Ferro-', '')
                        else:
                            # Pipot_Ferro_0_5mM_100mVpS_E1_scan_01.csv
                            concentration = f"{parts[2]}.{parts[3]}"
                        
                        scan_rate = parts[-4] if len(parts) > 6 else parts[3]
                        electrode = parts[-3] if len(parts) > 6 else parts[4]
                        scan_num = parts[-1] if len(parts) > 6 else parts[6]
                        
                        conditions['concentrations'].add(concentration)
                        conditions['scan_rates'].add(scan_rate)
                        conditions['electrodes'].add(electrode)
                        conditions['scan_numbers'].add(scan_num)
                        
            except Exception as e:
                continue
        
        # Convert sets to sorted lists
        for key in conditions:
            conditions[key] = sorted(list(conditions[key]))
            
        return dict(conditions)
    
    def _print_conditions(self, conditions):
        """พิมพ์เงื่อนไขการทดลอง"""
        for key, values in conditions.items():
            print(f"     {key}: {values[:10]}{'...' if len(values) > 10 else ''} (รวม {len(values)})")
    
    def _recommend_splitting_strategy(self, palmsens_files, stm32_files, palmsens_conditions, stm32_conditions):
        """แนะนำกลยุทธ์การแบ่งข้อมูล"""
        
        print(f"\n🎯 คำแนะนำการแบ่งข้อมูลสำหรับ Peak Detection Framework:")
        print("=" * 70)
        
        total_files = len(palmsens_files) + len(stm32_files)
        
        # คำนวณการแบ่งข้อมูลแนะนำ
        print(f"📊 ข้อมูลทั้งหมด: {total_files:,} ไฟล์")
        
        # แนะนำการแบ่งตามหลักการ ML
        train_percent = 70
        val_percent = 15  
        test_percent = 15
        
        train_size = int(total_files * train_percent / 100)
        val_size = int(total_files * val_percent / 100)
        test_size = total_files - train_size - val_size
        
        print(f"\n🔄 การแบ่งข้อมูลแนะนำ:")
        print(f"   📚 Training Set: {train_percent}% = {train_size:,} ไฟล์")
        print(f"   🔍 Validation Set: {val_percent}% = {val_size:,} ไฟล์") 
        print(f"   🧪 Test Set: {test_percent}% = {test_size:,} ไฟล์")
        
        print(f"\n💡 เหตุผลการแบ่งแบบนี้:")
        print(f"   ✅ Training (70%): ข้อมูลเพียงพอสำหรับการเรียนรู้ pattern")
        print(f"   ✅ Validation (15%): สำหรับ hyperparameter tuning และ model selection")
        print(f"   ✅ Test (15%): สำหรับประเมินประสิทธิภาพจริงแบบ unbiased")
        
        # วิเคราะห์ความเพียงพอของข้อมูล
        print(f"\n📈 การวิเคราะห์ความเพียงพอของข้อมูล:")
        
        # คำนวณ samples ต่อ condition
        palmsens_combinations = (
            len(palmsens_conditions.get('concentrations', [])) *
            len(palmsens_conditions.get('scan_rates', [])) *
            len(palmsens_conditions.get('electrodes', []))
        )
        
        stm32_combinations = (
            len(stm32_conditions.get('concentrations', [])) *
            len(stm32_conditions.get('scan_rates', [])) *
            len(stm32_conditions.get('electrodes', []))
        )
        
        palmsens_samples_per_condition = len(palmsens_files) / max(palmsens_combinations, 1)
        stm32_samples_per_condition = len(stm32_files) / max(stm32_combinations, 1)
        
        print(f"   PalmSens: ~{palmsens_samples_per_condition:.1f} samples/condition")
        print(f"   STM32H743: ~{stm32_samples_per_condition:.1f} samples/condition")
        
        # ประเมินความเพียงพอ
        if palmsens_samples_per_condition >= 10 and stm32_samples_per_condition >= 10:
            print(f"   ✅ ข้อมูลเพียงพอสำหรับการฝึก ML models")
        else:
            print(f"   ⚠️  ข้อมูลอาจไม่เพียงพอสำหรับบางเงื่อนไข")
        
        # แนะนำกลยุทธ์การแบ่งแบบ stratified
        print(f"\n🎲 กลยุทธ์การแบ่งข้อมูลแนะนำ:")
        print(f"   1. 📊 Stratified Splitting: แบ่งตาม experimental conditions")
        print(f"   2. 🔄 Cross-Instrument Validation: ใช้ PalmSens ฝึก, STM32 ทดสอบ (และทางกลับ)")
        print(f"   3. 🧪 Cross-Validation: K-fold CV สำหรับแต่ละ instrument")
        print(f"   4. 🌟 Leave-One-Condition-Out: ทดสอบกับเงื่อนไขที่ไม่เคยเห็น")
        
        # แนะนำการใช้งานสำหรับ 3-method comparison
        print(f"\n🏆 สำหรับ 3-Method Peak Detection Comparison:")
        print(f"   🔹 Baseline Detection: ใช้ทุก data (statistical method)")
        print(f"   🔹 Statistical Peak Detection: ใช้ training data สำหรับ parameter tuning")
        print(f"   🔹 ML Peak Detection: ใช้ training/validation/test split แบบเต็ม")
        
        # แนะนำขนาดข้อมูลสำหรับ peak detection
        print(f"\n📏 ความเพียงพอสำหรับ Peak Detection:")
        if total_files > 1000:
            print(f"   ✅ EXCELLENT: {total_files:,} ไฟล์ เพียงพอมากสำหรับ robust validation")
        elif total_files > 500:
            print(f"   ✅ GOOD: {total_files:,} ไฟล์ เพียงพอสำหรับการวิเคราะห์ที่ดี")
        elif total_files > 100:
            print(f"   ⚠️  MODERATE: {total_files:,} ไฟล์ ต้องระวังการ overfitting")
        else:
            print(f"   ❌ INSUFFICIENT: {total_files:,} ไฟล์ น้อยเกินไปสำหรับ ML")
            
        print(f"\n💫 ข้อเสนอแนะเพิ่มเติม:")
        print(f"   • ใช้ data augmentation ถ้าจำเป็น (noise injection, baseline shifting)")
        print(f"   • เก็บข้อมูล edge cases ไว้ใน test set")
        print(f"   • รักษาความสมดุลระหว่าง instruments ใน train/val/test")
        print(f"   • พิจารณา time-based splitting ถ้ามีข้อมูล temporal")

def main():
    analyzer = DataSplittingAnalyzer()
    analyzer.analyze_data_distribution()

if __name__ == "__main__":
    main()
