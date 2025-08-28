#!/usr/bin/env python3
"""
Advanced PLS Analyzer for Electrochemical Data
==============================================

ระบบ PLS (Partial Least Squares) ที่ใช้ข้อมูล peak และ baseline ที่แม่นยำ
สำหรับการวิเคราะห์เชิงปริมาณและการทำนายความเข้มข้น

Features:
- Multi-feature PLS models (peak height, area, shape parameters)
- Cross-validation and model optimization
- Real-time concentration prediction
- Model quality assessment and validation
- Feature importance analysis
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Optional imports
try:
    from sklearn.cross_decomposition import PLSRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score, LeaveOneOut
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit-learn not available - using fallback algorithms")
    
    # Fallback implementations
    class PLSRegression:
        def __init__(self, n_components=2):
            self.n_components = n_components
            self.coef_ = None
            
        def fit(self, X, y):
            # Simple linear regression fallback
            self.coef_ = np.linalg.lstsq(X, y, rcond=None)[0]
            return self
            
        def predict(self, X):
            if self.coef_ is None:
                raise ValueError("Model not fitted")
            return X @ self.coef_
    
    class StandardScaler:
        def __init__(self):
            self.mean_ = None
            self.scale_ = None
            
        def fit_transform(self, X):
            self.mean_ = np.mean(X, axis=0)
            self.scale_ = np.std(X, axis=0)
            self.scale_[self.scale_ == 0] = 1  # Avoid division by zero
            return (X - self.mean_) / self.scale_
            
        def transform(self, X):
            if self.mean_ is None:
                raise ValueError("Scaler not fitted")
            return (X - self.mean_) / self.scale_
    
    def r2_score(y_true, y_pred):
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    def mean_squared_error(y_true, y_pred):
        return np.mean((y_true - y_pred) ** 2)
    
    def mean_absolute_error(y_true, y_pred):
        return np.mean(np.abs(y_true - y_pred))
    
    def cross_val_score(model, X, y, cv=5, scoring='r2'):
        # Simple cross-validation fallback
        n = len(X)
        fold_size = n // cv
        scores = []
        
        for i in range(cv):
            start = i * fold_size
            end = start + fold_size if i < cv - 1 else n
            
            # Create train/test split
            test_mask = np.zeros(n, dtype=bool)
            test_mask[start:end] = True
            train_mask = ~test_mask
            
            X_train, X_test = X[train_mask], X[test_mask]
            y_train, y_test = y[train_mask], y[test_mask]
            
            # Fit and predict
            temp_model = PLSRegression(n_components=model.n_components)
            temp_model.fit(X_train, y_train)
            y_pred = temp_model.predict(X_test)
            
            # Calculate score
            if scoring == 'r2':
                score = r2_score(y_test, y_pred)
            else:
                score = -mean_squared_error(y_test, y_pred)
            
            scores.append(score)
        
        return np.array(scores)
    
    class LeaveOneOut:
        def split(self, X):
            n = len(X)
            for i in range(n):
                train_idx = np.concatenate([np.arange(i), np.arange(i+1, n)])
                test_idx = np.array([i])
                yield train_idx, test_idx

try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
    # Don't set palette here as it might cause issues
except ImportError:
    SEABORN_AVAILABLE = False

# Import our precision analyzer
try:
    from precision_peak_baseline_analyzer import PrecisionPeakBaselineAnalyzer, PLSFeatures
    PRECISION_ANALYZER_AVAILABLE = True
except ImportError:
    PRECISION_ANALYZER_AVAILABLE = False
    logging.warning("Precision analyzer not available - using fallback mode")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PLSCalibrationPoint:
    """Single calibration point for PLS model"""
    concentration: float           # Known concentration (M)
    features: PLSFeatures         # Extracted electrochemical features
    filename: str                 # Source filename
    measurement_conditions: Dict  # pH, temperature, scan rate, etc.
    timestamp: datetime          # Measurement timestamp
    quality_score: float         # Overall data quality

@dataclass
class PLSModel:
    """Complete PLS model with metadata"""
    model: PLSRegression          # Trained sklearn PLS model
    scaler: StandardScaler        # Feature scaler
    feature_names: List[str]      # Names of features used
    calibration_points: List[PLSCalibrationPoint]  # Training data
    model_metrics: Dict[str, float]  # R², RMSE, etc.
    optimal_components: int       # Number of PLS components
    feature_importance: Dict[str, float]  # Feature importance scores
    created_timestamp: datetime   # Model creation time
    model_id: str                # Unique model identifier

@dataclass
class ConcentrationPrediction:
    """Result of concentration prediction"""
    predicted_concentration: float    # Predicted concentration (M)
    confidence_interval: Tuple[float, float]  # 95% confidence interval
    prediction_confidence: float     # Prediction confidence (0-100)
    features_used: PLSFeatures       # Features used for prediction
    model_id: str                    # Model used for prediction
    timestamp: datetime              # Prediction timestamp

class AdvancedPLSAnalyzer:
    """
    Advanced PLS analyzer using precision peak/baseline detection
    for accurate quantitative electrochemical analysis
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = self._get_default_config()
        if config:
            self.config.update(config)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize precision analyzer
        if PRECISION_ANALYZER_AVAILABLE:
            self.precision_analyzer = PrecisionPeakBaselineAnalyzer(
                config=self.config.get('precision_analyzer_config', {})
            )
        else:
            self.precision_analyzer = None
            self.logger.warning("Precision analyzer not available - limited functionality")
        
        # Model storage
        self.models: Dict[str, PLSModel] = {}
        self.calibration_data: List[PLSCalibrationPoint] = []
        
        # Analysis history
        self.prediction_history: List[ConcentrationPrediction] = []
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for PLS analysis"""
        return {
            'max_pls_components': 10,
            'cv_folds': 5,
            'quality_threshold': 80.0,
            'min_calibration_points': 5,
            'feature_selection_threshold': 0.1,
            'model_validation_method': 'cross_validation',
            'save_models': True,
            'model_directory': 'pls_models',
            'precision_analyzer_config': {
                'analyte': 'ferrocene',
                'confidence_threshold': 85.0,
                'quality_threshold': 80.0
            }
        }
    
    def add_calibration_point(self, voltage: np.ndarray, current: np.ndarray, 
                            concentration: float, filename: str = "",
                            conditions: Optional[Dict] = None) -> bool:
        """
        Add a calibration point by analyzing CV data
        
        Args:
            voltage: Voltage array (V)
            current: Current array (μA)
            concentration: Known concentration (M)
            filename: Source filename
            conditions: Measurement conditions
            
        Returns:
            True if calibration point was successfully added
        """
        
        try:
            self.logger.info(f"📊 Adding calibration point: {concentration:.6f} M")
            
            if not self.precision_analyzer:
                self.logger.error("Precision analyzer not available")
                return False
            
            # Analyze the CV data
            analysis_results = self.precision_analyzer.analyze_cv_data(
                voltage, current, filename=filename
            )
            
            if not analysis_results['success']:
                self.logger.error(f"Analysis failed: {analysis_results.get('error', 'Unknown error')}")
                return False
            
            # Check data quality
            quality_score = analysis_results['quality_metrics']['overall_quality']
            if quality_score < self.config['quality_threshold']:
                self.logger.warning(f"Data quality too low: {quality_score:.1f}% < {self.config['quality_threshold']}%")
                return False
            
            # Extract PLS features
            pls_features_dict = analysis_results['pls_features']
            pls_features = PLSFeatures(**pls_features_dict)
            
            # Create calibration point
            calibration_point = PLSCalibrationPoint(
                concentration=concentration,
                features=pls_features,
                filename=filename,
                measurement_conditions=conditions or {},
                timestamp=datetime.now(),
                quality_score=quality_score
            )
            
            self.calibration_data.append(calibration_point)
            
            self.logger.info(f"✅ Calibration point added successfully (total: {len(self.calibration_data)})")
            self.logger.info(f"   Quality: {quality_score:.1f}%, Ox height: {pls_features.oxidation_height:.2f} μA")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add calibration point: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def build_pls_model(self, model_id: str = None, feature_subset: List[str] = None) -> Optional[PLSModel]:
        """
        Build PLS model from calibration data
        
        Args:
            model_id: Unique identifier for the model
            feature_subset: Specific features to use (if None, uses all)
            
        Returns:
            Trained PLS model or None if failed
        """
        
        try:
            if len(self.calibration_data) < self.config['min_calibration_points']:
                self.logger.error(f"Insufficient calibration data: {len(self.calibration_data)} < {self.config['min_calibration_points']}")
                return None
            
            model_id = model_id or f"pls_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.logger.info(f"🏗️ Building PLS model '{model_id}' with {len(self.calibration_data)} calibration points")
            
            # Extract features and concentrations
            feature_matrix, concentrations, feature_names = self._prepare_feature_matrix(feature_subset)
            
            # Feature selection and scaling
            selected_features, scaler = self._select_and_scale_features(feature_matrix, feature_names)
            
            # Optimize number of PLS components
            optimal_components = self._optimize_pls_components(selected_features, concentrations)
            
            # Train final model
            pls_model = PLSRegression(n_components=optimal_components)
            pls_model.fit(selected_features, concentrations)
            
            # Calculate model metrics
            model_metrics = self._calculate_model_metrics(pls_model, selected_features, concentrations)
            
            # Calculate feature importance
            feature_importance = self._calculate_feature_importance(pls_model, feature_names)
            
            # Create model object
            model = PLSModel(
                model=pls_model,
                scaler=scaler,
                feature_names=feature_names,
                calibration_points=self.calibration_data.copy(),
                model_metrics=model_metrics,
                optimal_components=optimal_components,
                feature_importance=feature_importance,
                created_timestamp=datetime.now(),
                model_id=model_id
            )
            
            # Store model
            self.models[model_id] = model
            
            # Save model if configured
            if self.config['save_models']:
                self._save_model(model)
            
            self.logger.info(f"✅ PLS model built successfully:")
            self.logger.info(f"   Components: {optimal_components}")
            self.logger.info(f"   R²: {model_metrics['r2_score']:.4f}")
            self.logger.info(f"   RMSE: {model_metrics['rmse']:.6f} M")
            self.logger.info(f"   Features: {len(feature_names)}")
            
            return model
            
        except Exception as e:
            self.logger.error(f"❌ Failed to build PLS model: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def _prepare_feature_matrix(self, feature_subset: List[str] = None) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepare feature matrix and concentration vector from calibration data"""
        
        # Define all available features
        all_features = [
            'oxidation_height', 'reduction_height', 'peak_separation', 'peak_ratio',
            'total_area', 'oxidation_area', 'reduction_area', 'area_ratio',
            'peak_symmetry', 'baseline_quality', 'signal_noise_ratio',
            'charge_transfer_resistance', 'diffusion_coefficient'
        ]
        
        # Use specified subset or all features
        feature_names = feature_subset or all_features
        
        # Extract data
        concentrations = np.array([point.concentration for point in self.calibration_data])
        
        feature_matrix = []
        for point in self.calibration_data:
            feature_vector = []
            for feature_name in feature_names:
                feature_value = getattr(point.features, feature_name, 0.0)
                feature_vector.append(feature_value)
            feature_matrix.append(feature_vector)
        
        feature_matrix = np.array(feature_matrix)
        
        self.logger.info(f"📊 Feature matrix: {feature_matrix.shape[0]} samples × {feature_matrix.shape[1]} features")
        self.logger.info(f"   Concentration range: {concentrations.min():.6f} to {concentrations.max():.6f} M")
        
        return feature_matrix, concentrations, feature_names
    
    def _select_and_scale_features(self, feature_matrix: np.ndarray, 
                                 feature_names: List[str]) -> Tuple[np.ndarray, StandardScaler]:
        """Select and scale features for PLS modeling"""
        
        # Remove features with low variance
        variances = np.var(feature_matrix, axis=0)
        variance_threshold = self.config['feature_selection_threshold']
        
        selected_indices = np.where(variances > variance_threshold)[0]
        selected_features = feature_matrix[:, selected_indices]
        selected_feature_names = [feature_names[i] for i in selected_indices]
        
        self.logger.info(f"🔍 Feature selection: {len(selected_indices)}/{len(feature_names)} features retained")
        
        # Scale features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(selected_features)
        
        return scaled_features, scaler
    
    def _optimize_pls_components(self, features: np.ndarray, concentrations: np.ndarray) -> int:
        """Optimize number of PLS components using cross-validation"""
        
        max_components = min(self.config['max_pls_components'], features.shape[1], len(concentrations) - 1)
        
        best_score = -np.inf
        best_components = 1
        
        for n_components in range(1, max_components + 1):
            try:
                pls = PLSRegression(n_components=n_components)
                
                # Use cross-validation
                cv_scores = cross_val_score(
                    pls, features, concentrations, 
                    cv=min(self.config['cv_folds'], len(concentrations)),
                    scoring='r2'
                )
                
                mean_score = np.mean(cv_scores)
                
                if mean_score > best_score:
                    best_score = mean_score
                    best_components = n_components
                
            except Exception as e:
                self.logger.warning(f"Failed to evaluate {n_components} components: {e}")
                break
        
        self.logger.info(f"🎯 Optimal components: {best_components} (CV R² = {best_score:.4f})")
        
        return best_components
    
    def _calculate_model_metrics(self, model: PLSRegression, features: np.ndarray, 
                               concentrations: np.ndarray) -> Dict[str, float]:
        """Calculate comprehensive model performance metrics"""
        
        # Make predictions
        predictions = model.predict(features).flatten()
        
        # Calculate metrics
        r2 = r2_score(concentrations, predictions)
        rmse = np.sqrt(mean_squared_error(concentrations, predictions))
        mae = mean_absolute_error(concentrations, predictions)
        
        # Relative error
        mean_concentration = np.mean(concentrations)
        relative_rmse = rmse / mean_concentration * 100 if mean_concentration > 0 else 0
        
        # Cross-validation metrics
        try:
            cv_scores = cross_val_score(model, features, concentrations, cv=5, scoring='r2')
            cv_r2_mean = np.mean(cv_scores)
            cv_r2_std = np.std(cv_scores)
        except:
            cv_r2_mean = r2
            cv_r2_std = 0.0
        
        metrics = {
            'r2_score': float(r2),
            'rmse': float(rmse),
            'mae': float(mae),
            'relative_rmse_percent': float(relative_rmse),
            'cv_r2_mean': float(cv_r2_mean),
            'cv_r2_std': float(cv_r2_std),
            'n_samples': len(concentrations),
            'n_features': features.shape[1]
        }
        
        return metrics
    
    def _calculate_feature_importance(self, model: PLSRegression, feature_names: List[str]) -> Dict[str, float]:
        """Calculate feature importance from PLS model"""
        
        # Use PLS coefficients as importance measure
        if hasattr(model, 'coef_'):
            importance_values = np.abs(model.coef_.flatten())
            
            # Normalize to sum to 1
            if np.sum(importance_values) > 0:
                importance_values = importance_values / np.sum(importance_values)
            
            feature_importance = {}
            for i, name in enumerate(feature_names):
                if i < len(importance_values):
                    feature_importance[name] = float(importance_values[i])
                else:
                    feature_importance[name] = 0.0
            
            return feature_importance
        else:
            return {name: 1.0/len(feature_names) for name in feature_names}
    
    def predict_concentration(self, voltage: np.ndarray, current: np.ndarray,
                            model_id: str = None, filename: str = "") -> Optional[ConcentrationPrediction]:
        """
        Predict concentration from CV data using trained PLS model
        
        Args:
            voltage: Voltage array (V)
            current: Current array (μA)
            model_id: Specific model to use (if None, uses best available)
            filename: Source filename for logging
            
        Returns:
            Concentration prediction or None if failed
        """
        
        try:
            if not self.models:
                self.logger.error("No trained models available")
                return None
            
            # Select model
            if model_id and model_id in self.models:
                model = self.models[model_id]
            else:
                # Use model with best R² score
                model = max(self.models.values(), key=lambda m: m.model_metrics['r2_score'])
                model_id = model.model_id
            
            self.logger.info(f"🔮 Predicting concentration using model '{model_id}'")
            
            # Analyze the CV data
            if not self.precision_analyzer:
                self.logger.error("Precision analyzer not available")
                return None
            
            analysis_results = self.precision_analyzer.analyze_cv_data(
                voltage, current, filename=filename
            )
            
            if not analysis_results['success']:
                self.logger.error(f"Analysis failed: {analysis_results.get('error', 'Unknown error')}")
                return None
            
            # Extract features
            pls_features_dict = analysis_results['pls_features']
            pls_features = PLSFeatures(**pls_features_dict)
            
            # Prepare feature vector
            feature_vector = []
            for feature_name in model.feature_names:
                feature_value = getattr(pls_features, feature_name, 0.0)
                feature_vector.append(feature_value)
            
            feature_vector = np.array(feature_vector).reshape(1, -1)
            
            # Scale features
            scaled_features = model.scaler.transform(feature_vector)
            
            # Make prediction
            predicted_concentration = model.model.predict(scaled_features)[0]
            
            # Calculate confidence interval (simplified)
            rmse = model.model_metrics['rmse']
            confidence_interval = (
                max(0, predicted_concentration - 2 * rmse),
                predicted_concentration + 2 * rmse
            )
            
            # Calculate prediction confidence based on model quality and data quality
            model_quality = model.model_metrics['r2_score'] * 100
            data_quality = analysis_results['quality_metrics']['overall_quality']
            prediction_confidence = (model_quality + data_quality) / 2
            
            # Create prediction result
            prediction = ConcentrationPrediction(
                predicted_concentration=float(predicted_concentration),
                confidence_interval=confidence_interval,
                prediction_confidence=float(prediction_confidence),
                features_used=pls_features,
                model_id=model_id,
                timestamp=datetime.now()
            )
            
            # Store prediction
            self.prediction_history.append(prediction)
            
            self.logger.info(f"✅ Concentration prediction: {predicted_concentration:.6f} M")
            self.logger.info(f"   Confidence: {prediction_confidence:.1f}%")
            self.logger.info(f"   95% CI: [{confidence_interval[0]:.6f}, {confidence_interval[1]:.6f}] M")
            
            return prediction
            
        except Exception as e:
            self.logger.error(f"❌ Prediction failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def validate_model(self, model_id: str) -> Dict[str, Any]:
        """Comprehensive model validation"""
        
        if model_id not in self.models:
            return {'success': False, 'error': 'Model not found'}
        
        model = self.models[model_id]
        
        try:
            self.logger.info(f"🔍 Validating model '{model_id}'")
            
            # Prepare data
            feature_matrix, concentrations, _ = self._prepare_feature_matrix(model.feature_names)
            scaled_features = model.scaler.transform(feature_matrix)
            
            # Leave-one-out cross-validation
            loo = LeaveOneOut()
            loo_predictions = []
            loo_true = []
            
            for train_idx, test_idx in loo.split(scaled_features):
                X_train, X_test = scaled_features[train_idx], scaled_features[test_idx]
                y_train, y_test = concentrations[train_idx], concentrations[test_idx]
                
                # Train model on training set
                temp_model = PLSRegression(n_components=model.optimal_components)
                temp_model.fit(X_train, y_train)
                
                # Predict on test set
                prediction = temp_model.predict(X_test)[0]
                loo_predictions.append(prediction)
                loo_true.append(y_test[0])
            
            loo_predictions = np.array(loo_predictions)
            loo_true = np.array(loo_true)
            
            # Calculate validation metrics
            loo_r2 = r2_score(loo_true, loo_predictions)
            loo_rmse = np.sqrt(mean_squared_error(loo_true, loo_predictions))
            
            # Prediction vs actual plot data
            plot_data = {
                'true_concentrations': loo_true.tolist(),
                'predicted_concentrations': loo_predictions.tolist()
            }
            
            validation_results = {
                'success': True,
                'model_id': model_id,
                'loo_r2': float(loo_r2),
                'loo_rmse': float(loo_rmse),
                'training_r2': model.model_metrics['r2_score'],
                'training_rmse': model.model_metrics['rmse'],
                'n_calibration_points': len(model.calibration_points),
                'optimal_components': model.optimal_components,
                'plot_data': plot_data,
                'validation_timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ Model validation complete:")
            self.logger.info(f"   LOO R²: {loo_r2:.4f}")
            self.logger.info(f"   LOO RMSE: {loo_rmse:.6f} M")
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"❌ Model validation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _save_model(self, model: PLSModel):
        """Save PLS model to disk"""
        
        try:
            model_dir = Path(self.config['model_directory'])
            model_dir.mkdir(exist_ok=True)
            
            model_file = model_dir / f"{model.model_id}.pkl"
            
            # Save model using joblib or pickle fallback
            if SKLEARN_AVAILABLE:
                try:
                    import joblib
                    joblib.dump(model, model_file)
                except ImportError:
                    import pickle
                    with open(model_file, 'wb') as f:
                        pickle.dump(model, f)
            else:
                import pickle
                with open(model_file, 'wb') as f:
                    pickle.dump(model, f)
            
            self.logger.info(f"💾 Model saved: {model_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save model: {e}")
    
    def load_model(self, model_file: str) -> bool:
        """Load PLS model from disk"""
        
        try:
            model_path = Path(model_file)
            if not model_path.exists():
                self.logger.error(f"Model file not found: {model_file}")
                return False
            
            # Load model using joblib or pickle fallback
            if SKLEARN_AVAILABLE:
                try:
                    import joblib
                    model = joblib.load(model_path)
                except ImportError:
                    import pickle
                    with open(model_path, 'rb') as f:
                        model = pickle.load(f)
            else:
                import pickle
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
            
            self.models[model.model_id] = model
            
            self.logger.info(f"📂 Model loaded: {model.model_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load model: {e}")
            return False
    
    def generate_calibration_report(self) -> Dict[str, Any]:
        """Generate comprehensive calibration report"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'calibration_points': len(self.calibration_data),
            'models': len(self.models),
            'predictions_made': len(self.prediction_history)
        }
        
        if self.calibration_data:
            concentrations = [point.concentration for point in self.calibration_data]
            quality_scores = [point.quality_score for point in self.calibration_data]
            
            report['concentration_range'] = {
                'min': float(min(concentrations)),
                'max': float(max(concentrations)),
                'mean': float(np.mean(concentrations)),
                'std': float(np.std(concentrations))
            }
            
            report['data_quality'] = {
                'mean_quality': float(np.mean(quality_scores)),
                'min_quality': float(min(quality_scores)),
                'points_above_threshold': sum(1 for q in quality_scores if q >= self.config['quality_threshold'])
            }
        
        if self.models:
            best_model = max(self.models.values(), key=lambda m: m.model_metrics['r2_score'])
            report['best_model'] = {
                'model_id': best_model.model_id,
                'r2_score': best_model.model_metrics['r2_score'],
                'rmse': best_model.model_metrics['rmse'],
                'n_components': best_model.optimal_components,
                'top_features': sorted(best_model.feature_importance.items(), 
                                     key=lambda x: x[1], reverse=True)[:5]
            }
        
        return report
    
    def plot_calibration_curve(self, model_id: str = None, save_path: str = None):
        """Plot calibration curve for visual validation"""
        
        if not self.models:
            self.logger.error("No models available for plotting")
            return
        
        # Select model
        if model_id and model_id in self.models:
            model = self.models[model_id]
        else:
            model = max(self.models.values(), key=lambda m: m.model_metrics['r2_score'])
        
        try:
            # Prepare data
            feature_matrix, concentrations, _ = self._prepare_feature_matrix(model.feature_names)
            scaled_features = model.scaler.transform(feature_matrix)
            predictions = model.model.predict(scaled_features).flatten()
            
            # Create plot
            plt.figure(figsize=(10, 8))
            
            # Calibration plot
            plt.subplot(2, 2, 1)
            plt.scatter(concentrations * 1e6, predictions * 1e6, alpha=0.7, s=50)
            plt.plot([concentrations.min() * 1e6, concentrations.max() * 1e6], 
                    [concentrations.min() * 1e6, concentrations.max() * 1e6], 'r--', alpha=0.8)
            plt.xlabel('True Concentration (μM)')
            plt.ylabel('Predicted Concentration (μM)')
            plt.title(f'Calibration Curve (R² = {model.model_metrics["r2_score"]:.4f})')
            plt.grid(True, alpha=0.3)
            
            # Residuals plot
            plt.subplot(2, 2, 2)
            residuals = (predictions - concentrations) * 1e6
            plt.scatter(concentrations * 1e6, residuals, alpha=0.7, s=50)
            plt.axhline(y=0, color='r', linestyle='--', alpha=0.8)
            plt.xlabel('True Concentration (μM)')
            plt.ylabel('Residuals (μM)')
            plt.title('Residuals Plot')
            plt.grid(True, alpha=0.3)
            
            # Feature importance
            plt.subplot(2, 2, 3)
            features = list(model.feature_importance.keys())
            importance = list(model.feature_importance.values())
            top_features = sorted(zip(features, importance), key=lambda x: x[1], reverse=True)[:8]
            
            plt.barh([f[0] for f in top_features], [f[1] for f in top_features])
            plt.xlabel('Feature Importance')
            plt.title('Top Features')
            plt.tight_layout()
            
            # PLS components plot
            plt.subplot(2, 2, 4)
            components_range = range(1, min(11, len(concentrations)))
            cv_scores = []
            
            for n_comp in components_range:
                try:
                    pls = PLSRegression(n_components=n_comp)
                    scores = cross_val_score(pls, scaled_features, concentrations, cv=3, scoring='r2')
                    cv_scores.append(np.mean(scores))
                except:
                    cv_scores.append(0)
            
            plt.plot(components_range, cv_scores, 'o-')
            plt.axvline(x=model.optimal_components, color='r', linestyle='--', alpha=0.8)
            plt.xlabel('Number of PLS Components')
            plt.ylabel('Cross-Validation R²')
            plt.title('Component Optimization')
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"📊 Calibration plot saved: {save_path}")
            
            plt.show()
            
        except Exception as e:
            self.logger.error(f"❌ Plotting failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())


def test_pls_analyzer():
    """Test the PLS analyzer with sample calibration data"""
    
    import os
    import pandas as pd
    import glob
    
    logger.info("🧪 Testing Advanced PLS Analyzer")
    logger.info("=" * 60)
    
    if not PRECISION_ANALYZER_AVAILABLE:
        logger.error("Precision analyzer not available - cannot run full test")
        return None
    
    # Create analyzer
    analyzer = AdvancedPLSAnalyzer({
        'quality_threshold': 75.0,
        'min_calibration_points': 3
    })
    
    # Look for calibration data
    data_patterns = [
        "Test_data/Palmsens/Palmsens_*mM/*.csv",
        "Test_data/Stm32/STM32_*mM/*.csv"
    ]
    
    calibration_files = []
    for pattern in data_patterns:
        calibration_files.extend(glob.glob(pattern, recursive=True))
    
    if not calibration_files:
        logger.warning("No calibration files found, creating synthetic test data")
        return test_synthetic_calibration()
    
    # Extract concentrations and add calibration points
    added_points = 0
    for filepath in calibration_files[:10]:  # Limit to first 10 files
        try:
            # Extract concentration from filename
            filename = os.path.basename(filepath)
            concentration = None
            
            # Try different concentration patterns
            import re
            patterns = [
                r'(\d+\.?\d*)mM',
                r'(\d+)_(\d+)mM',
                r'Ferro_(\d+\.?\d*)_'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, filename, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 1:
                        concentration = float(match.group(1)) * 1e-3  # Convert mM to M
                    else:
                        concentration = float(f"{match.group(1)}.{match.group(2)}") * 1e-3
                    break
            
            if concentration is None:
                continue
            
            # Load data
            df = pd.read_csv(filepath, skiprows=1)
            voltage = df.iloc[:, 0].values
            current = df.iloc[:, 1].values
            
            # Convert current to μA if needed
            if np.max(np.abs(current)) < 1e-3:
                current = current * 1e6
            
            # Add calibration point
            success = analyzer.add_calibration_point(
                voltage, current, concentration, filename=filename
            )
            
            if success:
                added_points += 1
                logger.info(f"   Added: {filename} ({concentration*1e6:.1f} μM)")
            
        except Exception as e:
            logger.warning(f"Failed to process {filepath}: {e}")
    
    logger.info(f"📊 Added {added_points} calibration points")
    
    if added_points >= 3:
        # Build PLS model
        model = analyzer.build_pls_model("test_model")
        
        if model:
            # Validate model
            validation = analyzer.validate_model("test_model")
            logger.info(f"🔍 Validation R²: {validation.get('loo_r2', 0):.4f}")
            
            # Generate report
            report = analyzer.generate_calibration_report()
            
            # Save report
            with open("pls_analysis_report.json", 'w') as f:
                json.dump(report, f, indent=2)
            logger.info("📄 Report saved: pls_analysis_report.json")
            
            # Plot calibration curve
            try:
                analyzer.plot_calibration_curve(save_path="pls_calibration_curve.png")
            except Exception as e:
                logger.warning(f"Plotting failed: {e}")
            
            return analyzer
    
    logger.warning("Insufficient calibration data for model building")
    return None


def test_synthetic_calibration():
    """Test with synthetic calibration data"""
    
    logger.info("🧪 Testing with synthetic calibration data")
    
    # Create synthetic CV data with known concentrations
    concentrations = [0.5e-6, 1.0e-6, 2.0e-6, 5.0e-6, 10.0e-6]  # μM concentrations
    
    analyzer = AdvancedPLSAnalyzer()
    
    for i, conc in enumerate(concentrations):
        # Generate synthetic CV data
        voltage = np.linspace(-0.2, 0.4, 200)
        
        # Synthetic oxidation peak
        ox_peak = conc * 1e6 * 10 * np.exp(-((voltage - 0.18)**2) / (2 * 0.02**2))
        
        # Synthetic reduction peak  
        red_peak = -conc * 1e6 * 8 * np.exp(-((voltage - 0.08)**2) / (2 * 0.02**2))
        
        # Background + noise
        background = 0.1 * voltage + np.random.normal(0, 0.1, len(voltage))
        
        current = ox_peak + red_peak + background
        
        # Add calibration point
        success = analyzer.add_calibration_point(
            voltage, current, conc, filename=f"synthetic_{conc*1e6:.1f}uM.csv"
        )
        
        if success:
            logger.info(f"   Added synthetic point: {conc*1e6:.1f} μM")
    
    # Build and test model
    model = analyzer.build_pls_model("synthetic_model")
    
    if model:
        # Test prediction with new synthetic data
        test_conc = 3.0e-6  # 3 μM
        test_voltage = np.linspace(-0.2, 0.4, 200)
        test_ox = test_conc * 1e6 * 10 * np.exp(-((test_voltage - 0.18)**2) / (2 * 0.02**2))
        test_red = -test_conc * 1e6 * 8 * np.exp(-((test_voltage - 0.08)**2) / (2 * 0.02**2))
        test_bg = 0.1 * test_voltage + np.random.normal(0, 0.1, len(test_voltage))
        test_current = test_ox + test_red + test_bg
        
        prediction = analyzer.predict_concentration(test_voltage, test_current, filename="test_sample.csv")
        
        if prediction:
            predicted_conc_uM = prediction.predicted_concentration * 1e6
            true_conc_uM = test_conc * 1e6
            error_percent = abs(predicted_conc_uM - true_conc_uM) / true_conc_uM * 100
            
            logger.info(f"🎯 Prediction test:")
            logger.info(f"   True: {true_conc_uM:.1f} μM")
            logger.info(f"   Predicted: {predicted_conc_uM:.1f} μM")
            logger.info(f"   Error: {error_percent:.1f}%")
    
    return analyzer


if __name__ == "__main__":
    test_pls_analyzer()
