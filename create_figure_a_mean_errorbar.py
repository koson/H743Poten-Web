#!/usr/bin/env python3
"""
Create Figure A with Mean ± Error Bar (Scatter Plot Style)
Replaces individual points with mean ± error bar for each concentration
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import json

def create_figure_a_mean_errorbar():
    """Create Figure A with mean ± error bar data"""
    
    # Input file path (in archive)
    input_file = "archive/result_folders/pls_mean_errorbar_analysis_20250828_213748/pls_detailed_statistics_20250828_213751.csv"
    
    # Output directory
    output_dir = "Article_Figure_Package/Figure_A_Data_Updated"
    
    print("📊 Creating Figure A with Mean ± Error Bar...")
    print(f"Input: {input_file}")
    
    # Read the data
    df = pd.read_csv(input_file)
    print(f"Data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"Devices: {df['Device'].unique()}")
    print(f"Concentrations: {sorted(df['Actual_Concentration_mM'].unique())}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # ===========================================
    # Figure A: Mean ± Error Bar Scatter Plot
    # ===========================================
    print("\n🎯 Creating Figure A Data (Mean ± Error Bar Scatter)...")
    
    # Format data for scatter plot with error bars
    def format_scatter_errorbar_data(device_data, device_name, symbol_style):
        return pd.DataFrame({
            'Actual_Concentration_mM': device_data['Actual_Concentration_mM'],
            'Predicted_Mean_mM': device_data['Predicted_Mean_mM'],
            'Predicted_Std_mM': device_data['Predicted_Std_mM'],
            'SEM_mM': device_data['Predicted_SEM_mM'],
            'Upper_Error_mM': device_data['Predicted_Mean_mM'] + device_data['Predicted_Std_mM'],
            'Lower_Error_mM': device_data['Predicted_Mean_mM'] - device_data['Predicted_Std_mM'],
            'Upper_SEM_mM': device_data['Predicted_Mean_mM'] + device_data['Predicted_SEM_mM'],
            'Lower_SEM_mM': device_data['Predicted_Mean_mM'] - device_data['Predicted_SEM_mM'],
            'N_Samples': device_data['N_Samples'],
            'CV_Percent': device_data['CV_Percent'],
            'Bias_mM': device_data['Bias_mM'],
            'Device': device_name,
            'Symbol': symbol_style,
            'Error_Type': 'Standard_Deviation'
        })
    
    # Split data by device
    palmsens_stats = df[df['Device'] == 'Palmsens'].copy()
    stm32_stats = df[df['Device'] == 'STM32'].copy()
    
    # Format for scatter plot with error bars
    palmsens_scatter = format_scatter_errorbar_data(palmsens_stats, 'Palmsens', 'Circle')
    stm32_scatter = format_scatter_errorbar_data(stm32_stats, 'STM32', 'Triangle')
    
    # Save individual device files
    palmsens_file = os.path.join(output_dir, "palmsens_mean_scatter.csv")
    stm32_file = os.path.join(output_dir, "stm32_mean_scatter.csv")
    
    palmsens_scatter.to_csv(palmsens_file, index=False)
    stm32_scatter.to_csv(stm32_file, index=False)
    
    print(f"✅ Palmsens mean scatter: {len(palmsens_scatter)} points → {palmsens_file}")
    print(f"✅ STM32 mean scatter: {len(stm32_scatter)} points → {stm32_file}")
    
    # Create combined file for easier plotting
    combined_scatter = pd.concat([palmsens_scatter, stm32_scatter], ignore_index=True)
    combined_file = os.path.join(output_dir, "combined_mean_scatter.csv")
    combined_scatter.to_csv(combined_file, index=False)
    print(f"✅ Combined mean scatter → {combined_file}")
    
    # Create perfect prediction line (same as before)
    concentrations = sorted(df['Actual_Concentration_mM'].unique())
    perfect_line = pd.DataFrame({
        'Actual_Concentration_mM': concentrations,
        'Predicted_Concentration_mM': concentrations,
        'Line_Type': 'Perfect_Prediction',
        'Line_Style': 'Dashed',
        'Line_Color': 'Orange'
    })
    
    perfect_file = os.path.join(output_dir, "perfect_prediction_line.csv")
    perfect_line.to_csv(perfect_file, index=False)
    print(f"✅ Perfect prediction line → {perfect_file}")
    
    # Create unity line variants for different ranges
    conc_range = np.linspace(0, max(concentrations) * 1.1, 100)
    unity_detailed = pd.DataFrame({
        'Actual_Concentration_mM': conc_range,
        'Predicted_Concentration_mM': conc_range,
        'Line_Type': 'Unity_Line_Detailed',
        'Line_Style': 'Dashed',
        'Line_Color': 'Orange'
    })
    
    unity_file = os.path.join(output_dir, "unity_line_detailed.csv")
    unity_detailed.to_csv(unity_file, index=False)
    print(f"✅ Detailed unity line → {unity_file}")
    
    # ===========================================
    # Create LabPlot2 instruction supplement
    # ===========================================
    
    labplot_instructions = """# LabPlot2 Instructions for Figure A (Mean ± Error Bar Scatter)

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
"""
    
    instructions_file = os.path.join(output_dir, "LabPlot2_Instructions_A_MeanErrorBar.md")
    with open(instructions_file, 'w') as f:
        f.write(labplot_instructions)
    print(f"✅ LabPlot2 instructions → {instructions_file}")
    
    # ===========================================
    # Create metadata
    # ===========================================
    
    # Calculate statistics
    overall_data = []
    for _, row in df.iterrows():
        # Estimate individual predictions for R² calculation
        np.random.seed(42 + int(row['Actual_Concentration_mM']*10))
        predictions = np.random.normal(row['Predicted_Mean_mM'], row['Predicted_Std_mM'], int(row['N_Samples']))
        actuals = np.full(int(row['N_Samples']), row['Actual_Concentration_mM'])
        
        overall_data.extend(list(zip(actuals, predictions)))
    
    actuals_all = [x[0] for x in overall_data]
    predictions_all = [x[1] for x in overall_data]
    
    overall_r2 = 1 - np.sum((np.array(actuals_all) - np.array(predictions_all))**2) / np.sum((np.array(actuals_all) - np.mean(actuals_all))**2)
    overall_mae = np.mean([abs(a - p) for a, p in overall_data])
    
    metadata = {
        'extraction_timestamp': datetime.now().isoformat(),
        'figure_type': 'Mean ± Error Bar Scatter Plot',
        'source_file': input_file,
        'total_data_points': len(combined_scatter),
        'palmsens_points': len(palmsens_scatter),
        'stm32_points': len(stm32_scatter),
        'concentration_levels': len(concentrations),
        'concentrations_mM': concentrations,
        'estimated_overall_r2': round(overall_r2, 4),
        'estimated_overall_mae_mM': round(overall_mae, 3),
        'error_bar_type': 'Standard Deviation (±1 SD)',
        'symbol_coding': {
            'Palmsens': 'Blue Circles (●)',
            'STM32': 'Red Triangles (▲)'
        },
        'files_created': [
            'palmsens_mean_scatter.csv',
            'stm32_mean_scatter.csv',
            'combined_mean_scatter.csv',
            'perfect_prediction_line.csv',
            'unity_line_detailed.csv',
            'LabPlot2_Instructions_A_MeanErrorBar.md'
        ]
    }
    
    # Save metadata
    metadata_file = os.path.join(output_dir, "figure_a_mean_errorbar_metadata.json")
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Metadata saved → {metadata_file}")
    
    # ===========================================
    # Summary
    # ===========================================
    print(f"\n📈 Figure A (Mean ± Error Bar) Summary:")
    print(f"  • Data points: {len(combined_scatter)} (5 concentrations × 2 devices)")
    print(f"  • Palmsens points: {len(palmsens_scatter)}")
    print(f"  • STM32 points: {len(stm32_scatter)}")
    print(f"  • Error bars: ±1 Standard Deviation")
    print(f"  • Estimated R²: {overall_r2:.4f}")
    print(f"  • Estimated MAE: {overall_mae:.3f} mM")
    
    print(f"\n🎨 Files created for LabPlot2:")
    print(f"📁 {output_dir}/")
    print(f"  ├── palmsens_mean_scatter.csv")
    print(f"  ├── stm32_mean_scatter.csv")
    print(f"  ├── combined_mean_scatter.csv")
    print(f"  ├── perfect_prediction_line.csv")
    print(f"  ├── unity_line_detailed.csv")
    print(f"  ├── LabPlot2_Instructions_A_MeanErrorBar.md")
    print(f"  └── figure_a_mean_errorbar_metadata.json")
    
    print(f"\n✅ Figure A (Mean ± Error Bar) created successfully!")
    print(f"This replaces the individual points with clean mean ± error bar visualization.")
    
    return output_dir

if __name__ == "__main__":
    create_figure_a_mean_errorbar()
