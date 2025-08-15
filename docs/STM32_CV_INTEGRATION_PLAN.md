# STM32 to CV Peak Analysis Integration Plan

## Overview
แผนการเชื่อมต่อข้อมูล Cyclic Voltammetry จาก STM32 H743 Potentiostat เข้าสู่ระบบวิเคราะห์ Peak Detection

## Data Flow Architecture

```mermaid
graph TB
    subgraph "STM32 H743 Potentiostat"
        ADC[ADC Sampling]
        DAC[DAC Voltage Control]
        SCPI[SCPI Command Handler]
        USB[USB/UART Interface]
    end
    
    subgraph "Communication Layer"
        SERIAL[Serial Communication]
        MQTT[MQTT Broker]
        HTTP[HTTP REST API]
        WS[WebSocket Connection]
    end
    
    subgraph "Data Acquisition Service"
        DAS[Data Acquisition Service]
        BUFFER[Circular Buffer]
        VALIDATOR[Data Validator]
        FORMATTER[Data Formatter]
    end
    
    subgraph "CV Peak Analysis System"
        QUEUE[Message Queue]
        PROCESSOR[Data Processor]
        DETECTOR[Peak Detector]
        STORAGE[Data Storage]
    end
    
    subgraph "Real-time Monitoring"
        DASHBOARD[Live Dashboard]
        ALERTS[Alert System]
        EXPORT[Data Export]
    end
    
    ADC --> SCPI
    DAC --> SCPI
    SCPI --> USB
    USB --> SERIAL
    SERIAL --> DAS
    DAS --> BUFFER
    BUFFER --> VALIDATOR
    VALIDATOR --> FORMATTER
    FORMATTER --> QUEUE
    QUEUE --> PROCESSOR
    PROCESSOR --> DETECTOR
    DETECTOR --> STORAGE
    STORAGE --> DASHBOARD
    DETECTOR --> ALERTS
    STORAGE --> EXPORT
    
    %% Alternative paths
    USB -.-> MQTT
    USB -.-> HTTP
    USB -.-> WS
    MQTT -.-> DAS
    HTTP -.-> DAS
    WS -.-> DAS
    
    style STM32 fill:#e3f2fd
    style DAS fill:#e8f5e8
    style DETECTOR fill:#fff3e0
    style DASHBOARD fill:#fce4ec
```

## STM32 Data Protocol Design

```mermaid
sequenceDiagram
    participant User
    participant WebApp
    participant DataService
    participant STM32
    participant PeakDetector
    
    User->>WebApp: Start CV Measurement
    WebApp->>DataService: Configure Measurement
    DataService->>STM32: Send SCPI Commands
    
    Note over STM32: Setup CV Parameters
    STM32->>STM32: Configure DAC/ADC
    STM32->>DataService: Ready Response
    
    DataService->>STM32: Start Measurement
    
    loop CV Scan Cycle
        STM32->>STM32: Generate Voltage
        STM32->>STM32: Measure Current
        STM32->>DataService: Send Data Point
        DataService->>DataService: Buffer Data
        
        alt Real-time Analysis
            DataService->>PeakDetector: Process Chunk
            PeakDetector->>WebApp: Live Results
        end
    end
    
    STM32->>DataService: Measurement Complete
    DataService->>PeakDetector: Full Dataset Analysis
    PeakDetector->>PeakDetector: All Detection Methods
    PeakDetector->>WebApp: Final Results
    WebApp->>User: Display Analysis
```

## Data Message Format

```mermaid
graph LR
    subgraph "STM32 Message Structure"
        A[Header] --> B[Timestamp]
        B --> C[Voltage]
        C --> D[Current]
        D --> E[Status]
        E --> F[Checksum]
    end
    
    subgraph "Header Fields"
        A --> A1[Message Type]
        A --> A2[Sequence Number]
        A --> A3[Data Length]
    end
    
    subgraph "Status Fields"
        E --> E1[Measurement State]
        E --> E2[Error Flags]
        E --> E3[Temperature]
    end
```

## Communication Protocols

