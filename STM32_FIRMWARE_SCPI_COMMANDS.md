# 🧪 **STM32 H743 Potentiostat SCPI Commands Reference**
## 📋 **Electrochemical Measurement Methods Documentation**

---

## 🎯 **Overview**
This document provides complete SCPI command reference for the STM32 H743 Potentiostat firmware, supporting three primary electrochemical measurement techniques: **Cyclic Voltammetry (CV)**, **Differential Pulse Voltammetry (DPV)**, and **Square Wave Voltammetry (SWV)**.

---

## ⚙️ **Essential Setup Commands**

### 🔧 **Current Range Configuration (Required)**
```scpi
POTEn:CURRent:RANGe <range>
```

**Current Range Values:**
- `0` = ±100µA (high current measurements)
- `1` = ±10µA (medium current measurements)  
- `2` = ±1µA (low current measurements)
- `3` = ±100nA (ultra-low current measurements)

**Example:**
```scpi
POTEn:CURRent:RANGe 2    # Set to ±1µA range
```

---

## 🔄 **1. CYCLIC VOLTAMMETRY (CV)**

### 🎯 **Method Description**
Cyclic Voltammetry sweeps the applied potential linearly between two limits while measuring the resulting current. It provides information about redox processes, reaction kinetics, and electrode surface properties.

### 📡 **SCPI Command Format**
```scpi
POTEn:CV:Start:ALL <InitialPotential>,<VertexPotential>,<FinalPotential>,<ScanRate>,<NumberOfScans>
```

### 📋 **Parameters**
| Parameter | Description | Unit | Example |
|-----------|-------------|------|---------|
| **InitialPotential** | Starting potential | V | -0.5 |
| **VertexPotential** | Turning point potential | V | 0.5 |
| **FinalPotential** | Ending potential | V | -0.5 |
| **ScanRate** | Voltage sweep rate | V/s | 0.1 |
| **NumberOfScans** | Number of cycles | - | 1 |

### 💻 **Usage Examples**

#### **Standard CV Scan:**
```scpi
POTEn:CURRent:RANGe 2
POTEn:CV:Start:ALL -0.5,0.5,-0.5,0.1,1
```
*Single cycle from -0.5V to +0.5V and back, at 0.1 V/s*

#### **Multi-Cycle CV:**
```scpi
POTEn:CURRent:RANGe 1
POTEn:CV:Start:ALL -0.8,0.8,-0.8,0.05,3
```
*Three cycles, wider potential window, slower scan rate*

#### **High-Speed CV:**
```scpi
POTEn:CURRent:RANGe 0
POTEn:CV:Start:ALL -0.3,0.3,-0.3,1.0,1
```
*Fast scan for kinetic studies*

### 🛑 **Control Commands**
```scpi
POTEn:CV:Stop        # Stop CV measurement
POTEn:CV:DATA?       # Retrieve measurement data
POTEn:CV:STATUS?     # Check measurement status
```

---

## 📊 **2. DIFFERENTIAL PULSE VOLTAMMETRY (DPV)**

### 🎯 **Method Description**
Differential Pulse Voltammetry applies voltage pulses of increasing amplitude on a staircase waveform. It measures the current difference before and after each pulse, providing enhanced sensitivity and resolution for trace analysis.

### 📡 **SCPI Command Format**
```scpi
POTEn:DPV:Start:ALL <InitialPotential>,<FinalPotential>,<PulseHeight>,<PulseIncrement>,<PulseWidth>,<PulsePeriod>
```

### 📋 **Parameters**
| Parameter | Description | Unit | Example |
|-----------|-------------|------|---------|
| **InitialPotential** | Starting potential | V | -0.5 |
| **FinalPotential** | Ending potential | V | 0.5 |
| **PulseHeight** | Pulse amplitude | V | 0.05 |
| **PulseIncrement** | Step size between pulses | V | 0.01 |
| **PulseWidth** | Pulse duration | s | 0.05 |
| **PulsePeriod** | Time between pulses | s | 0.1 |

### ⚡ **Pulse Timing Diagram**
```
Voltage Profile:
    |     ___
    |    |   |     ___
    |___|   |____|   |____
    t1  t2  t3  t4  t5  t6

t1-t2: Baseline potential
t2-t3: Pulse applied
t3-t4: Current sampled
t4-t5: Return to baseline  
t5-t6: Wait for next pulse
```

### 💻 **Usage Examples**

#### **Standard DPV Analysis:**
```scpi
POTEn:CURRent:RANGe 2
POTEn:DPV:Start:ALL -0.5,0.5,0.05,0.01,0.05,0.1
```
*Standard parameters: 50mV pulses, 10mV steps, 50ms pulse width*

#### **High-Resolution DPV:**
```scpi
POTEn:CURRent:RANGe 1
POTEn:DPV:Start:ALL -0.8,0.8,0.025,0.002,0.05,0.15
```
*Fine resolution: smaller pulses and steps for detailed analysis*

#### **Fast DPV Screening:**
```scpi
POTEn:CURRent:RANGe 0
POTEn:DPV:Start:ALL -0.3,0.3,0.01,0.05,0.03,0.1
```
*Quick scan with larger steps for rapid screening*

