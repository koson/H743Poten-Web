# CV Peak Analysis - System Design Plan

## Overview
แผนการพัฒนาระบบวิเคราะห์ Peak ใน Cyclic Voltammetry (CV) โดยใช้เทคนิคหลากหลายเพื่อเปรียบเทียบประสิทธิภาพ

## System Architecture

```mermaid
graph TB
    subgraph "CV Peak Analysis System"
        subgraph "Data Layer"
            A1[CSV Data Loader]
            A2[Database Connector]
            A3[Real-time Data Stream]
        end
        
        subgraph "Preprocessing Layer"
            B1[Data Validator]
            B2[Noise Filter]
            B3[Data Normalizer]
            B4[Baseline Corrector]
        end
        
        subgraph "Peak Detection Methods"
            C1[Traditional Method]
            C2[Statistical Method]
            C3[ML Method]
        end
        
        subgraph "Analysis Engine"
            D1[Peak Extractor]
            D2[Feature Calculator]
            D3[Performance Evaluator]
        end
        
        subgraph "Output Layer"
            E1[Visualization Engine]
            E2[Report Generator]
            E3[API Endpoints]
        end
        
        A1 --> B1
        A2 --> B1
        A3 --> B1
        B1 --> B2
        B2 --> B3
        B3 --> B4
        B4 --> C1
        B4 --> C2
        B4 --> C3
        C1 --> D1
        C2 --> D1
        C3 --> D1
        D1 --> D2
        D2 --> D3
        D3 --> E1
        D3 --> E2
        D3 --> E3
    end
```

## Peak Detection Methods Detail

```mermaid
classDiagram
    class PeakDetector {
        <<abstract>>
        +detect_peaks(data) List~Peak~
        +validate_peaks(peaks) bool
        +get_performance_metrics() dict
    }
    
    class TraditionalDetector {
        -baseline_method: str
        -threshold: float
        +find_baseline(data) float
        +detect_manual_peaks(data) List~Peak~
        +calculate_peak_current() float
    }
    
    class StatisticalDetector {
        -derivative_order: int
        -window_size: int
        -threshold_factor: float
        +apply_smoothing(data) array
        +calculate_derivatives(data) array
        +find_turning_points(data) List~int~
    }
    
    class MLDetector {
        -model_type: str
        -features: List~str~
        -is_trained: bool
        +extract_features(data) array
        +train_model(training_data) void
        +predict_peaks(data) List~Peak~
    }
    
    class Peak {
        +position: float
        +current: float
        +potential: float
        +peak_type: str
        +confidence: float
    }
    
    PeakDetector <|-- TraditionalDetector
    PeakDetector <|-- StatisticalDetector
    PeakDetector <|-- MLDetector
    PeakDetector --> Peak
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant WebAPI
    participant DataProcessor
    participant TraditionalDetector
    participant StatisticalDetector
    participant MLDetector
    participant PerformanceEvaluator
    participant Visualizer
    
    User->>WebAPI: Upload CV Data
    WebAPI->>DataProcessor: Validate & Preprocess
    DataProcessor->>DataProcessor: Clean & Normalize Data
    
    par Traditional Detection
        DataProcessor->>TraditionalDetector: Process Data
        TraditionalDetector->>TraditionalDetector: Find Baseline
        TraditionalDetector->>TraditionalDetector: Detect Peaks
    and Statistical Detection
        DataProcessor->>StatisticalDetector: Process Data
        StatisticalDetector->>StatisticalDetector: Apply Smoothing
        StatisticalDetector->>StatisticalDetector: Calculate Derivatives
        StatisticalDetector->>StatisticalDetector: Find Peaks
    and ML Detection
        DataProcessor->>MLDetector: Process Data
        MLDetector->>MLDetector: Extract Features
        MLDetector->>MLDetector: Predict Peaks
    end
    
    TraditionalDetector->>PerformanceEvaluator: Return Results
    StatisticalDetector->>PerformanceEvaluator: Return Results
    MLDetector->>PerformanceEvaluator: Return Results
    
    PerformanceEvaluator->>PerformanceEvaluator: Compare Methods
    PerformanceEvaluator->>Visualizer: Generate Comparison
    Visualizer->>WebAPI: Return Visualization
    WebAPI->>User: Display Results
```

## File Structure Plan

