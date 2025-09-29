#!/usr/bin/env python3
"""
H743 Current Range Software Fix (Temporary)
==========================================

This script provides a temporary software fix for the H743 current range hardware issue
where Range 0 and Range 1 exhibit identical slopes instead of the expected 10:1 ratio.

PROBLEM: TIA (Transimpedance Amplifier) hardware configuration issue
SOLUTION: Software compensation until hardware can be fixed

Usage:
1. Import this module in your measurement service
2. Call fix_current_range_data() to apply corrections
3. Update hardware when possible
"""

import numpy as np
import logging
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

class H743CurrentRangeFix:
    """Software compensation for H743 current range hardware issues"""
    
    # Hardware problem: Range 0 and Range 1 have identical slopes
    # Expected behavior based on TIA design:
    EXPECTED_TIA_CONFIG = {
        0: {'resistance': 1000,    'max_current': 1000e-6, 'gain_factor': 1.0},     # 1kΩ, ±1000µA
        1: {'resistance': 10000,   'max_current': 100e-6,  'gain_factor': 10.0},    # 10kΩ, ±100µA  
        2: {'resistance': 100000,  'max_current': 10e-6,   'gain_factor': 100.0},   # 100kΩ, ±10µA
        3: {'resistance': 1000000, 'max_current': 1e-6,    'gain_factor': 1000.0}   # 1MΩ, ±1µA
    }
    
    # Current hardware issue: Range 0 and Range 1 have same sensitivity
    # Correction factors to apply until hardware is fixed
    HARDWARE_FIX_FACTORS = {
        0: 1.0,     # Range 0: No correction (reference)
        1: 0.1,     # Range 1: Divide by 10 to correct for wrong TIA gain
        2: 0.01,    # Range 2: Estimated correction (needs verification)
        3: 0.001    # Range 3: Estimated correction (needs verification)
    }
    
    def __init__(self):
        self.calibration_applied = False
        self.fix_log = []
        
    def fix_current_value(self, current_raw: float, current_range: int) -> Tuple[float, Dict]:
        """
        Apply software fix to a single current value
        
        Args:
            current_raw: Raw current value from H743 (Amperes)
            current_range: Current range (0, 1, 2, 3)
            
        Returns:
            Tuple of (corrected_current, fix_info)
        """
        if current_range not in self.HARDWARE_FIX_FACTORS:
            logger.warning(f"Unknown current range: {current_range}, no correction applied")
            return current_raw, {'applied': False, 'reason': 'unknown_range'}
            
        fix_factor = self.HARDWARE_FIX_FACTORS[current_range]
        corrected_current = current_raw * fix_factor
        
        fix_info = {
            'applied': True,
            'current_range': current_range,
            'raw_current': current_raw,
            'corrected_current': corrected_current,
            'fix_factor': fix_factor,
            'tia_expected': self.EXPECTED_TIA_CONFIG[current_range]['resistance'],
            'max_range': self.EXPECTED_TIA_CONFIG[current_range]['max_current']
        }
        
        # Log significant corrections
        if abs(fix_factor - 1.0) > 0.1:
            self.fix_log.append(f"Range {current_range}: {current_raw*1e6:.2f}µA → {corrected_current*1e6:.2f}µA (factor: {fix_factor})")
            
        return corrected_current, fix_info
    
    def fix_cv_data(self, cv_data: List[Dict], current_range: int) -> Tuple[List[Dict], Dict]:
        """
        Apply software fix to CV measurement data
        
        Args:
            cv_data: List of {'voltage': V, 'current': I} dictionaries
            current_range: Current range used for measurement
            
        Returns:
            Tuple of (corrected_cv_data, summary_info)
        """
        if not cv_data:
            return cv_data, {'applied': False, 'reason': 'no_data'}
            
        corrected_data = []
        corrections_applied = 0
        
        for point in cv_data:
            voltage = point.get('voltage', 0)
            current_raw = point.get('current', 0)
            
            current_corrected, fix_info = self.fix_current_value(current_raw, current_range)
            
            corrected_data.append({
                'voltage': voltage,
                'current': current_corrected,
                'original_current': current_raw,
                'fix_applied': fix_info['applied']
            })
            
            if fix_info['applied'] and abs(fix_info['fix_factor'] - 1.0) > 0.1:
                corrections_applied += 1
        
        summary = {
            'applied': corrections_applied > 0,
            'total_points': len(cv_data),
            'corrected_points': corrections_applied,
            'current_range': current_range,
            'fix_factor': self.HARDWARE_FIX_FACTORS.get(current_range, 1.0),
            'hardware_issue': 'TIA configuration problem - Range 0 and Range 1 have identical slopes'
        }
        
        if corrections_applied > 0:
            logger.info(f"Applied H743 hardware fix to {corrections_applied}/{len(cv_data)} data points for Range {current_range}")
            
        return corrected_data, summary
    
    def get_range_recommendation(self, expected_current_range: float) -> Dict:
        """
        Recommend appropriate current range based on expected current magnitude
        
        Args:
            expected_current_range: Expected peak current (Amperes)
            
        Returns:
            Dictionary with range recommendation
        """
        current_ua = abs(expected_current_range * 1e6)
        
        for range_id, config in self.EXPECTED_TIA_CONFIG.items():
            max_current_ua = config['max_current'] * 1e6
            
            if current_ua <= max_current_ua * 0.8:  # Use 80% of range for safety
                return {
                    'recommended_range': range_id,
                    'max_current_ua': max_current_ua,
                    'utilization_percent': (current_ua / max_current_ua) * 100,
                    'tia_resistance': config['resistance'],
                    'hardware_fix_needed': range_id in [0, 1],
                    'fix_factor': self.HARDWARE_FIX_FACTORS[range_id]
                }
                
        # If current is too high for any range
        return {
            'recommended_range': 0,  # Use lowest sensitivity range
            'max_current_ua': 1000,
            'utilization_percent': (current_ua / 1000) * 100,
            'warning': 'Current exceeds maximum range',
            'hardware_fix_needed': True,
            'fix_factor': self.HARDWARE_FIX_FACTORS[0]
        }
    
    def generate_fix_report(self) -> str:
        """Generate a report of applied fixes"""
        report = f"""
H743 Current Range Software Fix Report
====================================

Fix Status: {'ACTIVE' if self.fix_log else 'NO CORRECTIONS NEEDED'}
Corrections Applied: {len(self.fix_log)}

Hardware Issue:
- Range 0 (±1000µA) and Range 1 (±100µA) have identical slopes
- Expected: Range 1 should be 10x more sensitive than Range 0
- Root Cause: TIA (Transimpedance Amplifier) configuration problem

Software Fix Applied:
"""
        
        for range_id, factor in self.HARDWARE_FIX_FACTORS.items():
            status = "ACTIVE" if abs(factor - 1.0) > 0.1 else "NONE"
            report += f"- Range {range_id}: Factor {factor} ({status})\n"
            
        if self.fix_log:
            report += f"\nCorrections Applied ({len(self.fix_log)} total):\n"
            for log_entry in self.fix_log[-10:]:  # Show last 10
                report += f"- {log_entry}\n"
                
        report += """
IMPORTANT:
- This is a TEMPORARY software fix
- Hardware inspection and repair required
- Contact hardware team for TIA circuit verification
- Test with known reference standards after hardware fix
"""
        
        return report