### 🛑 **Control Commands**
```scpi
POTEn:DPV:Stop       # Stop DPV measurement
POTEn:DPV:DATA?      # Retrieve measurement data
POTEn:DPV:STATUS?    # Check measurement status
POTEn:DPV:ABORt      # Abort measurement immediately
```

---

## ⚡ **3. SQUARE WAVE VOLTAMMETRY (SWV)**

### 🎯 **Method Description**
Square Wave Voltammetry superimposes a square wave on a staircase potential ramp. It measures both forward and reverse currents, calculating the difference for enhanced peak resolution and faster analysis.

### 📡 **SCPI Command Format**
```scpi
POTEn:SWV:Start:ALL <InitialPotential>,<FinalPotential>,<StepHeight>,<SquareWaveAmplitude>,<SquareWaveFrequency>
```

### 📋 **Parameters**
| Parameter | Description | Unit | Example |
|-----------|-------------|------|---------|
| **InitialPotential** | Starting potential | V | -0.5 |
| **FinalPotential** | Ending potential | V | 0.5 |
| **StepHeight** | Staircase step size | V | 0.005 |
| **SquareWaveAmplitude** | Square wave amplitude | V | 0.025 |
| **SquareWaveFrequency** | Square wave frequency | Hz | 50 |

### 📈 **Square Wave Pattern**
```
Voltage Profile:
       ___     ___     ___
      |   |   |   |   |   |
  ____|   |___|   |___|   |____
     Step 1   Step 2   Step 3

Current Sampling:
  Forward:  ↑ (positive pulse)
  Reverse:  ↓ (negative pulse)  
  Net = Forward - Reverse
```

### 💻 **Usage Examples**

#### **Standard SWV Analysis:**
```scpi
POTEn:CURRent:RANGe 1
POTEn:SWV:Start:ALL -0.5,0.5,0.005,0.025,50
```
*Standard parameters: 5mV steps, 25mV amplitude, 50Hz frequency*

#### **High-Frequency SWV:**
```scpi
POTEn:CURRent:RANGe 0
POTEn:SWV:Start:ALL -0.3,0.3,0.01,0.05,100
```
*Fast analysis: higher frequency and amplitude*

#### **High-Resolution SWV:**
```scpi
POTEn:CURRent:RANGe 2
POTEn:SWV:Start:ALL -0.8,0.8,0.002,0.015,25
```
*Fine resolution: smaller steps and lower frequency*

### 🛑 **Control Commands**
```scpi
POTEn:SWV:Stop       # Stop SWV measurement
POTEn:SWV:DATA?      # Retrieve measurement data
POTEn:SWV:STATUS?    # Check measurement status
POTEn:SWV:ABORt      # Abort measurement immediately
```

---

## 📊 **Data Retrieval and Status**

### 📡 **Universal Commands**
```scpi
*IDN?                # Device identification
*RST                 # Reset device
SYST:ERR?           # Check system errors
```

### 📈 **Data Format**
All measurements return data in the format:
```
<Method>,<Point>,<Time>,<Potential>,<Current_i1>[,<Current_i2>][,<DifferentialCurrent>]
```

**Example DPV Data:**
```
DPV,1,0.000,-0.500,1.23e-6,1.28e-6,0.05e-6
DPV,2,0.120,-0.490,1.25e-6,1.30e-6,0.05e-6
```

---

## ⚠️ **Important Notes**

### 🔧 **Setup Requirements**
1. **Always set current range first** before starting any measurement
2. **Verify STM32 connection** using `*IDN?` command
3. **Check for errors** using `SYST:ERR?` after each command

### 📋 **Parameter Guidelines**
- **Current Range**: Choose based on expected current levels
- **Scan Rates**: CV: 0.001-10 V/s, DPV: depends on pulse timing
- **Pulse Parameters**: DPV pulse width should be < pulse period
- **Frequency Limits**: SWV frequency limited by hardware (typically 1-1000 Hz)

### 🛠️ **Troubleshooting**
- **Current Overload**: Reduce current range or pulse amplitude
- **No Response**: Check serial connection and baud rate (115200)
- **Invalid Parameters**: Verify parameter ranges and format
- **Measurement Timeout**: Increase timeout for slow scans

---

## 📞 **Technical Support**

**Firmware Version**: Compatible with STM32 H743 Potentiostat v1.0+  
**Communication**: Serial UART, 115200 baud, 8N1  
**Command Termination**: Line feed (`\n`) or carriage return (`\r`)  

---

## 🎯 **Quick Reference Card**

| Method | Command Template | Typical Use |
|--------|------------------|-------------|
| **CV** | `POTEn:CV:Start:ALL -0.5,0.5,-0.5,0.1,1` | Redox characterization |
| **DPV** | `POTEn:DPV:Start:ALL -0.5,0.5,0.05,0.01,0.05,0.1` | Trace analysis |
| **SWV** | `POTEn:SWV:Start:ALL -0.5,0.5,0.005,0.025,50` | Fast screening |

**🎉 Ready for electrochemical analysis with STM32 H743 Potentiostat!** 🔬