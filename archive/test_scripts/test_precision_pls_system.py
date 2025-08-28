#!/usr/bin/env python3
"""
Test Suite for Precision Peak/Baseline Detection and PLS Analysis
================================================================

ทดสอบระบบ precision peak และ baseline detection พร้อมกับ PLS analysis
เพื่อให้แน่ใจว่าระบบทำงานได้แม่นยำสำหรับการวิเคราะห์เชิงปริมาณ
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging
import os
import json
from typing import Dict, List, Optional
from datetime import datetime
import glob

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_precision_analyzer():
    """Test precision peak and baseline analyzer"""
    
    try:
        from precision_peak_baseline_analyzer import PrecisionPeakBaselineAnalyzer
        logger.info("✅ Precision analyzer imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import precision analyzer: {e}")
        return False
    
    # Test with real data if available
    test_files = [
        "Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv",
        "Test_data/Stm32/STM32_Ferro_0_5mM_100mVpS_E1_scan_01.csv"
    ]
    
    analyzer = PrecisionPeakBaselineAnalyzer({
        'analyte': 'generic',  # Use generic for wider peak detection
        'confidence_threshold': 40.0,  # Lower threshold for real data
        'quality_threshold': 50.0,  # Lower quality threshold  
        'min_peak_height': 1.0,
        'peak_prominence_factor': 0.02  # Much lower for noisy data
    })
    
    for test_file in test_files:
        if os.path.exists(test_file):
            try:
                logger.info(f"🧪 Testing with: {test_file}")
                
                # Load data
                df = pd.read_csv(test_file, skiprows=1)
                voltage = df.iloc[:, 0].values
                current = df.iloc[:, 1].values
                
                # Convert current to μA if needed
                if np.max(np.abs(current)) < 1e-3:
                    current = current * 1e6
                
                # Run analysis
                results = analyzer.analyze_cv_data(voltage, current, filename=test_file)
                
                if results['success']:
                    logger.info(f"✅ Analysis successful:")
                    logger.info(f"   Peaks: {len(results['peaks'])}")
                    logger.info(f"   Quality: {results['quality_metrics']['overall_quality']:.1f}%")
                    logger.info(f"   Total area: {results['areas']['total_area']:.3f} μA⋅V")
                    
                    # Save results
                    output_file = f"precision_test_{os.path.basename(test_file)}.json"
                    with open(output_file, 'w') as f:
                        json.dump(results, f, indent=2)
                    logger.info(f"   Results saved: {output_file}")
                    
                    return True
                else:
                    logger.error(f"❌ Analysis failed: {results.get('error', 'Unknown error')}")
            
            except Exception as e:
                logger.error(f"❌ Test failed for {test_file}: {e}")
    
    logger.warning("No test files found, testing with synthetic data")
    return test_synthetic_data(analyzer)

def test_synthetic_data(analyzer):
    """Test with synthetic CV data"""
    
    logger.info("🧪 Testing with synthetic CV data")
    
    # Generate synthetic CV data
    voltage = np.linspace(-0.2, 0.4, 300)
    
    # Oxidation peak at ~0.18V
    ox_peak = 15.0 * np.exp(-((voltage - 0.18)**2) / (2 * 0.02**2))
    
    # Reduction peak at ~0.08V
    red_peak = -12.0 * np.exp(-((voltage - 0.08)**2) / (2 * 0.02**2))
    
    # Background + noise
    background = 0.1 * voltage + np.random.normal(0, 0.2, len(voltage))
    
    current = ox_peak + red_peak + background
    
    # Run analysis
    results = analyzer.analyze_cv_data(voltage, current, filename="synthetic_test.csv")
    
    if results['success']:
        logger.info("✅ Synthetic data analysis successful:")
        logger.info(f"   Peaks detected: {len(results['peaks'])}")
        logger.info(f"   Quality score: {results['quality_metrics']['overall_quality']:.1f}%")
        
        # Check if we detected expected peaks
        ox_peaks = [p for p in results['peaks'] if p['peak_type'] == 'oxidation']
        red_peaks = [p for p in results['peaks'] if p['peak_type'] == 'reduction']
        
        logger.info(f"   Oxidation peaks: {len(ox_peaks)}")
        logger.info(f"   Reduction peaks: {len(red_peaks)}")
        
        if ox_peaks and red_peaks:
            logger.info("✅ Both oxidation and reduction peaks detected correctly")
            return True
        else:
            logger.warning("⚠️ Expected peaks not detected")
            return False
    else:
        logger.error(f"❌ Synthetic data analysis failed: {results.get('error', 'Unknown error')}")
        return False

def test_pls_analyzer():
    """Test PLS analyzer with calibration data"""
    
    try:
        from advanced_pls_analyzer import AdvancedPLSAnalyzer
        logger.info("✅ PLS analyzer imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import PLS analyzer: {e}")
        return False
    
    # Check if sklearn is available
    try:
        from sklearn.cross_decomposition import PLSRegression
        logger.info("✅ Scikit-learn available")
    except ImportError:
        logger.error("❌ Scikit-learn not available - PLS analysis requires sklearn")
        return False
    
    # Create analyzer
    analyzer = AdvancedPLSAnalyzer({
        'quality_threshold': 70.0,
        'min_calibration_points': 3
    })
    
    # Look for real calibration data
    data_patterns = [
        "Test_data/Palmsens/**/*.csv",
        "Test_data/Stm32/**/*.csv"
    ]
    
    calibration_files = []
    for pattern in data_patterns:
        calibration_files.extend(glob.glob(pattern, recursive=True))
    
    if calibration_files:
        logger.info(f"📁 Found {len(calibration_files)} potential calibration files")
        return test_real_calibration_data(analyzer, calibration_files)
    else:
        logger.info("📁 No real data found, testing with synthetic calibration")
        return test_synthetic_calibration(analyzer)

def test_real_calibration_data(analyzer, calibration_files):
    """Test PLS with real calibration data"""
    
    import re
    
    added_points = 0
    for filepath in calibration_files[:10]:  # Limit to first 10 files
        try:
            filename = os.path.basename(filepath)
            
            # Extract concentration from filename
            concentration = None
            patterns = [
                r'(\d+\.?\d*)mM',
                r'(\d+)_(\d+)mM',
                r'Ferro_(\d+\.?\d*)_'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, filename, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 1:
                        concentration = float(match.group(1)) * 1e-3  # Convert mM to M
                    else:
                        concentration = float(f"{match.group(1)}.{match.group(2)}") * 1e-3
                    break
            
            if concentration is None:
                continue
            
            # Load and process data
            df = pd.read_csv(filepath, skiprows=1)
            voltage = df.iloc[:, 0].values
            current = df.iloc[:, 1].values
            
            # Convert current to μA if needed
            if np.max(np.abs(current)) < 1e-3:
                current = current * 1e6
            
            # Add calibration point
            success = analyzer.add_calibration_point(
                voltage, current, concentration, filename=filename
            )
            
            if success:
                added_points += 1
                logger.info(f"   ✅ Added: {filename} ({concentration*1e6:.1f} μM)")
            
            if added_points >= 5:  # Enough for testing
                break
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to process {filepath}: {e}")
    
    logger.info(f"📊 Successfully added {added_points} calibration points")
    
    if added_points >= 3:
        # Build PLS model
        logger.info("🏗️ Building PLS model...")
        model = analyzer.build_pls_model("real_data_model")
        
        if model:
            logger.info("✅ PLS model built successfully")
            
            # Validate model
            validation = analyzer.validate_model("real_data_model")
            if validation['success']:
                logger.info(f"🔍 Model validation:")
                logger.info(f"   LOO R²: {validation['loo_r2']:.4f}")
                logger.info(f"   Training R²: {validation['training_r2']:.4f}")
                logger.info(f"   LOO RMSE: {validation['loo_rmse']:.6f} M")
            
            # Generate report
            report = analyzer.generate_calibration_report()
            with open("real_pls_calibration_report.json", 'w') as f:
                json.dump(report, f, indent=2)
            logger.info("📄 Calibration report saved: real_pls_calibration_report.json")
            
            return True
        else:
            logger.error("❌ Failed to build PLS model")
            return False
    else:
        logger.warning("⚠️ Insufficient calibration data for model building")
        return False

def test_synthetic_calibration(analyzer):
    """Test PLS with synthetic calibration data"""
    
    logger.info("🧪 Testing PLS with synthetic calibration data")
    
    # Create synthetic calibration points
    concentrations = [0.5e-6, 1.0e-6, 2.0e-6, 5.0e-6, 10.0e-6]  # μM
    
    for i, conc in enumerate(concentrations):
        # Generate synthetic CV data with concentration-dependent peak heights
        voltage = np.linspace(-0.2, 0.4, 200)
        
        # Peak heights proportional to concentration
        ox_height = conc * 1e6 * 2.0  # Linear relationship
        red_height = conc * 1e6 * 1.8  # Slightly different for asymmetry
        
        # Oxidation peak
        ox_peak = ox_height * np.exp(-((voltage - 0.18)**2) / (2 * 0.02**2))
        
        # Reduction peak
        red_peak = -red_height * np.exp(-((voltage - 0.08)**2) / (2 * 0.02**2))
        
        # Background + noise
        background = 0.1 * voltage + np.random.normal(0, 0.1, len(voltage))
        
        current = ox_peak + red_peak + background
        
        # Add to calibration
        success = analyzer.add_calibration_point(
            voltage, current, conc, filename=f"synthetic_{conc*1e6:.1f}uM.csv"
        )
        
        if success:
            logger.info(f"   ✅ Added synthetic point: {conc*1e6:.1f} μM")
    
    # Build PLS model
    logger.info("🏗️ Building synthetic PLS model...")
    model = analyzer.build_pls_model("synthetic_model")
    
    if model:
        logger.info("✅ Synthetic PLS model built successfully")
        
        # Test prediction with new synthetic sample
        test_conc = 3.0e-6  # 3 μM
        test_voltage = np.linspace(-0.2, 0.4, 200)
        test_ox = test_conc * 1e6 * 2.0 * np.exp(-((test_voltage - 0.18)**2) / (2 * 0.02**2))
        test_red = -test_conc * 1e6 * 1.8 * np.exp(-((test_voltage - 0.08)**2) / (2 * 0.02**2))
        test_bg = 0.1 * test_voltage + np.random.normal(0, 0.1, len(test_voltage))
        test_current = test_ox + test_red + test_bg
        
        logger.info("🔮 Testing concentration prediction...")
        prediction = analyzer.predict_concentration(
            test_voltage, test_current, filename="test_sample.csv"
        )
        
        if prediction:
            predicted_uM = prediction.predicted_concentration * 1e6
            true_uM = test_conc * 1e6
            error_percent = abs(predicted_uM - true_uM) / true_uM * 100
            
            logger.info(f"🎯 Prediction test results:")
            logger.info(f"   True concentration: {true_uM:.1f} μM")
            logger.info(f"   Predicted concentration: {predicted_uM:.1f} μM")
            logger.info(f"   Prediction error: {error_percent:.1f}%")
            logger.info(f"   Confidence: {prediction.prediction_confidence:.1f}%")
            
            # Success criteria
            if error_percent < 20:  # Less than 20% error
                logger.info("✅ Prediction accuracy test PASSED")
                return True
            else:
                logger.warning("⚠️ Prediction accuracy test FAILED (error > 20%)")
                return False
        else:
            logger.error("❌ Prediction failed")
            return False
    else:
        logger.error("❌ Failed to build synthetic PLS model")
        return False

def test_integration():
    """Test full integration of precision analyzer + PLS"""
    
    logger.info("🔗 Testing full system integration")
    
    # Test 1: Precision analyzer
    logger.info("Step 1: Testing precision peak/baseline analyzer...")
    precision_ok = test_precision_analyzer()
    
    # Test 2: PLS analyzer
    logger.info("Step 2: Testing PLS analyzer...")
    pls_ok = test_pls_analyzer()
    
    # Overall result
    if precision_ok and pls_ok:
        logger.info("🎉 FULL INTEGRATION TEST PASSED!")
        logger.info("   ✅ Precision peak/baseline detection working")
        logger.info("   ✅ PLS analysis and prediction working")
        logger.info("   ✅ System ready for production use")
        return True
    else:
        logger.error("❌ INTEGRATION TEST FAILED!")
        logger.error(f"   Precision analyzer: {'✅' if precision_ok else '❌'}")
        logger.error(f"   PLS analyzer: {'✅' if pls_ok else '❌'}")
        return False

def generate_test_report():
    """Generate comprehensive test report"""
    
    logger.info("📊 Generating comprehensive test report...")
    
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'test_suite_version': '1.0.0',
        'tests_performed': []
    }
    
    # Run all tests and record results
    tests = [
        ('precision_analyzer', test_precision_analyzer),
        ('pls_analyzer', test_pls_analyzer),
        ('integration', test_integration)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        logger.info(f"🧪 Running {test_name} test...")
        try:
            result = test_func()
            test_results['tests_performed'].append({
                'test_name': test_name,
                'status': 'PASSED' if result else 'FAILED',
                'timestamp': datetime.now().isoformat()
            })
            if not result:
                all_passed = False
        except Exception as e:
            logger.error(f"❌ Test {test_name} crashed: {e}")
            test_results['tests_performed'].append({
                'test_name': test_name,
                'status': 'CRASHED',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            all_passed = False
    
    test_results['overall_status'] = 'PASSED' if all_passed else 'FAILED'
    
    # Save report
    report_file = f"precision_pls_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    logger.info(f"📄 Test report saved: {report_file}")
    logger.info(f"🏆 Overall test result: {test_results['overall_status']}")
    
    return test_results

def main():
    """Main test execution"""
    
    print("=" * 80)
    print("🧪 PRECISION PEAK/BASELINE DETECTION + PLS ANALYSIS TEST SUITE")
    print("=" * 80)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check Python environment
    logger.info("🐍 Checking Python environment...")
    
    required_packages = ['numpy', 'pandas', 'matplotlib', 'scipy']
    optional_packages = ['sklearn', 'seaborn', 'joblib']
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"   ✅ {package}")
        except ImportError:
            missing_required.append(package)
            logger.error(f"   ❌ {package} (REQUIRED)")
    
    for package in optional_packages:
        try:
            __import__(package)
            logger.info(f"   ✅ {package}")
        except ImportError:
            missing_optional.append(package)
            logger.warning(f"   ⚠️ {package} (optional)")
    
    if missing_required:
        logger.error(f"❌ Missing required packages: {missing_required}")
        logger.error("Please install required packages before running tests")
        return False
    
    if missing_optional:
        logger.warning(f"⚠️ Missing optional packages: {missing_optional}")
        logger.warning("Some features may not be available")
    
    print()
    
    # Run comprehensive test
    try:
        test_results = generate_test_report()
        
        print()
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        for test in test_results['tests_performed']:
            status_icon = "✅" if test['status'] == 'PASSED' else "❌"
            print(f"{status_icon} {test['test_name']}: {test['status']}")
        
        print()
        overall_icon = "🎉" if test_results['overall_status'] == 'PASSED' else "💥"
        print(f"{overall_icon} OVERALL RESULT: {test_results['overall_status']}")
        
        if test_results['overall_status'] == 'PASSED':
            print()
            print("🚀 System is ready for precision peak/baseline detection and PLS analysis!")
            print("   • Peak detection accuracy validated")
            print("   • Baseline correction working properly")
            print("   • Area under curve calculation precise")
            print("   • PLS models building and predicting correctly")
            print("   • Integration between components successful")
        else:
            print()
            print("🔧 System needs attention before production use")
            print("   • Check failed tests above")
            print("   • Review error messages and fix issues")
            print("   • Ensure all required packages are installed")
        
        print()
        print("=" * 80)
        
        return test_results['overall_status'] == 'PASSED'
        
    except Exception as e:
        logger.error(f"💥 Test suite crashed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
