#!/usr/bin/env python3
"""
PLS Workflow V4 Improved - Quick Test
=====================================
เวอร์ชันทดสอบเร็วที่ใช้ข้อมูลน้อยกว่า
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re
from datetime import datetime
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error

# Import Enhanced Detector V4 Improved
try:
    from enhanced_detector_v4_improved import EnhancedDetectorV4Improved
    print("✅ Enhanced Detector V4 Improved พร้อมใช้งาน")
except ImportError:
    print("❌ Enhanced Detector V4 Improved ไม่พบ")
    exit(1)

def extract_metadata_from_filename(filename):
    """แยก concentration และ scan rate"""
    filename_lower = filename.lower()
    
    # Concentration
    conc_match = re.search(r'palmsens[_\s]*(\d+\.?\d*)\s*mm', filename_lower)
    concentration = float(conc_match.group(1)) if conc_match else None
    
    # Scan rate
    scan_match = re.search(r'(\d+\.?\d*)\s*mv[\/\s]*p?s', filename_lower)
    scan_rate = float(scan_match.group(1)) if scan_match else None
    
    return concentration, scan_rate

def analyze_single_file(filepath, detector):
    """วิเคราะห์ไฟล์เดียวด้วย Enhanced V4 Improved"""
    try:
        # โหลดข้อมูล
        data = pd.read_csv(filepath, skiprows=2, names=['voltage', 'current'])
        
        if len(data) == 0:
            return None
        
        voltage = data['voltage'].values
        current = data['current'].values
        
        # ตรวจสอบข้อมูล
        if not (np.isfinite(voltage).all() and np.isfinite(current).all()):
            return None
        
        # วิเคราะห์ด้วย Enhanced V4 Improved
        cv_data_dict = {'voltage': voltage, 'current': current}
        results = detector.analyze_cv_data(cv_data_dict)
        
        if results and 'confidence' in results:
            confidence = results.get('confidence', 0)
            peak_data = results.get('peak_data', {})
            
            oxidation_peak = peak_data.get('oxidation_peak')
            reduction_peak = peak_data.get('reduction_peak')
            
            ox_height = oxidation_peak.get('height') if oxidation_peak else None
            red_height = abs(reduction_peak.get('height')) if reduction_peak else None
            
            has_both_peaks = (ox_height is not None and red_height is not None)
            
            return {
                'confidence': confidence,
                'anodic_peak': ox_height,
                'cathodic_peak': red_height,
                'has_both_peaks': has_both_peaks
            }
        
        return None
        
    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return None

def quick_pls_test():
    """ทดสอบ PLS แบบเร็ว"""
    print("🚀 PLS Quick Test with Enhanced Detector V4 Improved")
    print("=" * 55)
    
    # Initialize detector
    detector = EnhancedDetectorV4Improved(confidence_threshold=25.0)
    
    # สแกนข้อมูล Palmsens (1 ไฟล์ต่อ concentration/scan rate)
    palmsens_dir = Path("Test_data/Palmsens")
    
    if not palmsens_dir.exists():
        print("❌ ไม่พบโฟลเดอร์ Palmsens")
        return
    
    data_matrix = []
    total_files = 0
    successful_detections = 0
    
    print("\n📂 สแกนข้อมูล Palmsens...")
    
    for conc_folder in palmsens_dir.iterdir():
        if not conc_folder.is_dir():
            continue
        
        csv_files = list(conc_folder.glob("*.csv"))[:3]  # เอาแค่ 3 ไฟล์แรก
        
        for csv_file in csv_files:
            total_files += 1
            
            concentration, scan_rate = extract_metadata_from_filename(csv_file.name)
            
            if concentration is None or scan_rate is None:
                continue
            
            print(f"   🔬 {csv_file.name}...")
            
            # วิเคราะห์ไฟล์
            result = analyze_single_file(csv_file, detector)
            
            if result and result['has_both_peaks']:
                successful_detections += 1
                
                row = {
                    'filename': csv_file.name,
                    'concentration': concentration,
                    'scan_rate': scan_rate,
                    'anodic_peak': result['anodic_peak'],
                    'cathodic_peak': result['cathodic_peak'],
                    'confidence': result['confidence']
                }
                
                data_matrix.append(row)
                print(f"     ✅ Confidence: {result['confidence']:.1f}%")
            else:
                print(f"     ❌ Peak detection failed")
    
    # สถิติ
    print(f"\n📊 สถิติ:")
    print(f"   📁 ไฟล์ทั้งหมด: {total_files}")
    print(f"   ✅ Detect สำเร็จ: {successful_detections} ({successful_detections/total_files*100:.1f}%)")
    print(f"   📈 ไฟล์สำหรับ PLS: {len(data_matrix)}")
    
    if len(data_matrix) < 3:
        print("❌ ข้อมูลไม่เพียงพอสำหรับ PLS")
        return
    
    # PLS Analysis
    print(f"\n🧠 ทำ PLS Analysis ({len(data_matrix)} samples)...")
    
    df = pd.DataFrame(data_matrix)
    
    # เตรียมข้อมูล
    X = df[['anodic_peak', 'cathodic_peak']].values
    y = df['concentration'].values
    
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
    
    # Metrics
    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    
    print(f"   📈 R² = {r2:.3f}")
    print(f"   📈 RMSE = {rmse:.3f} mM")
    print(f"   📈 Average Confidence = {df['confidence'].mean():.1f}%")
    
    # Visualization
    print("\n📊 สร้างกราฟ...")
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Prediction vs Actual
    ax1 = axes[0]
    ax1.scatter(y, y_pred, alpha=0.7, s=60, color='blue')
    min_val, max_val = min(y.min(), y_pred.min()), max(y.max(), y_pred.max())
    ax1.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2)
    ax1.set_xlabel('Actual Concentration (mM)')
    ax1.set_ylabel('Predicted Concentration (mM)')
    ax1.set_title(f'PLS - Enhanced V4 Improved\nR² = {r2:.3f}')
    ax1.grid(True, alpha=0.3)
    
    # Confidence vs Error
    ax2 = axes[1]
    errors = np.abs(y - y_pred)
    ax2.scatter(df['confidence'], errors, alpha=0.7, s=60, color='green')
    ax2.set_xlabel('Detection Confidence (%)')
    ax2.set_ylabel('Prediction Error (mM)')
    ax2.set_title('Confidence vs Prediction Error')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # บันทึกรูป
    output_dir = Path("pls_results_v4_improved")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = output_dir / f"pls_quick_test_v4_improved_{timestamp}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"💾 บันทึกรูปภาพที่: {output_path}")
    
    plt.show()
    
    # บันทึกข้อมูล
    csv_path = output_dir / f"pls_data_v4_improved_{timestamp}.csv"
    df.to_csv(csv_path, index=False)
    print(f"💾 บันทึกข้อมูลที่: {csv_path}")
    
    print("\n✅ เสร็จสิ้น Quick Test!")
    
    return {
        'r2': r2,
        'rmse': rmse,
        'n_samples': len(data_matrix),
        'avg_confidence': df['confidence'].mean(),
        'detection_rate': successful_detections/total_files*100
    }

if __name__ == "__main__":
    result = quick_pls_test()
    
    if result:
        print(f"\n🎉 Quick Test สำเร็จ!")
        print(f"   Detection Rate: {result['detection_rate']:.1f}%")
        print(f"   R² = {result['r2']:.3f}")
        print(f"   RMSE = {result['rmse']:.3f} mM")
        print(f"   Average Confidence = {result['avg_confidence']:.1f}%")