```mermaid
graph TD
    subgraph "Protocol Options"
        P1[USB Serial]
        P2[UART]
        P3[SPI]
        P4[I2C]
        P5[Ethernet]
        P6[WiFi]
    end
    
    subgraph "Data Formats"
        F1[Binary Protocol]
        F2[JSON Messages]
        F3[CSV Stream]
        F4[SCPI Commands]
    end
    
    subgraph "Transport Layer"
        T1[TCP/IP]
        T2[UDP]
        T3[MQTT]
        T4[WebSocket]
        T5[HTTP REST]
    end
    
    P1 --> F1
    P1 --> F4
    P2 --> F1
    P5 --> T1
    P5 --> T2
    P6 --> T3
    P6 --> T4
    P6 --> T5
    
    F1 --> T1
    F2 --> T3
    F2 --> T4
    F2 --> T5
    
    style P1 fill:#c8e6c9
    style F4 fill:#e1f5fe
    style T3 fill:#fff3e0
```

## Real-time Data Processing Flow

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Connecting : Connect STM32
    Connecting --> Connected : Success
    Connecting --> Error : Connection Failed
    
    Connected --> Configuring : Send Parameters
    Configuring --> Ready : Config Complete
    Configuring --> Error : Config Failed
    
    Ready --> Measuring : Start CV Scan
    Measuring --> DataReceiving : Receiving Data
    
    state DataReceiving {
        [*] --> BufferFilling
        BufferFilling --> ProcessingChunk : Buffer Full
        ProcessingChunk --> BufferFilling : Continue
        ProcessingChunk --> RealTimeAnalysis : Detect Peaks
        RealTimeAnalysis --> BufferFilling : Continue
    }
    
    DataReceiving --> Complete : Scan Finished
    DataReceiving --> Error : Communication Error
    
    Complete --> FinalAnalysis : Process Full Dataset
    FinalAnalysis --> Results : Analysis Complete
    Results --> Ready : Ready for Next
    
    Error --> Idle : Reset Connection
    
    note right of RealTimeAnalysis
        Real-time peak detection
        Live visualization
        Alert generation
    end note
```

## STM32 Integration Components

```mermaid
classDiagram
    class STM32Communicator {
        -port: str
        -baudrate: int
        -connection: Serial
        +connect() bool
        +disconnect() void
        +send_command(cmd: str) str
        +read_data() bytes
        +is_connected() bool
    }
    
    class SCPIHandler {
        -communicator: STM32Communicator
        +configure_cv(params: CVParams) bool
        +start_measurement() bool
        +stop_measurement() bool
        +get_status() dict
        +reset_device() bool
    }
    
    class DataStreamProcessor {
        -buffer: CircularBuffer
        -validator: DataValidator
        +process_raw_data(data: bytes) CVDataPoint
        +validate_data_point(point: CVDataPoint) bool
        +get_buffered_data() List~CVDataPoint~
        +clear_buffer() void
    }
    
    class RealTimePeakDetector {
        -chunk_size: int
        -detection_methods: List~PeakDetector~
        +process_chunk(data: List~CVDataPoint~) List~Peak~
        +update_live_results(peaks: List~Peak~) void
        +is_peak_detected() bool
    }
    
    class CVDataPoint {
        +timestamp: datetime
        +voltage: float
        +current: float
        +temperature: float
        +status: int
    }
    
    class CVMeasurementSession {
        -session_id: str
        -parameters: CVParams
        -data_points: List~CVDataPoint~
        -peaks: List~Peak~
        +start_session() void
        +add_data_point(point: CVDataPoint) void
        +end_session() void
        +export_data() dict
    }
    
    STM32Communicator --> SCPIHandler
    SCPIHandler --> DataStreamProcessor
    DataStreamProcessor --> RealTimePeakDetector
    DataStreamProcessor --> CVDataPoint
    RealTimePeakDetector --> CVMeasurementSession
    CVDataPoint --> CVMeasurementSession
```

## Configuration and Setup

```yaml
# config/stm32_integration.yaml
stm32:
  communication:
    protocol: "usb_serial"  # usb_serial, uart, ethernet
    port: "COM3"           # Windows: COMx, Linux: /dev/ttyUSBx
    baudrate: 115200
    timeout: 5
    
  scpi:
    command_timeout: 2
    response_buffer_size: 1024
    error_retry_count: 3
    
  data_acquisition:
    buffer_size: 10000
    chunk_size: 100
    sampling_rate: 1000  # Hz
    
