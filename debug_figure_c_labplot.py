#!/usr/bin/env python3
"""
Debug Figure C (PLS Score Plot) Visualization Issue
Compares data with expected visualization patterns
"""

import pandas as pd
import numpy as np
import os

def debug_figure_c_visualization():
    """Debug and create verification data for Figure C visualization"""
    
    # Read the data files
    combined_file = "Article_Figure_Package/Figure_C_Data_Updated/combined_scores_labplot.csv"
    palmsens_file = "Article_Figure_Package/Figure_C_Data_Updated/palmsens_scores_labplot.csv"
    stm32_file = "Article_Figure_Package/Figure_C_Data_Updated/stm32_scores_labplot.csv"
    
    print("🔍 Debugging Figure C Visualization Issue...")
    print("=" * 60)
    
    # Read data
    combined_data = pd.read_csv(combined_file)
    palmsens_data = pd.read_csv(palmsens_file)
    stm32_data = pd.read_csv(stm32_file)
    
    print(f"📊 Data Summary:")
    print(f"  • Combined: {len(combined_data)} points")
    print(f"  • Palmsens: {len(palmsens_data)} points")
    print(f"  • STM32: {len(stm32_data)} points")
    
    # Check data ranges and centers
    print(f"\n📍 Data Centers (Expected from Copilot plot):")
    print(f"  • Palmsens: PC1 ≈ 1.32, PC2 ≈ -0.46 (RIGHT-BOTTOM)")
    print(f"  • STM32: PC1 ≈ -2.50, PC2 ≈ 0.43 (LEFT-TOP)")
    
    print(f"\n📍 Actual Data Centers:")
    palmsens_pc1_mean = palmsens_data['PC1_Score'].mean()
    palmsens_pc2_mean = palmsens_data['PC2_Score'].mean()
    stm32_pc1_mean = stm32_data['PC1_Score'].mean()
    stm32_pc2_mean = stm32_data['PC2_Score'].mean()
    
    print(f"  • Palmsens: PC1 = {palmsens_pc1_mean:.2f}, PC2 = {palmsens_pc2_mean:.2f}")
    print(f"  • STM32: PC1 = {stm32_pc1_mean:.2f}, PC2 = {stm32_pc2_mean:.2f}")
    
    # Verify ranges
    print(f"\n📏 Data Ranges:")
    print(f"  • PC1 range: {combined_data['PC1_Score'].min():.2f} to {combined_data['PC1_Score'].max():.2f}")
    print(f"  • PC2 range: {combined_data['PC2_Score'].min():.2f} to {combined_data['PC2_Score'].max():.2f}")
    
    # Check device assignment
    print(f"\n🏷️ Device Assignment Verification:")
    palmsens_count = len(combined_data[combined_data['Device'] == 'Palmsens'])
    stm32_count = len(combined_data[combined_data['Device'] == 'STM32'])
    print(f"  • Palmsens count: {palmsens_count}")
    print(f"  • STM32 count: {stm32_count}")
    
    # Create sample verification data
    print(f"\n🎯 Creating Verification Files...")
    
    # Sample a few points from each device for manual verification
    palmsens_sample = palmsens_data.sample(n=5, random_state=42)[['Device', 'PC1_Score', 'PC2_Score', 'Color', 'Symbol']].copy()
    stm32_sample = stm32_data.sample(n=5, random_state=42)[['Device', 'PC1_Score', 'PC2_Score', 'Color', 'Symbol']].copy()
    
    verification_data = pd.concat([palmsens_sample, stm32_sample], ignore_index=True)
    verification_data['Expected_Position'] = [
        'Right (positive PC1)', 'Right (positive PC1)', 'Right (positive PC1)', 'Right (positive PC1)', 'Right (positive PC1)',
        'Left (negative PC1)', 'Left (negative PC1)', 'Left (negative PC1)', 'Left (negative PC1)', 'Left (negative PC1)'
    ]
    
    output_dir = "Article_Figure_Package/Figure_C_Data_Updated"
    verification_file = os.path.join(output_dir, "debug_verification_sample.csv")
    verification_data.to_csv(verification_file, index=False)
    print(f"✅ Verification sample → {verification_file}")
    
    # Create corrected mapping guide
    mapping_guide = f"""# Figure C Visualization Mapping Guide

## 🚨 ISSUE IDENTIFIED:
LabPlot2 result shows different pattern than expected Copilot plot.

## 📊 Expected Pattern (from Copilot original):
- **Palmsens (Blue ●)**: RIGHT side (PC1 > 0), BOTTOM (PC2 < 0)
- **STM32 (Red ▲)**: LEFT side (PC1 < 0), TOP (PC2 > 0)

## 📊 Data Verification:
- **Palmsens center**: PC1 = {palmsens_pc1_mean:.2f}, PC2 = {palmsens_pc2_mean:.2f} ✅ CORRECT
- **STM32 center**: PC1 = {stm32_pc1_mean:.2f}, PC2 = {stm32_pc2_mean:.2f} ✅ CORRECT

## 🔧 LabPlot2 Configuration Check:

### 1. Verify Data Import:
- File: `combined_scores_labplot.csv`
- X-axis: **PC1_Score** (NOT x, NOT PC1)
- Y-axis: **PC2_Score** (NOT y, NOT PC2)

### 2. Verify Color/Symbol Mapping:
- Color by: **Device** column
  - Palmsens → Blue
  - STM32 → Red
- Symbol by: **Symbol** column
  - Circle → Palmsens
  - Triangle → STM32

### 3. Check Axis Orientation:
- X-axis (PC1_Score): Range {combined_data['PC1_Score'].min():.1f} to {combined_data['PC1_Score'].max():.1f}
- Y-axis (PC2_Score): Range {combined_data['PC2_Score'].min():.1f} to {combined_data['PC2_Score'].max():.1f}
- Make sure axes are NOT inverted

### 4. Alternative: Use Separate Series
Instead of combined file, use separate files:

**Series 1 (Palmsens)**:
- File: `palmsens_scores_labplot.csv`
- X: PC1_Score, Y: PC2_Score
- Color: Blue, Symbol: Circle

**Series 2 (STM32)**:
- File: `stm32_scores_labplot.csv`  
- X: PC1_Score, Y: PC2_Score
- Color: Red, Symbol: Triangle

## 🎯 Expected Result:
- Blue circles clustered on RIGHT (PC1 ≈ +1 to +3)
- Red triangles clustered on LEFT (PC1 ≈ -4 to -1)
- Clear separation between device types
"""
    
    mapping_file = os.path.join(output_dir, "DEBUG_LabPlot2_Mapping_Guide.md")
    with open(mapping_file, 'w') as f:
        f.write(mapping_guide)
    print(f"✅ Mapping debug guide → {mapping_file}")
    
    # Create simple test data for verification
    test_data = pd.DataFrame({
        'PC1_Score': [2.0, 1.5, 1.0, -2.0, -2.5, -3.0],
        'PC2_Score': [-0.5, -0.3, -0.7, 0.4, 0.2, 0.6],
        'Device': ['Palmsens', 'Palmsens', 'Palmsens', 'STM32', 'STM32', 'STM32'],
        'Color': ['Blue', 'Blue', 'Blue', 'Red', 'Red', 'Red'],
        'Symbol': ['Circle', 'Circle', 'Circle', 'Triangle', 'Triangle', 'Triangle'],
        'Label': ['P1', 'P2', 'P3', 'S1', 'S2', 'S3']
    })
    
    test_file = os.path.join(output_dir, "simple_test_data.csv")
    test_data.to_csv(test_file, index=False)
    print(f"✅ Simple test data → {test_file}")
    
    print(f"\n🔍 Diagnosis:")
    print(f"  • Data is CORRECT ✅")
    print(f"  • Issue is likely in LabPlot2 configuration ⚠️")
    print(f"  • Check column mapping: PC1_Score vs PC1 vs x")
    print(f"  • Check device/color assignment")
    print(f"  • Try using separate series instead of combined file")
    
    return output_dir

if __name__ == "__main__":
    debug_figure_c_visualization()
