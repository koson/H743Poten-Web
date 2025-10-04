#!/usr/bin/env python3
"""
🖥️ V6 CLI Validation Demo
========================

Command-line interface for peak validation when GUI is not available.
Perfect for WSL, server environments, or headless systems.

Usage:
python validation_data/v6_cli_demo.py

Author: H743Poten Research Team
Date: October 4, 2025
"""

import sys
import os
import pandas as pd
import numpy as np

sys.path.append('.')
sys.path.append('validation_data')

try:
    from enhanced_detector_v6_improved import EnhancedDetectorV6Improved
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def create_test_data():
    """Create test CV data with known peaks"""
    print("📊 Creating test CV data...")
    
    # Create ferrocyanide-like data
    voltage = np.linspace(-0.3, 0.6, 90)
    current = np.zeros_like(voltage)
    
    # Add oxidation peak at 0.22V
    ox_peak = 8.5 * np.exp(-((voltage - 0.22) / 0.06)**2)
    current += ox_peak
    
    # Add reduction peak at -0.08V
    red_peak = -7.2 * np.exp(-((voltage + 0.08) / 0.06)**2)
    current += red_peak
    
    # Add realistic baseline and noise
    baseline = 0.1 * voltage + 0.05 * np.sin(3 * voltage)
    noise = 0.4 * np.random.normal(0, 1, len(voltage))
    current += baseline + noise
    
    # Save to file
    filename = "temp_data/cli_demo_ferrocyanide.csv"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    df = pd.DataFrame({
        'Voltage': voltage,
        'Current': current
    })
    df.to_csv(filename, index=False)
    
    print(f"✅ Test data created: {filename}")
    print(f"   📊 {len(voltage)} points")
    print(f"   🎯 2 theoretical peaks (oxidation at 0.22V, reduction at -0.08V)")
    
    return filename

def main():
    """Main CLI validation demo"""
    print("🖥️  V6 CLI VALIDATION DEMO")
    print("=" * 50)
    print("Command-line interface for peak validation")
    print("Perfect for WSL, servers, or headless environments")
    print()
    
    # Initialize detector with forced CLI mode
    detector = EnhancedDetectorV6Improved(gui_mode=True)
    detector.force_cli_mode = True  # Force CLI validation
    
    # Check for existing files or create test data
    test_files = [
        "sample_data/cv_sample.csv",
        "temp_data/preview_Palmsens_Palmsens_0.5mM_CV_100mVpS_E1_scan_05.csv"
    ]
    
    available_files = [f for f in test_files if os.path.exists(f)]
    
    if not available_files:
        # Create test data
        test_file = create_test_data()
        available_files = [test_file]
    
    print(f"📁 Available files ({len(available_files)}):")
    for i, file in enumerate(available_files):
        print(f"   {i+1}. {file}")
    
    # Select file
    if len(available_files) == 1:
        selected_file = available_files[0]
        print(f"\\n🔬 Auto-selected: {selected_file}")
    else:
        print("\\n🔍 Select file:")
        while True:
            try:
                choice = input(f"Enter number (1-{len(available_files)}): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(available_files):
                    selected_file = available_files[idx]
                    break
                else:
                    print(f"❌ Invalid choice. Enter 1-{len(available_files)}")
            except (ValueError, KeyboardInterrupt):
                print("\\n👋 Goodbye!")
                return
    
    # Extract compound info
    compound_name = "Ferrocyanide"
    concentration = "0.5mM"
    scan_rate = "100mV/s"
    
    print(f"\\n📝 Analysis Setup:")
    print(f"   🧪 Compound: {compound_name}")
    print(f"   📊 Concentration: {concentration}")
    print(f"   ⚡ Scan rate: {scan_rate}")
    print()
    
    print("🎯 Starting V6 CLI Analysis...")
    print()
    
    # Run analysis
    try:
        result = detector.analyze_cv_file(
            selected_file,
            compound_name=compound_name,
            concentration=concentration,
            scan_rate=scan_rate
        )
        
        if result:
            print("\\n🎉 CLI VALIDATION COMPLETED!")
            print("=" * 40)
            print(f"📊 Session ID: {result['session_id']}")
            print(f"📈 Total peaks detected: {result['total_peaks']}")
            print(f"✅ Validated peaks: {len(result['validated_peaks'])}")
            
            if result['validated_peaks']:
                print("\\n✅ VALIDATED PEAKS:")
                for i, peak in enumerate(result['validated_peaks']):
                    print(f"   Peak {i+1}: {peak['voltage']:.3f}V, {peak['current']:.2f}µA ({peak['type']})")
            
            # Show database status
            training_data = detector.get_training_dataset()
            total_validated = len(training_data) if training_data is not None else 0
            
            print(f"\\n📚 Training Data Available: {total_validated} validated peaks")
            
            print("\\n🎯 Next Steps:")
            print("1. Train AI with validated data:")
            print("   python validation_data/train_deepcv_v21_improved.py")
            print()
            print("2. Run complete workflow:")
            print("   python validation_data/improved_workflow_demo.py")
            print()
            print("3. Check database:")
            print("   sqlite3 validation_data/peak_validation.db")
            print("   SELECT * FROM peak_validations;")
            
        else:
            print("❌ Analysis failed")
            
    except KeyboardInterrupt:
        print("\\n⚠️  Analysis interrupted")
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()