#!/usr/bin/env python3
"""
🧪 DeepCV V2 Comprehensive Test Suite
====================================

Complete testing framework for DeepCV V2 system including unit tests,
integration tests, performance benchmarks, and validation tests.

Author: H743Poten Research Team
Date: October 4, 2025
Version: 2.0.0

Test Categories:
- Architecture Tests: Neural network components
- Feature Engineering Tests: Multi-scale analysis
- Uncertainty Tests: Bayesian methods and confidence
- Persistence Tests: Model save/load and transfer
- Real-time Tests: Optimization and streaming
- Integration Tests: End-to-end pipeline
- Performance Tests: Benchmarking and profiling
"""

import unittest
import numpy as np
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import logging
import json
import argparse

# Test framework setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try importing PyTorch with fallback
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️  PyTorch not available - skipping PyTorch-dependent tests")

# Import our modules with fallbacks
try:
    from deepcv_v2 import DeepCVAnalyzerV2, DeepCVResult
    DEEPCV_AVAILABLE = True
except ImportError:
    DEEPCV_AVAILABLE = False
    print("⚠️  DeepCV V2 main module not available")

try:
    from deepcv_v2_uncertainty import UncertaintyQuantifier, UncertaintyEstimate
    UNCERTAINTY_AVAILABLE = True
except ImportError:
    UNCERTAINTY_AVAILABLE = False
    print("⚠️  Uncertainty module not available")

try:
    from deepcv_v2_multiscale import MultiScaleMultiModalAnalyzer
    MULTISCALE_AVAILABLE = True
except ImportError:
    MULTISCALE_AVAILABLE = False
    print("⚠️  Multiscale module not available")

try:
    from deepcv_v2_realtime import RealTimeOptimizer, OptimizationConfig
    REALTIME_AVAILABLE = True
except ImportError:
    REALTIME_AVAILABLE = False
    print("⚠️  Real-time module not available")

try:
    from deepcv_v2_persistence import ModelVersionManager, TransferLearningManager
    PERSISTENCE_AVAILABLE = True
except ImportError:
    PERSISTENCE_AVAILABLE = False
    print("⚠️  Persistence module not available")

class TestDataGenerator:
    """Generate synthetic test data for validation"""
    
    @staticmethod
    def generate_cv_data(n_points: int = 200, noise_level: float = 0.02) -> Tuple[np.ndarray, np.ndarray]:
        """Generate synthetic CV data"""
        voltage = np.linspace(-1.0, 1.0, n_points)
        
        # Multi-component current signal
        current = (0.1 * np.sin(3 * np.pi * voltage) + 
                  0.05 * np.sin(7 * np.pi * voltage) +
                  noise_level * np.random.randn(n_points))
        
        return voltage, current
    
    @staticmethod
    def add_synthetic_peaks(current: np.ndarray, peak_positions: List[int], 
                          peak_intensities: Optional[List[float]] = None) -> np.ndarray:
        """Add synthetic peaks to current signal"""
        current_with_peaks = current.copy()
        
        if peak_intensities is None:
            peak_intensities = [0.3] * len(peak_positions)
        
        for pos, intensity in zip(peak_positions, peak_intensities):
            if 0 <= pos < len(current_with_peaks):
                current_with_peaks[pos] += intensity * (1 + 0.1 * np.random.randn())
        
        return current_with_peaks
    
    @staticmethod
    def generate_training_dataset(n_samples: int = 50) -> List[Dict[str, Any]]:
        """Generate a complete training dataset"""
        dataset = []
        
        for i in range(n_samples):
            # Generate base signal
            voltage, current = TestDataGenerator.generate_cv_data()
            
            # Add random peaks
            n_peaks = np.random.randint(1, 6)  # 1-5 peaks
            peak_positions = np.random.choice(
                range(20, len(current) - 20), 
                n_peaks, 
                replace=False
            ).tolist()
            
            current_with_peaks = TestDataGenerator.add_synthetic_peaks(
                current, peak_positions
            )
            
            dataset.append({
                'voltages': voltage,
                'currents': current_with_peaks,
                'peak_positions': peak_positions,
                'sample_id': i
            })
        
        return dataset

