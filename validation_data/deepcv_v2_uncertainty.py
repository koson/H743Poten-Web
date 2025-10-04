#!/usr/bin/env python3
"""
🎲 DeepCV V2 Uncertainty Quantification & Bayesian Methods
==========================================================

Advanced uncertainty quantification using Bayesian neural networks,
Monte Carlo methods, and ensemble techniques for robust peak detection.

Author: H743Poten Research Team
Date: October 4, 2025
Version: 2.0.0

Features:
- Bayesian Neural Networks with variational inference
- Monte Carlo Dropout for uncertainty estimation
- Deep Ensembles for robust predictions
- Aleatoric and Epistemic uncertainty decomposition
- Confidence interval estimation
- Uncertainty-aware peak detection
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import time

# Scientific computing imports with fallbacks
try:
    import scipy.stats
    from scipy.stats import norm, beta, gamma
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("⚠️  SciPy not available - using basic uncertainty implementations")

# Try PyTorch imports with fallbacks
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.distributions import Normal, Bernoulli
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️  PyTorch not available - using basic implementations")

logger = logging.getLogger(__name__)

@dataclass
class UncertaintyEstimate:
    """Container for uncertainty estimates"""
    mean_prediction: np.ndarray
    aleatoric_uncertainty: np.ndarray  # Data uncertainty
    epistemic_uncertainty: np.ndarray  # Model uncertainty
    total_uncertainty: np.ndarray      # Combined uncertainty
    confidence_intervals: Dict[str, Tuple[np.ndarray, np.ndarray]]  # CI bounds
    prediction_samples: Optional[np.ndarray]  # Monte Carlo samples
    metadata: Dict[str, Any]

class BayesianLayer(nn.Module):
    """Bayesian linear layer with weight uncertainty"""
    
    def __init__(self, in_features: int, out_features: int, prior_std: float = 0.1):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.prior_std = prior_std
        
        # Weight parameters (mean and log variance)
        self.weight_mu = nn.Parameter(torch.randn(out_features, in_features) * 0.1)
        self.weight_log_var = nn.Parameter(torch.randn(out_features, in_features) * 0.1 - 5)
        
        # Bias parameters
        self.bias_mu = nn.Parameter(torch.randn(out_features) * 0.1)
        self.bias_log_var = nn.Parameter(torch.randn(out_features) * 0.1 - 5)
        
        self.kl_divergence = 0
    
    def forward(self, x, sample: bool = True):
        if sample:
            # Sample weights from posterior
            weight_std = torch.exp(0.5 * self.weight_log_var)
            weight_eps = torch.randn_like(self.weight_mu)
            weight = self.weight_mu + weight_std * weight_eps
            
            bias_std = torch.exp(0.5 * self.bias_log_var)
            bias_eps = torch.randn_like(self.bias_mu)
            bias = self.bias_mu + bias_std * bias_eps
            
            # Calculate KL divergence
            self.kl_divergence = self._kl_divergence()
        else:
            # Use mean weights (no sampling)
            weight = self.weight_mu
            bias = self.bias_mu
            self.kl_divergence = 0
        
        return F.linear(x, weight, bias)
    
    def _kl_divergence(self):
        """Calculate KL divergence between posterior and prior"""
        # KL(q(w)||p(w)) for weights
        weight_var = torch.exp(self.weight_log_var)
        weight_kl = 0.5 * torch.sum(
            (self.weight_mu.pow(2) + weight_var) / (self.prior_std ** 2) - 
            1 - torch.log(weight_var / (self.prior_std ** 2))
        )
        
        # KL for biases
        bias_var = torch.exp(self.bias_log_var)
        bias_kl = 0.5 * torch.sum(
            (self.bias_mu.pow(2) + bias_var) / (self.prior_std ** 2) - 
            1 - torch.log(bias_var / (self.prior_std ** 2))
        )
        
        return weight_kl + bias_kl

class MCDropoutLayer(nn.Module):
    """Monte Carlo Dropout layer for uncertainty estimation"""
    
    def __init__(self, p: float = 0.5):
        super().__init__()
        self.p = p
    
    def forward(self, x):
        # Apply dropout even during evaluation for MC sampling
        return F.dropout(x, p=self.p, training=True)

class BayesianCVNet(nn.Module):
    """Bayesian neural network for CV analysis with uncertainty"""
    
    def __init__(self, n_features: int, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.n_features = n_features
        
        # Network architecture with Bayesian layers
        hidden_dims = config.get('hidden_dims', [128, 64, 32])
        dropout_rate = config.get('dropout_rate', 0.1)
        prior_std = config.get('prior_std', 0.1)
        
        # Build Bayesian network
        layers = []
        input_dim = n_features
        
        for hidden_dim in hidden_dims:
            layers.extend([
                BayesianLayer(input_dim, hidden_dim, prior_std),
                nn.ReLU(),
                MCDropoutLayer(dropout_rate)
            ])
            input_dim = hidden_dim
        
        # Output layers
        layers.append(BayesianLayer(input_dim, 1, prior_std))  # Peak probability
        
        self.network = nn.ModuleList(layers)
        
        # Additional output head for aleatoric uncertainty
        self.aleatoric_head = BayesianLayer(input_dim, 1, prior_std)
    
    def forward(self, x, sample: bool = True):
        kl_loss = 0
        
        for layer in self.network:
            if isinstance(layer, BayesianLayer):
                x = layer(x, sample=sample)
                kl_loss += layer.kl_divergence
            else:
                x = layer(x)
        
        # Peak probability
        peak_logits = x
        
        # Aleatoric uncertainty (log variance)
        aleatoric_log_var = self.aleatoric_head(x, sample=sample)
        kl_loss += self.aleatoric_head.kl_divergence
        
        return {
            'peak_logits': peak_logits,
            'aleatoric_log_var': aleatoric_log_var,
            'kl_loss': kl_loss
        }

class MonteCarloPredictor:
    """Monte Carlo methods for uncertainty estimation"""
    
    def __init__(self, model, n_samples: int = 100):
        self.model = model
        self.n_samples = n_samples
    
    def predict_with_uncertainty(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Make predictions with uncertainty using Monte Carlo sampling"""
        self.model.eval()  # But dropout still active due to MC dropout
        
        samples = []
        aleatoric_samples = []
        
        with torch.no_grad():
            for _ in range(self.n_samples):
                outputs = self.model(x, sample=True)
                
                # Get predictions
                peak_probs = torch.sigmoid(outputs['peak_logits'])
                aleatoric_var = torch.exp(outputs['aleatoric_log_var'])
                
                samples.append(peak_probs)
                aleatoric_samples.append(aleatoric_var)
        
        # Stack samples
        samples = torch.stack(samples, dim=0)  # (n_samples, batch, seq_len)
        aleatoric_samples = torch.stack(aleatoric_samples, dim=0)
        
        # Calculate statistics
        mean_prediction = torch.mean(samples, dim=0)
        epistemic_uncertainty = torch.var(samples, dim=0)
        aleatoric_uncertainty = torch.mean(aleatoric_samples, dim=0)
        total_uncertainty = epistemic_uncertainty + aleatoric_uncertainty
        
        return {
            'mean_prediction': mean_prediction,
            'epistemic_uncertainty': epistemic_uncertainty,
            'aleatoric_uncertainty': aleatoric_uncertainty,
            'total_uncertainty': total_uncertainty,
            'prediction_samples': samples
        }

