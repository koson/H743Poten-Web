#!/usr/bin/env python3
"""
PLS Workflow with Enhanced Detector V4 Improved
===============================================
ใช้ Enhanced Detector V4 Improved สำหรับการ detect peak และ baseline ที่มีการปรับปรุง
reduction peak detection และ edge effect elimination
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import re
import json
import logging
from datetime import datetime
from sklearn.cross_decomposition import PLSRegression
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# Import Enhanced Detector V4 Improved
try:
    from enhanced_detector_v4_improved import EnhancedDetectorV4Improved
    ENHANCED_V4_IMPROVED_AVAILABLE = True
    print("✅ Enhanced Detector V4 Improved พร้อมใช้งาน")
except ImportError:
    ENHANCED_V4_IMPROVED_AVAILABLE = False
    print("❌ Enhanced Detector V4 Improved ไม่พบ")
    exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class PLSWorkflowV4Improved:
    """
    PLS Workflow ที่ใช้ Enhanced Detector V4 Improved
    """
    
    def __init__(self, palmsens_dir="Test_data/Palmsens", stm32_dir="Test_data/Stm32", output_dir="pls_results_v4_improved"):
        self.palmsens_dir = Path(palmsens_dir)
        self.stm32_dir = Path(stm32_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize Enhanced Detector V4 Improved with lower threshold
        self.detector = EnhancedDetectorV4Improved(confidence_threshold=25.0)
        
        self.results = {
            'data_matrix': [],
            'concentrations': [],
            'scan_rates': [],
            'peak_data': {},
            'missing_combinations': [],
            'detection_stats': {
                'total_files': 0,
                'successful_detections': 0,
                'failed_detections': 0,
                'high_confidence_detections': 0,
                'medium_confidence_detections': 0,
                'low_confidence_detections': 0
            }
        }
    
    def extract_metadata_from_filename(self, filename):
        """แยก concentration และ scan rate จาก filename"""
        filename_lower = filename.lower()
        
        # Pattern สำหรับ concentration
        concentration = None
        
        # Palmsens format: Palmsens_0.5mM_...
        conc_match = re.search(r'palmsens[_\s]*(\d+\.?\d*)\s*mm', filename_lower)
        if conc_match:
            concentration = float(conc_match.group(1))
        
        # STM32 format: Pipot_Ferro_0_5mM_... หรือ Pipot_Ferro_1_0mM_...
        if concentration is None:
            conc_match = re.search(r'pipot[_\s]*ferro[_\s]*(\d+)[_\s]*(\d+)[_\s]*mm', filename_lower)
            if conc_match:
                major = int(conc_match.group(1))
                minor = int(conc_match.group(2))
                concentration = major + minor / 10.0
        
        # Pattern สำหรับ scan rate
        scan_rate = None
        scan_match = re.search(r'(\d+\.?\d*)\s*mv[\/\s]*p?s', filename_lower)
        if scan_match:
            scan_rate = float(scan_match.group(1))
        
        return concentration, scan_rate
    
    def load_cv_file(self, filepath, device_type):
        """โหลดไฟล์ CV และวิเคราะห์ด้วย Enhanced Detector V4 Improved"""
        try:
            self.results['detection_stats']['total_files'] += 1
            
            # โหลดข้อมูล - skip 2 บรรทัดแรก (ชื่อไฟล์ + header)
            if device_type == 'palmsens':
                data = pd.read_csv(filepath, skiprows=2, names=['voltage', 'current'])
            else:
                data = pd.read_csv(filepath, skiprows=2, names=['voltage', 'current'])
            
            # ตรวจสอบข้อมูล
            if len(data) == 0:
                logger.warning(f"   ❌ ไฟล์ว่าง: {filepath.name}")
                self.results['detection_stats']['failed_detections'] += 1
                return None
            
            voltage = data['voltage'].values
            current = data['current'].values
            
            # ตรวจสอบว่าข้อมูลเป็นตัวเลข
            if not (np.isfinite(voltage).all() and np.isfinite(current).all()):
                logger.warning(f"   ❌ ข้อมูลไม่ถูกต้อง: {filepath.name}")
                self.results['detection_stats']['failed_detections'] += 1
                return None
            
            # ใช้ Enhanced Detector V4 Improved วิเคราะห์
            logger.info(f"🔬 วิเคราะห์ {filepath.name} ด้วย Enhanced Detector V4 Improved...")
            
            # สร้าง data structure ที่ Enhanced V4 Improved ต้องการ
            cv_data_dict = {
                'voltage': voltage,
                'current': current
            }
            
            # รัน Enhanced Detector V4 Improved
            results = self.detector.analyze_cv_data(cv_data_dict)
            
            # ตรวจสอบผลลัพธ์
            if results and 'confidence' in results:
                confidence = results.get('confidence', 0)
                
                # แยกข้อมูล peaks
                peak_data = results.get('peak_data', {})
                oxidation_peak = peak_data.get('oxidation_peak')
                reduction_peak = peak_data.get('reduction_peak')
                
                # ข้อมูล baseline
                baseline_data = results.get('baseline_data', {})
                
                # Peak heights และ areas
                ox_height = oxidation_peak.get('height') if oxidation_peak else None
                red_height = abs(reduction_peak.get('height')) if reduction_peak else None
                
                ox_area = oxidation_peak.get('area') if oxidation_peak else None
                red_area = abs(reduction_peak.get('area')) if reduction_peak else None
                
                # ตรวจสอบว่ามี peak ครบทั้ง 2 หรือไม่
                has_both_peaks = (ox_height is not None and red_height is not None and 
                                ox_area is not None and red_area is not None)
                
                # จำแนกระดับ confidence
                if confidence >= 75:
                    self.results['detection_stats']['high_confidence_detections'] += 1
                elif confidence >= 50:
                    self.results['detection_stats']['medium_confidence_detections'] += 1
                else:
                    self.results['detection_stats']['low_confidence_detections'] += 1
                
                if has_both_peaks:
                    self.results['detection_stats']['successful_detections'] += 1
                    status_icon = "✅"
                else:
                    self.results['detection_stats']['failed_detections'] += 1
                    status_icon = "⚠️"
                
                logger.info(f"   {status_icon} Confidence: {confidence:.1f}%, Peaks: {'✅' if has_both_peaks else '❌'}")
                
                return {
                    'voltage': voltage,
                    'current': current,
                    'enhanced_v4_improved_results': results,
                    'confidence': confidence,
                    'anodic_peak': ox_height,
                    'cathodic_peak': red_height,
                    'anodic_area': ox_area,
                    'cathodic_area': red_area,
                    'has_both_peaks': has_both_peaks,
                    'peak_data': peak_data,
                    'baseline_data': baseline_data
                }
            else:
                logger.warning(f"   ❌ Enhanced V4 Improved ไม่สามารถวิเคราะห์ได้")
                self.results['detection_stats']['failed_detections'] += 1
                return None
                
        except Exception as e:
            logger.error(f"❌ Error loading {filepath}: {e}")
            self.results['detection_stats']['failed_detections'] += 1
            return None
    
    def scan_data_files(self, max_files_per_combination=3):
        """สแกนไฟล์ข้อมูล CV ทั้งหมดจาก Palmsens และ STM32"""
        all_files = []
        
        # สแกนไฟล์ Palmsens
        if self.palmsens_dir.exists():
            for conc_folder in self.palmsens_dir.iterdir():
                if conc_folder.is_dir():
                    csv_files = list(conc_folder.glob("*.csv"))
                    for f in csv_files:
                        all_files.append((f, 'palmsens'))
        
        # สแกนไฟล์ STM32
        if self.stm32_dir.exists():
            for conc_folder in self.stm32_dir.iterdir():
                if conc_folder.is_dir():
                    csv_files = list(conc_folder.glob("*.csv"))
                    for f in csv_files:
                        all_files.append((f, 'stm32'))
        
        print(f"🔍 พบไฟล์ข้อมูล {len(all_files)} ไฟล์")
        print(f"   - Palmsens: {len([f for f, t in all_files if t == 'palmsens'])} ไฟล์")
        print(f"   - STM32: {len([f for f, t in all_files if t == 'stm32'])} ไฟล์")
        
        data_matrix = []
        concentrations = set()
        scan_rates = set()
        combination_counts = {}
        
        for filepath, device_type in all_files:
            # แยกข้อมูล metadata
            concentration, scan_rate = self.extract_metadata_from_filename(filepath.name)
            
            if concentration is None or scan_rate is None:
                continue
            
            # จำกัดจำนวนไฟล์ต่อ combination
            combo_key = (concentration, scan_rate, device_type)
            if combo_key not in combination_counts:
                combination_counts[combo_key] = 0
            
            if combination_counts[combo_key] >= max_files_per_combination:
                continue
            
            combination_counts[combo_key] += 1
            
            # โหลดและวิเคราะห์ไฟล์
            cv_data = self.load_cv_file(filepath, device_type)
            if cv_data is None:
                continue
            
            # เก็บข้อมูล
            row = {
                'filename': filepath.name,
                'filepath': str(filepath),
                'device_type': device_type,
                'concentration': concentration,
                'scan_rate': scan_rate,
                'anodic_peak': cv_data['anodic_peak'],
                'cathodic_peak': cv_data['cathodic_peak'], 
                'anodic_area': cv_data['anodic_area'],
                'cathodic_area': cv_data['cathodic_area'],
                'has_both_peaks': cv_data['has_both_peaks'],
                'confidence': cv_data['confidence'],
                'enhanced_v4_improved_results': cv_data['enhanced_v4_improved_results']
            }
            
            data_matrix.append(row)
            concentrations.add(concentration)
            scan_rates.add(scan_rate)
        
        self.results['data_matrix'] = data_matrix
        self.results['concentrations'] = sorted(concentrations)
        self.results['scan_rates'] = sorted(scan_rates)
        
        return pd.DataFrame(data_matrix)
    
    def print_detection_stats(self):
        """แสดงสถิติการ detect ของ Enhanced V4 Improved"""
        stats = self.results['detection_stats']
        
        if stats['total_files'] == 0:
            print("❌ ไม่มีไฟล์ที่ประมวลผล")
            return
        
        print(f"\n📊 สถิติการ detect ด้วย Enhanced Detector V4 Improved:")
        print(f"   📁 ไฟล์ทั้งหมด: {stats['total_files']}")
        print(f"   ✅ Detect สำเร็จ: {stats['successful_detections']} ({stats['successful_detections']/stats['total_files']*100:.1f}%)")
        print(f"   ❌ Detect ไม่สำเร็จ: {stats['failed_detections']} ({stats['failed_detections']/stats['total_files']*100:.1f}%)")
        print(f"   🎯 Confidence สูง (≥75%): {stats['high_confidence_detections']} ({stats['high_confidence_detections']/stats['total_files']*100:.1f}%)")
        print(f"   🔶 Confidence กลาง (50-75%): {stats['medium_confidence_detections']} ({stats['medium_confidence_detections']/stats['total_files']*100:.1f}%)")
        print(f"   🔸 Confidence ต่ำ (25-50%): {stats['low_confidence_detections']} ({stats['low_confidence_detections']/stats['total_files']*100:.1f}%)")
    
    def create_data_availability_table(self, df_all):
        """สร้างตารางแสดงข้อมูลที่มีและไม่มี"""
        
        availability_table = []
        missing_combinations = []
        
        for device in ['palmsens', 'stm32']:
            device_data = df_all[df_all['device_type'] == device]
            
            for conc in self.results['concentrations']:
                for scan in self.results['scan_rates']:
                    subset = device_data[(device_data['concentration'] == conc) & 
                                       (device_data['scan_rate'] == scan)]
                    valid_peaks = subset[subset['has_both_peaks'] == True]
                    
                    if len(valid_peaks) > 0:
                        # เลือกตัวที่มี confidence สูงสุด
                        best_sample = valid_peaks.loc[valid_peaks['confidence'].idxmax()]
                        availability_table.append({
                            'device_type': device,
                            'concentration': conc,
                            'scan_rate': scan, 
                            'available': True,
                            'filename': best_sample['filename'],
                            'confidence': best_sample['confidence'],
                            'anodic_peak': best_sample['anodic_peak'],
                            'cathodic_peak': best_sample['cathodic_peak']
                        })
                    else:
                        missing_combinations.append({
                            'device_type': device,
                            'concentration': conc,
                            'scan_rate': scan,
                            'available': False,
                            'reason': 'No data with both peaks'
                        })
                        availability_table.append({
                            'device_type': device,
                            'concentration': conc,
                            'scan_rate': scan,
                            'available': False, 
                            'filename': None,
                            'confidence': 0,
                            'anodic_peak': None,
                            'cathodic_peak': None
                        })
        
        self.results['missing_combinations'] = missing_combinations
        return pd.DataFrame(availability_table)
    
    def perform_pls_analysis(self, df_availability, device_type='palmsens', min_confidence=25.0):
        """ทำ PLS analysis กับข้อมูลที่มี"""
        # เลือกเฉพาะข้อมูลที่มี peak ครบและ confidence เพียงพอ
        valid_data = df_availability[
            (df_availability['available'] == True) & 
            (df_availability['device_type'] == device_type) &
            (df_availability['confidence'] >= min_confidence)
        ].copy()
        
        if len(valid_data) < 3:
            print(f"❌ ข้อมูล {device_type} ไม่เพียงพอสำหรับ PLS analysis (มี {len(valid_data)} samples, ต้องการอย่างน้อย 3)")
            return None
        
        print(f"🧠 ทำ PLS Analysis สำหรับ {device_type} ({len(valid_data)} samples, min confidence: {min_confidence}%)...")
        
        # เตรียมข้อมูล
        X = valid_data[['anodic_peak', 'cathodic_peak']].values
        y = valid_data['concentration'].values
        
        # ตรวจสอบข้อมูล
        if np.any(np.isnan(X)) or np.any(np.isnan(y)):
            print("❌ พบข้อมูล NaN")
            return None
        
        # Scaling
        scaler_X = StandardScaler()
        scaler_y = StandardScaler()
        
        X_scaled = scaler_X.fit_transform(X)
        y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()
        
        # PLS Model
        n_components = min(2, X.shape[1], len(y) - 1)
        pls = PLSRegression(n_components=n_components)
        pls.fit(X_scaled, y_scaled)
        
        # Prediction
        y_pred_scaled = pls.predict(X_scaled)
        y_pred = scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).ravel()
        
        # Cross-validation
        cv_folds = min(5, len(y))
        if cv_folds >= 2:
            cv_scores = cross_val_score(pls, X_scaled, y_scaled, cv=cv_folds, scoring='r2')
        else:
            cv_scores = np.array([0])
        
        # Metrics
        r2 = r2_score(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        mae = mean_absolute_error(y, y_pred)
        
        results = {
            'device_type': device_type,
            'model': pls,
            'scaler_X': scaler_X,
            'scaler_y': scaler_y,
            'X': X,
            'y': y,
            'y_pred': y_pred,
            'r2': r2,
            'rmse': rmse,
            'mae': mae,
            'cv_scores': cv_scores,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'n_samples': len(valid_data),
            'n_components': n_components,
            'min_confidence': min_confidence,
            'avg_confidence': valid_data['confidence'].mean()
        }
        
        return results
    
    def run_workflow(self):
        """รัน workflow หลัก"""
        print("🚀 เริ่มต้น PLS Workflow ด้วย Enhanced Detector V4 Improved")
        print("=" * 65)
        
        # 1. สแกนไฟล์ข้อมูล
        print("\n📂 1. สแกนไฟล์ข้อมูล CV...")
        df_all = self.scan_data_files(max_files_per_combination=2)
        print(f"   พบข้อมูล: {len(df_all)} ไฟล์")
        
        # แสดงสถิติการ detect
        self.print_detection_stats()
        
        # 2. สร้างตารางความพร้อมของข้อมูล
        print("\n📊 2. สร้างตารางความพร้อมของข้อมูล...")
        df_availability = self.create_data_availability_table(df_all)
        
        # 3. ทำ PLS Analysis สำหรับทั้ง Palmsens และ STM32
        print("\n🧠 3. ทำ PLS Analysis...")
        
        pls_palmsens = self.perform_pls_analysis(df_availability, 'palmsens', min_confidence=25.0)
        pls_stm32 = self.perform_pls_analysis(df_availability, 'stm32', min_confidence=25.0)
        
        # แสดงผลลัพธ์
        if pls_palmsens:
            print(f"\n📈 Palmsens Results ({pls_palmsens['n_samples']} samples, avg confidence: {pls_palmsens['avg_confidence']:.1f}%):")
            print(f"   R² = {pls_palmsens['r2']:.3f}")
            print(f"   RMSE = {pls_palmsens['rmse']:.3f} mM")
            if pls_palmsens['cv_scores'].size > 1:
                print(f"   CV R² = {pls_palmsens['cv_mean']:.3f} ± {pls_palmsens['cv_std']:.3f}")
        
        if pls_stm32:
            print(f"\n📈 STM32 Results ({pls_stm32['n_samples']} samples, avg confidence: {pls_stm32['avg_confidence']:.1f}%):")
            print(f"   R² = {pls_stm32['r2']:.3f}")
            print(f"   RMSE = {pls_stm32['rmse']:.3f} mM")
            if pls_stm32['cv_scores'].size > 1:
                print(f"   CV R² = {pls_stm32['cv_mean']:.3f} ± {pls_stm32['cv_std']:.3f}")
        
        # 4. สร้างรูปภาพ
        if pls_palmsens or pls_stm32:
            print("\n📊 4. สร้างการแสดงผล...")
            self.create_visualizations(pls_palmsens, pls_stm32, df_availability)
        
        # 5. บันทึกผลลัพธ์
        print("\n💾 5. บันทึกผลลัพธ์...")
        self.save_results(df_availability, pls_palmsens, pls_stm32)
        
        print("\n✅ เสร็จสิ้น PLS Workflow ด้วย Enhanced Detector V4 Improved!")
        return pls_palmsens, pls_stm32, df_availability
    
    def create_visualizations(self, pls_palmsens, pls_stm32, df_availability):
        """สร้างกราฟแสดงผล"""
        # Implementation similar to previous version but for V4 Improved
        print("📊 Creating visualization plots...")
        
        # Create simple plot for now
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        
        if pls_palmsens:
            y = pls_palmsens['y']
            y_pred = pls_palmsens['y_pred']
            ax.scatter(y, y_pred, alpha=0.7, s=60, color='blue', label='Palmsens')
            
        if pls_stm32:
            y = pls_stm32['y']
            y_pred = pls_stm32['y_pred']
            ax.scatter(y, y_pred, alpha=0.7, s=60, color='red', label='STM32')
        
        # Perfect prediction line
        if pls_palmsens or pls_stm32:
            all_y = []
            all_y_pred = []
            if pls_palmsens:
                all_y.extend(pls_palmsens['y'])
                all_y_pred.extend(pls_palmsens['y_pred'])
            if pls_stm32:
                all_y.extend(pls_stm32['y'])
                all_y_pred.extend(pls_stm32['y_pred'])
            
            min_val = min(min(all_y), min(all_y_pred))
            max_val = max(max(all_y), max(all_y_pred))
            ax.plot([min_val, max_val], [min_val, max_val], 'k--', lw=2, label='Perfect Prediction')
        
        ax.set_xlabel('Actual Concentration (mM)')
        ax.set_ylabel('Predicted Concentration (mM)')
        ax.set_title('PLS Analysis - Enhanced Detector V4 Improved')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # บันทึกรูป
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = self.output_dir / f"pls_analysis_v4_improved_{timestamp}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"💾 บันทึกรูปภาพที่: {output_path}")
        
        plt.show()
    
    def save_results(self, df_availability, pls_palmsens, pls_stm32):
        """บันทึกผลลัพธ์"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # บันทึก data availability
        availability_path = self.output_dir / f"data_availability_v4_improved_{timestamp}.csv"
        df_availability.to_csv(availability_path, index=False)
        
        # บันทึก summary report
        report_path = self.output_dir / f"pls_report_v4_improved_{timestamp}.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("PLS Analysis Report - Enhanced Detector V4 Improved\n")
            f.write("==================================================\n\n")
            f.write(f"Analysis Date: {datetime.now()}\n")
            f.write(f"Method: Enhanced Detector V4 Improved\n\n")
            
            # Detection stats
            stats = self.results['detection_stats']
            f.write("Detection Statistics:\n")
            f.write(f"- Total files processed: {stats['total_files']}\n")
            f.write(f"- Successful detections: {stats['successful_detections']} ({stats['successful_detections']/stats['total_files']*100:.1f}%)\n")
            f.write(f"- High confidence detections: {stats['high_confidence_detections']} ({stats['high_confidence_detections']/stats['total_files']*100:.1f}%)\n")
            f.write(f"- Medium confidence detections: {stats['medium_confidence_detections']} ({stats['medium_confidence_detections']/stats['total_files']*100:.1f}%)\n")
            f.write(f"- Low confidence detections: {stats['low_confidence_detections']} ({stats['low_confidence_detections']/stats['total_files']*100:.1f}%)\n\n")
            
            if pls_palmsens:
                f.write("Palmsens PLS Results:\n")
                f.write(f"- R² = {pls_palmsens['r2']:.3f}\n")
                f.write(f"- RMSE = {pls_palmsens['rmse']:.3f} mM\n")
                f.write(f"- Average Confidence = {pls_palmsens['avg_confidence']:.1f}%\n")
                f.write(f"- Samples used = {pls_palmsens['n_samples']}\n\n")
            
            if pls_stm32:
                f.write("STM32 PLS Results:\n")
                f.write(f"- R² = {pls_stm32['r2']:.3f}\n")
                f.write(f"- RMSE = {pls_stm32['rmse']:.3f} mM\n")
                f.write(f"- Average Confidence = {pls_stm32['avg_confidence']:.1f}%\n")
                f.write(f"- Samples used = {pls_stm32['n_samples']}\n\n")
        
        print(f"   💾 Data availability: {availability_path}")
        print(f"   💾 Report: {report_path}")


# วิธีการรัน
if __name__ == "__main__":
    if not ENHANCED_V4_IMPROVED_AVAILABLE:
        print("❌ Enhanced Detector V4 Improved ไม่พร้อมใช้งาน")
        exit(1)
    
    # สร้าง workflow
    workflow = PLSWorkflowV4Improved(
        palmsens_dir="Test_data/Palmsens",    # Reference potentiostat
        stm32_dir="Test_data/Stm32",          # Target potentiostat  
        output_dir="pls_results_v4_improved"
    )
    
    # รัน workflow
    pls_palmsens, pls_stm32, df_availability = workflow.run_workflow()
    
    # สรุปผลลัพธ์
    if pls_palmsens or pls_stm32:
        print("\n🎉 PLS Analysis สำเร็จ!")
        if pls_palmsens:
            print(f"   Palmsens: R² = {pls_palmsens['r2']:.3f} (Confidence: {pls_palmsens['avg_confidence']:.1f}%)")
        if pls_stm32:
            print(f"   STM32: R² = {pls_stm32['r2']:.3f} (Confidence: {pls_stm32['avg_confidence']:.1f}%)")
    else:
        print("\n❌ PLS Analysis ไม่สำเร็จ - ข้อมูลไม่เพียงพอ")
