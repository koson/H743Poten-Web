#!/usr/bin/env python3

"""
Test concentration extraction with updated regex patterns
"""

import re
import os

def extract_concentration_from_filename(filename: str) -> str:
    """Extract concentration from filename with improved pattern matching"""
    print(f"Extracting concentration from: {filename}")
    
    # Handle different filename patterns - ordered by specificity
    patterns = [
        # Dot notation patterns (highest priority)
        r'(\d+\.\d+)mM',           # 1.0mM, 5.0mM, 0.5mM
        r'(\d+\.\d+)\s*mM',        # 1.0 mM with space
        
        # Underscore patterns (legacy support)
        r'(\d+)_(\d+)mM',          # 1_0mM, 5_0mM, 0_5mM
        r'(\d+)_(\d+)\s*mM',       # 1_0 mM with space
        
        # Simple integer patterns
        r'(\d+)mM',                # 1mM, 5mM, 10mM
        r'(\d+)\s*mM',             # 1 mM with space
        
        # Dash patterns
        r'(\d+)-(\d+)mM',          # 1-0mM
        r'(\d+\.\d*)-mM',          # 1.0-mM
        
        # Fallback patterns
        r'(\d+\.?\d*)_mM',         # Any number_mM
        r'(\d+\.?\d*)-mM',         # Any number-mM
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:  # Two groups: handle X_Y format
                whole_part = match.group(1)
                decimal_part = match.group(2)
                result = f"{whole_part}.{decimal_part}mM"
                print(f"  Pattern match: {pattern} -> {result}")
                return result
            else:  # One group: direct match
                concentration = match.group(1)
                # If it's a whole number, add .0
                if '.' not in concentration and concentration.isdigit():
                    result = f"{concentration}.0mM"
                else:
                    result = f"{concentration}mM"
                print(f"  Pattern match: {pattern} -> {result}")
                return result
    
    # Enhanced fallback cases
    filename_lower = filename.lower()
    
    if '0_5mm' in filename_lower or '0.5mm' in filename_lower:
        print("  Fallback: Found 0.5mM")
        return '0.5mM'
    elif '1_0mm' in filename_lower or '1.0mm' in filename_lower:
        print("  Fallback: Found 1.0mM") 
        return '1.0mM'
    elif '5_0mm' in filename_lower or '5.0mm' in filename_lower:
        print("  Fallback: Found 5.0mM")
        return '5.0mM'
    elif '10mm' in filename_lower:
        print("  Fallback: Found 10.0mM")
        return '10.0mM'
    
    print("  No pattern matched!")
    return 'Unknown'

def test_concentration_extraction():
    """Test concentration extraction on real files"""
    
    csv_dir = r"data_logs\csv"
    if not os.path.exists(csv_dir):
        print(f"Directory {csv_dir} not found!")
        return
    
    # Test files from different concentration categories
    test_patterns = [
        "*0.5mM*",  # 0.5mM files
        "*1.0mM*",  # 1.0mM files  
        "*5.0mM*",  # 5.0mM files
        "*10mM*"    # 10mM files
    ]
    
    import glob
    
    for pattern in test_patterns:
        print(f"\n🔍 Testing pattern: {pattern}")
        files = glob.glob(os.path.join(csv_dir, pattern))
        
        if not files:
            print(f"  No files found for pattern {pattern}")
            continue
            
        # Test first 3 files of each pattern
        for i, file_path in enumerate(files[:3]):
            filename = os.path.basename(file_path)
            concentration = extract_concentration_from_filename(filename)
            print(f"  {filename} -> {concentration}")
        
        if len(files) > 3:
            print(f"  ... and {len(files) - 3} more files")

if __name__ == "__main__":
    print("=== Concentration Extraction Test ===")
    test_concentration_extraction()
