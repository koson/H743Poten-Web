#!/usr/bin/env python3
"""
Web Integration for Precision Peak/Baseline Detection and PLS Analysis
=====================================================================

รวมระบบ precision peak/baseline detection และ PLS analysis เข้ากับ web interface
สำหรับการใช้งานในสภาพแวดล้อม production

Features:
- RESTful API endpoints for precision analysis
- PLS model management via web interface
- Real-time concentration prediction
- Quality assessment and reporting
- Batch processing capabilities
"""

from flask import Blueprint, request, jsonify, current_app
import numpy as np
import pandas as pd
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import tempfile

# Import our precision systems
try:
    from precision_peak_baseline_analyzer import PrecisionPeakBaselineAnalyzer
    PRECISION_ANALYZER_AVAILABLE = True
except ImportError:
    PRECISION_ANALYZER_AVAILABLE = False

try:
    from advanced_pls_analyzer import AdvancedPLSAnalyzer
    PLS_ANALYZER_AVAILABLE = True
except ImportError:
    PLS_ANALYZER_AVAILABLE = False

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint
precision_pls_bp = Blueprint('precision_pls', __name__, url_prefix='/api/precision')

# Global instances (in production, these would be properly managed)
precision_analyzer = None
pls_analyzer = None

def initialize_analyzers():
    """Initialize the analyzer instances"""
    global precision_analyzer, pls_analyzer
    
    if PRECISION_ANALYZER_AVAILABLE and precision_analyzer is None:
        precision_analyzer = PrecisionPeakBaselineAnalyzer({
            'analyte': 'ferrocene',
            'confidence_threshold': 85.0,
            'quality_threshold': 80.0
        })
        logger.info("Precision analyzer initialized")
    
    if PLS_ANALYZER_AVAILABLE and pls_analyzer is None:
        pls_analyzer = AdvancedPLSAnalyzer({
            'quality_threshold': 80.0,
            'min_calibration_points': 5
        })
        logger.info("PLS analyzer initialized")

@precision_pls_bp.route('/status', methods=['GET'])
def get_system_status():
    """Get system status and capabilities"""
    
    status = {
        'timestamp': datetime.now().isoformat(),
        'precision_analyzer_available': PRECISION_ANALYZER_AVAILABLE,
        'pls_analyzer_available': PLS_ANALYZER_AVAILABLE,
        'initialized': False
    }
    
    if PRECISION_ANALYZER_AVAILABLE and PLS_ANALYZER_AVAILABLE:
        initialize_analyzers()
        status['initialized'] = True
        
        if pls_analyzer:
            status['calibration_points'] = len(pls_analyzer.calibration_data)
            status['trained_models'] = len(pls_analyzer.models)
    
    return jsonify(status)

