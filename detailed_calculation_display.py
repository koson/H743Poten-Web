#!/usr/bin/env python3
"""
Detailed Algorithm Performance Calculator
แสดงรายละเอียดการคำนวณทุก step สำหรับทุกอัลกอริทึม
"""

import math
import csv
import json
from typing import Dict, List

class DetailedPerformanceCalculator:
    """
    Calculator ที่แสดงรายละเอียดการคำนวณทุก step
    """
    
    def __init__(self):
        # ค่า base เริ่มต้นเท่าเทียมกัน
        self.base_scores = {
            'speed': 100.0,
            'accuracy': 100.0, 
            'memory': 100.0
        }
        
        # ค่าคงที่สำหรับการคำนวณ
        self.calculation_constants = {
            'complexity_multiplier': 15.0,
            'ml_overhead_multiplier': 45.0,
            'data_processing_multiplier': 2.0,
            'feature_richness_multiplier': 20.0,
            'noise_handling_multiplier': 15.0,
            'ml_enhancement_multiplier': 25.0,
            'feature_storage_multiplier': 8.0,
            'buffer_overhead_multiplier': 15.0
        }
        
        # พารามิเตอร์เฉพาะแต่ละอัลกอริทึม
        self.algorithm_params = {
            'TraditionalCV': {
                'complexity_factor': 1.0,
                'ml_overhead': 0.0,
                'feature_richness': 0.2,
                'noise_handling': 0.6,
                'ml_enhancement': 0.0,
                'memory_efficiency': 0.98,
                'feature_storage_offset': 0.2,
                'buffer_overhead': 0.0,
                'data_points': 1000
            },
            'DeepCV': {
                'complexity_factor': 4.0,
                'ml_overhead': 0.35,
                'feature_richness': 1.0,
                'noise_handling': 0.95,
                'ml_enhancement': 0.35,
                'memory_efficiency': 0.72,
                'feature_storage_offset': 0.2,
                'buffer_overhead': 0.35,
                'data_points': 1000
            },
            'HybridCV': {
                'complexity_factor': 2.2,
                'ml_overhead': 0.15,
                'feature_richness': 0.7,
                'noise_handling': 0.8,
                'ml_enhancement': 0.15,
                'memory_efficiency': 0.85,
                'feature_storage_offset': 0.2,
                'buffer_overhead': 0.15,
                'data_points': 1000
            }
        }
        
        # น้ำหนักสำหรับ Overall Score
        self.weights = {
            'speed': 0.25,
            'accuracy': 0.45,
            'memory': 0.30
        }

    def calculate_detailed_scores(self, algorithm: str) -> Dict:
        """
        คำนวณคะแนนพร้อมแสดงรายละเอียดทุก step
        """
        params = self.algorithm_params[algorithm]
        constants = self.calculation_constants
        
        # =========== SPEED CALCULATION ===========
        speed_base = self.base_scores['speed']
        complexity_penalty = (params['complexity_factor'] - 1.0) * constants['complexity_multiplier']
        ml_overhead_penalty = params['ml_overhead'] * constants['ml_overhead_multiplier']
        data_processing_penalty = math.log10(params['data_points']) * constants['data_processing_multiplier']
        
        raw_speed = speed_base - complexity_penalty - ml_overhead_penalty - data_processing_penalty
        final_speed = max(20.0, min(100.0, raw_speed))
        
        # =========== ACCURACY CALCULATION ===========
        # ใช้ base 100.0 เหมือน Speed เพื่อความเป็นธรรม
        accuracy_base = self.base_scores['accuracy']  # 100.0
        feature_richness_penalty = (1.0 - params['feature_richness']) * constants['feature_richness_multiplier']
        noise_handling_penalty = (1.0 - params['noise_handling']) * constants['noise_handling_multiplier']
        ml_enhancement_bonus = params['ml_enhancement'] * constants['ml_enhancement_multiplier']
        
        raw_accuracy = accuracy_base - feature_richness_penalty - noise_handling_penalty + ml_enhancement_bonus
        final_accuracy = max(30.0, min(100.0, raw_accuracy))
        
        # =========== MEMORY CALCULATION ===========
        memory_base = self.base_scores['memory']  # 100.0
        memory_efficiency_penalty = (1.0 - params['memory_efficiency']) * 100.0
        feature_storage_penalty = (params['feature_richness'] - params['feature_storage_offset']) * constants['feature_storage_multiplier']
        buffer_overhead_penalty = params['buffer_overhead'] * constants['buffer_overhead_multiplier']
        
        raw_memory = memory_base - memory_efficiency_penalty - feature_storage_penalty - buffer_overhead_penalty
        final_memory = max(40.0, min(100.0, raw_memory))
        
        # =========== OVERALL CALCULATION ===========
        overall_score = (self.weights['speed'] * final_speed + 
                        self.weights['accuracy'] * final_accuracy + 
                        self.weights['memory'] * final_memory)
        
        return {
            'algorithm': algorithm,
            # Speed details
            'speed_base': speed_base,
            'complexity_factor': params['complexity_factor'],
            'complexity_penalty': complexity_penalty,
            'ml_overhead': params['ml_overhead'],
            'ml_overhead_penalty': ml_overhead_penalty,
            'data_points': params['data_points'],
            'data_processing_penalty': data_processing_penalty,
            'raw_speed': raw_speed,
            'final_speed': round(final_speed, 1),
            
            # Accuracy details
            'accuracy_base': accuracy_base,
            'feature_richness': params['feature_richness'],
            'feature_richness_penalty': feature_richness_penalty,
            'noise_handling': params['noise_handling'],
            'noise_handling_penalty': noise_handling_penalty,
            'ml_enhancement': params['ml_enhancement'],
            'ml_enhancement_bonus': ml_enhancement_bonus,
            'raw_accuracy': raw_accuracy,
            'final_accuracy': round(final_accuracy, 1),
            
            # Memory details
            'memory_efficiency': params['memory_efficiency'],
            'memory_base': memory_base,
            'memory_efficiency_penalty': memory_efficiency_penalty,
            'feature_storage_offset': params['feature_storage_offset'],
            'feature_storage_penalty': feature_storage_penalty,
            'buffer_overhead': params['buffer_overhead'],
            'buffer_overhead_penalty': buffer_overhead_penalty,
            'raw_memory': raw_memory,
            'final_memory': round(final_memory, 1),
            
            # Overall
            'overall_score': round(overall_score, 1)
        }

    def display_detailed_calculation(self, algorithm: str, details: Dict):
        """
        แสดงรายละเอียดการคำนวณแบบ step-by-step
        """
        print(f"\n🔍 {algorithm} Calculation Example:")
        print()
        
        # Speed Calculation
        print("📐 Speed Score:")
        print(f"   Base Speed: {details['speed_base']}")
        print(f"   - Complexity Penalty: ({details['complexity_factor']} - 1.0) × 15 = {details['complexity_penalty']:.1f}")
        print(f"   - ML Overhead Penalty: {details['ml_overhead']:.2f} × 45 = {details['ml_overhead_penalty']:.1f}")
        print(f"   - Data Processing: log₁₀({details['data_points']}) × 2 = {details['data_processing_penalty']:.1f}")
        print(f"   Raw Speed = {details['speed_base']} - {details['complexity_penalty']:.1f} - {details['ml_overhead_penalty']:.1f} - {details['data_processing_penalty']:.1f} = {details['raw_speed']:.1f}")
        print(f"   Final Speed = {details['final_speed']}")
        print()
        
        # Accuracy Calculation
        print("📊 Accuracy Score:")
        print(f"   Base Accuracy: {details['accuracy_base']}")
        print(f"   - Feature Richness Penalty: (1.0 - {details['feature_richness']}) × 20 = {details['feature_richness_penalty']:.1f}")
        print(f"   - Noise Handling Penalty: (1.0 - {details['noise_handling']}) × 15 = {details['noise_handling_penalty']:.1f}")
        print(f"   + ML Enhancement: {details['ml_enhancement']:.2f} × 25 = {details['ml_enhancement_bonus']:.1f}")
        print(f"   Raw Accuracy = {details['accuracy_base']} - {details['feature_richness_penalty']:.1f} - {details['noise_handling_penalty']:.1f} + {details['ml_enhancement_bonus']:.1f} = {details['raw_accuracy']:.1f}")
        print(f"   Final Accuracy = {details['final_accuracy']}")
        print()
        
        # Memory Calculation
        print("💾 Memory Score:")
        print(f"   Base Memory: {details['memory_base']}")
        print(f"   - Memory Efficiency Penalty: (1.0 - {details['memory_efficiency']}) × 100 = {details['memory_efficiency_penalty']:.1f}")
        print(f"   - Feature Storage: ({details['feature_richness']} - {details['feature_storage_offset']}) × 8 = {details['feature_storage_penalty']:.1f}")
        print(f"   - Buffer Overhead: {details['buffer_overhead']:.2f} × 15 = {details['buffer_overhead_penalty']:.1f}")
        print(f"   Raw Memory = {details['memory_base']} - {details['memory_efficiency_penalty']:.1f} - {details['feature_storage_penalty']:.1f} - {details['buffer_overhead_penalty']:.1f} = {details['raw_memory']:.1f}")
        print(f"   Final Memory = {details['final_memory']}")
        print()
        
        # Overall Calculation
        print("🎯 Overall Score:")
        print(f"   Overall = 0.25 × {details['final_speed']} + 0.45 × {details['final_accuracy']} + 0.30 × {details['final_memory']}")
        print(f"   Overall = {0.25 * details['final_speed']:.1f} + {0.45 * details['final_accuracy']:.1f} + {0.30 * details['final_memory']:.1f} = {details['overall_score']}")
        
        print("=" * 80)

    def export_to_csv(self, all_details: List[Dict]):
        """
        ส่งออกรายละเอียดการคำนวณเป็น CSV
        """
        filename = 'algorithm_calculation_details.csv'
        
        # สร้าง header
        fieldnames = [
            'Algorithm',
            # Speed fields
            'Speed_Base', 'Complexity_Factor', 'Complexity_Penalty', 
            'ML_Overhead', 'ML_Overhead_Penalty', 'Data_Points', 'Data_Processing_Penalty',
            'Raw_Speed', 'Final_Speed',
            # Accuracy fields
            'Accuracy_Base', 'Feature_Richness', 'Feature_Richness_Penalty',
            'Noise_Handling', 'Noise_Handling_Penalty', 'ML_Enhancement', 'ML_Enhancement_Bonus',
            'Raw_Accuracy', 'Final_Accuracy',
            # Memory fields
            'Memory_Base', 'Memory_Efficiency', 'Memory_Efficiency_Penalty', 'Feature_Storage_Offset', 'Feature_Storage_Penalty',
            'Buffer_Overhead', 'Buffer_Overhead_Penalty', 'Raw_Memory', 'Final_Memory',
            # Overall
            'Overall_Score'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # เขียน header
            writer.writeheader()
            
            # เขียนข้อมูล
            for details in all_details:
                row = {
                    'Algorithm': details['algorithm'],
                    # Speed
                    'Speed_Base': details['speed_base'],
                    'Complexity_Factor': details['complexity_factor'],
                    'Complexity_Penalty': round(details['complexity_penalty'], 1),
                    'ML_Overhead': details['ml_overhead'],
                    'ML_Overhead_Penalty': round(details['ml_overhead_penalty'], 1),
                    'Data_Points': details['data_points'],
                    'Data_Processing_Penalty': round(details['data_processing_penalty'], 1),
                    'Raw_Speed': round(details['raw_speed'], 1),
                    'Final_Speed': details['final_speed'],
                    # Accuracy
                    'Accuracy_Base': details['accuracy_base'],
                    'Feature_Richness': details['feature_richness'],
                    'Feature_Richness_Penalty': round(details['feature_richness_penalty'], 1),
                    'Noise_Handling': details['noise_handling'],
                    'Noise_Handling_Penalty': round(details['noise_handling_penalty'], 1),
                    'ML_Enhancement': details['ml_enhancement'],
                    'ML_Enhancement_Bonus': round(details['ml_enhancement_bonus'], 1),
                    'Raw_Accuracy': round(details['raw_accuracy'], 1),
                    'Final_Accuracy': details['final_accuracy'],
                    # Memory
                    'Memory_Base': details['memory_base'],
                    'Memory_Efficiency': details['memory_efficiency'],
                    'Memory_Efficiency_Penalty': round(details['memory_efficiency_penalty'], 1),
                    'Feature_Storage_Offset': details['feature_storage_offset'],
                    'Feature_Storage_Penalty': round(details['feature_storage_penalty'], 1),
                    'Buffer_Overhead': details['buffer_overhead'],
                    'Buffer_Overhead_Penalty': round(details['buffer_overhead_penalty'], 1),
                    'Raw_Memory': round(details['raw_memory'], 1),
                    'Final_Memory': details['final_memory'],
                    # Overall
                    'Overall_Score': details['overall_score']
                }
                writer.writerow(row)
        
        print(f"✅ รายละเอียดการคำนวณส่งออกเป็น CSV: {filename}")

    def export_summary_csv(self, all_details: List[Dict]):
        """
        ส่งออกตารางสรุปผลลัพธ์เป็น CSV
        """
        filename = 'algorithm_performance_summary.csv'
        
        fieldnames = ['Algorithm', 'Speed_Score', 'Accuracy_Score', 'Memory_Score', 'Overall_Score']
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # เขียน header
            writer.writeheader()
            
            # เขียนข้อมูล
            for details in all_details:
                row = {
                    'Algorithm': details['algorithm'],
                    'Speed_Score': details['final_speed'],
                    'Accuracy_Score': details['final_accuracy'],
                    'Memory_Score': details['final_memory'],
                    'Overall_Score': details['overall_score']
                }
                writer.writerow(row)
        
        print(f"✅ ตารางสรุปส่งออกเป็น CSV: {filename}")

def main():
    """
    ฟังก์ชันหลักสำหรับรันการคำนวณและแสดงผล
    """
    print("🚀 Detailed Algorithm Performance Calculator")
    print("แสดงรายละเอียดการคำนวณทุก step สำหรับทุกอัลกอริทึม")
    print("=" * 80)
    
    calculator = DetailedPerformanceCalculator()
    algorithms = ['TraditionalCV', 'DeepCV', 'HybridCV']
    all_details = []
    
    # คำนวณและแสดงรายละเอียดสำหรับแต่ละอัลกอริทึม
    for algorithm in algorithms:
        details = calculator.calculate_detailed_scores(algorithm)
        all_details.append(details)
        calculator.display_detailed_calculation(algorithm, details)
    
    # แสดงตารางสรุป
    print("\n📈 PERFORMANCE SUMMARY TABLE")
    print("=" * 60)
    print(f"{'Algorithm':<15} {'Speed':<8} {'Accuracy':<10} {'Memory':<8} {'Overall'}")
    print("-" * 60)
    
    for details in all_details:
        print(f"{details['algorithm']:<15} {details['final_speed']:<8} {details['final_accuracy']:<10} {details['final_memory']:<8} {details['overall_score']}")
    
    print("-" * 60)
    
    # ส่งออกเป็น CSV
    print("\n📊 EXPORTING TO CSV FILES:")
    calculator.export_to_csv(all_details)
    calculator.export_summary_csv(all_details)
    
    # บันทึกเป็น JSON ด้วย
    with open('detailed_calculation_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_details, f, indent=2, ensure_ascii=False)
    print(f"✅ รายละเอียดครบถ้วนบันทึกเป็น JSON: detailed_calculation_results.json")
    
    print(f"\n🎉 การคำนวณเสร็จสมบูรณ์!")
    print(f"📋 ไฟล์ที่สร้าง:")
    print(f"   - algorithm_calculation_details.csv (รายละเอียดการคำนวณทุก step)")
    print(f"   - algorithm_performance_summary.csv (ตารางสรุปผลลัพธ์)")
    print(f"   - detailed_calculation_results.json (ข้อมูลครบถ้วนในรูปแบบ JSON)")

if __name__ == "__main__":
    main()