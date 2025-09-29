"""
Cross-Instrument Calibration API Routes
Provides endpoints for real-time calibration between STM32 and PalmSens measurements
Based on production calibration service with cross-sample calibration data
"""

from flask import Blueprint, request, jsonify, current_app
from src.services.production_calibration_service import ProductionCalibrationService
from src.services.hybrid_data_manager import HybridDataManager
from datetime import datetime
import logging
import traceback
import json
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
def calibrate_measurement():
    """Calibrate a stored measurement by ID"""
    try:
        # Get measurement data
        cv_data = hybrid_manager.get_cv_data(measurement_id)
        
        if not cv_data:
            return jsonify({'error': f'No CV data found for measurement {measurement_id}'}), 404
        
        # Get measurement metadata (try to extract from parameter logger)
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
def compare_measurements():
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

try:
    from ..services.cross_instrument_calibrator import cross_instrument_calibrator, CalibrationDataSet
    from ..services.parameter_logging import parameter_logger
    from ..services.hybrid_data_manager import hybrid_manager
except ImportError:
    from services.cross_instrument_calibrator import cross_instrument_calibrator, CalibrationDataSet
    from services.parameter_logging import parameter_logger
    from services.hybrid_data_manager import hybrid_manager

logger = logging.getLogger(__name__)

# Create blueprint
calibration_api_bp = Blueprint('calibration_api', __name__, url_prefix='/api/calibration')

