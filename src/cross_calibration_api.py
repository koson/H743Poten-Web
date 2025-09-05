#!/usr/bin/env python3
"""
Cross-Instrument Calibration API Integration
รวมเข้ากับ Flask application หลัก

Author: H743Poten Team
Date: September 6, 2025
"""

from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
import json
import logging
from pathlib import Path

from src.cross_instrument_calibration import CrossInstrumentCalibrator

# Setup logging
logger = logging.getLogger(__name__)

# Create Blueprint
cross_cal_bp = Blueprint('cross_calibration', __name__, url_prefix='/api/calibration')

# Global calibrator instance
calibrator = None

def init_calibration_system():
    """Initialize the calibration system"""
    global calibrator
    try:
        calibrator = CrossInstrumentCalibrator()
        logger.info("Cross-instrument calibration system initialized")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize calibration system: {e}")
        return False

@cross_cal_bp.route('/status', methods=['GET'])
def get_calibration_status():
    """Get overall calibration system status"""
    try:
        if calibrator is None:
            return jsonify({
                'status': 'error',
                'message': 'Calibration system not initialized'
            }), 500
        
        # Get basic status information
        status_data = {
            'status': 'active',
            'timestamp': datetime.now().isoformat(),
            'instruments_count': len(calibrator.instruments),
            'correction_factors_count': len(calibrator.correction_factors),
            'database_path': str(calibrator.cross_cal_db)
        }
        
        return jsonify({
            'status': 'success',
            'data': status_data
        })
        
    except Exception as e:
        logger.error(f"Error getting calibration status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@cross_cal_bp.route('/instruments', methods=['GET'])
def get_instruments():
    """Get list of registered instruments"""
    try:
        if calibrator is None:
            return jsonify({
                'status': 'error',
                'message': 'Calibration system not initialized'
            }), 500
        
        return jsonify({
            'status': 'success',
            'data': {
                'instruments': calibrator.instruments,
                'count': len(calibrator.instruments)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting instruments: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@cross_cal_bp.route('/instruments/register', methods=['POST'])
def register_instrument():
    """Register a new instrument"""
    try:
        if calibrator is None:
            return jsonify({
                'status': 'error',
                'message': 'Calibration system not initialized'
            }), 500
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['instrument_id', 'instrument_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Register instrument
        success = calibrator.register_instrument(
            instrument_id=data['instrument_id'],
            instrument_type=data['instrument_type'],
            serial_number=data.get('serial_number')
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f"Instrument {data['instrument_id']} registered successfully"
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to register instrument'
            }), 500
            
    except Exception as e:
        logger.error(f"Error registering instrument: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@cross_cal_bp.route('/load_existing_data', methods=['POST'])
def load_existing_data():
    """Load existing calibration data from previous steps"""
    try:
        if calibrator is None:
            return jsonify({
                'status': 'error',
                'message': 'Calibration system not initialized'
            }), 500
        
        # Load existing calibration data
        calibration_data = calibrator.load_existing_calibration_data()
        
        return jsonify({
            'status': 'success',
            'message': 'Existing calibration data loaded successfully',
            'data': {
                'sections_loaded': list(calibration_data.keys()),
                'models_count': len(calibration_data.get('models', {})),
                'has_cross_comparison': 'cross_comparison' in calibration_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error loading existing data: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@cross_cal_bp.route('/calculate_corrections', methods=['POST'])
def calculate_corrections():
    """Calculate correction factors from loaded data"""
    try:
        if calibrator is None:
            return jsonify({
                'status': 'error',
                'message': 'Calibration system not initialized'
            }), 500
        
        # Load calibration data first
        calibration_data = calibrator.load_existing_calibration_data()
        
        # Calculate correction factors
        correction_factors = calibrator.calculate_correction_factors(calibration_data)
        
        return jsonify({
            'status': 'success',
            'message': 'Correction factors calculated successfully',
            'data': {
                'instruments_processed': list(correction_factors.keys()),
                'total_factors': len(correction_factors)
            }
        })
        
    except Exception as e:
        logger.error(f"Error calculating corrections: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@cross_cal_bp.route('/corrections/<instrument_id>/<parameter_type>', methods=['GET'])
def get_correction_factors(instrument_id, parameter_type):
    """Get correction factors for specific instrument and parameter"""
    try:
        if calibrator is None:
            return jsonify({
                'status': 'error',
                'message': 'Calibration system not initialized'
            }), 500
        
        factors = calibrator.get_correction_factors(instrument_id, parameter_type)
        
        if factors:
            return jsonify({
                'status': 'success',
                'data': {
                    'instrument_id': instrument_id,
                    'parameter_type': parameter_type,
                    'correction_factors': factors
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'No correction factors found for {instrument_id}.{parameter_type}'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting correction factors: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@cross_cal_bp.route('/apply_correction', methods=['POST'])
def apply_correction():
    """Apply correction to a measurement value"""
    try:
        if calibrator is None:
            return jsonify({
                'status': 'error',
                'message': 'Calibration system not initialized'
            }), 500
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['instrument_id', 'parameter_type', 'raw_value']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Apply correction
        corrected_value = calibrator.apply_correction(
            instrument_id=data['instrument_id'],
            parameter_type=data['parameter_type'],
            raw_value=float(data['raw_value'])
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'instrument_id': data['instrument_id'],
                'parameter_type': data['parameter_type'],
                'raw_value': data['raw_value'],
                'corrected_value': corrected_value,
                'correction_applied': corrected_value != data['raw_value']
            }
        })
        
    except Exception as e:
        logger.error(f"Error applying correction: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@cross_cal_bp.route('/validate', methods=['POST'])
def validate_calibration():
    """Validate the calibration system"""
    try:
        if calibrator is None:
            return jsonify({
                'status': 'error',
                'message': 'Calibration system not initialized'
            }), 500
        
        # Load calibration data
        calibration_data = calibrator.load_existing_calibration_data()
        
        # Validate calibration
        validation_results = calibrator.validate_calibration(calibration_data)
        
        return jsonify({
            'status': 'success',
            'data': validation_results
        })
        
    except Exception as e:
        logger.error(f"Error validating calibration: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@cross_cal_bp.route('/report', methods=['GET'])
def generate_report():
    """Generate calibration report"""
    try:
        if calibrator is None:
            return jsonify({
                'status': 'error',
                'message': 'Calibration system not initialized'
            }), 500
        
        # Load calibration data and validate
        calibration_data = calibrator.load_existing_calibration_data()
        validation_results = calibrator.validate_calibration(calibration_data)
        
        # Generate report
        report_html = calibrator.generate_calibration_report(validation_results)
        
        # Save report
        report_path = Path("data_logs") / "cross_calibration_report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        return jsonify({
            'status': 'success',
            'message': 'Calibration report generated successfully',
            'data': {
                'report_path': str(report_path),
                'validation_status': validation_results['overall_status'],
                'timestamp': validation_results['timestamp']
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@cross_cal_bp.route('/dashboard', methods=['GET'])
def calibration_dashboard():
    """Return calibration dashboard page"""
    try:
        return render_template('calibration_dashboard.html')
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return f"Error loading calibration dashboard: {e}", 500

# Batch processing endpoints
@cross_cal_bp.route('/batch/full_calibration', methods=['POST'])
def full_calibration_process():
    """Execute complete calibration process"""
    try:
        if calibrator is None:
            return jsonify({
                'status': 'error',
                'message': 'Calibration system not initialized'
            }), 500
        
        results = {}
        
        # Step 1: Load existing data
        calibration_data = calibrator.load_existing_calibration_data()
        results['data_loading'] = {
            'success': True,
            'sections_loaded': list(calibration_data.keys())
        }
        
        # Step 2: Calculate correction factors
        correction_factors = calibrator.calculate_correction_factors(calibration_data)
        results['correction_calculation'] = {
            'success': True,
            'instruments_processed': list(correction_factors.keys())
        }
        
        # Step 3: Validate calibration
        validation_results = calibrator.validate_calibration(calibration_data)
        results['validation'] = validation_results
        
        # Step 4: Generate report
        report_html = calibrator.generate_calibration_report(validation_results)
        report_path = Path("data_logs") / f"cross_calibration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        results['report_generation'] = {
            'success': True,
            'report_path': str(report_path)
        }
        
        return jsonify({
            'status': 'success',
            'message': 'Full calibration process completed successfully',
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Error in full calibration process: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Helper function to register with main Flask app
def register_calibration_api(app):
    """Register calibration API with Flask app"""
    try:
        app.register_blueprint(cross_cal_bp)
        
        # Initialize calibration system
        if init_calibration_system():
            logger.info("Cross-instrument calibration API registered successfully")
            return True
        else:
            logger.error("Failed to initialize calibration system")
            return False
            
    except Exception as e:
        logger.error(f"Error registering calibration API: {e}")
        return False
