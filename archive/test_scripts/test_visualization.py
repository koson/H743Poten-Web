#!/usr/bin/env python3
"""
Test script for baseline visualization
"""

import os
import sys

def test_single_file():
    """Test the visualization with a single file"""
    try:
        from comprehensive_baseline_visualization import load_and_process_csv, create_baseline_visualization
        
        print("🧪 Testing baseline visualization...")
        
        # Find a test CSV file
        test_files = []
        for root, dirs, files in os.walk('Test_data'):
            for file in files:
                if file.endswith('.csv') and not file.endswith('.backup'):
                    test_files.append(os.path.join(root, file))
                    if len(test_files) >= 3:  # Get a few files to test
                        break
            if test_files:
                break
        
        if not test_files:
            print("❌ No test CSV files found")
            return
        
        print(f"📁 Found {len(test_files)} test files")
        
        # Test first file
        test_file = test_files[0]
        print(f"🔬 Testing with: {os.path.basename(test_file)}")
        
        result, error = load_and_process_csv(test_file)
        if error:
            print(f"❌ Error: {error}")
            return
        
        print("✅ CSV loaded and processed successfully")
        print(f"📊 Voltage points: {len(result['voltage'])}")
        print(f"⚡ Current range: {min(result['current']):.2e} to {max(result['current']):.2e} {result['detected_unit']}")
        print(f"🔋 Voltage range: {min(result['voltage']):.3f} to {max(result['voltage']):.3f} V")
        
        # Test plot creation
        plot_path = test_file.replace('.csv', '_test_plot.png')
        forward_r2, reverse_r2 = create_baseline_visualization(test_file, result, plot_path)
        
        print(f"📈 Plot created: {os.path.basename(plot_path)}")
        print(f"📊 R² - Forward: {forward_r2:.3f}, Reverse: {reverse_r2:.3f}")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_file()
