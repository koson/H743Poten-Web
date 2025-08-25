#!/usr/bin/env python3
"""
🔍 Debug Current Unit Issues
Test script to debug current scaling issues in the web platform
"""

import numpy as np
import sys
import os
import pandas as pd
import logging

# Setup path
sys.path.append('/mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web/src')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_cv_files():
    """Check CV files for current scaling issues"""
    
    print("🔍 Checking CV files for current scaling issues...")
    
    # Check some actual CV files
    data_dir = "/mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web/uploads"
    
    if not os.path.exists(data_dir):
        print(f"❌ Data directory not found: {data_dir}")
        return
    
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    if not csv_files:
        print("❌ No CSV files found in uploads directory")
        return
    
    print(f"📁 Found {len(csv_files)} CSV files")
    
    for filename in csv_files[:3]:  # Check first 3 files
        filepath = os.path.join(data_dir, filename)
        print(f"\n📄 Checking file: {filename}")
        
        try:
            # Try to read the file
            df = pd.read_csv(filepath)
            print(f"   📊 Shape: {df.shape}")
            print(f"   🔤 Columns: {list(df.columns)}")
            
            # Look for voltage and current columns
            voltage_col = None
            current_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'voltage' in col_lower or 'potential' in col_lower or col_lower in ['v', 'e']:
                    voltage_col = col
                elif 'current' in col_lower or col_lower in ['i', 'current (a)', 'current (µa)', 'current (ua)']:
                    current_col = col
            
            if voltage_col and current_col:
                voltages = df[voltage_col].values
                currents = df[current_col].values
                
                print(f"   📈 Voltage column: '{voltage_col}'")
                print(f"   ⚡ Current column: '{current_col}'")
                print(f"   📊 Voltage range: {voltages.min():.3f} to {voltages.max():.3f} V")
                print(f"   ⚡ Current range: {currents.min():.2e} to {currents.max():.2e}")
                print(f"   📏 Current magnitude: {np.max(np.abs(currents)):.2e}")
                
                # Check if current seems too small
                max_current = np.max(np.abs(currents))
                if max_current < 1e-3:
                    print(f"   ⚠️  WARNING: Current values are very small!")
                    print(f"   ⚠️  This suggests possible unit conversion issue")
                    print(f"   💡 Expected: µA range (1-1000), Got: {max_current:.2e}")
                elif max_current > 1000:
                    print(f"   ⚠️  WARNING: Current values are very large!")
                    print(f"   ⚠️  This might be in nA or pA instead of µA")
                else:
                    print(f"   ✅ Current magnitude looks reasonable for µA")
                    
            else:
                print(f"   ❌ Could not identify voltage/current columns")
                print(f"   🔤 Available columns: {list(df.columns)}")
                
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")

def test_unit_conversion():
    """Test different unit conversion scenarios"""
    
    print("\n🧪 Testing unit conversion scenarios...")
    
    # Test data with different scales
    test_cases = [
        ("Normal µA", np.array([1.0, 5.0, 10.0, 50.0])),
        ("Small µA (nA scale)", np.array([0.001, 0.005, 0.010, 0.050])),
        ("Very small (pA scale)", np.array([1e-6, 5e-6, 1e-5, 5e-5])),
        ("Large (mA scale)", np.array([1000, 5000, 10000, 50000]))
    ]
    
    for name, currents in test_cases:
        print(f"\n📊 {name}:")
        print(f"   Range: {currents.min():.2e} to {currents.max():.2e}")
        print(f"   Magnitude: {np.max(np.abs(currents)):.2e}")
        
        # Suggest conversion
        max_current = np.max(np.abs(currents))
        if max_current < 1e-3:
            factor = 1e6
            print(f"   💡 Suggestion: Multiply by {factor} (convert pA to µA)")
            converted = currents * factor
            print(f"   ✅ After conversion: {converted.min():.2e} to {converted.max():.2e}")
        elif max_current < 1:
            factor = 1e3
            print(f"   💡 Suggestion: Multiply by {factor} (convert nA to µA)")
            converted = currents * factor
            print(f"   ✅ After conversion: {converted.min():.2e} to {converted.max():.2e}")
        elif max_current > 1000:
            factor = 1e-3
            print(f"   💡 Suggestion: Multiply by {factor} (convert nA to µA)")
            converted = currents * factor
            print(f"   ✅ After conversion: {converted.min():.2e} to {converted.max():.2e}")
        else:
            print(f"   ✅ No conversion needed")

def main():
    """Main debugging function"""
    
    print("🔍 Current Unit Debug Suite")
    print("=" * 50)
    
    # Test 1: Check actual CV files
    check_cv_files()
    
    # Test 2: Test unit conversion scenarios
    test_unit_conversion()
    
    print("\n" + "=" * 50)
    print("💡 If current values are too small, check:")
    print("   1. Original data file units")
    print("   2. Database conversion factors")
    print("   3. Web display units")

if __name__ == "__main__":
    main()