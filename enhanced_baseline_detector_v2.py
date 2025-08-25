#!/usr/bin/env python3
"""
🚀 Enhanced Baseline Detection v2 with Feature Engineering
Advanced baseline detection using multiple features:
- Segment length analysis
- Stability assessment
- Peak proximity consideration
- Scan direction adaptation
"""

import numpy as np
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import json
import os

class EnhancedBaselineDetector:
    """🚀 Enhanced Baseline Detection v2 with Feature Engineering"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            'base_window': 20,               # Base window size for baseline estimation
            'peak_proximity_weight': 0.3,    # Weight reduction factor near peaks
            'stability_threshold': 0.05,     # Current stability requirement (CV)
            'segment_min_length': 5,         # Minimum segment length for analysis
            'scan_direction_adaptive': True,  # Enable scan direction adaptation
            'noise_estimation_window': 10,   # Window for local noise estimation
            'peak_distance_threshold': 15,   # Distance threshold for peak influence
            'baseline_smoothing': 5,         # Additional smoothing for baseline
            'confidence_threshold': 0.7,     # Minimum confidence for good baseline
        }
        
        self.last_metadata = {}
        print("🎯 Enhanced Baseline Detector v2 Initialized")
        print(f"📐 Config: {self.config}")
    
    def detect_baseline_enhanced(self, voltages: np.ndarray, currents: np.ndarray, 
                               filename: str = "unknown") -> Tuple[np.ndarray, Dict]:
        """🔍 Enhanced baseline detection with multiple features"""
        start_time = time.time()
        
        print(f"\n🧪 Analyzing: {filename}")
        print(f"📊 Data points: {len(voltages)}, Range: {voltages.min():.3f}V to {voltages.max():.3f}V")
        
        try:
            # Step 1: Quick peak detection for baseline planning
            peaks = self._quick_peak_detection(voltages, currents)
            print(f"🎯 Quick peaks detected: {len(peaks)} peaks")
            
            # Step 2: Segment Analysis
            segments = self._analyze_segments(voltages, currents)
            print(f"📏 Segments analyzed: {len(segments)} segments")
            
            # Step 3: Stability Assessment
            stability_map = self._assess_stability(currents)
            stability_score = np.mean(1.0 / (1.0 + stability_map))  # Higher = more stable
            print(f"🛡️ Overall stability: {stability_score:.3f}")
            
            # Step 4: Peak Distance Mapping
            peak_distance_map = self._calculate_peak_distances(peaks, len(currents))
            
            # Step 5: Scan Direction Analysis
            direction_map = self._analyze_scan_direction(voltages)
            forward_ratio = np.sum(direction_map == 1) / len(direction_map)
            print(f"⏭️ Forward scan ratio: {forward_ratio:.1%}")
            
            # Step 6: Feature-Enhanced Baseline Calculation
            baseline = self._calculate_adaptive_baseline(
                currents, segments, stability_map, 
                peak_distance_map, direction_map
            )
            
            # Step 7: Baseline Quality Assessment
            quality_metrics = self._assess_baseline_quality(currents, baseline, peaks)
            
            # Step 8: Post-processing smoothing
            if self.config['baseline_smoothing'] > 1:
                baseline = self._smooth_baseline(baseline)
            
            processing_time = time.time() - start_time
            
            # Prepare comprehensive metadata
            metadata = {
                'filename': filename,
                'processing_time': processing_time,
                'data_points': len(voltages),
                'peaks_detected': len(peaks),
                'peak_positions': [voltages[i] for i in peaks],
                'segments_count': len(segments),
                'stability_score': stability_score,
                'forward_scan_ratio': forward_ratio,
                'quality_metrics': quality_metrics,
                'config_used': self.config.copy(),
                'timestamp': datetime.now().isoformat()
            }
            
            self.last_metadata = metadata
            
            print(f"✅ Baseline detection completed in {processing_time:.3f}s")
            print(f"📈 Quality score: {quality_metrics['overall_quality']:.3f}")
            
            return baseline, metadata
            
        except Exception as e:
            print(f"❌ Error in baseline detection: {e}")
            import traceback
            traceback.print_exc()
            
            # Return simple fallback baseline
            fallback_baseline = np.median(currents) * np.ones_like(currents)
            fallback_metadata = {
                'filename': filename,
                'error': str(e),
                'fallback_used': True,
                'timestamp': datetime.now().isoformat()
            }
            return fallback_baseline, fallback_metadata
    
    def _quick_peak_detection(self, voltages: np.ndarray, currents: np.ndarray) -> List[int]:
        """⚡ Quick peak detection for baseline planning"""
        abs_currents = np.abs(currents)
        threshold = 0.1 * np.max(abs_currents)  # 10% of max for quick detection
        min_distance = 5
        
        peaks = []
        for i in range(min_distance, len(abs_currents) - min_distance):
            if abs_currents[i] > threshold:
                is_peak = True
                for j in range(1, min_distance + 1):
                    if (abs_currents[i] <= abs_currents[i-j] or 
                        abs_currents[i] <= abs_currents[i+j]):
                        is_peak = False
                        break
                
                if is_peak and (not peaks or i - peaks[-1] >= min_distance):
                    peaks.append(i)
        
        return peaks
    
    def _analyze_segments(self, voltages: np.ndarray, currents: np.ndarray) -> List[Dict]:
        """📏 Analyze data segments for characteristics"""
        segments = []
        min_length = self.config['segment_min_length']
        
        for i in range(0, len(currents), min_length):
            end_idx = min(i + min_length, len(currents))
            segment_currents = currents[i:end_idx]
            segment_voltages = voltages[i:end_idx]
            
            if len(segment_currents) < 2:
                continue
                
            segment_info = {
                'start_idx': i,
                'end_idx': end_idx,
                'length': end_idx - i,
                'mean_current': np.mean(segment_currents),
                'std_current': np.std(segment_currents),
                'range_current': np.max(segment_currents) - np.min(segment_currents),
                'voltage_span': segment_voltages[-1] - segment_voltages[0],
                'linearity': self._assess_linearity(segment_voltages, segment_currents)
            }
            segments.append(segment_info)
        
        return segments
    
    def _assess_linearity(self, voltages: np.ndarray, currents: np.ndarray) -> float:
        """📐 Assess linearity of voltage-current relationship"""
        if len(voltages) < 3:
            return 0.0
        
        try:
            # Simple linear correlation
            correlation = np.corrcoef(voltages, currents)[0, 1]
            return abs(correlation) if not np.isnan(correlation) else 0.0
        except:
            return 0.0
    
    def _assess_stability(self, currents: np.ndarray) -> np.ndarray:
        """🛡️ Assess local stability (coefficient of variation)"""
        window = self.config['noise_estimation_window']
        stability_scores = np.zeros(len(currents))
        
        for i in range(len(currents)):
            start = max(0, i - window//2)
            end = min(len(currents), i + window//2 + 1)
            
            local_currents = currents[start:end]
            if len(local_currents) > 1:
                local_mean = np.mean(local_currents)
                local_std = np.std(local_currents)
                
                # Coefficient of variation (normalized by mean)
                if abs(local_mean) > 1e-15:
                    stability_scores[i] = local_std / abs(local_mean)
                else:
                    stability_scores[i] = local_std / (1e-12)  # Prevent division by zero
            else:
                stability_scores[i] = 1.0  # Assume unstable if insufficient data
        
        return stability_scores
    
    def _calculate_peak_distances(self, peaks: List[int], data_length: int) -> np.ndarray:
        """🎯 Calculate normalized distance from each point to nearest peak"""
        distances = np.full(data_length, float('inf'))
        
        if len(peaks) == 0:
            return np.ones(data_length)  # All points are far from peaks
        
        for i in range(data_length):
            for peak_idx in peaks:
                distances[i] = min(distances[i], abs(i - peak_idx))
        
        # Normalize and invert: 1 = far from peaks, 0 = at peak
        max_distance = min(np.max(distances), self.config['peak_distance_threshold'])
        normalized_distances = distances / max_distance
        return np.clip(normalized_distances, 0, 1)
    
    def _analyze_scan_direction(self, voltages: np.ndarray) -> np.ndarray:
        """⏭️ Analyze scan direction at each point"""
        directions = np.zeros(len(voltages))
        
        if len(voltages) < 2:
            return directions
        
        # First point inherits from second
        directions[0] = 1 if voltages[1] > voltages[0] else -1
        
        for i in range(1, len(voltages)):
            voltage_diff = voltages[i] - voltages[i-1]
            if abs(voltage_diff) > 1e-6:  # Threshold for direction change
                directions[i] = 1 if voltage_diff > 0 else -1
            else:
                directions[i] = directions[i-1]  # Continue previous direction
        
        return directions
    
    def _calculate_adaptive_baseline(self, currents: np.ndarray, segments: List[Dict], 
                                   stability_map: np.ndarray, peak_distance_map: np.ndarray, 
                                   direction_map: np.ndarray) -> np.ndarray:
        """🧮 Calculate adaptive baseline using all features"""
        baseline = np.zeros_like(currents)
        base_window = self.config['base_window']
        
        for i in range(len(currents)):
            # Feature-based adaptive window sizing
            stability_score = stability_map[i]
            peak_distance = peak_distance_map[i]
            
            # More stable regions and farther from peaks get larger windows
            stability_factor = 1.0 / (1.0 + stability_score)  # 0.5 to 1.0
            distance_factor = 0.5 + 0.5 * peak_distance       # 0.5 to 1.0
            
            window_multiplier = stability_factor * distance_factor
            adaptive_window = max(3, int(base_window * window_multiplier))
            
            # Window bounds
            half_window = adaptive_window // 2
            start = max(0, i - half_window)
            end = min(len(currents), i + half_window + 1)
            
            # Calculate weights based on multiple features
            weights = np.ones(end - start)
            
            for j, idx in enumerate(range(start, end)):
                # Distance from center point
                distance_from_center = abs(idx - i)
                center_weight = 1.0 / (1.0 + 0.1 * distance_from_center)
                
                # Peak proximity weighting
                peak_weight = peak_distance_map[idx] ** self.config['peak_proximity_weight']
                
                # Stability weighting (more stable = higher weight)
                stability_weight = 1.0 / (1.0 + stability_map[idx])
                
                # Scan direction consistency
                direction_weight = 1.2 if direction_map[idx] == direction_map[i] else 0.8
                
                # Combined weight
                weights[j] = center_weight * peak_weight * stability_weight * direction_weight
            
            # Weighted baseline calculation
            window_currents = currents[start:end]
            
            # Use weighted median for robustness
            try:
                # Simple weighted average (median would be more complex to implement)
                baseline[i] = np.average(window_currents, weights=weights)
            except:
                baseline[i] = np.median(window_currents)  # Fallback
        
        return baseline
    
    def _smooth_baseline(self, baseline: np.ndarray) -> np.ndarray:
        """🌊 Apply additional smoothing to baseline"""
        smoothing_window = self.config['baseline_smoothing']
        if smoothing_window <= 1:
            return baseline
        
        # Simple moving average
        kernel = np.ones(smoothing_window) / smoothing_window
        return np.convolve(baseline, kernel, mode='same')
    
    def _assess_baseline_quality(self, currents: np.ndarray, baseline: np.ndarray, 
                               peaks: List[int]) -> Dict:
        """📊 Assess baseline quality metrics"""
        
        # Corrected signal
        corrected = currents - baseline
        
        # Metrics calculation
        try:
            # 1. Baseline smoothness (lower derivative = smoother)
            baseline_gradient = np.gradient(baseline)
            smoothness = 1.0 / (1.0 + np.std(baseline_gradient))
            
            # 2. Peak enhancement (peaks should be more prominent after correction)
            if len(peaks) > 0:
                original_peak_heights = [abs(currents[i]) for i in peaks]
                corrected_peak_heights = [abs(corrected[i]) for i in peaks]
                
                if len(original_peak_heights) > 0 and np.mean(original_peak_heights) > 1e-15:
                    enhancement = np.mean(corrected_peak_heights) / np.mean(original_peak_heights)
                else:
                    enhancement = 1.0
            else:
                enhancement = 1.0
            
            # 3. Baseline flatness in non-peak regions
            non_peak_mask = np.ones(len(currents), dtype=bool)
            for peak_idx in peaks:
                start = max(0, peak_idx - 5)
                end = min(len(currents), peak_idx + 6)
                non_peak_mask[start:end] = False
            
            if np.any(non_peak_mask):
                non_peak_baseline = baseline[non_peak_mask]
                flatness = 1.0 / (1.0 + np.std(non_peak_baseline))
            else:
                flatness = 0.5
            
            # 4. Overall quality score
            overall_quality = (0.4 * smoothness + 0.3 * min(enhancement, 2.0)/2.0 + 0.3 * flatness)
            
            return {
                'smoothness': smoothness,
                'peak_enhancement': enhancement,
                'flatness': flatness,
                'overall_quality': overall_quality
            }
            
        except Exception as e:
            print(f"⚠️ Quality assessment error: {e}")
            return {
                'smoothness': 0.5,
                'peak_enhancement': 1.0,
                'flatness': 0.5,
                'overall_quality': 0.5
            }


def load_cv_data(filepath: str) -> Tuple[np.ndarray, np.ndarray]:
    """📂 Load CV data from CSV file"""
    try:
        # Check if file exists
        if not os.path.exists(filepath):
            print(f"⚠️ File not found: {filepath}")
            return np.array([]), np.array([])
        
        with open(filepath, 'r') as f:
            # Check if first row contains headers
            first_line = f.readline().strip()
            has_header = not (first_line.replace('.', '').replace('-', '').replace(',', '').replace('e', '').replace('E', '').replace('+', '').isdigit())
        
        # Load data
        data = np.loadtxt(filepath, delimiter=',', skiprows=1 if has_header else 0)
        
        if data.shape[1] >= 2:
            voltages = data[:, 0]
            currents = data[:, 1]
            
            # Convert currents to µA if they're in A
            if np.max(np.abs(currents)) < 1e-3:  # Likely in Amperes
                currents = currents * 1e6  # Convert to µA
                print(f"🔄 Converted currents from A to µA")
            
            return voltages, currents
        else:
            raise ValueError("Insufficient columns in data file")
            
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return np.array([]), np.array([])


def test_enhanced_baseline_detector():
    """🧪 Test Enhanced Baseline Detector v2"""
    print("🚀 Testing Enhanced Baseline Detector v2")
    print("=" * 60)
    
    # Initialize detector
    detector = EnhancedBaselineDetector()
    
    # Check for available test files
    potential_files = [
        "cv_data/measurement_93_100.0mVs_2025-08-25T06-39-11.686802.csv",
        "cv_data/measurement_95_200.0mVs_2025-08-25T06-46-14.158045.csv", 
        "cv_data/measurement_96_20.0mVs_2025-08-25T06-46-22.774810.csv",
        "temp_data/preview_Palmsens_0.5mM_Palmsens_0.5mM_CV_100mVpS_E1_scan_05.csv",
        # Fallback to any CSV files in current directory
        "data_logs/measurements.csv",
        "sample_data.csv"
    ]
    
    # Find existing files
    test_files = []
    for filepath in potential_files:
        if os.path.exists(filepath):
            test_files.append(filepath)
    
    # If no specific files found, search for any CSV files
    if not test_files:
        print("⚠️ No predefined test files found, searching for CSV files...")
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.csv') and 'measurement' in file.lower():
                    test_files.append(os.path.join(root, file))
                    if len(test_files) >= 3:  # Limit to 3 files for testing
                        break
            if test_files:
                break
    
    if not test_files:
        print("❌ No suitable CSV test files found!")
        print("💡 Please ensure you have CV measurement files in the current directory")
        return []
    
    print(f"📁 Found {len(test_files)} test files:")
    for f in test_files:
        print(f"   {f}")
    
    results = []
    
    for filepath in test_files:
        try:
            print(f"\n🔍 Testing: {filepath}")
            
            # Load data
            voltages, currents = load_cv_data(filepath)
            
            if len(voltages) == 0:
                print(f"⚠️ Skipping {filepath} - no data loaded")
                continue
            
            print(f"📊 Loaded: {len(voltages)} points, Current range: {currents.min():.2e} to {currents.max():.2e} µA")
            
            # Test enhanced baseline detection
            baseline, metadata = detector.detect_baseline_enhanced(voltages, currents, filepath)
            
            # Store results
            result = {
                'filepath': filepath,
                'data_points': len(voltages),
                'baseline_quality': metadata['quality_metrics']['overall_quality'],
                'peaks_detected': metadata['peaks_detected'],
                'processing_time': metadata['processing_time'],
                'stability_score': metadata['stability_score']
            }
            results.append(result)
            
            print(f"✅ Success! Quality: {result['baseline_quality']:.3f}, Peaks: {result['peaks_detected']}")
            
        except Exception as e:
            print(f"❌ Error testing {filepath}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ENHANCED BASELINE DETECTOR v2 TEST SUMMARY")
    print("=" * 60)
    
    if results:
        avg_quality = np.mean([r['baseline_quality'] for r in results])
        avg_time = np.mean([r['processing_time'] for r in results])
        total_peaks = sum([r['peaks_detected'] for r in results])
        
        print(f"✅ Files processed: {len(results)}/{len(test_files)}")
        print(f"📈 Average baseline quality: {avg_quality:.3f}")
        print(f"⏱️ Average processing time: {avg_time:.3f}s")
        print(f"🎯 Total peaks detected: {total_peaks}")
        
        print(f"\n📋 Individual Results:")
        for r in results:
            print(f"  {r['filepath'].split('/')[-1]}: Q={r['baseline_quality']:.3f}, P={r['peaks_detected']}, T={r['processing_time']:.3f}s")
    else:
        print("❌ No files processed successfully")
    
    return results


if __name__ == "__main__":
    # Run the test
    results = test_enhanced_baseline_detector()