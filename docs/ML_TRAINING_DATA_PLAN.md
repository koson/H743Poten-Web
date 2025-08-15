# ML Training Data Collection & Strategy Plan

## Overview
แผนการเก็บข้อมูลและการ training สำหรับระบบ CV Peak Analysis และ ML Prediction

## Training Data Requirements

### 1. Data Categories และ Minimum Sample Size

```mermaid
graph TB
    subgraph "Training Data Categories"
        A[Peak Detection Training]
        B[Quantitative Analysis Training]
        C[Concentration Prediction Training]
        D[Substance Classification Training]
    end
    
    subgraph "Sample Size Requirements"
        A1[Peak Detection: 1,000+ CV curves]
        B1[Quantitative: 500+ per substance]
        C1[Concentration: 300+ per concentration level]
        D1[Classification: 200+ per substance class]
    end
    
    A --> A1
    B --> B1
    C --> C1
    D --> D1
    
    style A1 fill:#e8f5e8
    style B1 fill:#e3f2fd
    style C1 fill:#fff3e0
    style D1 fill:#fce4ec
```

### 2. Data Collection Matrix

| **Data Type** | **Minimum Samples** | **Recommended** | **Priority** | **Collection Method** |
|---------------|---------------------|-----------------|--------------|----------------------|
| **Peak Detection** | 1,000 CV curves | 5,000+ | High | Synthetic + Real |
| **Standard Solutions** | 50 per substance | 100+ | Critical | Laboratory |
| **Concentration Series** | 300 per series | 500+ | High | Calibration runs |
| **Substance Library** | 200 per class | 500+ | Medium | Literature + Lab |
| **Noise Variations** | 200 curves | 1,000+ | High | Synthetic |
| **Scan Rate Variations** | 100 per rate | 200+ | Medium | Systematic study |

## Data Collection Strategy

```mermaid
flowchart TD
    A[Data Collection Strategy] --> B[Synthetic Data Generation]
    A --> C[Laboratory Measurements]
    A --> D[Literature Data Mining]
    A --> E[Collaborative Data Sharing]
    
    B --> B1[Simulated CV Curves]
    B --> B2[Noise Addition]
    B --> B3[Parameter Variations]
    
    C --> C1[Standard Solutions]
    C --> C2[Mixed Samples]
    C --> C3[Real Matrices]
    
    D --> D1[Published Datasets]
    D --> D2[Reference Standards]
    D --> D3[Electrochemical Databases]
    
    E --> E1[Academic Partners]
    E --> E2[Industry Collaboration]
    E --> E3[Open Source Datasets]
    
    style B fill:#e8f5e8
    style C fill:#e3f2fd
    style D fill:#fff3e0
    style E fill:#fce4ec
```

## Detailed Training Data Specifications

### 1. Peak Detection Training Data

```mermaid
pie title Peak Detection Training Data Distribution
    "Clean CV Curves" : 30
    "Noisy Signals" : 25
    "Complex Mixtures" : 20
    "Edge Cases" : 15
    "Synthetic Data" : 10
```

**Requirements:**
- **1,000-5,000 CV curves** with manually annotated peaks
- **Peak annotations**: position, type (anodic/cathodic), confidence
- **Signal quality**: clean, noisy, baseline drift, interference
- **Complexity levels**: single peak, multiple peaks, overlapping peaks

**Data Format:**
```json
{
  "cv_data": {
    "voltage": [array],
    "current": [array],
    "scan_rate": 0.1,
    "cycles": 3
  },
  "peaks": [
    {
      "type": "anodic",
      "voltage": 0.25,
      "current": 1.2e-5,
      "confidence": 0.95,
      "width": 0.05
    }
  ],
  "metadata": {
    "substance": "Fe(CN)6",
    "concentration": 1e-3,
    "temperature": 25,
    "electrode": "GCE"
  }
}
```

### 2. Quantitative Analysis Training Data

```mermaid
graph LR
    A[Standard Solutions] --> B[Known Concentrations]
    B --> C[CV Measurements]
    C --> D[Peak Currents]
    D --> E[Linear Calibration]
    
    F[Quality Control] --> G[Replicate Measurements]
    G --> H[Statistical Validation]
    H --> I[R² > 0.995]
    
    style E fill:#c8e6c9
    style I fill:#c8e6c9
```

**Requirements per Substance:**
- **Minimum 50 calibration points** across linear range
- **5-7 concentration levels** minimum
- **3-5 replicates** per concentration
- **Detection limit** to **upper linear range**

**Priority Substances (Phase 1):**
1. **Ferrocyanide/Ferricyanide** (reference standard)
2. **Ascorbic Acid** (common analyte)
3. **Dopamine** (neurotransmitter)
4. **Glucose** (biosensor application)
5. **Heavy Metals** (Pb²⁺, Cd²⁺, Zn²⁺)

**Data Requirements:**
```python
# Example concentration series
concentrations = [1e-6, 5e-6, 1e-5, 5e-5, 1e-4, 5e-4, 1e-3]  # M
replicates = 5  # per concentration
total_per_substance = len(concentrations) * replicates  # 35 measurements
```

