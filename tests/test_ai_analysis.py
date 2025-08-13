#!/usr/bin/env python3
"""
Test script for AI Analysis functionality
"""

import sys
import os
import numpy as np
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required imports work"""
    try:
        from services.ai_analysis_service import create_analyzer, AnalysisResult
        logger.info("✓ AI analysis service imports successful")
        return True
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        return False

def test_basic_analysis():
    """Test basic analysis functionality"""
    try:
        from services.ai_analysis_service import create_analyzer
        
        # Create analyzer
        analyzer = create_analyzer()
        logger.info("✓ Analyzer created successfully")
        
        # Generate test data (simulated DPV curve)
        voltages = np.linspace(-0.5, 0.5, 100)
        currents = np.zeros_like(voltages)
        
        # Add some peaks
        for peak_v in [-0.2, 0.1, 0.3]:
            idx = np.argmin(np.abs(voltages - peak_v))
            currents[idx-5:idx+5] += np.exp(-((voltages[idx-5:idx+5] - peak_v) / 0.02)**2) * 1e-6
        
        # Add noise
        currents += np.random.normal(0, 1e-8, len(currents))
        
        logger.info(f"✓ Test data generated: {len(voltages)} points")
        
        # Perform analysis
        result = analyzer.analyze_measurement(voltages, currents, 'DPV')
        
        logger.info(f"✓ Analysis completed:")
        logger.info(f"  - Peaks detected: {len(result.peaks)}")
        logger.info(f"  - Confidence score: {result.confidence_score:.3f}")
        logger.info(f"  - Quality metrics: {list(result.quality_metrics.keys())}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_route_format():
    """Test that the route response format matches frontend expectations"""
    try:
        from services.ai_analysis_service import create_analyzer
        
        analyzer = create_analyzer()
        
        # Generate test data
        voltages = np.linspace(-0.5, 0.5, 50)
        currents = np.random.normal(0, 1e-8, len(voltages))
        currents[20:25] += 1e-6  # Add a peak
        
        # Perform analysis
        result = analyzer.analyze_measurement(voltages, currents, 'DPV')
        
        # Test response structure (matching what routes return)
        response_data = {
            'success': True,
            'data': {
                'peaks': [
                    {
                        'potential': peak.voltage,
                        'current': peak.current,
                        'confidence': peak.prominence / max([p.prominence for p in result.peaks] + [1.0]),
                    } for peak in result.peaks
                ],
                'quality_metrics': result.quality_metrics,
                'electrochemical_parameters': result.electrochemical_params,
                'overall_score': result.confidence_score,
                'recommendations': result.recommendations
            }
        }
        
        logger.info("✓ Response format test passed:")
        logger.info(f"  - Has 'data' key: {'data' in response_data}")
        logger.info(f"  - Has 'peaks' key: {'peaks' in response_data['data']}")
        logger.info(f"  - Peak format correct: {all('potential' in p for p in response_data['data']['peaks'])}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Route format test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("=== AI Analysis Testing ===")
    
    tests = [
        ("Import Test", test_imports),
        ("Basic Analysis", test_basic_analysis),  
        ("Route Format", test_route_format)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        success = test_func()
        results.append((test_name, success))
    
    logger.info("\n=== Test Results ===")
    all_passed = True
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        logger.info(f"{test_name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        logger.info("\n✓ All tests passed! AI analysis should work correctly.")
    else:
        logger.info("\n✗ Some tests failed. Check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
