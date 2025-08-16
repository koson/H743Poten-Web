#!/usr/bin/env python3
"""Quick test to check CV data format"""

import pandas as pd
import os

def test_file_format(file_path):
    """Test a single CV file format"""
    print(f"\n🔍 Testing: {os.path.basename(file_path)}")
    
    try:
        # Read the file - try with different options for header
        df = pd.read_csv(file_path)
        print(f"   Columns (default): {list(df.columns)}")
        
        # If reading fails, try skipping header
        if len(df.columns) == 1 or 'FileName:' in str(df.columns[0]):
            print("   Trying to read with skiprows=1...")
            df = pd.read_csv(file_path, skiprows=1)
            print(f"   Columns (skiprows=1): {list(df.columns)}")
        
        print(f"   Shape: {df.shape}")
        print(f"   First few rows:")
        print(df.head(3).to_string(index=False))
        
        # Try to identify columns
        potential_col = None
        current_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if any(term in col_lower for term in ['potential', 'voltage', 'volt', 'v']):
                potential_col = col
            elif any(term in col_lower for term in ['current', 'i', 'amp', 'ua', 'ma', 'na', 'pa']):
                current_col = col
        
        print(f"   Detected - Potential: {potential_col}, Current: {current_col}")
        
        if potential_col and current_col:
            pot_data = df[potential_col].values[:5]
            cur_data = df[current_col].values[:5]
            print(f"   Sample potential: {pot_data}")
            print(f"   Sample current: {cur_data}")
            return True
        else:
            print(f"   ❌ Could not identify columns properly")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🧪 Quick CV Data Format Test")
    print("=" * 50)
    
    # Test a few files from each instrument
    test_files = [
        "validation_data/reference_cv_data/palmsens/Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv",
        "validation_data/reference_cv_data/stm32h743/Pipot_Ferro_0_5mM_100mVpS_E1_scan_01.csv"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            success = test_file_format(file_path)
            if not success:
                print(f"   ⚠️  File format issue detected!")
        else:
            print(f"❌ File not found: {file_path}")
    
    print("\n✅ Quick test completed!")

if __name__ == "__main__":
    main()