class DeepCVArchitectureTests(unittest.TestCase):
    """Test neural network architecture components"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'batch_size': 8,
            'epochs': 5,  # Reduced for testing
            'learning_rate': 0.001,
            'min_training_samples': 10  # Reduced for testing
        }
        
        if DEEPCV_AVAILABLE:
            self.analyzer = DeepCVAnalyzerV2(self.config)
        
        # Generate test data
        self.voltage, self.current = TestDataGenerator.generate_cv_data()
        self.peak_positions = [50, 120, 150]
        self.current = TestDataGenerator.add_synthetic_peaks(
            self.current, self.peak_positions
        )
    
    @unittest.skipIf(not DEEPCV_AVAILABLE, "DeepCV V2 not available")
    def test_analyzer_initialization(self):
        """Test analyzer initialization"""
        self.assertIsNotNone(self.analyzer)
        self.assertEqual(self.analyzer.config['batch_size'], 8)
        self.assertFalse(self.analyzer.is_trained)
        self.assertEqual(len(self.analyzer.training_data), 0)
    
    @unittest.skipIf(not DEEPCV_AVAILABLE, "DeepCV V2 not available")
    def test_feature_extraction(self):
        """Test feature extraction"""
        features = self.analyzer.feature_extractor.extract_features(
            self.voltage, self.current
        )
        
        self.assertIsNotNone(features)
        self.assertEqual(len(features), len(self.voltage))
        self.assertGreater(features.shape[1], 10)  # Should have multiple features
    
    @unittest.skipIf(not DEEPCV_AVAILABLE, "DeepCV V2 not available")
    def test_training_data_addition(self):
        """Test adding training data"""
        initial_count = len(self.analyzer.training_data)
        
        self.analyzer.add_training_data(
            self.voltage, self.current, self.peak_positions
        )
        
        self.assertEqual(len(self.analyzer.training_data), initial_count + 1)
        
        # Check data integrity
        sample = self.analyzer.training_data[-1]
        self.assertEqual(len(sample['voltages']), len(self.voltage))
        self.assertEqual(len(sample['currents']), len(self.current))
        self.assertEqual(sample['ground_truth_peaks'], self.peak_positions)
    
    @unittest.skipIf(not DEEPCV_AVAILABLE or not TORCH_AVAILABLE, "Dependencies not available")
    def test_model_architecture(self):
        """Test neural network model architecture"""
        # Add sufficient training data
        dataset = TestDataGenerator.generate_training_dataset(15)
        for sample in dataset:
            self.analyzer.add_training_data(
                sample['voltages'], 
                sample['currents'], 
                sample['peak_positions']
            )
        
        # Train model
        success = self.analyzer.train(save_model=False)
        self.assertTrue(success)
        self.assertTrue(self.analyzer.is_trained)
        self.assertIsNotNone(self.analyzer.model)
    
    @unittest.skipIf(not DEEPCV_AVAILABLE, "DeepCV V2 not available")
    def test_peak_detection_basic(self):
        """Test basic peak detection functionality"""
        result = self.analyzer.detect_peaks(
            self.voltage, self.current, "test_sample.csv"
        )
        
        self.assertIsInstance(result, DeepCVResult)
        self.assertEqual(result.method, "DeepCV")
        self.assertEqual(result.version, "2.0.0")
        self.assertGreaterEqual(result.peaks_detected, 0)
        self.assertIsInstance(result.peak_potentials, list)
        self.assertIsInstance(result.peak_currents, list)

class FeatureEngineeringTests(unittest.TestCase):
    """Test multi-scale and multi-modal feature engineering"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.voltage, self.current = TestDataGenerator.generate_cv_data(300)
        
        if MULTISCALE_AVAILABLE:
            self.analyzer = MultiScaleMultiModalAnalyzer()
    
    @unittest.skipIf(not MULTISCALE_AVAILABLE, "Multiscale module not available")
    def test_multiscale_feature_extraction(self):
        """Test multi-scale feature extraction"""
        ms_features = self.analyzer.extract_comprehensive_features(
            self.voltage, self.current
        )
        
        self.assertIsNotNone(ms_features.fusion_features)
        self.assertGreater(ms_features.fusion_features.shape[1], 10)
        self.assertIn('scales_used', ms_features.metadata)
        self.assertGreater(len(ms_features.features_by_scale), 0)
    
    @unittest.skipIf(not MULTISCALE_AVAILABLE, "Multiscale module not available")
    def test_wavelet_decomposition(self):
        """Test wavelet multi-scale decomposition"""
        scale_features = self.analyzer.wavelet_analyzer.decompose_signal(self.current)
        
        self.assertIsInstance(scale_features, dict)
        self.assertGreater(len(scale_features), 0)
        
        for scale, features in scale_features.items():
            self.assertIsInstance(features, np.ndarray)
            self.assertGreater(features.shape[1], 0)
    
    @unittest.skipIf(not MULTISCALE_AVAILABLE, "Multiscale module not available")
    def test_time_frequency_analysis(self):
        """Test time-frequency analysis"""
        freqs, times, spectrogram = self.analyzer.tf_analyzer.compute_spectrogram(self.current)
        
        self.assertIsInstance(freqs, np.ndarray)
        self.assertIsInstance(times, np.ndarray)
        self.assertIsInstance(spectrogram, np.ndarray)
        self.assertEqual(len(freqs), spectrogram.shape[0])
        self.assertEqual(len(times), spectrogram.shape[1])
    
    @unittest.skipIf(not MULTISCALE_AVAILABLE, "Multiscale module not available")
    def test_multimodal_fusion(self):
        """Test multi-modal data fusion"""
        # Create mock features
        v_features = np.random.randn(200, 5)
        i_features = np.random.randn(200, 5)
        d_features = np.random.randn(200, 5)
        
        fused = self.analyzer.fusion_analyzer.fuse_modalities(
            v_features, i_features, d_features
        )
        
        self.assertIsInstance(fused, np.ndarray)
        self.assertEqual(len(fused), 200)
        self.assertGreater(fused.shape[1], 0)

