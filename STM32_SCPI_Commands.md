# STM32 SCPI Commands for CV Measurement

## Required SCPI Commands for STM32 Firmware

### 1. Start CV Measurement
**Command:** `POTEn:CV:Start:ALL <begin>,<upper>,<lower>,<rate>,<cycles>`

**Parameters:**
- `begin`: Starting potential (V) - จุดเริ่มต้นแรงดัน
- `upper`: Upper potential limit (V) - จุดสูงสุดแรงดัน  
- `lower`: Lower potential limit (V) - จุดต่ำสุดแรงดัน
- `rate`: Scan rate (V/s) - ความเร็วในการสแกน
- `cycles`: Number of cycles - จำนวนรอบ

**Example:**
```
POTEn:CV:Start:ALL 0.0,1.0,-1.0,0.1,1
```

**Response:** `OK` or error message

---

### 2. Query CV Data 
**Command:** `POTEn:CV:DATA?`

**Response Format:**
- Normal data: `<potential>,<current>,<cycle>,<direction>`
- No data available: `NO_DATA`
- Measurement complete: `<potential>,<current>,<cycle>,<direction>,COMPLETE`

**Examples:**
```
0.123,-0.000456,1,forward
-0.567,0.000234,2,reverse
NO_DATA
0.000,-0.000123,3,forward,COMPLETE
```

**Data Fields:**
- `potential`: Current applied potential (V)
- `current`: Measured current (A)
- `cycle`: Current cycle number (1-based)
- `direction`: Scan direction ("forward" or "reverse")
- `COMPLETE`: Optional status indicating measurement completion

---

### 3. Stop CV Measurement
**Command:** `POTEn:CV:STOP`

**Response:** `OK` or error message

---

## Implementation Notes

### CV Scan Cycle
Each CV cycle follows this pattern:
1. **Forward scan:** Begin → Upper → Lower
2. **Reverse scan:** Lower → Begin

### Data Streaming
- Web application queries `POTEn:CV:DATA?` every 50ms (20 Hz)
- STM32 should buffer data points and return the latest available data
- Return `NO_DATA` when no new data is available
- Return `COMPLETE` status when all cycles are finished

### Error Handling
- Invalid commands should return descriptive error messages
- Connection loss should be detected by web application
- Web application will fall back to simulation mode on communication errors

### Performance Requirements
- Data acquisition rate: Up to 20 Hz
- Response time: < 10ms for data queries
- Buffer depth: At least 100 data points

## Testing Commands

You can test these commands manually using a serial terminal:

```bash
# Start a simple CV measurement
POTEn:CV:Start:ALL 0.0,0.5,-0.5,0.1,1

# Query data (repeat multiple times)
POTEn:CV:DATA?

# Stop measurement
POTEn:CV:STOP
```

## Integration Status

✅ **Web Application:** Ready and implemented  
⏳ **STM32 Firmware:** Requires implementation of above commands
