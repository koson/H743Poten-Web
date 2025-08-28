#!/usr/bin/env python3
"""
Enhanced Peak and Baseline Detector V3.0
อัลกอริทึมการตรวจจับ peak และ baseline ที่ปรับปรุงแล้ว
ตามข้อเสนอแนะจากการวิเคราะห์ไฟล์ที่มีปัญหา
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

class EnhancedDetectorV3:
    """
    Peak และ Baseline Detector เวอร์ชั่น 3.0
    มีการปรับปรุงตามผลการวิเคราะห์ปัญหา
    """
    
    def __init__(self):
        self.confidence_threshold = 50.0  # Minimum confidence for valid peaks
        self.ferrocyanide_ox_range = (0.0, 0.5)    # Expected OX peak voltage range
        self.ferrocyanide_red_range = (-0.1, 0.3)  # Expected RED peak voltage range
        self.min_scan_ratio = 0.15  # Minimum scan length as ratio of total data
        
    def detect_scan_direction_improved(self, voltage):
        """
        ปรับปรุงการหา scan direction ให้แม่นยำขึ้น
        """
        logger.info("🔄 Enhanced scan direction detection...")
        
        # Method 1: Gradient-based detection
        voltage_diff = np.diff(voltage)
        
        # Smooth the gradient to reduce noise
        window_size = max(3, min(15, len(voltage_diff) // 10))
        if len(voltage_diff) >= window_size:
            smoothed_diff = np.convolve(voltage_diff, np.ones(window_size)/window_size, mode='same')
        else:
            smoothed_diff = voltage_diff
        
        # Find direction changes
        direction = np.sign(smoothed_diff)
        direction_changes = np.where(np.diff(direction) != 0)[0]
        
        if len(direction_changes) > 0:
            # เลือก direction change ที่เด่นชัดที่สุด
            turning_candidates = []
            
            for change_idx in direction_changes:
                # ตรวจสอบว่า direction change นี้มีนัยสำคัญไหม
                before_direction = np.mean(direction[max(0, change_idx-5):change_idx])
                after_direction = np.mean(direction[change_idx:min(len(direction), change_idx+5)])
                
                if abs(before_direction - after_direction) > 1.0:
                    turning_candidates.append(change_idx + 1)  # +1 เพราะ diff ลดมิติ
            
            if turning_candidates:
                turning_point = turning_candidates[0]  # เลือกตัวแรก
            else:
                turning_point = len(voltage) // 2  # Fallback
        else:
            turning_point = len(voltage) // 2  # Fallback
        
        # Validate turning point
        forward_length = turning_point
        reverse_length = len(voltage) - turning_point
        min_length = int(len(voltage) * self.min_scan_ratio)
        
        if forward_length < min_length:
            logger.warning(f"Forward scan too short ({forward_length}), adjusting to {min_length}")
            turning_point = min_length
        elif reverse_length < min_length:
            logger.warning(f"Reverse scan too short ({reverse_length}), adjusting")
            turning_point = len(voltage) - min_length
        
        logger.info(f"✅ Turning point: {turning_point} (Forward: {turning_point}, Reverse: {len(voltage)-turning_point})")
        
        return turning_point
    
    def calculate_dynamic_thresholds(self, current):
        """
        คำนวณ threshold แบบ dynamic ตาม SNR และลักษณะข้อมูล
        """
        logger.info("📊 Calculating dynamic thresholds...")
        
        # Calculate signal statistics
        current_abs = np.abs(current)
        noise_level = np.std(current)
        signal_level = np.max(current_abs)
        snr = signal_level / noise_level if noise_level > 0 else float('inf')
        
        # Dynamic prominence threshold based on SNR
        if snr > 10:        # High SNR - can be sensitive
            prominence_factor = 0.05
        elif snr > 5:       # Medium SNR - moderate sensitivity
            prominence_factor = 0.1
        elif snr > 2:       # Low SNR - be conservative
            prominence_factor = 0.15
        else:               # Very low SNR - very conservative
            prominence_factor = 0.25
        
        prominence_threshold = prominence_factor * np.max(current_abs)
        
        # Dynamic width requirement
        width_threshold = max(3, int(len(current) * 0.015))  # 1.5% of data width
        
        # Height threshold (minimum peak height above baseline)
        height_threshold = np.std(current) * 2  # 2 sigma above noise
        
        thresholds = {
            'prominence': prominence_threshold,
            'width': width_threshold,
            'height': height_threshold,
            'snr': snr,
            'noise_level': noise_level
        }
        
        logger.info(f"📈 SNR: {snr:.1f}, Prominence: {prominence_threshold:.3f}, Width: {width_threshold}")
        
        return thresholds
    
    def validate_peak_enhanced(self, voltage, current, peak_voltage, peak_current, peak_type, baseline_current=None):
        """
        Enhanced peak validation ด้วยหลายเกณฑ์
        """
        validation_score = 100.0
        issues = []
        
        # 1. Voltage range validation
        if peak_type == 'oxidation':
            if not (self.ferrocyanide_ox_range[0] <= peak_voltage <= self.ferrocyanide_ox_range[1]):
                validation_score *= 0.2  # Heavy penalty
                issues.append(f"OX voltage {peak_voltage:.3f}V outside expected range {self.ferrocyanide_ox_range}")
        elif peak_type == 'reduction':
            if not (self.ferrocyanide_red_range[0] <= peak_voltage <= self.ferrocyanide_red_range[1]):
                validation_score *= 0.2  # Heavy penalty
                issues.append(f"RED voltage {peak_voltage:.3f}V outside expected range {self.ferrocyanide_red_range}")
        
        # 2. Peak height validation
        if baseline_current is not None:
            peak_height = abs(peak_current - baseline_current)
        else:
            baseline_estimate = np.median(current)
            peak_height = abs(peak_current - baseline_estimate)
        
        current_range = current.max() - current.min()
        min_height = current_range * 0.03  # 3% of total range
        
        if peak_height < min_height:
            validation_score *= 0.5
            issues.append(f"Peak height {peak_height:.3f}µA too small (< {min_height:.3f}µA)")
        
        # 3. Signal-to-noise ratio
        noise_level = np.std(current)
        snr = peak_height / noise_level if noise_level > 0 else float('inf')
        
        if snr < 3.0:
            validation_score *= 0.7
            issues.append(f"Low SNR: {snr:.1f}")
        elif snr < 2.0:
            validation_score *= 0.3
            issues.append(f"Very low SNR: {snr:.1f}")
        
        # 4. Current direction validation
        if peak_type == 'oxidation' and peak_current < np.median(current):
            validation_score *= 0.6
            issues.append("OX peak current below median (unexpected for oxidation)")
        elif peak_type == 'reduction' and peak_current > np.median(current):
            validation_score *= 0.6
            issues.append("RED peak current above median (unexpected for reduction)")
        
        is_valid = validation_score >= self.confidence_threshold
        
        return {
            'valid': is_valid,
            'confidence': validation_score,
            'issues': issues,
            'snr': snr,
            'peak_height': peak_height
        }
    
    def detect_baseline_enhanced(self, voltage, current, peak_positions=None):
        """
        Enhanced baseline detection ที่หลีกเลี่ยงการชนกับ peaks
        """
        logger.info("📏 Enhanced baseline detection...")
        
        # 1. Find stable regions (low variation)
        window_size = max(5, len(current) // 20)
        current_variation = np.abs(np.gradient(current))
        smoothed_variation = np.convolve(current_variation, np.ones(window_size)/window_size, mode='same')
        
        # Use adaptive threshold for stability
        variation_threshold = np.percentile(smoothed_variation, 25)  # Bottom 25%
        stable_mask = smoothed_variation <= variation_threshold
        
        # 2. Remove points near peaks if peak positions are known
        if peak_positions:
            voltage_tolerance = 0.03  # 30 mV tolerance
            
            for peak in peak_positions:
                peak_mask = np.abs(voltage - peak['voltage']) < voltage_tolerance
                stable_mask = stable_mask & ~peak_mask
                logger.info(f"Excluded {np.sum(peak_mask)} points near peak at {peak['voltage']:.3f}V")
        
        stable_indices = np.where(stable_mask)[0]
        
        if len(stable_indices) < 10:
            logger.warning("Too few stable points found, relaxing criteria...")
            variation_threshold = np.percentile(smoothed_variation, 40)
            stable_mask = smoothed_variation <= variation_threshold
            stable_indices = np.where(stable_mask)[0]
        
        # 3. Split into voltage regions for better baseline estimation
        if len(stable_indices) > 0:
            stable_voltages = voltage[stable_indices]
            stable_currents = current[stable_indices]
            
            v_min, v_max = voltage.min(), voltage.max()
            v_range = v_max - v_min
            
            # Split into regions
            regions = {
                'low': stable_voltages < (v_min + v_range * 0.33),
                'mid': (stable_voltages >= (v_min + v_range * 0.33)) & (stable_voltages <= (v_min + v_range * 0.67)),
                'high': stable_voltages > (v_min + v_range * 0.67)
            }
            
            baseline_info = {}
            
            for region_name, region_mask in regions.items():
                if np.sum(region_mask) >= 3:
                    region_currents = stable_currents[region_mask]
                    region_voltages = stable_voltages[region_mask]
                    
                    baseline_info[region_name] = {
                        'voltage_range': (region_voltages.min(), region_voltages.max()),
                        'current_mean': region_currents.mean(),
                        'current_std': region_currents.std(),
                        'point_count': np.sum(region_mask),
                        'indices': stable_indices[region_mask]
                    }
                    
                    logger.info(f"📊 {region_name.title()} baseline: {region_currents.mean():.3f} ± {region_currents.std():.3f} µA ({np.sum(region_mask)} points)")
            
            return stable_indices, baseline_info
        else:
            logger.error("❌ No stable baseline regions found")
            return np.array([]), {}
    
    def detect_peaks_enhanced(self, voltage, current):
        """
        Enhanced peak detection ด้วยการปรับปรุงทั้งหมด
        """
        logger.info("🎯 Enhanced peak detection starting...")
        
        # 1. Detect scan direction
        turning_point = self.detect_scan_direction_improved(voltage)
        
        # 2. Calculate dynamic thresholds
        thresholds = self.calculate_dynamic_thresholds(current)
        
        # 3. Peak detection with scipy
        try:
            from scipy.signal import find_peaks
            
            # Normalize current for peak detection
            current_norm = current / np.abs(current).max() if np.abs(current).max() > 0 else current
            
            # Find oxidation peaks (positive)
            ox_peaks, ox_props = find_peaks(
                current_norm,
                prominence=thresholds['prominence'] / np.abs(current).max(),
                width=thresholds['width'],
                distance=max(5, thresholds['width'])
            )
            
            # Find reduction peaks (negative)
            red_peaks, red_props = find_peaks(
                -current_norm,
                prominence=thresholds['prominence'] / np.abs(current).max(),
                width=thresholds['width'],
                distance=max(5, thresholds['width'])
            )
            
            logger.info(f"🔍 Raw detection: {len(ox_peaks)} OX candidates, {len(red_peaks)} RED candidates")
            
        except ImportError:
            logger.warning("scipy not available, using simple peak detection")
            # Fallback implementation
            ox_peaks, red_peaks = self._simple_peak_detection(current_norm, thresholds)
            ox_props = {'prominences': [1.0] * len(ox_peaks)}
            red_props = {'prominences': [1.0] * len(red_peaks)}
        
        # 4. Validate and process peaks
        validated_peaks = []
        
        # Process oxidation peaks
        for i, peak_idx in enumerate(ox_peaks):
            peak_voltage = voltage[peak_idx]
            peak_current = current[peak_idx]
            prominence = ox_props['prominences'][i] if i < len(ox_props['prominences']) else 1.0
            
            validation = self.validate_peak_enhanced(voltage, current, peak_voltage, peak_current, 'oxidation')
            
            if validation['valid']:
                peak_info = {
                    'voltage': float(peak_voltage),
                    'current': float(peak_current),
                    'type': 'oxidation',
                    'confidence': float(validation['confidence']),
                    'height': float(validation['peak_height']),
                    'prominence': float(prominence),
                    'snr': float(validation['snr']),
                    'enabled': True,
                    'scan_section': 'forward' if peak_idx < turning_point else 'reverse'
                }
                validated_peaks.append(peak_info)
                logger.info(f"✅ Valid OX peak: {peak_voltage:.3f}V, {peak_current:.1f}µA, conf={validation['confidence']:.1f}%")
            else:
                logger.info(f"❌ Invalid OX peak: {peak_voltage:.3f}V - {', '.join(validation['issues'])}")
        
        # Process reduction peaks
        for i, peak_idx in enumerate(red_peaks):
            peak_voltage = voltage[peak_idx]
            peak_current = current[peak_idx]
            prominence = red_props['prominences'][i] if i < len(red_props['prominences']) else 1.0
            
            validation = self.validate_peak_enhanced(voltage, current, peak_voltage, peak_current, 'reduction')
            
            if validation['valid']:
                peak_info = {
                    'voltage': float(peak_voltage),
                    'current': float(peak_current),
                    'type': 'reduction',
                    'confidence': float(validation['confidence']),
                    'height': float(validation['peak_height']),
                    'prominence': float(prominence),
                    'snr': float(validation['snr']),
                    'enabled': True,
                    'scan_section': 'forward' if peak_idx < turning_point else 'reverse'
                }
                validated_peaks.append(peak_info)
                logger.info(f"✅ Valid RED peak: {peak_voltage:.3f}V, {peak_current:.1f}µA, conf={validation['confidence']:.1f}%")
            else:
                logger.info(f"❌ Invalid RED peak: {peak_voltage:.3f}V - {', '.join(validation['issues'])}")
        
        # 5. Detect baseline (avoiding peaks)
        baseline_indices, baseline_info = self.detect_baseline_enhanced(voltage, current, validated_peaks)
        
        # 6. Final conflict detection
        conflicts = self._detect_conflicts(voltage, baseline_indices, validated_peaks)
        
        logger.info(f"🎯 Final results: {len(validated_peaks)} valid peaks, {len(baseline_indices)} baseline points")
        
        return {
            'peaks': validated_peaks,
            'baseline_indices': baseline_indices,
            'baseline_info': baseline_info,
            'turning_point': turning_point,
            'thresholds': thresholds,
            'conflicts': conflicts,
            'scan_sections': {
                'forward': (0, turning_point),
                'reverse': (turning_point, len(voltage))
            }
        }
    
    def _simple_peak_detection(self, current_norm, thresholds):
        """Simple peak detection fallback when scipy is not available"""
        # Find local maxima for oxidation
        ox_peaks = []
        for i in range(thresholds['width'], len(current_norm) - thresholds['width']):
            left_max = np.max(current_norm[i-thresholds['width']:i])
            right_max = np.max(current_norm[i+1:i+thresholds['width']+1])
            if current_norm[i] > left_max and current_norm[i] > right_max:
                ox_peaks.append(i)
        
        # Find local minima for reduction
        red_peaks = []
        for i in range(thresholds['width'], len(current_norm) - thresholds['width']):
            left_min = np.min(current_norm[i-thresholds['width']:i])
            right_min = np.min(current_norm[i+1:i+thresholds['width']+1])
            if current_norm[i] < left_min and current_norm[i] < right_min:
                red_peaks.append(i)
        
        return np.array(ox_peaks), np.array(red_peaks)
    
    def _detect_conflicts(self, voltage, baseline_indices, peak_positions):
        """Detect conflicts between baseline and peaks"""
        conflicts = []
        voltage_tolerance = 0.02  # 20 mV
        
        if len(baseline_indices) == 0:
            return conflicts
        
        baseline_voltages = voltage[baseline_indices]
        
        for peak in peak_positions:
            peak_voltage = peak['voltage']
            nearby_baseline = np.abs(baseline_voltages - peak_voltage) < voltage_tolerance
            conflict_count = np.sum(nearby_baseline)
            
            if conflict_count > 0:
                conflicts.append({
                    'peak_voltage': peak_voltage,
                    'peak_type': peak['type'],
                    'baseline_count': conflict_count,
                    'severity': 'high' if conflict_count > 3 else 'low'
                })
        
        return conflicts

def test_enhanced_detector():
    """ทดสอบ Enhanced Detector V3.0 กับไฟล์ที่มีปัญหา"""
    detector = EnhancedDetectorV3()
    
    # ไฟล์ทดสอบ
    test_file = "Test_data/Stm32/Pipot_Ferro_0_5mM/Pipot_Ferro_0_5mM_100mVpS_E1_scan_08.csv"
    
    print(f"🧪 Testing Enhanced Detector V3.0 with: {test_file}")
    
    # โหลดข้อมูล
    try:
        df = pd.read_csv(test_file, skiprows=1)
        voltage = df['V'].values
        current = df['uA'].values
        
        print(f"📊 Data loaded: {len(voltage)} points")
        print(f"   Voltage: {voltage.min():.3f} to {voltage.max():.3f} V")
        print(f"   Current: {current.min():.3f} to {current.max():.3f} µA")
        
        # รัน Enhanced Detector
        results = detector.detect_peaks_enhanced(voltage, current)
        
        # แสดงผลลัพธ์
        print(f"\n📋 Enhanced Detection Results:")
        print(f"   🎯 Peaks found: {len(results['peaks'])}")
        print(f"   📏 Baseline points: {len(results['baseline_indices'])}")
        print(f"   🔄 Turning point: {results['turning_point']}")
        print(f"   ⚠️ Conflicts: {len(results['conflicts'])}")
        
        # รายละเอียด peaks
        ox_count = len([p for p in results['peaks'] if p['type'] == 'oxidation'])
        red_count = len([p for p in results['peaks'] if p['type'] == 'reduction'])
        print(f"   📈 Oxidation peaks: {ox_count}")
        print(f"   📉 Reduction peaks: {red_count}")
        
        for peak in results['peaks']:
            print(f"      {peak['type'][:3].upper()}: {peak['voltage']:.3f}V, {peak['current']:.1f}µA, "
                  f"conf={peak['confidence']:.1f}%, SNR={peak['snr']:.1f}")
        
        # รายละเอียด baseline
        if results['baseline_info']:
            print(f"\n   📊 Baseline regions:")
            for region, info in results['baseline_info'].items():
                print(f"      {region.title()}: {info['current_mean']:.3f} ± {info['current_std']:.3f} µA "
                      f"({info['point_count']} points)")
        
        return results
        
    except Exception as e:
        print(f"❌ Error testing enhanced detector: {e}")
        return None

def main():
    """Main function"""
    print("🚀 Enhanced Peak and Baseline Detector V3.0")
    print("=" * 60)
    
    # ทดสอบกับไฟล์ที่มีปัญหา
    results = test_enhanced_detector()
    
    if results:
        print(f"\n✅ Enhanced detection completed successfully!")
        print(f"🎯 This version addresses the key issues found in the analysis:")
        print(f"   ✓ Improved scan direction detection")
        print(f"   ✓ Enhanced peak validation with voltage ranges")
        print(f"   ✓ Dynamic threshold calculation based on SNR")
        print(f"   ✓ Baseline-peak conflict detection")
        print(f"   ✓ Confidence scoring system")
    else:
        print(f"❌ Testing failed")

if __name__ == "__main__":
    main()
