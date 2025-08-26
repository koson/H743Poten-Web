#!/usr/bin/env python3
"""
Fix Sample ID in Database
แก้ไข PS0.1mM เป็น PS1.0mM ในฐานข้อมูล
"""

import sqlite3
import os
from datetime import datetime

def fix_sample_id_in_database():
    """แก้ไข sample_id ใน database จาก PS0.1mM เป็น PS1.0mM"""
    
    # Path to the database
    db_path = "data_logs/parameter_log.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    print("🔧 Fixing Sample ID in Parameter Database")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # First, let's see what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("📋 Available tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Check current data with PS0.1mM pattern
        print("\n🔍 Searching for PS0.1mM records...")
        cursor.execute("SELECT * FROM measurements WHERE sample_id LIKE '%PS0.1mM%'")
        records = cursor.fetchall()
        
        if not records:
            print("✅ No PS0.1mM records found in measurements table")
        else:
            print(f"📊 Found {len(records)} records with PS0.1mM:")
            for record in records:
                print(f"   ID: {record['id']}, Sample ID: {record['sample_id']}")
        
        # Check for other variations
        variations = ['0.1mM', 'PS0.1mM']
        for variation in variations:
            cursor.execute("SELECT COUNT(*) as count FROM measurements WHERE sample_id LIKE ?", (f'%{variation}%',))
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"📊 Found {count} records containing '{variation}'")
        
        # Show user what will be changed
        cursor.execute("SELECT id, sample_id FROM measurements WHERE sample_id LIKE '%0.1mM%'")
        target_records = cursor.fetchall()
        
        if target_records:
            print(f"\n🎯 Will update {len(target_records)} records:")
            for record in target_records:
                old_id = record['sample_id']
                new_id = old_id.replace('0.1mM', '1.0mM')
                print(f"   {record['id']}: '{old_id}' → '{new_id}'")
            
            # Ask for confirmation
            response = input(f"\n❓ Proceed with updating {len(target_records)} records? (y/N): ")
            
            if response.lower() in ['y', 'yes']:
                # Create backup first
                backup_path = f"data_logs/parameter_log_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                import shutil
                shutil.copy(db_path, backup_path)
                print(f"💾 Backup created: {backup_path}")
                
                # Perform the update
                cursor.execute("""
                    UPDATE measurements 
                    SET sample_id = REPLACE(sample_id, '0.1mM', '1.0mM')
                    WHERE sample_id LIKE '%0.1mM%'
                """)
                
                affected_rows = cursor.rowcount
                conn.commit()
                
                print(f"✅ Successfully updated {affected_rows} records")
                
                # Verify the changes
                cursor.execute("SELECT id, sample_id FROM measurements WHERE sample_id LIKE '%1.0mM%'")
                updated_records = cursor.fetchall()
                print(f"\n📋 After update - {len(updated_records)} records with 1.0mM:")
                for record in updated_records:
                    print(f"   ID: {record['id']}, Sample ID: {record['sample_id']}")
                
            else:
                print("❌ Update cancelled by user")
        else:
            print("✅ No records found that need updating")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def show_current_sample_ids():
    """แสดง sample_id ทั้งหมดในฐานข้อมูล"""
    db_path = "data_logs/parameter_log.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT sample_id FROM measurements ORDER BY sample_id")
        sample_ids = cursor.fetchall()
        
        print("\n📋 All unique Sample IDs in database:")
        for row in sample_ids:
            print(f"   - {row['sample_id']}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing sample IDs: {e}")

if __name__ == "__main__":
    print("🔧 Sample ID Database Fixer")
    print("แก้ไข PS0.1mM → PS1.0mM")
    print("=" * 50)
    
    show_current_sample_ids()
    success = fix_sample_id_in_database()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ Database fix completed!")
        show_current_sample_ids()
    else:
        print("\n❌ Database fix failed!")
    
    print("\n💡 Note: You can also re-save with corrected Sample ID from the web interface")