# STM32 Integration Enhancement Plan

## Current System Analysis

ระบบปัจจุบันมีส่วนประกอบดังนี้:
- `SCPIHandler`: จัดการการสื่อสาร Serial กับ STM32
- `CSVDataEmulator`: จำลองข้อมูลจาก CSV files  
- `measurement_service.py`: บริการจัดการการวัด

## Enhanced Integration Architecture

```mermaid
graph TB
    subgraph "Current System"
        SCPI[SCPIHandler]
        CSV[CSVDataEmulator] 
        MS[MeasurementService]
    end
    
    subgraph "New CV Peak Analysis Integration"
        subgraph "Data Acquisition Layer"
            DAL[DataAcquisitionService]
            RDS[RealTimeDataStream]
            BUF[DataBuffer]
        end
        
        subgraph "Processing Pipeline"
            DP[DataProcessor]
            TD[TraditionalDetector]
            SD[StatisticalDetector]
            MD[MLDetector]
        end
        
        subgraph "Real-time Analysis"
            RTA[RealTimeAnalyzer]
            LViz[LiveVisualization]
            ALERT[AlertSystem]
        end
    end
    
    SCPI --> DAL
    CSV --> DAL
    MS --> DAL
    
    DAL --> RDS
    RDS --> BUF
    BUF --> DP
    
    DP --> TD
    DP --> SD  
    DP --> MD
    
    TD --> RTA
    SD --> RTA
    MD --> RTA
    
    RTA --> LViz
    RTA --> ALERT
    
    style SCPI fill:#e3f2fd
    style DAL fill:#e8f5e8
    style RTA fill:#fff3e0
```

## Code Structure Enhancement

```mermaid
classDiagram
    class DataAcquisitionService {
        -scpi_handler: SCPIHandler
        -csv_emulator: CSVDataEmulator
        -data_stream: RealTimeDataStream
        +start_acquisition(source: str) bool
        +stop_acquisition() void
        +get_data_stream() Iterator~CVDataPoint~
        +switch_data_source(source: str) void
    }
    
    class RealTimeDataStream {
        -buffer: CircularBuffer
        -subscribers: List~Callable~
        +add_data_point(point: CVDataPoint) void
        +subscribe(callback: Callable) void
        +get_latest_chunk(size: int) List~CVDataPoint~
        +get_streaming_data() Iterator~CVDataPoint~
    }
    
    class CVDataPoint {
        +timestamp: float
        +voltage: float
        +current: float
        +temperature: float
        +source: str
        +quality_flags: dict
        +to_dict() dict
        +from_dict(data: dict) CVDataPoint
    }
    
    class RealTimeAnalyzer {
        -detectors: List~PeakDetector~
        -chunk_size: int
        -analysis_queue: Queue
        +process_data_chunk(data: List~CVDataPoint~) AnalysisResult
        +add_detector(detector: PeakDetector) void
        +get_live_results() LiveAnalysisResult
    }
    
    class LiveAnalysisResult {
        +peaks: List~Peak~
        +confidence: float
        +processing_time: float
        +method_used: str
        +timestamp: datetime
        +metadata: dict
    }
    
    DataAcquisitionService --> RealTimeDataStream
    RealTimeDataStream --> CVDataPoint
    RealTimeAnalyzer --> CVDataPoint
    RealTimeAnalyzer --> LiveAnalysisResult
```

## File Modifications Required

### 1. Enhanced SCPIHandler (src/hardware/scpi_handler.py)

```python
# Additional methods to add:

def start_cv_measurement(self, params: dict) -> bool:
    """Start CV measurement with specified parameters"""
    
def get_measurement_data(self) -> List[CVDataPoint]:
    """Get measurement data as structured data points"""
    
def configure_real_time_streaming(self, enable: bool = True) -> bool:
    """Configure real-time data streaming from STM32"""
    
def get_device_status(self) -> dict:
    """Get comprehensive device status"""
```

### 2. Enhanced CSVDataEmulator (src/hardware/csv_data_emulator.py)

```python
# Additional methods to add:

def get_data_stream(self) -> Iterator[CVDataPoint]:
    """Get data as a stream compatible with real-time processing"""
    
def simulate_real_time_measurement(self, callback: Callable) -> None:
    """Simulate real-time measurement with callback"""
    
def get_standardized_data_point(self, index: int) -> CVDataPoint:
    """Get data point in standardized format"""
```

### 3. New DataAcquisitionService

```python
# New file: src/services/data_acquisition_service.py

class DataAcquisitionService:
    """Unified service for acquiring data from various sources"""
    
    def __init__(self):
        self.scpi_handler = SCPIHandler()
        self.csv_emulator = CSVDataEmulator()
        self.current_source = None
        self.data_stream = RealTimeDataStream()
        
    def start_acquisition(self, source: str, **kwargs) -> bool:
        """Start data acquisition from specified source"""
        
    def get_unified_data_stream(self) -> Iterator[CVDataPoint]:
        """Get unified data stream regardless of source"""
```

## Real-time Processing Pipeline

