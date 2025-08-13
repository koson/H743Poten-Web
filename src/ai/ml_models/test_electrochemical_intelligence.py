"""
Unit tests for ElectrochemicalIntelligence class
Tests coverage of electrochemical data analysis functionality
"""

import pytest
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Import the classes we're testing
from .electrochemical_intelligence import (
    ElectrochemicalIntelligence,
    ElectrochemicalContext,
    MeasurementType,
    AnalyteType,
    AnalyteIdentification,
    ElectrochemicalInsight,
    IntelligentAnalysis
)

# Test data generation helpers
def generate_cv_data(noise_level: float = 0.1) -> Tuple[np.ndarray, np.ndarray]:
    """Generate synthetic CV data for testing"""
    voltage = np.linspace(-0.5, 0.5, 1000)
    # Simulate dopamine CV (reversible redox couple)
    current = (
        2e-6 * np.exp(-((voltage - 0.15) / 0.03) ** 2) -    # Oxidation peak
        1.8e-6 * np.exp(-((voltage - 0.09) / 0.03) ** 2) +  # Reduction peak
        np.random.normal(0, noise_level * 1e-7, len(voltage)) # Noise
    )
    return voltage, current

def generate_dpv_data(noise_level: float = 0.1) -> Tuple[np.ndarray, np.ndarray]:
    """Generate synthetic DPV data for testing"""
    voltage = np.linspace(-0.2, 0.4, 500)
    # Simulate single sharp peak
    current = (
        3e-6 * np.exp(-((voltage - 0.15) / 0.02) ** 2) +  # Main peak
        np.random.normal(0, noise_level * 1e-7, len(voltage))  # Noise
    )
    return voltage, current

@pytest.fixture
def ei_instance():
    """Create an ElectrochemicalIntelligence instance for testing"""
    return ElectrochemicalIntelligence()

@pytest.fixture
def basic_context():
    """Create a basic measurement context for testing"""
    return ElectrochemicalContext(
        measurement_type=MeasurementType.CV,
        electrode_material="Glassy Carbon",
        electrolyte="PBS pH 7.4",
        ph=7.4,
        temperature=25.0,
        scan_rate=0.1
    )

@pytest.fixture
def calibration_data():
    """Generate calibration data for testing"""
    return [
        (1e-6, 1e-6),    # 1 μM → 1 μA
        (5e-6, 4.8e-6),  # 5 μM → 4.8 μA
        (10e-6, 9.2e-6), # 10 μM → 9.2 μA
    ]

