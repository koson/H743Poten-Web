#!/usr/bin/env python3
"""Fix unit handling to be case-insensitive in peak_detection.py"""

import re

def fix_unit_handling():
    file_path = "src/routes/peak_detection.py"
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find the unit checking code blocks
    pattern = r"(\s*# Simple unit conversion to µA.*?)\n(\s*if current_unit == 'ma':\n.*?\n.*?\n.*?\n.*?\n.*?\n.*?\n.*?# For 'ua' or 'uA' - keep as is \(no scaling\))"
    
    # Replacement with case-insensitive logic
    replacement = r"""\1
\2        current_unit_lower = current_unit.lower()
        if current_unit_lower == 'ma':
            current_scale = 1e3  # milliAmps to microAmps
        elif current_unit_lower == 'na':
            current_scale = 1e-3  # nanoAmps to microAmps
        elif current_unit_lower == 'a':
            current_scale = 1e6  # Amperes to microAmps
        elif current_unit_lower in ['ua', 'µa']:
            current_scale = 1.0  # microAmps - keep as is (no scaling)"""
    
    # Find and replace all instances
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Simple string replacement approach
    old_block = """        # Simple unit conversion to µA (PiPot files now have 'uA' headers after conversion)
        if current_unit == 'ma':
            current_scale = 1e3  # milliAmps to microAmps
        elif current_unit == 'na':
            current_scale = 1e-3  # nanoAmps to microAmps
        elif current_unit == 'a':
            current_scale = 1e6  # Amperes to microAmps
        # For 'ua' or 'uA' - keep as is (no scaling)"""
    
    new_block = """        # Simple unit conversion to µA (PiPot files now have 'uA' headers after conversion)
        current_unit_lower = current_unit.lower()
        if current_unit_lower == 'ma':
            current_scale = 1e3  # milliAmps to microAmps
        elif current_unit_lower == 'na':
            current_scale = 1e-3  # nanoAmps to microAmps
        elif current_unit_lower == 'a':
            current_scale = 1e6  # Amperes to microAmps
        elif current_unit_lower in ['ua', 'µa']:
            current_scale = 1.0  # microAmps - keep as is (no scaling)"""
    
    # Replace all instances
    new_content = content.replace(old_block, new_block)
    
    # Count replacements
    count = content.count(old_block)
    
    if count > 0:
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {count} instances of unit handling code")
    else:
        print("No instances found to fix")

if __name__ == "__main__":
    fix_unit_handling()