@precision_pls_bp.route('/analyze', methods=['POST'])
def analyze_cv_data():
    """
    Perform precision peak and baseline analysis on CV data
    
    Expected JSON payload:
    {
        "voltage": [array of voltage values],
        "current": [array of current values],
        "filename": "optional filename",
        "analyte": "optional analyte type",
        "config": {optional configuration overrides}
    }
    """
    
    try:
        if not PRECISION_ANALYZER_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Precision analyzer not available'
            }), 400
        
        initialize_analyzers()
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract data
        voltage = np.array(data.get('voltage', []))
        current = np.array(data.get('current', []))
        filename = data.get('filename', 'web_upload')
        analyte = data.get('analyte', 'ferrocene')
        config_override = data.get('config', {})
        
        if len(voltage) == 0 or len(current) == 0:
            return jsonify({
                'success': False,
                'error': 'Empty voltage or current data'
            }), 400
        
        if len(voltage) != len(current):
            return jsonify({
                'success': False,
                'error': 'Voltage and current arrays must have same length'
            }), 400
        
        # Update analyzer config if provided
        if config_override:
            for key, value in config_override.items():
                precision_analyzer.config[key] = value
        
        # Run precision analysis
        logger.info(f"Running precision analysis on {filename}")
        
        results = precision_analyzer.analyze_cv_data(
            voltage, current, filename=filename, analyte=analyte
        )
        
        # Add API metadata
        results['api_version'] = '1.0.0'
        results['endpoint'] = '/api/precision/analyze'
        results['processing_time'] = datetime.now().isoformat()
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Precision analysis failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@precision_pls_bp.route('/calibration/add', methods=['POST'])
def add_calibration_point():
    """
    Add a calibration point for PLS model building
    
    Expected JSON payload:
    {
        "voltage": [array of voltage values],
        "current": [array of current values],
        "concentration": float (in M),
        "filename": "optional filename",
        "conditions": {optional measurement conditions}
    }
    """
    
    try:
        if not PLS_ANALYZER_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'PLS analyzer not available'
            }), 400
        
        initialize_analyzers()
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract data
        voltage = np.array(data.get('voltage', []))
        current = np.array(data.get('current', []))
        concentration = data.get('concentration')
        filename = data.get('filename', 'web_calibration')
        conditions = data.get('conditions', {})
        
        if concentration is None:
            return jsonify({
                'success': False,
                'error': 'Concentration is required'
            }), 400
        
        if len(voltage) == 0 or len(current) == 0:
            return jsonify({
                'success': False,
                'error': 'Empty voltage or current data'
            }), 400
        
        # Add calibration point
        success = pls_analyzer.add_calibration_point(
            voltage, current, concentration, filename, conditions
        )
        
        if success:
            response = {
                'success': True,
                'message': 'Calibration point added successfully',
                'total_calibration_points': len(pls_analyzer.calibration_data),
                'concentration_uM': concentration * 1e6,
                'filename': filename
            }
        else:
            response = {
                'success': False,
                'error': 'Failed to add calibration point (check data quality)'
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Add calibration point failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@precision_pls_bp.route('/calibration/status', methods=['GET'])
def get_calibration_status():
    """Get current calibration status"""
    
    try:
        if not PLS_ANALYZER_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'PLS analyzer not available'
            }), 400
        
        initialize_analyzers()
        
        calibration_data = []
        if pls_analyzer.calibration_data:
            for point in pls_analyzer.calibration_data:
                calibration_data.append({
                    'concentration_M': point.concentration,
                    'concentration_uM': point.concentration * 1e6,
                    'filename': point.filename,
                    'quality_score': point.quality_score,
                    'timestamp': point.timestamp.isoformat()
                })
        
        status = {
            'success': True,
            'total_points': len(pls_analyzer.calibration_data),
            'min_required': pls_analyzer.config['min_calibration_points'],
            'ready_for_modeling': len(pls_analyzer.calibration_data) >= pls_analyzer.config['min_calibration_points'],
            'calibration_data': calibration_data
        }
        
        if calibration_data:
            concentrations = [p['concentration_M'] for p in calibration_data]
            status['concentration_range'] = {
                'min_M': min(concentrations),
                'max_M': max(concentrations),
                'min_uM': min(concentrations) * 1e6,
                'max_uM': max(concentrations) * 1e6
            }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Get calibration status failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@precision_pls_bp.route('/model/build', methods=['POST'])
