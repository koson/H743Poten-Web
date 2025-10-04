#!/usr/bin/env python3
"""
🖱️ V6 Interactive Validation Demo
================================

Demonstrates the interactive batch validation UI
for real CV data analysis and peak validation.

Usage:
python validation_data/v6_interactive_demo.py

Author: H743Poten Research Team
Date: October 4, 2025
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

sys.path.append('.')
sys.path.append('validation_data')

try:
    from enhanced_detector_v6_improved import EnhancedDetectorV6Improved
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def create_realistic_cv_data():
    """Create realistic CV data for demo"""
    print("📊 Creating realistic CV data for demonstration...")
    
    # Ferrocyanide-like data
    voltage = np.linspace(-0.4, 0.8, 120)
    current = np.zeros_like(voltage)
    
    # Add redox peaks
    # Oxidation peak at ~0.25V
    ox_peak = 15.0 * np.exp(-((voltage - 0.25) / 0.08)**2)
    current += ox_peak
    
    # Reduction peak at ~-0.05V
    red_peak = -12.0 * np.exp(-((voltage + 0.05) / 0.08)**2)
    current += red_peak
    
    # Add baseline and noise
    baseline = 0.2 * voltage + 0.1 * np.sin(5 * voltage)
    noise = 0.8 * np.random.normal(0, 1, len(voltage))
    current += baseline + noise
    
    # Save to file
    filename = "temp_data/interactive_demo_ferrocyanide.csv"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    df = pd.DataFrame({
        'Voltage': voltage,
        'Current': current
    })
    df.to_csv(filename, index=False)
    
    print(f"✅ Demo data saved: {filename}")
    return filename

def main():
    """Main interactive demo"""
    print("🖱️  V6 INTERACTIVE VALIDATION DEMO")
    print("=" * 50)
    print("This demo shows the batch validation UI for CV peak analysis")
    print()
    
    # Initialize detector with GUI mode
    detector = EnhancedDetectorV6Improved(gui_mode=True)
    
    # Create or use existing CV data
    cv_files = []
    
    # Check for existing files
    existing_files = [
        "sample_data/cv_sample.csv",
        "temp_data/preview_Palmsens_Palmsens_0.5mM_CV_100mVpS_E1_scan_05.csv"
    ]
    
    for file in existing_files:
        if os.path.exists(file):
            cv_files.append(file)
    
    # Create demo data if no files found
    if not cv_files:
        demo_file = create_realistic_cv_data()
        cv_files.append(demo_file)
    
    print(f"📁 Available CV files: {len(cv_files)}")
    for i, file in enumerate(cv_files):
        print(f"   {i+1}. {file}")
    
    print()
    print("🔍 Select a file to analyze:")
    print("   Enter file number (1-{}) or 'q' to quit:".format(len(cv_files)))
    
    while True:
        try:
            choice = input("👉 Your choice: ").strip().lower()
            
            if choice == 'q':
                print("👋 Goodbye!")
                return
            
            file_idx = int(choice) - 1
            if 0 <= file_idx < len(cv_files):
                selected_file = cv_files[file_idx]
                break
            else:
                print(f"❌ Invalid choice. Please enter 1-{len(cv_files)}")
                
        except ValueError:
            print("❌ Please enter a valid number or 'q'")
        except KeyboardInterrupt:
            print("\\n👋 Goodbye!")
            return
    
    print(f"\\n🔬 Analyzing: {selected_file}")
    
    # Extract compound info from filename
    filename_parts = os.path.basename(selected_file).replace('.csv', '').split('_')
    compound_name = filename_parts[0] if filename_parts else "Unknown"
    concentration = "1.0mM"  # Default
    scan_rate = "100mV/s"   # Default
    
    # Try to extract concentration from filename
    for part in filename_parts:
        if 'mM' in part or 'M' in part:
            concentration = part
            break
    
    print(f"📝 Compound: {compound_name}")
    print(f"📊 Concentration: {concentration}")
    print(f"⚡ Scan rate: {scan_rate}")
    print()
    
    print("🎯 Starting V6 Interactive Analysis...")
    print("📋 Instructions:")
    print("   • Click on peaks to select/deselect them")
    print("   • Use buttons to validate or reject selected peaks")
    print("   • Complete session when done")
    print("   • Export results for training data")
    print()
    
    # Run analysis with interactive UI
    try:
        result = detector.analyze_cv_file(
            selected_file,
            compound_name=compound_name,
            concentration=concentration,
            scan_rate=scan_rate
        )
        
        if result:
            print("\\n✅ Analysis completed!")
            print(f"📊 Session ID: {result['session_id']}")
            print(f"📈 Total peaks detected: {result['total_peaks']}")
            print(f"✅ Validated peaks: {len(result['validated_peaks'])}")
            
            # Show next steps
            print("\\n🎯 Next Steps:")
            print("1. Train AI with validated data:")
            print("   python validation_data/train_deepcv_v21_improved.py")
            print()
            print("2. Run complete workflow:")
            print("   python validation_data/improved_workflow_demo.py")
            print()
            print("3. Check database contents:")
            print("   sqlite3 validation_data/peak_validation.db")
            
        else:
            print("❌ Analysis failed")
            
    except KeyboardInterrupt:
        print("\\n⚠️  Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\\n🎉 V6 Interactive Demo Complete!")

if __name__ == "__main__":
    main()