# Global instance for easy import
h743_fix = H743CurrentRangeFix()

def apply_h743_current_fix(cv_data: List[Dict], current_range: int) -> Tuple[List[Dict], Dict]:
    """Convenience function to apply H743 current range fix"""
    return h743_fix.fix_cv_data(cv_data, current_range)

def fix_single_current(current: float, current_range: int) -> float:
    """Convenience function to fix a single current value"""
    corrected, _ = h743_fix.fix_current_value(current, current_range)
    return corrected

def get_fix_status() -> str:
    """Get current fix status report"""
    return h743_fix.generate_fix_report()

# Integration example for existing measurement service
class CVMeasurementServiceWithFix:
    """Example integration with existing CV measurement service"""
    
    def __init__(self):
        self.h743_fix = H743CurrentRangeFix()
        
    def process_measurement_data(self, raw_cv_data: List[Dict], current_range: int) -> Dict:
        """Process measurement data with H743 fix applied"""
        
        # Apply hardware fix
        corrected_data, fix_summary = self.h743_fix.fix_cv_data(raw_cv_data, current_range)
        
        # Log if fix was applied
        if fix_summary['applied']:
            logger.info(f"H743 hardware fix applied to Range {current_range} data: "
                       f"{fix_summary['corrected_points']}/{fix_summary['total_points']} points corrected")
        
        return {
            'cv_data': corrected_data,
            'fix_applied': fix_summary['applied'],
            'fix_summary': fix_summary,
            'hardware_issue_detected': current_range in [0, 1],
            'recommendation': 'Hardware inspection required for TIA circuit'
        }

if __name__ == "__main__":
    # Test the fix with sample data
    print("🔧 H743 Current Range Software Fix Test")
    print("======================================")
    
    # Sample CV data with the hardware problem (Range 0 and Range 1 identical)
    test_data_range_0 = [
        {'voltage': -0.5, 'current': -100e-6},
        {'voltage': 0.0, 'current': 0},
        {'voltage': 0.5, 'current': 100e-6}
    ]
    
    test_data_range_1 = [
        {'voltage': -0.5, 'current': -100e-6},  # Same as Range 0 (PROBLEM!)
        {'voltage': 0.0, 'current': 0},
        {'voltage': 0.5, 'current': 100e-6}
    ]
    
    # Apply fixes
    print("Testing Range 0 (±1000µA):")
    fixed_0, summary_0 = apply_h743_current_fix(test_data_range_0, 0)
    print(f"  Fix applied: {summary_0['applied']}")
    print(f"  Fix factor: {summary_0['fix_factor']}")
    
    print("\nTesting Range 1 (±100µA):")
    fixed_1, summary_1 = apply_h743_current_fix(test_data_range_1, 1)
    print(f"  Fix applied: {summary_1['applied']}")
    print(f"  Fix factor: {summary_1['fix_factor']}")
    
    print("\nBefore fix:")
    print(f"  Range 0: {test_data_range_0[2]['current']*1e6:.1f} µA")
    print(f"  Range 1: {test_data_range_1[2]['current']*1e6:.1f} µA")
    
    print("\nAfter fix:")
    print(f"  Range 0: {fixed_0[2]['current']*1e6:.1f} µA")
    print(f"  Range 1: {fixed_1[2]['current']*1e6:.1f} µA")
    
    print(f"\nFix Status Report:")
    print(get_fix_status())