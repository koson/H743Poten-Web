#!/usr/bin/env python3

"""
Cross-Instrument Calibration Validation System
Comprehensive validation metrics for calibration accuracy
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from scipy import stats
from scipy.stats import pearsonr, spearmanr
import warnings
warnings.filterwarnings('ignore')

def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj

class CalibrationValidator:
    """Comprehensive calibration validation system"""
    
    def __init__(self):
        self.validation_results = {}
        self.statistical_tests = {}
        self.improvement_metrics = {}
    
    def validate_calibration(self, original_data, calibrated_data, reference_data=None):
        """
        Comprehensive validation of calibration results
        
        Args:
            original_data: Original instrument data
            calibrated_data: Calibrated instrument data  
            reference_data: Reference/gold standard data (optional)
        """
        print("🔬 Starting Comprehensive Calibration Validation...")
        
        # 1. Basic Statistical Validation
        basic_stats = self._basic_statistical_validation(original_data, calibrated_data)
        
        # 2. Peak Analysis Validation
        peak_analysis = self._peak_analysis_validation(original_data, calibrated_data)
        
        # 3. Signal Quality Validation
        signal_quality = self._signal_quality_validation(original_data, calibrated_data)
        
        # 4. Correlation Analysis
        correlation_analysis = self._correlation_analysis(original_data, calibrated_data)
        
        # 5. Reference Comparison (if available)
        reference_validation = {}
        if reference_data is not None:
            reference_validation = self._reference_validation(
                original_data, calibrated_data, reference_data
            )
        
        # 6. Physical Plausibility Check
        plausibility_check = self._physical_plausibility_check(original_data, calibrated_data)
        
        # Compile all results
        validation_report = {
            'basic_statistics': basic_stats,
            'peak_analysis': peak_analysis,
            'signal_quality': signal_quality,
            'correlation_analysis': correlation_analysis,
            'reference_validation': reference_validation,
            'plausibility_check': plausibility_check,
            'overall_score': self._calculate_overall_score(
                basic_stats, peak_analysis, signal_quality, correlation_analysis
            )
        }
        
        self._print_validation_report(validation_report)
        # Convert numpy types to JSON-serializable types
        validation_report = convert_numpy_types(validation_report)
        return validation_report
    
    def _basic_statistical_validation(self, original, calibrated):
        """Basic statistical comparison"""
        print("\n📊 Basic Statistical Validation:")
        
        # Extract current values
        orig_current = np.array(original['current']) if 'current' in original else np.array(original['Current'])
        cal_current = np.array(calibrated['current']) if 'current' in calibrated else np.array(calibrated['Current'])
        
        # Statistical metrics
        stats_dict = {
            'original_mean': np.mean(orig_current),
            'calibrated_mean': np.mean(cal_current),
            'original_std': np.std(orig_current),
            'calibrated_std': np.std(cal_current),
            'mean_change_percent': ((np.mean(cal_current) - np.mean(orig_current)) / np.abs(np.mean(orig_current))) * 100,
            'std_change_percent': ((np.std(cal_current) - np.std(orig_current)) / np.std(orig_current)) * 100,
            'signal_preservation': 1 - np.abs((np.std(cal_current) - np.std(orig_current)) / np.std(orig_current))
        }
        
        print(f"  Original Mean: {stats_dict['original_mean']:.2e} A")
        print(f"  Calibrated Mean: {stats_dict['calibrated_mean']:.2e} A")
        print(f"  Mean Change: {stats_dict['mean_change_percent']:.1f}%")
        print(f"  Signal Preservation: {stats_dict['signal_preservation']:.3f}")
        
        return stats_dict
    
    def _peak_analysis_validation(self, original, calibrated):
        """Validate peak characteristics"""
        print("\n⛰️  Peak Analysis Validation:")
        
        orig_current = np.array(original['current']) if 'current' in original else np.array(original['Current'])
        cal_current = np.array(calibrated['current']) if 'current' in calibrated else np.array(calibrated['Current'])
        
        # Find peaks and valleys
        orig_max_idx = np.argmax(np.abs(orig_current))
        cal_max_idx = np.argmax(np.abs(cal_current))
        
        orig_peak = orig_current[orig_max_idx]
        cal_peak = cal_current[cal_max_idx]
        
        # Peak analysis
        peak_analysis = {
            'original_peak': orig_peak,
            'calibrated_peak': cal_peak,
            'peak_position_shift': abs(orig_max_idx - cal_max_idx),
            'peak_amplitude_change': ((cal_peak - orig_peak) / abs(orig_peak)) * 100,
            'peak_preservation': 1 - abs((cal_peak - orig_peak) / orig_peak)
        }
        
        print(f"  Original Peak: {peak_analysis['original_peak']:.2e} A")
        print(f"  Calibrated Peak: {peak_analysis['calibrated_peak']:.2e} A")
        print(f"  Peak Change: {peak_analysis['peak_amplitude_change']:.1f}%")
        print(f"  Position Shift: {peak_analysis['peak_position_shift']} points")
        
        return peak_analysis
    
    def _signal_quality_validation(self, original, calibrated):
        """Validate signal quality metrics"""
        print("\n📶 Signal Quality Validation:")
        
        orig_current = np.array(original['current']) if 'current' in original else np.array(original['Current'])
        cal_current = np.array(calibrated['current']) if 'current' in calibrated else np.array(calibrated['Current'])
        
        # Signal quality metrics
        def calculate_snr(signal):
            """Calculate Signal-to-Noise Ratio"""
            signal_power = np.mean(signal**2)
            noise_power = np.var(np.diff(signal))  # Estimate noise from derivatives
            return 10 * np.log10(signal_power / (noise_power + 1e-12))
        
        quality_metrics = {
            'original_snr': calculate_snr(orig_current),
            'calibrated_snr': calculate_snr(cal_current),
            'snr_improvement': calculate_snr(cal_current) - calculate_snr(orig_current),
            'smoothness_original': np.mean(np.abs(np.diff(orig_current, 2))),
            'smoothness_calibrated': np.mean(np.abs(np.diff(cal_current, 2))),
            'correlation_with_original': pearsonr(orig_current, cal_current)[0]
        }
        
        print(f"  Original SNR: {quality_metrics['original_snr']:.1f} dB")
        print(f"  Calibrated SNR: {quality_metrics['calibrated_snr']:.1f} dB")
        print(f"  SNR Improvement: {quality_metrics['snr_improvement']:.1f} dB")
        print(f"  Correlation: {quality_metrics['correlation_with_original']:.3f}")
        
        return quality_metrics
    
    def _correlation_analysis(self, original, calibrated):
        """Detailed correlation analysis"""
        print("\n🔗 Correlation Analysis:")
        
        orig_current = np.array(original['current']) if 'current' in original else np.array(original['Current'])
        cal_current = np.array(calibrated['current']) if 'current' in calibrated else np.array(calibrated['Current'])
        
        # Various correlation metrics
        pearson_corr, pearson_p = pearsonr(orig_current, cal_current)
        spearman_corr, spearman_p = spearmanr(orig_current, cal_current)
        
        correlation_stats = {
            'pearson_correlation': pearson_corr,
            'pearson_p_value': pearson_p,
            'spearman_correlation': spearman_corr,
            'spearman_p_value': spearman_p,
            'rmse': np.sqrt(mean_squared_error(orig_current, cal_current)),
            'mae': mean_absolute_error(orig_current, cal_current),
            'relative_error': np.mean(np.abs((cal_current - orig_current) / (orig_current + 1e-12))) * 100
        }
        
        print(f"  Pearson Correlation: {correlation_stats['pearson_correlation']:.3f} (p={correlation_stats['pearson_p_value']:.2e})")
        print(f"  Spearman Correlation: {correlation_stats['spearman_correlation']:.3f}")
        print(f"  RMSE: {correlation_stats['rmse']:.2e}")
        print(f"  Relative Error: {correlation_stats['relative_error']:.1f}%")
        
        return correlation_stats
    
    def _reference_validation(self, original, calibrated, reference):
        """Validate against reference data"""
        print("\n🎯 Reference Data Validation:")
        
        # Compare both original and calibrated against reference
        orig_current = np.array(original['current']) if 'current' in original else np.array(original['Current'])
        cal_current = np.array(calibrated['current']) if 'current' in calibrated else np.array(calibrated['Current'])
        ref_current = np.array(reference['current']) if 'current' in reference else np.array(reference['Current'])
        
        # Ensure same length for comparison
        min_len = min(len(orig_current), len(cal_current), len(ref_current))
        orig_current = orig_current[:min_len]
        cal_current = cal_current[:min_len]
        ref_current = ref_current[:min_len]
        
        reference_stats = {
            'original_vs_reference_corr': pearsonr(orig_current, ref_current)[0],
            'calibrated_vs_reference_corr': pearsonr(cal_current, ref_current)[0],
            'original_vs_reference_rmse': np.sqrt(mean_squared_error(ref_current, orig_current)),
            'calibrated_vs_reference_rmse': np.sqrt(mean_squared_error(ref_current, cal_current)),
            'improvement_in_correlation': pearsonr(cal_current, ref_current)[0] - pearsonr(orig_current, ref_current)[0],
            'improvement_in_rmse': np.sqrt(mean_squared_error(ref_current, orig_current)) - np.sqrt(mean_squared_error(ref_current, cal_current))
        }
        
        print(f"  Original vs Reference Correlation: {reference_stats['original_vs_reference_corr']:.3f}")
        print(f"  Calibrated vs Reference Correlation: {reference_stats['calibrated_vs_reference_corr']:.3f}")
        print(f"  Correlation Improvement: {reference_stats['improvement_in_correlation']:.3f}")
        print(f"  RMSE Improvement: {reference_stats['improvement_in_rmse']:.2e}")
        
        return reference_stats
    
    def _physical_plausibility_check(self, original, calibrated):
        """Check physical plausibility of calibration"""
        print("\n🔬 Physical Plausibility Check:")
        
        orig_current = np.array(original['current']) if 'current' in original else np.array(original['Current'])
        cal_current = np.array(calibrated['current']) if 'current' in calibrated else np.array(calibrated['Current'])
        
        # Physical checks
        plausibility = {
            'sign_preservation': np.sum(np.sign(orig_current) == np.sign(cal_current)) / len(orig_current),
            'magnitude_reasonable': np.all(np.abs(cal_current) < 10 * np.abs(orig_current).max()),
            'no_extreme_values': not np.any(np.isnan(cal_current)) and not np.any(np.isinf(cal_current)),
            'monotonicity_preservation': self._check_monotonicity_preservation(orig_current, cal_current),
            'dynamic_range_preservation': (np.max(cal_current) - np.min(cal_current)) / (np.max(orig_current) - np.min(orig_current))
        }
        
        print(f"  Sign Preservation: {plausibility['sign_preservation']:.1%}")
        print(f"  Magnitude Reasonable: {plausibility['magnitude_reasonable']}")
        print(f"  No Extreme Values: {plausibility['no_extreme_values']}")
        print(f"  Dynamic Range Ratio: {plausibility['dynamic_range_preservation']:.2f}")
        
        return plausibility
    
    def _check_monotonicity_preservation(self, original, calibrated):
        """Check if monotonic regions are preserved"""
        orig_diff = np.diff(original)
        cal_diff = np.diff(calibrated)
        
        # Count how many monotonic regions are preserved
        same_direction = np.sum(np.sign(orig_diff) == np.sign(cal_diff))
        return same_direction / len(orig_diff)
    
    def _calculate_overall_score(self, basic_stats, peak_analysis, signal_quality, correlation_analysis):
        """Calculate overall calibration quality score (0-100)"""
        
        # Weight different aspects
        weights = {
            'signal_preservation': 0.2,
            'peak_preservation': 0.2,
            'correlation': 0.3,
            'snr_improvement': 0.1,
            'low_error': 0.2
        }
        
        # Normalize metrics to 0-1 scale
        signal_score = max(0, min(1, basic_stats.get('signal_preservation', 0)))
        peak_score = max(0, min(1, peak_analysis.get('peak_preservation', 0)))
        correlation_score = max(0, min(1, correlation_analysis.get('pearson_correlation', 0)))
        snr_score = max(0, min(1, signal_quality.get('snr_improvement', 0) / 10))  # Normalize to 0-1
        error_score = max(0, min(1, 1 - correlation_analysis.get('relative_error', 100) / 100))
        
        overall_score = (
            weights['signal_preservation'] * signal_score +
            weights['peak_preservation'] * peak_score +
            weights['correlation'] * correlation_score +
            weights['snr_improvement'] * snr_score +
            weights['low_error'] * error_score
        ) * 100
        
        return overall_score
    
    def _print_validation_report(self, validation_report):
        """Print comprehensive validation report"""
        print("\n" + "="*60)
        print("🎯 CALIBRATION VALIDATION REPORT")
        print("="*60)
        
        overall_score = validation_report['overall_score']
        
        if overall_score >= 80:
            quality = "EXCELLENT ✅"
        elif overall_score >= 60:
            quality = "GOOD 👍"
        elif overall_score >= 40:
            quality = "FAIR ⚠️"
        else:
            quality = "POOR ❌"
        
        print(f"Overall Calibration Quality: {overall_score:.1f}/100 - {quality}")
        
        # Recommendations
        print("\n📋 RECOMMENDATIONS:")
        
        if validation_report['basic_statistics']['signal_preservation'] < 0.8:
            print("  ⚠️  Signal preservation is low - consider adjusting calibration parameters")
        
        if validation_report['signal_quality']['snr_improvement'] < 0:
            print("  ⚠️  SNR decreased after calibration - review noise handling")
        
        if validation_report['correlation_analysis']['pearson_correlation'] < 0.9:
            print("  ⚠️  Low correlation with original - verify calibration model")
        
        if validation_report['correlation_analysis']['relative_error'] > 20:
            print("  ⚠️  High relative error - consider model refinement")
        
        if overall_score >= 80:
            print("  ✅ Calibration is performing excellently!")
        elif overall_score >= 60:
            print("  👍 Calibration is performing well with minor improvements possible")
        else:
            print("  🔧 Calibration needs significant improvement")

if __name__ == "__main__":
    print("Cross-Instrument Calibration Validation System Ready! 🚀")
    print("Usage: validator = CalibrationValidator()")
    print("       results = validator.validate_calibration(original_data, calibrated_data)")
