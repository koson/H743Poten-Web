"""
Production Cross-Instrument Calibration API Routes
Provides endpoints for real-time calibration between STM32 and PalmSens measurements
Based on production calibration service with cross-sample calibration data
"""

from flask import Blueprint, request, jsonify
from src.services.production_calibration_service import ProductionCalibrationService
from src.services.hybrid_data_manager import HybridDataManager
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Create blueprint
calibration_bp = Blueprint('calibration', __name__, url_prefix='/api/calibration')

# Initialize services
cal_service = ProductionCalibrationService()
hybrid_manager = HybridDataManager()

@calibration_bp.route('/current', methods=['POST'])
def calibrate_current():
    """Calibrate a single current value from STM32 to PalmSens equivalent"""
    try:
        data = request.get_json()
        
        # Validate input
        if 'stm32_current' not in data:
            return jsonify({'error': 'stm32_current is required'}), 400
        
        stm32_current = float(data['stm32_current'])
        scan_rate = data.get('scan_rate')
        concentration = data.get('concentration')
        
        # Perform calibration
        result = cal_service.calibrate_current_stm32_to_palmsens(
            stm32_current, scan_rate, concentration
        )
        
        return jsonify({
            'success': True,
            'calibration': result
        })
        
    except Exception as e:
        logger.error(f"Error in current calibration: {e}")
        return jsonify({'error': str(e)}), 500

@calibration_bp.route('/cv-curve', methods=['POST'])
def calibrate_cv_curve():
    """Calibrate an entire CV curve from STM32 to PalmSens equivalent"""
    try:
        data = request.get_json()
        
        # Validate input
        if 'cv_data' not in data:
            return jsonify({'error': 'cv_data is required'}), 400
        
        cv_data = data['cv_data']
        scan_rate = data.get('scan_rate')
        concentration = data.get('concentration')
        
        # Validate CV data format
        if not isinstance(cv_data, list) or not cv_data:
            return jsonify({'error': 'cv_data must be a non-empty list'}), 400
        
        # Check first point format
        if not isinstance(cv_data[0], list) or len(cv_data[0]) < 2:
            return jsonify({'error': 'cv_data must be list of [voltage, current] pairs'}), 400
        
        # Perform calibration
        result = cal_service.calibrate_cv_curve(cv_data, scan_rate, concentration)
        
        return jsonify({
            'success': True,
            'calibration': result
        })
        
    except Exception as e:
        logger.error(f"Error in CV curve calibration: {e}")
        return jsonify({'error': str(e)}), 500

@calibration_bp.route('/measurement/<int:measurement_id>', methods=['POST'])
def calibrate_measurement(measurement_id):
    """Calibrate a stored measurement by ID"""
    try:
        # Get measurement data
        cv_data = hybrid_manager.get_cv_data(measurement_id)
        
        if not cv_data:
            return jsonify({'error': f'No CV data found for measurement {measurement_id}'}), 404
        
        # Get measurement metadata
        from src.services.parameter_logging import ParameterLogger
        logger_service = ParameterLogger()
        
        try:
            measurement = logger_service.get_measurement_by_id(measurement_id)
            scan_rate = measurement.get('scan_rate') if measurement else None
            
            # Try to extract concentration from sample_id
            concentration = None
            if measurement and 'sample_id' in measurement:
                sample_id = measurement['sample_id']
                if 'mM' in sample_id:
                    try:
                        conc_str = sample_id.split('mM')[0].strip()
                        concentration = float(conc_str) if conc_str.replace('.', '').isdigit() else None
                    except:
                        pass
        except:
            scan_rate = None
            concentration = None
        
        # Perform calibration
        result = cal_service.calibrate_cv_curve(cv_data, scan_rate, concentration)
        
        # Add measurement info
        result['measurement_info'] = {
            'id': measurement_id,
            'scan_rate': scan_rate,
            'concentration': concentration,
            'original_data_points': len(cv_data)
        }
        
        return jsonify({
            'success': True,
            'calibration': result
        })
        
    except Exception as e:
        logger.error(f"Error calibrating measurement {measurement_id}: {e}")
        return jsonify({'error': str(e)}), 500

