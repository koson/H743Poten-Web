#!/usr/bin/env python3
"""
สร้างกราฟเปรียบเทียบ STM32 ก่อน-หลัง calibrate พร้อมสถิติ
"""

from calibration_graph_comparison_fixed import CalibrationGraphComparison
import matplotlib
matplotlib.use('Agg')  # ใช้ backend ที่บันทึกไฟล์โดยไม่แสดงผล

def main():
    print("🚀 กำลังสร้างกราฟเปรียบเทียบ Calibration")
    print("="*60)
    
    visualizer = CalibrationGraphComparison()
    
    # แสดงรายการ measurements ที่มี
    visualizer.list_available_measurements()
    
    print("\n🎯 กำลังสร้างกราฟเปรียบเทียบ...")
    
    # เปรียบเทียบ STM32 กับ PalmSens ที่เป็นข้อมูลล่าสุด
    stm32_id = 75  # STM32 ล่าสุด (5mM E4S5, 50.000 V/s)
    palmsens_id = 90  # PalmSens ล่าสุด (5mM E3S8, 50.000 V/s)
    
    print(f"\n📊 เปรียบเทียบ STM32 ID {stm32_id} vs PalmSens ID {palmsens_id}")
    visualizer.plot_comparison(stm32_id, palmsens_id)
    
    print("\n✅ สำเร็จ! กราฟถูกบันทึกเป็นไฟล์ .png แล้ว")
    print("📁 ตรวจสอบไฟล์ในโฟลเดอร์ปัจจุบัน")

if __name__ == "__main__":
    main()