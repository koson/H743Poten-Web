#!/usr/bin/env python3
"""
Configuration file for 3-Method Peak Detection Framework
Centralized settings for DeepCV, TraditionalCV, and HybridCV

Author: H743Poten Research Team
Date: 2025-08-17
"""

from typing import Dict, Any
from pathlib import Path

class PeakDetectionConfig:
    """Configuration class for peak detection framework"""
    
    # Dataset Paths
    BASE_PATH = Path("validation_data")
    SPLITS_PATH = BASE_PATH / "splits"
    RESULTS_PATH = BASE_PATH / "results"
    METADATA_PATH = BASE_PATH / "metadata"
    
    # Traditional CV Configuration
    TRADITIONAL_CONFIG = {
        'smoothing_window': 5,        # Window size for Savitzky-Golay filter
        'min_peak_height': 1e-9,      # Minimum peak current (A)
        'min_peak_distance': 10,      # Minimum distance between peaks (data points)
        'prominence_factor': 0.1,     # Minimum prominence as fraction of max signal
        'baseline_window': 20,        # Window for baseline correction
        'snr_threshold': 2.0          # Signal-to-noise ratio threshold
    }
    
    # Deep Learning CV Configuration
    DEEP_CV_CONFIG = {
        'hidden_layers': (100, 50, 25),  # Neural network architecture
        'max_iter': 500,                 # Maximum training iterations
        'learning_rate': 0.001,          # Learning rate for optimization
        'random_state': 42,              # Random seed for reproducibility
        'feature_window': 10,            # Window size for feature extraction
        'min_training_samples': 50,      # Minimum samples before training
        'validation_split': 0.2,         # Fraction for validation during training
        'early_stopping_patience': 10    # Early stopping patience
    }
    
    # Hybrid CV Configuration
    HYBRID_CONFIG = {
        'traditional_weight': 0.6,       # Weight for traditional method
        'deep_weight': 0.4,             # Weight for deep learning method
        'consensus_threshold': 0.7,      # Confidence threshold for consensus
        'max_peak_difference': 0.05,     # Max voltage difference for peak matching (V)
        'ensemble_method': 'weighted',   # 'weighted', 'voting', 'stacking'
        'conflict_resolution': 'confidence'  # How to resolve conflicts
    }
    
    # Validation Configuration
    VALIDATION_CONFIG = {
        'dataset_splits': ['train', 'validation', 'test'],
        'parallel_processing': True,
        'max_workers': 4,               # Number of parallel workers
        'chunk_size': 50,               # Files per processing chunk
        'save_individual_results': True,
        'generate_plots': True,
        'plot_format': 'png',           # 'png', 'pdf', 'svg'
        'statistical_tests': True      # Perform statistical significance tests
    }
    
    # Data Loading Configuration
    DATA_CONFIG = {
        'voltage_columns': ['voltage', 'potential', 'v', 'e', 'V', 'E'],
        'current_columns': ['current', 'i', 'amp', 'I', 'A', 'Current'],
        'delimiter': ',',
        'header_rows': 0,               # Number of header rows to skip
        'min_data_points': 10,          # Minimum data points per file
        'max_data_points': 10000,       # Maximum data points (for memory)
        'interpolation_method': 'linear', # For missing data
        'outlier_detection': True       # Remove statistical outliers
    }
    
    # Quality Control Configuration
    QUALITY_CONFIG = {
        'min_confidence_score': 0.3,   # Minimum confidence to accept results
        'peak_validation_window': 5,    # Window for peak validation
        'current_noise_threshold': 1e-12, # Current noise level threshold
        'voltage_range_check': True,    # Validate voltage ranges
        'current_range_check': True,    # Validate current ranges
        'detect_saturation': True,      # Detect amplifier saturation
        'remove_baseline_drift': True   # Apply baseline drift correction
    }
    
    # Reporting Configuration
    REPORTING_CONFIG = {
        'include_plots': True,
        'plot_dpi': 300,               # Resolution for saved plots
        'plot_style': 'seaborn-v0_8',  # Matplotlib style
        'color_scheme': {
            'TraditionalCV': '#1f77b4',  # Blue
            'DeepCV': '#ff7f0e',         # Orange
            'HybridCV': '#2ca02c'        # Green
        },
        'report_format': 'json',        # 'json', 'html', 'pdf'
        'include_statistics': True,
        'include_method_comparison': True,
        'include_failure_analysis': True
    }
    
    # Cross-Instrument Calibration Configuration (Phase 2)
    CALIBRATION_CONFIG = {
        'reference_instrument': 'PalmSens',  # Reference for calibration
        'target_instrument': 'STM32H743',    # Instrument to calibrate
        'calibration_features': [
            'peak_potential', 'peak_current', 'peak_separation',
            'peak_area', 'peak_symmetry', 'baseline_current'
        ],
        'calibration_model': 'random_forest',  # 'linear', 'polynomial', 'random_forest'
        'cross_validation_folds': 5,
        'feature_importance_analysis': True,
        'transfer_learning': True            # Use pre-trained models
    }
    
    # Performance Optimization
    PERFORMANCE_CONFIG = {
        'use_multiprocessing': True,
        'cache_results': True,
        'cache_directory': BASE_PATH / "cache",
        'memory_limit_mb': 1024,         # Memory limit for large datasets
        'progress_reporting_interval': 100, # Report progress every N files
        'auto_cleanup_temp_files': True,
        'profile_performance': False      # Enable performance profiling
    }
    
    # Experimental Features (Advanced)
    EXPERIMENTAL_CONFIG = {
        'adaptive_thresholding': True,    # Adaptive peak detection thresholds
        'multi_scale_analysis': False,   # Multi-resolution peak detection
        'uncertainty_quantification': True, # Bayesian uncertainty estimates
        'online_learning': False,        # Update models with new data
        'federated_learning': False,     # Distributed model training
        'explainable_ai': True          # Generate explanations for predictions
    }
    
    @classmethod
    def get_config(cls, method: str) -> Dict[str, Any]:
        """Get configuration for specific method"""
        config_map = {
            'traditional': cls.TRADITIONAL_CONFIG,
            'deep': cls.DEEP_CV_CONFIG,
            'hybrid': cls.HYBRID_CONFIG,
            'validation': cls.VALIDATION_CONFIG,
            'data': cls.DATA_CONFIG,
            'quality': cls.QUALITY_CONFIG,
            'reporting': cls.REPORTING_CONFIG,
            'calibration': cls.CALIBRATION_CONFIG,
            'performance': cls.PERFORMANCE_CONFIG,
            'experimental': cls.EXPERIMENTAL_CONFIG
        }
        
        return config_map.get(method.lower(), {})
    
    @classmethod
    def get_all_configs(cls) -> Dict[str, Dict[str, Any]]:
        """Get all configuration dictionaries"""
        return {
            'traditional': cls.TRADITIONAL_CONFIG,
            'deep_cv': cls.DEEP_CV_CONFIG,
            'hybrid': cls.HYBRID_CONFIG,
            'validation': cls.VALIDATION_CONFIG,
            'data': cls.DATA_CONFIG,
            'quality': cls.QUALITY_CONFIG,
            'reporting': cls.REPORTING_CONFIG,
            'calibration': cls.CALIBRATION_CONFIG,
            'performance': cls.PERFORMANCE_CONFIG,
            'experimental': cls.EXPERIMENTAL_CONFIG
        }
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories for the framework"""
        directories = [
            cls.BASE_PATH,
            cls.SPLITS_PATH,
            cls.RESULTS_PATH,
            cls.METADATA_PATH,
            cls.PERFORMANCE_CONFIG['cache_directory'],
            cls.RESULTS_PATH / "plots",
            cls.RESULTS_PATH / "individual_results",
            cls.RESULTS_PATH / "reports"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"📁 Created directory: {directory}")
    
    @classmethod
    def validate_configuration(cls) -> bool:
        """Validate configuration parameters"""
        try:
            # Check weights sum to 1.0 for hybrid method
            weight_sum = cls.HYBRID_CONFIG['traditional_weight'] + cls.HYBRID_CONFIG['deep_weight']
            if abs(weight_sum - 1.0) > 1e-6:
                print(f"⚠️  Warning: Hybrid weights sum to {weight_sum}, not 1.0")
            
            # Check thresholds are in valid ranges
            if not 0 <= cls.HYBRID_CONFIG['consensus_threshold'] <= 1:
                print("❌ Error: consensus_threshold must be between 0 and 1")
                return False
            
            if not 0 <= cls.QUALITY_CONFIG['min_confidence_score'] <= 1:
                print("❌ Error: min_confidence_score must be between 0 and 1")
                return False
            
            # Check neural network architecture
            if len(cls.DEEP_CV_CONFIG['hidden_layers']) == 0:
                print("❌ Error: Neural network must have at least one hidden layer")
                return False
            
            print("✅ Configuration validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")
            return False
    
    @classmethod
    def print_summary(cls):
        """Print configuration summary"""
        print("🔧 Peak Detection Framework Configuration")
        print("=" * 50)
        print(f"📁 Base Path: {cls.BASE_PATH}")
        print(f"🧠 Deep Learning Architecture: {cls.DEEP_CV_CONFIG['hidden_layers']}")
        print(f"⚖️  Hybrid Weights: Traditional={cls.HYBRID_CONFIG['traditional_weight']:.1f}, Deep={cls.HYBRID_CONFIG['deep_weight']:.1f}")
        print(f"🎯 Min Confidence: {cls.QUALITY_CONFIG['min_confidence_score']:.1f}")
        print(f"🔄 Parallel Processing: {cls.VALIDATION_CONFIG['parallel_processing']}")
        print(f"📊 Generate Plots: {cls.REPORTING_CONFIG['include_plots']}")
        print(f"🚀 Experimental Features: {sum(cls.EXPERIMENTAL_CONFIG.values())} enabled")

# Configuration presets for different use cases
class ConfigPresets:
    """Predefined configuration presets for common scenarios"""
    
    @staticmethod
    def get_fast_validation_config():
        """Configuration for fast validation (reduced accuracy)"""
        config = PeakDetectionConfig.get_all_configs()
        
        # Reduce processing requirements
        config['traditional']['smoothing_window'] = 3
        config['deep_cv']['hidden_layers'] = (50, 25)
        config['deep_cv']['max_iter'] = 200
        config['validation']['parallel_processing'] = True
        config['validation']['max_workers'] = 8
        config['reporting']['include_plots'] = False
        
        return config
    
    @staticmethod
    def get_high_accuracy_config():
        """Configuration for high accuracy validation (slower)"""
        config = PeakDetectionConfig.get_all_configs()
        
        # Increase processing quality
        config['traditional']['smoothing_window'] = 7
        config['traditional']['min_peak_distance'] = 5
        config['deep_cv']['hidden_layers'] = (200, 100, 50, 25)
        config['deep_cv']['max_iter'] = 1000
        config['quality']['min_confidence_score'] = 0.5
        config['experimental']['adaptive_thresholding'] = True
        config['experimental']['uncertainty_quantification'] = True
        
        return config
    
    @staticmethod
    def get_research_config():
        """Configuration for research/development purposes"""
        config = PeakDetectionConfig.get_all_configs()
        
        # Enable all features
        config['validation']['generate_plots'] = True
        config['reporting']['include_statistics'] = True
        config['reporting']['include_failure_analysis'] = True
        config['performance']['profile_performance'] = True
        
        # Enable experimental features
        for key in config['experimental']:
            if key not in ['federated_learning', 'online_learning']:  # Keep some disabled
                config['experimental'][key] = True
        
        return config
    
    @staticmethod
    def get_production_config():
        """Configuration for production deployment"""
        config = PeakDetectionConfig.get_all_configs()
        
        # Optimize for speed and reliability
        config['validation']['parallel_processing'] = True
        config['performance']['use_multiprocessing'] = True
        config['performance']['cache_results'] = True
        config['quality']['min_confidence_score'] = 0.4
        config['reporting']['include_plots'] = False
        
        # Disable experimental features
        for key in config['experimental']:
            config['experimental'][key] = False
        
        return config

if __name__ == "__main__":
    # Configuration demonstration
    print("🔧 Peak Detection Configuration System")
    print("=" * 50)
    
    # Create directories
    PeakDetectionConfig.create_directories()
    
    # Validate configuration
    PeakDetectionConfig.validate_configuration()
    
    # Print summary
    PeakDetectionConfig.print_summary()
    
    print("\n📋 Available Configuration Presets:")
    print("1. Fast Validation (speed-optimized)")
    print("2. High Accuracy (quality-optimized)")
    print("3. Research (full-featured)")
    print("4. Production (deployment-ready)")
