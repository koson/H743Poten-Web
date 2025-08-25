#!/usr/bin/env python3
"""
Fix unit comparison case sensitivity in peak_detection.py
"""

import re

def fix_unit_comparison():
    """Fix case-sensitive unit comparison in load_csv_file function"""
    
    file_path = "src/routes/peak_detection.py"
    
    # อ่านไฟล์
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # หาและแทนที่ในฟังก์ชัน load_csv_file เท่านั้น
    # ใช้ regex เพื่อหา pattern ที่เฉพาะเจาะจง
    
    # Pattern 1: เปลี่ยน if current_unit == 'ma':
    pattern1 = r"(\s+if current_unit == 'ma':)"
    replacement1 = r"\1.replace('ma', 'MA').lower() == 'ma':"
    content = re.sub(pattern1, replacement1, content)
    
    # แทนที่จะใช้ regex ให้ใช้วิธีง่ายๆ
    # แก้ไขเฉพาะในฟังก์ชัน load_csv_file
    lines = content.split('\n')
    
    in_load_csv_function = False
    for i, line in enumerate(lines):
        if 'def load_csv_file(file_path):' in line:
            in_load_csv_function = True
            continue
        
        if in_load_csv_function:
            # หาจุดจบของฟังก์ชัน (def ถัดไป หรือ class)
            if line.strip().startswith('def ') and 'load_csv_file' not in line:
                in_load_csv_function = False
                continue
            
            # แก้ไขเฉพาะในฟังก์ชันนี้
            if "if current_unit == 'ma':" in line:
                lines[i] = line.replace("current_unit == 'ma'", "current_unit.lower() == 'ma'")
            elif "elif current_unit == 'na':" in line:
                lines[i] = line.replace("current_unit == 'na'", "current_unit.lower() == 'na'")
            elif "elif current_unit == 'a':" in line:
                lines[i] = line.replace("current_unit == 'a'", "current_unit.lower() == 'a'")
            elif "# For 'ua' or 'uA' - keep as is (no scaling)" in line:
                lines[i] = "        elif current_unit.lower() in ['ua', 'µa']:"
                lines.insert(i+1, "            current_scale = 1.0  # microAmps - keep as is (no scaling)")
                break
    
    # เขียนไฟล์กลับ
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✅ Fixed unit comparison case sensitivity in load_csv_file function")

if __name__ == "__main__":
    fix_unit_comparison()