#!/usr/bin/env python3
"""
Extract Figure C (PLS Score Plot PC1-PC2) Data for LabPlot2
Separates by device type for easy color coding
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import json

def extract_figure_c_scores():
    """Extract PLS Score Plot data separated by device"""
    
    # Input files (existing Figure C data)
    input_dir = "Article_Figure_Package/Figure_C_Data"
    palmsens_file = os.path.join(input_dir, "pls_scores_palmsens.csv")
    stm32_file = os.path.join(input_dir, "pls_scores_stm32.csv")
    
    # Output directory
    output_dir = "Article_Figure_Package/Figure_C_Data_Updated"
    
    print("🎯 Extracting Figure C (PLS Score Plot) Data for LabPlot2...")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if input files exist
    if not os.path.exists(palmsens_file):
        print(f"❌ Error: {palmsens_file} not found!")
        return None
    
    if not os.path.exists(stm32_file):
        print(f"❌ Error: {stm32_file} not found!")
        return None
    
    # Read existing data
    palmsens_data = pd.read_csv(palmsens_file)
    stm32_data = pd.read_csv(stm32_file)
    
    print(f"✅ Palmsens data: {len(palmsens_data)} points")
    print(f"✅ STM32 data: {len(stm32_data)} points")
    print(f"Total points: {len(palmsens_data) + len(stm32_data)}")
    
    # ===========================================
    # Enhanced Palmsens Data for LabPlot2
    # ===========================================
    print("\n📊 Processing Palmsens Score Data...")
    
    palmsens_enhanced = palmsens_data.copy()
    palmsens_enhanced['Device'] = 'Palmsens'
    palmsens_enhanced['Color'] = 'Blue'
    palmsens_enhanced['Symbol'] = 'Circle'
    palmsens_enhanced['Symbol_Size'] = 8
    palmsens_enhanced['Alpha'] = 0.7
    
    # Add point index for tracking
    palmsens_enhanced['Point_Index'] = range(1, len(palmsens_enhanced) + 1)
    palmsens_enhanced['Device_Point_ID'] = ['Palmsens_' + str(i) for i in range(1, len(palmsens_enhanced) + 1)]
    
    # Save enhanced Palmsens data
    palmsens_output_file = os.path.join(output_dir, "palmsens_scores_labplot.csv")
    palmsens_enhanced.to_csv(palmsens_output_file, index=False)
    print(f"✅ Enhanced Palmsens data → {palmsens_output_file}")
    
    # ===========================================
    # Enhanced STM32 Data for LabPlot2
    # ===========================================
    print("\n📊 Processing STM32 Score Data...")
    
    stm32_enhanced = stm32_data.copy()
    stm32_enhanced['Device'] = 'STM32'
    stm32_enhanced['Color'] = 'Red'
    stm32_enhanced['Symbol'] = 'Triangle'
    stm32_enhanced['Symbol_Size'] = 8
    stm32_enhanced['Alpha'] = 0.7
    
    # Add point index for tracking
    stm32_enhanced['Point_Index'] = range(1, len(stm32_enhanced) + 1)
    stm32_enhanced['Device_Point_ID'] = ['STM32_' + str(i) for i in range(1, len(stm32_enhanced) + 1)]
    
    # Save enhanced STM32 data
    stm32_output_file = os.path.join(output_dir, "stm32_scores_labplot.csv")
    stm32_enhanced.to_csv(stm32_output_file, index=False)
    print(f"✅ Enhanced STM32 data → {stm32_output_file}")
    
    # ===========================================
    # Combined Data for Unified Plotting
    # ===========================================
    print("\n📊 Creating Combined Dataset...")
    
    combined_data = pd.concat([palmsens_enhanced, stm32_enhanced], ignore_index=True)
    combined_data['Global_Point_ID'] = range(1, len(combined_data) + 1)
    
    # Save combined data
    combined_output_file = os.path.join(output_dir, "combined_scores_labplot.csv")
    combined_data.to_csv(combined_output_file, index=False)
    print(f"✅ Combined data → {combined_output_file}")
    
    # ===========================================
    # Create Device Summary Statistics
    # ===========================================
    print("\n📈 Calculating Summary Statistics...")
    
    summary_stats = []
    
    for device_name, device_data in [('Palmsens', palmsens_enhanced), ('STM32', stm32_enhanced)]:
        stats = {
            'Device': device_name,
            'N_Points': len(device_data),
            'PC1_Mean': device_data['PC1_Score'].mean(),
            'PC1_Std': device_data['PC1_Score'].std(),
            'PC1_Min': device_data['PC1_Score'].min(),
            'PC1_Max': device_data['PC1_Score'].max(),
            'PC2_Mean': device_data['PC2_Score'].mean(),
            'PC2_Std': device_data['PC2_Score'].std(),
            'PC2_Min': device_data['PC2_Score'].min(),
            'PC2_Max': device_data['PC2_Score'].max(),
            'PC1_Range': device_data['PC1_Score'].max() - device_data['PC1_Score'].min(),
            'PC2_Range': device_data['PC2_Score'].max() - device_data['PC2_Score'].min()
        }
        summary_stats.append(stats)
    
    summary_df = pd.DataFrame(summary_stats)
    summary_file = os.path.join(output_dir, "device_summary_statistics.csv")
    summary_df.to_csv(summary_file, index=False)
    print(f"✅ Summary statistics → {summary_file}")
    
    # ===========================================
    # Create Axis Ranges for Consistent Plotting
    # ===========================================
    print("\n📏 Creating Axis Range Information...")
    
    # Calculate optimal plot ranges
    all_pc1 = combined_data['PC1_Score']
    all_pc2 = combined_data['PC2_Score']
    
    pc1_margin = (all_pc1.max() - all_pc1.min()) * 0.05
    pc2_margin = (all_pc2.max() - all_pc2.min()) * 0.05
    
    axis_ranges = {
        'PC1_Min': all_pc1.min() - pc1_margin,
        'PC1_Max': all_pc1.max() + pc1_margin,
        'PC2_Min': all_pc2.min() - pc2_margin,
        'PC2_Max': all_pc2.max() + pc2_margin,
        'PC1_Center': all_pc1.mean(),
        'PC2_Center': all_pc2.mean(),
        'Suggested_PC1_Range': [-3, 5],  # Based on the image
        'Suggested_PC2_Range': [-3, 1.5],  # Based on the image
        'Grid_Lines': True,
        'Zero_Lines': True
    }
    
    # Create grid reference points
    pc1_grid = np.arange(-3, 6, 1)
    pc2_grid = np.arange(-3, 2, 0.5)
    
    grid_references = []
    for pc1_val in pc1_grid:
        grid_references.append({'Type': 'PC1_Grid', 'PC1_Score': pc1_val, 'PC2_Score': 0, 'Line_Type': 'Vertical'})
    
    for pc2_val in pc2_grid:
        grid_references.append({'Type': 'PC2_Grid', 'PC1_Score': 0, 'PC2_Score': pc2_val, 'Line_Type': 'Horizontal'})
    
    grid_df = pd.DataFrame(grid_references)
    grid_file = os.path.join(output_dir, "plot_grid_references.csv")
    grid_df.to_csv(grid_file, index=False)
    print(f"✅ Grid references → {grid_file}")
    
    # ===========================================
    # Create LabPlot2 Instructions
    # ===========================================
    
    labplot_instructions = f"""# LabPlot2 Instructions for Figure C (PLS Score Plot)