```
src/ai/cv_analysis/
├── __init__.py
├── peak_detection/
│   ├── __init__.py
│   ├── base_detector.py          # Abstract base class
│   ├── traditional_detector.py   # Baseline + manual method
│   ├── statistical_detector.py   # Derivative + threshold method
│   └── ml_detector.py            # Machine learning method
├── preprocessing/
│   ├── __init__.py
│   ├── data_loader.py           # Load CV data from various sources
│   ├── noise_filter.py          # Remove noise and artifacts
│   └── normalizer.py            # Data normalization
├── analysis/
│   ├── __init__.py
│   ├── peak_analyzer.py         # Peak feature extraction
│   ├── performance_evaluator.py # Compare method performance
│   └── validator.py             # Validate peak detection results
├── prediction/
│   ├── __init__.py
│   ├── feature_extractor.py     # Extract features for ML prediction
│   ├── quantitative_analyzer.py # Quantitative analysis & calibration
│   ├── concentration_predictor.py # Concentration prediction models
│   ├── substance_classifier.py  # Substance classification
│   └── model_trainer.py         # ML model training utilities
├── visualization/
│   ├── __init__.py
│   ├── cv_plotter.py           # Plot CV curves with peaks
│   ├── comparison_plotter.py    # Compare detection methods
│   └── prediction_plotter.py    # Visualize prediction results
└── models/
    ├── __init__.py
    ├── peak_model.py           # Peak data model
    ├── analysis_result.py      # Analysis result model
    ├── prediction_model.py     # Prediction result model
    └── calibration_model.py    # Calibration data model
```

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Create base data models (Peak, AnalysisResult)
- [ ] Implement data loader and preprocessing
- [ ] Set up basic project structure

### Phase 2: Traditional Method (Week 2)
- [ ] Implement baseline detection
- [ ] Manual peak detection algorithm
- [ ] Basic visualization

### Phase 3: Statistical Method (Week 3)
- [ ] Derivative-based peak detection
- [ ] Threshold and filtering algorithms
- [ ] Smoothing and noise reduction

### Phase 4: ML Method (Week 4)
- [ ] Feature extraction for ML
- [ ] Train peak detection model
- [ ] Implement ML-based detector

### Phase 5: ML Prediction Models (Week 5)
- [ ] Feature engineering for prediction
- [ ] Quantitative analysis models
- [ ] Concentration prediction algorithms
- [ ] Substance classification models

### Phase 6: Integration & Comparison (Week 6)
- [ ] Performance evaluation framework
- [ ] Method comparison tools
- [ ] Prediction accuracy validation
- [ ] Web interface integration

## Performance Metrics

```mermaid
pie title Peak Detection Evaluation Metrics
    "Accuracy" : 25
    "Precision" : 25  
    "Recall" : 25
    "Processing Time" : 15
    "Robustness to Noise" : 10
```

## Technical Requirements

### Dependencies
```python
# Core scientific computing
numpy>=1.21.0
scipy>=1.7.0
pandas>=1.3.0

# Machine learning
scikit-learn>=1.0.0
tensorflow>=2.6.0  # or pytorch

# Visualization
matplotlib>=3.4.0
plotly>=5.0.0

# Signal processing
pywavelets>=1.1.0
```

### Hardware Requirements
- RAM: Minimum 8GB (16GB recommended for ML training)
- CPU: Multi-core processor for parallel processing
- Storage: 1GB for models and sample data

## API Design

```mermaid
graph LR
    A[POST /api/cv/analyze] --> B{Method Selection}
    B -->|traditional| C[Traditional Detection]
    B -->|statistical| D[Statistical Detection]  
    B -->|ml| E[ML Detection]
    B -->|all| F[Compare All Methods]
    
    C --> G[JSON Response]
    D --> G
    E --> G
    F --> G
```

## Configuration Options

```yaml
# config/cv_analysis.yaml
peak_detection:
  traditional:
    baseline_method: "linear"  # linear, polynomial, spline
    threshold_factor: 0.1
  
  statistical:
    derivative_order: 2
    window_size: 5
    smoothing_method: "savgol"  # savgol, moving_average
  
  ml:
    model_type: "random_forest"  # random_forest, svm, neural_network
    feature_set: ["current", "potential", "derivatives"]
    training_data_path: "data/training/"

visualization:
  plot_style: "scientific"
  color_scheme: "viridis"
  interactive: true
```

## Next Steps
1. Review and approve this design plan
2. Set up development environment
3. Begin Phase 1 implementation
4. Create sample test data
5. Implement continuous integration/testing

---
*Created: August 15, 2025*  
*Version: 1.0*  
*Author: Development Team*
