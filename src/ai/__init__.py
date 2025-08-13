"""
PyPiPo AI Package - Machine Learning Integration
Advanced AI capabilities for electrochemical analysis
"""

__version__ = "2.0.0"
__author__ = "PyPiPo Development Team"

# Import core ML modules when available
try:
    from .ml_models.peak_classifier import PeakClassifier
    from .ml_models.concentration_predictor import ConcentrationPredictor
    from .ml_models.signal_processor import SignalProcessor
    from .ml_models.electrochemical_intelligence import ElectrochemicalIntelligence
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

__all__ = [
    'PeakClassifier',
    'ConcentrationPredictor',
    'SignalProcessor',
    'ElectrochemicalIntelligence',
    'ML_AVAILABLE'
]