class DeepEnsemble:
    """Deep ensemble for robust uncertainty estimation"""
    
    def __init__(self, model_class, n_models: int = 5):
        self.model_class = model_class
        self.n_models = n_models
        self.models = []
        self.trained = False
    
    def add_model(self, model):
        """Add a trained model to the ensemble"""
        self.models.append(model)
    
    def predict_ensemble(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Make ensemble predictions"""
        if not self.models:
            raise ValueError("No models in ensemble")
        
        predictions = []
        
        with torch.no_grad():
            for model in self.models:
                model.eval()
                outputs = model(x, sample=False)  # Use mean weights
                peak_probs = torch.sigmoid(outputs['peak_logits'])
                predictions.append(peak_probs)
        
        # Stack predictions
        predictions = torch.stack(predictions, dim=0)
        
        # Calculate ensemble statistics
        mean_prediction = torch.mean(predictions, dim=0)
        ensemble_uncertainty = torch.var(predictions, dim=0)
        
        return {
            'mean_prediction': mean_prediction,
            'ensemble_uncertainty': ensemble_uncertainty,
            'individual_predictions': predictions
        }

class UncertaintyQuantifier:
    """Main class for uncertainty quantification in CV peak detection"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Initialize components
        self.mc_predictor = None
        self.ensemble = None
        self.calibrated = False
        
        logger.info("🎲 Uncertainty Quantifier initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'mc_samples': 100,
            'ensemble_size': 5,
            'confidence_levels': [0.68, 0.95, 0.99],  # 1σ, 2σ, 3σ
            'calibration_method': 'platt',
            'uncertainty_threshold': 0.3,
            'bootstrap_samples': 1000
        }
    
    def setup_bayesian_model(self, n_features: int, model_config: Dict[str, Any]):
        """Setup Bayesian neural network model"""
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available - using basic uncertainty estimation")
            return False
        
        try:
            # Create Bayesian model
            model = BayesianCVNet(n_features, model_config).to(self.device)
            
            # Setup Monte Carlo predictor
            self.mc_predictor = MonteCarloPredictor(model, self.config['mc_samples'])
            
            logger.info(f"🧠 Bayesian model setup complete - Features: {n_features}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Bayesian model: {e}")
            return False
    
    def setup_ensemble(self, models: List):
        """Setup deep ensemble"""
        try:
            self.ensemble = DeepEnsemble(None, len(models))
            for model in models:
                self.ensemble.add_model(model)
            
            logger.info(f"🎯 Deep ensemble setup complete - Models: {len(models)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup ensemble: {e}")
            return False
    
    def estimate_uncertainty(self, features: np.ndarray, 
                           method: str = 'bayesian') -> UncertaintyEstimate:
        """Estimate uncertainty for given features"""
        
        if method == 'bayesian' and self.mc_predictor:
            return self._bayesian_uncertainty(features)
        elif method == 'ensemble' and self.ensemble:
            return self._ensemble_uncertainty(features)
        elif method == 'bootstrap':
            return self._bootstrap_uncertainty(features)
        else:
            return self._basic_uncertainty(features)
    
    def _bayesian_uncertainty(self, features: np.ndarray) -> UncertaintyEstimate:
        """Bayesian uncertainty estimation using Monte Carlo"""
        try:
            # Convert to tensor
            x = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(self.device)
            
            # Monte Carlo prediction
            mc_results = self.mc_predictor.predict_with_uncertainty(x)
            
            # Extract results
            mean_pred = mc_results['mean_prediction'].cpu().numpy().squeeze()
            epistemic_unc = mc_results['epistemic_uncertainty'].cpu().numpy().squeeze()
            aleatoric_unc = mc_results['aleatoric_uncertainty'].cpu().numpy().squeeze()
            total_unc = mc_results['total_uncertainty'].cpu().numpy().squeeze()
            samples = mc_results['prediction_samples'].cpu().numpy()
            
            # Calculate confidence intervals
            confidence_intervals = self._calculate_confidence_intervals(samples)
            
            return UncertaintyEstimate(
                mean_prediction=mean_pred,
                aleatoric_uncertainty=aleatoric_unc,
                epistemic_uncertainty=epistemic_unc,
                total_uncertainty=total_unc,
                confidence_intervals=confidence_intervals,
                prediction_samples=samples,
                metadata={
                    'method': 'bayesian',
                    'mc_samples': self.config['mc_samples'],
                    'device': str(self.device)
                }
            )
            
        except Exception as e:
            logger.error(f"Bayesian uncertainty estimation failed: {e}")
            return self._basic_uncertainty(features)
    
    def _ensemble_uncertainty(self, features: np.ndarray) -> UncertaintyEstimate:
        """Ensemble-based uncertainty estimation"""
        try:
            x = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(self.device)
            
            ensemble_results = self.ensemble.predict_ensemble(x)
            
            mean_pred = ensemble_results['mean_prediction'].cpu().numpy().squeeze()
            ensemble_unc = ensemble_results['ensemble_uncertainty'].cpu().numpy().squeeze()
            
            # For ensemble, epistemic = ensemble uncertainty, aleatoric = 0
            epistemic_unc = ensemble_unc
            aleatoric_unc = np.zeros_like(epistemic_unc)
            total_unc = ensemble_unc
            
            # Use individual predictions as samples
            samples = ensemble_results['individual_predictions'].cpu().numpy()
            confidence_intervals = self._calculate_confidence_intervals(samples)
            
            return UncertaintyEstimate(
                mean_prediction=mean_pred,
                aleatoric_uncertainty=aleatoric_unc,
                epistemic_uncertainty=epistemic_unc,
                total_uncertainty=total_unc,
                confidence_intervals=confidence_intervals,
                prediction_samples=samples,
                metadata={
                    'method': 'ensemble',
                    'n_models': len(self.ensemble.models)
                }
            )
            
        except Exception as e:
            logger.error(f"Ensemble uncertainty estimation failed: {e}")
            return self._basic_uncertainty(features)
    
    def _bootstrap_uncertainty(self, features: np.ndarray) -> UncertaintyEstimate:
        """Bootstrap uncertainty estimation"""
        # Simplified bootstrap without actual model retraining
        n_bootstrap = self.config.get('bootstrap_samples', 100)
        
        # Generate bootstrap samples by adding noise
        base_prediction = self._basic_prediction(features)
        noise_std = 0.1  # Assumed noise level
        
        bootstrap_samples = []
        for _ in range(n_bootstrap):
            noise = np.random.normal(0, noise_std, base_prediction.shape)
            sample = np.clip(base_prediction + noise, 0, 1)
            bootstrap_samples.append(sample)
        
        samples = np.array(bootstrap_samples)
        
        mean_pred = np.mean(samples, axis=0)
        bootstrap_unc = np.var(samples, axis=0)
        
        confidence_intervals = self._calculate_confidence_intervals(samples)
        
        return UncertaintyEstimate(
            mean_prediction=mean_pred,
            aleatoric_uncertainty=np.zeros_like(bootstrap_unc),
            epistemic_uncertainty=bootstrap_unc,
            total_uncertainty=bootstrap_unc,
            confidence_intervals=confidence_intervals,
            prediction_samples=samples,
            metadata={'method': 'bootstrap', 'n_samples': n_bootstrap}
        )
    
    def _basic_uncertainty(self, features: np.ndarray) -> UncertaintyEstimate:
        """Basic uncertainty estimation without advanced methods"""
        # Simple heuristic-based uncertainty
        prediction = self._basic_prediction(features)
        
        # Uncertainty based on prediction confidence (closer to 0.5 = higher uncertainty)
        uncertainty = 4 * prediction * (1 - prediction)  # Max at 0.5, min at 0 and 1
        
        return UncertaintyEstimate(
            mean_prediction=prediction,
            aleatoric_uncertainty=uncertainty * 0.3,
            epistemic_uncertainty=uncertainty * 0.7,
            total_uncertainty=uncertainty,
            confidence_intervals=self._basic_confidence_intervals(prediction, uncertainty),
            prediction_samples=None,
            metadata={'method': 'basic_heuristic'}
        )
    
    def _basic_prediction(self, features: np.ndarray) -> np.ndarray:
        """Basic prediction without neural networks"""
        # Simple heuristic: peaks are where features have high magnitude
        if features.ndim == 1:
            feature_magnitude = np.abs(features)
        else:
            feature_magnitude = np.linalg.norm(features, axis=1)
        
        # Normalize to [0, 1]
        if np.max(feature_magnitude) > np.min(feature_magnitude):
            normalized = (feature_magnitude - np.min(feature_magnitude)) / (np.max(feature_magnitude) - np.min(feature_magnitude))
        else:
            normalized = np.ones_like(feature_magnitude) * 0.5
        
        return normalized
    
    def _calculate_confidence_intervals(self, samples: np.ndarray) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """Calculate confidence intervals from samples"""
        confidence_intervals = {}
        
        for conf_level in self.config['confidence_levels']:
            alpha = 1 - conf_level
            lower_percentile = 100 * alpha / 2
            upper_percentile = 100 * (1 - alpha / 2)
            
            if SCIPY_AVAILABLE:
                lower_bound = np.percentile(samples, lower_percentile, axis=0)
                upper_bound = np.percentile(samples, upper_percentile, axis=0)
            else:
                # Basic percentile calculation
                sorted_samples = np.sort(samples, axis=0)
                n_samples = samples.shape[0]
                
                lower_idx = int(n_samples * lower_percentile / 100)
                upper_idx = int(n_samples * upper_percentile / 100)
                
                lower_bound = sorted_samples[lower_idx]
                upper_bound = sorted_samples[upper_idx]
            
            confidence_intervals[f'{conf_level:.2f}'] = (lower_bound, upper_bound)
        
        return confidence_intervals
    
    def _basic_confidence_intervals(self, prediction: np.ndarray, 
                                  uncertainty: np.ndarray) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """Basic confidence intervals using normal approximation"""
        confidence_intervals = {}
        
        for conf_level in self.config['confidence_levels']:
            if SCIPY_AVAILABLE:
                z_score = norm.ppf(1 - (1 - conf_level) / 2)
            else:
                # Approximate z-scores
                z_scores = {0.68: 1.0, 0.95: 1.96, 0.99: 2.58}
                z_score = z_scores.get(conf_level, 1.96)
            
            margin = z_score * np.sqrt(uncertainty)
            lower_bound = np.clip(prediction - margin, 0, 1)
            upper_bound = np.clip(prediction + margin, 0, 1)
            
            confidence_intervals[f'{conf_level:.2f}'] = (lower_bound, upper_bound)
        
        return confidence_intervals
    
    def uncertainty_aware_peak_detection(self, voltages: np.ndarray, 
                                       currents: np.ndarray,
                                       features: np.ndarray) -> Dict[str, Any]:
        """Peak detection with uncertainty quantification"""
        
        # Estimate uncertainty
        uncertainty_est = self.estimate_uncertainty(features)
        
        # Peak detection with uncertainty filtering
        mean_pred = uncertainty_est.mean_prediction
        total_unc = uncertainty_est.total_uncertainty
        
        # Threshold based on prediction confidence and uncertainty
        peak_threshold = 0.5
        uncertainty_threshold = self.config['uncertainty_threshold']
        
        # Find candidate peaks
        candidate_peaks = []
        for i in range(len(mean_pred)):
            if (mean_pred[i] > peak_threshold and 
                total_unc[i] < uncertainty_threshold):
                candidate_peaks.append(i)
        
        # Non-maximum suppression with uncertainty weighting
        final_peaks = self._uncertainty_weighted_nms(
            candidate_peaks, mean_pred, total_unc
        )
        
        # Calculate peak-specific uncertainties
        peak_uncertainties = {}
        for peak_idx in final_peaks:
            peak_uncertainties[peak_idx] = {
                'prediction': float(mean_pred[peak_idx]),
                'aleatoric': float(uncertainty_est.aleatoric_uncertainty[peak_idx]),
                'epistemic': float(uncertainty_est.epistemic_uncertainty[peak_idx]),
                'total': float(total_unc[peak_idx])
            }
        
        return {
            'peak_indices': final_peaks,
            'peak_potentials': [voltages[i] for i in final_peaks],
            'peak_currents': [currents[i] for i in final_peaks],
            'peak_uncertainties': peak_uncertainties,
            'uncertainty_estimate': uncertainty_est,
            'uncertainty_map': total_unc,
            'confidence_map': 1 - total_unc
        }
    
    def _uncertainty_weighted_nms(self, candidates: List[int], 
                                 predictions: np.ndarray,
                                 uncertainties: np.ndarray,
                                 min_distance: int = 10) -> List[int]:
        """Non-maximum suppression weighted by uncertainty"""
        if not candidates:
            return []
        
        # Sort by confidence (prediction / uncertainty)
        confidence_scores = predictions[candidates] / (uncertainties[candidates] + 1e-8)
        sorted_indices = sorted(candidates, key=lambda i: confidence_scores[candidates.index(i)], reverse=True)
        
        final_peaks = []
        
        for peak_idx in sorted_indices:
            # Check distance to already selected peaks
            if not final_peaks or all(abs(peak_idx - selected) >= min_distance 
                                    for selected in final_peaks):
                final_peaks.append(peak_idx)
        
        return sorted(final_peaks)

# Example usage and testing
if __name__ == "__main__":
    print("🎲 Uncertainty Quantification for CV Peak Detection")
    print("=" * 60)
    
    # Initialize uncertainty quantifier
    config = {
        'mc_samples': 50,  # Reduced for testing
        'confidence_levels': [0.68, 0.95],
        'uncertainty_threshold': 0.4
    }
    
    quantifier = UncertaintyQuantifier(config)
    
    # Generate synthetic data
    n_points = 200
    voltage = np.linspace(-1.0, 1.0, n_points)
    current = 0.1 * np.sin(3 * np.pi * voltage) + 0.02 * np.random.randn(n_points)
    
    # Add synthetic peaks
    peak_positions = [50, 100, 150]
    for pos in peak_positions:
        if pos < len(current):
            current[pos] += 0.3 * np.random.rand()
    
    print(f"📊 Test data: {n_points} points, {len(peak_positions)} synthetic peaks")
    
    # Create simple features
    features = np.column_stack([voltage, current, np.gradient(current)])
    
    # Test basic uncertainty estimation
    print("\n🎲 Testing uncertainty estimation...")
    uncertainty_est = quantifier.estimate_uncertainty(features, method='basic')
    
    print(f"✅ Uncertainty estimation completed:")
    print(f"   📊 Mean prediction range: [{np.min(uncertainty_est.mean_prediction):.3f}, {np.max(uncertainty_est.mean_prediction):.3f}]")
    print(f"   🎯 Total uncertainty range: [{np.min(uncertainty_est.total_uncertainty):.3f}, {np.max(uncertainty_est.total_uncertainty):.3f}]")
    print(f"   📈 Confidence intervals: {list(uncertainty_est.confidence_intervals.keys())}")
    
    # Test uncertainty-aware peak detection
    print("\n🔍 Testing uncertainty-aware peak detection...")
    peak_results = quantifier.uncertainty_aware_peak_detection(voltage, current, features)
    
    print(f"✅ Peak detection completed:")
    print(f"   🎯 Peaks detected: {len(peak_results['peak_indices'])}")
    print(f"   📍 Peak positions: {peak_results['peak_indices']}")
    
    # Show peak uncertainties
    if peak_results['peak_uncertainties']:
        print(f"   🎲 Peak uncertainties:")
        for peak_idx, unc_info in peak_results['peak_uncertainties'].items():
            print(f"      Peak {peak_idx}: pred={unc_info['prediction']:.3f}, unc={unc_info['total']:.3f}")
    
    # Calculate performance metrics
    detected_peaks = peak_results['peak_indices']
    tolerance = 15
    
    matches = 0
    for true_peak in peak_positions:
        for detected_peak in detected_peaks:
            if abs(true_peak - detected_peak) <= tolerance:
                matches += 1
                break
    
    accuracy = matches / len(peak_positions) if peak_positions else 0
    print(f"\n📈 Performance:")
    print(f"   🎯 Ground truth peaks: {len(peak_positions)}")
    print(f"   🔍 Detected peaks: {len(detected_peaks)}")
    print(f"   ✅ Matches (±{tolerance} tolerance): {matches}")
    print(f"   📊 Accuracy: {accuracy:.2%}")
    
    print("\n✅ Uncertainty Quantification test completed!")