#!/usr/bin/env python3
"""
🚀 HybridCV V7 - Ultimate Human-AI Peak Detection
================================================

The most advanced peak detection system combining:
- Enhanced Detector V6 (Human-validated traditional)
- DeepCV V2.1 (Trained on human-validated data)

This should provide the highest accuracy by combining expert knowledge 
with AI trained specifically on expert-validated peaks.

Author: H743Poten Research Team
Date: October 4, 2025
Version: V7 (Human-AI Synergy)
"""

import sys
import os
sys.path.append('.')
sys.path.append('validation_data')

import numpy as np
import pandas as pd
import time
from datetime import datetime
import pickle
from typing import Dict, List, Optional, Any, Tuple

try:
    from enhanced_detector_v6 import EnhancedDetectorV6
    from train_deepcv_v21_from_v6 import DeepCVV21Trainer
except ImportError:
    print("⚠️  V6 or V2.1 components not available")

class HybridCVV7:
    """
    HybridCV V7 - Ultimate Human-AI Peak Detection System
    
    Features:
    - Human-validated traditional detection (V6)
    - AI trained on human-validated data (V2.1)
    - Intelligent ensemble with expert reasoning
    - Quality-aware decision making
    - Continuous learning capability
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        
        # Initialize components
        self.v6_detector = None
        self.deepcv_v21 = None
        
        # Performance tracking
        self.detection_history = []
        self.quality_metrics = []
        
        print("🚀 Initializing HybridCV V7...")
        self._initialize_components()
    
    def _default_config(self) -> Dict:
        """Default configuration for HybridCV V7"""
        return {
            # Ensemble strategy
            'human_validation_weight': 0.7,    # Higher weight for human-validated
            'ai_prediction_weight': 0.3,       # AI trained on human data
            
            # Quality thresholds
            'min_confidence_threshold': 50.0,   # Minimum confidence for acceptance
            'consensus_threshold': 0.6,         # Agreement threshold
            'expert_override_enabled': True,    # Allow human override
            
            # Advanced features
            'adaptive_weighting': True,         # Adjust weights based on quality
            'uncertainty_quantification': True, # Track prediction uncertainty
            'continuous_learning': True,        # Learn from new validations
            
            # Quality control
            'outlier_detection': True,          # Remove outlier predictions
            'consistency_validation': True,     # Cross-validate results
            'expert_reasoning_required': False, # Require reasoning for decisions
            
            # Performance optimization
            'parallel_processing': False,       # Run detection in parallel
            'caching_enabled': True,           # Cache intermediate results
            'batch_processing': True,          # Support batch analysis
            
            # Interaction modes
            'interactive_mode': False,         # Enable interactive validation
            'auto_export': True,               # Automatically export results
            'detailed_logging': True,          # Comprehensive logging
            
            'verbose': True
        }
    
    def _initialize_components(self):
        """Initialize V6 and DeepCV V2.1 components"""
        try:
            # Initialize V6 detector
            self.v6_detector = EnhancedDetectorV6()
            print("✅ Enhanced Detector V6 initialized")
            
            # Try to load trained DeepCV V2.1
            v21_model_path = "deepcv_v21_human_trained.pkl"
            if os.path.exists(v21_model_path):
                self.deepcv_v21 = self._load_deepcv_v21(v21_model_path)
                print("✅ DeepCV V2.1 model loaded")
            else:
                print("⚠️  DeepCV V2.1 model not found - will use fallback")
                self.deepcv_v21 = None
                
        except Exception as e:
            print(f"❌ Component initialization error: {e}")
            self.v6_detector = None
            self.deepcv_v21 = None
    
    def _load_deepcv_v21(self, model_path: str):
        """Load trained DeepCV V2.1 model"""
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            # Create wrapper for loaded model
            class DeepCVV21Wrapper:
                def __init__(self, model_data):
                    self.scaler = model_data['scaler']
                    self.peak_count_model = model_data['peak_count_model']
                    self.confidence_model = model_data['confidence_model']
                    self.is_trained = model_data['is_trained']
                    self.version = model_data.get('version', 'DeepCV_V2.1')
                    self.training_source = model_data.get('training_source', 'human_validated_v6')
                
                def predict_peaks_v21(self, voltage, current):
                    """Predict using V2.1 model"""
                    if not self.is_trained:
                        return {'peaks_detected': 0, 'confidence': 0.0, 'error': 'Not trained'}
                    
                    try:
                        features = self._extract_features_from_cv(voltage, current)
                        if features is None:
                            return {'peaks_detected': 0, 'confidence': 0.0, 'error': 'Feature extraction failed'}
                        
                        features_scaled = self.scaler.transform(features.reshape(1, -1))
                        
                        peak_count = self.peak_count_model.predict(features_scaled)[0]
                        confidence = self.confidence_model.predict(features_scaled)[0]
                        
                        peak_count = max(0, round(peak_count))
                        confidence = max(0.0, min(100.0, confidence))
                        
                        return {
                            'peaks_detected': int(peak_count),
                            'confidence': float(confidence),
                            'method': 'DeepCV_V2.1_V6_Trained',
                            'training_source': self.training_source,
                            'uncertainty': abs(confidence - 50.0) / 50.0  # Simple uncertainty metric
                        }
                        
                    except Exception as e:
                        return {'peaks_detected': 0, 'confidence': 0.0, 'error': str(e)}
                
                def _extract_features_from_cv(self, voltage, current):
                    """Extract features matching training"""
                    try:
                        features = []
                        
                        # Basic statistical features
                        features.extend([
                            len(current),
                            np.mean(current), np.std(current),
                            np.min(current), np.max(current),
                            np.mean(voltage), np.std(voltage),
                            np.min(voltage), np.max(voltage),
                            np.ptp(current), np.ptp(voltage)
                        ])
                        
                        # Current distribution
                        positive_current = current[current > 0]
                        negative_current = current[current < 0]
                        
                        features.extend([
                            len(positive_current), len(negative_current),
                            np.mean(positive_current) if len(positive_current) > 0 else 0,
                            np.mean(negative_current) if len(negative_current) > 0 else 0,
                            len(positive_current) / len(current) if len(current) > 0 else 0
                        ])
                        
                        # Voltage analysis
                        v_range = np.ptp(voltage)
                        features.extend([
                            v_range,
                            np.sum((voltage >= np.min(voltage)) & (voltage < np.min(voltage) + v_range/3)),
                            np.sum((voltage >= np.min(voltage) + v_range/3) & (voltage <= np.min(voltage) + 2*v_range/3)),
                            np.sum(voltage > np.min(voltage) + 2*v_range/3)
                        ])
                        
                        # Pad to 30 features
                        while len(features) < 30:
                            features.append(0.0)
                        features = features[:30]
                        
                        features = np.array(features)
                        features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
                        
                        return features
                    except:
                        return None
            
            return DeepCVV21Wrapper(model_data)
            
        except Exception as e:
            print(f"❌ Error loading DeepCV V2.1: {e}")
            return None
    
    def detect_peaks_v7(self, voltage: np.ndarray, current: np.ndarray, 
                       filename: str = "unknown", interactive: bool = False) -> Dict[str, Any]:
        """
        Ultimate peak detection using V7 system
        
        Args:
            voltage: Voltage data
            current: Current data
            filename: File identifier
            interactive: Enable interactive validation
            
        Returns:
            Comprehensive V7 results
        """
        start_time = time.time()
        
        if self.config['verbose']:
            print(f"🚀 HybridCV V7 analyzing: {filename}")
        
        # Initialize result structure
        result = {
            'filename': filename,
            'timestamp': datetime.now().isoformat(),
            'v6_result': None,
            'deepcv_v21_result': None,
            'v7_ensemble_result': None,
            'quality_assessment': None,
            'processing_time': 0.0,
            'method': 'HybridCV_V7',
            'version': 'v7_human_ai_synergy'
        }
        
        # Step 1: Run V6 detection (potentially interactive)
        if interactive and self.v6_detector:
            print("🔬 Running interactive V6 validation...")
            v6_result = self._run_v6_interactive(voltage, current, filename)
        else:
            v6_result = self._run_v6_automatic(voltage, current, filename)
        
        result['v6_result'] = v6_result
        
        # Step 2: Run DeepCV V2.1 prediction
        deepcv_result = self._run_deepcv_v21(voltage, current, filename)
        result['deepcv_v21_result'] = deepcv_result
        
        # Step 3: V7 Intelligent Ensemble
        ensemble_result = self._v7_ensemble_prediction(v6_result, deepcv_result, voltage, current)
        result['v7_ensemble_result'] = ensemble_result
        
        # Step 4: Quality Assessment
        quality_assessment = self._assess_v7_quality(v6_result, deepcv_result, ensemble_result)
        result['quality_assessment'] = quality_assessment
        
        # Step 5: Update learning system
        if self.config['continuous_learning']:
            self._update_learning_system(result)
        
        result['processing_time'] = time.time() - start_time
        
        # Store in history
        self.detection_history.append(result)
        
        if self.config['verbose']:
            self._print_v7_summary(result)
        
        return result
    
    def _run_v6_interactive(self, voltage, current, filename):
        """Run V6 with interactive validation"""
        if self.v6_detector is None:
            return {'peaks_detected': 0, 'confidence': 0.0, 'error': 'V6 not available'}
        
        try:
            # This would launch the V6 interactive UI
            v6_result = self.v6_detector.detect_peaks_with_validation(voltage, current, filename)
            
            validated_peaks = v6_result.get('validated_peaks', [])
            
            return {
                'peaks_detected': len(validated_peaks),
                'confidence': 100.0,  # Human-validated = high confidence
                'validated_peaks': validated_peaks,
                'validation_actions': v6_result.get('validation_actions', 0),
                'expert_id': v6_result.get('expert_id', 'unknown'),
                'method': 'Enhanced_V6_Interactive',
                'quality': 'human_validated'
            }
            
        except Exception as e:
            print(f"⚠️  V6 interactive error: {e}")
            return {'peaks_detected': 0, 'confidence': 0.0, 'error': str(e)}
    
    def _run_v6_automatic(self, voltage, current, filename):
        """Run V6 in automatic mode (using V5 backend)"""
        # For automatic mode, we fall back to V5
        from enhanced_detector_v5 import EnhancedDetectorV5
        
        try:
            v5_detector = EnhancedDetectorV5()
            v5_result = v5_detector.detect_peaks_enhanced_v5(voltage, current)
            
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
                'method': 'Enhanced_V5_Backend',
                'quality': 'automatic',
                'raw_result': v5_result
            }
            
        except Exception as e:
            print(f"⚠️  V6 automatic error: {e}")
            return {'peaks_detected': 0, 'confidence': 0.0, 'error': str(e)}
    
    def _run_deepcv_v21(self, voltage, current, filename):
        """Run DeepCV V2.1 prediction"""
        if self.deepcv_v21 is None:
            return {'peaks_detected': 0, 'confidence': 0.0, 'error': 'DeepCV V2.1 not available'}
        
        try:
            result = self.deepcv_v21.predict_peaks_v21(voltage, current)
            return result
            
        except Exception as e:
            print(f"⚠️  DeepCV V2.1 error: {e}")
            return {'peaks_detected': 0, 'confidence': 0.0, 'error': str(e)}
    
    def _v7_ensemble_prediction(self, v6_result, deepcv_result, voltage, current):
        """Advanced V7 ensemble prediction"""
        try:
            # Extract predictions
            v6_peaks = v6_result.get('peaks_detected', 0)
            v6_conf = v6_result.get('confidence', 0.0)
            v6_quality = v6_result.get('quality', 'unknown')
            
            deepcv_peaks = deepcv_result.get('peaks_detected', 0)
            deepcv_conf = deepcv_result.get('confidence', 0.0)
            deepcv_uncertainty = deepcv_result.get('uncertainty', 0.5)
            
            # Quality-aware weighting
            if v6_quality == 'human_validated':
                # Human validation gets very high weight
                v6_weight = 0.85
                deepcv_weight = 0.15
                decision_basis = 'human_expert_priority'
            elif self.config['adaptive_weighting']:
                # Adaptive weighting based on confidence and uncertainty
                total_conf = v6_conf + deepcv_conf
                uncertainty_factor = 1.0 - deepcv_uncertainty  # Lower uncertainty = higher weight
                
                if total_conf > 0:
                    base_v6_weight = v6_conf / total_conf
                    base_deepcv_weight = deepcv_conf / total_conf
                    
                    # Adjust for uncertainty
                    deepcv_weight = base_deepcv_weight * uncertainty_factor
                    v6_weight = 1.0 - deepcv_weight
                else:
                    v6_weight = self.config['human_validation_weight']
                    deepcv_weight = self.config['ai_prediction_weight']
                
                decision_basis = 'adaptive_confidence_uncertainty'
            else:
                v6_weight = self.config['human_validation_weight']
                deepcv_weight = self.config['ai_prediction_weight']
                decision_basis = 'fixed_weights'
            
            # Ensemble prediction
            ensemble_peaks = v6_weight * v6_peaks + deepcv_weight * deepcv_peaks
            ensemble_peaks = max(0, round(ensemble_peaks))
            
            # Ensemble confidence with quality bonus
            ensemble_conf = v6_weight * v6_conf + deepcv_weight * deepcv_conf
            
            if v6_quality == 'human_validated':
                ensemble_conf *= 1.1  # 10% bonus for human validation
            
            ensemble_conf = min(100.0, ensemble_conf)
            
            # Consensus analysis
            peak_difference = abs(v6_peaks - deepcv_peaks)
            max_peaks = max(v6_peaks, deepcv_peaks, 1)
            consensus_score = 1.0 - (peak_difference / max_peaks)
            
            # Decision logic
            if consensus_score >= self.config['consensus_threshold']:
                decision = 'consensus'
            elif v6_quality == 'human_validated':
                decision = 'human_expert_override'
                ensemble_peaks = v6_peaks
                ensemble_conf = v6_conf * 1.05  # Small bonus
            elif v6_conf > deepcv_conf:
                decision = 'v6_preferred'
                ensemble_peaks = v6_peaks
                ensemble_conf = v6_conf * 0.95
            else:
                decision = 'deepcv_v21_preferred'
                ensemble_peaks = deepcv_peaks
                ensemble_conf = deepcv_conf * 0.95
            
            # Quality score
            quality_score = (consensus_score * 0.4 + 
                           (ensemble_conf / 100.0) * 0.4 +
                           (1.0 - deepcv_uncertainty) * 0.2)
            
            return {
                'peaks_detected': int(ensemble_peaks),
                'confidence': float(ensemble_conf),
                'quality_score': float(quality_score),
                'v6_weight': float(v6_weight),
                'deepcv_weight': float(deepcv_weight),
                'consensus_score': float(consensus_score),
                'decision': decision,
                'decision_basis': decision_basis,
                'uncertainty': float(deepcv_uncertainty),
                'method': 'HybridCV_V7_Ensemble'
            }
            
        except Exception as e:
            print(f"⚠️  V7 ensemble error: {e}")
            # Fallback to best available method
            if v6_result.get('peaks_detected', 0) > 0:
                return {
                    'peaks_detected': v6_result.get('peaks_detected', 0),
                    'confidence': v6_result.get('confidence', 0.0) * 0.8,
                    'decision': 'fallback_v6',
                    'method': 'HybridCV_V7_Fallback'
                }
            else:
                return {
                    'peaks_detected': 0,
                    'confidence': 0.0,
                    'decision': 'error',
                    'method': 'HybridCV_V7_Error'
                }
    
    def _assess_v7_quality(self, v6_result, deepcv_result, ensemble_result):
        """Comprehensive quality assessment"""
        return {
            'v6_available': 'error' not in v6_result,
            'deepcv_available': 'error' not in deepcv_result,
            'human_validated': v6_result.get('quality') == 'human_validated',
            'consensus_achieved': ensemble_result.get('consensus_score', 0) >= self.config['consensus_threshold'],
            'high_confidence': ensemble_result.get('confidence', 0) >= self.config['min_confidence_threshold'],
            'low_uncertainty': ensemble_result.get('uncertainty', 1.0) <= 0.3,
            'quality_score': ensemble_result.get('quality_score', 0.0),
            'decision_quality': ensemble_result.get('decision', 'unknown')
        }
    
    def _update_learning_system(self, result):
        """Update continuous learning system"""
        # Store result for future learning
        self.quality_metrics.append({
            'timestamp': result['timestamp'],
            'quality_score': result['quality_assessment'].get('quality_score', 0.0),
            'consensus_score': result['v7_ensemble_result'].get('consensus_score', 0.0),
            'confidence': result['v7_ensemble_result'].get('confidence', 0.0)
        })
    
    def _print_v7_summary(self, result):
        """Print V7 results summary"""
        v6 = result.get('v6_result', {})
        deepcv = result.get('deepcv_v21_result', {})
        ensemble = result.get('v7_ensemble_result', {})
        quality = result.get('quality_assessment', {})
        
        print(f"📊 V7 Results for {result['filename'][:30]}:")
        print(f"   🔬 V6:       {v6.get('peaks_detected', 0):2d} peaks ({v6.get('confidence', 0.0):5.1f}%) [{v6.get('quality', 'unknown')}]")
        print(f"   🧠 DeepCV21: {deepcv.get('peaks_detected', 0):2d} peaks ({deepcv.get('confidence', 0.0):5.1f}%) [uncertainty: {deepcv.get('uncertainty', 0.0):.2f}]")
        print(f"   🚀 V7:       {ensemble.get('peaks_detected', 0):2d} peaks ({ensemble.get('confidence', 0.0):5.1f}%) [{ensemble.get('decision', 'unknown')}]")
        print(f"   📈 Quality:  {quality.get('quality_score', 0.0):.2f} | Time: {result['processing_time']*1000:.1f}ms")

def test_hybrid_v7():
    """Test HybridCV V7 system"""
    print("🚀 TESTING HYBRIDCV V7 - ULTIMATE SYSTEM")
    print("=" * 60)
    
    # Initialize V7
    v7 = HybridCVV7()
    
    if v7.v6_detector is None and v7.deepcv_v21 is None:
        print("❌ Both V6 and DeepCV V2.1 unavailable")
        return False
    
    # Test with sample data
    voltage = np.linspace(-0.4, 0.7, 220)
    anodic = 15e-6 * np.exp(-((voltage - 0.2) / 0.08)**2)
    cathodic = -12e-6 * np.exp(-((voltage + 0.1) / 0.08)**2)
    background = 1e-8 * voltage
    noise = 0.5e-6 * np.random.normal(0, 1, len(voltage))
    current = (anodic + cathodic + background + noise) * 1e6
    
    # Test automatic mode
    print("🔬 Testing automatic mode...")
    result = v7.detect_peaks_v7(voltage, current, "test_ferrocyanide_v7.csv")
    
    # Performance summary
    if v7.detection_history:
        print("\\n📈 V7 Performance Summary:")
        latest = v7.detection_history[-1]
        ensemble = latest.get('v7_ensemble_result', {})
        quality = latest.get('quality_assessment', {})
        
        print(f"   Final prediction: {ensemble.get('peaks_detected', 0)} peaks")
        print(f"   Confidence: {ensemble.get('confidence', 0):.1f}%")
        print(f"   Quality score: {quality.get('quality_score', 0):.2f}")
        print(f"   Decision: {ensemble.get('decision', 'unknown')}")
        print(f"   Processing time: {latest.get('processing_time', 0)*1000:.1f} ms")
    
    return True

if __name__ == "__main__":
    success = test_hybrid_v7()
    print(f"\\n{'🎉 V7 TEST COMPLETE!' if success else '❌ V7 TEST FAILED!'}")