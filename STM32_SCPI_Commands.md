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

### 2. CV Data Streaming (Automatic)
**After Start Command:** STM32 automatically sends CV data without polling

**Data Format:**
- Continuous stream: `CV, <timestamp>, <potential>, <current>, <cycle>, <direction>, <extra_fields>`
- Completion signal: `CV_COMPLETE` or line containing `COMPLETE`
- Error responses: `**ERROR: -113, "Undefined header"` or `**ERROR: -350, "Queue overflow"`

**Examples:**
```
CV, 244, 0.0001, -1.0842e-09, 3, 1, 2050, 2051, 4, 2050
CV, 345, 0.1234, -2.3456e-09, 3, 1, 2051, 2052, 5, 2051
CV_COMPLETE
```

**Data Fields:**
- `CV`: Command identifier
- `timestamp`: STM32 timestamp in milliseconds
- `potential`: Current applied potential (V)
- `current`: Measured current (A)
- `cycle`: Current cycle number (1-based)
- `direction`: Direction code (1=forward, 0=reverse)
- `extra_fields`: Additional STM32-specific data (ignored by web app)

**No Polling Required:** Web application listens passively for incoming data

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

### Data Streaming Protocol
- **Start:** Send `POTEn:CV:Start:ALL` command once
- **Stream:** STM32 automatically sends data as it's collected
- **Listen:** Web application reads buffered serial data continuously
- **Complete:** STM32 sends completion signal when finished
- **No Polling:** Do NOT send `POTEn:CV:DATA?` queries

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
