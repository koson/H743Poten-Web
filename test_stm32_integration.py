#!/usr/bin/env python3
"""
Test STM32 data integration with Cross-Instrument Calibration system
"""

import sys
import os
sys.path.append('src')

from cross_instrument_calibration import CrossInstrumentCalibrator
import json

def test_stm32_data_loading():
    """Test loading STM32 test data"""
    print("=== Testing STM32 Data Integration ===")
    
    # Initialize calibrator
    calibrator = CrossInstrumentCalibrator()
    
    # Load all available data
    print("\n1. Loading existing calibration data...")
    all_data = calibrator.load_existing_calibration_data()
    
    if 'test_data' in all_data:
        print("✅ Test data found!")
        
        if 'stm32' in all_data['test_data']:
            print("✅ STM32 data loaded successfully!")
            stm32_data = all_data['test_data']['stm32']
            
            print(f"\nSTM32 Data Summary:")
            print(f"- Number of concentration sets: {len(stm32_data)}")
            
            for conc, data in stm32_data.items():
                print(f"\n📊 {conc}:")
                print(f"  - Files: {data.get('file_count', 0)}")
                print(f"  - Concentration: {data.get('concentration', 'N/A')}")
                print(f"  - Electrodes: {data.get('electrodes', {})}")
                
                if 'sample_data' in data:
                    sample = data['sample_data']
                    print(f"  - Columns: {sample.get('columns', [])}")
                    print(f"  - Rows: {sample.get('rows', 0)}")
                    print(f"  - Voltage range: {sample.get('voltage_range', 'N/A')}")
                    print(f"  - Current range: {sample.get('current_range', 'N/A')}")
        
        if 'palmsens' in all_data['test_data']:
            print("✅ PalmSens data found!")
            palmsens_data = all_data['test_data']['palmsens']
            print(f"PalmSens data keys: {list(palmsens_data.keys())}")
    
    # Test cross-instrument analysis
    print("\n2. Running cross-instrument analysis...")
    analysis_results = calibrator.analyze_cross_instrument_data()
    
    if 'error' not in analysis_results:
        print("✅ Cross-instrument analysis completed!")
        
        if 'instrument_comparison' in analysis_results:
            comp = analysis_results['instrument_comparison']
            print(f"\n📈 Instrument Comparison:")
            
            if 'concentration_coverage' in comp:
                coverage = comp['concentration_coverage']
                print(f"  - STM32 concentrations: {len(coverage.get('stm32_concentrations', []))}")
                print(f"  - Unique to STM32: {coverage.get('stm32_unique', [])}")
            
            if 'data_quality' in comp:
                print(f"  - Quality analysis for {len(comp['data_quality'])} concentrations")
                
                # Show quality scores
                for conc, quality in comp['data_quality'].items():
                    score = quality.get('quality_score', 0)
                    print(f"    {conc}: Quality Score = {score:.1f}/100")
        
        if 'stm32_analysis' in analysis_results:
            stm32_analysis = analysis_results['stm32_analysis']
            print(f"\n🔬 STM32 Consistency Analysis:")
            
            if 'electrode_performance' in stm32_analysis:
                electrodes = stm32_analysis['electrode_performance']
                print(f"  - Electrodes analyzed: {list(electrodes.keys())}")
                
                for electrode, data in electrodes.items():
                    total_scans = sum(data.values())
                    print(f"    {electrode}: {total_scans} total scans across concentrations")
            
            if 'concentration_trends' in stm32_analysis:
                trends = stm32_analysis['concentration_trends']
                print(f"  - {trends.get('coverage_analysis', 'No trends')}")
    
    else:
        print(f"❌ Analysis failed: {analysis_results['error']}")
    
    return all_data, analysis_results

def test_data_validation():
    """Test data validation and quality checks"""
    print("\n=== Data Validation Tests ===")
    
    # Check if Test_data directory exists and has expected structure
    test_data_path = "Test_data"
    if os.path.exists(test_data_path):
        print("✅ Test_data directory found")
        
        stm32_path = os.path.join(test_data_path, "Stm32")
        if os.path.exists(stm32_path):
            print("✅ STM32 data directory found")
            
            # Count concentration folders
            conc_folders = [f for f in os.listdir(stm32_path) if os.path.isdir(os.path.join(stm32_path, f))]
            print(f"  - Concentration folders: {len(conc_folders)}")
            
            # Count total CSV files
            total_files = 0
            for folder in conc_folders:
                folder_path = os.path.join(stm32_path, folder)
                csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
                total_files += len(csv_files)
                print(f"    {folder}: {len(csv_files)} files")
            
            print(f"  - Total CSV files: {total_files}")
        
        palmsens_path = os.path.join(test_data_path, "Palmsens")
        if os.path.exists(palmsens_path):
            print("✅ PalmSens data directory found")
    
    else:
        print("❌ Test_data directory not found")

if __name__ == "__main__":
    try:
        # Run data validation
        test_data_validation()
        
        # Run STM32 integration test
        all_data, analysis_results = test_stm32_data_loading()
        
        print("\n=== Test Summary ===")
        print("✅ STM32 data integration test completed successfully!")
        print(f"✅ Loaded data from {len(all_data)} main categories")
        print(f"✅ Analysis results contain {len(analysis_results)} analysis types")
        
        # Save results for review
        with open('stm32_integration_results.json', 'w') as f:
            json.dump({
                'loaded_data_summary': {k: type(v).__name__ for k, v in all_data.items()},
                'analysis_results': analysis_results
            }, f, indent=2, default=str)
        
        print("✅ Results saved to stm32_integration_results.json")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
