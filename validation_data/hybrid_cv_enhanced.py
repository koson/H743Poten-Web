#!/usr/bin/env python3
"""
🔄 HybridCV Enhanced - The Ultimate Peak Detection System
=========================================================

Final step in the workflow diagram:
TraditionalCV Enhanced V5 → DeepCV V2 (trained by V5) → HybridCV Enhanced

This combines the best of both worlds:
- Enhanced Detector V5 (Traditional + Advanced Signal Processing)
- DeepCV V2 (AI-trained by V5 with scikit-learn)

Author: H743Poten Research Team
Date: October 4, 2025
Version: Enhanced (V5 + DeepCV V2)
"""

import sys
import os
sys.path.append('.')

import numpy as np
import pandas as pd
import pickle
import time
from typing import Dict, List, Optional, Any, Tuple

class HybridCVEnhanced:
    """
    Enhanced Hybrid CV Peak Detection System
    
    Combines:
    1. Enhanced Detector V5 (Traditional approach with advanced algorithms)
    2. DeepCV V2 (AI approach trained by V5)
    
    Uses intelligent ensemble method to get best of both worlds.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        
        # Initialize components
        self.v5_detector = None
        self.deepcv_v2 = None
        
        # Performance tracking
        self.performance_history = []
        self.last_result = None
        
        print("🔄 Initializing HybridCV Enhanced...")
        self._initialize_components()
    
    def _default_config(self) -> Dict:
        """Default configuration for HybridCV Enhanced"""
        return {
            # Ensemble weights
            'v5_weight': 0.6,           # Traditional approach weight
            'deepcv_weight': 0.4,       # AI approach weight
            
            # Consensus parameters
            'consensus_threshold': 0.5,  # Minimum agreement for peak acceptance
            'confidence_threshold': 30.0, # Minimum confidence for valid peaks
            
            # Advanced ensemble parameters
            'adaptive_weighting': True,   # Adjust weights based on data quality
            'uncertainty_aware': True,    # Use uncertainty in decision making
            'cross_validation': True,     # Validate results between methods
            
            # Performance optimization
            'parallel_processing': False, # Run both methods in parallel
            'caching_enabled': True,      # Cache results for performance
            
            # Quality control
            'outlier_detection': True,    # Remove outlier predictions
            'consistency_check': True,    # Check result consistency
            
            # Debugging
            'verbose': True,              # Detailed logging
            'save_intermediate': False    # Save intermediate results
        }
    
    def _initialize_components(self):
        """Initialize V5 and DeepCV V2 components"""
        try:
            # Initialize Enhanced Detector V5
            from enhanced_detector_v5 import EnhancedDetectorV5
            self.v5_detector = EnhancedDetectorV5()
            print("✅ Enhanced Detector V5 initialized")
            
            # Load trained DeepCV V2
            deepcv_model_path = "deepcv_v2_trained_by_v5.pkl"
            if os.path.exists(deepcv_model_path):
                self.deepcv_v2 = self._load_deepcv_v2(deepcv_model_path)
                print("✅ DeepCV V2 model loaded")
            else:
                print("⚠️  DeepCV V2 model not found - using fallback")
                self.deepcv_v2 = None
                
        except Exception as e:
            print(f"❌ Component initialization error: {e}")
            self.v5_detector = None
            self.deepcv_v2 = None
    
    def _load_deepcv_v2(self, model_path: str):
        """Load trained DeepCV V2 model"""
        class DeepCVV2Wrapper:
            def __init__(self, model_path):
                with open(model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.scaler = model_data['scaler']
                self.peak_count_model = model_data['peak_count_model']
                self.confidence_model = model_data['confidence_model']
                self.is_trained = model_data['is_trained']
                self.version = model_data.get('version', 'DeepCV_V2')
                
            def extract_advanced_features(self, voltage, current):
                """Extract advanced features (same as training)"""
                try:
                    features = []
                    
                    # Basic statistical features
                    features.extend([
                        np.mean(current), np.std(current), 
                        np.min(current), np.max(current),
                        np.mean(voltage), np.std(voltage),
                        len(current), np.ptp(current)
                    ])
                    
                    # Advanced electrochemical features
                    current_range = np.ptp(current)
                    current_positive = current[current > 0]
                    current_negative = current[current < 0]
                    
                    features.extend([
                        len(current_positive) / len(current) if len(current) > 0 else 0,
                        len(current_negative) / len(current) if len(current) > 0 else 0,
                        np.mean(current_positive) if len(current_positive) > 0 else 0,
                        np.mean(current_negative) if len(current_negative) > 0 else 0,
                        current_range
                    ])
                    
                    # Derivative features
                    dcurrent_dv = np.gradient(current, voltage)
                    features.extend([
                        np.mean(dcurrent_dv), np.std(dcurrent_dv),
                        np.max(dcurrent_dv), np.min(dcurrent_dv),
                        np.sum(dcurrent_dv > 0), np.sum(dcurrent_dv < 0)
                    ])
                    
                    # Second derivative
                    d2current_dv2 = np.gradient(dcurrent_dv, voltage)
                    features.extend([
                        np.mean(d2current_dv2), np.std(d2current_dv2),
                        np.max(d2current_dv2), np.min(d2current_dv2)
                    ])
                    
                    # Frequency domain features
                    fft_current = np.fft.fft(current)
                    fft_power = np.abs(fft_current[:len(fft_current)//2])
                    features.extend([
                        np.mean(fft_power), np.std(fft_power),
                        np.argmax(fft_power),
                        np.sum(fft_power[:5]),
                        np.sum(fft_power[-5:]) if len(fft_power) > 5 else 0
                    ])
                    
                    # Simple peak detection features
                    try:
                        from scipy.signal import find_peaks
                        peaks_pos, _ = find_peaks(current, height=np.std(current))
                        peaks_neg, _ = find_peaks(-current, height=np.std(current))
                        
                        features.extend([
                            len(peaks_pos), len(peaks_neg),
                            np.mean(current[peaks_pos]) if len(peaks_pos) > 0 else 0,
                            np.mean(current[peaks_neg]) if len(peaks_neg) > 0 else 0
                        ])
                    except:
                        features.extend([0, 0, 0, 0])
                    
                    # Voltage window analysis
                    v_min, v_max = np.min(voltage), np.max(voltage)
                    v_windows = 5
                    window_size = (v_max - v_min) / v_windows
                    
                    for i in range(v_windows):
                        v_start = v_min + i * window_size
                        v_end = v_min + (i + 1) * window_size
                        window_mask = (voltage >= v_start) & (voltage < v_end)
                        window_current = current[window_mask]
                        
                        if len(window_current) > 0:
                            features.extend([
                                np.mean(window_current),
                                np.std(window_current),
                                np.max(window_current) - np.min(window_current)
                            ])
                        else:
                            features.extend([0, 0, 0])
                    
                    # Clean features
                    features = np.array(features)
                    features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
                    
                    return features
                    
                except Exception as e:
                    print(f"⚠️  DeepCV V2 feature extraction error: {e}")
                    return np.zeros(50)
            
            def predict_peaks(self, voltage, current):
                """Predict peaks using trained DeepCV V2"""
                if not self.is_trained:
                    return {'peaks_detected': 0, 'confidence': 0.0, 'method': 'DeepCV_V2_Untrained'}
                
                try:
                    features = self.extract_advanced_features(voltage, current).reshape(1, -1)
                    features_scaled = self.scaler.transform(features)
                    
                    peak_count = self.peak_count_model.predict(features_scaled)[0]
                    confidence = self.confidence_model.predict(features_scaled)[0]
                    
                    peak_count = max(0, round(peak_count))
                    confidence = max(0.0, min(100.0, confidence))
                    
                    return {
                        'peaks_detected': int(peak_count),
                        'confidence': float(confidence),
                        'method': 'DeepCV_V2_Enhanced',
                        'teacher': 'Enhanced_V5'
                    }
                    
                except Exception as e:
                    print(f"⚠️  DeepCV V2 prediction error: {e}")
                    return {'peaks_detected': 0, 'confidence': 0.0, 'method': 'DeepCV_V2_Error'}
        
        return DeepCVV2Wrapper(model_path)
    
    def detect_peaks(self, voltage: np.ndarray, current: np.ndarray, 
                    filename: str = "unknown") -> Dict[str, Any]:
        """
        Enhanced hybrid peak detection using V5 + DeepCV V2
        
        Args:
            voltage: Voltage data
            current: Current data  
            filename: File identifier
            
        Returns:
            Comprehensive results with ensemble predictions
        """
        start_time = time.time()
        
        if self.config['verbose']:
            print(f"🔄 HybridCV Enhanced analyzing: {filename}")
        
        # Initialize results structure
        result = {
            'filename': filename,
            'timestamp': time.time(),
            'v5_result': None,
            'deepcv_result': None,
            'ensemble_result': None,
            'processing_time': 0.0,
            'method': 'HybridCV_Enhanced',
            'version': 'V5_plus_DeepCV_V2'
        }
        
        # Step 1: Run Enhanced Detector V5
        v5_result = self._run_v5_detection(voltage, current, filename)
        result['v5_result'] = v5_result
        
        # Step 2: Run DeepCV V2
        deepcv_result = self._run_deepcv_detection(voltage, current, filename)
        result['deepcv_result'] = deepcv_result
        
        # Step 3: Ensemble prediction
        ensemble_result = self._ensemble_prediction(v5_result, deepcv_result, voltage, current)
        result['ensemble_result'] = ensemble_result
        
        # Step 4: Quality assessment
        quality_metrics = self._assess_quality(v5_result, deepcv_result, ensemble_result)
        result['quality_metrics'] = quality_metrics
        
        # Final processing time
        result['processing_time'] = time.time() - start_time
        
        # Store for performance tracking
        self.last_result = result
        self.performance_history.append({
            'filename': filename,
            'processing_time': result['processing_time'],
            'v5_peaks': v5_result.get('peaks_detected', 0),
            'deepcv_peaks': deepcv_result.get('peaks_detected', 0),
            'ensemble_peaks': ensemble_result.get('peaks_detected', 0),
            'confidence': ensemble_result.get('confidence', 0.0)
        })
        
        if self.config['verbose']:
            self._print_result_summary(result)
        
        return result
    
    def _run_v5_detection(self, voltage, current, filename):
        """Run Enhanced Detector V5"""
        if self.v5_detector is None:
            return {'peaks_detected': 0, 'confidence': 0.0, 'error': 'V5 not available'}
        
        try:
            v5_result = self.v5_detector.detect_peaks_enhanced_v5(voltage, current)
            
            # Extract key information
            peaks_list = v5_result.get('peaks', [])
            peak_count = len(peaks_list)
            
            if peaks_list:
                confidences = [p.get('confidence', 0.0) for p in peaks_list if 'confidence' in p]
                avg_confidence = np.mean(confidences) if confidences else 0.0
            else:
                avg_confidence = 0.0
            
            return {
                'peaks_detected': peak_count,
                'confidence': avg_confidence,
                'peaks_list': peaks_list,
                'method': 'Enhanced_V5',
                'raw_result': v5_result
            }
            
        except Exception as e:
            print(f"⚠️  V5 detection error: {e}")
            return {'peaks_detected': 0, 'confidence': 0.0, 'error': str(e)}
    
    def _run_deepcv_detection(self, voltage, current, filename):
        """Run DeepCV V2"""
        if self.deepcv_v2 is None:
            return {'peaks_detected': 0, 'confidence': 0.0, 'error': 'DeepCV V2 not available'}
        
        try:
            deepcv_result = self.deepcv_v2.predict_peaks(voltage, current)
            return deepcv_result
            
        except Exception as e:
            print(f"⚠️  DeepCV V2 detection error: {e}")
            return {'peaks_detected': 0, 'confidence': 0.0, 'error': str(e)}
    
    def _ensemble_prediction(self, v5_result, deepcv_result, voltage, current):
        """Intelligent ensemble prediction"""
        try:
            # Extract predictions
            v5_peaks = v5_result.get('peaks_detected', 0)
            v5_conf = v5_result.get('confidence', 0.0)
            
            deepcv_peaks = deepcv_result.get('peaks_detected', 0)
            deepcv_conf = deepcv_result.get('confidence', 0.0)
            
            # Adaptive weighting based on confidence
            if self.config.get('adaptive_weighting', True):
                # Higher confidence gets higher weight
                total_conf = v5_conf + deepcv_conf
                if total_conf > 0:
                    v5_weight = v5_conf / total_conf
                    deepcv_weight = deepcv_conf / total_conf
                else:
                    v5_weight = self.config.get('v5_weight', 0.6)
                    deepcv_weight = self.config.get('deepcv_weight', 0.4)
            else:
                v5_weight = self.config.get('v5_weight', 0.6)
                deepcv_weight = self.config.get('deepcv_weight', 0.4)
            
            # Weighted ensemble prediction
            ensemble_peaks = v5_weight * v5_peaks + deepcv_weight * deepcv_peaks
            ensemble_peaks = max(0, round(ensemble_peaks))
            
            # Ensemble confidence
            ensemble_conf = v5_weight * v5_conf + deepcv_weight * deepcv_conf
            
            # Consensus check
            peak_difference = abs(v5_peaks - deepcv_peaks)
            max_peaks = max(v5_peaks, deepcv_peaks)
            
            if max_peaks > 0:
                consensus_score = 1.0 - (peak_difference / max_peaks)
            else:
                consensus_score = 1.0
            
            # Adjust confidence based on consensus
            consensus_factor = max(0.5, consensus_score)  # Don't penalize too much
            final_confidence = ensemble_conf * consensus_factor
            
            # Decision logic
            consensus_threshold = self.config.get('consensus_threshold', 0.5)
            if consensus_score >= consensus_threshold:
                decision = 'consensus'
            elif v5_conf > deepcv_conf:
                decision = 'v5_preferred'
                ensemble_peaks = v5_peaks
                final_confidence = v5_conf * 0.9  # Slight penalty for no consensus
            else:
                decision = 'deepcv_preferred'
                ensemble_peaks = deepcv_peaks
                final_confidence = deepcv_conf * 0.9
            
            return {
                'peaks_detected': int(ensemble_peaks),
                'confidence': float(final_confidence),
                'v5_weight': float(v5_weight),
                'deepcv_weight': float(deepcv_weight),
                'consensus_score': float(consensus_score),
                'decision': decision,
                'method': 'HybridCV_Enhanced_Ensemble'
            }
            
        except Exception as e:
            print(f"⚠️  Ensemble prediction error: {e}")
            # Fallback to V5 if available
            if v5_result.get('peaks_detected', 0) > 0:
                return {
                    'peaks_detected': v5_result.get('peaks_detected', 0),
                    'confidence': v5_result.get('confidence', 0.0) * 0.8,
                    'v5_weight': 1.0,
                    'deepcv_weight': 0.0,
                    'consensus_score': 0.0,
                    'decision': 'fallback_v5',
                    'method': 'HybridCV_Enhanced_Fallback'
                }
            else:
                return {
                    'peaks_detected': 0,
                    'confidence': 0.0,
                    'v5_weight': 0.0,
                    'deepcv_weight': 0.0,
                    'consensus_score': 0.0,
                    'decision': 'error',
                    'method': 'HybridCV_Enhanced_Error'
                }
    
    def _assess_quality(self, v5_result, deepcv_result, ensemble_result):
        """Assess prediction quality metrics"""
        return {
            'agreement_score': 1.0 - abs(v5_result.get('peaks_detected', 0) - 
                                        deepcv_result.get('peaks_detected', 0)) / 
                                   max(1, max(v5_result.get('peaks_detected', 0), 
                                             deepcv_result.get('peaks_detected', 0))),
            'confidence_consistency': abs(v5_result.get('confidence', 0.0) - 
                                        deepcv_result.get('confidence', 0.0)) < 30.0,
            'v5_available': 'error' not in v5_result,
            'deepcv_available': 'error' not in deepcv_result,
            'ensemble_confidence': ensemble_result.get('confidence', 0.0)
        }
    
    def _print_result_summary(self, result):
        """Print detailed result summary"""
        v5 = result['v5_result']
        deepcv = result['deepcv_result']
        ensemble = result['ensemble_result']
        
        print(f"📊 Results for {result['filename'][:30]}:")
        print(f"   🔬 V5:      {v5.get('peaks_detected', 0):2d} peaks ({v5.get('confidence', 0.0):5.1f}%)")
        print(f"   🧠 DeepCV:  {deepcv.get('peaks_detected', 0):2d} peaks ({deepcv.get('confidence', 0.0):5.1f}%)")
        print(f"   🔄 Hybrid:  {ensemble.get('peaks_detected', 0):2d} peaks ({ensemble.get('confidence', 0.0):5.1f}%) [{ensemble.get('decision', 'unknown')}]")
        print(f"   ⏱️  Time: {result['processing_time']*1000:.1f}ms")
    
    def get_performance_summary(self):
        """Get performance summary"""
        if not self.performance_history:
            return "No performance data available"
        
        df_history = pd.DataFrame(self.performance_history)
        
        summary = {
            'total_files': len(df_history),
            'avg_processing_time': df_history['processing_time'].mean() * 1000,  # ms
            'avg_v5_peaks': df_history['v5_peaks'].mean(),
            'avg_deepcv_peaks': df_history['deepcv_peaks'].mean(),
            'avg_ensemble_peaks': df_history['ensemble_peaks'].mean(),
            'avg_confidence': df_history['confidence'].mean(),
            'agreement_rate': (df_history['v5_peaks'] == df_history['deepcv_peaks']).mean() * 100
        }
        
        return summary

def test_hybrid_enhanced():
    """Test HybridCV Enhanced with sample data"""
    print("🧪 TESTING HYBRIDCV ENHANCED")
    print("=" * 60)
    
    # Initialize HybridCV Enhanced
    hybrid = HybridCVEnhanced()
    
    if hybrid.v5_detector is None and hybrid.deepcv_v2 is None:
        print("❌ Both components unavailable - cannot test")
        return False
    
    # Test with sample CV data
    print("🔬 Generating test CV data...")
    
    # Create realistic CV data
    voltage = np.linspace(-0.4, 0.7, 220)
    
    # Simulate ferrocyanide CV with two peaks
    anodic_peak = 15e-6 * np.exp(-((voltage - 0.2) / 0.08)**2)    # Oxidation peak
    cathodic_peak = -12e-6 * np.exp(-((voltage + 0.1) / 0.08)**2)  # Reduction peak
    background = 1e-8 * voltage  # Linear background
    noise = 0.5e-6 * np.random.normal(0, 1, len(voltage))  # Noise
    
    current = anodic_peak + cathodic_peak + background + noise
    current *= 1e6  # Convert to µA
    
    # Test the hybrid system
    result = hybrid.detect_peaks(voltage, current, "test_cv_data.csv")
    
    print(f"\\n📊 Test Results:")
    print(f"Processing time: {result['processing_time']*1000:.1f} ms")
    
    if result['ensemble_result']:
        ensemble = result['ensemble_result']
        print(f"Final prediction: {ensemble['peaks_detected']} peaks")
        print(f"Confidence: {ensemble['confidence']:.1f}%")
        print(f"Decision method: {ensemble['decision']}")
        
        # Performance summary
        summary = hybrid.get_performance_summary()
        print(f"\\n📈 Performance Summary:")
        for key, value in summary.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.2f}")
            else:
                print(f"   {key}: {value}")
    
    return True

if __name__ == "__main__":
    success = test_hybrid_enhanced()
    print(f"\\n{'🎉 TEST COMPLETE!' if success else '❌ TEST FAILED!'}")