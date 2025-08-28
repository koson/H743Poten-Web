#!/usr/bin/env python3
"""
PLS Workflow Basic - ใช้ simple peak detection และ PLS analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import re
from datetime import datetime
from sklearn.cross_decomposition import PLSRegression
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from scipy.signal import find_peaks
from scipy.integrate import trapz

class PLSWorkflowBasic:
    """PLS Workflow ที่ใช้ simple peak detection"""
    
    def __init__(self, palmsens_dir="Test_data/Palmsens", output_dir="pls_results_basic"):
        self.palmsens_dir = Path(palmsens_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def extract_metadata_from_filename(self, filename):
        """แยก concentration และ scan rate จาก filename"""
        filename_lower = filename.lower()
        
        # Concentration
        conc_match = re.search(r'palmsens[_\s]*(\d+\.?\d*)\s*mm', filename_lower)
        concentration = float(conc_match.group(1)) if conc_match else None
        
        # Scan rate
        scan_match = re.search(r'(\d+\.?\d*)\s*mv[\/\s]*p?s', filename_lower)
        scan_rate = float(scan_match.group(1)) if scan_match else None
        
        return concentration, scan_rate
    
    def simple_peak_detection(self, voltage, current):
        """Simple peak detection"""
        try:
            # หา peaks
            pos_peaks, _ = find_peaks(current, height=np.std(current)*0.5)
            neg_peaks, _ = find_peaks(-current, height=np.std(current)*0.5)
            
            # Peak heights
            anodic_peak = np.max(current[pos_peaks]) if len(pos_peaks) > 0 else None
            cathodic_peak = abs(np.min(current[neg_peaks])) if len(neg_peaks) > 0 else None
            
            # Peak areas (simple approximation)
            anodic_area = None
            cathodic_area = None
            
            if len(pos_peaks) > 0:
                peak_idx = pos_peaks[np.argmax(current[pos_peaks])]
                start_idx = max(0, peak_idx - 10)
                end_idx = min(len(current), peak_idx + 10)
                anodic_area = trapz(current[start_idx:end_idx], voltage[start_idx:end_idx])
            
            if len(neg_peaks) > 0:
                peak_idx = neg_peaks[np.argmin(current[neg_peaks])]
                start_idx = max(0, peak_idx - 10)
                end_idx = min(len(current), peak_idx + 10)
                cathodic_area = abs(trapz(current[start_idx:end_idx], voltage[start_idx:end_idx]))
            
            has_both_peaks = (anodic_peak is not None and cathodic_peak is not None)
            
            return {
                'anodic_peak': anodic_peak,
                'cathodic_peak': cathodic_peak,
                'anodic_area': anodic_area,
                'cathodic_area': cathodic_area,
                'has_both_peaks': has_both_peaks
            }
            
        except Exception as e:
            print(f"Error in peak detection: {e}")
            return {
                'anodic_peak': None,
                'cathodic_peak': None,
                'anodic_area': None,
                'cathodic_area': None,
                'has_both_peaks': False
            }
    
    def load_cv_file(self, filepath):
        """โหลดไฟล์ CV"""
        try:
            # อ่านไฟล์ (skip 2 บรรทัดแรก)
            data = pd.read_csv(filepath, skiprows=2, names=['voltage', 'current'])
            
            if len(data) == 0:
                return None
            
            voltage = data['voltage'].values
            current = data['current'].values
            
            # Simple peak detection
            peak_results = self.simple_peak_detection(voltage, current)
            
            return peak_results
            
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return None
    
    def scan_data_files(self, max_files_per_combination=2):
        """สแกนไฟล์ข้อมูล"""
        if not self.palmsens_dir.exists():
            print("❌ ไม่พบโฟลเดอร์ Palmsens")
            return pd.DataFrame()
        
        data_matrix = []
        concentrations = set()
        scan_rates = set()
        combination_counts = {}
        
        print(f"🔍 สแกนข้อมูล Palmsens...")
        
        for conc_folder in self.palmsens_dir.iterdir():
            if not conc_folder.is_dir():
                continue
            
            csv_files = list(conc_folder.glob("*.csv"))
            print(f"📂 {conc_folder.name}: {len(csv_files)} ไฟล์")
            
            for csv_file in csv_files:
                concentration, scan_rate = self.extract_metadata_from_filename(csv_file.name)
                
                if concentration is None or scan_rate is None:
                    continue
                
                # จำกัดจำนวนไฟล์ต่อ combination
                combo_key = (concentration, scan_rate)
                if combo_key not in combination_counts:
                    combination_counts[combo_key] = 0
                
                if combination_counts[combo_key] >= max_files_per_combination:
                    continue
                
                combination_counts[combo_key] += 1
                
                # โหลดและวิเคราะห์ไฟล์
                cv_data = self.load_cv_file(csv_file)
                if cv_data is None:
                    continue
                
                # เก็บข้อมูล
                row = {
                    'filename': csv_file.name,
                    'concentration': concentration,
                    'scan_rate': scan_rate,
                    'anodic_peak': cv_data['anodic_peak'],
                    'cathodic_peak': cv_data['cathodic_peak'],
                    'anodic_area': cv_data['anodic_area'],
                    'cathodic_area': cv_data['cathodic_area'],
                    'has_both_peaks': cv_data['has_both_peaks']
                }
                
                data_matrix.append(row)
                concentrations.add(concentration)
                scan_rates.add(scan_rate)
                
                if cv_data['has_both_peaks']:
                    print(f"   ✅ {csv_file.name}: {concentration}mM @ {scan_rate}mV/s")
                else:
                    print(f"   ⚠️  {csv_file.name}: {concentration}mM @ {scan_rate}mV/s (ไม่มี peak ครบ)")
        
        print(f"\n📊 สรุป:")
        print(f"   🧪 Concentrations: {sorted(concentrations)} mM")
        print(f"   ⚡ Scan rates: {sorted(scan_rates)} mV/s")
        print(f"   📁 ไฟล์ที่ประมวลผล: {len(data_matrix)} ไฟล์")
        
        return pd.DataFrame(data_matrix)
    
    def perform_pls_analysis(self, df):
        """ทำ PLS analysis"""
        # เลือกเฉพาะข้อมูลที่มี peak ครบ
        valid_data = df[df['has_both_peaks'] == True].copy()
        
        if len(valid_data) < 5:
            print(f"❌ ข้อมูลไม่เพียงพอสำหรับ PLS analysis (มี {len(valid_data)} samples, ต้องการอย่างน้อย 5)")
            return None
        
        print(f"🧠 ทำ PLS Analysis ({len(valid_data)} samples)...")
        
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
        cv_scores = cross_val_score(pls, X_scaled, y_scaled, cv=cv_folds, scoring='r2')
        
        # Metrics
        r2 = r2_score(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        mae = mean_absolute_error(y, y_pred)
        
        print(f"   📈 R² = {r2:.3f}")
        print(f"   📈 RMSE = {rmse:.3f} mM")
        print(f"   📈 CV R² = {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        return {
            'model': pls,
            'X': X,
            'y': y,
            'y_pred': y_pred,
            'r2': r2,
            'rmse': rmse,
            'mae': mae,
            'cv_scores': cv_scores,
            'valid_data': valid_data
        }
    
    def create_visualization(self, pls_results):
        """สร้างกราฟ"""
        if pls_results is None:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        y = pls_results['y']
        y_pred = pls_results['y_pred']
        
        # 1. Prediction vs Actual
        ax1 = axes[0, 0]
        ax1.scatter(y, y_pred, alpha=0.7, s=60, color='blue')
        min_val, max_val = min(y.min(), y_pred.min()), max(y.max(), y_pred.max())
        ax1.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2)
        ax1.set_xlabel('Actual Concentration (mM)')
        ax1.set_ylabel('Predicted Concentration (mM)')
        ax1.set_title(f'PLS Prediction vs Actual\nR² = {pls_results["r2"]:.3f}')
        ax1.grid(True, alpha=0.3)
        
        # 2. Residuals
        ax2 = axes[0, 1]
        residuals = y - y_pred
        ax2.scatter(y_pred, residuals, alpha=0.7, color='green')
        ax2.axhline(y=0, color='r', linestyle='--')
        ax2.set_xlabel('Predicted Concentration (mM)')
        ax2.set_ylabel('Residuals')
        ax2.set_title('Residual Plot')
        ax2.grid(True, alpha=0.3)
        
        # 3. PLS Loadings
        ax3 = axes[1, 0]
        loadings = pls_results['model'].x_loadings_[:, 0]
        features = ['Anodic Peak', 'Cathodic Peak']
        bars = ax3.bar(features, loadings, color=['blue' if l >= 0 else 'red' for l in loadings])
        ax3.set_ylabel('Loading Value')
        ax3.set_title('PLS X-Loadings (Component 1)')
        ax3.grid(True, alpha=0.3)
        
        # 4. CV Scores
        ax4 = axes[1, 1]
        cv_scores = pls_results['cv_scores']
        ax4.bar(range(len(cv_scores)), cv_scores, color='purple', alpha=0.7)
        ax4.set_xlabel('CV Fold')
        ax4.set_ylabel('R² Score')
        ax4.set_title(f'Cross-Validation Scores\nMean = {cv_scores.mean():.3f}')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # บันทึกรูป
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = self.output_dir / f"pls_analysis_basic_{timestamp}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"💾 บันทึกรูปภาพที่: {output_path}")
        
        plt.show()
    
    def run_workflow(self):
        """รัน workflow หลัก"""
        print("🚀 เริ่มต้น PLS Workflow Basic")
        print("=" * 40)
        
        # 1. สแกนไฟล์ข้อมูล
        df_all = self.scan_data_files()
        
        if len(df_all) == 0:
            print("❌ ไม่พบข้อมูล")
            return None
        
        # 2. ทำ PLS Analysis
        pls_results = self.perform_pls_analysis(df_all)
        
        # 3. สร้างรูปภาพ
        if pls_results:
            print("\n📊 สร้างการแสดงผล...")
            self.create_visualization(pls_results)
        
        print("\n✅ เสร็จสิ้น!")
        return pls_results

if __name__ == "__main__":
    workflow = PLSWorkflowBasic()
    result = workflow.run_workflow()