class UncertaintyQuantificationTests(unittest.TestCase):
    """Test uncertainty quantification methods"""
    
    def setUp(self):
        """Set up test fixtures"""
        if UNCERTAINTY_AVAILABLE:
            self.quantifier = UncertaintyQuantifier({
                'mc_samples': 20,  # Reduced for testing
                'confidence_levels': [0.68, 0.95]
            })
        
        # Generate test features
        self.features = np.random.randn(100, 15)
    
    @unittest.skipIf(not UNCERTAINTY_AVAILABLE, "Uncertainty module not available")
    def test_basic_uncertainty_estimation(self):
        """Test basic uncertainty estimation"""
        uncertainty_est = self.quantifier.estimate_uncertainty(
            self.features, method='basic'
        )
        
        self.assertIsInstance(uncertainty_est, UncertaintyEstimate)
        self.assertEqual(len(uncertainty_est.mean_prediction), len(self.features))
        self.assertEqual(len(uncertainty_est.total_uncertainty), len(self.features))
        self.assertIn('0.68', uncertainty_est.confidence_intervals)
        self.assertIn('0.95', uncertainty_est.confidence_intervals)
    
    @unittest.skipIf(not UNCERTAINTY_AVAILABLE, "Uncertainty module not available")
    def test_bootstrap_uncertainty(self):
        """Test bootstrap uncertainty estimation"""
        uncertainty_est = self.quantifier.estimate_uncertainty(
            self.features, method='bootstrap'
        )
        
        self.assertEqual(uncertainty_est.metadata['method'], 'bootstrap')
        self.assertGreater(uncertainty_est.metadata['n_samples'], 0)
        self.assertIsNotNone(uncertainty_est.prediction_samples)
    
    @unittest.skipIf(not UNCERTAINTY_AVAILABLE, "Uncertainty module not available")
    def test_uncertainty_aware_peak_detection(self):
        """Test uncertainty-aware peak detection"""
        voltage, current = TestDataGenerator.generate_cv_data()
        
        peak_results = self.quantifier.uncertainty_aware_peak_detection(
            voltage, current, self.features[:len(voltage)]
        )
        
        self.assertIn('peak_indices', peak_results)
        self.assertIn('peak_uncertainties', peak_results)
        self.assertIn('uncertainty_map', peak_results)
        self.assertIn('confidence_map', peak_results)
    
    @unittest.skipIf(not UNCERTAINTY_AVAILABLE, "Uncertainty module not available")
    def test_confidence_intervals(self):
        """Test confidence interval calculation"""
        # Generate mock samples
        samples = np.random.randn(50, 100)  # 50 samples, 100 data points
        
        confidence_intervals = self.quantifier._calculate_confidence_intervals(samples)
        
        for conf_level in self.quantifier.config['confidence_levels']:
            key = f'{conf_level:.2f}'
            self.assertIn(key, confidence_intervals)
            
            lower, upper = confidence_intervals[key]
            self.assertEqual(len(lower), 100)
            self.assertEqual(len(upper), 100)
            
            # Upper should be >= lower
            self.assertTrue(np.all(upper >= lower))

