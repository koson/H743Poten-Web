"""
Simple Calibration Validator
No external dependencies required
"""
import numpy as np
import pandas as pd

class SimpleCalibrationValidator:
    """Simple calibration validator without SciPy dependencies"""
    
    def validate_calibration(self, original_data, calibrated_data, reference_data=None):
        """
        Simple validation using basic statistics
        """
        try:
            results = {
                'overall_quality_score': 0,
                'validation_passed': False,
                'metrics': {},
                'errors': []
            }
            
            # Basic data validation
            if len(original_data) == 0 or len(calibrated_data) == 0:
                results['errors'].append('Empty data provided')
                return results
            
            # Get current columns
            orig_current = self._get_current_column(original_data)
            cal_current = self._get_current_column(calibrated_data)
            
            if orig_current is None or cal_current is None:
                results['errors'].append('Current column not found')
                return results
            
            # Basic statistical metrics
            correlation = self._calculate_correlation(orig_current, cal_current)
            rmse = self._calculate_rmse(orig_current, cal_current)
            relative_error = self._calculate_relative_error(orig_current, cal_current)
            signal_preservation = self._calculate_signal_preservation(orig_current, cal_current)
            
            # Store metrics
            results['metrics'] = {
                'correlation': correlation,
                'rmse': rmse,
                'relative_error': relative_error,
                'signal_preservation': signal_preservation
            }
            
            # Calculate overall quality score
            quality_score = 0
            score_components = 0
            
            if correlation is not None:
                quality_score += max(0, correlation * 100)
                score_components += 1
            
            if signal_preservation is not None:
                quality_score += signal_preservation
                score_components += 1
            
            if relative_error is not None:
                # Lower error is better, so invert
                error_score = max(0, 100 - relative_error)
                quality_score += error_score
                score_components += 1
            
            if score_components > 0:
                results['overall_quality_score'] = quality_score / score_components
            
            # Validation criteria
            results['validation_passed'] = (
                (correlation is None or correlation > 0.8) and
                (relative_error is None or relative_error < 20) and
                (signal_preservation is None or signal_preservation > 80)
            )
            
            return results
            
        except Exception as e:
            return {
                'overall_quality_score': 0,
                'validation_passed': False,
                'metrics': {},
                'errors': [f'Validation error: {str(e)}']
            }
    
    def _get_current_column(self, data):
        """Get current column from dataframe"""
        possible_names = ['current', 'Current', 'I', 'i', 'Current (A)', 'Current(A)']
        
        for col_name in possible_names:
            if col_name in data.columns:
                return np.array(data[col_name])
        
        return None
    
    def _calculate_correlation(self, x, y):
        """Calculate correlation coefficient"""
        try:
            if len(x) != len(y) or len(x) < 2:
                return None
            
            # Remove NaN values
            mask = ~(np.isnan(x) | np.isnan(y))
            x_clean = x[mask]
            y_clean = y[mask]
            
            if len(x_clean) < 2:
                return None
            
            # Calculate correlation manually
            mean_x = np.mean(x_clean)
            mean_y = np.mean(y_clean)
            
            numerator = np.sum((x_clean - mean_x) * (y_clean - mean_y))
            denominator_x = np.sum((x_clean - mean_x) ** 2)
            denominator_y = np.sum((y_clean - mean_y) ** 2)
            
            if denominator_x == 0 or denominator_y == 0:
                return None
            
            correlation = numerator / np.sqrt(denominator_x * denominator_y)
            return float(correlation)
            
        except:
            return None
    
    def _calculate_rmse(self, x, y):
        """Calculate root mean square error"""
        try:
            if len(x) != len(y) or len(x) == 0:
                return None
            
            # Remove NaN values
            mask = ~(np.isnan(x) | np.isnan(y))
            x_clean = x[mask]
            y_clean = y[mask]
            
            if len(x_clean) == 0:
                return None
            
            mse = np.mean((x_clean - y_clean) ** 2)
            return float(np.sqrt(mse))
            
        except:
            return None
    
    def _calculate_relative_error(self, x, y):
        """Calculate relative error as percentage"""
        try:
            if len(x) != len(y) or len(x) == 0:
                return None
            
            # Remove NaN values
            mask = ~(np.isnan(x) | np.isnan(y))
            x_clean = x[mask]
            y_clean = y[mask]
            
            if len(x_clean) == 0:
                return None
            
            # Calculate mean absolute relative error
            x_abs = np.abs(x_clean)
            mask_nonzero = x_abs > 1e-10  # Avoid division by very small numbers
            
            if np.sum(mask_nonzero) == 0:
                return None
            
            relative_errors = np.abs(x_clean[mask_nonzero] - y_clean[mask_nonzero]) / x_abs[mask_nonzero]
            mean_relative_error = np.mean(relative_errors) * 100  # Convert to percentage
            
            return float(mean_relative_error)
            
        except:
            return None
    
    def _calculate_signal_preservation(self, x, y):
        """Calculate how well the signal shape is preserved"""
        try:
            if len(x) != len(y) or len(x) < 3:
                return None
            
            # Remove NaN values
            mask = ~(np.isnan(x) | np.isnan(y))
            x_clean = x[mask]
            y_clean = y[mask]
            
            if len(x_clean) < 3:
                return None
            
            # Calculate signal ranges
            x_range = np.max(x_clean) - np.min(x_clean)
            y_range = np.max(y_clean) - np.min(y_clean)
            
            if x_range == 0:
                return 100.0 if y_range == 0 else 0.0
            
            # Calculate how well the range is preserved
            range_preservation = min(x_range, y_range) / max(x_range, y_range) * 100
            
            # Calculate signal variance preservation
            x_var = np.var(x_clean)
            y_var = np.var(y_clean)
            
            if x_var == 0:
                variance_preservation = 100.0 if y_var == 0 else 0.0
            else:
                variance_preservation = min(x_var, y_var) / max(x_var, y_var) * 100
            
            # Average of range and variance preservation
            signal_preservation = (range_preservation + variance_preservation) / 2
            
            return float(signal_preservation)
            
        except:
            return None
