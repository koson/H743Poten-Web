# CV Analysis with ML Prediction - Extended Architecture

## Enhanced System Architecture with ML Prediction

```mermaid
graph TB
    subgraph "CV Analysis System with ML Prediction"
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
        
        subgraph "ML Prediction Engine"
            E1[Quantitative Analyzer]
            E2[Concentration Predictor]
            E3[Substance Classifier]
            E4[Regression Models]
        end
        
        subgraph "Output Layer"
            F1[Visualization Engine]
            F2[Report Generator]
            F3[API Endpoints]
            F4[Prediction Dashboard]
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
        D2 --> E1
        D2 --> E2
        D2 --> E3
        E1 --> E4
        E2 --> E4
        E3 --> E4
        D3 --> F1
        E4 --> F1
        E4 --> F2
        E4 --> F3
        E4 --> F4
    end
```

## ML Prediction Pipeline

```mermaid
sequenceDiagram
    participant CVData as CV Data
    participant PeakDetector as Peak Detector
    participant FeatureExtractor as Feature Extractor
    participant QuantAnalyzer as Quantitative Analyzer
    participant ConcPredictor as Concentration Predictor
    participant SubstClassifier as Substance Classifier
    participant Dashboard as Results Dashboard
    
    CVData->>PeakDetector: Raw CV Data
    PeakDetector->>PeakDetector: Detect Peaks
    PeakDetector->>FeatureExtractor: Peak Positions & Currents
    
    FeatureExtractor->>FeatureExtractor: Extract Features
    Note over FeatureExtractor: Peak height, width, area,<br/>potential, shape descriptors
    
    par Parallel ML Analysis
        FeatureExtractor->>QuantAnalyzer: Peak Features
        QuantAnalyzer->>QuantAnalyzer: Calculate Quantities
        QuantAnalyzer->>Dashboard: Quantitative Results
    and
        FeatureExtractor->>ConcPredictor: Peak Features
        ConcPredictor->>ConcPredictor: Predict Concentrations
        ConcPredictor->>Dashboard: Concentration Predictions
    and
        FeatureExtractor->>SubstClassifier: Peak Features
        SubstClassifier->>SubstClassifier: Classify Substances
        SubstClassifier->>Dashboard: Classification Results
    end
    
    Dashboard->>Dashboard: Combine All Results
    Dashboard->>CVData: Final Analysis Report
```

## Feature Engineering for ML Prediction

```mermaid
mindmap
    root((CV Features))
        Peak Characteristics
            Peak Height (Current)
            Peak Potential
            Peak Width (FWHM)
            Peak Area
            Peak Asymmetry
            Peak Sharpness
        Electrochemical Properties
            Anodic Peak Current
            Cathodic Peak Current
            Peak Separation
            Current Ratio (Ipa/Ipc)
            Half-wave Potential
        Signal Properties
            Baseline Current
            Noise Level
            Signal-to-Noise Ratio
            Slope at Peak
            Curvature
        Derived Features
            Normalized Peak Height
            Peak Density
            Multi-peak Interactions
            Scan Rate Dependencies
            Temperature Corrections
```

## ML Models Architecture

```mermaid
classDiagram
    class FeatureExtractor {
        +extract_peak_features(peaks: List~Peak~) DataFrame
        +calculate_electrochemical_features(cv_data: CVData) dict
        +normalize_features(features: DataFrame) DataFrame
        +select_features(features: DataFrame) DataFrame
    }
    
    class QuantitativeAnalyzer {
        -calibration_models: dict
        -linear_models: List~LinearRegression~
        +fit_calibration_curve(concentrations: array, currents: array) void
        +predict_quantity(peak_current: float) float
        +calculate_detection_limit() float
        +validate_linearity() dict
    }
    
    class ConcentrationPredictor {
        -regression_models: dict
        -ensemble_model: VotingRegressor
        +train_models(features: DataFrame, concentrations: array) void
        +predict_concentration(features: array) Prediction
        +get_prediction_uncertainty() float
        +cross_validate() dict
    }
    
    class SubstanceClassifier {
        -classification_models: dict
        -substance_database: DataFrame
        +train_classifier(features: DataFrame, labels: array) void
        +classify_substance(features: array) Classification
        +get_classification_probability() dict
        +identify_unknown_substances() List~str~
    }
    
    class Prediction {
        +value: float
        +confidence: float
        +uncertainty: float
        +method: str
        +metadata: dict
    }
    
    class Classification {
        +substance_name: str
        +probability: float
        +alternative_matches: List~dict~
        +confidence_score: float
        +metadata: dict
    }
    
    FeatureExtractor --> QuantitativeAnalyzer
    FeatureExtractor --> ConcentrationPredictor
    FeatureExtractor --> SubstanceClassifier
    ConcentrationPredictor --> Prediction
    SubstanceClassifier --> Classification
```

## Database Schema for ML Predictions

