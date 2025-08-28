#!/usr/bin/env python3
"""
Mean + Error Bar Comparison for PLS Concentration Prediction
============================================================
เปรียบเทียบ mean และ error bar ของการทำนายความเข้มข้นระหว่าง Palmsens และ STM32
เพื่อดูความสมเหตุสมผลในการแสดงผลกราฟ PLS

Author: AI Assistant
Date: 2025-08-28
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# ตั้งค่าสไตล์กราฟ
plt.style.use('default')
sns.set_palette("husl")

def load_prediction_data():
    """โหลดข้อมูลการทำนายจากทั้งสองเครื่อง"""
    
    # หาโฟลเดอร์ผลลัพธ์ล่าสุด
    base_dir = "."
    results_dirs = [d for d in os.listdir(base_dir) if d.startswith('comprehensive_pls_results_')]
    
    if not results_dirs:
        raise FileNotFoundError("❌ ไม่พบโฟลเดอร์ผลลัพธ์")
    
    latest_dir = max(results_dirs)
    data_dir = os.path.join(base_dir, latest_dir, 'LabPlot2_Data')
    
    # โหลดข้อมูล
    palmsens_file = os.path.join(data_dir, 'concentration_prediction_palmsens.csv')
    stm32_file = os.path.join(data_dir, 'concentration_prediction_stm32.csv')
    
    palmsens_df = pd.read_csv(palmsens_file)
    stm32_df = pd.read_csv(stm32_file)
    
    print(f"✅ โหลดข้อมูล Palmsens: {len(palmsens_df)} samples")
    print(f"✅ โหลดข้อมูล STM32: {len(stm32_df)} samples")
    
    return palmsens_df, stm32_df, latest_dir

def calculate_statistics_by_concentration(df, device_name):
    """คำนวณสถิติตามความเข้มข้น"""
    
    # Group by actual concentration
    stats = df.groupby('Actual_Concentration_mM').agg({
        'Predicted_Concentration_mM': ['mean', 'std', 'count'],
        'Absolute_Error_mM': ['mean', 'std'],
        'Relative_Error_Percent': ['mean', 'std']
    }).round(4)
    
    # Flatten column names
    stats.columns = [
        'Predicted_Mean', 'Predicted_Std', 'N_Samples',
        'AbsError_Mean', 'AbsError_Std', 
        'RelError_Mean', 'RelError_Std'
    ]
    
    stats = stats.reset_index()
    stats['Device'] = device_name
    
    # คำนวณ Standard Error of Mean (SEM)
    stats['Predicted_SEM'] = stats['Predicted_Std'] / np.sqrt(stats['N_Samples'])
    stats['AbsError_SEM'] = stats['AbsError_Std'] / np.sqrt(stats['N_Samples'])
    
    return stats

def create_comparison_plots(palmsens_stats, stm32_stats, output_dir):
    """สร้างกราฟเปรียบเทียบ mean + error bar"""
    
    # รวมข้อมูล
    combined_stats = pd.concat([palmsens_stats, stm32_stats], ignore_index=True)
    
    # สร้างกราฟ
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('PLS Concentration Prediction: Mean ± Error Bar Comparison\nPalmsens vs STM32', 
                 fontsize=16, fontweight='bold')
    
    # กำหนดสี
    colors = {'Palmsens': '#2E86AB', 'STM32': '#A23B72'}
    
    # Plot 1: Predicted vs Actual with Error Bars
    ax1 = axes[0, 0]
    
    for device in ['Palmsens', 'STM32']:
        data = combined_stats[combined_stats['Device'] == device]
        
        ax1.errorbar(data['Actual_Concentration_mM'], 
                    data['Predicted_Mean'],
                    yerr=data['Predicted_Std'],  # ใช้ Standard Deviation
                    fmt='o-', 
                    label=f'{device} (n={data["N_Samples"].sum()})',
                    color=colors[device],
                    capsize=5,
                    capthick=2,
                    markersize=8,
                    linewidth=2)
    
    # Perfect prediction line
    max_conc = combined_stats['Actual_Concentration_mM'].max()
    ax1.plot([0, max_conc], [0, max_conc], 'r--', alpha=0.7, linewidth=2, label='Perfect Prediction (y=x)')
    
    ax1.set_xlabel('Actual Concentration (mM)', fontweight='bold')
    ax1.set_ylabel('Predicted Concentration (mM)', fontweight='bold')
    ax1.set_title('A) Predicted vs Actual Concentration\n(Error bars = ± 1 SD)', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Predicted vs Actual with SEM
    ax2 = axes[0, 1]
    
    for device in ['Palmsens', 'STM32']:
        data = combined_stats[combined_stats['Device'] == device]
        
        ax2.errorbar(data['Actual_Concentration_mM'], 
                    data['Predicted_Mean'],
                    yerr=data['Predicted_SEM'],  # ใช้ Standard Error of Mean
                    fmt='s-', 
                    label=f'{device} (±SEM)',
                    color=colors[device],
                    capsize=5,
                    capthick=2,
                    markersize=8,
                    linewidth=2)
    
    # Perfect prediction line
    ax2.plot([0, max_conc], [0, max_conc], 'r--', alpha=0.7, linewidth=2, label='Perfect Prediction (y=x)')
    
    ax2.set_xlabel('Actual Concentration (mM)', fontweight='bold')
    ax2.set_ylabel('Predicted Concentration (mM)', fontweight='bold')
    ax2.set_title('B) Predicted vs Actual Concentration\n(Error bars = ± SEM)', fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Absolute Error by Concentration
    ax3 = axes[1, 0]
    
    for device in ['Palmsens', 'STM32']:
        data = combined_stats[combined_stats['Device'] == device]
        
        ax3.errorbar(data['Actual_Concentration_mM'], 
                    data['AbsError_Mean'],
                    yerr=data['AbsError_Std'],
                    fmt='o-', 
                    label=f'{device}',
                    color=colors[device],
                    capsize=5,
                    capthick=2,
                    markersize=8,
                    linewidth=2)
    
    ax3.set_xlabel('Actual Concentration (mM)', fontweight='bold')
    ax3.set_ylabel('Mean Absolute Error (mM)', fontweight='bold')
    ax3.set_title('C) Prediction Error by Concentration\n(Error bars = ± 1 SD)', fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Sample Size by Concentration
    ax4 = axes[1, 1]
    
    palmsens_data = combined_stats[combined_stats['Device'] == 'Palmsens']
    stm32_data = combined_stats[combined_stats['Device'] == 'STM32']
    
    x_pos = np.arange(len(palmsens_data))
    width = 0.35
    
    bars1 = ax4.bar(x_pos - width/2, palmsens_data['N_Samples'], width, 
                   label='Palmsens', color=colors['Palmsens'], alpha=0.8)
    bars2 = ax4.bar(x_pos + width/2, stm32_data['N_Samples'], width,
                   label='STM32', color=colors['STM32'], alpha=0.8)
    
    # เพิ่มค่าบน bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}', ha='center', va='bottom', fontweight='bold')
    
    ax4.set_xlabel('Concentration (mM)', fontweight='bold')
    ax4.set_ylabel('Number of Samples', fontweight='bold')
    ax4.set_title('D) Sample Size Distribution', fontweight='bold')
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels([f'{c:.1f}' for c in palmsens_data['Actual_Concentration_mM']])
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # บันทึกกราฟ
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'pls_mean_errorbar_comparison_{timestamp}.png'
    filepath = os.path.join(output_dir, filename)
    
    plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"💾 บันทึกกราฟ: {filename}")
    
    return filepath, combined_stats

def create_detailed_statistics_table(combined_stats, output_dir):
    """สร้างตารางสถิติโดยละเอียด"""
    
    # คำนวณสถิติเพิ่มเติม
    detailed_stats = []
    
    for device in ['Palmsens', 'STM32']:
        device_data = combined_stats[combined_stats['Device'] == device]
        
        for _, row in device_data.iterrows():
            detailed_stats.append({
                'Device': device,
                'Actual_Concentration_mM': row['Actual_Concentration_mM'],
                'N_Samples': int(row['N_Samples']),
                'Predicted_Mean_mM': row['Predicted_Mean'],
                'Predicted_Std_mM': row['Predicted_Std'],
                'Predicted_SEM_mM': row['Predicted_SEM'],
                'CV_Percent': (row['Predicted_Std'] / row['Predicted_Mean'] * 100) if row['Predicted_Mean'] != 0 else 0,
                'Bias_mM': row['Predicted_Mean'] - row['Actual_Concentration_mM'],
                'Bias_Percent': ((row['Predicted_Mean'] - row['Actual_Concentration_mM']) / row['Actual_Concentration_mM'] * 100) if row['Actual_Concentration_mM'] != 0 else 0,
                'AbsError_Mean_mM': row['AbsError_Mean'],
                'AbsError_Std_mM': row['AbsError_Std'],
                'RelError_Mean_Percent': row['RelError_Mean'],
                'RelError_Std_Percent': row['RelError_Std']
            })
    
    detailed_df = pd.DataFrame(detailed_stats)
    detailed_df = detailed_df.round(4)
    
    # บันทึกตาราง
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'pls_detailed_statistics_{timestamp}.csv'
    filepath = os.path.join(output_dir, filename)
    
    detailed_df.to_csv(filepath, index=False)
    print(f"💾 บันทึกตารางสถิติ: {filename}")
    
    return filepath, detailed_df

def analyze_prediction_quality(combined_stats):
    """วิเคราะห์คุณภาพการทำนาย"""
    
    print("\n" + "="*60)
    print("📊 การวิเคราะห์คุณภาพการทำนายความเข้มข้น")
    print("="*60)
    
    for device in ['Palmsens', 'STM32']:
        device_data = combined_stats[combined_stats['Device'] == device]
        print(f"\n🔸 {device}:")
        print(f"   จำนวนความเข้มข้นที่ทดสอบ: {len(device_data)} ระดับ")
        print(f"   จำนวนตัวอย่างรวม: {device_data['N_Samples'].sum()} samples")
        
        # คำนวณ overall statistics
        total_samples = device_data['N_Samples'].sum()
        weighted_bias = (device_data['Predicted_Mean'] - device_data['Actual_Concentration_mM']).mean()
        weighted_abs_error = device_data['AbsError_Mean'].mean()
        weighted_rel_error = device_data['RelError_Mean'].mean()
        
        print(f"   Bias เฉลี่ย: {weighted_bias:.3f} mM")
        print(f"   Absolute Error เฉลี่ย: {weighted_abs_error:.3f} mM")
        print(f"   Relative Error เฉลี่ย: {weighted_rel_error:.1f}%")
        
        # วิเคราะห์แต่ละความเข้มข้น
        print(f"\n   📋 รายละเอียดตามความเข้มข้น:")
        for _, row in device_data.iterrows():
            conc = row['Actual_Concentration_mM']
            pred = row['Predicted_Mean']
            std = row['Predicted_Std']
            n = int(row['N_Samples'])
            cv = (std / pred * 100) if pred != 0 else 0
            bias = pred - conc
            
            print(f"     {conc:4.1f} mM: {pred:6.3f}±{std:5.3f} (n={n:2d}, CV={cv:5.1f}%, Bias={bias:+6.3f})")

def main():
    """ฟังก์ชันหลัก"""
    
    print("🔍 เริ่มการวิเคราะห์ Mean + Error Bar สำหรับ PLS Concentration Prediction")
    print("="*80)
    
    try:
        # โหลดข้อมูล
        palmsens_df, stm32_df, results_dir = load_prediction_data()
        
        # คำนวณสถิติ
        print("\n📊 กำลังคำนวณสถิติ...")
        palmsens_stats = calculate_statistics_by_concentration(palmsens_df, 'Palmsens')
        stm32_stats = calculate_statistics_by_concentration(stm32_df, 'STM32')
        
        # สร้างโฟลเดอร์สำหรับผลลัพธ์
        output_dir = f"pls_mean_errorbar_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(output_dir, exist_ok=True)
        
        # สร้างกราฟ
        print("\n📈 กำลังสร้างกราฟเปรียบเทียบ...")
        plot_file, combined_stats = create_comparison_plots(palmsens_stats, stm32_stats, output_dir)
        
        # สร้างตารางสถิติ
        print("\n📋 กำลังสร้างตารางสถิติ...")
        stats_file, detailed_df = create_detailed_statistics_table(combined_stats, output_dir)
        
        # วิเคราะห์คุณภาพ
        analyze_prediction_quality(combined_stats)
        
        # สรุปผลลัพธ์
        print("\n" + "="*80)
        print("🎉 การวิเคราะห์เสร็จสิ้น!")
        print("="*80)
        print(f"📁 โฟลเดอร์ผลลัพธ์: {output_dir}")
        print(f"📊 กราฟเปรียบเทียบ: {os.path.basename(plot_file)}")
        print(f"📋 ตารางสถิติ: {os.path.basename(stats_file)}")
        
        # แสดงสรุปสำคัญ
        print(f"\n📈 สรุปสำคัญ:")
        print(f"   • Palmsens: {len(palmsens_df)} samples, {len(palmsens_stats)} concentration levels")
        print(f"   • STM32: {len(stm32_df)} samples, {len(stm32_stats)} concentration levels")
        print(f"   • Error bars แสดงทั้ง Standard Deviation และ Standard Error of Mean")
        print(f"   • ข้อมูลพร้อมสำหรับการประเมินความเหมาะสมของกราฟ PLS")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
