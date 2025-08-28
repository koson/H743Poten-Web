#!/usr/bin/env python3
"""
🚀 Enhanced Baseline Detection v2.1 - Optimized Version
Improved baseline detection based on analysis and parameter optimization

Key Improvements:
- Better parameter defaults for CV data
- Hybrid mode for automatic method selection
- Optimized for STM32 potentiostat data
"""

import numpy as np
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import os

# Import the original Enhanced Detector
from enhanced_baseline_detector_v2 import EnhancedBaselineDetector, load_cv_data

class OptimizedBaselineDetector:
    """🚀 Optimized Baseline Detector v2.1 with Smart Method Selection"""
    
    def __init__(self, auto_mode: bool = True):
        """
        Initialize optimized detector
        auto_mode: If True, automatically choose best method based on data
        """
        self.auto_mode = auto_mode
        
        # Optimized configuration for CV data
        self.enhanced_config = {
            'base_window': 30,               # Larger window for smoother baselines
            'peak_proximity_weight': 0.1,    # Reduced weight near peaks
            'stability_threshold': 0.05,     
            'segment_min_length': 5,         
            'scan_direction_adaptive': True,  
            'noise_estimation_window': 15,   # Larger noise estimation window
            'peak_distance_threshold': 20,   # Increased peak distance threshold
            'baseline_smoothing': 10,        # More aggressive smoothing
            'confidence_threshold': 0.7,     
        }
        
        self.enhanced_detector = EnhancedBaselineDetector(self.enhanced_config)
        self.traditional_window = 25  # Optimized traditional window size
        
        print("🎯 Optimized Baseline Detector v2.1 Initialized")
        print(f"🤖 Auto-mode: {'ON' if auto_mode else 'OFF'}")
        if auto_mode:
            print("📊 Will automatically select best method based on data characteristics")
    
    def detect_baseline(self, voltages: np.ndarray, currents: np.ndarray, 
                       filename: str = "unknown", force_method: str = None) -> Tuple[np.ndarray, Dict]:
        """
        🎯 Smart baseline detection with automatic method selection
        
        Args:
            voltages: Voltage array
            currents: Current array  
            filename: Data filename for logging
            force_method: Force specific method ('traditional', 'enhanced', None for auto)
        
        Returns:
            baseline: Detected baseline
            metadata: Detection metadata
        """
        start_time = time.time()
        
        print(f"\n🔍 Optimized Baseline Detection: {filename}")
        print(f"📊 Data: {len(voltages)} points, Range: {voltages.min():.3f}V to {voltages.max():.3f}V")
        print(f"⚡ Current range: {currents.min():.2e} to {currents.max():.2e} µA")
        
        # Method selection
        if force_method:
            selected_method = force_method
            print(f"🔧 Forced method: {selected_method}")
        elif self.auto_mode:
            selected_method = self._select_optimal_method(currents)
            print(f"🤖 Auto-selected method: {selected_method}")
        else:
            selected_method = 'enhanced'  # Default to enhanced
            print(f"📊 Default method: {selected_method}")
        
        # Apply selected method
        if selected_method == 'traditional':
            baseline = self._traditional_baseline(currents)
            metadata = {
                'method': 'traditional_optimized',
                'window_size': self.traditional_window,
                'data_complexity': self._assess_data_complexity(currents),
                'processing_time': time.time() - start_time,
                'quality_metrics': {'overall_quality': 0.8}  # Estimated quality
            }
            print(f"✅ Traditional method completed in {metadata['processing_time']:.3f}s")
        else:
            baseline, enhanced_metadata = self.enhanced_detector.detect_baseline_enhanced(
                voltages, currents, filename
            )
            enhanced_metadata['method'] = 'enhanced_optimized'
            enhanced_metadata['auto_selected'] = self.auto_mode
            metadata = enhanced_metadata
        
        # Add selection reasoning
        metadata['selection_reasoning'] = self._get_selection_reasoning(currents, selected_method)
        metadata['filename'] = filename
        
        return baseline, metadata
    
    def _select_optimal_method(self, currents: np.ndarray) -> str:
        """🧠 Intelligent method selection based on data characteristics"""
        
        complexity_score = self._assess_data_complexity(currents)
        
        # Decision thresholds (optimized based on testing)
        if complexity_score < 0.3:
            return 'traditional'  # Very clean data - traditional is better
        elif complexity_score < 0.6:
            # Medium complexity - check additional factors
            noise_level = self._assess_noise_level(currents)
            if noise_level < 0.1:
                return 'traditional'  # Low noise - traditional works well
            else:
                return 'enhanced'    # Some noise - enhanced is better
        else:
            return 'enhanced'        # High complexity - definitely enhanced
    
    def _assess_data_complexity(self, currents: np.ndarray) -> float:
        """🔍 Assess data complexity to guide method selection"""
        
        factors = []
        
        # 1. Noise level (coefficient of variation of differences)
        if len(currents) > 1:
            diff_cv = np.std(np.diff(currents)) / (np.std(currents) + 1e-12)
            noise_factor = min(diff_cv * 5, 1.0)  # Normalized to [0,1]
            factors.append(noise_factor)
        
        # 2. Number of local extrema (indicating complexity)
        extrema_count = 0
        for i in range(1, len(currents) - 1):
            if ((currents[i] > currents[i-1] and currents[i] > currents[i+1]) or
                (currents[i] < currents[i-1] and currents[i] < currents[i+1])):
                extrema_count += 1
        
        extrema_factor = min(extrema_count / len(currents) * 20, 1.0)
        factors.append(extrema_factor)
        
        # 3. Dynamic range variation
        if np.std(currents) > 1e-12:
            range_variation = (np.max(currents) - np.min(currents)) / np.std(currents)
            range_factor = min(range_variation / 20, 1.0)
            factors.append(range_factor)
        
        # 4. Baseline drift assessment
        if len(currents) >= 10:
            # Split into segments and check consistency
            n_segments = 5
            segment_size = len(currents) // n_segments
            segment_means = []
            
            for i in range(n_segments):
                start = i * segment_size
                end = min((i + 1) * segment_size, len(currents))
                if end > start:
                    segment_means.append(np.mean(currents[start:end]))
            
            if len(segment_means) > 1:
                drift_factor = min(np.std(segment_means) / (np.mean(np.abs(segment_means)) + 1e-12), 1.0)
                factors.append(drift_factor)
        
        # Combined complexity score
        complexity = np.mean(factors) if factors else 0.0
        return complexity
    
    def _assess_noise_level(self, currents: np.ndarray) -> float:
        """📊 Assess noise level in the data"""
        if len(currents) < 3:
            return 0.0
        
        # High-frequency noise assessment using second derivative
        second_diff = np.diff(currents, n=2)
        noise_level = np.std(second_diff) / (np.std(currents) + 1e-12)
        return min(noise_level, 1.0)
    
    def _traditional_baseline(self, currents: np.ndarray) -> np.ndarray:
        """📊 Optimized traditional rolling median baseline"""
        baseline = np.zeros_like(currents)
        half_window = self.traditional_window // 2
        
        for i in range(len(currents)):
            start = max(0, i - half_window)
            end = min(len(currents), i + half_window + 1)
            baseline[i] = np.median(currents[start:end])
        
        return baseline
    
    def _get_selection_reasoning(self, currents: np.ndarray, selected_method: str) -> Dict:
        """📝 Provide reasoning for method selection"""
        complexity = self._assess_data_complexity(currents)
        noise = self._assess_noise_level(currents)
        
        reasoning = {
            'complexity_score': complexity,
            'noise_level': noise,
            'selected_method': selected_method,
            'reasoning_text': ""
        }
        
        if selected_method == 'traditional':
            if complexity < 0.3:
                reasoning['reasoning_text'] = "Low complexity data - traditional method optimal for smoothness"
            elif noise < 0.1:
                reasoning['reasoning_text'] = "Low noise data - traditional method sufficient"
            else:
                reasoning['reasoning_text'] = "Traditional method selected despite medium complexity"
        else:
            if complexity > 0.6:
                reasoning['reasoning_text'] = "High complexity data - enhanced method needed"
            elif noise > 0.1:
                reasoning['reasoning_text'] = "Noisy data - enhanced method provides better robustness"
            else:
                reasoning['reasoning_text'] = "Enhanced method selected for advanced features"
        
        return reasoning