```mermaid
erDiagram
    CV_Measurement {
        id int PK
        name string
        upload_date datetime
        file_path string
        scan_rate float
        voltage_range string
        cycles int
        status string
    }
    
    Peak_Detection_Result {
        id int PK
        measurement_id int FK
        method_type string
        detection_time datetime
        peak_count int
        processing_time float
        confidence_score float
    }
    
    Peak {
        id int PK
        result_id int FK
        peak_type string
        position_voltage float
        peak_current float
        peak_width float
        area_under_curve float
        confidence float
    }
    
    Feature_Set {
        id int PK
        peak_id int FK
        feature_name string
        feature_value float
        feature_type string
        extraction_method string
    }
    
    Quantitative_Analysis {
        id int PK
        measurement_id int FK
        substance_name string
        predicted_quantity float
        quantity_unit string
        confidence float
        method_used string
        calibration_r2 float
    }
    
    Concentration_Prediction {
        id int PK
        measurement_id int FK
        predicted_concentration float
        concentration_unit string
        prediction_uncertainty float
        model_used string
        cross_validation_score float
    }
    
    Substance_Classification {
        id int PK
        measurement_id int FK
        predicted_substance string
        classification_probability float
        alternative_substances json
        confidence_score float
        classification_method string
    }
    
    Calibration_Data {
        id int PK
        substance_name string
        known_concentration float
        measured_current float
        measurement_conditions json
        created_date datetime
    }
    
    CV_Measurement ||--o{ Peak_Detection_Result : "has results"
    Peak_Detection_Result ||--o{ Peak : "contains peaks"
    Peak ||--o{ Feature_Set : "has features"
    CV_Measurement ||--o{ Quantitative_Analysis : "has quantitative results"
    CV_Measurement ||--o{ Concentration_Prediction : "has concentration predictions"
    CV_Measurement ||--o{ Substance_Classification : "has substance classifications"
```

## ML Training Data Flow

```mermaid
flowchart TD
    A[Known Sample Data] --> B[CV Measurement]
    B --> C[Peak Detection]
    C --> D[Feature Extraction]
    D --> E[Feature Engineering]
    
    F[Ground Truth Labels] --> G{Label Type}
    G -->|Concentration| H[Concentration Labels]
    G -->|Substance| I[Substance Labels]
    G -->|Quantity| J[Quantity Labels]
    
    E --> K[Feature Matrix]
    H --> L[Training Dataset]
    I --> L
    J --> L
    K --> L
    
    L --> M{Model Type}
    M -->|Regression| N[Train Regression Models]
    M -->|Classification| O[Train Classification Models]
    M -->|Ensemble| P[Train Ensemble Models]
    
    N --> Q[Model Validation]
    O --> Q
    P --> Q
    
    Q --> R{Performance OK?}
    R -->|No| S[Hyperparameter Tuning]
    S --> N
    R -->|Yes| T[Deploy Models]
    
    T --> U[Production Prediction]
    
    style A fill:#e8f5e8
    style U fill:#c8e6c9
    style S fill:#ffecb3
```

## Prediction Algorithms

### 1. Quantitative Analysis
```python
# Linear calibration curve
concentration = (peak_current - intercept) / slope

# Multi-component analysis
concentrations = solve_linear_system(peak_matrix, current_vector)

# Non-linear calibration
concentration = polynomial_fit(peak_current, calibration_coefficients)
```

### 2. Concentration Prediction
```python
# Feature-based regression
concentration = ensemble_regressor.predict(features)

# Uncertainty quantification
uncertainty = std(bootstrap_predictions)

# Confidence intervals
ci_lower, ci_upper = quantile_regression(features, [0.025, 0.975])
```

### 3. Substance Classification
```python
# Multi-class classification
substance_probs = classifier.predict_proba(features)

# Similarity matching
similarity_scores = cosine_similarity(features, reference_database)

# Ensemble voting
final_prediction = voting_classifier.predict(features)
```

## Performance Metrics for ML Models

```mermaid
graph LR
    subgraph "Regression Metrics"
        A1[R² Score]
        A2[RMSE]
        A3[MAE]
        A4[MAPE]
    end
    
    subgraph "Classification Metrics"
        B1[Accuracy]
        B2[Precision]
        B3[Recall]
        B4[F1-Score]
        B5[AUC-ROC]
    end
    
    subgraph "Cross-Validation"
        C1[K-Fold CV]
        C2[Stratified CV]
        C3[Time Series CV]
    end
    
    subgraph "Business Metrics"
        D1[Detection Limit]
        D2[Linear Range]
        D3[Prediction Speed]
        D4[Model Size]
    end
```

## Real-time Prediction Integration

```mermaid
stateDiagram-v2
    [*] --> DataReceived
    DataReceived --> PeakDetection
    PeakDetection --> FeatureExtraction
    FeatureExtraction --> ModelPrediction
    
    state ModelPrediction {
        [*] --> LoadModels
        LoadModels --> QuantitativeAnalysis
        LoadModels --> ConcentrationPrediction
        LoadModels --> SubstanceClassification
        
        QuantitativeAnalysis --> CombineResults
        ConcentrationPrediction --> CombineResults
        SubstanceClassification --> CombineResults
    }
    
    ModelPrediction --> ValidationCheck
    ValidationCheck --> UpdateDashboard
    UpdateDashboard --> [*]
    
    ValidationCheck --> AlertSystem : Low Confidence
    AlertSystem --> ManualReview
    ManualReview --> UpdateDashboard
```

## API Endpoints for ML Predictions

```mermaid
graph TB
    subgraph "Prediction API"
        A1[POST /api/predict/quantity]
        A2[POST /api/predict/concentration]
        A3[POST /api/predict/substance]
        A4[POST /api/predict/all]
    end
    
    subgraph "Model Management API"
        B1[GET /api/models/list]
        B2[POST /api/models/train]
        B3[POST /api/models/retrain]
        B4[GET /api/models/performance]
    end
    
    subgraph "Calibration API"
        C1[POST /api/calibration/add-data]
        C2[GET /api/calibration/curves]
        C3[POST /api/calibration/validate]
        C4[GET /api/calibration/statistics]
    end
```

---
*Extended Architecture with ML Prediction*  
*Version: 1.1*  
*Date: August 15, 2025*
