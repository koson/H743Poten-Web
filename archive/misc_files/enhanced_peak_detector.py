#!/usr/bin/env python3
"""
Enhanced Peak Detection Algorithm
ปรับปรุง algorithm ให้ detect ได้แม่นยำ 100% ด้วย validation rules
"""

import numpy as np
from scipy.signal import find_peaks
import logging

class EnhancedPeakDetector:
    """Peak detector ที่มี validation rules แบบใน peak_validator.py"""
    
    def __init__(self):
        # Voltage zones for Ferrocene (based on real data analysis)
        self.OX_VOLTAGE_MIN = 0.170   # 5th percentile of real oxidation peaks
        self.OX_VOLTAGE_MAX = 0.210   # 95th percentile of real oxidation peaks
        self.RED_VOLTAGE_MIN = 0.070  # 5th percentile of real reduction peaks  
        self.RED_VOLTAGE_MAX = 0.110  # 95th percentile of real reduction peaks
        
        # Current thresholds
        self.MIN_PEAK_HEIGHT = 5.0   # Minimum peak height (μA)
        self.MIN_PEAK_AREA = 0.1     # Minimum peak area
        
        # Detection parameters
        self.PROMINENCE = 0.1
        self.WIDTH = 5
        
        self.logger = logging.getLogger(__name__)
    
    def validate_peak_pre_detection(self, voltage, current, peak_type):
        """ตรวจสอบ peak ก่อน add เข้าไปในผลลัพธ์"""
        
        # Rule 1: Voltage zone validation
        if peak_type == 'oxidation':
            if voltage < self.OX_VOLTAGE_MIN or voltage > self.OX_VOLTAGE_MAX:
                return False, f"Ox peak voltage {voltage:.3f}V outside valid range {self.OX_VOLTAGE_MIN}-{self.OX_VOLTAGE_MAX}V"
                
        elif peak_type == 'reduction':
            if voltage < self.RED_VOLTAGE_MIN or voltage > self.RED_VOLTAGE_MAX:
                return False, f"Red peak voltage {voltage:.3f}V outside valid range {self.RED_VOLTAGE_MIN}-{self.RED_VOLTAGE_MAX}V"
        
        # Rule 2: Current direction validation
        if peak_type == 'oxidation' and current < 0:
            return False, f"Ox peak has negative current {current:.2f}μA"
            
        elif peak_type == 'reduction' and current > 0:
            return False, f"Red peak has positive current {current:.2f}μA"
        
        # Rule 3: Peak size validation
        if abs(current) < self.MIN_PEAK_HEIGHT:
            return False, f"Peak current {current:.2f}μA too small"
        
        # Rule 4: Voltage vs peak type logic check
        if peak_type == 'reduction' and voltage > self.OX_VOLTAGE_MIN:
            return False, f"Red peak voltage {voltage:.3f}V suspiciously high (in Ox zone)"
            
        if peak_type == 'oxidation' and voltage < self.RED_VOLTAGE_MAX:
            return False, f"Ox peak voltage {voltage:.3f}V suspiciously low (in Red zone)"
        
        return True, "Valid peak"
    
    def detect_peaks_enhanced(self, voltage, current, baseline_forward=None, baseline_reverse=None):
        """Enhanced peak detection ด้วย validation rules"""
        
        self.logger.info(f"🔍 Enhanced Peak Detection: starting with {len(voltage)} data points")
        self.logger.info(f"📊 Data range - V: {voltage.min():.3f} to {voltage.max():.3f}V, I: {current.min():.3f} to {current.max():.3f}µA")
        
        # Normalize current for peak detection
        current_max = np.abs(current).max()
        if current_max == 0:
            self.logger.warning("Current is all zeros, cannot detect peaks")
            return {'peaks': [], 'baseline': {}}
        
        current_norm = current / current_max
        
        # Find positive peaks (oxidation candidates)
        try:
            pos_peaks, pos_properties = find_peaks(
                current_norm,
                prominence=self.PROMINENCE,
                width=self.WIDTH
            )
            self.logger.info(f"➕ Found {len(pos_peaks)} oxidation candidates at indices {pos_peaks}")
        except Exception as e:
            self.logger.error(f"❌ Positive peak finding failed: {e}")
            pos_peaks, pos_properties = np.array([]), {'prominences': np.array([])}

        # Find negative peaks (reduction candidates)
        try:
            neg_peaks, neg_properties = find_peaks(
                -current_norm,
                prominence=self.PROMINENCE,
                width=self.WIDTH
            )
            self.logger.info(f"➖ Found {len(neg_peaks)} reduction candidates at indices {neg_peaks}")
        except Exception as e:
            self.logger.error(f"❌ Negative peak finding failed: {e}")
            neg_peaks, neg_properties = np.array([]), {'prominences': np.array([])}
        
        # Use simple baseline if none provided
        if baseline_forward is None or baseline_reverse is None:
            baseline_full = np.zeros_like(current)
            baseline_forward = baseline_full[:len(baseline_full)//2]
            baseline_reverse = baseline_full[len(baseline_full)//2:]
        else:
            baseline_full = np.concatenate([baseline_forward, baseline_reverse])
        
        peaks = []
        rejected_peaks = []
        
        # Process oxidation peak candidates with validation
        for i, peak_idx in enumerate(pos_peaks):
            try:
                peak_voltage = float(voltage[peak_idx])
                peak_current = float(current[peak_idx])
                
                # Calculate baseline current at peak
                n_forward = len(baseline_forward)
                if peak_idx < n_forward:
                    baseline_at_peak = float(baseline_forward[peak_idx])
                else:
                    reverse_idx = peak_idx - n_forward
                    if reverse_idx < len(baseline_reverse):
                        baseline_at_peak = float(baseline_reverse[reverse_idx])
                    else:
                        baseline_at_peak = float(baseline_full[peak_idx] if peak_idx < len(baseline_full) else 0)
                
                # Calculate peak height from baseline
                peak_height = peak_current - baseline_at_peak
                
                # Validate peak before adding
                is_valid, validation_message = self.validate_peak_pre_detection(
                    peak_voltage, peak_current, 'oxidation'
                )
                
                if is_valid:
                    peaks.append({
                        'voltage': peak_voltage,
                        'current': peak_current,
                        'type': 'oxidation',
                        'confidence': float(pos_properties['prominences'][i] * 100),
                        'height': float(peak_height),
                        'baseline_current': baseline_at_peak,
                        'enabled': True
                    })
                    self.logger.info(f"✅ Valid Ox peak: V={peak_voltage:.3f}V, I={peak_current:.3f}μA, height={peak_height:.3f}μA")
                else:
                    rejected_peaks.append({
                        'voltage': peak_voltage,
                        'current': peak_current,
                        'type': 'oxidation',
                        'reason': validation_message
                    })
                    self.logger.warning(f"❌ Rejected Ox peak: V={peak_voltage:.3f}V, I={peak_current:.3f}μA - {validation_message}")
                
            except Exception as e:
                self.logger.error(f"❌ Error processing oxidation peak {i}: {e}")

        # Process reduction peak candidates with validation
        for i, peak_idx in enumerate(neg_peaks):
            try:
                peak_voltage = float(voltage[peak_idx])
                peak_current = float(current[peak_idx])
                
                # Calculate baseline current at peak
                n_forward = len(baseline_forward)
                if peak_idx < n_forward:
                    baseline_at_peak = float(baseline_forward[peak_idx])
                else:
                    reverse_idx = peak_idx - n_forward
                    if reverse_idx < len(baseline_reverse):
                        baseline_at_peak = float(baseline_reverse[reverse_idx])
                    else:
                        baseline_at_peak = float(baseline_full[peak_idx] if peak_idx < len(baseline_full) else 0)
                
                # Calculate peak height from baseline (absolute value for reduction)
                peak_height = abs(peak_current - baseline_at_peak)
                
                # Validate peak before adding
                is_valid, validation_message = self.validate_peak_pre_detection(
                    peak_voltage, peak_current, 'reduction'
                )
                
                if is_valid:
                    peaks.append({
                        'voltage': peak_voltage,
                        'current': peak_current,
                        'type': 'reduction',
                        'confidence': float(neg_properties['prominences'][i] * 100),
                        'height': float(peak_height),
                        'baseline_current': baseline_at_peak,
                        'enabled': True
                    })
                    self.logger.info(f"✅ Valid Red peak: V={peak_voltage:.3f}V, I={peak_current:.3f}μA, height={peak_height:.3f}μA")
                else:
                    rejected_peaks.append({
                        'voltage': peak_voltage,
                        'current': peak_current,
                        'type': 'reduction',
                        'reason': validation_message
                    })
                    self.logger.warning(f"❌ Rejected Red peak: V={peak_voltage:.3f}V, I={peak_current:.3f}μA - {validation_message}")
                
            except Exception as e:
                self.logger.error(f"❌ Error processing reduction peak {i}: {e}")
        
        # Summary
        total_candidates = len(pos_peaks) + len(neg_peaks)
        valid_peaks = len(peaks)
        rejected_count = len(rejected_peaks)
        
        self.logger.info(f"📊 Detection Summary:")
        self.logger.info(f"   Candidates: {total_candidates} ({len(pos_peaks)} Ox + {len(neg_peaks)} Red)")
        self.logger.info(f"   ✅ Valid: {valid_peaks} peaks")
        self.logger.info(f"   ❌ Rejected: {rejected_count} peaks")
        self.logger.info(f"   🎯 Accuracy: {valid_peaks/total_candidates*100:.1f}%" if total_candidates > 0 else "   🎯 Accuracy: N/A")
        
        return {
            'peaks': peaks,
            'baseline': {
                'forward': baseline_forward.tolist() if hasattr(baseline_forward, 'tolist') else baseline_forward,
                'reverse': baseline_reverse.tolist() if hasattr(baseline_reverse, 'tolist') else baseline_reverse
            },
            'rejected_peaks': rejected_peaks,
            'summary': {
                'total_candidates': total_candidates,
                'valid_peaks': valid_peaks,
                'rejected_peaks': rejected_count,
                'accuracy_percent': valid_peaks/total_candidates*100 if total_candidates > 0 else 0
            }
        }

def test_enhanced_detector():
    """ทดสอบ enhanced detector กับข้อมูลจริง"""
    
    # Load a test file
    import os
    import pandas as pd
    
    test_file = "Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv"
    
    if os.path.exists(test_file):
        try:
            df = pd.read_csv(test_file, skiprows=1)  # Skip first line with filename
            if len(df.columns) < 2:
                print(f"❌ Not enough columns in file")
                return None
            
            voltage = df.iloc[:, 0].values  # First column is voltage
            current = df.iloc[:, 1].values  # Second column is current
            
            detector = EnhancedPeakDetector()
            
            print("🧪 Testing Enhanced Peak Detector")
            print("=" * 50)
            print(f"File: {test_file}")
            print(f"Data points: {len(voltage)}")
            print(f"Voltage range: [{voltage.min():.3f}, {voltage.max():.3f}] V")
            print(f"Current range: [{current.min():.3f}, {current.max():.3f}] µA")
            
            # Run detection
            results = detector.detect_peaks_enhanced(voltage, current)
            
            print(f"\n📊 Results:")
            print(f"   Valid peaks: {len(results['peaks'])}")
            print(f"   Rejected peaks: {len(results['rejected_peaks'])}")
            
            if results['peaks']:
                print(f"\n✅ Valid peaks:")
                for i, peak in enumerate(results['peaks'], 1):
                    print(f"   {i}. {peak['type']} at {peak['voltage']:.3f}V, {peak['current']:.2f}μA")
            
            if results['rejected_peaks']:
                print(f"\n❌ Rejected peaks:")
                for i, peak in enumerate(results['rejected_peaks'], 1):
                    print(f"   {i}. {peak['type']} at {peak['voltage']:.3f}V, {peak['current']:.2f}μA - {peak['reason']}")
            
            return results
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return None
    else:
        print(f"❌ Test file not found: {test_file}")
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_enhanced_detector()