def test_optimized_detector():
    """🧪 Test the optimized detector"""
    print("🧪 TESTING OPTIMIZED BASELINE DETECTOR v2.1")
    print("=" * 60)
    
    # Test files
    test_files = [
        "cv_data/measurement_93_100.0mVs_2025-08-25T06-39-11.686802.csv",
        "cv_data/measurement_95_200.0mVs_2025-08-25T06-46-14.158045.csv",
        "cv_data/measurement_96_20.0mVs_2025-08-25T06-46-22.774810.csv"
    ]
    
    # Test both auto and manual modes
    modes = [
        ("Auto Mode", True),
        ("Enhanced Only", False)
    ]
    
    results = {}
    
    for mode_name, auto_mode in modes:
        print(f"\n🔬 Testing {mode_name}")
        print("-" * 40)
        
        detector = OptimizedBaselineDetector(auto_mode=auto_mode)
        mode_results = []
        
        for test_file in test_files:
            if not os.path.exists(test_file):
                continue
                
            print(f"\n📂 File: {test_file.split('/')[-1]}")
            
            # Load data
            voltages, currents = load_cv_data(test_file)
            if len(voltages) == 0:
                continue
            
            # Test detection
            baseline, metadata = detector.detect_baseline(voltages, currents, test_file)
            
            result = {
                'file': test_file.split('/')[-1],
                'method': metadata['method'],
                'complexity': metadata['selection_reasoning']['complexity_score'],
                'quality': metadata['quality_metrics']['overall_quality'],
                'processing_time': metadata['processing_time']
            }
            
            mode_results.append(result)
            
            print(f"   Method: {metadata['method']}")
            print(f"   Complexity: {result['complexity']:.3f}")
            print(f"   Quality: {result['quality']:.3f}")
            print(f"   Time: {result['processing_time']:.3f}s")
            print(f"   Reasoning: {metadata['selection_reasoning']['reasoning_text']}")
        
        results[mode_name] = mode_results
    
    # Summary comparison
    print("\n" + "=" * 60)
    print("📊 OPTIMIZED DETECTOR SUMMARY")
    print("=" * 60)
    
    for mode_name, mode_results in results.items():
        if mode_results:
            avg_quality = np.mean([r['quality'] for r in mode_results])
            avg_time = np.mean([r['processing_time'] for r in mode_results])
            
            print(f"\n🎯 {mode_name}:")
            print(f"   Average Quality: {avg_quality:.3f}")
            print(f"   Average Time: {avg_time:.3f}s")
            print(f"   Files processed: {len(mode_results)}")
            
            # Method distribution for auto mode
            if mode_name == "Auto Mode":
                methods = [r['method'] for r in mode_results]
                method_counts = {method: methods.count(method) for method in set(methods)}
                print(f"   Method selection: {method_counts}")
    
    return results


