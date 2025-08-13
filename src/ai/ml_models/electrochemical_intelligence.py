"""
Electrochemical Intelligence - Advanced AI system for electrochemical analysis
Combines pattern recognition, expert rules, and machine learning for intelligent interpretation
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)

# Import our ML models
try:
    from .peak_classifier import PeakClassifier, PeakType
    from .concentration_predictor import ConcentrationPredictor
    from .signal_processor import SignalProcessor
    ML_MODELS_AVAILABLE = True
except ImportError:
    ML_MODELS_AVAILABLE = False
    logger.warning("ML models not available")

class MeasurementType(Enum):
    """Types of electrochemical measurements"""
    CV = "Cyclic Voltammetry"
    CA = "Chronoamperometry" 
    DPV = "Differential Pulse Voltammetry"
    SWV = "Square Wave Voltammetry"
    LSV = "Linear Sweep Voltammetry"
    UNKNOWN = "Unknown"

class AnalyteType(Enum):
    """Types of analytes commonly detected"""
    ORGANIC = "Organic Compound"
    METAL_ION = "Metal Ion"
    PROTEIN = "Protein/Biomolecule"
    DRUG = "Pharmaceutical"
    ENVIRONMENTAL = "Environmental Pollutant"
    UNKNOWN = "Unknown Analyte"

@dataclass
class ElectrochemicalContext:
    """Context information for electrochemical analysis"""
    measurement_type: MeasurementType
    electrode_material: str = "Unknown"
    electrolyte: str = "Unknown"
    ph: Optional[float] = None
    temperature: Optional[float] = None  # Celsius
    scan_rate: Optional[float] = None    # V/s for CV
    frequency: Optional[float] = None    # Hz for SWV
    pulse_amplitude: Optional[float] = None  # V for DPV
    additional_info: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AnalyteIdentification:
    """Result of analyte identification"""
    analyte_type: AnalyteType
    confidence: float  # 0-1
    possible_compounds: List[str]
    characteristic_features: Dict[str, Any]
    supporting_evidence: List[str]
    suggested_confirmations: List[str]

@dataclass
class ElectrochemicalInsight:
    """Comprehensive analysis insight"""
    title: str
    description: str
    confidence: float
    category: str  # 'peak', 'kinetics', 'mechanism', 'quantitative', 'quality'
    evidence: List[str]
    recommendations: List[str]
    references: List[str] = field(default_factory=list)

@dataclass
class IntelligentAnalysis:
    """Complete intelligent analysis result"""
    measurement_summary: Dict[str, Any]
    peak_analysis: Dict[str, Any]
    analyte_identification: Optional[AnalyteIdentification]
    concentration_analysis: Optional[Dict[str, Any]]
    insights: List[ElectrochemicalInsight]
    quality_assessment: Dict[str, Any]
    expert_recommendations: List[str]
    timestamp: datetime
    processing_time: float  # seconds

class ElectrochemicalIntelligence:
    """
    Advanced AI system for electrochemical data interpretation
    Combines multiple analysis approaches for comprehensive insights
    """
    
    def __init__(self, intelligence_config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.config = intelligence_config or self._get_default_config()
        
        # Initialize ML components
        if ML_MODELS_AVAILABLE:
            self.peak_classifier = PeakClassifier()
            self.concentration_predictor = ConcentrationPredictor()
            self.signal_processor = SignalProcessor()
        else:
            self.peak_classifier = None
            self.concentration_predictor = None
            self.signal_processor = None
        
        # Knowledge base
        self.compound_database = self._load_compound_database()
        self.expert_rules = self._load_expert_rules()
        
        # Analysis history
        self.analysis_count = 0
        self.insight_cache = {}
        
        self.logger.info("Electrochemical Intelligence system initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration for intelligent analysis"""
        return {
            # Analysis thresholds
            'min_peak_significance': 0.1,    # Minimum peak significance
            'min_confidence_threshold': 0.5,  # Minimum confidence for insights
            'max_insights_per_category': 3,   # Limit insights per category
            
            # Pattern recognition
            'enable_pattern_matching': True,
            'enable_kinetic_analysis': True,
            'enable_mechanism_inference': True,
            
            # Expert rules
            'apply_expert_rules': True,
            'rule_confidence_weight': 0.7,   # Weight for expert rules vs ML
            
            # Compound identification
            'enable_compound_id': True,
            'compound_match_threshold': 0.6, # Minimum match score
            
            # Quality control
            'quality_gate_enabled': True,
            'min_quality_score': 0.5,        # Minimum acceptable quality
        }
    
    def _load_compound_database(self) -> Dict[str, Dict[str, Any]]:
        """Load compound database for analyte identification"""
        # Simplified compound database - in production this would be comprehensive
        return {
            'dopamine': {
                'type': AnalyteType.ORGANIC,
                'peak_potentials_cv': [0.15, 0.20],  # V vs Ag/AgCl, pH 7
                'peak_shape': 'reversible',
                'ph_dependence': True,
                'typical_concentrations': [1e-8, 1e-4],  # M
                'interferences': ['ascorbic_acid', 'uric_acid'],
                'confirmatory_tests': ['UV-Vis', 'HPLC-MS']
            },
            'ascorbic_acid': {
                'type': AnalyteType.ORGANIC,
                'peak_potentials_cv': [0.05, 0.10],
                'peak_shape': 'irreversible',
                'ph_dependence': True,
                'typical_concentrations': [1e-6, 1e-3],
                'interferences': ['dopamine'],
                'confirmatory_tests': ['Titration', 'UV-Vis']
            },
            'lead_ion': {
                'type': AnalyteType.METAL_ION,
                'peak_potentials_dpv': [-0.40, -0.45],  # Pb2+/Pb
                'peak_shape': 'sharp',
                'ph_dependence': False,
                'typical_concentrations': [1e-9, 1e-5],
                'interferences': ['bismuth', 'cadmium'],
                'confirmatory_tests': ['ICP-MS', 'AAS']
            },
            'glucose': {
                'type': AnalyteType.ORGANIC,
                'peak_potentials_cv': [0.60, 0.65],  # On Au electrode
                'peak_shape': 'broad',
                'ph_dependence': True,
                'typical_concentrations': [1e-6, 1e-2],
                'interferences': ['fructose', 'sucrose'],
                'confirmatory_tests': ['Enzymatic', 'GC-MS']
            }
        }
    
    def _load_expert_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load expert knowledge rules"""
        return {
            'reversible_kinetics': {
                'condition': 'peak_separation < 0.059/n',  # n = electron number
                'confidence': 0.9,
                'insight': 'Electrochemically reversible process detected',
                'recommendations': ['Confirm with scan rate studies', 'Check temperature dependence']
            },
            'irreversible_kinetics': {
                'condition': 'peak_separation > 0.2',
                'confidence': 0.8,
                'insight': 'Irreversible electrochemical process',
                'recommendations': ['Consider kinetic parameters', 'Check for side reactions']
            },
            'diffusion_control': {
                'condition': 'current_vs_sqrt_scan_rate_linear',
                'confidence': 0.85,
                'insight': 'Diffusion-controlled electrode reaction',
                'recommendations': ['Calculate diffusion coefficient', 'Verify with rotating disk electrode']
            },
            'adsorption_control': {
                'condition': 'current_vs_scan_rate_linear',
                'confidence': 0.8,
                'insight': 'Adsorption-controlled electrode reaction',
                'recommendations': ['Study coverage effects', 'Check for surface contamination']
            },
            'high_background': {
                'condition': 'background_current > signal_current * 0.5',
                'confidence': 0.9,
                'insight': 'High background current detected',
                'recommendations': ['Clean electrode surface', 'Purge solution with inert gas', 'Check electrolyte purity']
            }
        }
    
    def analyze_measurement(self, voltage: np.ndarray, current: np.ndarray,
                          context: ElectrochemicalContext,
                          calibration_data: Optional[List[Tuple[float, float]]] = None) -> IntelligentAnalysis:
        """
        Perform comprehensive intelligent analysis of electrochemical measurement
        
        Args:
            voltage: Voltage array (V)
            current: Current array (A)
            context: Measurement context and conditions
            calibration_data: Optional calibration points [(concentration, current)]
            
        Returns:
            Complete intelligent analysis
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Starting intelligent analysis of {context.measurement_type.value}")
            
            # 1. Signal quality assessment
            quality_assessment = self._assess_signal_quality(voltage, current)
            
            # Quality gate check
            if (self.config['quality_gate_enabled'] and 
                quality_assessment.get('quality_score', 0) < self.config['min_quality_score']):
                self.logger.warning("Signal quality below threshold - analysis may be unreliable")
            
            # 2. Peak analysis
            peak_analysis = self._analyze_peaks(voltage, current, context)
            
            # 3. Analyte identification
            analyte_identification = self._identify_analyte(peak_analysis, context)
            
            # 4. Concentration analysis
            concentration_analysis = None
            if calibration_data and self.concentration_predictor:
                concentration_analysis = self._analyze_concentration(
                    voltage, current, calibration_data, context
                )
            
            # 5. Generate insights
            insights = self._generate_insights(
                voltage, current, peak_analysis, context, quality_assessment
            )
            
            # 6. Expert recommendations
            expert_recommendations = self._generate_expert_recommendations(
                peak_analysis, quality_assessment, context
            )
            
            # 7. Measurement summary
            measurement_summary = self._create_measurement_summary(
                voltage, current, context, peak_analysis
            )
            
            # Create analysis result
            processing_time = (datetime.now() - start_time).total_seconds()
            
            analysis = IntelligentAnalysis(
                measurement_summary=measurement_summary,
                peak_analysis=peak_analysis,
                analyte_identification=analyte_identification,
                concentration_analysis=concentration_analysis,
                insights=insights,
                quality_assessment=quality_assessment,
                expert_recommendations=expert_recommendations,
                timestamp=start_time,
                processing_time=processing_time
            )
            
            self.analysis_count += 1
            self.logger.info(f"Analysis completed in {processing_time:.2f}s with {len(insights)} insights")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Intelligent analysis failed: {e}")
            # Return minimal analysis on error
            return IntelligentAnalysis(
                measurement_summary={'error': str(e)},
                peak_analysis={},
                analyte_identification=None,
                concentration_analysis=None,
                insights=[],
                quality_assessment={'error': str(e)},
                expert_recommendations=[f"Analysis failed: {str(e)}"],
                timestamp=start_time,
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _assess_signal_quality(self, voltage: np.ndarray, current: np.ndarray) -> Dict[str, Any]:
        """Assess signal quality using signal processor"""
        try:
            if self.signal_processor:
                quality = self.signal_processor.assess_signal_quality(voltage, current)
                return {
                    'snr_db': quality.snr_db,
                    'baseline_drift': quality.baseline_drift,
                    'noise_level': quality.noise_level,
                    'data_completeness': quality.data_completeness,
                    'quality_score': quality.quality_score,
                    'recommendations': quality.recommendations
                }
            else:
                # Fallback quality assessment
                valid_ratio = np.sum(np.isfinite(current)) / len(current)
                noise_est = np.std(np.diff(current)) if len(current) > 1 else 0
                
                return {
                    'snr_db': 20.0,  # Assume reasonable SNR
                    'baseline_drift': 0.1,
                    'noise_level': noise_est,
                    'data_completeness': valid_ratio,
                    'quality_score': min(valid_ratio, 0.8),
                    'recommendations': ['Install SciPy for advanced quality assessment']
                }
                
        except Exception as e:
            self.logger.warning(f"Quality assessment failed: {e}")
            return {'error': str(e), 'quality_score': 0.5}
    
    def _analyze_peaks(self, voltage: np.ndarray, current: np.ndarray,
                      context: ElectrochemicalContext) -> Dict[str, Any]:
        """Analyze peaks using ML classifier"""
        try:
            if self.peak_classifier:
                # Use ML peak analysis
                peaks_result = self.peak_classifier.detect_and_classify_peaks(voltage, current)
                
                return {
                    'peaks_detected': len(peaks_result.get('peaks', [])),
                    'peak_data': peaks_result.get('peaks', []),
                    'peak_types': peaks_result.get('peak_types', []),
                    'classification_confidence': peaks_result.get('confidence', 0.0),
                    'method': 'ML_classification'
                }
            else:
                # Fallback peak detection
                return self._fallback_peak_analysis(voltage, current)
                
        except Exception as e:
            self.logger.warning(f"Peak analysis failed: {e}")
            return {'error': str(e), 'peaks_detected': 0}
    
    def _fallback_peak_analysis(self, voltage: np.ndarray, current: np.ndarray) -> Dict[str, Any]:
        """Fallback peak analysis without ML"""
        try:
            # Simple peak detection using gradient
            valid_mask = np.isfinite(current) & np.isfinite(voltage)
            current_clean = current[valid_mask]
            voltage_clean = voltage[valid_mask]
            
            if len(current_clean) < 5:
                return {'peaks_detected': 0, 'method': 'fallback'}
            
            # Find local maxima
            gradient = np.gradient(current_clean)
            peaks = []
            
            for i in range(1, len(gradient) - 1):
                if gradient[i-1] > 0 and gradient[i+1] < 0:  # Sign change indicates peak
                    if abs(current_clean[i]) > np.std(current_clean) * 2:  # Significant peak
                        peaks.append({
                            'potential': voltage_clean[i],
                            'current': current_clean[i],
                            'index': i,
                            'type': 'oxidation' if current_clean[i] > 0 else 'reduction'
                        })
            
            return {
                'peaks_detected': len(peaks),
                'peak_data': peaks,
                'method': 'fallback_gradient'
            }
            
        except Exception as e:
            return {'error': str(e), 'peaks_detected': 0}
    
    def _identify_analyte(self, peak_analysis: Dict[str, Any],
                         context: ElectrochemicalContext) -> Optional[AnalyteIdentification]:
        """Identify possible analytes based on peak characteristics"""
        try:
            if not self.config['enable_compound_id']:
                return None
            
            peaks = peak_analysis.get('peak_data', [])
            if not peaks:
                return None
            
            # Extract peak potentials
            peak_potentials = [peak.get('potential', 0) for peak in peaks]
            
            # Match against compound database
            matches = []
            for compound, data in self.compound_database.items():
                match_score = self._calculate_compound_match_score(
                    peak_potentials, data, context
                )
                
                if match_score > self.config['compound_match_threshold']:
                    matches.append((compound, match_score, data))
            
            if not matches:
                return AnalyteIdentification(
                    analyte_type=AnalyteType.UNKNOWN,
                    confidence=0.0,
                    possible_compounds=[],
                    characteristic_features={},
                    supporting_evidence=[],
                    suggested_confirmations=['MS analysis', 'Standard addition']
                )
            
            # Select best match
            best_match = max(matches, key=lambda x: x[1])
            compound, confidence, data = best_match
            
            return AnalyteIdentification(
                analyte_type=data['type'],
                confidence=confidence,
                possible_compounds=[m[0] for m in sorted(matches, key=lambda x: x[1], reverse=True)[:3]],
                characteristic_features={
                    'peak_potentials': peak_potentials,
                    'peak_shape': data.get('peak_shape', 'unknown'),
                    'ph_dependence': data.get('ph_dependence', False)
                },
                supporting_evidence=[
                    f"Peak potential match: {confidence:.1%}",
                    f"Typical for {data['type'].value}"
                ],
                suggested_confirmations=data.get('confirmatory_tests', [])
            )
            
        except Exception as e:
            self.logger.warning(f"Analyte identification failed: {e}")
            return None
    
    def _calculate_compound_match_score(self, observed_potentials: List[float],
                                      compound_data: Dict[str, Any],
                                      context: ElectrochemicalContext) -> float:
        """Calculate match score between observed peaks and compound database entry"""
        try:
            # Get expected potentials based on measurement type
            measurement_key = {
                MeasurementType.CV: 'peak_potentials_cv',
                MeasurementType.DPV: 'peak_potentials_dpv',
                MeasurementType.SWV: 'peak_potentials_swv'
            }.get(context.measurement_type, 'peak_potentials_cv')
            
            expected_potentials = compound_data.get(measurement_key, [])
            if not expected_potentials:
                return 0.0
            
            # Find best matching potentials
            match_scores = []
            for obs_pot in observed_potentials:
                best_match = min(expected_potentials, key=lambda exp: abs(exp - obs_pot))
                deviation = abs(best_match - obs_pot)
                
                # Score based on deviation (within ±100 mV gets high score)
                if deviation < 0.05:  # ±50 mV
                    match_scores.append(1.0)
                elif deviation < 0.1:  # ±100 mV
                    match_scores.append(0.8)
                elif deviation < 0.2:  # ±200 mV
                    match_scores.append(0.5)
                else:
                    match_scores.append(0.1)
            
            # Average match score
            return sum(match_scores) / len(match_scores) if match_scores else 0.0
            
        except Exception as e:
            self.logger.warning(f"Match score calculation failed: {e}")
            return 0.0
    
    def _analyze_concentration(self, voltage: np.ndarray, current: np.ndarray,
                             calibration_data: List[Tuple[float, float]],
                             context: ElectrochemicalContext) -> Dict[str, Any]:
        """Analyze concentration using calibration data"""
        try:
            if not self.concentration_predictor:
                return {'error': 'Concentration predictor not available'}
            
            # Add calibration points
            for conc, curr in calibration_data:
                self.concentration_predictor.add_calibration_point(conc, curr)
            
            # Calibrate
            cal_result = self.concentration_predictor.calibrate()
            
            if not cal_result['success']:
                return {'error': f"Calibration failed: {cal_result.get('error', 'Unknown')}"}
            
            # Predict concentration from peak current
            peak_current = np.max(np.abs(current))  # Use absolute max as representative
            
            conc_result = self.concentration_predictor.predict_concentration(peak_current)
            
            return {
                'predicted_concentration': conc_result.predicted_concentration,
                'confidence_interval': conc_result.confidence_interval,
                'r_squared': conc_result.r_squared,
                'method': conc_result.method_used,
                'calibration_points': conc_result.calibration_points,
                'calibration_curve': self.concentration_predictor.get_calibration_curve_data()
            }
            
        except Exception as e:
            self.logger.warning(f"Concentration analysis failed: {e}")
            return {'error': str(e)}
    
    def _generate_insights(self, voltage: np.ndarray, current: np.ndarray,
                          peak_analysis: Dict[str, Any], context: ElectrochemicalContext,
                          quality_assessment: Dict[str, Any]) -> List[ElectrochemicalInsight]:
        """Generate intelligent insights from analysis"""
        insights = []
        
        try:
            # Peak-related insights
            insights.extend(self._generate_peak_insights(peak_analysis, context))
            
            # Quality-related insights
            insights.extend(self._generate_quality_insights(quality_assessment))
            
            # Kinetic insights (if enabled)
            if self.config['enable_kinetic_analysis']:
                insights.extend(self._generate_kinetic_insights(voltage, current, context))
            
            # Mechanism insights (if enabled)
            if self.config['enable_mechanism_inference']:
                insights.extend(self._generate_mechanism_insights(peak_analysis, context))
            
            # Limit insights per category
            categorized_insights = {}
            for insight in insights:
                cat = insight.category
                if cat not in categorized_insights:
                    categorized_insights[cat] = []
                categorized_insights[cat].append(insight)
            
            # Select top insights per category
            final_insights = []
            for cat, cat_insights in categorized_insights.items():
                sorted_insights = sorted(cat_insights, key=lambda x: x.confidence, reverse=True)
                final_insights.extend(sorted_insights[:self.config['max_insights_per_category']])
            
            return final_insights
            
        except Exception as e:
            self.logger.warning(f"Insight generation failed: {e}")
            return []
    
    def _generate_peak_insights(self, peak_analysis: Dict[str, Any],
                              context: ElectrochemicalContext) -> List[ElectrochemicalInsight]:
        """Generate insights about detected peaks"""
        insights = []
        
        try:
            peaks_detected = peak_analysis.get('peaks_detected', 0)
            
            if peaks_detected == 0:
                insights.append(ElectrochemicalInsight(
                    title="No Significant Peaks Detected",
                    description="No electrochemically active species detected in the measured potential range.",
                    confidence=0.9,
                    category="peak",
                    evidence=["Peak detection algorithm found no significant features"],
                    recommendations=[
                        "Expand potential window",
                        "Increase analyte concentration",
                        "Check electrode surface condition"
                    ]
                ))
            elif peaks_detected == 1:
                insights.append(ElectrochemicalInsight(
                    title="Single Redox Process Detected",
                    description="One electrochemically active species or process identified.",
                    confidence=0.8,
                    category="peak",
                    evidence=[f"Single peak detected"],
                    recommendations=[
                        "Confirm with repeat measurements",
                        "Consider scan rate studies for kinetic characterization"
                    ]
                ))
            else:
                insights.append(ElectrochemicalInsight(
                    title="Multiple Redox Processes",
                    description=f"Multiple electrochemically active species detected ({peaks_detected} peaks).",
                    confidence=0.8,
                    category="peak",
                    evidence=[f"{peaks_detected} distinct peaks identified"],
                    recommendations=[
                        "Check for interferences",
                        "Consider selective detection methods",
                        "Verify peak assignments"
                    ]
                ))
                
        except Exception as e:
            self.logger.warning(f"Peak insight generation failed: {e}")
        
        return insights
    
    def _generate_quality_insights(self, quality_assessment: Dict[str, Any]) -> List[ElectrochemicalInsight]:
        """Generate insights about signal quality"""
        insights = []
        
        try:
            quality_score = quality_assessment.get('quality_score', 0)
            snr_db = quality_assessment.get('snr_db', 0)
            
            if quality_score < 0.5:
                insights.append(ElectrochemicalInsight(
                    title="Poor Signal Quality Detected",
                    description="The measurement signal quality is below acceptable standards.",
                    confidence=0.9,
                    category="quality",
                    evidence=[
                        f"Quality score: {quality_score:.2f}/1.0",
                        f"SNR: {snr_db:.1f} dB"
                    ],
                    recommendations=quality_assessment.get('recommendations', [])
                ))
            elif snr_db > 30:
                insights.append(ElectrochemicalInsight(
                    title="Excellent Signal Quality",
                    description="High-quality measurement with excellent signal-to-noise ratio.",
                    confidence=0.9,
                    category="quality",
                    evidence=[f"SNR: {snr_db:.1f} dB"],
                    recommendations=["Signal quality is optimal for quantitative analysis"]
                ))
                
        except Exception as e:
            self.logger.warning(f"Quality insight generation failed: {e}")
        
        return insights
    
    def _generate_kinetic_insights(self, voltage: np.ndarray, current: np.ndarray,
                                 context: ElectrochemicalContext) -> List[ElectrochemicalInsight]:
        """Generate insights about electrode kinetics"""
        insights = []
        
        try:
            if context.measurement_type == MeasurementType.CV and context.scan_rate:
                # Analyze kinetics from CV data
                
                # Simple kinetic analysis - in production this would be more sophisticated
                peak_current = np.max(np.abs(current))
                
                # Randles-Sevcik equation suggests sqrt(scan_rate) dependence for diffusion
                # This is a simplified analysis
                
                insights.append(ElectrochemicalInsight(
                    title="Kinetic Analysis Available",
                    description="Electrode kinetics can be analyzed from cyclic voltammetry data.",
                    confidence=0.7,
                    category="kinetics",
                    evidence=[f"CV at {context.scan_rate:.3f} V/s"],
                    recommendations=[
                        "Perform multi-scan rate study",
                        "Calculate apparent diffusion coefficient",
                        "Determine electron transfer rate constant"
                    ]
                ))
                
        except Exception as e:
            self.logger.warning(f"Kinetic insight generation failed: {e}")
        
        return insights
    
    def _generate_mechanism_insights(self, peak_analysis: Dict[str, Any],
                                   context: ElectrochemicalContext) -> List[ElectrochemicalInsight]:
        """Generate insights about reaction mechanisms"""
        insights = []
        
        try:
            peaks = peak_analysis.get('peak_data', [])
            
            if len(peaks) >= 2:
                # Check for reversible redox couple
                potentials = [p.get('potential', 0) for p in peaks]
                potential_separation = max(potentials) - min(potentials)
                
                if 0.05 < potential_separation < 0.2:  # Typical range for reversible systems
                    insights.append(ElectrochemicalInsight(
                        title="Potential Reversible Redox Couple",
                        description="Peak separation suggests a potentially reversible electrode reaction.",
                        confidence=0.7,
                        category="mechanism",
                        evidence=[f"Peak separation: {potential_separation*1000:.0f} mV"],
                        recommendations=[
                            "Confirm with scan rate studies",
                            "Check temperature dependence",
                            "Verify with impedance spectroscopy"
                        ]
                    ))
                    
        except Exception as e:
            self.logger.warning(f"Mechanism insight generation failed: {e}")
        
        return insights
    
    def _generate_expert_recommendations(self, peak_analysis: Dict[str, Any],
                                       quality_assessment: Dict[str, Any],
                                       context: ElectrochemicalContext) -> List[str]:
        """Generate expert-level recommendations"""
        recommendations = []
        
        try:
            # Based on measurement type
            if context.measurement_type == MeasurementType.CV:
                recommendations.extend([
                    "Consider multiple scan rates for kinetic analysis",
                    "Verify reproducibility with repeat measurements"
                ])
            elif context.measurement_type == MeasurementType.DPV:
                recommendations.extend([
                    "Optimize pulse amplitude for best sensitivity",
                    "Consider baseline correction for quantitative analysis"
                ])
            
            # Based on signal quality
            quality_score = quality_assessment.get('quality_score', 0)
            if quality_score < 0.7:
                recommendations.extend([
                    "Improve signal quality before quantitative analysis",
                    "Consider signal averaging or filtering"
                ])
            
            # Based on peaks detected
            peaks_detected = peak_analysis.get('peaks_detected', 0)
            if peaks_detected > 2:
                recommendations.append("Multiple peaks detected - check for interferences")
            
            # Remove duplicates
            recommendations = list(set(recommendations))
            
        except Exception as e:
            self.logger.warning(f"Expert recommendation generation failed: {e}")
        
        return recommendations
    
    def _create_measurement_summary(self, voltage: np.ndarray, current: np.ndarray,
                                  context: ElectrochemicalContext,
                                  peak_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive measurement summary"""
        try:
            return {
                'measurement_type': context.measurement_type.value,
                'data_points': len(voltage),
                'potential_range': {
                    'min': float(np.min(voltage[np.isfinite(voltage)])),
                    'max': float(np.max(voltage[np.isfinite(voltage)]))
                },
                'current_range': {
                    'min': float(np.min(current[np.isfinite(current)])),
                    'max': float(np.max(current[np.isfinite(current)]))
                },
                'peaks_detected': peak_analysis.get('peaks_detected', 0),
                'conditions': {
                    'electrode': context.electrode_material,
                    'electrolyte': context.electrolyte,
                    'ph': context.ph,
                    'temperature': context.temperature,
                    'scan_rate': context.scan_rate
                }
            }
            
        except Exception as e:
            self.logger.warning(f"Summary creation failed: {e}")
            return {'error': str(e)}
    
    def get_intelligence_summary(self) -> Dict[str, Any]:
        """Get summary of intelligence system status"""
        return {
            'ml_models_available': ML_MODELS_AVAILABLE,
            'analysis_count': self.analysis_count,
            'compound_database_entries': len(self.compound_database),
            'expert_rules': len(self.expert_rules),
            'config': self.config
        }

# Demo function
def demo_electrochemical_intelligence():
    """Demonstrate electrochemical intelligence capabilities"""
    print("🧠 Electrochemical Intelligence Demo")
    print("=" * 45)
    
    # Create intelligence system
    ei = ElectrochemicalIntelligence()
    
    # Generate synthetic CV data
    voltage = np.linspace(-0.5, 0.5, 1000)
    
    # Simulate dopamine CV (reversible redox couple)
    current = (2e-6 * np.exp(-((voltage - 0.15) / 0.03) ** 2) -    # Oxidation peak
              1.8e-6 * np.exp(-((voltage - 0.09) / 0.03) ** 2) +     # Reduction peak
              np.random.normal(0, 1e-7, len(voltage)))               # Noise
    
    # Create measurement context
    context = ElectrochemicalContext(
        measurement_type=MeasurementType.CV,
        electrode_material="Glassy Carbon",
        electrolyte="PBS pH 7.4",
        ph=7.4,
        temperature=25.0,
        scan_rate=0.1
    )
    
    print("Generated synthetic dopamine CV data:")
    print(f"  Voltage range: {np.min(voltage):.1f} to {np.max(voltage):.1f} V")
    print(f"  Peak current: ~{np.max(current)*1e6:.1f} μA")
    print(f"  Context: {context.measurement_type.value} on {context.electrode_material}")
    
    # Perform intelligent analysis
    print(f"\nPerforming intelligent analysis...")
    
    # Optional calibration data
    calibration_data = [
        (1e-6, 1e-6),    # 1 μM → 1 μA
        (5e-6, 4.8e-6),  # 5 μM → 4.8 μA
        (10e-6, 9.2e-6), # 10 μM → 9.2 μA
    ]
    
    analysis = ei.analyze_measurement(voltage, current, context, calibration_data)
    
    # Display results
    print(f"\n📊 Analysis Results:")
    print(f"  Processing time: {analysis.processing_time:.2f} seconds")
    print(f"  Peaks detected: {analysis.peak_analysis.get('peaks_detected', 0)}")
    
    # Quality assessment
    qa = analysis.quality_assessment
    print(f"\n🔍 Signal Quality:")
    print(f"  Quality score: {qa.get('quality_score', 0):.2f}/1.0")
    print(f"  SNR: {qa.get('snr_db', 0):.1f} dB")
    
    # Analyte identification
    if analysis.analyte_identification:
        ai = analysis.analyte_identification
        print(f"\n🧪 Analyte Identification:")
        print(f"  Type: {ai.analyte_type.value}")
        print(f"  Confidence: {ai.confidence:.1%}")
        print(f"  Possible compounds: {', '.join(ai.possible_compounds[:3])}")
    
    # Concentration analysis
    if analysis.concentration_analysis and 'error' not in analysis.concentration_analysis:
        ca = analysis.concentration_analysis
        print(f"\n📈 Concentration Analysis:")
        print(f"  Predicted: {ca['predicted_concentration']*1e6:.2f} μM")
        print(f"  Method: {ca['method']}")
        print(f"  R²: {ca['r_squared']:.3f}")
    
    # Insights
    print(f"\n💡 Intelligent Insights ({len(analysis.insights)}):")
    for i, insight in enumerate(analysis.insights, 1):
        print(f"  {i}. {insight.title} (confidence: {insight.confidence:.1%})")
        print(f"     {insight.description}")
        if insight.recommendations:
            print(f"     Recommendations: {'; '.join(insight.recommendations[:2])}")
    
    # Expert recommendations
    print(f"\n👨‍🔬 Expert Recommendations:")
    for i, rec in enumerate(analysis.expert_recommendations[:5], 1):
        print(f"  {i}. {rec}")
    
    # System summary
    summary = ei.get_intelligence_summary()
    print(f"\n🤖 System Summary:")
    print(f"  ML Models Available: {summary['ml_models_available']}")
    print(f"  Analyses Performed: {summary['analysis_count']}")
    print(f"  Compound Database: {summary['compound_database_entries']} entries")
    print(f"  Expert Rules: {summary['expert_rules']} rules")
    
    return ei, analysis

if __name__ == "__main__":
    demo_electrochemical_intelligence()
