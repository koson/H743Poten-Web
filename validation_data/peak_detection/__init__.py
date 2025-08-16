"""
Peak Detection Framework - Package Initialization
===============================================

This package implements three methods for peak detection in CV data:
1. Baseline Detection (Method 1)
2. Statistical Detection (Method 2) 
3. Machine Learning Detection (Method 3)
"""

from .utils import CVDataLoader, CVPreprocessor, PeakAnalyzer, DataSplitManager, plot_cv_with_peaks

__version__ = "1.0.0"
__author__ = "H743Poten Peak Detection Framework"

__all__ = [
    'CVDataLoader', 'CVPreprocessor', 'PeakAnalyzer', 
    'DataSplitManager', 'plot_cv_with_peaks'
]
