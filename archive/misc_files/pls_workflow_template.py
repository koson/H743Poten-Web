"""
PLS Workflow Template for CV Data Analysis
==========================================

- เลือกความเข้มข้นและอัตราการสแกน
- สุ่มเลือกข้อมูลที่มี peak ครบทั้ง 2 ด้าน (ใช้ baseline detector V4)
- สร้างตารางข้อมูลและ gap analysis
- สร้างและประเมินผลโมเดล PLS
- Visualization แบบที่นิยมในงานวิจัย
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import glob
import os
from pathlib import Path
from sklearn.cross_decomposition import PLSRegression
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from scipy.signal import find_peaks
from scipy.integrate import trapz

# Import Enhanced Detector V4 (อัลกอริทึมที่ได้ผลเกือบ 100%)
try:
    from enhanced_detector_v4 import EnhancedDetectorV4
    ENHANCED_V4_AVAILABLE = True
    print("✅ Enhanced Detector V4 พร้อมใช้งาน")
except ImportError:
    ENHANCED_V4_AVAILABLE = False
    print("⚠️  Enhanced Detector V4 ไม่พบ - จะใช้ simple baseline detection")

def simple_baseline_detector(voltage, current):
    """Simple baseline detection fallback"""
    n = len(voltage)
    mid = n // 2
    
    # ใช้ส่วนแรกและส่วนสุดท้าย 20% เป็น baseline
    baseline_region_size = n // 5
    
    forward_baseline_value = np.mean(current[:baseline_region_size])
    reverse_baseline_value = np.mean(current[-baseline_region_size:])
    
    forward_baseline = np.full(mid, forward_baseline_value)
    reverse_baseline = np.full(n - mid, reverse_baseline_value)
    
    return forward_baseline, reverse_baseline, {'method': 'simple_fallback'}

class CVPLSWorkflow:
    """
    PLS Workflow ที่ใช้ baseline detector V4 สำหรับการ detect peak ที่แม่นยำ
    """
    
    def __init__(self, palmsens_dir="Test_data/Palmsens", stm32_dir="Test_data/Stm32", output_dir="pls_results"):
        self.palmsens_dir = Path(palmsens_dir)
        self.stm32_dir = Path(stm32_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.results = {
            'data_matrix': [],
            'concentrations': [],
            'scan_rates': [],
            'peak_data': {},
            'missing_combinations': []
        }
    
    def load_cv_file(self, filepath):
        """โหลดไฟล์ CV และ detect peaks ด้วย V4"""
        try:
            # โหลดข้อมูล
            if filepath.suffix == '.csv':
                data = pd.read_csv(filepath)
            elif filepath.suffix == '.json':
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    if 'data' in data:
                        df = pd.DataFrame(data['data'])
                    else:
                        return None
            else:
                return None
            
            # ตรวจสอบ columns ที่จำเป็น
            if 'voltage' not in data.columns or 'current' not in data.columns:
                return None
            
            voltage = data['voltage'].values
            current = data['current'].values
            
            # ใช้ Enhanced Detector V4 หรือ fallback
            if ENHANCED_V4_AVAILABLE:
                detector = EnhancedDetectorV4()
                # ใช้ Enhanced V4 สำหรับการวิเคราะห์ CV ข้อมูล
                results = detector.analyze_cv_data({
                    'voltage': voltage,
                    'current': current
                })
                
                # แยกข้อมูลจากผลลัพธ์
                if 'baseline_data' in results:
                    baseline_info = results['baseline_data']
                    forward_baseline = baseline_info.get('forward_baseline', np.zeros(len(voltage)//2))
                    reverse_baseline = baseline_info.get('reverse_baseline', np.zeros(len(voltage) - len(voltage)//2))
                    info = {'method': 'enhanced_v4', 'confidence': results.get('confidence', 0)}
                else:
                    # fallback ถ้า Enhanced V4 fail
                    forward_baseline, reverse_baseline, info = simple_baseline_detector(voltage, current)
            else:
                forward_baseline, reverse_baseline, info = simple_baseline_detector(voltage, current)
            
            # หา peak หลังจาก subtract baseline
            corrected_current = current - np.concatenate([forward_baseline, reverse_baseline])
            
            # Peak detection
            peaks_pos, _ = find_peaks(corrected_current, height=np.std(corrected_current))
            peaks_neg, _ = find_peaks(-corrected_current, height=np.std(corrected_current))
            
            # คำนวณ peak properties
            peak_heights = []
            peak_areas = []
            
            if len(peaks_pos) > 0:
                anodic_peak_height = np.max(corrected_current[peaks_pos])
                peak_heights.append(anodic_peak_height)
                
                # คำนวณ area รอบ peak
                peak_idx = peaks_pos[np.argmax(corrected_current[peaks_pos])]
                start_idx = max(0, peak_idx - 20)
                end_idx = min(len(corrected_current), peak_idx + 20)
                area = trapz(corrected_current[start_idx:end_idx], voltage[start_idx:end_idx])
                peak_areas.append(area)
            
            if len(peaks_neg) > 0:
                cathodic_peak_height = np.min(corrected_current[peaks_neg])
                peak_heights.append(abs(cathodic_peak_height))
                
                # คำนวณ area รอบ peak
                peak_idx = peaks_neg[np.argmin(corrected_current[peaks_neg])]
                start_idx = max(0, peak_idx - 20)
                end_idx = min(len(corrected_current), peak_idx + 20)
                area = abs(trapz(corrected_current[start_idx:end_idx], voltage[start_idx:end_idx]))
                peak_areas.append(area)
            
            return {
                'voltage': voltage,
                'current': current,
                'corrected_current': corrected_current,
                'baseline_info': info,
                'anodic_peak': peak_heights[0] if len(peak_heights) > 0 else None,
                'cathodic_peak': peak_heights[1] if len(peak_heights) > 1 else None,
                'anodic_area': peak_areas[0] if len(peak_areas) > 0 else None,
                'cathodic_area': peak_areas[1] if len(peak_areas) > 1 else None,
                'has_both_peaks': len(peak_heights) >= 2
            }
            
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return None
    
    def extract_metadata_from_filename(self, filename):
        """แยก concentration และ scan rate จาก filename สำหรับทั้ง Palmsens และ STM32"""
        import re
        
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
        
        # General pattern: ใด ๆ ที่มี mM
        if concentration is None:
            conc_match = re.search(r'(\d+\.?\d*)\s*mm', filename_lower)
            if conc_match:
                concentration = float(conc_match.group(1))
        
        # Pattern สำหรับ scan rate
        scan_rate = None
        
        # รูปแบบต่าง ๆ ของ scan rate: 100mVpS, 100mV/s, 100mVs, etc.
        scan_patterns = [
            r'(\d+\.?\d*)\s*mv[\/\s]*p?s',  # 100mVpS, 100mV/s, 100mVs
            r'(\d+\.?\d*)\s*mv',            # 100mV
            r'(\d+\.?\d*)\s*scan',          # ถ้ามี scan ในชื่อ
        ]
        
        for pattern in scan_patterns:
            scan_match = re.search(pattern, filename_lower)
            if scan_match:
                scan_rate = float(scan_match.group(1))
                break
        
        # Debug info
        if concentration is None or scan_rate is None:
            print(f"⚠️  ไม่สามารถแยกข้อมูลได้: {filename}")
            print(f"   Concentration: {concentration}, Scan Rate: {scan_rate}")
        
        return concentration, scan_rate

    
    def scan_data_files(self):
        """สแกนไฟล์ข้อมูล CV ทั้งหมดจาก Palmsens และ STM32"""
        all_files = []
        
        # สแกนไฟล์ Palmsens (reference potentiostat)
        if self.palmsens_dir.exists():
            palmsens_files = list(self.palmsens_dir.glob("**/*.csv"))
            palmsens_files.extend(list(self.palmsens_dir.glob("**/*.json")))
            for f in palmsens_files:
                all_files.append((f, 'palmsens'))
        
        # สแกนไฟล์ STM32 (target potentiostat) 
        if self.stm32_dir.exists():
            stm32_files = list(self.stm32_dir.glob("**/*.csv"))
            stm32_files.extend(list(self.stm32_dir.glob("**/*.json")))
            for f in stm32_files:
                all_files.append((f, 'stm32'))
        
        print(f"🔍 พบไฟล์ข้อมูล {len(all_files)} ไฟล์")
        print(f"   - Palmsens: {len([f for f, t in all_files if t == 'palmsens'])} ไฟล์")
        print(f"   - STM32: {len([f for f, t in all_files if t == 'stm32'])} ไฟล์")
        
        data_matrix = []
        concentrations = set()
        scan_rates = set()
        
        for filepath, device_type in all_files:
            # แยกข้อมูล metadata
            concentration, scan_rate = self.extract_metadata_from_filename(filepath.name)
            
            if concentration is None or scan_rate is None:
                continue
                
            # โหลดและวิเคราะห์ไฟล์
            cv_data = self.load_cv_file(filepath)
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
                'baseline_method': cv_data.get('baseline_info', {}).get('method', 'unknown'),
                'confidence': cv_data.get('baseline_info', {}).get('confidence', 0)
            }
            
            data_matrix.append(row)
            concentrations.add(concentration)
            scan_rates.add(scan_rate)
        
        self.results['data_matrix'] = data_matrix
        self.results['concentrations'] = sorted(concentrations)
        self.results['scan_rates'] = sorted(scan_rates)
        
        return pd.DataFrame(data_matrix)
    
    def create_data_availability_table(self):
        """สร้างตารางแสดงข้อมูลที่มีและไม่มี"""
        df = pd.DataFrame(self.results['data_matrix'])
        
        # สร้างตาราง concentration vs scan_rate
        availability_table = []
        missing_combinations = []
        
        for conc in self.results['concentrations']:
            for scan in self.results['scan_rates']:
                subset = df[(df['concentration'] == conc) & (df['scan_rate'] == scan)]
                valid_peaks = subset[subset['has_both_peaks'] == True]
                
                if len(valid_peaks) > 0:
                    # มีข้อมูลที่ใช้ได้
                    sample = valid_peaks.iloc[0]  # เลือกตัวแรก หรือจะ random ก็ได้
                    availability_table.append({
                        'concentration': conc,
                        'scan_rate': scan, 
                        'available': True,
                        'filename': sample['filename'],
                        'anodic_peak': sample['anodic_peak'],
                        'cathodic_peak': sample['cathodic_peak']
                    })
                else:
                    # ไม่มีข้อมูลหรือไม่มี peak ครบ
                    missing_combinations.append({
                        'concentration': conc,
                        'scan_rate': scan,
                        'available': False,
                        'reason': 'No data with both peaks'
                    })
                    availability_table.append({
                        'concentration': conc,
                        'scan_rate': scan,
                        'available': False, 
                        'filename': None,
                        'anodic_peak': None,
                        'cathodic_peak': None
                    })
        
        self.results['missing_combinations'] = missing_combinations
        return pd.DataFrame(availability_table)
    
    def perform_pls_analysis(self, df_available):
        """ทำ PLS analysis กับข้อมูลที่มี"""
        # เลือกเฉพาะข้อมูลที่มี peak ครบ
        valid_data = df_available[df_available['available'] == True].copy()
        
        if len(valid_data) < 5:
            print("❌ ข้อมูลไม่เพียงพอสำหรับ PLS analysis (ต้องการอย่างน้อย 5 samples)")
            return None
        
        # เตรียมข้อมูล
        X = valid_data[['anodic_peak', 'cathodic_peak']].values
        y = valid_data['concentration'].values
        
        # Scaling
        scaler_X = StandardScaler()
        scaler_y = StandardScaler()
        
        X_scaled = scaler_X.fit_transform(X)
        y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()
        
        # PLS Model
        pls = PLSRegression(n_components=min(2, X.shape[1]))
        pls.fit(X_scaled, y_scaled)
        
        # Prediction
        y_pred_scaled = pls.predict(X_scaled)
        y_pred = scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).ravel()
        
        # Cross-validation
        cv_scores = cross_val_score(pls, X_scaled, y_scaled, cv=5, scoring='r2')
        
        # Metrics
        r2 = r2_score(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        mae = mean_absolute_error(y, y_pred)
        
        results = {
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
            'cv_std': cv_scores.std()
        }
        
        return results
    
    def create_visualizations(self, pls_results, df_available):
        """สร้างกราฟแสดงผล"""
        if pls_results is None:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. Prediction vs Actual
        ax1 = axes[0, 0]
        y = pls_results['y']
        y_pred = pls_results['y_pred']
        
        ax1.scatter(y, y_pred, alpha=0.7, s=60)
        min_val, max_val = min(y.min(), y_pred.min()), max(y.max(), y_pred.max())
        ax1.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2)
        ax1.set_xlabel('Actual Concentration (mM)')
        ax1.set_ylabel('Predicted Concentration (mM)')
        ax1.set_title(f'PLS Prediction vs Actual\nR² = {pls_results["r2"]:.3f}')
        ax1.grid(True, alpha=0.3)
        
        # 2. Residuals
        ax2 = axes[0, 1]
        residuals = y - y_pred
        ax2.scatter(y_pred, residuals, alpha=0.7)
        ax2.axhline(y=0, color='r', linestyle='--')
        ax2.set_xlabel('Predicted Concentration (mM)')
        ax2.set_ylabel('Residuals')
        ax2.set_title('Residual Plot')
        ax2.grid(True, alpha=0.3)
        
        # 3. PLS Loadings
        ax3 = axes[1, 0]
        loadings = pls_results['model'].x_loadings_[:, 0]
        features = ['Anodic Peak', 'Cathodic Peak']
        bars = ax3.bar(features, loadings)
        ax3.set_ylabel('Loading Value')
        ax3.set_title('PLS X-Loadings (Component 1)')
        ax3.grid(True, alpha=0.3)
        
        # สี bars ตาม sign
        for i, bar in enumerate(bars):
            if loadings[i] >= 0:
                bar.set_color('blue')
            else:
                bar.set_color('red')
        
        # 4. Data availability heatmap
        ax4 = axes[1, 1]
        
        # สร้าง pivot table สำหรับ heatmap
        heatmap_data = df_available.pivot(index='concentration', 
                                        columns='scan_rate', 
                                        values='available')
        
        # แปลง boolean เป็น int
        heatmap_data = heatmap_data.astype(int)
        
        sns.heatmap(heatmap_data, annot=True, cmap='RdYlGn', 
                   cbar_kws={'label': 'Data Available'}, ax=ax4)
        ax4.set_title('Data Availability Matrix')
        ax4.set_xlabel('Scan Rate (mV/s)')
        ax4.set_ylabel('Concentration (mM)')
        
        plt.tight_layout()
        
        # บันทึกรูป
        output_path = self.output_dir / f"pls_analysis_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"💾 บันทึกรูปภาพที่: {output_path}")
        
        plt.show()
        
        return output_path
    
    def run_workflow(self):
        """รัน workflow หลัก"""
        print("🚀 เริ่มต้น PLS Workflow ด้วย Baseline Detector V4")
        print("=" * 50)
        
        # 1. สแกนไฟล์ข้อมูล
        print("\n📂 1. สแกนไฟล์ข้อมูล CV...")
        df_all = self.scan_data_files()
        print(f"   พบข้อมูล: {len(df_all)} ไฟล์")
        
        # 2. สร้างตารางความพร้อมของข้อมูล
        print("\n📊 2. สร้างตารางความพร้อมของข้อมูล...")
        df_availability = self.create_data_availability_table()
        
        available_count = len(df_availability[df_availability['available'] == True])
        total_combinations = len(self.results['concentrations']) * len(self.results['scan_rates'])
        
        print(f"   ✅ มีข้อมูล: {available_count}/{total_combinations} combinations")
        print(f"   ❌ ไม่มีข้อมูล: {total_combinations - available_count} combinations")
        
        # แสดงข้อมูลที่หายไป
        if self.results['missing_combinations']:
            print("\n🔍 ข้อมูลที่หายไป:")
            for missing in self.results['missing_combinations']:
                print(f"   - {missing['concentration']} mM @ {missing['scan_rate']} mV/s")
        
        # 3. ทำ PLS Analysis
        print("\n🧠 3. ทำ PLS Analysis...")
        pls_results = self.perform_pls_analysis(df_availability)
        
        if pls_results:
            print(f"   📈 R² = {pls_results['r2']:.3f}")
            print(f"   📈 RMSE = {pls_results['rmse']:.3f}")
            print(f"   📈 MAE = {pls_results['mae']:.3f}")
            print(f"   📈 CV R² = {pls_results['cv_mean']:.3f} ± {pls_results['cv_std']:.3f}")
        
        # 4. สร้างรูปภาพ
        print("\n📊 4. สร้างการแสดงผล...")
        self.create_visualizations(pls_results, df_availability)
        
        # 5. บันทึกผลลัพธ์
        print("\n💾 5. บันทึกผลลัพธ์...")
        self.save_results(df_availability, pls_results)
        
        print("\n✅ เสร็จสิ้น PLS Workflow!")
        return pls_results, df_availability
    
    def save_results(self, df_availability, pls_results):
        """บันทึกผลลัพธ์"""
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        
        # บันทึก data availability
        availability_path = self.output_dir / f"data_availability_{timestamp}.csv"
        df_availability.to_csv(availability_path, index=False)
        
        # บันทึก summary report
        report_path = self.output_dir / f"pls_report_{timestamp}.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("PLS Analysis Report\n")
            f.write("==================\n\n")
            f.write(f"Analysis Date: {pd.Timestamp.now()}\n")
            f.write(f"Method: Baseline Detector V4\n\n")
            
            f.write("Data Summary:\n")
            f.write(f"- Total concentrations: {len(self.results['concentrations'])}\n")
            f.write(f"- Total scan rates: {len(self.results['scan_rates'])}\n")
            f.write(f"- Available combinations: {len(df_availability[df_availability['available']])}\n")
            f.write(f"- Missing combinations: {len(self.results['missing_combinations'])}\n\n")
            
            if pls_results:
                f.write("PLS Results:\n")
                f.write(f"- R² = {pls_results['r2']:.3f}\n")
                f.write(f"- RMSE = {pls_results['rmse']:.3f}\n") 
                f.write(f"- MAE = {pls_results['mae']:.3f}\n")
                f.write(f"- CV R² = {pls_results['cv_mean']:.3f} ± {pls_results['cv_std']:.3f}\n")
        
        print(f"   💾 Data availability: {availability_path}")
        print(f"   💾 Report: {report_path}")


# วิธีการรัน
if __name__ == "__main__":
    # ใช้ path ที่ถูกต้องสำหรับข้อมูล Reference (Palmsens) และ Target (STM32)
    workflow = CVPLSWorkflow(
        palmsens_dir="Test_data/Palmsens",    # Reference potentiostat
        stm32_dir="Test_data/Stm32",          # Target potentiostat  
        output_dir="pls_results"
    )
    
    # รัน workflow
    pls_results, df_availability = workflow.run_workflow()
    
    if pls_results:
        print("\n🎉 PLS Analysis สำเร็จ!")
        print(f"   R² = {pls_results['r2']:.3f}")
        print(f"   RMSE = {pls_results['rmse']:.3f} mM")
        print(f"   MAE = {pls_results['mae']:.3f} mM")
    else:
        print("\n❌ PLS Analysis ไม่สำเร็จ - ข้อมูลไม่เพียงพอ")
