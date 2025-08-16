#!/usr/bin/env python3
"""
Quick test script for 3-method peak detection framework
Non-interactive version for automated testing
"""

import sys
from pathlib import Path
import numpy as np

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_imports():
    """Test if all modules can be imported"""
    print("🧪 Testing Imports...")
    try:
        from config import PeakDetectionConfig
        print("✅ Config module imported")
        
        from peak_detection_framework import TraditionalCVAnalyzer, DeepCVAnalyzer, HybridCVAnalyzer
        print("✅ Peak detection analyzers imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_single_analysis():
    """Test single file analysis"""
    print("\n🔬 Testing Single File Analysis...")
    
    try:
        from peak_detection_framework import TraditionalCVAnalyzer
        
        # Create sample data
        voltages = np.linspace(-0.5, 0.5, 100)
        currents = (
            2e-6 * np.exp(-((voltages - 0.2) / 0.05)**2) +    # Anodic peak
            -1.5e-6 * np.exp(-((voltages + 0.2) / 0.05)**2) + # Cathodic peak
            1e-8 * voltages +                                   # Background
            5e-9 * np.random.normal(0, 1, len(voltages))       # Noise
        )
        
        # Test traditional analyzer
        analyzer = TraditionalCVAnalyzer()
        result = analyzer.detect_peaks(voltages, currents, "test_file.csv")
        
        print(f"✅ Traditional analysis completed")
        print(f"   Peaks detected: {result.peaks_detected}")
        print(f"   Confidence: {result.confidence_score:.1%}")
        print(f"   Processing time: {result.processing_time:.3f}s")
        
        return True
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

def test_configuration():
    """Test configuration system"""
    print("\n⚙️  Testing Configuration...")
    
    try:
        from config import PeakDetectionConfig
        
        # Test configuration validation
        is_valid = PeakDetectionConfig.validate_configuration()
        print(f"✅ Configuration validation: {'PASSED' if is_valid else 'FAILED'}")
        
        # Test directory creation
        PeakDetectionConfig.create_directories()
        print("✅ Directories created")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_data_splits():
    """Test data split availability"""
    print("\n📊 Testing Data Splits...")
    
    splits_path = Path("splits")
    if not splits_path.exists():
        print("❌ Splits directory not found")
        return False
    
    split_files = ["train_files.txt", "validation_files.txt", "test_files.txt"]
    for split_file in split_files:
        file_path = splits_path / split_file
        if file_path.exists():
            with open(file_path, 'r') as f:
                count = len([line for line in f if line.strip()])
            print(f"✅ {split_file}: {count} files")
        else:
            print(f"❌ {split_file}: not found")
            return False
    
    return True

def test_validator_initialization():
    """Test validator can be initialized"""
    print("\n🎯 Testing Validator...")
    
    try:
        from peak_detection_framework import PeakDetectionValidator
        
        validator = PeakDetectionValidator()
        print("✅ Validator initialized successfully")
        print(f"   Base path: {validator.base_path}")
        print(f"   Results path: {validator.results_path}")
        
        return True
    except Exception as e:
        print(f"❌ Validator initialization failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 H743Poten 3-Method Peak Detection Framework")
    print("🔬 AUTOMATED TESTING")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Single Analysis", test_single_analysis), 
        ("Configuration", test_configuration),
        ("Data Splits", test_data_splits),
        ("Validator", test_validator_initialization)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Test...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Framework is ready for validation.")
        print("\n🚀 Next Steps:")
        print("   1. Run validation: python run_validation.py")
        print("   2. Or try demo: python run_validation.py --demo")
        print("   3. Check status: python run_validation.py --check")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        print("\n💡 Possible fixes:")
        print("   1. Install dependencies: pip install pandas numpy scipy scikit-learn")
        print("   2. Run data splitter: python stratified_data_splitter.py")
        print("   3. Check file paths and permissions")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