### 3. Concentration Prediction Training Data

```mermaid
graph TB
    subgraph "Feature Matrix"
        A[Peak Height]
        B[Peak Area]
        C[Peak Width]
        D[Potential]
        E[Background Current]
        F[Scan Rate]
        G[Temperature]
    end
    
    H[Concentration Labels] --> I[Training Matrix]
    A --> I
    B --> I
    C --> I
    D --> I
    E --> I
    F --> I
    G --> I
    
    I --> J[ML Models]
    J --> K[Cross Validation]
    K --> L[Performance Metrics]
```

**Requirements:**
- **300-500 samples** per concentration range
- **Multiple scan rates** (0.02-1.0 V/s)
- **Temperature variations** (15-35°C)
- **Different electrode conditions**
- **Matrix effects** (different background electrolytes)

**Feature Engineering:**
- **Electrochemical features**: Peak current, potential, width, asymmetry
- **Signal features**: Baseline, noise level, signal-to-noise ratio
- **Experimental conditions**: Scan rate, temperature, pH
- **Derived features**: Normalized values, ratios, interactions

### 4. Substance Classification Training Data

```mermaid
mindmap
    root((Substance Classes))
        Organic Compounds
            Ascorbic Acid
            Dopamine
            Caffeine
            Paracetamol
        Inorganic Ions
            Heavy Metals
                Lead
                Cadmium
                Zinc
            Transition Metals
                Iron
                Copper
                Nickel
        Biomolecules
            Glucose
            Uric Acid
            Amino Acids
        Synthetic Compounds
            Pharmaceuticals
            Pesticides
            Dyes
```

**Requirements per Substance Class:**
- **200-500 CV measurements** per substance
- **Various concentrations** (3-5 levels)
- **Different conditions** (pH, temperature, scan rate)
- **Potential interferences** included

**Priority Classification Tasks:**
1. **Binary Classification**: Target vs Non-target
2. **Multi-class**: 5-10 common substances
3. **Hierarchical**: Organic vs Inorganic → Specific substance

## Data Quality Standards

### 1. Data Validation Criteria

```mermaid
flowchart TD
    A[Raw CV Data] --> B{Quality Check}
    
    B -->|Pass| C[Data Preprocessing]
    B -->|Fail| D[Reject/Flag]
    
    C --> E{Feature Extraction}
    E -->|Valid| F[Add to Training Set]
    E -->|Invalid| G[Manual Review]
    
    G --> H{Expert Decision}
    H -->|Accept| F
    H -->|Reject| D
    
    F --> I[Training Database]
    D --> J[Quality Log]
    
    style F fill:#c8e6c9
    style D fill:#ffcdd2
```

**Quality Criteria:**
- **Signal-to-noise ratio** > 10:1
- **Peak reproducibility** < 5% RSD
- **Baseline stability** < 1% drift
- **No artifacts** (spikes, dropouts)
- **Complete scan range** coverage

### 2. Data Annotation Guidelines

```yaml
annotation_standards:
  peak_detection:
    manual_annotation: true
    expert_validation: required
    confidence_scoring: 1-10
    inter_annotator_agreement: >85%
    
  concentration_labels:
    preparation_method: documented
    uncertainty: ±5%
    traceability: required
    calibration_verification: mandatory
    
  substance_identity:
    purity: >95%
    certificate_analysis: required
    storage_conditions: controlled
    expiry_tracking: mandatory
```

## Training Dataset Structure

### Database Schema for Training Data

```sql
-- Training datasets
CREATE TABLE training_datasets (
    id SERIAL PRIMARY KEY,
    dataset_name VARCHAR(100),
    dataset_type VARCHAR(50), -- 'peak_detection', 'quantitative', 'classification'
    version VARCHAR(20),
    creation_date TIMESTAMP,
    description TEXT,
    total_samples INTEGER,
    quality_score FLOAT
);

-- Training samples
CREATE TABLE training_samples (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES training_datasets(id),
    sample_id VARCHAR(50) UNIQUE,
    cv_data JSONB,
    labels JSONB,
    metadata JSONB,
    quality_flags JSONB,
    annotation_confidence FLOAT,
    created_at TIMESTAMP
);

-- Ground truth annotations
CREATE TABLE ground_truth_annotations (
    id SERIAL PRIMARY KEY,
    sample_id VARCHAR(50),
    annotation_type VARCHAR(50),
    annotator_id VARCHAR(50),
    annotation_data JSONB,
    confidence_score FLOAT,
    validation_status VARCHAR(20),
    created_at TIMESTAMP
);

-- Training model performance
CREATE TABLE model_training_results (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100),
    dataset_version VARCHAR(20),
    training_date TIMESTAMP,
    performance_metrics JSONB,
    hyperparameters JSONB,
    cross_validation_scores JSONB,
    model_path VARCHAR(255)
);
```

## Data Collection Timeline

