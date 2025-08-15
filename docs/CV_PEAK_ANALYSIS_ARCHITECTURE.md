# CV Peak Analysis - Technical Architecture

## Component Interaction Diagram

```mermaid
graph TD
    subgraph "Web Interface Layer"
        UI[React/Vue Frontend]
        API[Flask API Routes]
    end
    
    subgraph "Business Logic Layer"
        subgraph "Peak Detection Service"
            PDS[Peak Detection Service]
            PDS --> TD[Traditional Detector]
            PDS --> SD[Statistical Detector]
            PDS --> MLD[ML Detector]
        end
        
        subgraph "Data Processing Service"
            DPS[Data Processing Service]
            DPS --> DL[Data Loader]
            DPS --> NF[Noise Filter]
            DPS --> DN[Data Normalizer]
        end
        
        subgraph "Analysis Service"
            AS[Analysis Service]
            AS --> PA[Peak Analyzer]
            AS --> PE[Performance Evaluator]
            AS --> VL[Validator]
        end
    end
    
    subgraph "Data Access Layer"
        subgraph "Data Sources"
            CSV[CSV Files]
            DB[Database]
            RT[Real-time Stream]
        end
        
        subgraph "Storage"
            FS[File System]
            CACHE[Redis Cache]
            MODELS[ML Models Store]
        end
    end
    
    UI --> API
    API --> PDS
    API --> DPS
    API --> AS
    
    DPS --> CSV
    DPS --> DB
    DPS --> RT
    
    PDS --> FS
    AS --> CACHE
    MLD --> MODELS
    
    style UI fill:#e1f5fe
    style API fill:#f3e5f5
    style PDS fill:#e8f5e8
    style DPS fill:#fff3e0
    style AS fill:#fce4ec
```

