#!/usr/bin/env python3
"""
Peak Validation Rules System
Quick Fix สำหรับ filter peaks ที่ไม่น่าเชื่อถือออกโดยอัตโนมัติ
"""

import sqlite3
import numpy as np
from datetime import datetime

class PeakValidator:
    """ระบบตรวจสอบความน่าเชื่อถือของ peak detection"""
    
    def __init__(self, db_path="data_logs/parameter_log.db"):
        self.db_path = db_path
        
        # Voltage zones for Ferrocene (typical ranges)
        self.OX_VOLTAGE_MIN = 0.15   # Oxidation peak should be > 0.15V
        self.OX_VOLTAGE_MAX = 0.30   # Oxidation peak should be < 0.30V
        self.RED_VOLTAGE_MIN = 0.05  # Reduction peak should be > 0.05V  
        self.RED_VOLTAGE_MAX = 0.20  # Reduction peak should be < 0.20V
        
        # Current thresholds
        self.MIN_PEAK_HEIGHT = 5.0   # Minimum peak height (μA)
        self.MIN_PEAK_AREA = 0.1     # Minimum peak area
        
    def validate_peak(self, peak_data):
        """ตรวจสอบความน่าเชื่อถือของ peak เดียว"""
        
        peak_type = peak_data.get('peak_type', '')
        voltage = peak_data.get('peak_voltage', 0)
        current = peak_data.get('peak_current', 0)
        height = peak_data.get('peak_height', 0)
        area = peak_data.get('peak_area', 0)
        
        validation_results = {
            'is_valid': True,
            'confidence_score': 100,
            'issues': []
        }
        
        # Rule 1: Voltage zone validation
        if peak_type == 'oxidation':
            if voltage < self.OX_VOLTAGE_MIN or voltage > self.OX_VOLTAGE_MAX:
                validation_results['is_valid'] = False
                validation_results['confidence_score'] -= 50
                validation_results['issues'].append(f"Ox peak voltage {voltage:.3f}V outside valid range {self.OX_VOLTAGE_MIN}-{self.OX_VOLTAGE_MAX}V")
                
        elif peak_type == 'reduction':
            if voltage < self.RED_VOLTAGE_MIN or voltage > self.RED_VOLTAGE_MAX:
                validation_results['is_valid'] = False
                validation_results['confidence_score'] -= 50
                validation_results['issues'].append(f"Red peak voltage {voltage:.3f}V outside valid range {self.RED_VOLTAGE_MIN}-{self.RED_VOLTAGE_MAX}V")
        
        # Rule 2: Current direction validation
        if peak_type == 'oxidation' and current < 0:
            validation_results['is_valid'] = False
            validation_results['confidence_score'] -= 40
            validation_results['issues'].append(f"Ox peak has negative current {current:.2f}μA")
            
        elif peak_type == 'reduction' and current > 0:
            validation_results['is_valid'] = False
            validation_results['confidence_score'] -= 40
            validation_results['issues'].append(f"Red peak has positive current {current:.2f}μA")
        
        # Rule 3: Peak size validation
        if abs(height) < self.MIN_PEAK_HEIGHT:
            validation_results['confidence_score'] -= 20
            validation_results['issues'].append(f"Peak height {height:.2f}μA too small")
            
        if abs(area) < self.MIN_PEAK_AREA:
            validation_results['confidence_score'] -= 15
            validation_results['issues'].append(f"Peak area {area:.3f} too small")
        
        # Rule 4: Voltage vs peak type logic check
        if peak_type == 'reduction' and voltage > self.OX_VOLTAGE_MIN:
            validation_results['confidence_score'] -= 30
            validation_results['issues'].append(f"Red peak voltage {voltage:.3f}V suspiciously high (in Ox zone)")
            
        if peak_type == 'oxidation' and voltage < self.RED_VOLTAGE_MAX:
            validation_results['confidence_score'] -= 30
            validation_results['issues'].append(f"Ox peak voltage {voltage:.3f}V suspiciously low (in Red zone)")
        
        # Final confidence adjustment
        validation_results['confidence_score'] = max(0, validation_results['confidence_score'])
        
        # Mark as invalid if confidence too low
        if validation_results['confidence_score'] < 50:
            validation_results['is_valid'] = False
            
        return validation_results
    
    def validate_all_peaks(self):
        """ตรวจสอบ peaks ทั้งหมดใน database"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all peaks
            cursor.execute("""
                SELECT pp.*, m.sample_id, m.scan_rate
                FROM peak_parameters pp
                LEFT JOIN measurements m ON pp.measurement_id = m.id
                ORDER BY pp.id
            """)
            
            peaks = cursor.fetchall()
            
            print(f"🔍 Validating {len(peaks)} peaks...")
            print("=" * 60)
            
            validation_summary = {
                'total_peaks': len(peaks),
                'valid_peaks': 0,
                'invalid_peaks': 0,
                'low_confidence_peaks': 0,
                'issues_by_type': {}
            }
            
            invalid_peaks = []
            
            for peak in peaks:
                peak_dict = dict(peak)
                validation = self.validate_peak(peak_dict)
                
                if validation['is_valid']:
                    validation_summary['valid_peaks'] += 1
                else:
                    validation_summary['invalid_peaks'] += 1
                    invalid_peaks.append({
                        'peak_id': peak['id'],
                        'sample_id': peak['sample_id'],
                        'peak_type': peak['peak_type'],
                        'voltage': peak['peak_voltage'],
                        'current': peak['peak_current'],
                        'confidence': validation['confidence_score'],
                        'issues': validation['issues']
                    })
                
                if validation['confidence_score'] < 70:
                    validation_summary['low_confidence_peaks'] += 1
                
                # Count issues by type
                for issue in validation['issues']:
                    issue_type = issue.split()[0] + " " + issue.split()[1]  # First two words
                    validation_summary['issues_by_type'][issue_type] = validation_summary['issues_by_type'].get(issue_type, 0) + 1
            
            # Print summary
            print("📊 Validation Summary:")
            print(f"   Total peaks: {validation_summary['total_peaks']}")
            print(f"   ✅ Valid peaks: {validation_summary['valid_peaks']}")
            print(f"   ❌ Invalid peaks: {validation_summary['invalid_peaks']}")
            print(f"   ⚠️  Low confidence peaks: {validation_summary['low_confidence_peaks']}")
            
            if validation_summary['issues_by_type']:
                print(f"\n🔍 Common issues:")
                for issue_type, count in sorted(validation_summary['issues_by_type'].items(), key=lambda x: x[1], reverse=True):
                    print(f"   {issue_type}: {count} peaks")
            
            # Show problematic peaks
            if invalid_peaks:
                print(f"\n❌ Invalid peaks that should be filtered:")
                for i, peak in enumerate(invalid_peaks[:10]):  # Show first 10
                    print(f"   {i+1}. ID {peak['peak_id']}: {peak['sample_id']} - {peak['peak_type']} at {peak['voltage']:.3f}V")
                    print(f"      Current: {peak['current']:.2f}μA, Confidence: {peak['confidence']}%")
                    print(f"      Issues: {', '.join(peak['issues'])}")
                    print()
                
                if len(invalid_peaks) > 10:
                    print(f"   ... and {len(invalid_peaks) - 10} more invalid peaks")
            
            conn.close()
            return validation_summary, invalid_peaks
            
        except Exception as e:
            print(f"❌ Error validating peaks: {e}")
            return None, None
    
    def mark_invalid_peaks(self, apply_changes=False):
        """Mark invalid peaks as disabled in database"""
        
        validation_summary, invalid_peaks = self.validate_all_peaks()
        
        if not invalid_peaks:
            print("✅ No invalid peaks found to disable")
            return
        
        if not apply_changes:
            print(f"\n💡 To actually disable {len(invalid_peaks)} invalid peaks, run with apply_changes=True")
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create backup first
            backup_path = f"data_logs/parameter_log_backup_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            import shutil
            shutil.copy(self.db_path, backup_path)
            print(f"💾 Backup created: {backup_path}")
            
            # Disable invalid peaks
            invalid_ids = [peak['peak_id'] for peak in invalid_peaks]
            placeholders = ','.join(['?' for _ in invalid_ids])
            
            cursor.execute(f"""
                UPDATE peak_parameters 
                SET enabled = 0 
                WHERE id IN ({placeholders})
            """, invalid_ids)
            
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
            
            print(f"✅ Disabled {affected_rows} invalid peaks")
            print(f"📊 Remaining valid peaks: {validation_summary['total_peaks'] - len(invalid_peaks)}")
            
        except Exception as e:
            print(f"❌ Error marking invalid peaks: {e}")

def main():
    """Run peak validation"""
    
    print("🔍 Peak Validation System - Quick Fix")
    print("=" * 60)
    
    validator = PeakValidator()
    
    # Run validation
    validation_summary, invalid_peaks = validator.validate_all_peaks()
    
    if invalid_peaks:
        print(f"\n💡 Quick Fix Strategy:")
        print(f"   1. ✅ Keep {validation_summary['valid_peaks']} valid peaks for PLS")
        print(f"   2. 🚫 Auto-disable {len(invalid_peaks)} invalid peaks")
        print(f"   3. ⚠️  Flag {validation_summary['low_confidence_peaks']} low-confidence peaks for review")
        print(f"\n   This will give you clean data for immediate PLS analysis!")
        
        # Ask if user wants to apply changes
        response = input(f"\n❓ Disable {len(invalid_peaks)} invalid peaks? (y/N): ")
        if response.lower() in ['y', 'yes']:
            validator.mark_invalid_peaks(apply_changes=True)
    
    print(f"\n🎯 Next step: Extract validated peak data for PLS analysis")

if __name__ == "__main__":
    main()