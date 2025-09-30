# SWV with Preconcentration - User Guide
# H743 Potentiostat Complete System

## 🧪 Introduction

Square Wave Voltammetry (SWV) with Preconcentration is a powerful electrochemical technique that combines:
- **Preconcentration**: Accumulate analytes at electrode surface for enhanced sensitivity
- **SWV Measurement**: High-sensitivity voltammetric detection

## ⚙️ Parameter Configuration

### Basic SWV Parameters
- **Start Voltage**: Initial potential (typically -0.5 to -1.0 V)
- **End Voltage**: Final potential (typically +0.5 to +1.0 V)
- **Step Voltage**: Potential increment per step (1-10 mV)
- **SW Amplitude**: Square wave amplitude (10-100 mV)
- **SW Frequency**: Square wave frequency (1-50 Hz)

### Preconcentration Parameters
- **Enable Preconcentration**: Check to activate preconcentration
- **Precon Pot1**: First preconcentration potential (typically -1.9 V)
- **Precon Pot2**: Second preconcentration potential (typically -0.5 V)
- **Precon Time**: Preconcentration duration (30-600 seconds)
- **Equilibration Time**: Rest time before measurement (5-30 seconds)

## 🎛️ Preset Configurations

### Quick Preset (60s + 10s)
- Best for: Quick analysis, high concentration samples
- Total time: ~70 seconds
- Sensitivity: Standard

### Medium Preset (120s + 15s)
- Best for: General purpose analysis
- Total time: ~135 seconds
- Sensitivity: Enhanced

### Long Preset (240s + 20s)
- Best for: Low concentration samples
- Total time: ~260 seconds
- Sensitivity: High

### Extended Preset (600s + 30s)
- Best for: Trace analysis, very low concentrations
- Total time: ~630 seconds (10.5 minutes)
- Sensitivity: Maximum

## ⏱️ Time Management

### Progress Indicators
The system provides real-time progress feedback:
- **Progress Bar**: Shows preconcentration completion percentage
- **Time Display**: Current/total time and remaining time
- **Status Updates**: Step-by-step process information

### Time Warnings
- **Orange Warning**: Appears for processes > 2 minutes
- **Time Calculation**: Automatically updates based on your settings
- **Process Cancellation**: Can stop long processes if needed

## 📊 Expected Results

### Preconcentration Phase
1. **PRECONCENTRATION_START**: Process begins
2. **PRECON_PROGRESS**: Regular updates every 10 seconds
3. **PRECON_FINISHED**: Preconcentration completed
4. **Equilibration**: Brief rest period

### SWV Measurement Phase
1. **Data Collection**: SWV voltammogram data points
2. **Real-time Plotting**: Live current vs. potential plot
3. **Completion**: Final results and statistics

## 🔧 Troubleshooting

### Long Wait Times
- **Expected**: Preconcentration times are intentionally long
- **Progress**: Monitor progress bar for real-time updates
- **Cancellation**: Use Stop button if needed

### No Preconcentration Data
- **Check Connection**: Ensure STM32 is properly connected
- **Parameter Range**: Verify preconcentration potentials are valid
- **Time Settings**: Ensure preconcentration time > 0

### Poor Sensitivity
- **Increase Precon Time**: Try longer preconcentration
- **Adjust Potentials**: Optimize preconcentration potential range
- **Check Electrode**: Verify working electrode condition

## 💡 Best Practices

### Parameter Selection
1. **Start Conservative**: Use Medium preset (120s) initially
2. **Optimize Gradually**: Increase preconcentration time if needed
3. **Monitor Results**: Check signal-to-noise ratio improvement

### Time Management
1. **Plan Ahead**: Long preconcentrations require patience
2. **Multi-tasking**: Use progress indicators to manage time
3. **Document Settings**: Record successful parameter combinations

### Data Quality
1. **Baseline Check**: Run without preconcentration first
2. **Reproducibility**: Repeat measurements with same parameters
3. **Control Experiments**: Use blank solutions for comparison

## 📈 Sensitivity Enhancement

Preconcentration typically provides:
- **5-50x**: Signal enhancement for metal ions
- **10-100x**: Enhancement for organic compounds
- **Detection Limits**: Often improved by 1-2 orders of magnitude

## ⚠️ Safety Notes

- **Electrode Potentials**: Keep within ±2.5V range
- **Long Processes**: Ensure stable connection during extended runs
- **Ventilation**: Ensure adequate ventilation for sample preparation

---

**System Status**: Complete implementation with real-time progress monitoring
**Last Updated**: September 30, 2025
**Version**: v1.0 - Full SWV + Preconcentration Support
