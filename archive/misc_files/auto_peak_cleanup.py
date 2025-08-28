#!/usr/bin/env python3
"""
Auto Peak Validation and Cleanup
ทำความสะอาด invalid peaks โดยอัตโนมัติ
"""

import sqlite3
import shutil
from datetime import datetime

def auto_cleanup_invalid_peaks():
    """ทำความสะอาด invalid peaks โดยอัตโนมัติ"""
    
    db_path = "data_logs/parameter_log.db"
    
    print("🔧 Auto Peak Cleanup System")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Define validation rules
        invalid_conditions = [
            # Ox peaks with negative voltage (clearly wrong)
            "(peak_type = 'oxidation' AND peak_voltage < 0)",
            # Red peaks with very high voltage (clearly wrong) 
            "(peak_type = 'reduction' AND peak_voltage > 0.4)",
            # Ox peaks with negative current (wrong direction)
            "(peak_type = 'oxidation' AND peak_current < 0 AND peak_voltage < 0.1)",
            # Red peaks with positive current and high voltage (wrong type)
            "(peak_type = 'reduction' AND peak_current > 0 AND peak_voltage > 0.3)"
        ]
        
        # Find invalid peaks
        where_clause = " OR ".join([f"({condition})" for condition in invalid_conditions])
        
        cursor.execute(f"""
            SELECT id, peak_type, peak_voltage, peak_current, enabled
            FROM peak_parameters 
            WHERE {where_clause}
            ORDER BY id
        """)
        
        invalid_peaks = cursor.fetchall()
        
        print(f"🔍 Found {len(invalid_peaks)} clearly invalid peaks:")
        for peak in invalid_peaks:
            print(f"   ID {peak['id']}: {peak['peak_type']} at {peak['peak_voltage']:.3f}V, {peak['peak_current']:.2f}μA, enabled={peak['enabled']}")
        
        if not invalid_peaks:
            print("✅ No invalid peaks found!")
            conn.close()
            return
        
        # Create backup
        backup_path = f"data_logs/parameter_log_backup_auto_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy(db_path, backup_path)
        print(f"💾 Backup created: {backup_path}")
        
        # Disable invalid peaks
        invalid_ids = [peak['id'] for peak in invalid_peaks]
        placeholders = ','.join(['?' for _ in invalid_ids])
        
        cursor.execute(f"""
            UPDATE peak_parameters 
            SET enabled = 0 
            WHERE id IN ({placeholders})
        """, invalid_ids)
        
        affected_rows = cursor.rowcount
        conn.commit()
        
        # Verify results
        cursor.execute("SELECT COUNT(*) FROM peak_parameters WHERE enabled = 1")
        valid_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM peak_parameters WHERE enabled = 0")
        disabled_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM peak_parameters")
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n✅ Cleanup completed!")
        print(f"   Disabled: {affected_rows} invalid peaks")
        print(f"   Valid peaks remaining: {valid_count}")
        print(f"   Total disabled: {disabled_count}")
        print(f"   Total peaks: {total_count}")
        print(f"   Data quality: {valid_count/total_count*100:.1f}% valid")
        
        return {
            'disabled': affected_rows,
            'valid_remaining': valid_count,
            'total': total_count
        }
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return None

def show_clean_data_summary():
    """แสดงสรุปข้อมูลหลังทำความสะอาด"""
    
    db_path = "data_logs/parameter_log.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print(f"\n📊 Clean Data Summary for PLS Analysis")
        print("=" * 50)
        
        # Valid peaks by type
        cursor.execute("""
            SELECT peak_type, COUNT(*) as count
            FROM peak_parameters 
            WHERE enabled = 1
            GROUP BY peak_type
        """)
        peak_types = cursor.fetchall()
        
        print("🎯 Valid peaks by type:")
        for row in peak_types:
            print(f"   {row['peak_type']}: {row['count']} peaks")
        
        # Valid peaks by sample
        cursor.execute("""
            SELECT m.sample_id, COUNT(*) as peak_count
            FROM peak_parameters pp
            JOIN measurements m ON pp.measurement_id = m.id
            WHERE pp.enabled = 1
            GROUP BY m.sample_id
            ORDER BY m.sample_id
        """)
        sample_counts = cursor.fetchall()
        
        print(f"\n📋 Valid peaks by sample:")
        for row in sample_counts:
            print(f"   {row['sample_id']}: {row['peak_count']} peaks")
        
        # Voltage ranges for valid peaks
        cursor.execute("""
            SELECT 
                peak_type,
                MIN(peak_voltage) as min_voltage,
                MAX(peak_voltage) as max_voltage,
                AVG(peak_voltage) as avg_voltage,
                COUNT(*) as count
            FROM peak_parameters 
            WHERE enabled = 1
            GROUP BY peak_type
        """)
        voltage_stats = cursor.fetchall()
        
        print(f"\n⚡ Voltage ranges for valid peaks:")
        for row in voltage_stats:
            print(f"   {row['peak_type']}: {row['min_voltage']:.3f} - {row['max_voltage']:.3f}V (avg: {row['avg_voltage']:.3f}V, n={row['count']})")
        
        conn.close()
        
        print(f"\n✅ Data is now clean and ready for PLS analysis!")
        
    except Exception as e:
        print(f"❌ Error showing summary: {e}")

if __name__ == "__main__":
    result = auto_cleanup_invalid_peaks()
    
    if result:
        show_clean_data_summary()
        print(f"\n🎯 Next: Extract {result['valid_remaining']} valid peaks for PLS model")