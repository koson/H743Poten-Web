"""
Neural Network Peak Classifier for Electrochemical Analysis
Uses lightweight neural networks optimized for Raspberry Pi
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Check for ML dependencies
try:
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, accuracy_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("Scikit-learn not available - ML features will be limited")

@dataclass
class PeakFeatures:
    """Features extracted from electrochemical peaks for ML classification"""
    height: float           # Peak current magnitude
    width: float           # Peak width at half maximum
    potential: float       # Peak potential
    area: float           # Peak area (integrated current)
    symmetry: float       # Peak symmetry ratio
    sharpness: float      # Peak sharpness (height/width ratio)
    prominence: float     # Peak prominence above baseline
    noise_level: float    # Local noise level around peak

@dataclass
class PeakClassification:
    """Result of peak classification"""
    peak_type: str        # e.g., "oxidation", "reduction", "faradaic", "capacitive"
    confidence: float     # Classification confidence (0-1)
    analyte_class: str    # Predicted analyte class if available
    features: PeakFeatures # Original features used for classification
    timestamp: datetime   # Classification timestamp

class PeakClassifier:
    """
    Neural network-based peak classifier for electrochemical analysis
    Optimized for real-time analysis on Raspberry Pi
    """
    
    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.model_config = model_config or self._get_default_config()
        
        # Initialize model components
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.classifier = None
        self.is_trained = False
        self.feature_names = [
            'height', 'width', 'potential', 'area', 
            'symmetry', 'sharpness', 'prominence', 'noise_level'
        ]
        
        # Performance tracking
        self.classification_count = 0
        self.accuracy_history = []
        
        if SKLEARN_AVAILABLE:
            self._initialize_model()
        else:
            self.logger.warning("Running in fallback mode - limited ML capabilities")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default neural network configuration optimized for RPi"""
        return {
            'hidden_layers': (50, 25),  # Smaller networks for RPi
            'activation': 'relu',
            'solver': 'adam',
            'alpha': 0.001,  # L2 regularization
            'batch_size': 'auto',
            'learning_rate': 'constant',
            'learning_rate_init': 0.001,
            'max_iter': 500,  # Reasonable for embedded systems
            'random_state': 42,
            'early_stopping': True,
            'validation_fraction': 0.1,
            'n_iter_no_change': 10
        }
    
    def _initialize_model(self):
        """Initialize the neural network model"""
        if not SKLEARN_AVAILABLE:
            return
            
        try:
            self.classifier = MLPClassifier(**self.model_config)
            self.logger.info("Neural network peak classifier initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize classifier: {e}")
            self.classifier = None
    
    def extract_features(self, voltages: np.ndarray, currents: np.ndarray, 
                        peak_indices: List[int]) -> List[PeakFeatures]:
        """
        Extract features from detected peaks for classification
        
        Args:
            voltages: Voltage array
            currents: Current array  
            peak_indices: Indices of detected peaks
            
        Returns:
            List of PeakFeatures objects
        """
        features_list = []
        
        for peak_idx in peak_indices:
            try:
                # Basic peak properties
                height = abs(currents[peak_idx])
                potential = voltages[peak_idx]
                
                # Calculate peak width (simple FWHM estimation)
                width = self._calculate_peak_width(currents, peak_idx)
                
                # Calculate peak area (trapezoid integration)
                area = self._calculate_peak_area(currents, peak_idx, width)
                
                # Calculate symmetry
                symmetry = self._calculate_peak_symmetry(currents, peak_idx, width)
                
                # Calculate sharpness
                sharpness = height / max(width, 1e-9)  # Avoid division by zero
                
                # Calculate prominence
                prominence = self._calculate_prominence(currents, peak_idx)
                
                # Estimate local noise level
                noise_level = self._estimate_noise_level(currents, peak_idx)
                
                features = PeakFeatures(
                    height=height,
                    width=width,
                    potential=potential,
                    area=area,
                    symmetry=symmetry,
                    sharpness=sharpness,
                    prominence=prominence,
                    noise_level=noise_level
                )
                
                features_list.append(features)
                
            except Exception as e:
                self.logger.warning(f"Failed to extract features for peak {peak_idx}: {e}")
                
        return features_list
    
    def _calculate_peak_width(self, currents: np.ndarray, peak_idx: int) -> float:
        """Calculate peak width at half maximum"""
        try:
            peak_height = abs(currents[peak_idx])
            half_height = peak_height / 2
            
            # Find left boundary
            left_idx = peak_idx
            while left_idx > 0 and abs(currents[left_idx]) > half_height:
                left_idx -= 1
                
            # Find right boundary  
            right_idx = peak_idx
            while right_idx < len(currents) - 1 and abs(currents[right_idx]) > half_height:
                right_idx += 1
                
            return max(right_idx - left_idx, 1)  # Minimum width of 1
            
        except Exception:
            return 5.0  # Default width
    
    def _calculate_peak_area(self, currents: np.ndarray, peak_idx: int, width: float) -> float:
        """Calculate peak area using trapezoidal integration"""
        try:
            half_width = int(width // 2)
            start_idx = max(0, peak_idx - half_width)
            end_idx = min(len(currents), peak_idx + half_width + 1)
            
            # Simple trapezoidal integration
            area = np.trapz(np.abs(currents[start_idx:end_idx]))
            return area
            
        except Exception:
            return abs(currents[peak_idx]) * width  # Fallback approximation
    
    def _calculate_peak_symmetry(self, currents: np.ndarray, peak_idx: int, width: float) -> float:
        """Calculate peak symmetry ratio"""
        try:
            half_width = int(width // 2)
            
            # Get left and right halves
            left_start = max(0, peak_idx - half_width)
            right_end = min(len(currents), peak_idx + half_width + 1)
            
            left_area = np.trapz(np.abs(currents[left_start:peak_idx]))
            right_area = np.trapz(np.abs(currents[peak_idx:right_end]))
            
            if right_area == 0:
                return 0.0
                
            return min(left_area, right_area) / max(left_area, right_area)
            
        except Exception:
            return 0.5  # Default moderate asymmetry
    
    def _calculate_prominence(self, currents: np.ndarray, peak_idx: int) -> float:
        """Calculate peak prominence above local baseline"""
        try:
            window_size = 20  # Local window for baseline estimation
            start_idx = max(0, peak_idx - window_size)
            end_idx = min(len(currents), peak_idx + window_size + 1)
            
            local_currents = currents[start_idx:end_idx]
            baseline = np.median(local_currents)  # Robust baseline estimate
            
            return abs(currents[peak_idx] - baseline)
            
        except Exception:
            return abs(currents[peak_idx])  # Fallback to absolute height
    
    def _estimate_noise_level(self, currents: np.ndarray, peak_idx: int) -> float:
        """Estimate local noise level around peak"""
        try:
            window_size = 10
            start_idx = max(0, peak_idx - window_size)
            end_idx = min(len(currents), peak_idx + window_size + 1)
            
            local_currents = currents[start_idx:end_idx]
            
            # Calculate noise as standard deviation after smoothing
            if len(local_currents) > 3:
                # Simple moving average for smoothing
                smoothed = np.convolve(local_currents, np.ones(3)/3, mode='valid')
                noise = np.std(local_currents[1:-1] - smoothed)
            else:
                noise = np.std(local_currents)
                
            return noise
            
        except Exception:
            return 1e-9  # Default minimal noise level
    
    def classify_peaks(self, features_list: List[PeakFeatures]) -> List[PeakClassification]:
        """
        Classify peaks based on extracted features
        
        Args:
            features_list: List of PeakFeatures to classify
            
        Returns:
            List of PeakClassification results
        """
        classifications = []
        
        if not self.is_trained or not SKLEARN_AVAILABLE:
            # Fallback to rule-based classification
            return self._rule_based_classification(features_list)
        
        try:
            # Convert features to array
            feature_array = self._features_to_array(features_list)
            
            # Scale features
            feature_array_scaled = self.scaler.transform(feature_array)
            
            # Predict classes and probabilities
            predictions = self.classifier.predict(feature_array_scaled)
            probabilities = self.classifier.predict_proba(feature_array_scaled)
            
            # Create classification results
            for i, (features, pred, probs) in enumerate(zip(features_list, predictions, probabilities)):
                confidence = np.max(probs)
                
                classification = PeakClassification(
                    peak_type=pred,
                    confidence=confidence,
                    analyte_class="unknown",  # Would need additional training
                    features=features,
                    timestamp=datetime.now()
                )
                
                classifications.append(classification)
                
            self.classification_count += len(classifications)
            self.logger.info(f"Classified {len(classifications)} peaks with ML model")
            
        except Exception as e:
            self.logger.error(f"ML classification failed: {e}")
            return self._rule_based_classification(features_list)
        
        return classifications
    
    def _rule_based_classification(self, features_list: List[PeakFeatures]) -> List[PeakClassification]:
        """Fallback rule-based classification when ML is not available"""
        classifications = []
        
        for features in features_list:
            # Simple rules based on electrochemical knowledge
            if features.potential > 0:
                peak_type = "oxidation"
            else:
                peak_type = "reduction"
                
            # Confidence based on peak quality metrics
            snr = features.height / max(features.noise_level, 1e-9)
            confidence = min(0.9, max(0.1, snr / 20))  # Scale SNR to confidence
            
            classification = PeakClassification(
                peak_type=peak_type,
                confidence=confidence,
                analyte_class="unknown",
                features=features,
                timestamp=datetime.now()
            )
            
            classifications.append(classification)
        
        self.logger.info(f"Used rule-based classification for {len(classifications)} peaks")
        return classifications
    
    def _features_to_array(self, features_list: List[PeakFeatures]) -> np.ndarray:
        """Convert PeakFeatures list to numpy array for ML processing"""
        feature_array = []
        
        for features in features_list:
            row = [
                features.height,
                features.width,
                features.potential,
                features.area,
                features.symmetry,
                features.sharpness,
                features.prominence,
                features.noise_level
            ]
            feature_array.append(row)
            
        return np.array(feature_array)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            'sklearn_available': SKLEARN_AVAILABLE,
            'is_trained': self.is_trained,
            'classification_count': self.classification_count,
            'feature_names': self.feature_names,
            'model_config': self.model_config,
            'accuracy_history': self.accuracy_history[-10:] if self.accuracy_history else []
        }

# Demo function for immediate testing
def demo_peak_classification():
    """Demonstrate peak classification with synthetic data"""
    print("🧠 Peak Classification Demo")
    print("=" * 40)
    
    # Create synthetic electrochemical data
    np.random.seed(42)
    voltages = np.linspace(-0.5, 0.5, 100)
    
    # Add some synthetic peaks
    currents = np.random.normal(0, 1e-8, 100)  # Background noise
    currents[30] += 5e-6  # Reduction peak
    currents[70] += 3e-6  # Oxidation peak
    
    # Initialize classifier
    classifier = PeakClassifier()
    
    # Detect peaks (simple)
    peak_indices = [30, 70]
    
    # Extract features
    features = classifier.extract_features(voltages, currents, peak_indices)
    
    # Classify peaks
    classifications = classifier.classify_peaks(features)
    
    # Display results
    for i, (features, classification) in enumerate(zip(features, classifications)):
        print(f"\nPeak {i+1}:")
        print(f"  Potential: {features.potential:.3f} V")
        print(f"  Height: {features.height:.2e} A")
        print(f"  Type: {classification.peak_type}")
        print(f"  Confidence: {classification.confidence:.1%}")
    
    # Model info
    info = classifier.get_model_info()
    print(f"\nModel Info:")
    print(f"  Sklearn Available: {info['sklearn_available']}")
    print(f"  Classifications: {info['classification_count']}")
    
    return classifier, classifications

if __name__ == "__main__":
    demo_peak_classification()
