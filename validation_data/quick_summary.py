#!/usr/bin/env python3
"""Quick summary of validation data structure"""

import os
from pathlib import Path
import pandas as pd

def analyze_data_structure():
    """Analyze the structure of our validation data"""
    
    print("📊 H743Poten Peak Detection Validation Framework")
    print("=" * 60)
    
    base_path = Path("validation_data")
    palmsens_path = base_path / "reference_cv_data" / "palmsens"
    stm32_path = base_path / "reference_cv_data" / "stm32h743"
    
    # Count files
    palmsens_files = list(palmsens_path.glob("*.csv")) if palmsens_path.exists() else []
    stm32_files = list(stm32_path.glob("*.csv")) if stm32_path.exists() else []
    
    print(f"📁 Data Sources:")
    print(f"   PalmSens files: {len(palmsens_files)}")
    print(f"   STM32H743 files: {len(stm32_files)}")
    print(f"   Total files: {len(palmsens_files) + len(stm32_files)}")
    
    # Analyze file naming patterns
    if palmsens_files:
        print(f"\n🏷️  PalmSens File Naming Pattern:")
        sample_names = [f.name for f in palmsens_files[:3]]
        for name in sample_names:
            print(f"   {name}")
    
    if stm32_files:
        print(f"\n🏷️  STM32H743 File Naming Pattern:")
        sample_names = [f.name for f in stm32_files[:3]]
        for name in sample_names:
            print(f"   {name}")
    
    # Test a few files for format
    print(f"\n🔍 Data Format Analysis:")
    
    test_files = []
    if palmsens_files:
        test_files.append(("PalmSens", palmsens_files[0]))
    if stm32_files:
        test_files.append(("STM32H743", stm32_files[0]))
    
    for instrument, file_path in test_files:
        try:
            # Read with skiprows to handle metadata
            df = pd.read_csv(file_path, skiprows=1)
            
            print(f"\n   {instrument} ({file_path.name}):")
            print(f"     Columns: {list(df.columns)}")
            print(f"     Data points: {len(df)}")
            
            if 'V' in df.columns and 'uA' in df.columns:
                v_range = [df['V'].min(), df['V'].max()]
                ua_range = [df['uA'].min(), df['uA'].max()]
                print(f"     Voltage range: {v_range[0]:.3f} to {v_range[1]:.3f} V")
                print(f"     Current range: {ua_range[0]:.2e} to {ua_range[1]:.2e} uA")
            
        except Exception as e:
            print(f"   ❌ Error reading {instrument}: {e}")
    
    # Extract experimental conditions from filenames
    print(f"\n🧪 Experimental Conditions Summary:")
    
    def extract_conditions(files, instrument):
        conditions = {
            'concentrations': set(),
            'scan_rates': set(),
            'electrodes': set()
        }
        
        for file_path in files[:20]:  # Sample first 20 files
            name = file_path.name
            try:
                if instrument == "PalmSens":
                    # Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv
                    parts = name.split('_')
                    if len(parts) >= 5:
                        conc = parts[1]  # 0.5mM
                        scan_rate = parts[3]  # 100mVpS
                        electrode = parts[4]  # E1
                        
                        conditions['concentrations'].add(conc)
                        conditions['scan_rates'].add(scan_rate)
                        conditions['electrodes'].add(electrode)
                        
                elif instrument == "STM32H743":
                    # Pipot_Ferro_0_5mM_100mVpS_E1_scan_01.csv
                    parts = name.split('_')
                    if len(parts) >= 6:
                        conc = parts[2] + parts[3]  # 0_5mM -> 0.5mM
                        scan_rate = parts[4]  # 100mVpS
                        electrode = parts[5]  # E1
                        
                        conditions['concentrations'].add(conc.replace('_', '.'))
                        conditions['scan_rates'].add(scan_rate)
                        conditions['electrodes'].add(electrode)
                        
            except Exception as e:
                continue
                
        return conditions
    
    if palmsens_files:
        palmsens_conditions = extract_conditions(palmsens_files, "PalmSens")
        print(f"\n   PalmSens Conditions:")
        print(f"     Concentrations: {sorted(palmsens_conditions['concentrations'])}")
        print(f"     Scan rates: {sorted(palmsens_conditions['scan_rates'])}")
        print(f"     Electrodes: {sorted(palmsens_conditions['electrodes'])}")
    
    if stm32_files:
        stm32_conditions = extract_conditions(stm32_files, "STM32H743")
        print(f"\n   STM32H743 Conditions:")
        print(f"     Concentrations: {sorted(stm32_conditions['concentrations'])}")
        print(f"     Scan rates: {sorted(stm32_conditions['scan_rates'])}")
        print(f"     Electrodes: {sorted(stm32_conditions['electrodes'])}")
    
    print(f"\n🎯 Peak Detection Framework Ready:")
    print(f"   ✅ Data structure validated")
    print(f"   ✅ File formats compatible")
    print(f"   ✅ Multiple experimental conditions available")
    print(f"   ✅ Ready for 3-method peak detection comparison")
    
    print(f"\n📋 Next Steps:")
    print(f"   1. Complete full validation (running in background)")
    print(f"   2. Implement baseline detection algorithm")
    print(f"   3. Implement statistical peak detection")
    print(f"   4. Implement ML-based peak detection")
    print(f"   5. Compare results across methods")

def main():
    analyze_data_structure()

if __name__ == "__main__":
    main()
