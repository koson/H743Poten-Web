#!/usr/bin/env python3
"""
Manual fix for unit comparison case sensitivity
"""

def fix_peak_detection_file():
    file_path = "src/routes/peak_detection.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # แทนที่ในฟังก์ชัน load_csv_file เท่านั้น
    replacements = [
        ("if current_unit == 'ma':", "if current_unit.lower() == 'ma':"),
        ("elif current_unit == 'na':", "elif current_unit.lower() == 'na':"),
        ("elif current_unit == 'a':", "elif current_unit.lower() == 'a':"),
        ("# For 'ua' or 'uA' - keep as is (no scaling)", 
         "elif current_unit.lower() in ['ua', 'µa']:\n            current_scale = 1.0  # microAmps - keep as is (no scaling)"),
    ]
    
    # ใช้ regex เพื่อแทนที่เฉพาะในฟังก์ชัน load_csv_file
    import re
    
    # หาตำแหน่งฟังก์ชัน load_csv_file
    start_pattern = r'def load_csv_file\(file_path\):'
    end_pattern = r'\ndef [^_]'  # ฟังก์ชันถัดไป
    
    start_match = re.search(start_pattern, content)
    if start_match:
        start_pos = start_match.start()
        
        # หาจุดจบของฟังก์ชัน
        remaining_content = content[start_pos:]
        end_match = re.search(end_pattern, remaining_content)
        
        if end_match:
            end_pos = start_pos + end_match.start()
        else:
            end_pos = len(content)
        
        # แก้ไขเฉพาะในฟังก์ชันนี้
        function_content = content[start_pos:end_pos]
        
        for old, new in replacements:
            function_content = function_content.replace(old, new)
        
        # รวมเนื้อหาใหม่
        new_content = content[:start_pos] + function_content + content[end_pos:]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Fixed unit comparison in load_csv_file function")
        return True
    
    print("❌ Could not find load_csv_file function")
    return False

if __name__ == "__main__":
    fix_peak_detection_file()