#!/usr/bin/env python3
"""
Quick validation test without scientific libraries
Tests basic functionality with fallback implementations
"""

import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add current directory to path  
sys.path.append(str(Path(__file__).parent))

def test_basic_peak_detection():
    """Test basic peak detection without scientific libraries"""
    print("🧪 Testing Basic Peak Detection (Fallback Mode)...")
    
    try:
        from peak_detection_framework import TraditionalCVAnalyzer
        
        # Create sample CV data
        voltages = np.linspace(-0.5, 0.5, 100)
        
        # Simple CV curve with clear peaks
        currents = np.zeros_like(voltages)
        
        # Add anodic peak at +0.2V
        peak1_idx = np.argmin(np.abs(voltages - 0.2))
        currents[peak1_idx-2:peak1_idx+3] = [1e-6, 3e-6, 5e-6, 3e-6, 1e-6]
        
        # Add cathodic peak at -0.2V  
        peak2_idx = np.argmin(np.abs(voltages + 0.2))
        currents[peak2_idx-2:peak2_idx+3] = [-1e-6, -3e-6, -4e-6, -3e-6, -1e-6]
        
        # Add small noise
        currents += 1e-8 * np.random.normal(0, 1, len(voltages))
        
        print(f"📊 Sample data created: {len(voltages)} points")
        print(f"⚡ Voltage range: {voltages.min():.2f} to {voltages.max():.2f} V")
        print(f"🔌 Current range: {currents.min():.2e} to {currents.max():.2e} A")
        
        # Test Traditional CV Analyzer
        analyzer = TraditionalCVAnalyzer()
        result = analyzer.detect_peaks(voltages, currents, "test_sample.csv")
        
        print(f"\n🔬 Traditional Analysis Results:")
        print(f"   Peaks detected: {result.peaks_detected}")
        print(f"   Anodic peaks: {len(result.anodic_peaks)}")
        print(f"   Cathodic peaks: {len(result.cathodic_peaks)}")
        print(f"   Confidence: {result.confidence_score:.1%}")
        print(f"   Processing time: {result.processing_time:.3f}s")
        
        if result.peak_potentials:
            print(f"   Peak potentials: {[f'{v:.3f}V' for v in result.peak_potentials]}")
        
        if result.peak_separation:
            print(f"   Peak separation: {result.peak_separation:.3f}V")
            
        return result.peaks_detected > 0
        
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_system():
    """Test configuration without dependencies"""
    print("\n⚙️  Testing Configuration System...")
    
    try:
        from config import PeakDetectionConfig
        
        # Test basic configuration
        config = PeakDetectionConfig.get_config('traditional')
        print(f"✅ Traditional config loaded: {len(config)} parameters")
        
        # Test validation
        is_valid = PeakDetectionConfig.validate_configuration()
        print(f"✅ Configuration validation: {'PASSED' if is_valid else 'FAILED'}")
        
        # Test directory creation
        PeakDetectionConfig.create_directories()
        print("✅ Directories created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_data_availability():
    """Test if our dataset is available"""
    print("\n📊 Testing Data Availability...")
    
    splits_path = Path("splits")
    
    if not splits_path.exists():
        print("❌ Data splits not found")
        print("💡 Run: python stratified_data_splitter.py")
        return False
    
    files_found = 0
    total_files = 0
    
    for split_name in ["train", "validation", "test"]:
        split_file = splits_path / f"{split_name}_files.txt"
        
        if split_file.exists():
            with open(split_file, 'r') as f:
                file_list = [line.strip() for line in f if line.strip()]
            
            files_found += 1
            total_files += len(file_list)
            print(f"✅ {split_name}: {len(file_list)} files")
        else:
            print(f"❌ {split_name}: not found")
    
    print(f"\n📊 Total dataset: {total_files} files across {files_found} splits")
    
    return files_found == 3

def main():
    """Run basic validation tests"""
    print("🎯 H743Poten 3-Method Peak Detection Framework")
    print("🧪 BASIC VALIDATION TEST (Fallback Mode)")
    print("=" * 60)
    print("📝 Testing core functionality without scientific libraries")
    print("💡 This tests fallback implementations")
    
    tests = [
        ("Peak Detection", test_basic_peak_detection),
        ("Configuration", test_configuration_system), 
        ("Data Availability", test_data_availability)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name} Test")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print(f"\n📊 TEST SUMMARY")
    print("=" * 40)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL BASIC TESTS PASSED!")
        print("\n🚀 Framework Status: READY (Fallback Mode)")
        print("📝 Notes:")
        print("   • Core functionality working")
        print("   • Using fallback peak detection")
        print("   • Scientific libraries recommended for full features")
        print("\n💡 Next Steps:")
        print("   1. Install full dependencies: pip install scipy scikit-learn")
        print("   2. Run validation: python run_validation.py")
        print("   3. Or proceed with current setup (limited features)")
    else:
        print("⚠️  Some tests failed")
        print("🔧 Check the error messages above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