## Data Files:
- `palmsens_scores_labplot.csv` - Palmsens PC1-PC2 scores ({len(palmsens_enhanced)} points)
- `stm32_scores_labplot.csv` - STM32 PC1-PC2 scores ({len(stm32_enhanced)} points)
- `combined_scores_labplot.csv` - All data combined ({len(combined_data)} points)
- `device_summary_statistics.csv` - Statistical summaries
- `plot_grid_references.csv` - Grid line references

## Plot Setup:

### 1. Create Scatter Plot:
- **X-axis**: PC1 (range: -3 to 5)
- **Y-axis**: PC2 (range: -3 to 1.5)
- **Title**: "Device Classification - PLS Score Plot"

### 2. Add Data Series:

#### Option A: Separate Series (Recommended)
**Palmsens Series:**
- File: `palmsens_scores_labplot.csv`
- X: PC1_Score, Y: PC2_Score
- Symbol: Blue circles (●)
- Size: 8 points
- Alpha: 0.7

**STM32 Series:**
- File: `stm32_scores_labplot.csv`
- X: PC1_Score, Y: PC2_Score
- Symbol: Red triangles (▲)
- Size: 8 points
- Alpha: 0.7

#### Option B: Single Series with Color Coding
- File: `combined_scores_labplot.csv`
- X: PC1_Score, Y: PC2_Score
- Color by: Device column
- Symbol by: Symbol column

