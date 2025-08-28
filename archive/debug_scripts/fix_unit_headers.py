#!/usr/bin/env python3
"""
Fix unit header handling in peak_detection.py to be case-insensitive
"""

import re

def fix_peak_detection():
    file_path = "src/routes/peak_detection.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to find the unit conversion code
        pattern1 = r"(# Simple unit conversion to µA \(PiPot files now have 'uA' headers after conversion\)\s+)if current_unit == 'ma':(.*?)# For 'ua' or 'uA' - keep as is \(no scaling\)"
        
        replacement1 = r"""\1current_unit_lower = current_unit.lower()
        if current_unit_lower == 'ma':
            current_scale = 1e3  # milliAmps to microAmps
        elif current_unit_lower == 'na':
            current_scale = 1e-3  # nanoAmps to microAmps
        elif current_unit_lower == 'a':
            current_scale = 1e6  # Amperes to microAmps
        elif current_unit_lower in ['ua', 'µa']:
            current_scale = 1.0  # microAmps - keep as is (no scaling)"""
        
        # Apply the fix
        new_content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Fixed {file_path}")
            print("Updated unit conversion to be case-insensitive")
            return True
        else:
            print("❌ No matches found to replace")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing unit header handling...")
    success = fix_peak_detection()
    if success:
        print("✅ All fixes applied successfully!")
    else:
        print("❌ Some fixes failed")