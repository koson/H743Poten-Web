#!/usr/bin/env python3
"""
Demo Script for 3-Method Peak Detection Framework
Demonstrates usage and capabilities of the validation system

Author: H743Poten Research Team
Date: 2025-08-17
"""

import sys
import time
import numpy as np
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from config import PeakDetectionConfig, ConfigPresets
from peak_detection_framework import (
    PeakDetectionValidator, 
    TraditionalCVAnalyzer, 
    DeepCVAnalyzer, 
    HybridCVAnalyzer,
    PeakDetectionResult
)

def demo_single_file_analysis():
    """Demonstrate single file analysis with all three methods"""
    print("\n🔬 Demo 1: Single File Analysis")
    print("=" * 40)
    
    # Create sample CV data
    voltages = np.linspace(-0.5, 0.5, 200)
    
    # Simulate CV curve with peaks
    currents = (
        2e-6 * np.exp(-((voltages - 0.2) / 0.05)**2) +    # Anodic peak
        -1.5e-6 * np.exp(-((voltages + 0.2) / 0.05)**2) + # Cathodic peak
        1e-8 * voltages +                                   # Linear background
        5e-9 * np.random.normal(0, 1, len(voltages))       # Noise
    )
    
    print(f"📊 Sample data: {len(voltages)} points")
    print(f"⚡ Voltage range: {voltages.min():.2f} to {voltages.max():.2f} V")
    print(f"🔌 Current range: {currents.min():.2e} to {currents.max():.2e} A")
    
    # Initialize analyzers
    traditional = TraditionalCVAnalyzer()
    deep = DeepCVAnalyzer()
    hybrid = HybridCVAnalyzer()
    
    print("\n🎯 Running peak detection...")
    
    # Analyze with all methods
    results = []
    for analyzer, name in [(traditional, "Traditional"), (deep, "Deep Learning"), (hybrid, "Hybrid")]:
        start_time = time.time()
        result = analyzer.detect_peaks(voltages, currents, "demo_sample.csv")
        elapsed = time.time() - start_time
        
        print(f"\n🔬 {name} Method:")
        print(f"   Peaks detected: {result.peaks_detected}")
        print(f"   Processing time: {elapsed:.3f}s")
        print(f"   Confidence: {result.confidence_score:.1%}")
        print(f"   Anodic peaks: {len(result.anodic_peaks)}")
        print(f"   Cathodic peaks: {len(result.cathodic_peaks)}")
        if result.peak_separation:
            print(f"   Peak separation: {result.peak_separation:.3f}V")
        
        results.append(result)
    
    print("\n✅ Single file analysis completed!")
    return results

def demo_configuration_system():
    """Demonstrate configuration system"""
    print("\n⚙️  Demo 2: Configuration System")
    print("=" * 40)
    
    # Show default configuration
    PeakDetectionConfig.print_summary()
    
    print("\n📋 Available Presets:")
    presets = {
        "Fast": ConfigPresets.get_fast_validation_config(),
        "High Accuracy": ConfigPresets.get_high_accuracy_config(),
        "Research": ConfigPresets.get_research_config(),
        "Production": ConfigPresets.get_production_config()
    }
    
    for name, config in presets.items():
        traditional_config = config['traditional']
        deep_config = config['deep_cv']
        
        print(f"\n📌 {name} Preset:")
        print(f"   Smoothing window: {traditional_config['smoothing_window']}")
        print(f"   NN architecture: {deep_config['hidden_layers']}")
        print(f"   Max iterations: {deep_config['max_iter']}")
        print(f"   Parallel processing: {config['validation']['parallel_processing']}")
    
    print("\n✅ Configuration system demonstrated!")

def demo_data_loading():
    """Demonstrate data loading capabilities"""
    print("\n📁 Demo 3: Data Loading System")
    print("=" * 40)
    
    # Check for actual data files
    splits_path = Path("splits")
    
    if splits_path.exists():
        print("📊 Checking available data splits...")
        
        for split_file in ["train_files.txt", "validation_files.txt", "test_files.txt"]:
            file_path = splits_path / split_file
            if file_path.exists():
                with open(file_path, 'r') as f:
                    lines = [line.strip() for line in f if line.strip()]
                
                split_name = split_file.replace('_files.txt', '')
                print(f"   {split_name.capitalize()}: {len(lines)} files")
                
                # Show sample filenames
                if lines:
                    print(f"      Sample files:")
                    for filename in lines[:3]:
                        print(f"        - {Path(filename).name}")
                    if len(lines) > 3:
                        print(f"        ... and {len(lines) - 3} more")
            else:
                print(f"❌ {split_file} not found")
    else:
        print("❌ Splits directory not found")
        print("💡 Run stratified_data_splitter.py first to create data splits")
    
    print("\n✅ Data loading check completed!")