@calibration_bp.route('/info', methods=['GET'])
def get_calibration_info():
    """Get information about available calibrations and statistics"""
    try:
        available_calibrations = cal_service.get_available_calibrations()
        stats = cal_service.get_calibration_stats()
        
        return jsonify({
            'success': True,
            'available_calibrations': available_calibrations,
            'statistics': stats,
            'service_info': {
                'default_gain_factor': cal_service.default_gain,
                'default_offset': cal_service.default_offset,
                'confidence_levels': cal_service.confidence_levels
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting calibration info: {e}")
        return jsonify({'error': str(e)}), 500

@calibration_bp.route('/compare/<int:stm32_id>/<int:palmsens_id>', methods=['GET'])
def compare_measurements(stm32_id, palmsens_id):
    """Compare STM32 and PalmSens measurements with calibration"""
    try:
        # Get CV data for both measurements
        stm32_cv = hybrid_manager.get_cv_data(stm32_id)
        palmsens_cv = hybrid_manager.get_cv_data(palmsens_id)
        
        if not stm32_cv:
            return jsonify({'error': f'No STM32 CV data found for measurement {stm32_id}'}), 404
        if not palmsens_cv:
            return jsonify({'error': f'No PalmSens CV data found for measurement {palmsens_id}'}), 404
        
        # Get measurement metadata
        from src.services.parameter_logging import ParameterLogger
        logger_service = ParameterLogger()
        
        try:
            stm32_meta = logger_service.get_measurement_by_id(stm32_id)
            palmsens_meta = logger_service.get_measurement_by_id(palmsens_id)
            
            # Extract conditions from STM32 measurement
            scan_rate = stm32_meta.get('scan_rate') if stm32_meta else None
            concentration = None
            if stm32_meta and 'sample_id' in stm32_meta:
                sample_id = stm32_meta['sample_id']
                if 'mM' in sample_id:
                    try:
                        conc_str = sample_id.split('mM')[0].strip()
                        concentration = float(conc_str) if conc_str.replace('.', '').isdigit() else None
                    except:
                        pass
        except:
            stm32_meta = palmsens_meta = None
            scan_rate = concentration = None
        
        # Calibrate STM32 data
        calibration_result = cal_service.calibrate_cv_curve(stm32_cv, scan_rate, concentration)
        
        # Calculate comparison metrics
        # Extract current arrays
        stm32_currents = np.array([point[1] for point in stm32_cv])
        calibrated_currents = np.array([point[1] for point in calibration_result['calibrated_data']])
        palmsens_currents = np.array([point[1] for point in palmsens_cv])
        
        # Align lengths for comparison
        min_len = min(len(calibrated_currents), len(palmsens_currents))
        cal_aligned = calibrated_currents[:min_len]
        ref_aligned = palmsens_currents[:min_len]
        
        # Calculate correlation
        correlation = np.corrcoef(cal_aligned, ref_aligned)[0, 1] if min_len > 1 else 0
        
        # Calculate RMSE
        rmse = np.sqrt(np.mean((cal_aligned - ref_aligned) ** 2))
        
        return jsonify({
            'success': True,
            'comparison': {
                'stm32_id': stm32_id,
                'palmsens_id': palmsens_id,
                'correlation': float(correlation),
                'rmse': float(rmse),
                'data_points_compared': min_len
            },
            'data': {
                'stm32_original': stm32_cv,
                'stm32_calibrated': calibration_result['calibrated_data'],
                'palmsens_reference': palmsens_cv
            },
            'calibration_info': calibration_result.get('calibration_info', {}),
            'metadata': {
                'stm32': stm32_meta,
                'palmsens': palmsens_meta
            }
        })
        
    except Exception as e:
        logger.error(f"Error comparing measurements {stm32_id} vs {palmsens_id}: {e}")
        return jsonify({'error': str(e)}), 500

@calibration_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for calibration service"""
    try:
        stats = cal_service.get_calibration_stats()
        return jsonify({
            'success': True,
            'status': 'healthy',
            'calibration_conditions': stats['total_conditions'],
            'service_ready': True
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': str(e)
        }), 500