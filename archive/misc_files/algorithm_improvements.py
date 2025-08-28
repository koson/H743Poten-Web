#!/usr/bin/env python3
"""
Algorithm Improvement Recommendations
ข้อเสนอแนะในการปรับปรุงอัลกอริทึมการตรวจจับ peak และ baseline

จากการวิเคราะห์ไฟล์ที่มีปัญหา พบประเด็นที่ต้องปรับปรุง:
"""

import numpy as np
import pandas as pd
from pathlib import Path

class AlgorithmImprovements:
    """คลาสข้อเสนอแนะการปรับปรุงอัลกอริทึม"""
    
    def __init__(self):
        self.issues_found = [
            {
                'issue': 'การแบ่ง scan direction ไม่ถูกต้อง',
                'description': 'Forward scan มีแค่ 2-3 จุด ทำให้การวิเคราะห์ไม่ถูกต้อง',
                'impact': 'Baseline detection และ peak validation ผิดพลาด',
                'solution': 'ปรับปรุงการหา turning point ให้แม่นยำ'
            },
            {
                'issue': 'Peak validation ยังไม่เข้มงวดพอ',
                'description': 'Peak ที่ +0.7V ยังถูกตรวจจับแม้ว่าไม่ควรเจอ',
                'impact': 'False positive peaks',
                'solution': 'เพิ่ม voltage range validation และ prominence threshold'
            },
            {
                'issue': 'Baseline-peak collision detection',
                'description': 'ยังไม่มีการตรวจสอบว่า baseline ทับกับ peak หรือไม่',
                'impact': 'Baseline accuracy ลดลง',
                'solution': 'เพิ่มการตรวจสอบ overlap และ conflict resolution'
            },
            {
                'issue': 'Signal-to-noise ratio consideration',
                'description': 'ไม่ได้พิจารณา SNR ในการตั้ง threshold',
                'impact': 'Miss peaks ในข้อมูลที่มี noise สูง',
                'solution': 'Dynamic threshold based on SNR'
            }
        ]
    
    def detect_scan_direction_improved(self, voltage):
        """การปรับปรุงการหา scan direction"""
        print("🔄 Improved Scan Direction Detection:")
        
        # Method 1: หาจุดที่แรงดันเปลี่ยนทิศทางจริงๆ
        voltage_diff = np.diff(voltage)
        
        # หา running average ของ direction
        window_size = min(10, len(voltage_diff) // 4)
        if window_size < 3:
            window_size = 3
            
        direction_avg = np.convolve(np.sign(voltage_diff), 
                                  np.ones(window_size)/window_size, 
                                  mode='same')
        
        # หาจุดที่ direction เปลี่ยนจาก positive เป็น negative (หรือกลับกัน)
        direction_changes = []
        for i in range(1, len(direction_avg)):
            if abs(direction_avg[i] - direction_avg[i-1]) > 1.0:  # Significant direction change
                direction_changes.append(i)
        
        if len(direction_changes) > 0:
            # เลือก direction change ที่มีนัยสำคัญมากที่สุด
            turning_point = direction_changes[0]
            
            # Validate ว่า turning point มีความหมาย
            forward_length = turning_point
            reverse_length = len(voltage) - turning_point
            
            min_scan_length = len(voltage) * 0.1  # อย่างน้อย 10% ของข้อมูล
            
            if forward_length < min_scan_length:
                print(f"   ⚠️ Forward scan too short ({forward_length} points), adjusting...")
                turning_point = int(min_scan_length)
            elif reverse_length < min_scan_length:
                print(f"   ⚠️ Reverse scan too short ({reverse_length} points), adjusting...")
                turning_point = len(voltage) - int(min_scan_length)
            
            print(f"   ✅ Improved turning point: {turning_point}")
            print(f"   📊 Forward: {turning_point} points, Reverse: {len(voltage)-turning_point} points")
            
            return turning_point
        else:
            print(f"   ❌ No clear direction change found")
            return len(voltage) // 2
    
    def improved_peak_validation(self, voltage, current, peak_voltage, peak_current, peak_type):
        """การปรับปรุง peak validation"""
        print(f"🎯 Improved Peak Validation for {peak_type} at {peak_voltage:.3f}V:")
        
        validation_results = {
            'valid': True,
            'confidence': 100.0,
            'reasons': []
        }
        
        # Rule 1: Voltage range validation (based on ferrocyanide characteristics)
        if peak_type == 'oxidation':
            if peak_voltage < 0.0 or peak_voltage > 0.5:
                validation_results['valid'] = False
                validation_results['confidence'] *= 0.3
                validation_results['reasons'].append(f"OX peak voltage {peak_voltage:.3f}V outside expected range [0.0, 0.5]V")
        elif peak_type == 'reduction':
            if peak_voltage < -0.1 or peak_voltage > 0.3:
                validation_results['valid'] = False
                validation_results['confidence'] *= 0.3
                validation_results['reasons'].append(f"RED peak voltage {peak_voltage:.3f}V outside expected range [-0.1, 0.3]V")
        
        # Rule 2: Current magnitude validation
        current_range = current.max() - current.min()
        min_peak_height = current_range * 0.05  # อย่างน้อย 5% ของ current range
        
        baseline_estimate = np.median(current)  # Simple baseline estimate
        peak_height = abs(peak_current - baseline_estimate)
        
        if peak_height < min_peak_height:
            validation_results['valid'] = False
            validation_results['confidence'] *= 0.5
            validation_results['reasons'].append(f"Peak height {peak_height:.3f}µA too small (< {min_peak_height:.3f}µA)")
        
        # Rule 3: Signal-to-noise ratio
        current_noise = np.std(current)
        snr = peak_height / current_noise if current_noise > 0 else float('inf')
        
        if snr < 3.0:  # SNR should be at least 3
            validation_results['confidence'] *= 0.7
            validation_results['reasons'].append(f"Low SNR: {snr:.1f} (< 3.0)")
        
        # Rule 4: Peak isolation (ไม่ควรมี peak อื่นใกล้เกินไป)
        voltage_tolerance = 0.05  # 50 mV
        nearby_peaks = []
        
        # สมมติว่ามี list ของ peaks อื่นที่ตรวจพบแล้ว
        # (ใน implementation จริงต้องส่ง parameter เพิ่ม)
        
        print(f"   📊 Peak height: {peak_height:.3f}µA, SNR: {snr:.1f}")
        print(f"   🎯 Confidence: {validation_results['confidence']:.1f}%")
        
        if not validation_results['valid']:
            print(f"   ❌ INVALID: {', '.join(validation_results['reasons'])}")
        else:
            print(f"   ✅ VALID peak")
        
        return validation_results
    
    def baseline_peak_conflict_detection(self, voltage, current, baseline_indices, peak_positions):
        """ตรวจสอบการชนกันระหว่าง baseline และ peak"""
        print(f"🔍 Baseline-Peak Conflict Detection:")
        
        conflicts = []
        voltage_tolerance = 0.02  # 20 mV tolerance
        
        for peak in peak_positions:
            peak_voltage = peak['voltage']
            peak_type = peak['type']
            
            # หา baseline points ที่อยู่ใกล้ peak
            baseline_voltages = voltage[baseline_indices]
            nearby_baseline = np.abs(baseline_voltages - peak_voltage) < voltage_tolerance
            
            if np.any(nearby_baseline):
                conflict_info = {
                    'peak_voltage': peak_voltage,
                    'peak_type': peak_type,
                    'baseline_count': np.sum(nearby_baseline),
                    'conflict_severity': 'high' if np.sum(nearby_baseline) > 5 else 'low'
                }
                conflicts.append(conflict_info)
                
                print(f"   ⚠️ Conflict detected: {peak_type} peak at {peak_voltage:.3f}V has {conflict_info['baseline_count']} baseline points nearby")
        
        if len(conflicts) == 0:
            print(f"   ✅ No conflicts detected")
        else:
            print(f"   🚨 {len(conflicts)} conflicts found")
            
            # Suggest resolution
            for conflict in conflicts:
                if conflict['conflict_severity'] == 'high':
                    print(f"   💡 Suggestion: Remove baseline points near {conflict['peak_voltage']:.3f}V ({conflict['peak_type']} peak)")
                else:
                    print(f"   💡 Suggestion: Keep monitoring {conflict['peak_voltage']:.3f}V area")
        
        return conflicts
    
    def dynamic_threshold_calculation(self, current):
        """คำนวณ threshold แบบ dynamic ตาม SNR"""
        print(f"📊 Dynamic Threshold Calculation:")
        
        # Method 1: Percentile-based
        current_abs = np.abs(current)
        percentile_90 = np.percentile(current_abs, 90)
        percentile_50 = np.percentile(current_abs, 50)
        
        # Method 2: Noise-based
        noise_level = np.std(current)
        signal_level = np.max(current_abs)
        snr = signal_level / noise_level if noise_level > 0 else float('inf')
        
        # Dynamic prominence threshold
        if snr > 10:  # High SNR
            prominence_threshold = 0.05  # Low threshold - sensitive
        elif snr > 5:   # Medium SNR
            prominence_threshold = 0.1   # Medium threshold
        else:           # Low SNR
            prominence_threshold = 0.2   # High threshold - conservative
        
        # Dynamic width requirement
        width_threshold = max(3, int(len(current) * 0.02))  # At least 2% of data width
        
        thresholds = {
            'prominence': prominence_threshold,
            'width': width_threshold,
            'height': percentile_50 * 0.1,  # 10% of median
            'snr': snr,
            'noise_level': noise_level
        }
        
        print(f"   📈 SNR: {snr:.1f}")
        print(f"   🎯 Prominence threshold: {prominence_threshold:.2f}")
        print(f"   📏 Width threshold: {width_threshold} points")
        print(f"   📊 Height threshold: {thresholds['height']:.3f}µA")
        
        return thresholds
    
    def generate_improvement_summary(self):
        """สร้างสรุปข้อเสนอแนะ"""
        print(f"\n{'='*80}")
        print("📋 ALGORITHM IMPROVEMENT RECOMMENDATIONS")
        print(f"{'='*80}")
        
        print(f"\n🎯 Priority Improvements:")
        
        for i, issue in enumerate(self.issues_found, 1):
            print(f"\n{i}. **{issue['issue']}**")
            print(f"   📝 Description: {issue['description']}")
            print(f"   💥 Impact: {issue['impact']}")
            print(f"   💡 Solution: {issue['solution']}")
        
        print(f"\n🔧 Implementation Checklist:")
        checklist = [
            "[ ] Implement improved scan direction detection",
            "[ ] Add voltage range validation for peaks",
            "[ ] Implement baseline-peak conflict detection",
            "[ ] Add dynamic threshold calculation based on SNR",
            "[ ] Create peak isolation validation",
            "[ ] Add confidence scoring system",
            "[ ] Implement multi-pass validation",
            "[ ] Add user feedback integration"
        ]
        
        for item in checklist:
            print(f"   {item}")
        
        print(f"\n🎁 Expected Benefits:")
        benefits = [
            "Reduced false positive peaks",
            "Better baseline accuracy",
            "Improved performance on noisy data",
            "More robust scan direction detection",
            "Higher overall detection confidence"
        ]
        
        for benefit in benefits:
            print(f"   ✅ {benefit}")

def main():
    """Main demonstration function"""
    print("🚀 Algorithm Improvement Analysis")
    
    # สร้าง instance
    improvements = AlgorithmImprovements()
    
    # สาธิตการปรับปรุงด้วยข้อมูลตัวอย่าง
    print(f"\n📊 Demonstrating Improvements with Sample Data:")
    
    # สร้างข้อมูลตัวอย่าง
    voltage = np.linspace(-0.4, 0.7, 220)
    voltage = np.concatenate([voltage[:2], voltage[2:][::-1]])  # Simulate CV scan
    current = np.sin(voltage * 5) * 10 + np.random.normal(0, 1, len(voltage))
    
    print(f"   📈 Sample data: {len(voltage)} points")
    
    # 1. ปรับปรุงการหา scan direction
    turning_point = improvements.detect_scan_direction_improved(voltage)
    
    # 2. ทดสอบ peak validation
    test_peaks = [
        {'voltage': 0.2, 'current': 15.0, 'type': 'oxidation'},
        {'voltage': 0.8, 'current': 5.0, 'type': 'oxidation'},  # Should be invalid
        {'voltage': 0.1, 'current': -10.0, 'type': 'reduction'}
    ]
    
    for peak in test_peaks:
        improvements.improved_peak_validation(voltage, current, peak['voltage'], peak['current'], peak['type'])
    
    # 3. คำนวณ dynamic threshold
    thresholds = improvements.dynamic_threshold_calculation(current)
    
    # 4. สร้างสรุป
    improvements.generate_improvement_summary()

if __name__ == "__main__":
    main()