class TestElectrochemicalIntelligence:
    """Test suite for ElectrochemicalIntelligence class"""

    def test_initialization(self, ei_instance):
        """Test proper initialization of ElectrochemicalIntelligence"""
        assert ei_instance is not None
        assert ei_instance.config is not None
        assert ei_instance.analysis_count == 0
        assert len(ei_instance.compound_database) > 0
        assert len(ei_instance.expert_rules) > 0

    def test_signal_quality_assessment_clean(self, ei_instance, basic_context):
        """Test signal quality assessment with clean data"""
        voltage, current = generate_cv_data(noise_level=0.1)
        analysis = ei_instance.analyze_measurement(voltage, current, basic_context)
        
        quality = analysis.quality_assessment
        assert quality is not None
        assert 'quality_score' in quality
        assert quality['quality_score'] > 0.7  # Clean data should have good quality
        assert 'snr_db' in quality
        assert 'recommendations' in quality

    def test_signal_quality_assessment_noisy(self, ei_instance, basic_context):
        """Test signal quality assessment with noisy data"""
        voltage, current = generate_cv_data(noise_level=1.0)
        analysis = ei_instance.analyze_measurement(voltage, current, basic_context)
        
        quality = analysis.quality_assessment
        assert quality is not None
        assert 'quality_score' in quality
        assert 'snr_db' in quality
        # Noisy data should give lower quality score or SNR
        assert quality['quality_score'] < 0.9

    def test_peak_analysis_cv(self, ei_instance, basic_context):
        """Test peak analysis with CV data"""
        voltage, current = generate_cv_data()
        analysis = ei_instance.analyze_measurement(voltage, current, basic_context)
        
        peaks = analysis.peak_analysis
        assert peaks is not None
        assert peaks['peaks_detected'] >= 2  # Should detect oxidation and reduction peaks
        assert 'peak_data' in peaks
        if 'peak_data' in peaks:
            assert len(peaks['peak_data']) >= 2

    def test_peak_analysis_dpv(self, ei_instance):
        """Test peak analysis with DPV data"""
        voltage, current = generate_dpv_data()
        context = ElectrochemicalContext(
            measurement_type=MeasurementType.DPV,
            electrode_material="Glassy Carbon",
            electrolyte="PBS pH 7.4",
            pulse_amplitude=0.05
        )
        
        analysis = ei_instance.analyze_measurement(voltage, current, context)
        
        peaks = analysis.peak_analysis
        assert peaks is not None
        assert peaks['peaks_detected'] >= 1  # Should detect at least one peak
        assert 'peak_data' in peaks
        if 'peak_data' in peaks:
            assert len(peaks['peak_data']) >= 1

    def test_analyte_identification(self, ei_instance, basic_context):
        """Test analyte identification"""
        voltage, current = generate_cv_data()
        analysis = ei_instance.analyze_measurement(voltage, current, basic_context)
        
        analyte = analysis.analyte_identification
        assert analyte is not None
        assert isinstance(analyte, AnalyteIdentification)
        assert analyte.analyte_type != AnalyteType.UNKNOWN
        assert analyte.confidence > 0.0
        assert len(analyte.possible_compounds) > 0
        assert len(analyte.supporting_evidence) > 0

    def test_concentration_analysis(self, ei_instance, basic_context, calibration_data):
        """Test concentration analysis with calibration data"""
        voltage, current = generate_cv_data()
        analysis = ei_instance.analyze_measurement(voltage, current, basic_context, calibration_data)
        
        conc = analysis.concentration_analysis
        assert conc is not None
        assert 'predicted_concentration' in conc
        assert 'confidence_interval' in conc
        assert 'r_squared' in conc
        assert 'method' in conc
        assert conc['r_squared'] > 0.9  # Should have good fit with synthetic data

    def test_insight_generation(self, ei_instance, basic_context):
        """Test insight generation"""
        voltage, current = generate_cv_data()
        analysis = ei_instance.analyze_measurement(voltage, current, basic_context)
        
        insights = analysis.insights
        assert len(insights) > 0
        assert all(isinstance(i, ElectrochemicalInsight) for i in insights)
        assert all(0.0 <= i.confidence <= 1.0 for i in insights)
        
        # Check different insight categories are present
        categories = {i.category for i in insights}
        assert len(categories) >= 2  # Should have multiple categories of insights

    def test_expert_recommendations(self, ei_instance, basic_context):
        """Test expert recommendation generation"""
        voltage, current = generate_cv_data()
        analysis = ei_instance.analyze_measurement(voltage, current, basic_context)
        
        recommendations = analysis.expert_recommendations
        assert len(recommendations) > 0
        assert all(isinstance(r, str) for r in recommendations)
        assert len(set(recommendations)) == len(recommendations)  # No duplicates

    def test_error_handling(self, ei_instance, basic_context):
        """Test error handling with invalid data"""
        # Test with invalid voltage/current arrays
        voltage = np.array([])  # Empty array
        current = np.array([])
        
        analysis = ei_instance.analyze_measurement(voltage, current, basic_context)
        assert analysis is not None  # Should not raise exception
        assert 'error' in analysis.measurement_summary
        
        # Test with NaN/inf values
        voltage = np.array([1.0, np.nan, 3.0])
        current = np.array([1.0, 2.0, np.inf])
        
        analysis = ei_instance.analyze_measurement(voltage, current, basic_context)
        assert analysis is not None
        assert 'quality_score' in analysis.quality_assessment
        assert analysis.quality_assessment['quality_score'] < 0.5  # Bad quality due to invalid data

    def test_reproducibility(self, ei_instance, basic_context):
        """Test reproducibility of analysis results"""
        voltage, current = generate_cv_data(noise_level=0.0)  # No random noise
        
        # Run analysis twice
        analysis1 = ei_instance.analyze_measurement(voltage, current, basic_context)
        analysis2 = ei_instance.analyze_measurement(voltage, current, basic_context)
        
        # Compare key metrics
        assert analysis1.peak_analysis['peaks_detected'] == analysis2.peak_analysis['peaks_detected']
        if analysis1.analyte_identification and analysis2.analyte_identification:
            assert (analysis1.analyte_identification.analyte_type == 
                   analysis2.analyte_identification.analyte_type)

    def test_measurement_types(self, ei_instance):
        """Test analysis with different measurement types"""
        measurement_types = [
            (MeasurementType.CV, generate_cv_data()),
            (MeasurementType.DPV, generate_dpv_data())
        ]
        
        for mtype, (voltage, current) in measurement_types:
            context = ElectrochemicalContext(measurement_type=mtype)
            analysis = ei_instance.analyze_measurement(voltage, current, context)
            
            assert analysis is not None
            assert analysis.measurement_summary['measurement_type'] == mtype.value
            assert len(analysis.insights) > 0

    def test_get_intelligence_summary(self, ei_instance):
        """Test intelligence system summary"""
        summary = ei_instance.get_intelligence_summary()
        assert isinstance(summary, dict)
        assert 'ml_models_available' in summary
        assert 'analysis_count' in summary
        assert 'compound_database_entries' in summary
        assert 'expert_rules' in summary
        assert 'config' in summary

if __name__ == '__main__':
    pytest.main(['-v'])
