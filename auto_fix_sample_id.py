#!/usr/bin/env python3
"""
Auto Fix Sample ID in Database (No Prompt)
แก้ไข PS0.1mM เป็น PS1.0mM ในฐานข้อมูลโดยอัตโนมัติ
"""

import sqlite3
import os
import shutil
from datetime import datetime

def auto_fix_sample_id():
    """แก้ไข sample_id ใน database จาก PS0.1mM เป็น PS1.0mM โดยอัตโนมัติ"""
    
    db_path = "data_logs/parameter_log.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    print("🔧 Auto-Fixing Sample ID in Parameter Database")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check current records that need fixing
        cursor.execute("SELECT COUNT(*) as count FROM measurements WHERE sample_id LIKE '%0.1mM%'")
        count_before = cursor.fetchone()[0]
        
        if count_before == 0:
            print("✅ No records need fixing")
            conn.close()
            return True
        
        print(f"📊 Found {count_before} records to fix")
        
        # Create backup
        backup_path = f"data_logs/parameter_log_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy(db_path, backup_path)
        print(f"💾 Backup created: {backup_path}")
        
        # Show sample before fix
        cursor.execute("SELECT id, sample_id FROM measurements WHERE sample_id LIKE '%0.1mM%' LIMIT 5")
        sample_records = cursor.fetchall()
        print("\n📋 Sample records to be updated:")
        for record in sample_records:
            old_id = record['sample_id']
            new_id = old_id.replace('0.1mM', '1.0mM')
            print(f"   ID {record['id']}: '{old_id}' → '{new_id}'")
        
        # Perform the update
        cursor.execute("""
            UPDATE measurements 
            SET sample_id = REPLACE(sample_id, '0.1mM', '1.0mM')
            WHERE sample_id LIKE '%0.1mM%'
        """)
        
        affected_rows = cursor.rowcount
        conn.commit()
        
        print(f"\n✅ Successfully updated {affected_rows} records")
        
        # Verify the changes
        cursor.execute("SELECT COUNT(*) as count FROM measurements WHERE sample_id LIKE '%0.1mM%'")
        count_after = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as count FROM measurements WHERE sample_id LIKE '%1.0mM%'")
        count_fixed = cursor.fetchone()[0]
        
        print(f"📊 Verification:")
        print(f"   - Records with 0.1mM after fix: {count_after}")
        print(f"   - Records with 1.0mM after fix: {count_fixed}")
        
        # Show unique sample IDs after fix
        cursor.execute("SELECT DISTINCT sample_id FROM measurements ORDER BY sample_id")
        sample_ids = cursor.fetchall()
        
        print(f"\n📋 All unique Sample IDs after fix:")
        for row in sample_ids:
            print(f"   - {row['sample_id']}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Auto Sample ID Database Fixer")
    print("แก้ไข PS0.1mM → PS1.0mM (อัตโนมัติ)")
    print("=" * 50)
    
    success = auto_fix_sample_id()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ Database auto-fix completed!")
    else:
        print("\n❌ Database auto-fix failed!")