class ModelPersistenceTests(unittest.TestCase):
    """Test model persistence and transfer learning"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        if PERSISTENCE_AVAILABLE:
            self.version_manager = ModelVersionManager(str(self.temp_dir / "models"))
    
    def tearDown(self):
        """Clean up test fixtures"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @unittest.skipIf(not PERSISTENCE_AVAILABLE, "Persistence module not available")
    def test_version_manager_initialization(self):
        """Test version manager initialization"""
        self.assertIsNotNone(self.version_manager)
        self.assertTrue(self.version_manager.base_path.exists())
    
    @unittest.skipIf(not PERSISTENCE_AVAILABLE or not TORCH_AVAILABLE, "Dependencies not available")
    def test_model_versioning(self):
        """Test model version management"""
        from deepcv_v2_persistence import ModelCheckpoint
        
        # Create dummy model state
        dummy_state = {
            'model_state_dict': {'layer1.weight': torch.randn(10, 5)},
            'optimizer_state_dict': {},
            'config': {'test': True}
        }
        
        metadata = {'accuracy': 0.95, 'epochs': 100}
        checkpoint = ModelCheckpoint(dummy_state, metadata)
        
        # Save version
        version_name = self.version_manager.save_version(
            checkpoint, "test_v1.0", "Test version"
        )
        
        self.assertEqual(version_name, "test_v1.0")
        
        # Load version
        loaded_checkpoint = self.version_manager.load_version("test_v1.0")
        self.assertIsNotNone(loaded_checkpoint)
        self.assertEqual(loaded_checkpoint.metadata['accuracy'], 0.95)
        
        # List versions
        versions = self.version_manager.list_versions()
        self.assertEqual(len(versions), 1)
        self.assertEqual(versions[0]['version_name'], "test_v1.0")

