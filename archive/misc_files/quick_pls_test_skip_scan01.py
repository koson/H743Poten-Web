#!/usr/bin/env python3
"""
Quick PLS Test: Palmsens vs STM32 (ข้าม scan_01)
ทดสอบรวดเร็วก่อนรัน full analysis
"""

import pandas as pd
import numpy as np
import glob
from pathlib import Path
import time
from datetime import datetime

def quick_pls_test():
    print("🚀 Quick PLS Test: Palmsens vs STM32")
    print("⚠️ ข้าม scan_01 (ระบบยังไม่เสถียร)")
    print("=" * 50)
    
    try:
        from enhanced_detector_v4_improved import EnhancedDetectorV4Improved
        detector = EnhancedDetectorV4Improved(confidence_threshold=25.0)
        print("✅ Enhanced V4 Improved พร้อมใช้งาน")
    except ImportError:
        print("❌ Enhanced V4 Improved ไม่พร้อมใช้งาน")
        return
    
    # หาไฟล์ตัวอย่าง (ข้าม scan_01)
    palmsens_files = [f for f in glob.glob('Test_data/Palmsens/**/*.csv', recursive=True) 
                      if 'scan_01' not in f][:10]  # ใช้แค่ 10 ไฟล์
    
    stm32_files = [f for f in glob.glob('Test_data/Stm32/**/*.csv', recursive=True) 
                   if 'scan_01' not in f][:10]  # ใช้แค่ 10 ไฟล์
    
    print(f"📁 ทดสอบ Palmsens: {len(palmsens_files)} ไฟล์")
    print(f"📁 ทดสอบ STM32: {len(stm32_files)} ไฟล์")
    
    def analyze_file_quick(filepath, device_name):
        """วิเคราะห์ไฟล์อย่างรวดเร็ว"""
        try:
            data = pd.read_csv(filepath, skiprows=2, names=['voltage', 'current'])
            cv_data = {
                'voltage': data['voltage'].tolist(),
                'current': data['current'].tolist()
            }
            
            results = detector.analyze_cv_data(cv_data)
            peaks = results.get('peaks', [])
            
            ox_peaks = [p for p in peaks if p.get('type') == 'oxidation']
            red_peaks = [p for p in peaks if p.get('type') == 'reduction']
            
            if len(ox_peaks) > 0 and len(red_peaks) > 0:
                return {
                    'filename': Path(filepath).name,
                    'device': device_name,
                    'ox_voltage': ox_peaks[0]['voltage'],
                    'ox_current': ox_peaks[0]['current'],
                    'red_voltage': red_peaks[0]['voltage'],
                    'red_current': red_peaks[0]['current'],
                    'peak_separation': abs(ox_peaks[0]['voltage'] - red_peaks[0]['voltage']),
                    'current_ratio': ox_peaks[0]['current'] / red_peaks[0]['current'] if red_peaks[0]['current'] != 0 else 0
                }
            
        except Exception as e:
            print(f"❌ Error: {Path(filepath).name}: {str(e)[:30]}")
            
        return None
    
    # วิเคราะห์ Palmsens
    print(f"\\n🔬 วิเคราะห์ Palmsens (ข้าม scan_01)...")
    palmsens_results = []
    for i, filepath in enumerate(palmsens_files):
        print(f"[{i+1:2d}/10] {Path(filepath).name}...", end=" ")
        result = analyze_file_quick(filepath, "Palmsens")
        if result:
            palmsens_results.append(result)
            print(f"✅ ox:{result['ox_voltage']:.3f}V, red:{result['red_voltage']:.3f}V")
        else:
            print("❌")
    
    # วิเคราะห์ STM32
    print(f"\\n🎯 วิเคราะห์ STM32 (ข้าม scan_01)...")
    stm32_results = []
    for i, filepath in enumerate(stm32_files):
        print(f"[{i+1:2d}/10] {Path(filepath).name}...", end=" ")
        result = analyze_file_quick(filepath, "STM32")
        if result:
            stm32_results.append(result)
            print(f"✅ ox:{result['ox_voltage']:.3f}V, red:{result['red_voltage']:.3f}V")
        else:
            print("❌")
    
    # สรุปผล
    print(f"\\n📊 สรุปผลการทดสอบ:")
    print(f"  Palmsens สำเร็จ: {len(palmsens_results)}/10 ({len(palmsens_results)*10}%)")
    print(f"  STM32 สำเร็จ: {len(stm32_results)}/10 ({len(stm32_results)*10}%)")
    
    if palmsens_results and stm32_results:
        print(f"\\n🎯 เปรียบเทียบ Peak Characteristics:")
        
        # Palmsens stats
        pal_ox_v = [r['ox_voltage'] for r in palmsens_results]
        pal_red_v = [r['red_voltage'] for r in palmsens_results]
        pal_sep = [r['peak_separation'] for r in palmsens_results]
        
        print(f"  Palmsens:")
        print(f"    Ox voltage: {np.mean(pal_ox_v):.3f}±{np.std(pal_ox_v):.3f} V")
        print(f"    Red voltage: {np.mean(pal_red_v):.3f}±{np.std(pal_red_v):.3f} V")
        print(f"    Separation: {np.mean(pal_sep):.3f}±{np.std(pal_sep):.3f} V")
        
        # STM32 stats
        stm_ox_v = [r['ox_voltage'] for r in stm32_results]
        stm_red_v = [r['red_voltage'] for r in stm32_results]
        stm_sep = [r['peak_separation'] for r in stm32_results]
        
        print(f"  STM32:")
        print(f"    Ox voltage: {np.mean(stm_ox_v):.3f}±{np.std(stm_ox_v):.3f} V")
        print(f"    Red voltage: {np.mean(stm_red_v):.3f}±{np.std(stm_red_v):.3f} V")
        print(f"    Separation: {np.mean(stm_sep):.3f}±{np.std(stm_sep):.3f} V")
        
        # Export quick results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Combined DataFrame
        all_results = palmsens_results + stm32_results
        df = pd.DataFrame(all_results)
        
        quick_file = f"pls_quick_test_results_{timestamp}.csv"
        df.to_csv(quick_file, index=False)
        
        print(f"\\n📄 Quick test results: {quick_file}")
        print(f"✅ พร้อมสำหรับ full PLS analysis!")
        
        return True
    else:
        print(f"\\n❌ ไม่มีข้อมูลเพียงพอสำหรับ PLS analysis")
        return False

if __name__ == "__main__":
    success = quick_pls_test()
    if success:
        print(f"\\n🎉 Quick test สำเร็จ! พร้อมรัน full PLS analysis")
    else:
        print(f"\\n💥 Quick test ล้มเหลว - ตรวจสอบข้อมูลก่อน")
