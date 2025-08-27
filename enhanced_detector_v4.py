#!/usr/bin/env python3
"""
Enhanced Peak and Baseline Detector V4.0
แก้ไขปัญหาเฉพาะจากผลการทดสอบ:
- ปรับปรุงการตรวจจับ reduction peaks
- แก้ไข baseline detection 
- ปรับปรุงการตรวจจับใน low signal cases
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedDetectorV4:
    """
    Peak และ Baseline Detector เวอร์ชั่น 4.0
    แก้ไขปัญหาจากการทดสอบจริง
    """
    
    def __init__(self):
        self.confidence_threshold = 40.0  # ลดจาก 50 เพื่อให้ detect ได้ง่ายขึ้น
        
        # ปรับ voltage ranges ให้ครอบคลุมมากขึ้น
        self.ferrocyanide_ox_range = (-0.1, 0.8)    # ขยายช่วง OX
        self.ferrocyanide_red_range = (-0.4, 0.4)   # ขยายช่วง RED
        
        self.min_scan_ratio = 0.10  # ลดความเข้มงวด scan length
        
    def detect_scan_direction_v4(self, voltage):
        """
        ปรับปรุงการหา scan direction สำหรับ V4
        """
        logger.info("🔄 Enhanced V4 scan direction detection...")
        
        n = len(voltage)
        
        # Method 1: Simple range-based detection
        v_start = voltage[0]
        v_end = voltage[-1] 
        v_max = np.max(voltage)
        v_min = np.min(voltage)
        
        # หา turning point โดยใช้ voltage extremes
        max_idx = np.argmax(voltage)
        min_idx = np.argmin(voltage)
        
        # ถ้า max อยู่ก่อน min -> เริ่มจาก high ไป low แล้วกลับ
        # ถ้า min อยู่ก่อน max -> เริ่มจาก low ไป high แล้วกลับ
        
        if max_idx < min_idx:
            # Max มาก่อน -> แบบ high-to-low-to-high
            turning_point = min_idx
        else:
            # Min มาก่อน -> แบบ low-to-high-to-low  
            turning_point = max_idx
            
        # ตรวจสอบ turning point ให้สมเหตุสมผล
        if turning_point < n * 0.2:
            turning_point = int(n * 0.3)
        elif turning_point > n * 0.8:
            turning_point = int(n * 0.7)
            
        logger.info(f"✅ V4 Turning point: {turning_point} (Forward: {turning_point}, Reverse: {n - turning_point})")
        
        return {
            'turning_point': turning_point,
            'forward': (0, turning_point),
            'reverse': (turning_point, n)
        }
    
    def calculate_dynamic_thresholds_v4(self, current, scan_sections):
        """
        คำนวณ dynamic thresholds สำหรับ V4
        """
        logger.info("📊 V4 dynamic threshold calculation...")
        
        # ใช้ข้อมูลทั้งหมดในการคำนวณ baseline
        baseline_current = np.median(current)
        current_std = np.std(current)
        current_range = np.max(current) - np.min(current)
        
        # ลด threshold ให้ sensitive มากขึ้น
        prominence_threshold = max(
            current_std * 1.5,      # ลดจาก 2.0
            current_range * 0.03    # ลดจาก 0.05
        )
        
        height_threshold = max(
            current_std * 1.0,      # ลดจาก 1.5
            current_range * 0.02    # ลดจาก 0.03
        )
        
        # SNR calculation
        snr = current_range / current_std if current_std > 0 else 10.0
        
        # Width - ให้ยืดหยุ่นขึ้น
        width = max(2, min(8, len(current) // 30))  # ลดขนาด
        
        logger.info(f"📈 V4 SNR: {snr:.1f}, Prominence: {prominence_threshold:.3f}, Width: {width}")
        
        return {
            'prominence': prominence_threshold,
            'height': height_threshold,
            'width': width,
            'snr': snr,
            'baseline': baseline_current
        }
    
    def validate_peak_v4(self, peak_voltage, peak_current, peak_type, current, baseline_current=None):
        """
        V4 peak validation - ยืดหยุ่นขึ้น
        """
        validation_score = 100.0
        issues = []
        
        # 1. Voltage range validation - ใช้ช่วงกว้างขึ้น
        if peak_type == 'oxidation':
            if not (self.ferrocyanide_ox_range[0] <= peak_voltage <= self.ferrocyanide_ox_range[1]):
                validation_score *= 0.4  # penalty น้อยลง
                issues.append(f"OX voltage {peak_voltage:.3f}V outside range {self.ferrocyanide_ox_range}")
        elif peak_type == 'reduction':
            if not (self.ferrocyanide_red_range[0] <= peak_voltage <= self.ferrocyanide_red_range[1]):
                validation_score *= 0.4  # penalty น้อยลง
                issues.append(f"RED voltage {peak_voltage:.3f}V outside range {self.ferrocyanide_red_range}")
        
        # 2. Current direction validation - ยืดหยุ่นขึ้น
        baseline_ref = baseline_current if baseline_current is not None else np.median(current)
        
        if peak_type == 'oxidation':
            if peak_current < baseline_ref:
                validation_score *= 0.7  # penalty น้อยลง
                issues.append(f"OX current {peak_current:.3f}µA below baseline {baseline_ref:.3f}µA")
        elif peak_type == 'reduction':
            if peak_current > baseline_ref:
                validation_score *= 0.7  # penalty น้อยลง
                issues.append(f"RED current {peak_current:.3f}µA above baseline {baseline_ref:.3f}µA")
        
        # 3. Peak height validation - ปรับให้เหมาะสม
        peak_height = abs(peak_current - baseline_ref)
        current_range = np.max(current) - np.min(current)
        min_height = current_range * 0.01  # ลดจาก 0.03
        
        if peak_height < min_height:
            validation_score *= 0.6  # penalty น้อยลง
            issues.append(f"Peak height {peak_height:.3f}µA small")
        
        # 4. SNR validation - ยืดหยุ่นขึ้น
        noise_level = np.std(current)
        snr = peak_height / noise_level if noise_level > 0 else float('inf')
        
        if snr < 2.0:
            validation_score *= 0.8  # penalty น้อยลง
            issues.append(f"Low SNR: {snr:.1f}")
        
        is_valid = validation_score >= self.confidence_threshold
        
        return {
            'valid': is_valid,
            'confidence': validation_score,
            'issues': issues,
            'snr': snr,
            'peak_height': peak_height
        }
    
    def detect_baseline_v4(self, voltage, current, peak_positions=None):
        """
        V4 baseline detection - แบบ adaptive มากขึ้น
        """
        logger.info("📏 V4 Enhanced baseline detection...")
        
        # 1. หาจุดที่มี variation ต่ำ
        window_size = max(3, len(current) // 30)  # ลดขนาด window
        
        # ใช้ moving average แทน gradient
        current_smooth = np.convolve(current, np.ones(window_size)/window_size, mode='same')
        variation = np.abs(current - current_smooth)
        
        # ใช้ percentile ที่ยืดหยุ่นขึ้น
        variation_threshold = np.percentile(variation, 40)  # เพิ่มจาก 25%
        stable_mask = variation <= variation_threshold
        
        # 2. Remove points near peaks (ถ้ามี)
        if peak_positions:
            voltage_tolerance = 0.05  # เพิ่ม tolerance
            
            for peak in peak_positions:
                peak_mask = np.abs(voltage - peak['voltage']) < voltage_tolerance
                stable_mask = stable_mask & ~peak_mask
                excluded_count = np.sum(peak_mask)
                if excluded_count > 0:
                    logger.info(f"Excluded {excluded_count} points near peak at {peak['voltage']:.3f}V")
        
        # 3. แบ่ง baseline ตาม voltage regions
        baseline_indices = np.where(stable_mask)[0]
        
        if len(baseline_indices) < 5:
            # ถ้าหา baseline ไม่ได้ ใช้ percentile method
            logger.info("Using percentile fallback for baseline")
            low_percentile = np.percentile(current, 25)
            high_percentile = np.percentile(current, 75)
            
            # หาจุดที่อยู่ใกล้ percentiles
            low_mask = np.abs(current - low_percentile) < np.std(current) * 0.5
            high_mask = np.abs(current - high_percentile) < np.std(current) * 0.5
            baseline_mask = low_mask | high_mask
            baseline_indices = np.where(baseline_mask)[0]
        
        # 4. สร้าง baseline regions
        baseline_info = []
        
        if len(baseline_indices) > 0:
            # แบ่งเป็น regions ตาม voltage
            v_low = np.percentile(voltage[baseline_indices], 33)
            v_high = np.percentile(voltage[baseline_indices], 67)
            
            low_region = baseline_indices[voltage[baseline_indices] <= v_low]
            mid_region = baseline_indices[(voltage[baseline_indices] > v_low) & (voltage[baseline_indices] < v_high)]
            high_region = baseline_indices[voltage[baseline_indices] >= v_high]
            
            for region_name, region_indices in [("Low", low_region), ("Mid", mid_region), ("High", high_region)]:
                if len(region_indices) >= 3:  # ลดความเข้มงวด
                    region_current = current[region_indices]
                    region_mean = np.mean(region_current)
                    region_std = np.std(region_current)
                    
                    baseline_info.append({
                        'name': region_name,
                        'indices': region_indices.tolist(),
                        'mean_current': region_mean,
                        'std_current': region_std,
                        'count': len(region_indices)
                    })
                    
                    logger.info(f"📊 {region_name} baseline: {region_mean:.3f} ± {region_std:.3f} µA ({len(region_indices)} points)")
        
        logger.info(f"🎯 Total baseline regions: {len(baseline_info)}, Total points: {len(baseline_indices)}")
        
        return {
            'indices': baseline_indices.tolist(),
            'regions': baseline_info,
            'quality': min(1.0, len(baseline_indices) / (len(current) * 0.3))
        }
    
    def detect_peaks_enhanced_v4(self, voltage, current):
        """
        Enhanced peak detection V4 - main method
        """
        logger.info("🎯 Enhanced V4 peak detection starting...")
        
        voltage = np.array(voltage)
        current = np.array(current)
        
        # 1. Scan direction detection
        scan_sections = self.detect_scan_direction_v4(voltage)
        
        # 2. Dynamic thresholds
        thresholds = self.calculate_dynamic_thresholds_v4(current, scan_sections)
        
        # 3. Peak detection with multiple methods
        peaks = self._detect_peaks_v4(voltage, current, thresholds, scan_sections)
        
        # 4. Baseline detection
        baseline_result = self.detect_baseline_v4(voltage, current, peaks)
        
        # 5. Final validation and formatting
        final_peaks = []
        rejected_peaks = []
        
        for peak in peaks:
            validation = self.validate_peak_v4(
                peak['voltage'], peak['current'], peak['type'], current, thresholds['baseline']
            )
            
            if validation['valid']:
                peak['confidence'] = validation['confidence']
                final_peaks.append(peak)
                logger.info(f"✅ Valid {peak['type'][:3].upper()} peak: {peak['voltage']:.3f}V, {peak['current']:.1f}µA, conf={validation['confidence']:.0f}%")
            else:
                peak['confidence'] = validation['confidence']
                peak['rejection_reason'] = ', '.join(validation['issues'])
                rejected_peaks.append(peak)
                logger.info(f"❌ Invalid {peak['type'][:3].upper()} peak: {peak['voltage']:.3f}V - {peak['rejection_reason']}")
        
        logger.info(f"🎯 V4 Final results: {len(final_peaks)} valid peaks, {len(baseline_result['indices'])} baseline points")
        
        return {
            'peaks': final_peaks,
            'rejected_peaks': rejected_peaks,
            'baseline_indices': baseline_result['indices'],
            'baseline_info': baseline_result['regions'],
            'enhanced_results': {
                'version': 'V4.0',
                'scan_sections': scan_sections,
                'thresholds': thresholds,
                'baseline_quality': baseline_result['quality'],
                'total_detected': len(peaks),
                'validation_passed': len(final_peaks)
            }
        }
    
    def _detect_peaks_v4(self, voltage, current, thresholds, scan_sections):
        """
        V4 peak detection with improved sensitivity
        """
        logger.info("🔍 V4 peak detection...")
        
        peaks = []
        
        # ใช้ scipy ถ้ามี หรือ fallback ไป simple method
        try:
            from scipy.signal import find_peaks
            
            # หา oxidation peaks (positive direction)
            ox_peaks, ox_properties = find_peaks(
                current, 
                prominence=thresholds['prominence'] * 0.7,  # ลด threshold
                width=max(1, thresholds['width'] - 1),      # ลด width requirement
                height=thresholds['baseline'] + thresholds['height'] * 0.5  # ลด height requirement
            )
            
            # หา reduction peaks (negative direction)
            red_peaks, red_properties = find_peaks(
                -current,  # invert สำหรับ reduction
                prominence=thresholds['prominence'] * 0.7,  # ลด threshold
                width=max(1, thresholds['width'] - 1),      # ลด width requirement
                height=-(thresholds['baseline'] - thresholds['height'] * 0.5)  # ปรับ height
            )
            
            logger.info(f"🔍 V4 Raw detection: {len(ox_peaks)} OX candidates, {len(red_peaks)} RED candidates")
            
        except ImportError:
            logger.info("🔧 Using V4 simple detection (scipy not available)")
            ox_peaks, red_peaks = self._simple_peak_detection_v4(current, thresholds)
        
        # จัดรูปแบบ peaks
        for idx in ox_peaks:
            if 0 <= idx < len(voltage):
                peaks.append({
                    'voltage': voltage[idx],
                    'current': current[idx],
                    'type': 'oxidation',
                    'index': int(idx)
                })
        
        for idx in red_peaks:
            if 0 <= idx < len(voltage):
                peaks.append({
                    'voltage': voltage[idx],
                    'current': current[idx],
                    'type': 'reduction',
                    'index': int(idx)
                })
        
        return peaks
    
    def _simple_peak_detection_v4(self, current, thresholds):
        """
        V4 Simple peak detection fallback
        """
        ox_peaks = []
        red_peaks = []
        
        width = max(1, thresholds['width'] - 1)  # ลด width requirement
        
        # หา local maxima สำหรับ oxidation (ปรับให้ sensitive ขึ้น)
        for i in range(width, len(current) - width):
            left_window = current[i-width:i]
            right_window = current[i+1:i+width+1]
            
            if len(left_window) > 0 and len(right_window) > 0:
                left_max = np.max(left_window)
                right_max = np.max(right_window)
                
                # ลด requirement ให้ detect ง่ายขึ้น
                if (current[i] > left_max * 0.95 and current[i] > right_max * 0.95 and
                    current[i] > thresholds['baseline'] + thresholds['height'] * 0.3):  # ลด threshold
                    ox_peaks.append(i)
        
        # หา local minima สำหรับ reduction (ปรับให้ sensitive ขึ้น)
        for i in range(width, len(current) - width):
            left_window = current[i-width:i]
            right_window = current[i+1:i+width+1]
            
            if len(left_window) > 0 and len(right_window) > 0:
                left_min = np.min(left_window)
                right_min = np.min(right_window)
                
                # ลด requirement ให้ detect ง่ายขึ้น
                if (current[i] < left_min * 1.05 and current[i] < right_min * 1.05 and
                    current[i] < thresholds['baseline'] - thresholds['height'] * 0.3):  # ลด threshold
                    red_peaks.append(i)
        
        return np.array(ox_peaks), np.array(red_peaks)

# Test function
def test_enhanced_v4(file_path):
    """
    ทดสอบ Enhanced V4 detector
    """
    print(f"🧪 Testing Enhanced V4 with: {file_path}")
    
    try:
        detector = EnhancedDetectorV4()
        
        # โหลดข้อมูล
        df = pd.read_csv(file_path, skiprows=1)
        voltage = df['V'].values
        current = df['uA'].values
        
        print(f"📊 Data: {len(voltage)} points, V: {voltage.min():.3f} to {voltage.max():.3f}V")
        print(f"⚡ Current: {current.min():.3f} to {current.max():.3f}µA")
        
        # ทำการ detect
        results = detector.detect_peaks_enhanced_v4(voltage, current)
        
        # แสดงผล
        peaks = results['peaks']
        rejected = results['rejected_peaks']
        
        print(f"\n🎯 V4 RESULTS:")
        print(f"✅ Valid peaks: {len(peaks)}")
        print(f"❌ Rejected peaks: {len(rejected)}")
        
        ox_count = len([p for p in peaks if p['type'] == 'oxidation'])
        red_count = len([p for p in peaks if p['type'] == 'reduction'])
        print(f"   OX: {ox_count}, RED: {red_count}")
        
        for i, peak in enumerate(peaks):
            print(f"   Peak {i+1}: {peak['type'][:3].upper()} at {peak['voltage']:.3f}V, {peak['current']:.2f}µA, conf={peak.get('confidence', 0):.0f}%")
            
        return results
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None

if __name__ == "__main__":
    # ทดสอบด้วยไฟล์ตัวอย่าง
    test_files = [
        "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_100mVpS_E5_scan_02.csv",
        "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_200mVpS_E2_scan_01.csv",
        "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_20mVpS_E1_scan_02.csv"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print("=" * 60)
            test_enhanced_v4(test_file)
            print()
        else:
            print(f"❌ File not found: {test_file}")