class RealTimeOptimizationTests(unittest.TestCase):
    """Test real-time optimization and edge deployment"""
    
    def setUp(self):
        """Set up test fixtures"""
        if REALTIME_AVAILABLE:
            self.opt_config = OptimizationConfig(
                target_latency_ms=100.0,
                quantization_method='dynamic'
            )
            self.optimizer = RealTimeOptimizer(self.opt_config)
    
    @unittest.skipIf(not REALTIME_AVAILABLE, "Real-time module not available")
    def test_optimizer_initialization(self):
        """Test optimizer initialization"""
        self.assertIsNotNone(self.optimizer)
        self.assertEqual(self.optimizer.config.target_latency_ms, 100.0)
    
    @unittest.skipIf(not REALTIME_AVAILABLE, "Real-time module not available")
    def test_streaming_feature_extractor(self):
        """Test streaming feature extraction"""
        # Add samples
        for i in range(20):
            voltage = np.sin(i * 0.1)
            current = 0.1 * np.cos(i * 0.1) + 0.01 * np.random.randn()
            self.optimizer.feature_extractor.add_sample(voltage, current)
        
        # Extract features
        features = self.optimizer.feature_extractor.extract_features()
        self.assertIsNotNone(features)
        self.assertGreater(len(features), 5)  # Should have multiple features
    
    @unittest.skipIf(not REALTIME_AVAILABLE or not TORCH_AVAILABLE, "Dependencies not available")
    def test_lightweight_model_creation(self):
        """Test lightweight model creation"""
        n_features = 10
        model = self.optimizer.create_lightweight_model(n_features)
        
        self.assertIsNotNone(model)
        self.assertIsInstance(model, torch.nn.Module)
        
        # Test forward pass
        test_input = torch.randn(1, 50, n_features)
        with torch.no_grad():
            output = model(test_input)
            self.assertEqual(output.shape, (1, 50))

class IntegrationTests(unittest.TestCase):
    """End-to-end integration tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Generate comprehensive test dataset
        self.dataset = TestDataGenerator.generate_training_dataset(20)
        
        # Setup temporary directory
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test fixtures"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @unittest.skipIf(not DEEPCV_AVAILABLE, "DeepCV V2 not available")
    def test_end_to_end_pipeline(self):
        """Test complete end-to-end pipeline"""
        # Initialize analyzer
        config = {
            'batch_size': 4,
            'epochs': 3,  # Minimal training for testing
            'min_training_samples': 15
        }
        analyzer = DeepCVAnalyzerV2(config)
        
        # Add training data
        for sample in self.dataset:
            analyzer.add_training_data(
                sample['voltages'],
                sample['currents'],
                sample['peak_positions']
            )
        
        # Check training data was added
        self.assertEqual(len(analyzer.training_data), len(self.dataset))
        
        # Test detection without training (should use fallback)
        test_voltage, test_current = TestDataGenerator.generate_cv_data()
        result = analyzer.detect_peaks(test_voltage, test_current, "test.csv")
        
        self.assertIsInstance(result, DeepCVResult)
        self.assertIn("Fallback", result.version)
    
    @unittest.skipIf(not (DEEPCV_AVAILABLE and UNCERTAINTY_AVAILABLE), "Dependencies not available")
    def test_pipeline_with_uncertainty(self):
        """Test pipeline with uncertainty quantification"""
        # Setup components
        analyzer = DeepCVAnalyzerV2({'min_training_samples': 10})
        quantifier = UncertaintyQuantifier({'mc_samples': 10})
        
        # Generate test data
        voltage, current = TestDataGenerator.generate_cv_data()
        
        # Extract features
        features = analyzer.feature_extractor.extract_features(voltage, current)
        
        # Estimate uncertainty
        uncertainty_est = quantifier.estimate_uncertainty(features, method='basic')
        
        # Uncertainty-aware peak detection
        results = quantifier.uncertainty_aware_peak_detection(
            voltage, current, features
        )
        
        self.assertIn('peak_indices', results)
        self.assertIn('uncertainty_estimate', results)

class PerformanceTests(unittest.TestCase):
    """Performance and benchmarking tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.large_dataset = TestDataGenerator.generate_training_dataset(100)
        self.benchmark_data = [
            TestDataGenerator.generate_cv_data(n_points=n) 
            for n in [100, 200, 500, 1000]
        ]
    
    @unittest.skipIf(not DEEPCV_AVAILABLE, "DeepCV V2 not available")
    def test_feature_extraction_performance(self):
        """Test feature extraction performance"""
        analyzer = DeepCVAnalyzerV2({})
        
        performance_results = []
        
        for voltage, current in self.benchmark_data:
            start_time = time.perf_counter()
            
            features = analyzer.feature_extractor.extract_features(voltage, current)
            
            end_time = time.perf_counter()
            processing_time = (end_time - start_time) * 1000  # ms
            
            performance_results.append({
                'data_points': len(voltage),
                'processing_time_ms': processing_time,
                'feature_dimensions': features.shape[1] if features is not None else 0
            })
        
        # Check that processing time scales reasonably
        for result in performance_results:
            self.assertLess(result['processing_time_ms'], 1000)  # Should be < 1 second
            self.assertGreater(result['feature_dimensions'], 0)
    
    @unittest.skipIf(not MULTISCALE_AVAILABLE, "Multiscale module not available")
    def test_multiscale_analysis_performance(self):
        """Test multi-scale analysis performance"""
        analyzer = MultiScaleMultiModalAnalyzer()
        
        # Test with different data sizes
        for voltage, current in self.benchmark_data[:2]:  # Limit to smaller datasets
            start_time = time.perf_counter()
            
            ms_features = analyzer.extract_comprehensive_features(voltage, current)
            
            end_time = time.perf_counter()
            processing_time = (end_time - start_time) * 1000
            
            self.assertLess(processing_time, 5000)  # Should be < 5 seconds
            self.assertIsNotNone(ms_features.fusion_features)

