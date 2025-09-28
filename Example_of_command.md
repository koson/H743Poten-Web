# H743 Potentiostat SCPI Commands Guide

## Current Range Setting (Required for all techniques)
```
POTEn:CURRent:RANGe <range>
```
- **Range values**: 0=1kΩ, 1=10kΩ, 2=100kΩ, 3=1MΩ
- **Example**: `POTEn:CURRent:RANGe 2` (100kΩ range, ±10µA)

---

## Cyclic Voltammetry (CV)

### Command Pattern:
```
POTEn:CV:Start:ALL <LowerVoltage>,<UpperVoltage>,<BeginVoltage>,<SweepRate>,<NumCycles>
```

### Parameters:
- **LowerVoltage**: Lower potential limit (V)
- **UpperVoltage**: Upper potential limit (V) 
- **BeginVoltage**: Starting potential (V)
- **SweepRate**: Scan rate (V/s)
- **NumCycles**: Number of cycles

### Example:
```
POTEn:CURRent:RANGe 2
POTEn:CV:Start:ALL -1.0,1.0,-1.0,0.05,3
```
*Scan from -1V to +1V, starting at -1V, 50 mV/s, 3 cycles*

### Stop Command:
```
POTEn:CV:Stop
```

---

## Differential Pulse Voltammetry (DPV)

### Command Pattern:
```
POTEn:DPV:Start:ALL <InitialPotential>,<FinalPotential>,<PulseHeight>,<PulseIncrement>,<PulseWidth>,<PulsePeriod>
```

### Parameters:
- **InitialPotential**: Starting potential (V)
- **FinalPotential**: Ending potential (V)
- **PulseHeight**: Pulse amplitude (V)
- **PulseIncrement**: Step size between pulses (V)
- **PulseWidth**: Pulse duration (s)
- **PulsePeriod**: Time between pulses (s)

### Example:
```
POTEn:CURRent:RANGe 2
POTEn:DPV:Start:ALL -0.5,0.5,0.05,0.01,0.05,0.1
```
*Scan -0.5V to +0.5V, 50mV pulses, 10mV steps, 50ms pulse width, 100ms period*

### Stop Command:
```
POTEn:DPV:Stop
```

---

## Square Wave Voltammetry (SWV)

### Command Pattern:
```
POTEn:SWV:Start:ALL <InitialPot>,<FinalPot>,<StepPot>,<Amplitude>,<Freq>,<PreconEn>,<PreconPot1>,<PreconPot2>,<PreconTime>,<EquilTime>
```

### Parameters:
- **InitialPot**: Starting potential (V)
- **FinalPot**: Ending potential (V)
- **StepPot**: Step size (V)
- **Amplitude**: Square wave amplitude (V)
- **Freq**: Frequency (Hz)
- **PreconEn**: Enable preconcentration (0=disable, 1=enable)
- **PreconPot1**: Preconcentration potential (V)
- **PreconPot2**: Second precon potential (V) - not used
- **PreconTime**: Preconcentration time (s)
- **EquilTime**: Equilibration time (s)

### Example (without preconcentration):
```
POTEn:CURRent:RANGe 2
POTEn:SWV:Start:ALL -0.5,0.5,0.005,0.05,5,0,0,0,0,0
```
*Scan -0.5V to +0.5V, 5mV steps, 50mV amplitude, 5Hz, no preconcentration*

### Example (with preconcentration):
```
POTEn:CURRent:RANGe 2
POTEn:SWV:Start:ALL -0.5,0.5,0.005,0.05,5,1,-1.9,-0.5,240,10
```
*Same scan with 240s preconcentration at -1.9V, 10s equilibration*

### Stop Command:
```
POTEn:SWV:Stop
```

---

## Common Notes:

1. **Always set current range first** before starting any technique
2. **Voltage range**: ±2.5V (limited by VREF = 2.5V)
3. **Current ranges**:
   - Range 0: ±100µA (1kΩ TIA)
   - Range 1: ±10µA (10kΩ TIA)  
   - Range 2: ±1µA (100kΩ TIA)
   - Range 3: ±100nA (1MΩ TIA)

4. **Data output**: Results are printed to serial console in CSV format
5. **StatusLED**: Currently disabled to prevent GPIO conflicts

---

## Troubleshooting:

- **DAC1 voltage issues**: Fixed by disabling StatusLED (GPIO conflict with ADC)
- **ADC clock conflicts**: SWV uses DIV2 prescaler (same as DPV) for stability
- **Virtual ground**: Should be ~1.25V when DAC is working properly