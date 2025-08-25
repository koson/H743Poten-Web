#!/usr/bin/env python3
"""
Fix unit conversion logic after PiPot files have been converted to µA
"""

import re

def fix_peak_detection_unit_logic():
    """Remove STM32-specific logic since all PiPot files now have µA headers"""
    
    file_path = "src/routes/peak_detection.py"
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find and replace the STM32 unit detection logic (both instances)
    old_pattern = r'''        # Check if this is STM32/Pipot file \(uses 'A' header but values are actually in µA\)
        is_stm32_file = \(
            'pipot' in file_path\.lower\(\) or 
            'stm32' in file_path\.lower\(\) or
            \(current_unit == 'a' and lines\[0\]\.strip\(\)\.startswith\('FileName:'\)\)
        \)
        
        if current_unit == 'ma':
            current_scale = 1e3  # milliAmps to microAmps
        elif current_unit == 'na':
            current_scale = 1e-3  # nanoAmps to microAmps
        elif current_unit == 'a' and is_stm32_file:
            current_scale = 1e6  # STM32 A values are in Amperes, so multiply by 1e6 to convert A to µA
            logger\.info\("Detected STM32/Pipot file - converting A values from Amperes to µA"\)
        elif current_unit == 'a' and not is_stm32_file:
            current_scale = 1e6  # True Amperes to microAmps
        # For 'ua' or 'uA' - keep as is \(no scaling\)
        
        logger\.info\(f"Current unit: {current_unit}, scale: {current_scale} \(keeping in µA\), STM32: {is_stm32_file}"\)'''
    
    new_pattern = '''        # Simple unit conversion to µA (PiPot files now have 'uA' headers after conversion)
        if current_unit == 'ma':
            current_scale = 1e3  # milliAmps to microAmps
        elif current_unit == 'na':
            current_scale = 1e-3  # nanoAmps to microAmps
        elif current_unit == 'a':
            current_scale = 1e6  # Amperes to microAmps
        # For 'ua' or 'uA' - keep as is (no scaling)
        
        logger.info(f"Current unit: {current_unit}, scale: {current_scale} (keeping in µA)")'''
    
    # Replace both instances
    content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)
    
    # Check if replacement worked
    if 'is_stm32_file' in content:
        print("⚠️  Warning: Some STM32 logic may still remain")
    else:
        print("✅ Successfully removed STM32-specific unit conversion logic")
    
    # Write back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"📝 Updated {file_path}")

if __name__ == "__main__":
    fix_peak_detection_unit_logic()