def demo_validator_initialization():
    """Demonstrate validator initialization"""
    print("\n🎯 Demo 4: Validator Initialization")
    print("=" * 40)
    
    try:
        # Create directories if they don't exist
        PeakDetectionConfig.create_directories()
        
        # Initialize validator
        validator = PeakDetectionValidator()
        
        print("✅ Validator initialized successfully!")
        print(f"📁 Base path: {validator.base_path}")
        print(f"📊 Results path: {validator.results_path}")
        print(f"🔬 Analyzers ready: 3 methods")
        
        # Test analyzer initialization
        analyzers = [
            ("Traditional", validator.traditional_analyzer),
            ("Deep Learning", validator.deep_analyzer),
            ("Hybrid", validator.hybrid_analyzer)
        ]
        
        print("\n🔬 Analyzer Status:")
        for name, analyzer in analyzers:
            config_available = hasattr(analyzer, 'config') and analyzer.config is not None
            print(f"   {name}: {'✅ Ready' if config_available else '⚠️  Limited config'}")
        
    except Exception as e:
        print(f"❌ Validator initialization failed: {e}")
    
    print("\n✅ Validator initialization check completed!")

def demo_performance_estimation():
    """Estimate performance for different dataset sizes"""
    print("\n⚡ Demo 5: Performance Estimation")
    print("=" * 40)
    
    # Simulate processing times based on method complexity
    single_file_times = {
        "Traditional": 0.005,  # Fast signal processing
        "Deep Learning": 0.050,  # Neural network overhead
        "Hybrid": 0.055        # Combined approach
    }
    
    # Estimate for different dataset sizes
    dataset_sizes = [100, 500, 1000, 2000, 3332]  # Including our actual dataset
    
    print("📊 Estimated Processing Times:")
    print(f"{'Dataset Size':<12} {'Traditional':<12} {'Deep Learning':<15} {'Hybrid':<10}")
    print("-" * 55)
    
    for size in dataset_sizes:
        traditional_time = size * single_file_times["Traditional"]
        deep_time = size * single_file_times["Deep Learning"]
        hybrid_time = size * single_file_times["Hybrid"]
        
        print(f"{size:<12} {traditional_time:<12.1f}s {deep_time:<15.1f}s {hybrid_time:<10.1f}s")
    
    # Special note for our dataset
    actual_size = 3332
    total_time = actual_size * sum(single_file_times.values())
    print(f"\n🎯 For our dataset ({actual_size} files):")
    print(f"   Estimated total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"   With 4 parallel workers: {total_time/4:.1f}s ({total_time/240:.1f} minutes)")
    
    print("\n✅ Performance estimation completed!")

def demo_feature_capabilities():
    """Demonstrate framework capabilities"""
    print("\n🚀 Demo 6: Framework Capabilities")
    print("=" * 40)
    
    capabilities = {
        "Peak Detection Methods": [
            "Traditional signal processing (scipy)",
            "Deep learning (neural networks)", 
            "Hybrid ensemble approach"
        ],
        "Data Formats": [
            "CSV files with flexible column detection",
            "Voltage/potential and current data",
            "Multiple naming conventions"
        ],
        "Validation Features": [
            "Stratified train/validation/test splits",
            "Cross-instrument validation",
            "Leave-one-condition-out (LOCO)",
            "Statistical performance metrics"
        ],
        "Output & Reporting": [
            "JSON result files",
            "Individual analysis results",
            "Comprehensive validation reports",
            "Performance comparisons"
        ],
        "Quality Control": [
            "Confidence scoring",
            "Baseline correction",
            "Noise filtering",
            "Outlier detection"
        ],
        "Advanced Features": [
            "Parallel processing",
            "Memory optimization",
            "Configurable parameters",
            "Fallback implementations"
        ]
    }
    
    for category, features in capabilities.items():
        print(f"\n📋 {category}:")
        for feature in features:
            print(f"   ✅ {feature}")
    
    print("\n🎯 Ready for Phase 2: Cross-Instrument Calibration")
    print("   🔬 STM32H743 → PalmSens calibration")
    print("   🤖 Machine learning transfer models")
    print("   📊 Real-time calibration adjustment")
    
    print("\n✅ Capability overview completed!")

def main():
    """Main demo execution"""
    print("🎯 H743Poten 3-Method Peak Detection Framework")
    print("🚀 DEMONSTRATION MODE")
    print("=" * 60)
    print("📊 Showcasing DeepCV + TraditionalCV + HybridCV validation")
    
    # Run all demos
    demos = [
        demo_single_file_analysis,
        demo_configuration_system,
        demo_data_loading,
        demo_validator_initialization,
        demo_performance_estimation,
        demo_feature_capabilities
    ]
    
    for i, demo_func in enumerate(demos, 1):
        try:
            demo_func()
        except Exception as e:
            print(f"❌ Demo {i} failed: {e}")
        
        if i < len(demos):
            input("\n⏸️  Press Enter to continue to next demo...")
    
    print("\n🎉 ALL DEMOS COMPLETED!")
    print("=" * 60)
    print("🚀 Framework is ready for validation execution!")
    print("📝 To run actual validation:")
    print("   python peak_detection_framework.py")
    print("\n💡 Next Steps:")
    print("   1. ✅ Run validation on test dataset")
    print("   2. 📊 Analyze method performance")
    print("   3. 🔬 Optimize configurations")
    print("   4. 🎯 Begin Phase 2 calibration")

if __name__ == "__main__":
    main()
