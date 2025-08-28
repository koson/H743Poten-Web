#!/usr/bin/env python3
"""
Simplified test - just import and test basic functionality
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, '.')

print("🧪 Testing imports...")

try:
    import pandas as pd
    print("✅ pandas imported")
except Exception as e:
    print(f"❌ pandas failed: {e}")

try:
    import numpy as np
    print("✅ numpy imported")
except Exception as e:
    print(f"❌ numpy failed: {e}")

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    print("✅ matplotlib imported (non-interactive)")
except Exception as e:
    print(f"❌ matplotlib failed: {e}")

try:
    from baseline_detector_voltage_windows import detect_baseline_voltage_windows
    print("✅ baseline detector imported")
except Exception as e:
    print(f"❌ baseline detector failed: {e}")
    sys.exit(1)

# Test with a simple file
test_file = "Test_data/Stm32/Pipot_Ferro_1_0mM_20mVpS_E4_scan_05.csv"
print(f"\n🔍 Testing with: {test_file}")

if os.path.exists(test_file):
    print("✅ Test file exists")
    
    try:
        df = pd.read_csv(test_file)
        print(f"✅ CSV loaded: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Find columns
        voltage_col = None
        current_col = None
        
        for col in df.columns:
            col_lower = col.lower().strip()
            if 'voltage' in col_lower or 'potential' in col_lower:
                voltage_col = col
            elif 'current' in col_lower:
                current_col = col
        
        print(f"Voltage column: {voltage_col}")
        print(f"Current column: {current_col}")
        
        if voltage_col and current_col:
            voltage_data = df[voltage_col].values
            current_data = df[current_col].values
            
            # Simple unit conversion (assume µA after conversion script)
            current_data = current_data * 1.0  # Keep as-is if already µA
            
            print(f"Data shape: V={len(voltage_data)}, I={len(current_data)}")
            print(f"Voltage range: {voltage_data.min():.3f} to {voltage_data.max():.3f}")
            print(f"Current range: {current_data.min():.3f} to {current_data.max():.3f}")
            
            # Try baseline detection
            print("\n🔍 Running baseline detection...")
            result = detect_baseline_voltage_windows(voltage_data, current_data)
            
            print(f"Baseline detected: {result.get('baseline_detected', False)}")
            
            if result.get('baseline_detected'):
                baseline_v = result.get('baseline_voltage', [])
                baseline_i = result.get('baseline_current', [])
                print(f"Baseline points: {len(baseline_v)}")
                
                # Create a simple plot
                print("📊 Creating plot...")
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(voltage_data, current_data, 'b-', alpha=0.7, label='CV Data')
                ax.plot(baseline_v, baseline_i, 'g-', linewidth=3, label='Baseline')
                ax.set_xlabel('Voltage (V)')
                ax.set_ylabel('Current (µA)')
                ax.set_title('Test Baseline Detection')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                output_file = 'simple_test_plot.png'
                plt.savefig(output_file, dpi=150, bbox_inches='tight')
                plt.close()
                
                print(f"✅ Plot saved: {output_file}")
            else:
                print("❌ No baseline detected")
        else:
            print("❌ Could not find voltage/current columns")
            
    except Exception as e:
        print(f"❌ Processing error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ Test file not found")

print("\n✅ Test completed")