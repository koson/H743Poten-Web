#!/usr/bin/env python3
"""
🔬 DeepCV V2 Multi-Scale & Multi-Modal Analysis
===============================================

Advanced multi-scale temporal analysis and multi-modal data fusion
for enhanced electrochemical peak detection.

Author: H743Poten Research Team
Date: October 4, 2025
Version: 2.0.0

Features:
- Multi-scale wavelet decomposition
- Multi-resolution time-frequency analysis
- Multi-modal data fusion (voltage + current + derivatives)
- Hierarchical feature pyramid networks
- Cross-scale attention mechanisms
- Adaptive temporal pooling
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass

# Scientific computing imports with fallbacks
try:
    import scipy.signal
    import scipy.fft
    from scipy.signal import cwt, ricker, morlet, find_peaks
    from scipy.signal.windows import hann, hamming, blackman
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("⚠️  SciPy not available - using basic implementations")

# Try PyTorch imports with fallbacks
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️  PyTorch not available - using basic implementations")

logger = logging.getLogger(__name__)

@dataclass
class MultiScaleFeatures:
    """Container for multi-scale feature representations"""
    scale_levels: List[int]
    features_by_scale: Dict[int, np.ndarray]
    attention_weights: Optional[np.ndarray]
    fusion_features: np.ndarray
    metadata: Dict[str, Any]

class WaveletMultiScaleAnalyzer:
    """Multi-scale wavelet analysis for CV signals"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scale_levels = config.get('scale_levels', [1, 2, 4, 8, 16])
        self.wavelet_type = config.get('wavelet_type', 'ricker')
        self.min_scale = config.get('min_scale', 1)
        self.max_scale = config.get('max_scale', 32)
    
    def decompose_signal(self, signal: np.ndarray) -> Dict[int, np.ndarray]:
        """Decompose signal into multiple scales using wavelets"""
        if not SCIPY_AVAILABLE:
            return self._basic_multi_scale_decomposition(signal)
        
        try:
            # Generate scale widths
            max_width = min(self.max_scale, len(signal) // 4)
            widths = np.logspace(
                np.log10(self.min_scale), 
                np.log10(max_width), 
                num=len(self.scale_levels)
            )
            
            # Perform continuous wavelet transform
            if self.wavelet_type == 'ricker':
                wavelet_matrix = cwt(signal, ricker, widths)
            elif self.wavelet_type == 'morlet':
                wavelet_matrix = cwt(signal, morlet, widths)
            else:
                # Fallback to Ricker
                wavelet_matrix = cwt(signal, ricker, widths)
            
            # Extract features at each scale
            scale_features = {}
            for i, scale in enumerate(self.scale_levels):
                if i < len(wavelet_matrix):
                    # Extract magnitude and phase information
                    magnitude = np.abs(wavelet_matrix[i])
                    phase = np.angle(wavelet_matrix[i]) if np.iscomplexobj(wavelet_matrix[i]) else np.zeros_like(magnitude)
                    
                    # Combine magnitude and phase features
                    scale_features[scale] = np.column_stack([magnitude, phase])
                else:
                    # Fallback for insufficient scales
                    scale_features[scale] = np.zeros((len(signal), 2))
            
            return scale_features
            
        except Exception as e:
            logger.warning(f"Wavelet decomposition failed: {e}")
            return self._basic_multi_scale_decomposition(signal)
    
    def _basic_multi_scale_decomposition(self, signal: np.ndarray) -> Dict[int, np.ndarray]:
        """Basic multi-scale decomposition without scipy"""
        scale_features = {}
        
        for scale in self.scale_levels:
            # Simple moving average at different scales
            window_size = min(scale, len(signal))
            if window_size > 1:
                # Moving average
                kernel = np.ones(window_size) / window_size
                smoothed = np.convolve(signal, kernel, mode='same')
                
                # Local variance
                variance = np.convolve((signal - smoothed)**2, kernel, mode='same')
                
                scale_features[scale] = np.column_stack([smoothed, variance])
            else:
                scale_features[scale] = np.column_stack([signal, np.zeros_like(signal)])
        
        return scale_features
    
    def extract_scale_specific_peaks(self, scale_features: Dict[int, np.ndarray]) -> Dict[int, List[int]]:
        """Extract peaks at each scale level"""
        peaks_by_scale = {}
        
        for scale, features in scale_features.items():
            magnitude = features[:, 0]
            
            if SCIPY_AVAILABLE:
                # Use scipy peak detection
                peaks, properties = find_peaks(
                    magnitude,
                    height=np.std(magnitude) * 0.5,
                    distance=max(1, scale // 2),
                    prominence=np.std(magnitude) * 0.3
                )
                peaks_by_scale[scale] = peaks.tolist()
            else:
                # Basic peak detection
                peaks = []
                threshold = np.mean(magnitude) + np.std(magnitude)
                
                for i in range(1, len(magnitude) - 1):
                    if (magnitude[i] > magnitude[i-1] and 
                        magnitude[i] > magnitude[i+1] and 
                        magnitude[i] > threshold):
                        peaks.append(i)
                
                peaks_by_scale[scale] = peaks
        
        return peaks_by_scale

class TimeFrequencyAnalyzer:
    """Time-frequency analysis for electrochemical signals"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.window_size = config.get('stft_window_size', 64)
        self.overlap = config.get('stft_overlap', 0.5)
        self.n_fft = config.get('n_fft', 128)
    
    def compute_spectrogram(self, signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute Short-Time Fourier Transform spectrogram"""
        if not SCIPY_AVAILABLE:
            return self._basic_spectrogram(signal)
        
        try:
            # Compute STFT
            frequencies, times, stft_matrix = scipy.signal.stft(
                signal,
                window='hann',
                nperseg=self.window_size,
                noverlap=int(self.window_size * self.overlap),
                nfft=self.n_fft
            )
            
            spectrogram = np.abs(stft_matrix)
            return frequencies, times, spectrogram
            
        except Exception as e:
            logger.warning(f"STFT computation failed: {e}")
            return self._basic_spectrogram(signal)
    
    def _basic_spectrogram(self, signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Basic spectrogram computation without scipy"""
        # Simple windowed FFT approach
        hop_length = self.window_size // 2
        n_frames = (len(signal) - self.window_size) // hop_length + 1
        
        # Create time and frequency axes
        times = np.arange(n_frames) * hop_length
        frequencies = np.linspace(0, 0.5, self.n_fft // 2 + 1)  # Normalized frequency
        
        # Compute spectrogram
        spectrogram = np.zeros((len(frequencies), n_frames))
        
        for frame_idx in range(n_frames):
            start = frame_idx * hop_length
            end = start + self.window_size
            
            if end <= len(signal):
                # Apply window and FFT
                windowed_signal = signal[start:end] * np.hanning(self.window_size)
                fft_result = np.fft.fft(windowed_signal, n=self.n_fft)
                spectrogram[:, frame_idx] = np.abs(fft_result[:self.n_fft // 2 + 1])
        
        return frequencies, times, spectrogram
    
    def extract_spectral_features(self, spectrogram: np.ndarray) -> np.ndarray:
        """Extract features from spectrogram"""
        features = []
        
        # Spectral centroid (frequency center of mass)
        frequencies = np.arange(spectrogram.shape[0])
        spectral_centroid = np.sum(frequencies[:, np.newaxis] * spectrogram, axis=0) / (np.sum(spectrogram, axis=0) + 1e-12)
        features.append(spectral_centroid)
        
        # Spectral bandwidth
        freq_diff = frequencies[:, np.newaxis] - spectral_centroid[np.newaxis, :]
        spectral_bandwidth = np.sqrt(np.sum((freq_diff**2) * spectrogram, axis=0) / (np.sum(spectrogram, axis=0) + 1e-12))
        features.append(spectral_bandwidth)
        
        # Spectral rolloff (frequency below which 85% of energy is contained)
        cumulative_energy = np.cumsum(spectrogram, axis=0)
        total_energy = np.sum(spectrogram, axis=0)
        rolloff_threshold = 0.85 * total_energy
        
        spectral_rolloff = np.zeros(spectrogram.shape[1])
        for t in range(spectrogram.shape[1]):
            rolloff_idx = np.where(cumulative_energy[:, t] >= rolloff_threshold[t])[0]
            spectral_rolloff[t] = rolloff_idx[0] if len(rolloff_idx) > 0 else 0
        
        features.append(spectral_rolloff)
        
        # Zero crossing rate approximation from spectral data
        spectral_flatness = np.exp(np.mean(np.log(spectrogram + 1e-12), axis=0)) / (np.mean(spectrogram, axis=0) + 1e-12)
        features.append(spectral_flatness)
        
        return np.array(features)

class MultiModalDataFusion:
    """Fuse multiple modalities of electrochemical data"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.fusion_method = config.get('fusion_method', 'concatenation')
        self.modal_weights = config.get('modal_weights', {'voltage': 0.3, 'current': 0.4, 'derived': 0.3})
    
    def fuse_modalities(self, voltage_features: np.ndarray, 
                       current_features: np.ndarray,
                       derived_features: np.ndarray) -> np.ndarray:
        """Fuse multiple modalities into unified representation"""
        
        if self.fusion_method == 'concatenation':
            return self._concatenation_fusion(voltage_features, current_features, derived_features)
        elif self.fusion_method == 'weighted_sum':
            return self._weighted_sum_fusion(voltage_features, current_features, derived_features)
        elif self.fusion_method == 'attention':
            return self._attention_fusion(voltage_features, current_features, derived_features)
        else:
            # Default to concatenation
            return self._concatenation_fusion(voltage_features, current_features, derived_features)
    
    def _concatenation_fusion(self, v_features: np.ndarray, 
                             i_features: np.ndarray, 
                             d_features: np.ndarray) -> np.ndarray:
        """Simple concatenation fusion"""
        # Ensure all features have same length
        min_length = min(len(v_features), len(i_features), len(d_features))
        
        v_features = v_features[:min_length]
        i_features = i_features[:min_length]
        d_features = d_features[:min_length]
        
        # Handle different dimensionalities
        if v_features.ndim == 1:
            v_features = v_features[:, np.newaxis]
        if i_features.ndim == 1:
            i_features = i_features[:, np.newaxis]
        if d_features.ndim == 1:
            d_features = d_features[:, np.newaxis]
        
        return np.concatenate([v_features, i_features, d_features], axis=1)
    
    def _weighted_sum_fusion(self, v_features: np.ndarray, 
                            i_features: np.ndarray, 
                            d_features: np.ndarray) -> np.ndarray:
        """Weighted sum fusion"""
        # Normalize features to same scale
        v_norm = (v_features - np.mean(v_features)) / (np.std(v_features) + 1e-12)
        i_norm = (i_features - np.mean(i_features)) / (np.std(i_features) + 1e-12)
        d_norm = (d_features - np.mean(d_features)) / (np.std(d_features) + 1e-12)
        
        # Apply weights
        w_v = self.modal_weights.get('voltage', 1/3)
        w_i = self.modal_weights.get('current', 1/3)
        w_d = self.modal_weights.get('derived', 1/3)
        
        # Ensure features can be broadcast together
        min_length = min(len(v_norm), len(i_norm), len(d_norm))
        v_norm = v_norm[:min_length]
        i_norm = i_norm[:min_length]
        d_norm = d_norm[:min_length]
        
        if v_norm.ndim > 1:
            v_norm = np.mean(v_norm, axis=1)
        if i_norm.ndim > 1:
            i_norm = np.mean(i_norm, axis=1)
        if d_norm.ndim > 1:
            d_norm = np.mean(d_norm, axis=1)
        
        fused = w_v * v_norm + w_i * i_norm + w_d * d_norm
        return fused[:, np.newaxis]
    
    def _attention_fusion(self, v_features: np.ndarray, 
                         i_features: np.ndarray, 
                         d_features: np.ndarray) -> np.ndarray:
        """Simple attention-based fusion (without neural networks)"""
        # Calculate attention weights based on variance
        v_var = np.var(v_features, axis=0) if v_features.ndim > 1 else np.var(v_features)
        i_var = np.var(i_features, axis=0) if i_features.ndim > 1 else np.var(i_features)
        d_var = np.var(d_features, axis=0) if d_features.ndim > 1 else np.var(d_features)
        
        # Normalize attention weights
        total_var = v_var + i_var + d_var + 1e-12
        att_v = v_var / total_var
        att_i = i_var / total_var
        att_d = d_var / total_var
        
        # Apply attention weights
        min_length = min(len(v_features), len(i_features), len(d_features))
        
        if v_features.ndim > 1:
            v_weighted = att_v * np.mean(v_features[:min_length], axis=1)
        else:
            v_weighted = att_v * v_features[:min_length]
            
        if i_features.ndim > 1:
            i_weighted = att_i * np.mean(i_features[:min_length], axis=1)
        else:
            i_weighted = att_i * i_features[:min_length]
            
        if d_features.ndim > 1:
            d_weighted = att_d * np.mean(d_features[:min_length], axis=1)
        else:
            d_weighted = att_d * d_features[:min_length]
        
        fused = v_weighted + i_weighted + d_weighted
        return fused[:, np.newaxis]

class HierarchicalFeaturePyramid:
    """Hierarchical feature pyramid for multi-scale analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pyramid_levels = config.get('pyramid_levels', [1, 2, 4, 8])
        self.pooling_method = config.get('pooling_method', 'average')
    
    def build_pyramid(self, features: np.ndarray) -> Dict[int, np.ndarray]:
        """Build feature pyramid at multiple scales"""
        pyramid = {}
        
        for level in self.pyramid_levels:
            if level == 1:
                # Original resolution
                pyramid[level] = features
            else:
                # Downsample features
                pyramid[level] = self._downsample_features(features, level)
        
        return pyramid
    
    def _downsample_features(self, features: np.ndarray, factor: int) -> np.ndarray:
        """Downsample features by given factor"""
        if len(features) < factor:
            return features
        
        if self.pooling_method == 'average':
            # Average pooling
            n_samples = len(features) // factor
            downsampled = np.zeros((n_samples, features.shape[1] if features.ndim > 1 else 1))
            
            for i in range(n_samples):
                start_idx = i * factor
                end_idx = min((i + 1) * factor, len(features))
                
                if features.ndim > 1:
                    downsampled[i] = np.mean(features[start_idx:end_idx], axis=0)
                else:
                    downsampled[i, 0] = np.mean(features[start_idx:end_idx])
            
            return downsampled
            
        elif self.pooling_method == 'max':
            # Max pooling
            n_samples = len(features) // factor
            downsampled = np.zeros((n_samples, features.shape[1] if features.ndim > 1 else 1))
            
            for i in range(n_samples):
                start_idx = i * factor
                end_idx = min((i + 1) * factor, len(features))
                
                if features.ndim > 1:
                    downsampled[i] = np.max(features[start_idx:end_idx], axis=0)
                else:
                    downsampled[i, 0] = np.max(features[start_idx:end_idx])
            
            return downsampled
        
        else:
            # Decimation (take every nth sample)
            return features[::factor]
    
    def fuse_pyramid_levels(self, pyramid: Dict[int, np.ndarray]) -> np.ndarray:
        """Fuse multiple pyramid levels into single representation"""
        # Find common length (use smallest)
        min_length = min(len(pyramid[level]) for level in pyramid.keys())
        
        fused_features = []
        
        for level in sorted(pyramid.keys()):
            level_features = pyramid[level][:min_length]
            
            # Ensure consistent dimensionality
            if level_features.ndim == 1:
                level_features = level_features[:, np.newaxis]
            
            # Weight by level (higher levels get less weight)
            weight = 1.0 / level
            weighted_features = weight * level_features
            
            fused_features.append(weighted_features)
        
        # Concatenate all weighted features
        return np.concatenate(fused_features, axis=1)

class MultiScaleMultiModalAnalyzer:
    """Main analyzer combining all multi-scale and multi-modal techniques"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()
        
        # Initialize sub-analyzers
        self.wavelet_analyzer = WaveletMultiScaleAnalyzer(self.config)
        self.tf_analyzer = TimeFrequencyAnalyzer(self.config)
        self.fusion_analyzer = MultiModalDataFusion(self.config)
        self.pyramid_analyzer = HierarchicalFeaturePyramid(self.config)
        
        logger.info("🔬 Multi-Scale Multi-Modal Analyzer initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'scale_levels': [1, 2, 4, 8, 16],
            'wavelet_type': 'ricker',
            'min_scale': 1,
            'max_scale': 32,
            'stft_window_size': 64,
            'stft_overlap': 0.5,
            'n_fft': 128,
            'fusion_method': 'concatenation',
            'modal_weights': {'voltage': 0.3, 'current': 0.4, 'derived': 0.3},
            'pyramid_levels': [1, 2, 4, 8],
            'pooling_method': 'average'
        }
    
    def extract_comprehensive_features(self, voltages: np.ndarray, 
                                     currents: np.ndarray) -> MultiScaleFeatures:
        """Extract comprehensive multi-scale multi-modal features"""
        
        try:
            # 1. Multi-scale wavelet decomposition
            voltage_scales = self.wavelet_analyzer.decompose_signal(voltages)
            current_scales = self.wavelet_analyzer.decompose_signal(currents)
            
            # 2. Time-frequency analysis
            v_freqs, v_times, v_spectrogram = self.tf_analyzer.compute_spectrogram(voltages)
            i_freqs, i_times, i_spectrogram = self.tf_analyzer.compute_spectrogram(currents)
            
            # Extract spectral features
            v_spectral_features = self.tf_analyzer.extract_spectral_features(v_spectrogram)
            i_spectral_features = self.tf_analyzer.extract_spectral_features(i_spectrogram)
            
            # 3. Derived features
            v_derivative = np.gradient(voltages)
            i_derivative = np.gradient(currents)
            
            # Combine derivatives into derived modality
            derived_features = np.column_stack([v_derivative, i_derivative])
            
            # 4. Multi-modal fusion at each scale
            features_by_scale = {}
            
            for scale in self.config['scale_levels']:
                if scale in voltage_scales and scale in current_scales:
                    # Get features for this scale
                    v_scale_features = voltage_scales[scale]
                    i_scale_features = current_scales[scale]
                    
                    # Ensure minimum length for derived features
                    min_len = min(len(v_scale_features), len(i_scale_features), len(derived_features))
                    
                    # Fuse modalities
                    fused_features = self.fusion_analyzer.fuse_modalities(
                        v_scale_features[:min_len],
                        i_scale_features[:min_len], 
                        derived_features[:min_len]
                    )
                    
                    features_by_scale[scale] = fused_features
            
            # 5. Build hierarchical feature pyramid
            # Use the finest scale as base for pyramid
            base_features = features_by_scale.get(1, np.column_stack([voltages, currents]))
            pyramid = self.pyramid_analyzer.build_pyramid(base_features)
            
            # 6. Final feature fusion
            pyramid_features = self.pyramid_analyzer.fuse_pyramid_levels(pyramid)
            
            # Add spectral features
            min_spectral_len = min(len(v_spectral_features.T), len(i_spectral_features.T), len(pyramid_features))
            
            spectral_combined = np.concatenate([
                v_spectral_features.T[:min_spectral_len],
                i_spectral_features.T[:min_spectral_len]
            ], axis=1)
            
            # Final concatenation
            final_features = np.concatenate([
                pyramid_features[:min_spectral_len],
                spectral_combined
            ], axis=1)
            
            # 7. Calculate attention weights (simplified)
            attention_weights = self._calculate_attention_weights(final_features)
            
            return MultiScaleFeatures(
                scale_levels=self.config['scale_levels'],
                features_by_scale=features_by_scale,
                attention_weights=attention_weights,
                fusion_features=final_features,
                metadata={
                    'original_length': len(voltages),
                    'final_feature_dim': final_features.shape[1],
                    'scales_used': list(features_by_scale.keys()),
                    'fusion_method': self.config['fusion_method'],
                    'spectral_features_dim': spectral_combined.shape[1]
                }
            )
            
        except Exception as e:
            logger.error(f"Multi-scale multi-modal analysis failed: {e}")
            # Return basic features as fallback
            basic_features = np.column_stack([voltages, currents])
            return MultiScaleFeatures(
                scale_levels=[1],
                features_by_scale={1: basic_features},
                attention_weights=None,
                fusion_features=basic_features,
                metadata={'error': str(e), 'fallback': True}
            )
    
    def _calculate_attention_weights(self, features: np.ndarray) -> np.ndarray:
        """Calculate attention weights for temporal positions"""
        if features.ndim == 1:
            return np.ones(len(features)) / len(features)
        
        # Calculate importance based on feature magnitude
        feature_magnitudes = np.linalg.norm(features, axis=1)
        
        # Softmax normalization
        exp_magnitudes = np.exp(feature_magnitudes - np.max(feature_magnitudes))
        attention_weights = exp_magnitudes / np.sum(exp_magnitudes)
        
        return attention_weights
    
    def detect_multi_scale_peaks(self, voltages: np.ndarray, 
                                currents: np.ndarray) -> Dict[str, Any]:
        """Detect peaks using multi-scale analysis"""
        
        # Extract comprehensive features
        ms_features = self.extract_comprehensive_features(voltages, currents)
        
        # Detect peaks at each scale
        voltage_peaks_by_scale = self.wavelet_analyzer.extract_scale_specific_peaks(
            {scale: features[:, :features.shape[1]//3] for scale, features in ms_features.features_by_scale.items()}
        )
        
        current_peaks_by_scale = self.wavelet_analyzer.extract_scale_specific_peaks(
            {scale: features[:, features.shape[1]//3:2*features.shape[1]//3] for scale, features in ms_features.features_by_scale.items()}
        )
        
        # Consensus peak detection across scales
        consensus_peaks = self._find_consensus_peaks(voltage_peaks_by_scale, current_peaks_by_scale)
        
        return {
            'consensus_peaks': consensus_peaks,
            'voltage_peaks_by_scale': voltage_peaks_by_scale,
            'current_peaks_by_scale': current_peaks_by_scale,
            'multi_scale_features': ms_features,
            'attention_weights': ms_features.attention_weights
        }
    
    def _find_consensus_peaks(self, voltage_peaks: Dict[int, List[int]], 
                             current_peaks: Dict[int, List[int]]) -> List[int]:
        """Find consensus peaks across multiple scales"""
        all_peaks = []
        
        # Collect all peak positions with their scale weights
        peak_votes = {}
        
        for scale, v_peaks in voltage_peaks.items():
            weight = 1.0 / scale  # Higher weight for finer scales
            for peak in v_peaks:
                if peak not in peak_votes:
                    peak_votes[peak] = 0
                peak_votes[peak] += weight
        
        for scale, i_peaks in current_peaks.items():
            weight = 1.0 / scale
            for peak in i_peaks:
                if peak not in peak_votes:
                    peak_votes[peak] = 0
                peak_votes[peak] += weight
        
        # Select peaks with sufficient votes
        vote_threshold = np.mean(list(peak_votes.values())) if peak_votes else 0
        consensus_peaks = [peak for peak, votes in peak_votes.items() if votes >= vote_threshold]
        
        # Remove closely spaced peaks (non-maximum suppression)
        final_peaks = []
        min_distance = 5
        
        for peak in sorted(consensus_peaks):
            if not final_peaks or peak - final_peaks[-1] >= min_distance:
                final_peaks.append(peak)
        
        return final_peaks

# Example usage and testing
if __name__ == "__main__":
    print("🔬 Multi-Scale Multi-Modal Analysis for CV Peak Detection")
    print("=" * 60)
    
    # Initialize analyzer
    config = {
        'scale_levels': [1, 2, 4, 8],
        'wavelet_type': 'ricker',
        'fusion_method': 'concatenation'
    }
    
    analyzer = MultiScaleMultiModalAnalyzer(config)
    
    # Generate synthetic CV data
    n_points = 300
    voltage = np.linspace(-1.0, 1.0, n_points)
    
    # Create multi-component signal
    current = (0.1 * np.sin(3 * np.pi * voltage) + 
              0.05 * np.sin(7 * np.pi * voltage) +
              0.02 * np.random.randn(n_points))
    
    # Add synthetic peaks
    peak_positions = [75, 150, 225]
    for pos in peak_positions:
        if pos < len(current):
            current[pos] += 0.3 * (1 + 0.1 * np.random.randn())
    
    print(f"📊 Test data: {n_points} points, {len(peak_positions)} synthetic peaks")
    
    # Extract multi-scale features
    print("\n🔍 Extracting multi-scale multi-modal features...")
    ms_features = analyzer.extract_comprehensive_features(voltage, current)
    
    print(f"✅ Feature extraction completed:")
    print(f"   📏 Feature dimensions: {ms_features.fusion_features.shape}")
    print(f"   📊 Scales analyzed: {ms_features.scale_levels}")
    print(f"   🎯 Features per scale: {[f.shape for f in ms_features.features_by_scale.values()]}")
    
    # Multi-scale peak detection
    print("\n🎯 Performing multi-scale peak detection...")
    peak_results = analyzer.detect_multi_scale_peaks(voltage, current)
    
    print(f"✅ Peak detection completed:")
    print(f"   🎯 Consensus peaks found: {len(peak_results['consensus_peaks'])}")
    print(f"   📍 Peak positions: {peak_results['consensus_peaks']}")
    print(f"   📊 Peaks by scale: {peak_results['voltage_peaks_by_scale']}")
    
    # Compare with ground truth
    detected_peaks = peak_results['consensus_peaks']
    tolerance = 10  # Allow ±10 point tolerance
    
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
    
    print("\n✅ Multi-Scale Multi-Modal Analysis test completed!")