```mermaid
gantt
    title Training Data Collection Timeline
    dateFormat  YYYY-MM-DD
    section Phase 1: Foundation Data
    Reference Standards    :done, ref1, 2025-08-15, 10d
    Peak Detection Data    :active, peak1, 2025-08-20, 15d
    Basic Calibrations     :cal1, 2025-08-25, 12d
    
    section Phase 2: Expanded Dataset
    Multi-substance Data   :multi1, after peak1, 20d
    Complex Mixtures       :mix1, after cal1, 18d
    Interference Studies   :inter1, after multi1, 15d
    
    section Phase 3: Validation Data
    Independent Validation :val1, after inter1, 10d
    Blind Test Samples     :blind1, after val1, 8d
    External Validation    :ext1, after blind1, 12d
    
    section Phase 4: Continuous Collection
    Real-world Samples     :real1, after ext1, 30d
    Model Updates          :update1, after real1, ongoing
```

## Synthetic Data Generation

### 1. CV Curve Simulation

```python
def generate_synthetic_cv(
    substance_params: dict,
    noise_level: float = 0.01,
    baseline_drift: float = 0.001,
    scan_rate: float = 0.1
) -> dict:
    """
    Generate synthetic CV data with controlled parameters
    
    Parameters:
    - substance_params: E0, k0, alpha, concentration
    - noise_level: Gaussian noise standard deviation
    - baseline_drift: Linear baseline drift
    - scan_rate: Scan rate in V/s
    """
    pass
```

**Synthetic Data Benefits:**
- **Large volumes** (10,000+ curves quickly)
- **Controlled parameters** (known ground truth)
- **Edge cases** (extreme conditions)
- **Balanced datasets** (equal representation)
- **Cost effective** (no reagents needed)

### 2. Noise and Artifact Simulation

```mermaid
graph LR
    A[Clean Signal] --> B[Add Gaussian Noise]
    B --> C[Add Baseline Drift]
    C --> D[Add Spikes/Dropouts]
    D --> E[Add 50/60 Hz Interference]
    E --> F[Realistic Noisy Signal]
    
    style A fill:#e8f5e8
    style F fill:#ffecb3
```

## Training Strategy

### 1. Progressive Training Approach

```mermaid
graph TD
    A[Phase 1: Clean Data] --> B[Basic Models]
    B --> C[Phase 2: Add Noise]
    C --> D[Robust Models]
    D --> E[Phase 3: Complex Cases]
    E --> F[Advanced Models]
    F --> G[Phase 4: Real Data]
    G --> H[Production Models]
    
    style A fill:#e8f5e8
    style H fill:#c8e6c9
```

### 2. Cross-Validation Strategy

```python
# Training split strategy
train_split = 0.70  # 70% training
val_split = 0.15    # 15% validation  
test_split = 0.15   # 15% testing

# Time-series aware splits for temporal data
# Stratified splits for classification
# Group splits for substance-wise independence
```

### 3. Model Performance Targets

| **Model Type** | **Metric** | **Minimum** | **Target** | **Excellent** |
|----------------|------------|-------------|------------|---------------|
| **Peak Detection** | F1-Score | 0.85 | 0.90 | 0.95 |
| **Quantitative** | R² | 0.95 | 0.98 | 0.995 |
| **Concentration** | MAPE | <15% | <10% | <5% |
| **Classification** | Accuracy | 0.85 | 0.90 | 0.95 |

## Data Management Infrastructure

### 1. Storage Requirements

```mermaid
pie title Storage Allocation (Total: 500GB)
    "Raw CV Data" : 40
    "Processed Features" : 20
    "Trained Models" : 15
    "Synthetic Data" : 15
    "Backup & Versioning" : 10
```

### 2. Data Pipeline

```mermaid
flowchart LR
    A[Data Collection] --> B[Quality Control]
    B --> C[Preprocessing]
    C --> D[Feature Extraction]
    D --> E[Data Augmentation]
    E --> F[Training Database]
    
    F --> G[Model Training]
    G --> H[Model Validation]
    H --> I[Model Deployment]
    
    J[Continuous Collection] --> B
    I --> K[Performance Monitoring]
    K --> J
    
    style F fill:#e3f2fd
    style I fill:#c8e6c9
```

## Implementation Priority

### Week 1-2: Foundation Dataset
- [ ] Set up data collection infrastructure
- [ ] Collect 100 reference standard measurements
- [ ] Generate 1,000 synthetic CV curves
- [ ] Create basic peak annotations

### Week 3-4: Quantitative Data
- [ ] Collect calibration data for 3 priority substances
- [ ] 50 points per substance (150 total)
- [ ] Validate linearity and reproducibility

### Week 5-6: Classification Data
- [ ] Collect 200 samples for 5 substance classes
- [ ] Include concentration variations
- [ ] Add interference studies

### Week 7-8: Validation & Testing
- [ ] Independent validation dataset
- [ ] Blind test samples
- [ ] Performance benchmarking

---
*ML Training Data Collection Plan*  
*Version: 1.0*  
*Created: August 15, 2025*