### 3. Format Plot:
- **Grid**: Enable major grid lines
- **Zero lines**: Add reference lines at PC1=0 and PC2=0
- **Legend**: Show device legend (top-right)
- **Axis labels**: "PC1" and "PC2"

### 4. Statistical Information:
- **Palmsens**: {len(palmsens_enhanced)} samples
- **STM32**: {len(stm32_enhanced)} samples
- **Total**: {len(combined_data)} samples
- **Classification**: Shows device separation in PLS space

## Expected Result:
Scatter plot showing clear separation (or overlap) between Palmsens and STM32 
devices in the first two principal components space.
"""
    
    instructions_file = os.path.join(output_dir, "LabPlot2_Instructions_Figure_C.md")
    with open(instructions_file, 'w') as f:
        f.write(labplot_instructions)
    print(f"✅ LabPlot2 instructions → {instructions_file}")
    
    # ===========================================
    # Create Metadata
    # ===========================================
    
    metadata = {
        'extraction_timestamp': datetime.now().isoformat(),
        'figure_type': 'PLS Score Plot (PC1 vs PC2)',
        'source_files': [palmsens_file, stm32_file],
        'total_data_points': len(combined_data),
        'palmsens_points': len(palmsens_enhanced),
        'stm32_points': len(stm32_enhanced),
        'pc1_range_actual': [float(all_pc1.min()), float(all_pc1.max())],
        'pc2_range_actual': [float(all_pc2.min()), float(all_pc2.max())],
        'pc1_range_suggested': [-3, 5],
        'pc2_range_suggested': [-3, 1.5],
        'color_coding': {
            'Palmsens': 'Blue Circles (●)',
            'STM32': 'Red Triangles (▲)'
        },
        'statistical_summary': {
            'palmsens_pc1_mean': float(palmsens_enhanced['PC1_Score'].mean()),
            'palmsens_pc2_mean': float(palmsens_enhanced['PC2_Score'].mean()),
            'stm32_pc1_mean': float(stm32_enhanced['PC1_Score'].mean()),
            'stm32_pc2_mean': float(stm32_enhanced['PC2_Score'].mean())
        },
        'files_created': [
            'palmsens_scores_labplot.csv',
            'stm32_scores_labplot.csv',
            'combined_scores_labplot.csv',
            'device_summary_statistics.csv',
            'plot_grid_references.csv',
            'LabPlot2_Instructions_Figure_C.md'
        ]
    }
    
    # Save metadata
    metadata_file = os.path.join(output_dir, "figure_c_metadata.json")
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Metadata saved → {metadata_file}")
    
    # ===========================================
    # Summary
    # ===========================================
    print(f"\n🎯 Figure C (PLS Score Plot) Summary:")
    print(f"  • Total points: {len(combined_data)}")
    print(f"  • Palmsens (Blue ●): {len(palmsens_enhanced)} points")
    print(f"  • STM32 (Red ▲): {len(stm32_enhanced)} points")
    print(f"  • PC1 range: {all_pc1.min():.2f} to {all_pc1.max():.2f}")
    print(f"  • PC2 range: {all_pc2.min():.2f} to {all_pc2.max():.2f}")
    
    print(f"\n📊 Device Separation:")
    print(f"  • Palmsens center: PC1={palmsens_enhanced['PC1_Score'].mean():.2f}, PC2={palmsens_enhanced['PC2_Score'].mean():.2f}")
    print(f"  • STM32 center: PC1={stm32_enhanced['PC1_Score'].mean():.2f}, PC2={stm32_enhanced['PC2_Score'].mean():.2f}")
    
    print(f"\n🎨 Files created for LabPlot2:")
    print(f"📁 {output_dir}/")
    print(f"  ├── palmsens_scores_labplot.csv")
    print(f"  ├── stm32_scores_labplot.csv")
    print(f"  ├── combined_scores_labplot.csv")
    print(f"  ├── device_summary_statistics.csv")
    print(f"  ├── plot_grid_references.csv")
    print(f"  ├── LabPlot2_Instructions_Figure_C.md")
    print(f"  └── figure_c_metadata.json")
    
    print(f"\n✅ Figure C data extraction completed!")
    print(f"Ready for LabPlot2 with separated device data for easy color coding.")
    
    return output_dir

if __name__ == "__main__":
    extract_figure_c_scores()
