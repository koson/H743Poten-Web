#!/usr/bin/env python3
"""
Data Processing Status Survey
ตรวจสอบสถานะการประมวลผลข้อมูล - ไฟล์ทั้งหมด vs ข้อมูลใน database
"""

import sqlite3
import os
import glob
from datetime import datetime
import json

def survey_data_status():
    """ตรวจสอบสถานะการประมวลผลข้อมูล"""
    
    print("📊 Data Processing Status Survey")
    print("=" * 60)
    
    # 1. นับไฟล์ทั้งหมดใน Test_data
    test_data_patterns = [
        "Test_data/**/*.csv",
        "Test_data/**/*.txt"
    ]
    
    all_files = []
    for pattern in test_data_patterns:
        files = glob.glob(pattern, recursive=True)
        all_files.extend(files)
    
    print(f"📁 Total CSV/TXT files in Test_data: {len(all_files)}")
    
    # Group by subdirectory
    dir_count = {}
    for file in all_files:
        dir_name = os.path.dirname(file).split(os.sep)[1] if os.sep in file else "root"
        dir_count[dir_name] = dir_count.get(dir_name, 0) + 1
    
    print("📂 Files by directory:")
    for dir_name, count in sorted(dir_count.items()):
        print(f"   {dir_name}: {count} files")
    
    # 2. ตรวจสอบข้อมูลใน database
    db_path = "data_logs/parameter_log.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # ตรวจสอบ tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n🗃️  Database tables: {', '.join(tables)}")
        
        # นับ records ในแต่ละ table
        for table in tables:
            if table != 'sqlite_sequence':
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   {table}: {count} records")
        
        # ตรวจสอบ measurements table - ไฟล์ที่ผ่าน Web UI แล้ว
        cursor.execute("SELECT DISTINCT file_path FROM measurements WHERE file_path IS NOT NULL")
        processed_files = [row[0] for row in cursor.fetchall()]
        print(f"\n✅ Files processed through Web UI: {len(processed_files)}")
        
        # แสดงตัวอย่าง processed files
        if processed_files:
            print("📋 Sample processed files:")
            for i, file_path in enumerate(processed_files[:5]):
                print(f"   {i+1}. {file_path}")
            if len(processed_files) > 5:
                print(f"   ... and {len(processed_files) - 5} more")
        
        # ตรวจสอบ peak_parameters table
        cursor.execute("SELECT COUNT(*) FROM peak_parameters")
        peak_count = cursor.fetchone()[0]
        print(f"\n🎯 Total peak parameters detected: {peak_count}")
        
        # ดู sample IDs และจำนวน peaks
        cursor.execute("""
            SELECT sample_id, COUNT(*) as peak_count 
            FROM peak_parameters 
            GROUP BY sample_id 
            ORDER BY sample_id
        """)
        sample_peaks = cursor.fetchall()
        print(f"\n📊 Peak data by Sample ID:")
        for row in sample_peaks:
            print(f"   {row['sample_id']}: {row['peak_count']} peaks")
        
        # คำนวณไฟล์ที่ยังไม่ประมวลผล
        unprocessed_count = len(all_files) - len(processed_files)
        print(f"\n⏳ Files NOT processed yet: {unprocessed_count}")
        print(f"📈 Processing progress: {len(processed_files)}/{len(all_files)} ({len(processed_files)/len(all_files)*100:.1f}%)")
        
        # ตรวจสอบ peak types
        cursor.execute("""
            SELECT peak_type, COUNT(*) as count 
            FROM peak_parameters 
            GROUP BY peak_type
        """)
        peak_types = cursor.fetchall()
        print(f"\n🔍 Peak types detected:")
        for row in peak_types:
            print(f"   {row['peak_type']}: {row['count']} peaks")
        
        conn.close()
        
        # สรุป
        print("\n" + "=" * 60)
        print("📋 SUMMARY:")
        print(f"   Total files: {len(all_files)}")
        print(f"   Processed: {len(processed_files)}")
        print(f"   Remaining: {unprocessed_count}")
        print(f"   Peak data: {peak_count} parameters")
        print(f"   Sample IDs: {len(sample_peaks)}")
        
        if peak_count > 0:
            print("\n✅ Ready for PLS analysis with existing peak data")
        else:
            print("\n⚠️  No peak data available for PLS analysis")
        
        if unprocessed_count > 2000:
            print(f"💡 Suggestion: Create batch processing for {unprocessed_count} remaining files")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

def show_sample_peak_data():
    """แสดงตัวอย่างข้อมูล peak สำหรับ PLS"""
    
    db_path = "data_logs/parameter_log.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("\n" + "=" * 60)
        print("🎯 Sample Peak Data for PLS Analysis")
        print("=" * 60)
        
        # ดูโครงสร้างข้อมูล peak
        cursor.execute("PRAGMA table_info(peak_parameters)")
        columns = cursor.fetchall()
        print("📋 Peak parameters table structure:")
        for col in columns:
            print(f"   {col['name']}: {col['type']}")
        
        # ดูตัวอย่างข้อมูล
        cursor.execute("""
            SELECT * FROM peak_parameters 
            LIMIT 3
        """)
        samples = cursor.fetchall()
        
        if samples:
            print(f"\n📊 Sample peak data (first 3 records):")
            for i, row in enumerate(samples, 1):
                print(f"\n   Record {i}:")
                for key in row.keys():
                    print(f"     {key}: {row[key]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing sample data: {e}")

if __name__ == "__main__":
    survey_data_status()
    show_sample_peak_data()