## Database Schema Design

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
    
    Performance_Metric {
        id int PK
        result_id int FK
        metric_name string
        metric_value float
        unit string
    }
    
    ML_Model {
        id int PK
        model_name string
        model_type string
        training_date datetime
        accuracy float
        model_path string
        parameters json
    }
    
    CV_Measurement ||--o{ Peak_Detection_Result : "has results"
    Peak_Detection_Result ||--o{ Peak : "contains peaks"
    Peak_Detection_Result ||--o{ Performance_Metric : "has metrics"
    ML_Model ||--o{ Peak_Detection_Result : "generates"
```

## State Management Flow

```mermaid
stateDiagram-v2
    [*] --> DataUploaded
    DataUploaded --> Preprocessing
    Preprocessing --> MethodSelection
    
    MethodSelection --> TraditionalProcessing
    MethodSelection --> StatisticalProcessing
    MethodSelection --> MLProcessing
    MethodSelection --> AllMethodsProcessing
    
    TraditionalProcessing --> PeakExtracted
    StatisticalProcessing --> PeakExtracted
    MLProcessing --> PeakExtracted
    AllMethodsProcessing --> PeakExtracted
    
    PeakExtracted --> ResultAnalysis
    ResultAnalysis --> PerformanceEvaluation
    PerformanceEvaluation --> Visualization
    
    Visualization --> ResultDisplayed
    ResultDisplayed --> [*]
    
    ResultDisplayed --> MethodSelection : Reanalyze
    
    note right of MLProcessing
        Requires trained model
        Feature extraction
        Prediction confidence
    end note
    
    note right of PerformanceEvaluation
        Compare accuracy
        Processing time
        Robustness metrics
    end note
```

## Microservices Architecture (Future Scaling)

```mermaid
graph TB
    subgraph "Frontend Services"
        WEB[Web Dashboard]
        MOBILE[Mobile App]
        API_GW[API Gateway]
    end
    
    subgraph "Core Services"
        AUTH[Authentication Service]
        DATA[Data Management Service]
        DETECT[Peak Detection Service]
        ANALYSIS[Analysis Service]
        VIZ[Visualization Service]
    end
    
    subgraph "ML Services"
        TRAIN[Model Training Service]
        PREDICT[Prediction Service]
        FEATURE[Feature Extraction Service]
    end
    
    subgraph "Infrastructure Services"
        CONFIG[Configuration Service]
        LOG[Logging Service]
        MONITOR[Monitoring Service]
        CACHE[Cache Service]
    end
    
    subgraph "Data Storage"
        POSTGRES[(PostgreSQL)]
        REDIS[(Redis)]
        S3[(Object Storage)]
        ELASTIC[(Elasticsearch)]
    end
    
    WEB --> API_GW
    MOBILE --> API_GW
    API_GW --> AUTH
    API_GW --> DATA
    API_GW --> DETECT
    API_GW --> ANALYSIS
    API_GW --> VIZ
    
    DETECT --> TRAIN
    DETECT --> PREDICT
    DETECT --> FEATURE
    
    DATA --> POSTGRES
    CACHE --> REDIS
    TRAIN --> S3
    LOG --> ELASTIC
    
    style WEB fill:#e3f2fd
    style MOBILE fill:#e3f2fd
    style API_GW fill:#f3e5f5
    style AUTH fill:#e8f5e8
    style DETECT fill:#fff3e0
    style TRAIN fill:#fce4ec
```

## Security & Performance Considerations

```mermaid
mindmap
    root((CV Peak Analysis))
        Security
            Authentication
                JWT Tokens
                OAuth 2.0
                Role-based Access
            Data Protection
                Encryption at Rest
                Encryption in Transit
                Input Validation
            API Security
                Rate Limiting
                CORS Configuration
                Input Sanitization
        Performance
            Caching Strategy
                Redis for Results
                CDN for Static Assets
                Browser Caching
            Optimization
                Async Processing
                Background Tasks
                Database Indexing
            Scalability
                Horizontal Scaling
                Load Balancing
                Auto-scaling
        Monitoring
            Metrics
                Response Time
                Error Rates
                Resource Usage
            Logging
                Structured Logging
                Error Tracking
                Audit Trail
            Alerting
                Performance Alerts
                Error Notifications
                Capacity Warnings
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        DEV_APP[Development App]
        DEV_DB[(Dev Database)]
        DEV_CACHE[(Dev Cache)]
    end
    
    subgraph "Staging Environment"
        STAGE_APP[Staging App]
        STAGE_DB[(Staging Database)]
        STAGE_CACHE[(Staging Cache)]
    end
    
    subgraph "Production Environment"
        subgraph "Load Balancer"
            LB[Nginx Load Balancer]
        end
        
        subgraph "Application Tier"
            PROD_APP1[App Instance 1]
            PROD_APP2[App Instance 2]
            PROD_APP3[App Instance 3]
        end
        
        subgraph "Data Tier"
            PROD_DB[(Production Database)]
            PROD_CACHE[(Production Cache)]
            BACKUP[(Backup Storage)]
        end
        
        subgraph "Monitoring"
            PROMETHEUS[Prometheus]
            GRAFANA[Grafana]
            ALERT[AlertManager]
        end
    end
    
    DEV_APP --> STAGE_APP
    STAGE_APP --> LB
    
    LB --> PROD_APP1
    LB --> PROD_APP2
    LB --> PROD_APP3
    
    PROD_APP1 --> PROD_DB
    PROD_APP2 --> PROD_DB
    PROD_APP3 --> PROD_DB
    
    PROD_APP1 --> PROD_CACHE
    PROD_APP2 --> PROD_CACHE
    PROD_APP3 --> PROD_CACHE
    
    PROD_DB --> BACKUP
    
    PROMETHEUS --> GRAFANA
    PROMETHEUS --> ALERT
    
    style DEV_APP fill:#e8f5e8
    style STAGE_APP fill:#fff3e0
    style PROD_APP1 fill:#e3f2fd
    style PROD_APP2 fill:#e3f2fd
    style PROD_APP3 fill:#e3f2fd
```

---
*Technical Architecture Document*  
*Version: 1.0*  
*Date: August 15, 2025*