def build_pls_model():
    """
    Build PLS model from calibration data
    
    Expected JSON payload:
    {
        "model_id": "optional model identifier",
        "features": ["optional list of features to use"]
    }
    """
    
    try:
        if not PLS_ANALYZER_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'PLS analyzer not available'
            }), 400
        
        initialize_analyzers()
        
        data = request.get_json() or {}
        model_id = data.get('model_id')
        feature_subset = data.get('features')
        
        if len(pls_analyzer.calibration_data) < pls_analyzer.config['min_calibration_points']:
            return jsonify({
                'success': False,
                'error': f'Insufficient calibration data: {len(pls_analyzer.calibration_data)} < {pls_analyzer.config["min_calibration_points"]}'
            }), 400
        
        # Build model
        model = pls_analyzer.build_pls_model(model_id, feature_subset)
        
        if model:
            response = {
                'success': True,
                'model_id': model.model_id,
                'optimal_components': model.optimal_components,
                'r2_score': model.model_metrics['r2_score'],
                'rmse': model.model_metrics['rmse'],
                'relative_rmse_percent': model.model_metrics['relative_rmse_percent'],
                'n_calibration_points': len(model.calibration_points),
                'features_used': model.feature_names,
                'feature_importance': model.feature_importance,
                'created_timestamp': model.created_timestamp.isoformat()
            }
        else:
            response = {
                'success': False,
                'error': 'Failed to build PLS model'
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Build PLS model failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@precision_pls_bp.route('/model/list', methods=['GET'])
def list_pls_models():
    """List all available PLS models"""
    
    try:
        if not PLS_ANALYZER_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'PLS analyzer not available'
            }), 400
        
        initialize_analyzers()
        
        models = []
        for model_id, model in pls_analyzer.models.items():
            models.append({
                'model_id': model.model_id,
                'r2_score': model.model_metrics['r2_score'],
                'rmse': model.model_metrics['rmse'],
                'optimal_components': model.optimal_components,
                'n_features': len(model.feature_names),
                'n_calibration_points': len(model.calibration_points),
                'created_timestamp': model.created_timestamp.isoformat()
            })
        
        # Sort by R² score (best first)
        models.sort(key=lambda x: x['r2_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'models': models,
            'total_models': len(models)
        })
        
    except Exception as e:
        logger.error(f"List PLS models failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@precision_pls_bp.route('/model/validate/<model_id>', methods=['POST'])
def validate_pls_model(model_id):
    """Validate a specific PLS model"""
    
    try:
        if not PLS_ANALYZER_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'PLS analyzer not available'
            }), 400
        
        initialize_analyzers()
        
        validation_results = pls_analyzer.validate_model(model_id)
        return jsonify(validation_results)
        
    except Exception as e:
        logger.error(f"Validate PLS model failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@precision_pls_bp.route('/predict', methods=['POST'])
def predict_concentration():
    """
    Predict concentration from CV data using trained PLS model
    
    Expected JSON payload:
    {
        "voltage": [array of voltage values],
        "current": [array of current values],
        "filename": "optional filename",
        "model_id": "optional specific model to use"
    }
    """
    
    try:
        if not PLS_ANALYZER_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'PLS analyzer not available'
            }), 400
        
        initialize_analyzers()
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract data
        voltage = np.array(data.get('voltage', []))
        current = np.array(data.get('current', []))
        filename = data.get('filename', 'web_prediction')
        model_id = data.get('model_id')
        
        if len(voltage) == 0 or len(current) == 0:
            return jsonify({
                'success': False,
                'error': 'Empty voltage or current data'
            }), 400
        
        if not pls_analyzer.models:
            return jsonify({
                'success': False,
                'error': 'No trained models available'
            }), 400
        
        # Make prediction
        prediction = pls_analyzer.predict_concentration(
            voltage, current, model_id, filename
        )
        
        if prediction:
            response = {
                'success': True,
                'predicted_concentration_M': prediction.predicted_concentration,
                'predicted_concentration_uM': prediction.predicted_concentration * 1e6,
                'confidence_interval_M': prediction.confidence_interval,
                'confidence_interval_uM': [ci * 1e6 for ci in prediction.confidence_interval],
                'prediction_confidence': prediction.prediction_confidence,
                'model_used': prediction.model_id,
                'timestamp': prediction.timestamp.isoformat(),
                'filename': filename
            }
        else:
            response = {
                'success': False,
                'error': 'Prediction failed'
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Concentration prediction failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@precision_pls_bp.route('/batch/analyze', methods=['POST'])
def batch_analyze():
    """
    Batch analysis of multiple CV datasets
    
    Expected JSON payload:
    {
        "datasets": [
            {
                "voltage": [array],
                "current": [array], 
                "filename": "optional",
                "concentration": float (for calibration mode)
            },
            ...
        ],
        "mode": "analysis" or "calibration" or "prediction",
        "model_id": "optional for prediction mode"
    }
    """
    
    try:
        if not (PRECISION_ANALYZER_AVAILABLE and PLS_ANALYZER_AVAILABLE):
            return jsonify({
                'success': False,
                'error': 'Required analyzers not available'
            }), 400
        
        initialize_analyzers()
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        datasets = data.get('datasets', [])
        mode = data.get('mode', 'analysis')
        model_id = data.get('model_id')
        
        if not datasets:
            return jsonify({
                'success': False,
                'error': 'No datasets provided'
            }), 400
        
        results = []
        
        for i, dataset in enumerate(datasets):
            try:
                voltage = np.array(dataset.get('voltage', []))
                current = np.array(dataset.get('current', []))
                filename = dataset.get('filename', f'batch_dataset_{i+1}')
                concentration = dataset.get('concentration')
                
                if len(voltage) == 0 or len(current) == 0:
                    results.append({
                        'filename': filename,
                        'success': False,
                        'error': 'Empty data'
                    })
                    continue
                
                if mode == 'analysis':
                    # Pure analysis
                    analysis_result = precision_analyzer.analyze_cv_data(
                        voltage, current, filename=filename
                    )
                    results.append(analysis_result)
                
                elif mode == 'calibration':
                    # Add to calibration
                    if concentration is None:
                        results.append({
                            'filename': filename,
                            'success': False,
                            'error': 'Concentration required for calibration mode'
                        })
                        continue
                    
                    success = pls_analyzer.add_calibration_point(
                        voltage, current, concentration, filename
                    )
                    results.append({
                        'filename': filename,
                        'success': success,
                        'concentration_uM': concentration * 1e6 if success else None
                    })
                
                elif mode == 'prediction':
                    # Predict concentration
                    prediction = pls_analyzer.predict_concentration(
                        voltage, current, model_id, filename
                    )
                    
                    if prediction:
                        results.append({
                            'filename': filename,
                            'success': True,
                            'predicted_concentration_uM': prediction.predicted_concentration * 1e6,
                            'confidence': prediction.prediction_confidence
                        })
                    else:
                        results.append({
                            'filename': filename,
                            'success': False,
                            'error': 'Prediction failed'
                        })
                
            except Exception as e:
                results.append({
                    'filename': filename,
                    'success': False,
                    'error': str(e)
                })
        
        # Summary statistics
        successful = sum(1 for r in results if r.get('success', False))
        
        response = {
            'success': True,
            'mode': mode,
            'total_datasets': len(datasets),
            'successful_analyses': successful,
            'failed_analyses': len(datasets) - successful,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@precision_pls_bp.route('/report/calibration', methods=['GET'])
def get_calibration_report():
    """Generate comprehensive calibration report"""
    
    try:
        if not PLS_ANALYZER_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'PLS analyzer not available'
            }), 400
        
        initialize_analyzers()
        
        report = pls_analyzer.generate_calibration_report()
        report['success'] = True
        
        return jsonify(report)
        
    except Exception as e:
        logger.error(f"Generate calibration report failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@precision_pls_bp.route('/export/model/<model_id>', methods=['GET'])
def export_model(model_id):
    """Export PLS model for external use"""
    
    try:
        if not PLS_ANALYZER_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'PLS analyzer not available'
            }), 400
        
        initialize_analyzers()
        
        if model_id not in pls_analyzer.models:
            return jsonify({
                'success': False,
                'error': 'Model not found'
            }), 404
        
        model = pls_analyzer.models[model_id]
        
        # Create exportable model data
        export_data = {
            'model_id': model.model_id,
            'created_timestamp': model.created_timestamp.isoformat(),
            'feature_names': model.feature_names,
            'optimal_components': model.optimal_components,
            'model_metrics': model.model_metrics,
            'feature_importance': model.feature_importance,
            'calibration_info': {
                'n_points': len(model.calibration_points),
                'concentration_range': [
                    min(p.concentration for p in model.calibration_points),
                    max(p.concentration for p in model.calibration_points)
                ]
            }
        }
        
        return jsonify({
            'success': True,
            'export_data': export_data
        })
        
    except Exception as e:
        logger.error(f"Export model failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Error handlers
@precision_pls_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': str(error)
    }), 400

@precision_pls_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Not found',
        'message': str(error)
    }), 404

@precision_pls_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': str(error)
    }), 500

# Initialize when module is imported
def register_blueprint(app):
    """Register the blueprint with the Flask app"""
    app.register_blueprint(precision_pls_bp)
    logger.info("Precision PLS API blueprint registered")

if __name__ == "__main__":
    # For testing purposes
    from flask import Flask
    
    app = Flask(__name__)
    app.register_blueprint(precision_pls_bp)
    
    print("🧪 Testing Precision PLS API endpoints...")
    print("Available endpoints:")
    print("  GET  /api/precision/status")
    print("  POST /api/precision/analyze")
    print("  POST /api/precision/calibration/add")
    print("  GET  /api/precision/calibration/status")
    print("  POST /api/precision/model/build")
    print("  GET  /api/precision/model/list")
    print("  POST /api/precision/model/validate/<model_id>")
    print("  POST /api/precision/predict")
    print("  POST /api/precision/batch/analyze")
    print("  GET  /api/precision/report/calibration")
    print("  GET  /api/precision/export/model/<model_id>")
    
    app.run(debug=True, port=5001)
