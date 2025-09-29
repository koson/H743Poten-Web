# STM32_SCPI_DATA_COMMANDS_MISSING.md

## 🚨 ✅ PARTIALLY FIXED: SCPI DATA Commands Implementation Issue

**Date**: September 29, 2025  
**Status**: 🟡 PARTIALLY FIXED - Commands respond but wrong data format  
**Severity**: MEDIUM - Web interface gets responses but incorrect data  
**Component**: STM32 H743 Firmware SCPI Implementation

---

## 📋 Problem Summary (UPDATED)

✅ **FIXED**: SCPI commands now respond (no longer empty)  
❌ **REMAINING**: Commands return debug/config messages instead of measurement data

## 🧪 Test Results (UPDATED - September 29, 2025)

### ✅ Working Commands:
```
*IDN? → "MANUFACTURE,INSTR2013,0,01-02"
POTEn:CV:Start:ALL -0.5,0.5,0.1,1 → "OK" 
POTEn:CURRent:RANGe 2 → "OK"
POTEn:CV:STATUS? → "IDLE" (before), config messages (after)
POTEn:CV:DATA? → Config messages (46+ chars)
POTEn:DPV:STATUS? → Config messages  
POTEn:DPV:DATA? → Config messages
```

### ❌ Wrong Data Format (Commands respond but incorrect content):
```
POTEn:CV:STATUS? → "ElectrochemConfig: CV configuration restored" 
                   (should be "MEASURING", "IDLE", "COMPLETE")

POTEn:CV:DATA? → "ElectrochemConfig: Current configuration saved"
                 (should be "voltage,current\n-0.5,1.23e-6\n...")
                 
POTEn:DPV:STATUS? → Debug messages instead of measurement status
POTEn:DPV:DATA? → Debug messages instead of voltage,current data
```

## 📊 Current CV Measurement Behavior

1. **START Command**: `POTEn:CV:Start:ALL -0.5,0.5,0.1,1` → ✅ Returns "OK"
2. **Initial Response**: STM32 sends configuration messages:
   ```
   ElectrochemConfig: Current configuration saved
   ElectrochemConfig: CV configuration restored
   ElectrochemConfig: Switched from NONE to CV
   PotenCVScan: Configuration validation passed
   PotenCVScan: Configuration synced to running parameters
   PotenCVScan: Successfully switched to CV with isolated configuration
   ```
3. **Data Streaming**: ❌ **No measurement data sent**
4. **STATUS Query**: `POTEn:CV:STATUS?` → ❌ **Empty response**
5. **DATA Query**: `POTEn:CV:DATA?` → ❌ **Empty response**

## 🎯 Expected Behavior

### CV Measurement Flow:
```
1. POTEn:CV:Start:ALL -0.5,0.5,0.1,1 → "OK"
2. POTEn:CV:STATUS? → "RUNNING" or "MEASURING" 
3. POTEn:CV:DATA? → "voltage,current\n-0.5,1.23e-6\n-0.4,2.45e-6\n..."
4. [Repeat STATUS/DATA until complete]
5. POTEn:CV:STATUS? → "IDLE" or "COMPLETE"
```

### DPV Measurement Flow:
```
1. POTEn:DPV:Start:ALL -0.5,0.5,0.05,0.01,0.05,0.1 → "OK"
2. POTEn:DPV:STATUS? → "RUNNING" or "MEASURING"
3. POTEn:DPV:DATA? → "voltage,current\n-0.5,1.23e-6\n-0.45,2.45e-6\n..."
4. [Repeat STATUS/DATA until complete]
5. POTEn:DPV:STATUS? → "IDLE" or "COMPLETE"
```

## 🛠️ Required STM32 Firmware Changes

### 1. Implement CV:STATUS? Command
```c
// In SCPI command parser
if (strcmp(command, "POTEn:CV:STATUS?") == 0) {
    if (cv_measurement_active) {
        send_response("MEASURING");
    } else if (cv_measurement_complete) {
        send_response("COMPLETE");
    } else {
        send_response("IDLE");
    }
    return;
}
```

### 2. Implement CV:DATA? Command
```c
// In SCPI command parser  
if (strcmp(command, "POTEn:CV:DATA?") == 0) {
    if (cv_data_available) {
        // Send accumulated CV data points
        send_cv_data_buffer();
    } else {
        send_response(""); // No data available
    }
    return;
}
```

### 3. Implement DPV:STATUS? Command
```c
if (strcmp(command, "POTEn:DPV:STATUS?") == 0) {
    if (dpv_measurement_active) {
        send_response("MEASURING");
    } else if (dpv_measurement_complete) {
        send_response("COMPLETE");
    } else {
        send_response("IDLE");
    }
    return;
}
```

### 4. Implement DPV:DATA? Command
```c
if (strcmp(command, "POTEn:DPV:DATA?") == 0) {
    if (dpv_data_available) {
        send_dpv_data_buffer();
    } else {
        send_response("");
    }
    return;
}
```

## 📈 Data Format Specification

### CV Data Format:
```
voltage,current
-0.500,1.234e-06
-0.400,2.456e-06
-0.300,3.789e-06
...
```

### DPV Data Format:
```
voltage,current
-0.500,1.234e-06
-0.450,2.456e-06
-0.400,3.789e-06
...
```

## 🔄 Alternative Approaches

### Option 1: Query-Based (Recommended)
- Web calls STATUS? to check progress
- Web calls DATA? to get accumulated data
- **Standard SCPI pattern**

### Option 2: Streaming-Based (Current - Broken)
- STM32 continuously streams data after START
- **Problem**: No data is being streamed after config messages

### Option 3: Hybrid
- STM32 streams data during measurement
- DATA? command returns accumulated buffer
- **Best of both worlds**

## 🚨 Impact

**Without these commands**:
- ❌ Web interface shows "0 data points available"
- ❌ CV measurements appear to fail
- ❌ DPV measurements cannot retrieve data
- ❌ Users cannot see measurement results

**With these commands**:
- ✅ Web interface can retrieve data
- ✅ Measurements work end-to-end
- ✅ Standard SCPI compliance
- ✅ Better debugging capabilities

## 🏃‍♂️ Next Steps

1. **Implement CV:STATUS?** command in STM32 firmware
2. **Implement CV:DATA?** command in STM32 firmware  
3. **Implement DPV:STATUS?** command in STM32 firmware
4. **Implement DPV:DATA?** command in STM32 firmware
5. **Test** with web interface
6. **Verify** data format compatibility

## 📝 Test Commands

After firmware update, test these commands:
```bash
# Connect to STM32
python -c "
from hardware.scpi_handler import SCPIHandler
scpi = SCPIHandler('/dev/ttyACM0', 115200)
scpi.connect()

# Test CV flow
print(scpi.send_custom_command('POTEn:CV:Start:ALL -0.5,0.5,0.1,1'))
time.sleep(2)
print(scpi.send_custom_command('POTEn:CV:STATUS?'))  # Should return MEASURING or COMPLETE
print(scpi.send_custom_command('POTEn:CV:DATA?'))    # Should return voltage,current data

# Test DPV flow  
print(scpi.send_custom_command('POTEn:DPV:Start:ALL -0.5,0.5,0.05,0.01,0.05,0.1'))
time.sleep(2)
print(scpi.send_custom_command('POTEn:DPV:STATUS?')) # Should return MEASURING or COMPLETE
print(scpi.send_custom_command('POTEn:DPV:DATA?'))   # Should return voltage,current data
"
```

---

**Priority**: HIGH - Required for web interface functionality  
**Assignee**: STM32 Firmware Team  
**Due Date**: ASAP for web interface testing