class TestRunner:
    """Custom test runner with categorization"""
    
    def __init__(self):
        self.test_categories = {
            'architecture': DeepCVArchitectureTests,
            'features': FeatureEngineeringTests,
            'uncertainty': UncertaintyQuantificationTests,
            'persistence': ModelPersistenceTests,
            'realtime': RealTimeOptimizationTests,
            'integration': IntegrationTests,
            'performance': PerformanceTests
        }
    
    def run_category(self, category: str, verbosity: int = 2):
        """Run tests for a specific category"""
        if category not in self.test_categories:
            print(f"❌ Unknown test category: {category}")
            print(f"Available categories: {list(self.test_categories.keys())}")
            return False
        
        print(f"🧪 Running {category} tests...")
        
        test_class = self.test_categories[category]
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=verbosity)
        
        result = runner.run(suite)
        
        if result.wasSuccessful():
            print(f"✅ {category} tests passed!")
            return True
        else:
            print(f"❌ {category} tests failed!")
            return False
    
    def run_all(self, verbosity: int = 2):
        """Run all test categories"""
        print("🧪 Running comprehensive DeepCV V2 test suite...")
        
        results = {}
        total_tests = 0
        passed_tests = 0
        
        for category in self.test_categories:
            print(f"\n{'='*60}")
            success = self.run_category(category, verbosity)
            results[category] = success
            
            if success:
                passed_tests += 1
            total_tests += 1
        
        # Summary
        print(f"\n{'='*60}")
        print(f"📊 Test Summary:")
        print(f"   Total categories: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        
        for category, success in results.items():
            status = "✅" if success else "❌"
            print(f"   {status} {category}")
        
        overall_success = passed_tests == total_tests
        if overall_success:
            print(f"\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  Some tests failed!")
        
        return overall_success

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description='DeepCV V2 Test Suite')
    parser.add_argument('--category', '-c', 
                       help='Run specific test category',
                       choices=['architecture', 'features', 'uncertainty', 
                               'persistence', 'realtime', 'integration', 'performance'])
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--list-categories', '-l', action='store_true',
                       help='List available test categories')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.list_categories:
        print("📋 Available test categories:")
        for category in runner.test_categories:
            print(f"   • {category}")
        return
    
    verbosity = 2 if args.verbose else 1
    
    if args.category:
        success = runner.run_category(args.category, verbosity)
        exit(0 if success else 1)
    else:
        success = runner.run_all(verbosity)
        exit(0 if success else 1)

if __name__ == "__main__":
    main()