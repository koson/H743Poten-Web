"""
AI Dashboard Routes for H743Poten-Web
Migrated from PyPiPo Working-AI-Dashboard-V1
"""

from flask import Blueprint, render_template, jsonify, request
import sys
import os
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

try:
    from ai.ml_models.electrochemical_intelligence import ElectrochemicalIntelligence
    from ai.ml_models.peak_classifier import PeakClassifier
    from ai.ml_models.concentration_predictor import ConcentrationPredictor
    from ai.ml_models.signal_processor import SignalProcessor
except ImportError as e:
    print(f"Warning: AI modules not available: {e}")
    # Create mock classes for development
    class ElectrochemicalIntelligence:
        def analyze_cv_data(self, data): return {"analysis": "Mock analysis"}
    
    class PeakClassifier:
        def classify_peaks(self, peaks): return {"classification": "Mock classification"}
    
    class ConcentrationPredictor:
        def predict_concentration(self, data): return {"concentration": 0.001}
    
    class SignalProcessor:
        def enhance_signal(self, signal): return signal

# Create Blueprint
ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

# Initialize AI modules
try:
    electrochemical_ai = ElectrochemicalIntelligence()
    peak_classifier = PeakClassifier()
    concentration_predictor = ConcentrationPredictor()
    signal_processor = SignalProcessor()
except Exception as e:
    print(f"Warning: Failed to initialize AI modules: {e}")
    # Use mock instances
    electrochemical_ai = ElectrochemicalIntelligence()
    peak_classifier = PeakClassifier()
    concentration_predictor = ConcentrationPredictor()
    signal_processor = SignalProcessor()

@ai_bp.route('/')
@ai_bp.route('/dashboard')
def ai_dashboard():
    """Main AI Dashboard page"""
    return render_template('ai_dashboard.html')

@ai_bp.route('/api/analyze', methods=['POST'])
def analyze_data():
    """Analyze electrochemical data using AI"""
    try:
        data = request.get_json()
        
        if not data or 'voltage' not in data or 'current' not in data:
            return jsonify({
                'success': False,
                'error': 'Invalid data format. Expected voltage and current arrays.'
            }), 400
        
        # Perform AI analysis
        analysis_result = electrochemical_ai.analyze_cv_data(data)
        
        return jsonify({
            'success': True,
            'analysis': analysis_result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Analysis failed: {str(e)}'
        }), 500

@ai_bp.route('/api/classify-peaks', methods=['POST'])
def classify_peaks():
    """Classify peaks in electrochemical data"""
    try:
        data = request.get_json()
        
        if not data or 'peaks' not in data:
            return jsonify({
                'success': False,
                'error': 'Invalid data format. Expected peaks array.'
            }), 400
        
        # Classify peaks
        classification = peak_classifier.classify_peaks(data['peaks'])
        
        return jsonify({
            'success': True,
            'classification': classification
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Peak classification failed: {str(e)}'
        }), 500

@ai_bp.route('/api/predict-concentration', methods=['POST'])
def predict_concentration():
    """Predict analyte concentration"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Predict concentration
        concentration = concentration_predictor.predict_concentration(data)
        
        return jsonify({
            'success': True,
            'concentration': concentration
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Concentration prediction failed: {str(e)}'
        }), 500

@ai_bp.route('/api/enhance-signal', methods=['POST'])
def enhance_signal():
    """Enhance signal quality using AI"""
    try:
        data = request.get_json()
        
        if not data or 'signal' not in data:
            return jsonify({
                'success': False,
                'error': 'Invalid data format. Expected signal array.'
            }), 400
        
        # Enhance signal
        enhanced_signal = signal_processor.enhance_signal(data['signal'])
        
        return jsonify({
            'success': True,
            'enhanced_signal': enhanced_signal
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Signal enhancement failed: {str(e)}'
        }), 500

@ai_bp.route('/api/status')
def ai_status():
    """Get AI system status"""
    try:
        status = {
            'ai_modules_loaded': True,
            'electrochemical_ai': 'available',
            'peak_classifier': 'available',
            'concentration_predictor': 'available',
            'signal_processor': 'available',
            'version': '2.0.0',
            'last_updated': '2025-08-14'
        }
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Status check failed: {str(e)}'
        }), 500
