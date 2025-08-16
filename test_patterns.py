#!/usr/bin/env python3
"""Test regex patterns for filename parsing"""

import re

# Test PalmSens patterns
palmsens_files = [
    'Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv',
    'Palmsens_1.0mM_CV_200mVpS_E2_scan_05.csv',
    'Palmsens_10mM_CV_50mVpS_E3_scan_11.csv'
]

# Test STM32H743 patterns  
stm32_files = [
    'Pipot_Ferro_0_5mM_100mVpS_E1_scan_01.csv',
    'Pipot_Ferro-1_0mM_200mVpS_E2_scan_05.csv',
    'Pipot_Ferro_10mM_50mVpS_E3_scan_11.csv',
    'Pipot_Ferro-20mM_50mVpS_E4_scan_01.csv'
]

# Current regex patterns
palmsens_pattern = r'Palmsens_(\d+\.?\d*)mM_CV_(\d+)mVpS_E(\d+)_scan_(\d+)'

# STM32H743 patterns
stm32_pattern_1 = r'Pipot_Ferro_(\d+)_(\d+)mM_(\d+)mVpS_E(\d+)_scan_(\d+)'  # decimal with underscore
stm32_pattern_2 = r'Pipot_Ferro-(\d+)_(\d+)mM_(\d+)mVpS_E(\d+)_scan_(\d+)'  # decimal with dash and underscore
stm32_pattern_3 = r'Pipot_Ferro_(\d+)mM_(\d+)mVpS_E(\d+)_scan_(\d+)'        # integer with underscore
stm32_pattern_4 = r'Pipot_Ferro-(\d+)mM_(\d+)mVpS_E(\d+)_scan_(\d+)'        # integer with dash

print('Testing PalmSens patterns:')
for f in palmsens_files:
    match = re.match(palmsens_pattern, f)
    if match:
        print(f'✅ {f} -> conc: {match.group(1)}, rate: {match.group(2)}, electrode: {match.group(3)}, scan: {match.group(4)}')
    else:
        print(f'❌ {f} -> No match')

print('\nTesting STM32H743 patterns:')
for f in stm32_files:
    name = f.replace('.csv', '')
    
    # Try pattern1 (decimal with underscore)
    match = re.match(stm32_pattern_1, name)
    if match:
        concentration = float(f"{match.group(1)}.{match.group(2)}")
        print(f'✅ {f} -> pattern1 (decimal_underscore) -> conc: {concentration}, rate: {match.group(3)}, electrode: {match.group(4)}, scan: {match.group(5)}')
        continue
    
    # Try pattern2 (decimal with dash and underscore)
    match = re.match(stm32_pattern_2, name)
    if match:
        concentration = float(f"{match.group(1)}.{match.group(2)}")
        print(f'✅ {f} -> pattern2 (decimal_dash_underscore) -> conc: {concentration}, rate: {match.group(3)}, electrode: {match.group(4)}, scan: {match.group(5)}')
        continue
    
    # Try pattern3 (integer with underscore)
    match = re.match(stm32_pattern_3, name)
    if match:
        concentration = float(match.group(1))
        print(f'✅ {f} -> pattern3 (integer_underscore) -> conc: {concentration}, rate: {match.group(2)}, electrode: {match.group(3)}, scan: {match.group(4)}')
        continue
        
    # Try pattern4 (integer with dash)
    match = re.match(stm32_pattern_4, name)
    if match:
        concentration = float(match.group(1))
        print(f'✅ {f} -> pattern4 (integer_dash) -> conc: {concentration}, rate: {match.group(2)}, electrode: {match.group(3)}, scan: {match.group(4)}')
        continue
        
    print(f'❌ {f} -> No match')