measurement:
  cv_parameters:
    voltage_min: -1.0    # V
    voltage_max: 1.0     # V
    scan_rate: 0.1       # V/s
    cycles: 3
    
  real_time:
    enable_live_detection: true
    live_update_interval: 100  # ms
    peak_threshold: 1e-6   # A
    
peak_detection:
  methods:
    - "traditional"
    - "statistical"
    - "ml"
  
  real_time_method: "statistical"  # Fastest for real-time
  
storage:
  auto_save: true
  save_format: "hdf5"  # hdf5, csv, json
  compression: true
```

## Error Handling and Recovery

```mermaid
flowchart TD
    A[STM32 Communication Error] --> B{Error Type}
    
    B -->|Connection Lost| C[Reconnection Attempt]
    B -->|Data Corruption| D[Request Retransmission]
    B -->|Buffer Overflow| E[Clear Buffer & Resume]
    B -->|Device Error| F[Reset STM32]
    
    C --> G{Reconnect Success?}
    G -->|Yes| H[Resume Measurement]
    G -->|No| I[Alert User]
    
    D --> J{Retransmit Success?}
    J -->|Yes| H
    J -->|No| K[Skip Data Point]
    
    E --> L[Log Lost Data]
    L --> H
    
    F --> M{Reset Success?}
    M -->|Yes| N[Reconfigure Device]
    M -->|No| I
    
    N --> H
    K --> H
    H --> O[Continue Analysis]
    I --> P[Manual Intervention]
    
    style A fill:#ffcdd2
    style I fill:#ffcdd2
    style P fill:#ffcdd2
    style O fill:#c8e6c9
```

## Performance Optimization

```mermaid
graph TB
    subgraph "Data Throughput Optimization"
        A1[Binary Protocol]
        A2[Data Compression]
        A3[Batch Processing]
        A4[Circular Buffering]
    end
    
    subgraph "Real-time Processing"
        B1[Async Data Processing]
        B2[Multi-threading]
        B3[Memory Mapping]
        B4[Hardware Acceleration]
    end
    
    subgraph "Network Optimization"
        C1[TCP Keep-alive]
        C2[Connection Pooling]
        C3[Message Queuing]
        C4[Load Balancing]
    end
    
    A1 --> D[High Performance System]
    A2 --> D
    A3 --> D
    A4 --> D
    B1 --> D
    B2 --> D
    B3 --> D
    B4 --> D
    C1 --> D
    C2 --> D
    C3 --> D
    C4 --> D
```

## API Endpoints for STM32 Integration

```mermaid
graph LR
    subgraph "STM32 Control API"
        A1[POST /api/stm32/connect]
        A2[POST /api/stm32/disconnect]
        A3[GET /api/stm32/status]
        A4[POST /api/stm32/configure]
    end
    
    subgraph "Measurement API"
        B1[POST /api/measurement/start]
        B2[POST /api/measurement/stop]
        B3[GET /api/measurement/live]
        B4[GET /api/measurement/progress]
    end
    
    subgraph "Data API"
        C1[GET /api/data/stream]
        C2[GET /api/data/export]
        C3[POST /api/data/validate]
        C4[GET /api/data/statistics]
    end
    
    subgraph "Analysis API"
        D1[POST /api/analysis/real-time]
        D2[GET /api/analysis/results]
        D3[GET /api/analysis/peaks]
        D4[GET /api/analysis/compare]
    end
```

## Implementation Priority

### Phase 1: Basic Communication (Week 1)
- [ ] STM32 USB/Serial communication
- [ ] Basic SCPI command handling
- [ ] Data point structure definition
- [ ] Simple data validation

### Phase 2: Data Streaming (Week 2)
- [ ] Real-time data streaming
- [ ] Circular buffer implementation
- [ ] Error handling and recovery
- [ ] Basic live visualization

### Phase 3: Integration (Week 3)
- [ ] Connect to existing CV analysis system
- [ ] Real-time peak detection
- [ ] Live dashboard updates
- [ ] Data persistence

### Phase 4: Optimization (Week 4)
- [ ] Performance optimization
- [ ] Advanced error handling
- [ ] Multi-session support
- [ ] Export functionality

---
*STM32 Integration Plan*  
*Version: 1.0*  
*Created: August 15, 2025*
