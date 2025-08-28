# LabPlot2 Instructions for Figure A (Mean ± Error Bar Scatter)

## Data Files Required:
- `palmsens_mean_scatter.csv` - Palmsens mean ± error data
- `stm32_mean_scatter.csv` - STM32 mean ± error data  
- `combined_mean_scatter.csv` - All data combined
- `perfect_prediction_line.csv` - Unity line reference
- `unity_line_detailed.csv` - Detailed unity line

## Plot Setup:

### 1. Create Scatter Plot
- X-axis: Actual_Concentration_mM
- Y-axis: Predicted_Mean_mM

### 2. Add Error Bars
- Use Upper_Error_mM and Lower_Error_mM for ± 1 SD
- Or use Upper_SEM_mM and Lower_SEM_mM for ± 1 SEM

### 3. Symbol Formatting:
- **Palmsens**: Blue circles (●) with error bars
- **STM32**: Red triangles (▲) with error bars

### 4. Add Perfect Prediction Line:
- Orange dashed line (y = x)
- Use unity_line_detailed.csv for smooth line

## Expected Result:
A clean scatter plot showing mean predictions ± error bars for each concentration level, 
demonstrating overall model accuracy and precision trends.
