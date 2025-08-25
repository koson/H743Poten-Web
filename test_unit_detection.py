#!/usr/bin/env python3
"""
Test unit detection directly
"""

# Test the converted file directly
file_path = "Test_data/Stm32/Pipot_Ferro_1_0mM/Pipot_Ferro_1_0mM_20mVpS_E4_scan_05.csv"

print("Testing unit detection...")

with open(file_path, 'r') as f:
    lines = f.readlines()

# Parse headers
headers = [h.strip().lower() for h in lines[1].strip().split(',')]
print(f"Headers: {headers}")

# Find current unit
current_idx = -1
for i, header in enumerate(headers):
    if header in ['a', 'ua', 'ma', 'na', 'current'] or 'amp' in header or 'curr' in header:
        current_idx = i
        break

if current_idx != -1:
    current_unit = headers[current_idx]
    print(f"Current unit detected: '{current_unit}'")
    
    # Test current logic
    current_scale = 1.0
    if current_unit == 'ma':
        current_scale = 1e3
        print("→ milliAmps to microAmps")
    elif current_unit == 'na':
        current_scale = 1e-3
        print("→ nanoAmps to microAmps")
    elif current_unit == 'a':
        current_scale = 1e6
        print("→ Amperes to microAmps")
    else:
        print("→ No scaling (assuming microAmps)")
    
    print(f"Scale factor: {current_scale}")
    
    # Test with case-insensitive
    current_unit_lower = current_unit.lower()
    current_scale_fixed = 1.0
    
    if current_unit_lower == 'ma':
        current_scale_fixed = 1e3
    elif current_unit_lower == 'na':
        current_scale_fixed = 1e-3
    elif current_unit_lower == 'a':
        current_scale_fixed = 1e6
    elif current_unit_lower in ['ua', 'µa']:
        current_scale_fixed = 1.0
        print("→ FIXED: Correctly detected as microAmps")
    
    print(f"Fixed scale factor: {current_scale_fixed}")
    
    # Test sample data
    sample_line = lines[2].strip().split(',')
    if len(sample_line) == 2:
        current_value = float(sample_line[1])
        print(f"\nSample data:")
        print(f"Original: {current_value} {current_unit}")
        print(f"Current logic: {current_value * current_scale} µA")
        print(f"Fixed logic: {current_value * current_scale_fixed} µA")

else:
    print("No current column found!")