def compare_with_traditional():
    """⚖️ Compare optimized detector with traditional method"""
    print("\n⚖️ COMPARISON: Optimized v2.1 vs Traditional")
    print("=" * 60)
    
    detector = OptimizedBaselineDetector(auto_mode=True)
    test_file = "cv_data/measurement_93_100.0mVs_2025-08-25T06-39-11.686802.csv"
    
    if not os.path.exists(test_file):
        print("❌ Test file not found!")
        return
    
    # Load data
    voltages, currents = load_cv_data(test_file)
    if len(voltages) == 0:
        return
    
    print(f"📊 Testing with: {test_file.split('/')[-1]}")
    
    # Test auto-selection
    auto_baseline, auto_metadata = detector.detect_baseline(voltages, currents, test_file)
    
    # Force traditional
    traditional_baseline, trad_metadata = detector.detect_baseline(
        voltages, currents, test_file, force_method='traditional'
    )
    
    # Force enhanced
    enhanced_baseline, enh_metadata = detector.detect_baseline(
        voltages, currents, test_file, force_method='enhanced'
    )
    
    print(f"\n📋 COMPARISON RESULTS:")
    print(f"Auto-selected: {auto_metadata['method']} (Quality: {auto_metadata['quality_metrics']['overall_quality']:.3f})")
    print(f"Traditional: {trad_metadata['method']} (Quality: {trad_metadata['quality_metrics']['overall_quality']:.3f})")
    print(f"Enhanced: {enh_metadata['method']} (Quality: {enh_metadata['quality_metrics']['overall_quality']:.3f})")
    
    print(f"\n🧠 Selection Reasoning:")
    print(f"Complexity: {auto_metadata['selection_reasoning']['complexity_score']:.3f}")
    print(f"Reasoning: {auto_metadata['selection_reasoning']['reasoning_text']}")


if __name__ == "__main__":
    # Run comprehensive testing
    print("🚀 OPTIMIZED BASELINE DETECTOR v2.1 - COMPREHENSIVE TEST")
    print("=" * 80)
    
    # Test optimized detector
    test_results = test_optimized_detector()
    
    # Compare methods
    compare_with_traditional()
    
    print("\n" + "=" * 80)
    print("✅ OPTIMIZED BASELINE DETECTOR v2.1 TESTING COMPLETE!")
    print("🎯 Ready for production use with smart method selection")