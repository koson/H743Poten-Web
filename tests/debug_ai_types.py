#!/usr/bin/env python3
"""
Debug script to check exact data types returned by AI analysis
"""

import sys
sys.path.insert(0, 'src')

def debug_ai_types():
    """Debug the exact types returned by AI analysis"""
    print("🔍 Debugging AI Analysis Data Types...")
    
    try:
        import numpy as np
        from services.ai_analysis_service import create_analyzer
        from routes.ai_analysis_routes import convert_numpy_types
        
        # Create dummy data
        voltages = np.linspace(-0.5, 0.5, 10)
        currents = np.array([1e-6, 2e-6, 5e-6, 8e-6, 3e-6, 1e-6, 2e-6, 1e-6, 1e-6, 1e-6])
        
        print(f"Input types:")
        print(f"  voltages: {type(voltages)} shape: {voltages.shape}")
        print(f"  currents: {type(currents)} shape: {currents.shape}")
        
        # Create analyzer and run analysis
        analyzer = create_analyzer()
        result = analyzer.analyze_measurement(voltages, currents, "DPV")
        
        print(f"\nResult object type: {type(result)}")
        print(f"Result attributes: {dir(result)}")
        
        # Check individual result attributes
        print(f"\nResult attribute types:")
        print(f"  timestamp: {type(result.timestamp)}")
        print(f"  measurement_type: {type(result.measurement_type)}")
        print(f"  confidence_score: {type(result.confidence_score)} = {result.confidence_score}")
        print(f"  peaks: {type(result.peaks)} length: {len(result.peaks)}")
        
        # Check peak types
        if result.peaks:
            peak = result.peaks[0]
            print(f"\nFirst peak attribute types:")
            for attr in ['voltage', 'current', 'index', 'height', 'width', 'area', 'prominence']:
                if hasattr(peak, attr):
                    value = getattr(peak, attr)
                    print(f"  {attr}: {type(value)} = {value}")
        
        # Check quality metrics
        print(f"\nQuality metrics type: {type(result.quality_metrics)}")
        if isinstance(result.quality_metrics, dict):
            for key, value in result.quality_metrics.items():
                print(f"  {key}: {type(value)} = {value}")
        
        # Check electrochemical params
        print(f"\nElectrochemical params type: {type(result.electrochemical_params)}")
        if hasattr(result, 'electrochemical_params') and isinstance(result.electrochemical_params, dict):
            for key, value in result.electrochemical_params.items():
                print(f"  {key}: {type(value)} = {value}")
        
        # Test manual peak processing
        print(f"\n🧪 Testing manual peak processing...")
        peaks_data = []
        for i, peak in enumerate(result.peaks):
            peak_dict = {
                'potential': peak.voltage,
                'current': peak.current,
                'index': peak.index,
                'height': peak.height,
                'width': peak.width,
                'area': peak.area
            }
            print(f"Peak {i} before conversion:")
            for key, value in peak_dict.items():
                print(f"    {key}: {type(value)} = {value}")
            
            # Apply conversion
            converted_peak = convert_numpy_types(peak_dict)
            print(f"Peak {i} after conversion:")
            for key, value in converted_peak.items():
                print(f"    {key}: {type(value)} = {value}")
            
            peaks_data.append(converted_peak)
            
            if i >= 1:  # Only show first 2 peaks
                break
        
        # Test JSON serialization
        print(f"\n🧪 Testing JSON serialization...")
        import json
        
        test_response = {
            'success': True,
            'data': {
                'peaks_detected': len(result.peaks),
                'peaks': peaks_data,
                'confidence_score': float(result.confidence_score),
                'quality_metrics': convert_numpy_types(result.quality_metrics)
            }
        }
        
        print(f"Response data before final conversion:")
        def print_types(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    print(f"{prefix}{key}: {type(value)}")
                    if isinstance(value, (dict, list)) and prefix.count("  ") < 2:
                        print_types(value, prefix + "  ")
            elif isinstance(obj, list) and obj:
                print(f"{prefix}[0]: {type(obj[0])}")
                if isinstance(obj[0], (dict, list)):
                    print_types(obj[0], prefix + "  ")
        
        print_types(test_response)
        
        # Final conversion
        final_response = convert_numpy_types(test_response)
        
        # Try JSON serialization
        json_str = json.dumps(final_response)
        print(f"\n✅ JSON serialization successful! Length: {len(json_str)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = debug_ai_types()
    sys.exit(0 if success else 1)
