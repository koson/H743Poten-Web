#!/usr/bin/env python3
"""Quick file content inspection"""

def inspect_file(file_path):
    print(f"\n🔍 Inspecting: {file_path}")
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()[:10]  # First 10 lines
        
        print(f"   Total lines: ~{len(lines)}+ lines")
        for i, line in enumerate(lines):
            print(f"   Line {i+1}: {repr(line)}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    files = [
        "validation_data/reference_cv_data/palmsens/Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv",
        "validation_data/reference_cv_data/stm32h743/Pipot_Ferro_0_5mM_100mVpS_E1_scan_01.csv"
    ]
    
    for file_path in files:
        inspect_file(file_path)

if __name__ == "__main__":
    main()
