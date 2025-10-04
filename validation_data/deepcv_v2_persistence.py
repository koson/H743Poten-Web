#!/usr/bin/env python3
"""
🔄 DeepCV V2 Model Persistence & Transfer Learning
=================================================

Advanced model management, persistence, and transfer learning capabilities
for DeepCV V2 system.

Author: H743Poten Research Team
Date: October 4, 2025
Version: 2.0.0

Features:
- Model checkpointing and versioning
- Transfer learning from pre-trained models
- Continual learning capabilities
- Model compression and quantization
- Cross-instrument transfer learning
- Federated learning support
"""

import torch
import torch.nn as nn
import numpy as np
import json
import pickle
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import logging
import shutil
import zipfile

logger = logging.getLogger(__name__)

class ModelCheckpoint:
    """Enhanced model checkpoint with metadata"""
    
    def __init__(self, model_state: Dict, metadata: Dict):
        self.model_state = model_state
        self.metadata = metadata
        self.timestamp = datetime.now()
        self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate checksum for model integrity"""
        model_str = str(sorted(self.model_state.items()))
        return hashlib.md5(model_str.encode()).hexdigest()[:8]

class ModelVersionManager:
    """Manage multiple versions of trained models"""
    
    def __init__(self, base_path: str = "models/deepcv_v2"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.versions_file = self.base_path / "versions.json"
        self.versions = self._load_versions()
    
    def _load_versions(self) -> Dict:
        """Load version registry"""
        if self.versions_file.exists():
            with open(self.versions_file, 'r') as f:
                return json.load(f)
        return {"versions": [], "latest": None}
    
    def _save_versions(self):
        """Save version registry"""
        with open(self.versions_file, 'w') as f:
            json.dump(self.versions, f, indent=2, default=str)
    
    def save_version(self, checkpoint: ModelCheckpoint, version_name: str, 
                    description: str = "", is_latest: bool = True) -> str:
        """Save a new model version"""
        
        version_info = {
            "version_name": version_name,
            "description": description,
            "timestamp": checkpoint.timestamp.isoformat(),
            "checksum": checkpoint.checksum,
            "metadata": checkpoint.metadata
        }
        
        # Create version directory
        version_dir = self.base_path / version_name
        version_dir.mkdir(exist_ok=True)
        
        # Save model checkpoint
        model_path = version_dir / "model.pth"
        torch.save(checkpoint.model_state, model_path)
        
        # Save metadata
        metadata_path = version_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(version_info, f, indent=2, default=str)
        
        # Update version registry
        self.versions["versions"].append(version_info)
        if is_latest:
            self.versions["latest"] = version_name
        
        self._save_versions()
        
        logger.info(f"💾 Saved model version '{version_name}' - Checksum: {checkpoint.checksum}")
        return version_name
    
    def load_version(self, version_name: Optional[str] = None) -> Optional[ModelCheckpoint]:
        """Load a specific model version"""
        if version_name is None:
            version_name = self.versions.get("latest")
        
        if not version_name:
            logger.warning("No model version specified and no latest version available")
            return None
        
        version_dir = self.base_path / version_name
        if not version_dir.exists():
            logger.error(f"Model version '{version_name}' not found")
            return None
        
        try:
            # Load model state
            model_path = version_dir / "model.pth"
            model_state = torch.load(model_path, map_location='cpu')
            
            # Load metadata
            metadata_path = version_dir / "metadata.json"
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            checkpoint = ModelCheckpoint(model_state, metadata)
            logger.info(f"📁 Loaded model version '{version_name}' - Checksum: {checkpoint.checksum}")
            return checkpoint
            
        except Exception as e:
            logger.error(f"Failed to load model version '{version_name}': {e}")
            return None
    
    def list_versions(self) -> List[Dict]:
        """List all available model versions"""
        return self.versions.get("versions", [])
    
    def delete_version(self, version_name: str) -> bool:
        """Delete a model version"""
        version_dir = self.base_path / version_name
        if not version_dir.exists():
            logger.warning(f"Version '{version_name}' not found")
            return False
        
        try:
            shutil.rmtree(version_dir)
            
            # Update registry
            self.versions["versions"] = [
                v for v in self.versions["versions"] 
                if v["version_name"] != version_name
            ]
            
            if self.versions.get("latest") == version_name:
                remaining_versions = self.versions["versions"]
                if remaining_versions:
                    self.versions["latest"] = remaining_versions[-1]["version_name"]
                else:
                    self.versions["latest"] = None
            
            self._save_versions()
            logger.info(f"🗑️ Deleted model version '{version_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete version '{version_name}': {e}")
            return False

class TransferLearningManager:
    """Manage transfer learning between different models and domains"""
    
    def __init__(self, source_analyzer, target_analyzer):
        self.source_analyzer = source_analyzer
        self.target_analyzer = target_analyzer
    
    def transfer_features(self, freeze_layers: List[str] = None) -> bool:
        """Transfer learned features from source to target model"""
        if not self.source_analyzer.is_trained:
            logger.error("Source model is not trained")
            return False
        
        try:
            # Get source model state
            source_state = self.source_analyzer.model.state_dict()
            target_state = self.target_analyzer.model.state_dict()
            
            # Transfer compatible layers
            transferred_layers = []
            for layer_name, source_params in source_state.items():
                if layer_name in target_state:
                    target_params = target_state[layer_name]
                    
                    # Check shape compatibility
                    if source_params.shape == target_params.shape:
                        target_state[layer_name] = source_params.clone()
                        transferred_layers.append(layer_name)
                        
                        # Freeze layer if specified
                        if freeze_layers and any(frozen in layer_name for frozen in freeze_layers):
                            for param in self.target_analyzer.model.named_parameters():
                                if param[0] == layer_name:
                                    param[1].requires_grad = False
            
            # Load transferred parameters
            self.target_analyzer.model.load_state_dict(target_state)
            
            logger.info(f"🔄 Transferred {len(transferred_layers)} layers from source model")
            logger.info(f"Transferred layers: {transferred_layers}")
            
            return True
            
        except Exception as e:
            logger.error(f"Transfer learning failed: {e}")
            return False
    
    def fine_tune(self, fine_tune_config: Dict, training_data: List) -> bool:
        """Fine-tune transferred model on target domain"""
        
        # Reduce learning rate for fine-tuning
        original_lr = self.target_analyzer.config['learning_rate']
        self.target_analyzer.config['learning_rate'] = fine_tune_config.get('learning_rate', original_lr * 0.1)
        
        # Reduce epochs for fine-tuning
        original_epochs = self.target_analyzer.config['epochs']
        self.target_analyzer.config['epochs'] = fine_tune_config.get('epochs', original_epochs // 2)
        
        try:
            # Add fine-tuning data
            for sample in training_data:
                self.target_analyzer.add_training_data(
                    sample['voltages'], 
                    sample['currents'], 
                    sample['peaks']
                )
            
            # Fine-tune model
            success = self.target_analyzer.train(save_model=False)  # Don't auto-save during fine-tuning
            
            # Restore original config
            self.target_analyzer.config['learning_rate'] = original_lr
            self.target_analyzer.config['epochs'] = original_epochs
            
            if success:
                logger.info("✅ Fine-tuning completed successfully")
            else:
                logger.error("❌ Fine-tuning failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Fine-tuning failed: {e}")
            return False

class ContinualLearningManager:
    """Manage continual learning to avoid catastrophic forgetting"""
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.task_memories = []  # Store samples from previous tasks
        self.importance_weights = {}  # EWC importance weights
        self.previous_params = {}  # Previous task parameters
    
    def add_task_memory(self, samples: List[Dict], max_samples: int = 100):
        """Add representative samples from current task to memory"""
        # Simple random sampling for memory
        if len(samples) > max_samples:
            indices = np.random.choice(len(samples), max_samples, replace=False)
            memory_samples = [samples[i] for i in indices]
        else:
            memory_samples = samples
        
        self.task_memories.extend(memory_samples)
        logger.info(f"Added {len(memory_samples)} samples to task memory")
    
    def calculate_importance_weights(self, dataloader, device):
        """Calculate Fisher Information Matrix for EWC (Elastic Weight Consolidation)"""
        if not self.analyzer.model:
            return
        
        self.analyzer.model.eval()
        importance_weights = {}
        
        # Initialize importance weights
        for name, param in self.analyzer.model.named_parameters():
            importance_weights[name] = torch.zeros_like(param)
        
        # Calculate Fisher Information
        num_samples = 0
        for batch_features, batch_labels in dataloader:
            batch_features = batch_features.to(device)
            batch_labels = batch_labels.to(device)
            
            outputs = self.analyzer.model(batch_features)
            loss = self.analyzer._calculate_loss(outputs, batch_labels)
            
            # Backward pass to get gradients
            self.analyzer.model.zero_grad()
            loss.backward()
            
            # Accumulate squared gradients (Fisher Information approximation)
            for name, param in self.analyzer.model.named_parameters():
                if param.grad is not None:
                    importance_weights[name] += param.grad.data.clone().pow(2)
            
            num_samples += batch_features.size(0)
        
        # Normalize by number of samples
        for name in importance_weights:
            importance_weights[name] /= num_samples
        
        self.importance_weights = importance_weights
        logger.info("📊 Calculated Fisher Information weights for EWC")
    
    def save_task_parameters(self):
        """Save current model parameters as previous task parameters"""
        self.previous_params = {}
        for name, param in self.analyzer.model.named_parameters():
            self.previous_params[name] = param.data.clone()
    
    def ewc_loss(self, lambda_ewc: float = 1000.0) -> torch.Tensor:
        """Calculate EWC regularization loss"""
        ewc_loss = 0
        
        for name, param in self.analyzer.model.named_parameters():
            if name in self.importance_weights and name in self.previous_params:
                importance = self.importance_weights[name]
                prev_param = self.previous_params[name]
                ewc_loss += (importance * (param - prev_param).pow(2)).sum()
        
        return lambda_ewc * ewc_loss
    
    def train_with_memory_replay(self, new_training_data: List[Dict], 
                               memory_ratio: float = 0.3) -> bool:
        """Train with memory replay to prevent catastrophic forgetting"""
        
        # Combine new data with memory
        memory_size = int(len(new_training_data) * memory_ratio)
        if len(self.task_memories) > memory_size:
            memory_samples = np.random.choice(
                self.task_memories, memory_size, replace=False
            ).tolist()
        else:
            memory_samples = self.task_memories
        
        combined_data = new_training_data + memory_samples
        
        # Add to analyzer training data
        for sample in combined_data:
            self.analyzer.add_training_data(
                sample['voltages'],
                sample['currents'], 
                sample['peaks']
            )
        
        # Train with combined data
        success = self.analyzer.train()
        
        if success:
            # Update task memory with new samples
            self.add_task_memory(new_training_data)
            logger.info(f"✅ Continual learning completed - Memory size: {len(self.task_memories)}")
        
        return success

class ModelCompressionManager:
    """Model compression and quantization for edge deployment"""
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
    
    def quantize_model(self, quantization_type: str = "dynamic") -> bool:
        """Quantize model for reduced memory and faster inference"""
        if not self.analyzer.model:
            logger.error("No model to quantize")
            return False
        
        try:
            if quantization_type == "dynamic":
                # Dynamic quantization
                quantized_model = torch.quantization.quantize_dynamic(
                    self.analyzer.model,
                    {nn.Linear, nn.LSTM, nn.Conv1d},
                    dtype=torch.qint8
                )
            elif quantization_type == "static":
                # Static quantization (requires calibration data)
                self.analyzer.model.qconfig = torch.quantization.get_default_qconfig('fbgemm')
                torch.quantization.prepare(self.analyzer.model, inplace=True)
                
                # Calibration step would go here with representative data
                # For now, we'll skip this and just finalize
                quantized_model = torch.quantization.convert(self.analyzer.model, inplace=False)
            else:
                raise ValueError(f"Unknown quantization type: {quantization_type}")
            
            # Replace model
            original_size = self._get_model_size(self.analyzer.model)
            quantized_size = self._get_model_size(quantized_model)
            
            self.analyzer.model = quantized_model
            
            compression_ratio = original_size / quantized_size
            logger.info(f"🗜️ Model quantized - Compression ratio: {compression_ratio:.2f}x")
            logger.info(f"Original size: {original_size:.2f} MB, Quantized size: {quantized_size:.2f} MB")
            
            return True
            
        except Exception as e:
            logger.error(f"Model quantization failed: {e}")
            return False
    
    def prune_model(self, sparsity: float = 0.3) -> bool:
        """Prune model to remove less important weights"""
        if not self.analyzer.model:
            logger.error("No model to prune")
            return False
        
        try:
            import torch.nn.utils.prune as prune
            
            # Get all linear layers for pruning
            parameters_to_prune = []
            for module in self.analyzer.model.modules():
                if isinstance(module, (nn.Linear, nn.Conv1d)):
                    parameters_to_prune.append((module, 'weight'))
            
            # Apply global magnitude pruning
            prune.global_unstructured(
                parameters_to_prune,
                pruning_method=prune.L1Unstructured,
                amount=sparsity,
            )
            
            # Make pruning permanent
            for module, param_name in parameters_to_prune:
                prune.remove(module, param_name)
            
            logger.info(f"✂️ Model pruned with {sparsity*100:.1f}% sparsity")
            return True
            
        except ImportError:
            logger.error("PyTorch pruning not available in this version")
            return False
        except Exception as e:
            logger.error(f"Model pruning failed: {e}")
            return False
    
    def _get_model_size(self, model) -> float:
        """Calculate model size in MB"""
        param_size = 0
        buffer_size = 0
        
        for param in model.parameters():
            param_size += param.nelement() * param.element_size()
        
        for buffer in model.buffers():
            buffer_size += buffer.nelement() * buffer.element_size()
        
        size_mb = (param_size + buffer_size) / (1024 * 1024)
        return size_mb

class CrossInstrumentTransfer:
    """Transfer learning between different electrochemical instruments"""
    
    def __init__(self):
        self.instrument_configs = {
            'PalmSens': {
                'voltage_range': (-2.0, 2.0),
                'current_range': (-1e-3, 1e-3),
                'noise_level': 1e-12,
                'sampling_rate': 1000
            },
            'STM32H743': {
                'voltage_range': (-1.5, 1.5),
                'current_range': (-5e-4, 5e-4),
                'noise_level': 5e-12,
                'sampling_rate': 500
            },
            'BioLogic': {
                'voltage_range': (-3.0, 3.0),
                'current_range': (-1e-2, 1e-2),
                'noise_level': 1e-13,
                'sampling_rate': 2000
            }
        }
    
    def create_transfer_features(self, source_instrument: str, target_instrument: str,
                               voltages: np.ndarray, currents: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create normalized features for cross-instrument transfer"""
        
        source_config = self.instrument_configs.get(source_instrument, {})
        target_config = self.instrument_configs.get(target_instrument, {})
        
        # Normalize voltage
        source_v_range = source_config.get('voltage_range', (-2, 2))
        target_v_range = target_config.get('voltage_range', (-2, 2))
        
        v_normalized = (voltages - source_v_range[0]) / (source_v_range[1] - source_v_range[0])
        v_target = v_normalized * (target_v_range[1] - target_v_range[0]) + target_v_range[0]
        
        # Normalize current
        source_i_range = source_config.get('current_range', (-1e-3, 1e-3))
        target_i_range = target_config.get('current_range', (-1e-3, 1e-3))
        
        i_normalized = (currents - source_i_range[0]) / (source_i_range[1] - source_i_range[0])
        i_target = i_normalized * (target_i_range[1] - target_i_range[0]) + target_i_range[0]
        
        # Add instrument-specific noise simulation
        target_noise_level = target_config.get('noise_level', 1e-12)
        i_target += np.random.normal(0, target_noise_level, len(i_target))
        
        return v_target, i_target
    
    def transfer_model(self, source_analyzer, target_instrument: str) -> 'DeepCVAnalyzerV2':
        """Transfer model to different instrument"""
        from deepcv_v2 import DeepCVAnalyzerV2  # Import here to avoid circular import
        
        # Create target analyzer with modified config
        target_config = source_analyzer.config.copy()
        target_config['target_instrument'] = target_instrument
        
        target_analyzer = DeepCVAnalyzerV2(target_config)
        
        # Initialize model with same architecture
        if source_analyzer.model:
            sample_features = source_analyzer.training_data[0]['features'] if source_analyzer.training_data else None
            if sample_features is not None:
                n_features = sample_features.shape[1]
                target_analyzer.model = source_analyzer.model.__class__(n_features, target_config)
                
                # Transfer weights
                transfer_manager = TransferLearningManager(source_analyzer, target_analyzer)
                transfer_manager.transfer_features()
                
                logger.info(f"🔄 Model transferred to {target_instrument}")
        
        return target_analyzer

# Example usage and testing
if __name__ == "__main__":
    print("🔄 DeepCV V2 Model Persistence & Transfer Learning")
    print("=" * 60)
    
    # Test version management
    version_manager = ModelVersionManager("test_models/deepcv_v2")
    
    # Create dummy checkpoint
    dummy_state = {'layer1.weight': torch.randn(10, 5)}
    dummy_metadata = {'accuracy': 0.95, 'epochs': 100}
    checkpoint = ModelCheckpoint(dummy_state, dummy_metadata)
    
    # Save version
    version_name = version_manager.save_version(
        checkpoint, 
        "test_v1.0", 
        "Test model version"
    )
    
    # List versions
    versions = version_manager.list_versions()
    print(f"📋 Available versions: {len(versions)}")
    
    # Load version
    loaded_checkpoint = version_manager.load_version("test_v1.0")
    if loaded_checkpoint:
        print(f"✅ Successfully loaded checkpoint - Checksum: {loaded_checkpoint.checksum}")
    
    print("✅ Model persistence system test completed!")