# STM32 vs Palmsens CV Analysis Summary
## Generated: 2025-08-26 20:50:48

### Overview
This analysis compares cyclic voltammetry (CV) calibration performance between STM32 and Palmsens potentiostat systems. Both systems were analyzed using identical data processing methods with all units in µA.

### Data Summary

#### STM32 System
- **Files processed**: 50 files
- **Concentrations**: 0.5, 1.0, 10.0, 20.0 mM
- **Scan rates**: 20.0, 50.0, 100.0, 200.0, 400.0 mV/s
- **Peak height range**: 0.9 to 1331.4 µA

#### Palmsens System
- **Files processed**: 90 files
- **Concentrations**: 0.5, 1.0, 5.0, 10.0, 20.0, 50.0 mM (wider range)
- **Scan rates**: 20.0, 50.0, 100.0, 200.0, 400.0 mV/s
- **Peak height range**: 19.6 to 1723.8 µA

### Calibration Results by Scan Rate

| Scan Rate | STM32 R² | Palmsens R² | STM32 Slope | Palmsens Slope | Slope Ratio (P/S) |
|-----------|----------|-------------|-------------|----------------|-------------------|
| 20 mV/s   | 0.014    | 0.866       | 7.23        | 16.59         | 2.29             |
| 50 mV/s   | 0.983    | 0.908       | 36.67       | 31.25         | 0.85             |
| 100 mV/s  | 0.963    | 0.876       | 41.69       | 33.16         | 0.80             |
| 200 mV/s  | 0.879    | 0.856       | 51.15       | 31.32         | 0.61             |
| 400 mV/s  | 0.847    | 0.688       | 69.71       | 24.97         | 0.36             |

### Key Observations

1. **20 mV/s Performance Issue**: STM32 shows very poor linearity (R² = 0.014) at 20 mV/s, while Palmsens performs well (R² = 0.866). This suggests STM32 may have issues with slow scan rates.

2. **Overall Linearity**: Both systems show good linearity at 50-200 mV/s range, with R² > 0.85 for most conditions.

3. **Sensitivity Trends**: 
   - STM32 sensitivity increases with scan rate (slope: 7.23 → 69.71)
   - Palmsens sensitivity is more stable across scan rates (slope: 16.59 → 31.32)

4. **High Scan Rate Performance**: At 400 mV/s, both systems show reduced linearity, but STM32 maintains higher R² (0.847 vs 0.688).

### Slope Ratio Analysis
- **Below 1.0**: STM32 more sensitive (50-400 mV/s)
- **Above 1.0**: Palmsens more sensitive (20 mV/s)
- **Trend**: Slope ratio decreases with increasing scan rate (2.29 → 0.36)

### Recommendations

1. **STM32 Improvements Needed**:
   - Investigate 20 mV/s performance issues
   - Optimize for slow scan rate stability

2. **Palmsens Advantages**:
   - More consistent performance across scan rates
   - Better linearity at very slow scan rates
   - Wider concentration range capability

3. **Optimal Operating Conditions**:
   - Both systems: 50-200 mV/s range for best linearity
   - STM32: Avoid 20 mV/s, consider >50 mV/s
   - Palmsens: Suitable for full range 20-400 mV/s

### Technical Notes
- All data converted to µA units for direct comparison
- Baseline correction applied using linear fit to first/last 20% of data
- Peak height calculated as max - min of baseline-corrected current
- Analysis includes 140 total data points across both systems

### Files Generated
- `stm32_vs_palmsens_comparison_20250826_205048.png` - Comparison plots
- `stm32_vs_palmsens_report_20250826_205048.json` - Detailed numeric results
- `palmsens_simple_analysis_20250826_204705.png` - Palmsens-only analysis
- `palmsens_simple_report_20250826_204705.json` - Palmsens-only results

This analysis provides the foundation for:
1. System selection based on application requirements
2. Optimization targets for STM32 development
3. Validation of Palmsens as reference standard
4. Protocol development for CV experiments