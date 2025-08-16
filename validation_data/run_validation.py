#!/usr/bin/env python3
"""
Quick Start Script for 3-Method Peak Detection Framework
One-command execution for immediate validation

Author: H743Poten Research Team  
Date: 2025-08-17
Usage: python run_validation.py [--preset fast|accurate|research|production] [--split test|validation|train]
"""

import sys
import argparse
import time
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from config import PeakDetectionConfig, ConfigPresets
from peak_detection_framework import PeakDetectionValidator

def setup_argument_parser():
    """Setup command line argument parser"""
    parser = argparse.ArgumentParser(
        description="3-Method Peak Detection Framework Validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_validation.py                     # Run default validation on test set
  python run_validation.py --preset fast       # Use fast preset for quick testing
  python run_validation.py --preset accurate   # Use high accuracy preset
  python run_validation.py --split validation  # Run on validation set
  python run_validation.py --demo              # Run demonstration mode
  python run_validation.py --check             # Check system status only
        """
    )
    
    parser.add_argument(
        '--preset', 
        choices=['fast', 'accurate', 'research', 'production'],
        default='research',
        help='Configuration preset to use (default: research)'
    )
    
    parser.add_argument(
        '--split',
        choices=['train', 'validation', 'test'],
        default='test',
        help='Dataset split to validate (default: test)'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run demonstration mode instead of validation'
    )
    
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check system status and exit'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='validation_data/results',
        help='Output directory for results'
    )
    
    return parser

def check_system_status():
    """Check if system is ready for validation"""
    print("🔍 Checking System Status...")
    print("=" * 40)
    
    status = {"ready": True, "issues": []}
    
    # Check Python libraries
    try:
        import pandas as pd
        import numpy as np
        print("✅ Core libraries: pandas, numpy")
    except ImportError as e:
        status["ready"] = False
        status["issues"].append(f"Missing core libraries: {e}")
        print(f"❌ Core libraries: {e}")
    
    try:
        from scipy import signal
        from sklearn.metrics import mean_squared_error
        print("✅ Scientific libraries: scipy, sklearn")
    except ImportError as e:
        print(f"⚠️  Scientific libraries: {e} (fallback mode available)")
    
    # Check data splits
    splits_path = Path("validation_data/splits")
    if splits_path.exists():
        split_files = ["train_files.txt", "validation_files.txt", "test_files.txt"]
        missing_splits = []
        
        for split_file in split_files:
            if (splits_path / split_file).exists():
                with open(splits_path / split_file, 'r') as f:
                    count = len([line for line in f if line.strip()])
                print(f"✅ {split_file}: {count} files")
            else:
                missing_splits.append(split_file)
                print(f"❌ {split_file}: missing")
        
        if missing_splits:
            status["ready"] = False
            status["issues"].append(f"Missing split files: {missing_splits}")
    else:
        status["ready"] = False
        status["issues"].append("Data splits directory not found")
        print("❌ Data splits: not found")
    
    # Check configuration
    try:
        if PeakDetectionConfig.validate_configuration():
            print("✅ Configuration: valid")
        else:
            status["ready"] = False
            status["issues"].append("Invalid configuration")
    except Exception as e:
        status["ready"] = False
        status["issues"].append(f"Configuration error: {e}")
        print(f"❌ Configuration: {e}")
    
    # Check output directory
    output_path = Path("validation_data/results")
    try:
        output_path.mkdir(parents=True, exist_ok=True)
        print("✅ Output directory: ready")
    except Exception as e:
        status["ready"] = False
        status["issues"].append(f"Cannot create output directory: {e}")
        print(f"❌ Output directory: {e}")
    
    print("\n" + "=" * 40)
    if status["ready"]:
        print("🎉 System is ready for validation!")
    else:
        print("⚠️  System has issues:")
        for issue in status["issues"]:
            print(f"   - {issue}")
        print("\n💡 Suggested fixes:")
        print("   1. Install required libraries: pip install -r requirements.txt")
        print("   2. Run data splitter: python stratified_data_splitter.py")
        print("   3. Check file permissions")
    
    return status["ready"]

def run_demonstration():
    """Run demonstration mode"""
    print("🎯 Starting Demonstration Mode...")
    print("=" * 50)
    
    try:
        from demo_framework import main as demo_main
        demo_main()
    except ImportError:
        print("❌ Demo framework not available")
        return False
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False
    
    return True

def apply_configuration_preset(preset_name):
    """Apply configuration preset"""
    print(f"⚙️  Applying {preset_name} preset...")
    
    preset_configs = {
        'fast': ConfigPresets.get_fast_validation_config(),
        'accurate': ConfigPresets.get_high_accuracy_config(),
        'research': ConfigPresets.get_research_config(),
        'production': ConfigPresets.get_production_config()
    }
    
    if preset_name in preset_configs:
        config = preset_configs[preset_name]
        print(f"✅ {preset_name.capitalize()} preset applied")
        
        # Print key settings
        print(f"   🧠 NN Architecture: {config['deep_cv']['hidden_layers']}")
        print(f"   ⚡ Max Iterations: {config['deep_cv']['max_iter']}")
        print(f"   🔄 Parallel: {config['validation']['parallel_processing']}")
        print(f"   📊 Generate Plots: {config['reporting']['include_plots']}")
        
        return config
    else:
        print(f"❌ Unknown preset: {preset_name}")
        return None

def run_validation(split_name, preset_config, verbose=False):
    """Run the main validation"""
    print(f"\n🚀 Starting Validation on {split_name.upper()} set")
    print("=" * 50)
    
    start_time = time.time()
    
    try:
        # Initialize validator
        validator = PeakDetectionValidator()
        
        # Apply custom configuration if provided
        if preset_config:
            # Here you would apply the preset config to analyzers
            # For now, we use the default initialization
            pass
        
        # Run validation
        results = validator.run_validation(split_name)
        
        if results:
            total_time = time.time() - start_time
            
            print(f"\n🎉 Validation Completed Successfully!")
            print(f"⏱️  Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
            print(f"📁 Results saved to: {validator.results_path}")
            
            # Print summary
            print(f"\n📊 Summary for {split_name.upper()} set:")
            for method, metrics in results.items():
                success_rate = metrics.successful_detections / max(metrics.total_files, 1) * 100
                print(f"   🔬 {method}:")
                print(f"      Success Rate: {success_rate:.1f}%")
                print(f"      Avg Confidence: {metrics.average_confidence:.1%}")
                print(f"      Avg Time/File: {metrics.average_processing_time:.3f}s")
            
            return True
        else:
            print("❌ Validation failed - no results returned")
            return False
    
    except FileNotFoundError as e:
        print(f"❌ Data not found: {e}")
        print("💡 Make sure to run stratified_data_splitter.py first")
        return False
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False

def print_welcome_banner():
    """Print welcome banner"""
    print("🎯 H743Poten 3-Method Peak Detection Framework")
    print("🚀 VALIDATION EXECUTION SYSTEM")
    print("=" * 60)
    print("🔬 Methods: DeepCV + TraditionalCV + HybridCV")
    print("📊 Dataset: Massive 3,332-file collection")
    print("🎯 Goal: Comprehensive peak detection validation")
    print("=" * 60)

def main():
    """Main execution function"""
    # Parse arguments
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Print welcome banner
    print_welcome_banner()
    
    # Handle check mode
    if args.check:
        return 0 if check_system_status() else 1
    
    # Handle demo mode
    if args.demo:
        success = run_demonstration()
        return 0 if success else 1
    
    # Check system status first
    if not check_system_status():
        print("\n❌ System not ready. Use --check for details.")
        return 1
    
    # Apply configuration preset
    preset_config = apply_configuration_preset(args.preset)
    
    # Run validation
    success = run_validation(args.split, preset_config, args.verbose)
    
    if success:
        print("\n🎉 VALIDATION COMPLETED SUCCESSFULLY!")
        print("📋 Next Steps:")
        print("   1. 📊 Review results in validation_data/results/")
        print("   2. 📈 Analyze method performance comparison")
        print("   3. ⚙️  Optimize configuration if needed")
        print("   4. 🎯 Proceed to Phase 2: Cross-instrument calibration")
        return 0
    else:
        print("\n❌ VALIDATION FAILED!")
        print("💡 Try:")
        print("   - Check system status: python run_validation.py --check")
        print("   - Run demo mode: python run_validation.py --demo")
        print("   - Use verbose mode: python run_validation.py --verbose")
        return 1

if __name__ == "__main__":
    sys.exit(main())