```mermaid
sequenceDiagram
    participant STM32
    participant SCPI as SCPIHandler
    participant DAS as DataAcquisitionService
    participant RDS as RealTimeDataStream
    participant RTA as RealTimeAnalyzer
    participant PD as PeakDetector
    participant UI as WebInterface
    
    STM32->>SCPI: Send CV Data
    SCPI->>DAS: Raw Data
    DAS->>DAS: Parse & Validate
    DAS->>RDS: CVDataPoint
    RDS->>RTA: Data Chunk
    
    par Real-time Detection
        RTA->>PD: Traditional Method
        RTA->>PD: Statistical Method
        RTA->>PD: ML Method
    end
    
    PD->>RTA: Peak Results
    RTA->>UI: Live Analysis
    UI->>UI: Update Visualization
    
    Note over RTA: Process in chunks for
    Note over RTA: real-time performance
```

## Configuration Updates

```yaml
# config/data_acquisition.yaml
data_acquisition:
  sources:
    stm32:
      enabled: true
      default_port: "COM3"
      baudrate: 115200
      timeout: 5
      
    csv_emulation:
      enabled: true
      default_file: "sample_data/cv_sample.csv"
      playback_speed: 1.0
      
  real_time:
    buffer_size: 1000
    chunk_size: 50
    processing_interval: 100  # ms
    max_latency: 500  # ms
    
  data_validation:
    enable_quality_checks: true
    voltage_range: [-2.0, 2.0]  # V
    current_range: [-1e-3, 1e-3]  # A
    
peak_detection:
  real_time:
    methods: ["statistical"]  # Fast methods for real-time
    confidence_threshold: 0.7
    
  batch:
    methods: ["traditional", "statistical", "ml"]  # All methods for final analysis
```

## API Endpoints Enhancement

```mermaid
graph LR
    subgraph "Enhanced Data API"
        A1[POST /api/data/start-acquisition]
        A2[GET /api/data/stream/live] 
        A3[POST /api/data/switch-source]
        A4[GET /api/data/status]
    end
    
    subgraph "Real-time Analysis API"
        B1[GET /api/analysis/live-stream]
        B2[POST /api/analysis/configure]
        B3[GET /api/analysis/live-peaks]
        B4[POST /api/analysis/alert-config]
    end
    
    subgraph "WebSocket API"
        C1[ws://api/stream/data]
        C2[ws://api/stream/analysis] 
        C3[ws://api/stream/alerts]
    end
```

## Database Schema for Real-time Data

```sql
-- Real-time measurement sessions
CREATE TABLE measurement_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    data_source VARCHAR(20),
    parameters JSONB,
    status VARCHAR(20),
    total_points INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Real-time data points (optional storage)
CREATE TABLE real_time_data_points (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(50),
    timestamp DOUBLE PRECISION,
    voltage DOUBLE PRECISION,
    current DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    quality_flags JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Real-time peak detections
CREATE TABLE real_time_peaks (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50),
    detection_timestamp TIMESTAMP,
    peak_type VARCHAR(10),
    voltage DOUBLE PRECISION,
    current DOUBLE PRECISION,
    method VARCHAR(20),
    confidence DOUBLE PRECISION,
    metadata JSONB
);

-- Indexes for performance
CREATE INDEX idx_session_timestamp ON real_time_data_points(session_id, timestamp);
CREATE INDEX idx_peaks_session ON real_time_peaks(session_id);
```

## Performance Optimization Strategies

```mermaid
mindmap
    root((Performance Optimization))
        Data Processing
            Chunked Processing
            Async Operations
            Memory Pooling
            Vectorized Operations
        Communication
            Binary Protocols
            Compression
            Connection Pooling
            Buffering
        Analysis
            Fast Algorithms
            Parallel Processing
            GPU Acceleration
            Caching
        Storage
            Streaming Inserts
            Batch Operations
            Indexing
            Partitioning
```

## Implementation Timeline

### Week 1: Foundation
- [ ] Create DataAcquisitionService
- [ ] Enhance SCPIHandler with streaming
- [ ] Implement RealTimeDataStream
- [ ] Basic WebSocket support

### Week 2: Real-time Analysis
- [ ] Create RealTimeAnalyzer
- [ ] Integrate with existing peak detectors
- [ ] Implement live visualization updates
- [ ] Add quality validation

### Week 3: Integration
- [ ] Connect all components
- [ ] Database schema implementation
- [ ] API endpoint creation
- [ ] Testing with real STM32

### Week 4: Optimization
- [ ] Performance tuning
- [ ] Error handling
- [ ] Documentation
- [ ] User interface improvements

## Testing Strategy

```mermaid
graph TD
    A[Unit Tests] --> B[Integration Tests]
    B --> C[Real-time Performance Tests]
    C --> D[End-to-End Tests]
    
    A1[Test Individual Components] --> A
    A2[Mock Data Sources] --> A
    
    B1[Test Data Flow] --> B
    B2[Test API Endpoints] --> B
    
    C1[Latency Tests] --> C
    C2[Throughput Tests] --> C
    C3[Memory Usage Tests] --> C
    
    D1[STM32 Hardware Tests] --> D
    D2[User Workflow Tests] --> D
    D3[Load Tests] --> D
```

---
*STM32 Integration Enhancement Plan*  
*Version: 1.0*  
*Created: August 15, 2025*
