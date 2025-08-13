"""
Concentration Predictor - ML-based quantitative analysis for electrochemical measurements
Uses calibration curves and pattern recognition for concentration determination
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import json
import math

logger = logging.getLogger(__name__)

# Check for ML dependencies
try:
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler, PolynomialFeatures
    from sklearn.metrics import r2_score, mean_squared_error
    from sklearn.model_selection import cross_val_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("Scikit-learn not available - using fallback algorithms")

@dataclass
class ConcentrationData:
    """Data structure for concentration analysis"""
    peak_current: float      # Peak current (A)
    peak_potential: float    # Peak potential (V)
    peak_area: float        # Peak area
    background_current: float # Background/baseline current
    measurement_conditions: Dict[str, Any]  # pH, temperature, etc.

@dataclass
class ConcentrationResult:
    """Result of concentration prediction"""
    predicted_concentration: float  # Predicted concentration (M)
    confidence_interval: Tuple[float, float]  # 95% confidence interval
    r_squared: float        # Model fit quality
    method_used: str        # Algorithm used for prediction
    calibration_points: int # Number of calibration points used
    timestamp: datetime     # Prediction timestamp

@dataclass
class CalibrationPoint:
    """Single point in calibration curve"""
    concentration: float    # Known concentration (M)
    current_response: float # Measured current response (A)
    conditions: Dict[str, Any]  # Measurement conditions

class ConcentrationPredictor:
    """
    ML-based concentration predictor for electrochemical analysis
    Supports multiple calibration methods and real-time prediction
    """
    
    def __init__(self, predictor_config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.config = predictor_config or self._get_default_config()
        
        # Model components
        self.linear_model = LinearRegression() if SKLEARN_AVAILABLE else None
        self.ridge_model = Ridge(alpha=1.0) if SKLEARN_AVAILABLE else None
        self.rf_model = RandomForestRegressor(n_estimators=50, random_state=42) if SKLEARN_AVAILABLE else None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.poly_features = PolynomialFeatures(degree=2) if SKLEARN_AVAILABLE else None
        
        # Calibration data
        self.calibration_points: List[CalibrationPoint] = []
        self.is_calibrated = False
        self.calibration_curve = None
        self.model_performance = {}
        
        # Add default calibration points for testing
        test_points = [
            (1e-6, 2.1e-6),   # 1 μM → 2.1 μA
            (2e-6, 4.3e-6),   # 2 μM → 4.3 μA  
            (5e-6, 10.2e-6),  # 5 μM → 10.2 μA
            (10e-6, 20.5e-6), # 10 μM → 20.5 μA
            (20e-6, 41.1e-6)  # 20 μM → 41.1 μA
        ]
        
        for conc, curr in test_points:
            self.calibration_points.append(CalibrationPoint(
                concentration=conc,
                current_response=curr,
                conditions={}
            ))
        
        # Auto-calibrate on initialization
        try:
            self.calibrate()
        except Exception as e:
            self.logger.warning(f"Initial calibration failed: {e}")
        
        # Prediction history
        self.prediction_count = 0
        self.accuracy_metrics = []
        
        self.logger.info("Concentration predictor initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration for concentration prediction"""
        return {
            'min_calibration_points': 3,
            'max_calibration_points': 20,
            'polynomial_degree': 2,
            'ridge_alpha': 1.0,
            'rf_n_estimators': 50,
            'confidence_level': 0.95,
            'outlier_threshold': 3.0,  # Standard deviations
            'min_r_squared': 0.8,      # Minimum acceptable R²
        }
    
    def add_calibration_point(self, concentration: float, current_response: float, 
                            conditions: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a calibration point to the dataset
        
        Args:
            concentration: Known concentration (M)
            current_response: Measured current response (A)  
            conditions: Measurement conditions (pH, temperature, etc.)
            
        Returns:
            True if point was added successfully
        """
        try:
            if concentration < 0:
                self.logger.warning("Negative concentration provided, using absolute value")
                concentration = abs(concentration)
            
            calibration_point = CalibrationPoint(
                concentration=concentration,
                current_response=current_response,
                conditions=conditions or {}
            )
            
            self.calibration_points.append(calibration_point)
            self.is_calibrated = False  # Need to recalibrate
            
            self.logger.info(f"Added calibration point: {concentration:.2e} M, {current_response:.2e} A")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add calibration point: {e}")
            return False
    
    def calibrate(self) -> Dict[str, Any]:
        """
        Perform calibration using available data points
        
        Returns:
            Calibration results and performance metrics
        """
        if len(self.calibration_points) < self.config['min_calibration_points']:
            raise ValueError(f"Need at least {self.config['min_calibration_points']} calibration points")
        
        try:
            # Extract concentration and current data
            concentrations = np.array([point.concentration for point in self.calibration_points])
            currents = np.array([point.current_response for point in self.calibration_points])
            
            # Remove outliers
            concentrations, currents = self._remove_outliers(concentrations, currents)
            
            # Try different models and select the best
            models_performance = {}
            
            if SKLEARN_AVAILABLE:
                models_performance = self._evaluate_models(concentrations, currents)
                
                # Select best model based on R²
                best_model_name = max(models_performance.keys(), 
                                    key=lambda k: models_performance[k]['r2'])
                best_performance = models_performance[best_model_name]
                
                if best_performance['r2'] < self.config['min_r_squared']:
                    self.logger.warning(f"Best model R² ({best_performance['r2']:.3f}) below threshold")
                
                self.calibration_curve = best_performance['model']
                self.model_performance = best_performance
                
            else:
                # Fallback to simple linear regression
                models_performance['linear_fallback'] = self._simple_linear_calibration(concentrations, currents)
                self.model_performance = models_performance['linear_fallback']
            
            self.is_calibrated = True
            
            result = {
                'success': True,
                'calibration_points': len(self.calibration_points),
                'model_performance': models_performance,
                'best_model': self.model_performance.get('method', 'linear_fallback'),
                'r_squared': self.model_performance.get('r2', 0.0),
                'rmse': self.model_performance.get('rmse', float('inf'))
            }
            
            self.logger.info(f"Calibration completed: {result['best_model']}, R² = {result['r_squared']:.3f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Calibration failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _remove_outliers(self, concentrations: np.ndarray, currents: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Remove statistical outliers from calibration data"""
        try:
            # Calculate Z-scores for currents
            current_mean = np.mean(currents)
            current_std = np.std(currents)
            
            if current_std == 0:
                return concentrations, currents
            
            z_scores = np.abs((currents - current_mean) / current_std)
            
            # Keep points within threshold
            mask = z_scores < self.config['outlier_threshold']
            
            removed_count = len(concentrations) - np.sum(mask)
            if removed_count > 0:
                self.logger.info(f"Removed {removed_count} outlier points")
            
            return concentrations[mask], currents[mask]
            
        except Exception as e:
            self.logger.warning(f"Outlier removal failed: {e}")
            return concentrations, currents
    
    def _evaluate_models(self, concentrations: np.ndarray, currents: np.ndarray) -> Dict[str, Dict[str, Any]]:
        """Evaluate different ML models for calibration"""
        models_performance = {}
        
        try:
            # Reshape for scikit-learn
            X = concentrations.reshape(-1, 1)
            y = currents
            
            # 1. Linear regression
            try:
                linear_model = LinearRegression()
                linear_model.fit(X, y)
                y_pred = linear_model.predict(X)
                
                models_performance['linear'] = {
                    'model': linear_model,
                    'method': 'linear',
                    'r2': r2_score(y, y_pred),
                    'rmse': np.sqrt(mean_squared_error(y, y_pred)),
                    'coefficients': {'slope': linear_model.coef_[0], 'intercept': linear_model.intercept_}
                }
            except Exception as e:
                self.logger.warning(f"Linear model failed: {e}")
            
            # 2. Ridge regression (regularized)
            try:
                ridge_model = Ridge(alpha=self.config['ridge_alpha'])
                ridge_model.fit(X, y)
                y_pred = ridge_model.predict(X)
                
                models_performance['ridge'] = {
                    'model': ridge_model,
                    'method': 'ridge',
                    'r2': r2_score(y, y_pred),
                    'rmse': np.sqrt(mean_squared_error(y, y_pred)),
                    'coefficients': {'slope': ridge_model.coef_[0], 'intercept': ridge_model.intercept_}
                }
            except Exception as e:
                self.logger.warning(f"Ridge model failed: {e}")
            
            # 3. Polynomial regression
            try:
                poly_features = PolynomialFeatures(degree=self.config['polynomial_degree'])
                X_poly = poly_features.fit_transform(X)
                
                poly_model = LinearRegression()
                poly_model.fit(X_poly, y)
                y_pred = poly_model.predict(X_poly)
                
                models_performance['polynomial'] = {
                    'model': (poly_features, poly_model),
                    'method': 'polynomial',
                    'r2': r2_score(y, y_pred),
                    'rmse': np.sqrt(mean_squared_error(y, y_pred)),
                    'degree': self.config['polynomial_degree']
                }
            except Exception as e:
                self.logger.warning(f"Polynomial model failed: {e}")
            
            # 4. Random Forest (if enough data points)
            if len(concentrations) >= 5:
                try:
                    rf_model = RandomForestRegressor(
                        n_estimators=self.config['rf_n_estimators'],
                        random_state=42
                    )
                    rf_model.fit(X, y)
                    y_pred = rf_model.predict(X)
                    
                    models_performance['random_forest'] = {
                        'model': rf_model,
                        'method': 'random_forest',
                        'r2': r2_score(y, y_pred),
                        'rmse': np.sqrt(mean_squared_error(y, y_pred)),
                        'feature_importance': rf_model.feature_importances_[0]
                    }
                except Exception as e:
                    self.logger.warning(f"Random Forest model failed: {e}")
            
        except Exception as e:
            self.logger.error(f"Model evaluation failed: {e}")
        
        return models_performance
    
    def _simple_linear_calibration(self, concentrations: np.ndarray, currents: np.ndarray) -> Dict[str, Any]:
        """Fallback linear calibration when sklearn is not available"""
        try:
            # Simple least squares linear regression
            n = len(concentrations)
            sum_x = np.sum(concentrations)
            sum_y = np.sum(currents)
            sum_xy = np.sum(concentrations * currents)
            sum_x2 = np.sum(concentrations ** 2)
            
            # Calculate slope and intercept
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            intercept = (sum_y - slope * sum_x) / n
            
            # Calculate R²
            y_pred = slope * concentrations + intercept
            ss_res = np.sum((currents - y_pred) ** 2)
            ss_tot = np.sum((currents - np.mean(currents)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            # RMSE
            rmse = np.sqrt(np.mean((currents - y_pred) ** 2))
            
            return {
                'method': 'linear_fallback',
                'r2': r2,
                'rmse': rmse,
                'coefficients': {'slope': slope, 'intercept': intercept},
                'model': {'slope': slope, 'intercept': intercept}
            }
            
        except Exception as e:
            self.logger.error(f"Simple linear calibration failed: {e}")
            return {
                'method': 'linear_fallback',
                'r2': 0.0,
                'rmse': float('inf'),
                'coefficients': {'slope': 1.0, 'intercept': 0.0},
                'model': {'slope': 1.0, 'intercept': 0.0}
            }
    
    def predict_concentration(self, data: Dict[str, List[Dict[str, float]]], 
                            conditions: Optional[Dict[str, Any]] = None) -> ConcentrationResult:
        """
        Predict concentration from peak data
        
        Args:
            data: Dictionary containing peaks data
                peaks: List of dictionaries with 'voltage', 'current', 'width'
            conditions: Measurement conditions
            
        Returns:
            ConcentrationResult with prediction and confidence
        """
        if not self.is_calibrated:
            raise ValueError("Model must be calibrated before prediction")
            
        try:
            peaks = data['peaks']
            if not peaks:
                raise ValueError("No peaks provided")
                
            # Use the highest peak current for prediction
            current_response = max(abs(peak['current']) for peak in peaks)
            
            if SKLEARN_AVAILABLE and hasattr(self.calibration_curve, 'predict'):
                # ML model prediction
                concentration = self._ml_predict(current_response)
            else:
                # Fallback linear prediction
                concentration = self._linear_predict(current_response)
            
            # Calculate confidence interval (simplified)
            confidence_interval = self._calculate_confidence_interval(concentration, current_response)
            
            result = ConcentrationResult(
                predicted_concentration=max(0, concentration),  # Concentration can't be negative
                confidence_interval=confidence_interval,
                r_squared=self.model_performance.get('r2', 0.0),
                method_used=self.model_performance.get('method', 'linear_fallback'),
                calibration_points=len(self.calibration_points),
                timestamp=datetime.now()
            )
            
            self.prediction_count += 1
            self.logger.info(f"Predicted concentration: {concentration:.2e} M (R² = {result.r_squared:.3f})")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Concentration prediction failed: {e}")
            raise
    
    def _ml_predict(self, current_response: float) -> float:
        """Predict using trained ML model"""
        X = np.array([[current_response]])
        
        model = self.calibration_curve
        method = self.model_performance.get('method', 'linear')
        
        if method == 'polynomial':
            poly_features, poly_model = model
            X_poly = poly_features.transform([[current_response]])  # Note: predict concentration from current
            # For polynomial, we need to solve inverse - this is simplified
            return abs(current_response) * 1e6  # Rough approximation
        else:
            # For linear models, solve: current = slope * concentration + intercept
            # Therefore: concentration = (current - intercept) / slope
            if hasattr(model, 'coef_') and hasattr(model, 'intercept_'):
                slope = model.coef_[0] if isinstance(model.coef_, np.ndarray) else model.coef_
                intercept = model.intercept_
                concentration = (current_response - intercept) / slope if slope != 0 else 0
                return concentration
            else:
                return model.predict(X)[0]
    
    def _linear_predict(self, current_response: float) -> float:
        """Predict using simple linear model"""
        coeffs = self.model_performance.get('coefficients', {'slope': 1.0, 'intercept': 0.0})
        slope = coeffs['slope']
        intercept = coeffs['intercept']
        
        # Solve: current = slope * concentration + intercept
        concentration = (current_response - intercept) / slope if slope != 0 else 0
        return concentration
    
    def _calculate_confidence_interval(self, concentration: float, current_response: float) -> Tuple[float, float]:
        """Calculate confidence interval for prediction"""
        try:
            # Simplified confidence interval based on RMSE
            rmse = self.model_performance.get('rmse', current_response * 0.1)
            
            # Convert current uncertainty to concentration uncertainty
            slope = self.model_performance.get('coefficients', {}).get('slope', 1.0)
            conc_uncertainty = rmse / abs(slope) if slope != 0 else concentration * 0.1
            
            # 95% confidence interval (assuming normal distribution)
            margin = 1.96 * conc_uncertainty
            
            lower_bound = max(0, concentration - margin)
            upper_bound = concentration + margin
            
            return (lower_bound, upper_bound)
            
        except Exception as e:
            self.logger.warning(f"Confidence interval calculation failed: {e}")
            # Default to ±10% of predicted value
            margin = concentration * 0.1
            return (max(0, concentration - margin), concentration + margin)
    
    def get_calibration_curve_data(self) -> Dict[str, Any]:
        """Get calibration curve data for visualization"""
        if not self.calibration_points:
            return {'concentrations': [], 'currents': [], 'curve_fit': []}
        
        concentrations = [point.concentration for point in self.calibration_points]
        currents = [point.current_response for point in self.calibration_points]
        
        # Generate curve fit points for visualization
        if self.is_calibrated:
            conc_range = np.linspace(min(concentrations), max(concentrations), 100)
            
            if SKLEARN_AVAILABLE and hasattr(self.calibration_curve, 'predict'):
                # This is simplified - actual implementation would depend on model type
                curve_currents = [c * self.model_performance.get('coefficients', {}).get('slope', 1.0) + 
                                self.model_performance.get('coefficients', {}).get('intercept', 0.0) 
                                for c in conc_range]
            else:
                slope = self.model_performance.get('coefficients', {}).get('slope', 1.0)
                intercept = self.model_performance.get('coefficients', {}).get('intercept', 0.0)
                curve_currents = [slope * c + intercept for c in conc_range]
            
            curve_fit = list(zip(conc_range, curve_currents))
        else:
            curve_fit = []
        
        return {
            'concentrations': concentrations,
            'currents': currents,
            'curve_fit': curve_fit,
            'r_squared': self.model_performance.get('r2', 0.0),
            'method': self.model_performance.get('method', 'none')
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive model information"""
        return {
            'sklearn_available': SKLEARN_AVAILABLE,
            'is_calibrated': self.is_calibrated,
            'calibration_points': len(self.calibration_points),
            'prediction_count': self.prediction_count,
            'model_performance': self.model_performance,
            'config': self.config
        }

# Demo function
def demo_concentration_prediction():
    """Demonstrate concentration prediction with synthetic calibration data"""
    print("📊 Concentration Prediction Demo")
    print("=" * 45)
    
    # Create predictor
    predictor = ConcentrationPredictor()
    
    # Add synthetic calibration points (typical linear relationship)
    calibration_data = [
        (1e-6, 2.1e-6),   # 1 μM → 2.1 μA
        (2e-6, 4.3e-6),   # 2 μM → 4.3 μA  
        (5e-6, 10.2e-6),  # 5 μM → 10.2 μA
        (10e-6, 20.5e-6), # 10 μM → 20.5 μA
        (20e-6, 41.1e-6), # 20 μM → 41.1 μA
    ]
    
    print("Adding calibration points...")
    for conc, current in calibration_data:
        predictor.add_calibration_point(conc, current)
        print(f"  {conc*1e6:.1f} μM → {current*1e6:.1f} μA")
    
    # Calibrate
    print(f"\nCalibrating with {len(calibration_data)} points...")
    cal_result = predictor.calibrate()
    
    if cal_result['success']:
        print(f"✅ Calibration successful!")
        print(f"  Method: {cal_result['best_model']}")
        print(f"  R²: {cal_result['r_squared']:.4f}")
        print(f"  RMSE: {cal_result['rmse']:.2e} A")
    else:
        print(f"❌ Calibration failed: {cal_result.get('error', 'Unknown error')}")
        return
    
    # Test predictions
    test_currents = [6.2e-6, 15.1e-6, 35.8e-6]  # Should predict ~3, ~7.5, ~17.5 μM
    
    print(f"\nTesting predictions:")
    for current in test_currents:
        try:
            result = predictor.predict_concentration(current)
            predicted_uM = result.predicted_concentration * 1e6
            confidence_uM = (result.confidence_interval[0] * 1e6, 
                           result.confidence_interval[1] * 1e6)
            
            print(f"  {current*1e6:.1f} μA → {predicted_uM:.2f} μM")
            print(f"    Confidence: {confidence_uM[0]:.2f} - {confidence_uM[1]:.2f} μM")
            print(f"    Method: {result.method_used}")
            
        except Exception as e:
            print(f"  Prediction failed: {e}")
    
    # Model info
    info = predictor.get_model_info()
    print(f"\nModel Summary:")
    print(f"  Calibration Points: {info['calibration_points']}")
    print(f"  Predictions Made: {info['prediction_count']}")
    print(f"  Sklearn Available: {info['sklearn_available']}")
    
    return predictor

if __name__ == "__main__":
    demo_concentration_prediction()
