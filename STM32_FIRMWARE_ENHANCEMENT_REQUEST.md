# STM32 H743 Potentiostat Firmware Enhancement Request

## 📋 Issue Summary
Request firmware modifications to improve SCPI communication and add data streaming capabilities for CV measurements.

## 🚨 Priority Issues

### 1. **Debug Message Cleanup** (High Priority)
**Problem**: STM32 firmware currently sends excessive debug messages mixed with SCPI responses:
```
🔤 SCPI: Processing char '*' (0x2A)
🔤 SCPI: Processing char 'I' (0x49)
📥 CDC: Received 7 bytes: *IDN?
🔍 SCPI_Parse: Parsing 6 bytes: "*IDN?"
MANUFACTURE,INSTR2013,0,01-02  ← Real response buried in debug
```

**Request**: 
- Add compile-time flag to disable debug messages for production
- Or redirect debug messages to separate debug UART/interface
- Keep only clean SCPI responses on main USB CDC interface

### 2. **CV Data Streaming** (High Priority)
**Current Behavior**: CV data must be requested point-by-point
**Request**: Add streaming command for complete CV measurement

**Proposed SCPI Commands**:
```
POTEn:CV:Stream:START    - Start CV measurement with continuous data streaming
POTEn:CV:Stream:STOP     - Stop streaming
POTEn:CV:Stream:DATA?    - Get all accumulated data at once
```

**Expected Data Format**:
```
voltage,current
-0.500,-0.000123
-0.490,-0.000121
...
0.500,0.000089
```

## 🎯 Detailed Requirements

### Debug Message Control
```c
// Proposed implementation
#ifdef PRODUCTION_BUILD
    #define DEBUG_PRINT(...)
#else 
    #define DEBUG_PRINT(...) printf(__VA_ARGS__)
#endif
```

### Data Streaming Protocol
1. **Start Streaming**: `POTEn:CV:Stream:START`
   - Begin CV measurement
   - Store all data points in internal buffer
   - Send "OK" response immediately
   - Continue measurement in background

2. **Status Check**: `POTEn:CV:Stream:STATUS?`
   - Return: "MEASURING", "COMPLETE", or "ERROR"
   - Include progress percentage if possible

3. **Data Retrieval**: `POTEn:CV:Stream:DATA?`
   - Return complete CSV data
   - Format: Header + data points
   - Clear buffer after sending

4. **Stop Streaming**: `POTEn:CV:Stream:STOP`
   - Abort current measurement
   - Clear buffer
   - Return to IDLE state

## 💻 Integration Architecture

```
┌─────────────────┐    Clean SCPI    ┌──────────────────┐    REST API    ┌─────────────┐
│   STM32 H743    │ ◄─────────────► │  SCPI Server     │ ◄──────────── │ Web Frontend│
│   (No Debug)    │                 │  (Data Buffer)   │               │ (Consumer)  │
└─────────────────┘                 └──────────────────┘               └─────────────┘
```

## 🔧 Expected Benefits

1. **Clean Communication**: No debug message filtering needed
2. **Complete Data Capture**: Full CV curves without data loss
3. **Better Performance**: Streaming reduces communication overhead
4. **File Export Ready**: Data format suitable for CSV/PNG generation
5. **Database Integration**: Structured data for measurement storage

## 📊 Current vs Proposed Workflow

### Current (Problematic):
```
Web → SCPI Server → STM32: "POTEn:CV:Start:ALL"
Web → SCPI Server → STM32: "POTEn:CV:DATA?" (repeat every 1.5s)
STM32 → SCPI Server: "🔤 DEBUG MESSAGES + real data"
SCPI Server → Web: Filtered response (may lose data)
```

### Proposed (Clean):
```
Web → SCPI Server → STM32: "POTEn:CV:Stream:START" 
STM32 → SCPI Server: "OK" (immediate response)
[STM32 performs full CV measurement internally]
Web → SCPI Server → STM32: "POTEn:CV:Stream:DATA?"
STM32 → SCPI Server: Clean CSV data (complete measurement)
SCPI Server → Web: Complete data + file export
```

## 🎯 Implementation Priority

1. **Phase 1**: Debug message cleanup (enables immediate testing)
2. **Phase 2**: Basic streaming commands (POTEn:CV:Stream:*)
3. **Phase 3**: Enhanced status reporting and error handling

## 🧪 Testing Requirements

- [ ] Clean SCPI responses without debug messages
- [ ] Complete CV measurement streaming (500+ data points)
- [ ] Proper error handling and status reporting
- [ ] Memory management for data buffering
- [ ] Performance testing (multiple CV cycles)

## 📞 Contact
- **Web Team**: Working on SCPI Server and Web Frontend
- **Integration**: Ready to test as soon as firmware updates available
- **Timeline**: Flexible, but cleanup of debug messages would help immediately

---
**Note**: This issue supports the development of a tiered architecture where STM32 handles measurements, SCPI Server manages data/files, and Web Frontend provides user interface.