@calibration_api_bp.route('/parse-stm32', methods=['POST'])
def parse_stm32_data():
    """Parse STM32 CSV data into calibration format"""
    try:
        data = request.get_json()
        csv_data = data.get('csv_data', '')
        sample_id = data.get('sample_id', 'unknown')
        
        if not csv_data:
            return jsonify({
                'success': False,
                'error': 'No CSV data provided'
            }), 400
        
        # Parse STM32 data
        dataset = cross_instrument_calibrator.parse_stm32_data(csv_data, sample_id)
        
        # Convert to response format
        response_data = {
            'success': True,
            'dataset': {
                'measurement_mode': dataset.measurement_mode,
                'sample_id': dataset.sample_id,
                'instrument_type': dataset.instrument_type,
                'timestamp': dataset.timestamp.isoformat(),
                'scan_rate': dataset.scan_rate,
                'voltage_start': dataset.voltage_start,
                'voltage_end': dataset.voltage_end,
                'data_points_count': len(dataset.data_points) if dataset.data_points else 0,
                'cv_data_count': len(dataset.cv_data) if dataset.cv_data else 0
            },
            'cv_data': dataset.cv_data[:100] if dataset.cv_data else [],  # Limit for response size
            'preview_data': [
                {
                    'timestamp_us': point.timestamp_us,
                    're_voltage': point.re_voltage,
                    'we_voltage': point.we_voltage,
                    'we_current': point.we_current,
                    'we_current_range': point.we_current_range,
                    'cycle_no': point.cycle_no
                }
                for point in (dataset.data_points[:10] if dataset.data_points else [])
            ]
        }
        
        logger.info(f"Parsed STM32 data: {len(dataset.data_points)} points, mode={dataset.measurement_mode}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error parsing STM32 data: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@calibration_api_bp.route('/calibrate', methods=['POST'])
def perform_calibration():
    """Perform calibration between STM32 and PalmSens measurements"""
    try:
        data = request.get_json()
        stm32_measurement_id = data.get('stm32_measurement_id')
        palmsens_measurement_id = data.get('palmsens_measurement_id')
        stm32_csv_data = data.get('stm32_csv_data')  # Alternative: provide CSV directly
        
        if not stm32_measurement_id and not stm32_csv_data:
            return jsonify({
                'success': False,
                'error': 'Either stm32_measurement_id or stm32_csv_data must be provided'
            }), 400
            
        if not palmsens_measurement_id:
            return jsonify({
                'success': False,
                'error': 'palmsens_measurement_id is required'
            }), 400
        
        # Get PalmSens reference data
        palmsens_measurement = parameter_logger.get_measurement_by_id(palmsens_measurement_id)
        if not palmsens_measurement:
            return jsonify({
                'success': False,
                'error': f'PalmSens measurement {palmsens_measurement_id} not found'
            }), 404
        
        # Get PalmSens CV data
        try:
            palmsens_cv_data = hybrid_manager.get_measurement_data(palmsens_measurement_id)
        except:
            # Fallback to parameter logger
            palmsens_cv_data = parameter_logger.get_measurement_cv_data(palmsens_measurement_id)
            
        if not palmsens_cv_data:
            return jsonify({
                'success': False,
                'error': f'No CV data found for PalmSens measurement {palmsens_measurement_id}'
            }), 404
        
        # Create PalmSens dataset
        palmsens_dataset = CalibrationDataSet(
            measurement_mode='CV',  # Assume CV for now
            sample_id=palmsens_measurement['sample_id'],
            instrument_type='palmsens',
            timestamp=datetime.fromisoformat(palmsens_measurement['timestamp']),
            scan_rate=palmsens_measurement.get('scan_rate'),
            voltage_start=palmsens_measurement.get('voltage_start'),
            voltage_end=palmsens_measurement.get('voltage_end'),
            cv_data=palmsens_cv_data
        )
        
        # Get STM32 data
        if stm32_measurement_id:
            # Get from database
            stm32_measurement = parameter_logger.get_measurement_by_id(stm32_measurement_id)
            if not stm32_measurement:
                return jsonify({
                    'success': False,
                    'error': f'STM32 measurement {stm32_measurement_id} not found'
                }), 404
            
            # Get STM32 CV data
            try:
                stm32_cv_data = hybrid_manager.get_measurement_data(stm32_measurement_id)
            except:
                stm32_cv_data = parameter_logger.get_measurement_cv_data(stm32_measurement_id)
                
            if not stm32_cv_data:
                return jsonify({
                    'success': False,
                    'error': f'No CV data found for STM32 measurement {stm32_measurement_id}'
                }), 404
            
            # Create STM32 dataset
            stm32_dataset = CalibrationDataSet(
                measurement_mode='CV',
                sample_id=stm32_measurement['sample_id'],
                instrument_type='stm32',
                timestamp=datetime.fromisoformat(stm32_measurement['timestamp']),
                cv_data=stm32_cv_data
            )
        else:
            # Parse from CSV data
            stm32_dataset = cross_instrument_calibrator.parse_stm32_data(
                stm32_csv_data, palmsens_measurement['sample_id']
            )
        
        # Perform calibration
        calibration_result = cross_instrument_calibrator.calibrate_stm32_to_palmsens(
            stm32_dataset, palmsens_dataset
        )
        
        # Save calibration model
        models_file = "data_logs/calibration_models.json"
        cross_instrument_calibrator.save_calibration_models(models_file)
        
        logger.info(f"Calibration completed: STM32 {stm32_measurement_id or 'CSV'} vs PalmSens {palmsens_measurement_id}")
        return jsonify({
            'success': True,
            'calibration_result': calibration_result
        })
        
    except Exception as e:
        logger.error(f"Error performing calibration: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@calibration_api_bp.route('/apply/<int:measurement_id>', methods=['POST'])
def apply_calibration_to_measurement():
    """Apply stored calibration to a measurement"""
    try:
        measurement_id = int(measurement_id)
        data = request.get_json()
        calibration_model_key = data.get('calibration_model_key')
        
        # Get measurement
        measurement = parameter_logger.get_measurement_by_id(measurement_id)
        if not measurement:
            return jsonify({
                'success': False,
                'error': f'Measurement {measurement_id} not found'
            }), 404
        
        # Get CV data
        try:
            cv_data = hybrid_manager.get_measurement_data(measurement_id)
        except:
            cv_data = parameter_logger.get_measurement_cv_data(measurement_id)
            
        if not cv_data:
            return jsonify({
                'success': False,
                'error': f'No CV data found for measurement {measurement_id}'
            }), 404
        
        # Get calibration model
        if calibration_model_key:
            calibration_params = cross_instrument_calibrator.calibration_models.get(calibration_model_key)
        else:
            # Auto-detect calibration model
            model_key = f"CV_{measurement['sample_id']}"
            calibration_params = cross_instrument_calibrator.get_calibration_model('CV', measurement['sample_id'])
        
        if not calibration_params:
            return jsonify({
                'success': False,
                'error': 'No suitable calibration model found'
            }), 404
        
        # Apply calibration
        calibrated_data = cross_instrument_calibrator.apply_calibration(cv_data, calibration_params)
        
        return jsonify({
            'success': True,
            'original_data': cv_data,
            'calibrated_data': calibrated_data,
            'calibration_params': {
                'current_slope': calibration_params['current_slope'],
                'current_offset': calibration_params['current_offset'],
                'voltage_slope': calibration_params['voltage_slope'],
                'voltage_offset': calibration_params['voltage_offset'],
                'r_squared': calibration_params['r_squared'],
                'timestamp': calibration_params['timestamp'].isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error applying calibration: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@calibration_api_bp.route('/models', methods=['GET'])
def get_calibration_models():
    """Get all stored calibration models"""
    try:
        models_info = {}
        
        for key, model in cross_instrument_calibrator.calibration_models.items():
            models_info[key] = {
                'current_slope': model['current_slope'],
                'current_offset': model['current_offset'],
                'voltage_slope': model['voltage_slope'],
                'voltage_offset': model['voltage_offset'],
                'r_squared': model['r_squared'],
                'timestamp': model['timestamp'].isoformat(),
                'quality': 'excellent' if model['r_squared'] > 0.95 else 'good' if model['r_squared'] > 0.8 else 'fair'
            }
        
        return jsonify({
            'success': True,
            'models': models_info,
            'count': len(models_info)
        })
        
    except Exception as e:
        logger.error(f"Error getting calibration models: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@calibration_api_bp.route('/measurement-pairs', methods=['GET'])
def get_measurement_pairs():
    """Get available measurement pairs for calibration"""
    try:
        measurements = parameter_logger.get_measurements()
        
        # Group by sample_id
        samples = {}
        for m in measurements:
            sample_id = m['sample_id']
            if sample_id not in samples:
                samples[sample_id] = {'stm32': [], 'palmsens': []}
            
            instrument = m.get('instrument_type', 'unknown')
            if instrument in samples[sample_id]:
                samples[sample_id][instrument].append({
                    'id': m['id'],
                    'timestamp': m['timestamp'],
                    'scan_rate': m.get('scan_rate'),
                    'voltage_start': m.get('voltage_start'),
                    'voltage_end': m.get('voltage_end')
                })
        
        # Find pairs
        calibration_pairs = []
        for sample_id, instruments in samples.items():
            if instruments['stm32'] and instruments['palmsens']:
                for stm32_m in instruments['stm32']:
                    for palmsens_m in instruments['palmsens']:
                        calibration_pairs.append({
                            'sample_id': sample_id,
                            'stm32_measurement': stm32_m,
                            'palmsens_measurement': palmsens_m,
                            'time_difference_hours': abs(
                                (datetime.fromisoformat(stm32_m['timestamp']) - 
                                 datetime.fromisoformat(palmsens_m['timestamp'])).total_seconds() / 3600
                            )
                        })
        
        # Sort by time difference (closest measurements first)
        calibration_pairs.sort(key=lambda x: x['time_difference_hours'])
        
        return jsonify({
            'success': True,
            'pairs': calibration_pairs,
            'count': len(calibration_pairs)
        })
        
    except Exception as e:
        logger.error(f"Error getting measurement pairs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500