#!/usr/bin/env python3
"""
Enhanced Peak and Baseline Detector V5.0
แก้ไขปัญหาสำคัญจาก V4:
- แก้ไข RED peak detection ที่ล้มเหลวทั้งหมด
- ปรับปรุง baseline fitting ให้ถูกต้อง
- ลด peak validation ที่เข้มงวดเกินไป
- เพิ่ม adaptive thresholding
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

class EnhancedDetectorV5:
    """
    Peak และ Baseline Detector เวอร์ชั่น 5.0
    แก้ไขปัญหา RED peak detection และ baseline fitting
    """
    
    def __init__(self):
        self.confidence_threshold = 30.0  # ลดอีกเพื่อให้ detect ได้ง่ายขึ้น
        
        # ปรับ voltage ranges ให้เฉพาะเจาะจงสำหรับ ferrocyanide
        self.ferrocyanide_ox_range = (0.0, 0.8)     # Oxidation ที่ positive voltage
        self.ferrocyanide_red_range = (-0.3, 0.2)   # Reduction ที่ negative voltage
        
        self.min_scan_ratio = 0.05  # ลดความเข้มงวดเพิ่มเติม
        
    def detect_scan_direction_v5(self, voltage):
        """
        ปรับปรุงการหา scan direction สำหรับ V5
        ใช้ gradient analysis แทน simple range
        """
        logger.info("🔄 Enhanced V5 scan direction detection...")
        
        n = len(voltage)
        
        # คำนวณ gradient เพื่อหา turning point
        voltage_diff = np.diff(voltage)
        
        # หา sign changes ใน gradient
        sign_changes = np.where(np.diff(np.sign(voltage_diff)))[0]
        
        # ถ้าไม่เจอ sign changes หรือน้อยเกินไป ใช้ extreme point
        if len(sign_changes) == 0:
            max_idx = np.argmax(voltage)
            min_idx = np.argmin(voltage)
            turning_point = max_idx if max_idx < min_idx else min_idx
        else:
            # ใช้ sign change ที่อยู่ตรงกลางที่สุด
            turning_point = sign_changes[len(sign_changes)//2] + 1
            
        # Sanity check
        if turning_point < n * 0.1:
            turning_point = int(n * 0.3)
        elif turning_point > n * 0.9:
            turning_point = int(n * 0.7)
            
        logger.info(f"✅ V5 Turning point: {turning_point} (Forward: {turning_point}, Reverse: {n - turning_point})")
        
        return {
            'turning_point': turning_point,
            'forward': (0, turning_point),
            'reverse': (turning_point, n)
        }
    
    def calculate_adaptive_thresholds_v5(self, current, voltage, scan_sections):
        """
        Adaptive threshold calculation สำหรับ V5
        คำนวณ threshold แยกสำหรับแต่ละ voltage region
        """
        logger.info("📊 V5 adaptive threshold calculation...")
        
        # หา baseline จาก stable regions
        baseline_current = self._estimate_baseline_current(current, voltage)
        current_std = np.std(current)
        current_range = np.max(current) - np.min(current)
        
        # Adaptive thresholding ตาม signal characteristics
        if current_range < 1.0:  # Low signal
            prominence_factor = 0.5
            height_factor = 0.3
            width_factor = 0.8
        elif current_range < 10.0:  # Medium signal
            prominence_factor = 0.7
            height_factor = 0.5
            width_factor = 1.0
        else:  # High signal
            prominence_factor = 1.0
            height_factor = 0.7
            width_factor = 1.2
        
        # Calculate thresholds
        prominence_threshold = max(
            current_std * 1.0 * prominence_factor,
            current_range * 0.02 * prominence_factor
        )
        
        height_threshold = max(
            current_std * 0.8 * height_factor,
            current_range * 0.015 * height_factor
        )
        
        # Width based on data density
        width = max(1, int(len(current) / 50 * width_factor))
        
        # SNR calculation
        snr = current_range / current_std if current_std > 0 else 10.0
        
        logger.info(f"📈 V5 SNR: {snr:.1f}, Prominence: {prominence_threshold:.3f}, Height: {height_threshold:.3f}, Width: {width}")
        
        return {
            'prominence': prominence_threshold,
            'height': height_threshold,
            'width': width,
            'snr': snr,
            'baseline': baseline_current,
            'current_range': current_range
        }
    
    def _estimate_baseline_current(self, current, voltage):
        """
        ประมาณ baseline current จาก voltage regions ที่ไม่มี peaks
        """
        # หา voltage regions ที่ baseline น่าจะอยู่
        # โดยทั่วไปจะอยู่ที่ voltage ที่ไม่มี redox reaction
        
        v_min, v_max = np.min(voltage), np.max(voltage)
        v_range = v_max - v_min
        
        # Baseline regions: ปลายทั้งสองด้าน และตรงกลาง (ถ้าไม่มี reaction)
        baseline_regions = []
        
        # ปลายซ้าย (negative voltage)
        left_mask = voltage <= (v_min + v_range * 0.2)
        if np.sum(left_mask) > 5:
            baseline_regions.extend(current[left_mask])
            
        # ปลายขวา (positive voltage สูง)
        right_mask = voltage >= (v_max - v_range * 0.2)
        if np.sum(right_mask) > 5:
            baseline_regions.extend(current[right_mask])
        
        if len(baseline_regions) > 0:
            return np.median(baseline_regions)
        else:
            return np.median(current)
    
    def validate_peak_v5(self, peak_voltage, peak_current, peak_type, current, voltage, thresholds):
        """
        V5 peak validation - ลด penalty และเพิ่ม context awareness
        """
        validation_score = 100.0
        issues = []
        baseline_current = thresholds['baseline']
        
        # 1. Voltage range validation - ใช้ adaptive ranges
        if peak_type == 'oxidation':
            if not (self.ferrocyanide_ox_range[0] <= peak_voltage <= self.ferrocyanide_ox_range[1]):
                validation_score *= 0.6  # penalty น้อยลงอีก
                issues.append(f"OX voltage {peak_voltage:.3f}V outside range {self.ferrocyanide_ox_range}")
        elif peak_type == 'reduction':
            if not (self.ferrocyanide_red_range[0] <= peak_voltage <= self.ferrocyanide_red_range[1]):
                validation_score *= 0.6  # penalty น้อยลงอีก
                issues.append(f"RED voltage {peak_voltage:.3f}V outside range {self.ferrocyanide_red_range}")
        
        # 2. Current direction validation - ใช้ local context
        local_baseline = self._get_local_baseline(peak_voltage, voltage, current)
        
        if peak_type == 'oxidation':
            if peak_current <= local_baseline:
                validation_score *= 0.8  # penalty น้อยลงอีก
                issues.append(f"OX current {peak_current:.3f}µA not above local baseline {local_baseline:.3f}µA")
        elif peak_type == 'reduction':
            if peak_current >= local_baseline:
                validation_score *= 0.8  # penalty น้อยลงอีก
                issues.append(f"RED current {peak_current:.3f}µA not below local baseline {local_baseline:.3f}µA")
        
        # 3. Peak height validation - adaptive based on signal range
        peak_height = abs(peak_current - local_baseline)
        min_height = thresholds['current_range'] * 0.005  # ลดเป็น 0.5%
        
        if peak_height < min_height:
            validation_score *= 0.7  # penalty น้อยลง
            issues.append(f"Peak height {peak_height:.3f}µA too small")
        
        # 4. SNR validation - ยืดหยุ่นขึ้น
        noise_level = np.std(current)
        snr = peak_height / noise_level if noise_level > 0 else float('inf')
        
        if snr < 1.5:  # ลดจาก 2.0
            validation_score *= 0.9  # penalty น้อยลง
            issues.append(f"Low SNR: {snr:.1f}")
        
        # 5. Peak shape validation - เช็คว่าเป็น peak จริง
        shape_score = self._validate_peak_shape(peak_voltage, voltage, current)
        validation_score *= shape_score
        
        if shape_score < 0.8:
            issues.append(f"Poor peak shape (score: {shape_score:.2f})")
        
        is_valid = validation_score >= self.confidence_threshold
        
        return {
            'valid': is_valid,
            'confidence': validation_score,
            'issues': issues,
            'snr': snr,
            'peak_height': peak_height,
            'shape_score': shape_score
        }
    
    def _get_local_baseline(self, peak_voltage, voltage, current):
        """
        หา local baseline รอบ ๆ peak
        """
        # หาจุดที่อยู่ห่างจาก peak voltage
        distance = np.abs(voltage - peak_voltage)
        
        # ใช้จุดที่ห่างมากกว่า 0.1V เป็น baseline reference
        baseline_mask = distance > 0.1
        
        if np.sum(baseline_mask) > 5:
            return np.median(current[baseline_mask])
        else:
            return np.median(current)
    
    def _validate_peak_shape(self, peak_voltage, voltage, current):
        """
        ตรวจสอบ shape ของ peak ว่าเป็น peak จริงหรือไม่
        """
        # หา index ของ peak
        peak_idx = np.argmin(np.abs(voltage - peak_voltage))
        
        # ตรวจสอบรอบ ๆ peak
        window = 5
        start_idx = max(0, peak_idx - window)
        end_idx = min(len(current), peak_idx + window + 1)
        
        if end_idx - start_idx < 3:
            return 0.5  # ข้อมูลไม่พอ
        
        window_current = current[start_idx:end_idx]
        center_idx = peak_idx - start_idx
        
        if center_idx < 0 or center_idx >= len(window_current):
            return 0.5
        
        # เช็คว่า peak อยู่ที่จุดสูงสุดหรือต่ำสุดใน window
        is_max = window_current[center_idx] == np.max(window_current)
        is_min = window_current[center_idx] == np.min(window_current)
        
        if is_max or is_min:
            return 1.0
        else:
            # คำนวณ score ตาม relative position
            max_val = np.max(window_current)
            min_val = np.min(window_current)
            peak_val = window_current[center_idx]
            
            if max_val == min_val:
                return 0.5
            
            # Normalize peak position in range
            normalized_pos = (peak_val - min_val) / (max_val - min_val)
            
            # Score based on how close to extreme
            return max(0.3, min(abs(normalized_pos), abs(1 - normalized_pos)) * 2)
    
    def detect_baseline_v5(self, voltage, current, peak_positions=None):
        """
        V5 baseline detection - ใช้ voltage-based segmentation
        """
        logger.info("📏 V5 Enhanced baseline detection...")
        
        # 1. แบ่ง voltage เป็น regions
        v_min, v_max = np.min(voltage), np.max(voltage)
        v_range = v_max - v_min
        
        # แบ่งเป็น 5 regions
        regions = []
        for i in range(5):
            v_start = v_min + (i * v_range / 5)
            v_end = v_min + ((i + 1) * v_range / 5)
            region_mask = (voltage >= v_start) & (voltage < v_end)
            
            if i == 4:  # last region
                region_mask = (voltage >= v_start) & (voltage <= v_end)
            
            regions.append({
                'mask': region_mask,
                'v_range': (v_start, v_end),
                'name': f"Region_{i+1}"
            })
        
        # 2. สำหรับแต่ละ region หา baseline candidates
        baseline_indices = []
        baseline_info = []
        
        for region in regions:
            if np.sum(region['mask']) < 3:
                continue
                
            region_current = current[region['mask']]
            region_indices = np.where(region['mask'])[0]
            
            # หา stable points ใน region นี้
            if len(region_current) >= 5:
                # ใช้ percentile เพื่อหา stable range
                p25 = np.percentile(region_current, 25)
                p75 = np.percentile(region_current, 75)
                iqr = p75 - p25
                
                # หาจุดที่อยู่ใกล้ median
                region_median = np.median(region_current)
                stable_threshold = max(iqr * 0.5, np.std(region_current) * 0.3)
                
                stable_mask = np.abs(region_current - region_median) <= stable_threshold
                stable_indices = region_indices[stable_mask]
                
                if len(stable_indices) >= 2:
                    baseline_indices.extend(stable_indices)
                    
                    baseline_info.append({
                        'name': region['name'],
                        'voltage_range': region['v_range'],
                        'indices': stable_indices.tolist(),
                        'mean_current': np.mean(current[stable_indices]),
                        'std_current': np.std(current[stable_indices]),
                        'count': len(stable_indices)
                    })
                    
                    logger.info(f"📊 {region['name']} [{region['v_range'][0]:.2f}, {region['v_range'][1]:.2f}]V: "
                              f"{np.mean(current[stable_indices]):.3f} ± {np.std(current[stable_indices]):.3f} µA "
                              f"({len(stable_indices)} points)")
        
        # 3. Remove points near detected peaks
        if peak_positions:
            voltage_tolerance = 0.03  # ลด tolerance
            original_count = len(baseline_indices)
            
            for peak in peak_positions:
                peak_mask = np.abs(voltage[baseline_indices] - peak['voltage']) < voltage_tolerance
                baseline_indices = [idx for i, idx in enumerate(baseline_indices) if not peak_mask[i]]
            
            removed_count = original_count - len(baseline_indices)
            if removed_count > 0:
                logger.info(f"🚫 Removed {removed_count} baseline points near peaks")
        
        logger.info(f"🎯 Total baseline regions: {len(baseline_info)}, Total points: {len(baseline_indices)}")
        
        return {
            'indices': baseline_indices,
            'regions': baseline_info,
            'quality': min(1.0, len(baseline_indices) / (len(current) * 0.25))
        }
    
    def detect_peaks_enhanced_v5(self, voltage, current):
        """
        Enhanced peak detection V5 - main method
        """
        logger.info("🎯 Enhanced V5 peak detection starting...")
        
        voltage = np.array(voltage)
        current = np.array(current)
        
        # 1. Scan direction detection
        scan_sections = self.detect_scan_direction_v5(voltage)
        
        # 2. Adaptive thresholds
        thresholds = self.calculate_adaptive_thresholds_v5(current, voltage, scan_sections)
        
        # 3. Multi-method peak detection
        peaks = self._detect_peaks_v5(voltage, current, thresholds, scan_sections)
        
        # 4. Baseline detection (ใช้ข้อมูล peaks เบื้องต้น)
        baseline_result = self.detect_baseline_v5(voltage, current, peaks)
        
        # 5. Final validation และจัดรูปแบบ
        final_peaks = []
        rejected_peaks = []
        
        for peak in peaks:
            validation = self.validate_peak_v5(
                peak['voltage'], peak['current'], peak['type'], current, voltage, thresholds
            )
            
            if validation['valid']:
                peak['confidence'] = validation['confidence']
                peak['shape_score'] = validation['shape_score']
                final_peaks.append(peak)
                logger.info(f"✅ Valid {peak['type'][:3].upper()} peak: {peak['voltage']:.3f}V, "
                          f"{peak['current']:.1f}µA, conf={validation['confidence']:.0f}%, "
                          f"shape={validation['shape_score']:.2f}")
            else:
                peak['confidence'] = validation['confidence']
                peak['rejection_reason'] = ', '.join(validation['issues'])
                rejected_peaks.append(peak)
                logger.info(f"❌ Invalid {peak['type'][:3].upper()} peak: {peak['voltage']:.3f}V - {peak['rejection_reason']}")
        
        # 6. ปรับปรุง baseline หลังจากมี final peaks
        final_baseline = self.detect_baseline_v5(voltage, current, final_peaks)
        
        logger.info(f"🎯 V5 Final results: {len(final_peaks)} valid peaks, {len(final_baseline['indices'])} baseline points")
        
        return {
            'peaks': final_peaks,
            'rejected_peaks': rejected_peaks,
            'baseline_indices': final_baseline['indices'],
            'baseline_info': final_baseline['regions'],
            'enhanced_results': {
                'version': 'V5.0',
                'scan_sections': scan_sections,
                'thresholds': thresholds,
                'baseline_quality': final_baseline['quality'],
                'total_detected': len(peaks),
                'validation_passed': len(final_peaks),
                'adaptive_factors': {
                    'current_range': thresholds['current_range'],
                    'snr': thresholds['snr']
                }
            }
        }
    
    def _detect_peaks_v5(self, voltage, current, thresholds, scan_sections):
        """
        V5 peak detection with enhanced RED peak detection
        """
        logger.info("🔍 V5 peak detection with enhanced RED sensitivity...")
        
        peaks = []
        
        # ใช้ scipy ถ้ามี
        try:
            from scipy.signal import find_peaks
            
            # Method 1: Standard peak detection
            ox_peaks_1, _ = find_peaks(
                current, 
                prominence=thresholds['prominence'] * 0.5,  # ลดอีก
                width=max(1, thresholds['width'] - 2),      # ลด width มากขึ้น
                height=thresholds['baseline'] + thresholds['height'] * 0.3
            )
            
            red_peaks_1, _ = find_peaks(
                -current,  # invert สำหรับ reduction
                prominence=thresholds['prominence'] * 0.5,  # ลดอีก
                width=max(1, thresholds['width'] - 2),      
                height=-(thresholds['baseline'] - thresholds['height'] * 0.3)
            )
            
            # Method 2: Local extrema detection (สำหรับ RED peaks)
            ox_peaks_2, red_peaks_2 = self._local_extrema_detection_v5(voltage, current, thresholds)
            
            # Method 3: Gradient-based detection
            ox_peaks_3, red_peaks_3 = self._gradient_based_detection_v5(voltage, current, thresholds)
            
            # รวม peaks จากทุก methods
            all_ox_peaks = list(set(list(ox_peaks_1) + list(ox_peaks_2) + list(ox_peaks_3)))
            all_red_peaks = list(set(list(red_peaks_1) + list(red_peaks_2) + list(red_peaks_3)))
            
            logger.info(f"🔍 V5 Combined detection: {len(all_ox_peaks)} OX candidates, {len(all_red_peaks)} RED candidates")
            
        except ImportError:
            logger.info("🔧 Using V5 simple detection (scipy not available)")
            all_ox_peaks, all_red_peaks = self._simple_peak_detection_v5(voltage, current, thresholds)
        
        # จัดรูปแบบ peaks
        for idx in all_ox_peaks:
            if 0 <= idx < len(voltage):
                peaks.append({
                    'voltage': voltage[idx],
                    'current': current[idx],
                    'type': 'oxidation',
                    'index': int(idx)
                })
        
        for idx in all_red_peaks:
            if 0 <= idx < len(voltage):
                peaks.append({
                    'voltage': voltage[idx],
                    'current': current[idx],
                    'type': 'reduction',
                    'index': int(idx)
                })
        
        return peaks
    
    def _local_extrema_detection_v5(self, voltage, current, thresholds):
        """
        หา local extrema ด้วย sliding window
        """
        ox_peaks = []
        red_peaks = []
        
        window = max(2, thresholds['width'] // 2)
        
        for i in range(window, len(current) - window):
            left_data = current[i-window:i]
            right_data = current[i+1:i+window+1]
            center_value = current[i]
            
            # Local maximum (oxidation)
            if (len(left_data) > 0 and len(right_data) > 0 and
                center_value > np.max(left_data) and center_value > np.max(right_data)):
                
                # เช็ค voltage range
                if self.ferrocyanide_ox_range[0] <= voltage[i] <= self.ferrocyanide_ox_range[1]:
                    ox_peaks.append(i)
            
            # Local minimum (reduction)
            if (len(left_data) > 0 and len(right_data) > 0 and
                center_value < np.min(left_data) and center_value < np.min(right_data)):
                
                # เช็ค voltage range
                if self.ferrocyanide_red_range[0] <= voltage[i] <= self.ferrocyanide_red_range[1]:
                    red_peaks.append(i)
        
        return np.array(ox_peaks), np.array(red_peaks)
    
    def _gradient_based_detection_v5(self, voltage, current, thresholds):
        """
        หา peaks ด้วย gradient analysis
        """
        ox_peaks = []
        red_peaks = []
        
        # คำนวณ gradients
        current_grad = np.gradient(current)
        
        # หา zero crossings ใน gradient
        grad_sign = np.sign(current_grad)
        grad_changes = np.where(np.diff(grad_sign))[0]
        
        for idx in grad_changes:
            if idx < 1 or idx >= len(current) - 1:
                continue
                
            # เช็คว่าเป็น peak หรือ valley
            before_grad = current_grad[idx]
            after_grad = current_grad[idx + 1]
            
            # Peak (gradient เปลี่ยนจาก + เป็น -)
            if before_grad > 0 and after_grad < 0:
                if self.ferrocyanide_ox_range[0] <= voltage[idx] <= self.ferrocyanide_ox_range[1]:
                    # เช็ค magnitude
                    if current[idx] > thresholds['baseline'] + thresholds['height'] * 0.2:
                        ox_peaks.append(idx)
            
            # Valley (gradient เปลี่ยนจาก - เป็น +)
            elif before_grad < 0 and after_grad > 0:
                if self.ferrocyanide_red_range[0] <= voltage[idx] <= self.ferrocyanide_red_range[1]:
                    # เช็ค magnitude
                    if current[idx] < thresholds['baseline'] - thresholds['height'] * 0.2:
                        red_peaks.append(idx)
        
        return np.array(ox_peaks), np.array(red_peaks)
    
    def _simple_peak_detection_v5(self, voltage, current, thresholds):
        """
        V5 Simple peak detection fallback with enhanced RED detection
        """
        ox_peaks = []
        red_peaks = []
        
        width = max(1, thresholds['width'] - 2)
        
        for i in range(width, len(current) - width):
            window_left = current[i-width:i]
            window_right = current[i+1:i+width+1]
            
            if len(window_left) == 0 or len(window_right) == 0:
                continue
            
            # Oxidation peaks
            if (current[i] >= np.max(window_left) and current[i] >= np.max(window_right) and
                self.ferrocyanide_ox_range[0] <= voltage[i] <= self.ferrocyanide_ox_range[1] and
                current[i] > thresholds['baseline'] + thresholds['height'] * 0.2):
                ox_peaks.append(i)
            
            # Reduction peaks
            if (current[i] <= np.min(window_left) and current[i] <= np.min(window_right) and
                self.ferrocyanide_red_range[0] <= voltage[i] <= self.ferrocyanide_red_range[1] and
                current[i] < thresholds['baseline'] - thresholds['height'] * 0.2):
                red_peaks.append(i)
        
        return np.array(ox_peaks), np.array(red_peaks)

# Test function
def test_enhanced_v5(file_path):
    """
    ทดสอบ Enhanced V5 detector
    """
    print(f"🧪 Testing Enhanced V5 with: {file_path}")
    
    try:
        detector = EnhancedDetectorV5()
        
        # โหลดข้อมูล
        df = pd.read_csv(file_path, skiprows=1)
        voltage = df['V'].values
        current = df['uA'].values
        
        print(f"📊 Data: {len(voltage)} points, V: {voltage.min():.3f} to {voltage.max():.3f}V")
        print(f"⚡ Current: {current.min():.3f} to {current.max():.3f}µA")
        
        # ทำการ detect
        results = detector.detect_peaks_enhanced_v5(voltage, current)
        
        # แสดงผล
        peaks = results['peaks']
        rejected = results['rejected_peaks']
        
        print(f"\n🎯 V5 RESULTS:")
        print(f"✅ Valid peaks: {len(peaks)}")
        print(f"❌ Rejected peaks: {len(rejected)}")
        
        ox_count = len([p for p in peaks if p['type'] == 'oxidation'])
        red_count = len([p for p in peaks if p['type'] == 'reduction'])
        print(f"   OX: {ox_count}, RED: {red_count}")
        
        for i, peak in enumerate(peaks):
            shape_score = peak.get('shape_score', 0)
            print(f"   Peak {i+1}: {peak['type'][:3].upper()} at {peak['voltage']:.3f}V, "
                  f"{peak['current']:.2f}µA, conf={peak.get('confidence', 0):.0f}%, shape={shape_score:.2f}")
            
        # แสดง rejected peaks
        if rejected:
            print(f"\n❌ Rejected peaks:")
            for i, peak in enumerate(rejected):
                print(f"   Rejected {i+1}: {peak['type'][:3].upper()} at {peak['voltage']:.3f}V - {peak.get('rejection_reason', 'Unknown')}")
            
        return results
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # ทดสอบด้วยไฟล์ตัวอย่าง
    test_files = [
        "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_100mVpS_E5_scan_02.csv",
        "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_200mVpS_E2_scan_01.csv",
        "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_20mVpS_E1_scan_02.csv",
        "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_200mVpS_E4_scan_01.csv"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print("=" * 70)
            test_enhanced_v5(test_file)
            print()
        else:
            print(f"❌ File not found: {test_file}")
