# LabPlot2 Instructions for Figure 1B: Concentration-Dependent Performance

## 📊 Figure Description
**Mean prediction accuracy with error bars** showing concentration-dependent performance for both potentiostat systems.

## 📁 Data Files Required
```
Figure_B_Data/
├── concentration_means_palmsens.csv    # Palmsens mean ± SD by concentration
├── concentration_means_stm32.csv       # STM32 mean ± SD by concentration
└── concentration_statistics.csv        # Combined statistics (backup)
```

## 🎨 LabPlot2 Setup Instructions

### Step 1: Create New Project
1. Open LabPlot2
2. File > New Project
3. Name: "Figure_1B_Concentration_Performance"

### Step 2: Import Data Files
1. **Import Palmsens Statistics:**
   - File > Import > CSV
   - Select `concentration_means_palmsens.csv`
   - Name the spreadsheet: "Palmsens_Stats"

2. **Import STM32 Statistics:**
   - File > Import > CSV  
   - Select `concentration_means_stm32.csv`
   - Name the spreadsheet: "STM32_Stats"

### Step 3: Create Main Plot
1. **Insert Worksheet:**
   - Right-click Project > Insert > Worksheet
   - Name: "Figure_1B"

2. **Insert Cartesian Plot:**
   - Right-click Worksheet > Insert > XY-Plot
   - Name: "Concentration_Performance_Plot"

### Step 4: Add Palmsens Data with Error Bars
1. **Right-click Plot > Insert > XY-Curve**
2. **Data Source:** Palmsens_Stats
3. **Configure:**
   - **X Column:** Actual_Concentration_mM
   - **Y Column:** Predicted_Mean_mM
   - **Name:** "Palmsens"

4. **Symbol Settings:**
   - **Type:** Circle (●)
   - **Size:** 10 points
   - **Border Color:** #1F4E79 (dark blue)
   - **Filling Color:** #2E86AB (blue)
   - **Border Width:** 1.5 points

5. **Line Settings:**
   - **Type:** Solid Line
   - **Color:** #2E86AB (blue)
   - **Width:** 2 points

6. **Error Bars (Vertical):**
   - **Enable:** Y Error Bars
   - **Data Column:** Predicted_Std_mM
   - **Type:** Symmetric (±)
   - **Cap Style:** Cap with whiskers
   - **Cap Size:** 8 points
   - **Line Width:** 1.5 points
   - **Color:** #2E86AB (blue)

### Step 5: Add STM32 Data with Error Bars
1. **Right-click Plot > Insert > XY-Curve**
2. **Data Source:** STM32_Stats
3. **Configure:**
   - **X Column:** Actual_Concentration_mM
   - **Y Column:** Predicted_Mean_mM
   - **Name:** "STM32"

4. **Symbol Settings:**
   - **Type:** Triangle Up (▲)
   - **Size:** 10 points
   - **Border Color:** #7A1C4B (dark red)
   - **Filling Color:** #A23B72 (red)
   - **Border Width:** 1.5 points

5. **Line Settings:**
   - **Type:** Solid Line
   - **Color:** #A23B72 (red)
   - **Width:** 2 points

6. **Error Bars (Vertical):**
   - **Enable:** Y Error Bars
   - **Data Column:** Predicted_Std_mM
   - **Type:** Symmetric (±)
   - **Cap Style:** Cap with whiskers
   - **Cap Size:** 8 points
   - **Line Width:** 1.5 points
   - **Color:** #A23B72 (red)

### Step 6: Add Perfect Prediction Reference Line
1. **Right-click Plot > Insert > XY-Curve**
2. **Manual Data Entry or use Perfect Line file**
3. **Configure:**
   - **X Values:** 0, 25
   - **Y Values:** 0, 25
   - **Name:** "Perfect Prediction (y=x)"

4. **Line Settings:**
   - **Type:** Dashed Line
   - **Color:** #F18F01 (orange)
   - **Width:** 2 points
   - **Dash Pattern:** Long dash

5. **Symbol Settings:**
   - **Type:** No Symbol

### Step 7: Format Axes
1. **X-Axis (Bottom):**
   - **Title:** "Actual Concentration (mM)"
   - **Title Font:** Arial, 14pt, Bold
   - **Label Font:** Arial, 12pt
   - **Range:** 0 to 22
   - **Major Ticks:** 0, 5, 10, 15, 20
   - **Minor Ticks:** Every 1 mM

2. **Y-Axis (Left):**
   - **Title:** "Predicted Concentration (mM)"
   - **Title Font:** Arial, 14pt, Bold
   - **Label Font:** Arial, 12pt
   - **Range:** 0 to 22
   - **Major Ticks:** 0, 5, 10, 15, 20
   - **Minor Ticks:** Every 1 mM

### Step 8: Add Grid and Format
1. **Grid Settings:**
   - **Major Grid:** Light gray (#CCCCCC), 0.5pt width
   - **Minor Grid:** Very light gray (#EEEEEE), 0.25pt width

2. **Plot Area:**
   - **Background:** White
   - **Border:** Black, 1pt width

### Step 9: Insert Legend
1. **Right-click Plot > Insert > Legend**
2. **Position:** Top Left corner
3. **Settings:**
   - **Background:** White with border
   - **Font:** Arial, 11pt
   - **Border:** Black, 0.5pt
   - **Padding:** 5pt all sides
   - **Items:** All three series (Palmsens, STM32, Perfect Prediction)

### Step 10: Add Sample Size Annotations
1. **For each concentration point, add text labels with sample sizes:**

   **Palmsens Sample Sizes:**
   - 0.5 mM: n=50
   - 1.0 mM: n=50  
   - 5.0 mM: n=50
   - 10.0 mM: n=50
   - 20.0 mM: n=20

   **STM32 Sample Sizes:**
   - 0.5 mM: n=30
   - 1.0 mM: n=50
   - 5.0 mM: n=50
   - 10.0 mM: n=40
   - 20.0 mM: n=13

2. **Method:**
   - Right-click Plot > Insert > Text Label
   - Position near each point
   - Font: Arial, 9pt
   - Format: "n=XX"

### Step 11: Add Statistics Table (Optional)
1. **Right-click Plot > Insert > Text Label**
2. **Content:**
   ```
   Error Bars: ± 1 Standard Deviation
   
   Concentration Range Performance:
   • 0.5-1.0 mM: High variability (CV > 25%)
   • 5.0-20.0 mM: Optimal precision (CV < 12%)
   ```
3. **Position:** Bottom Right corner
4. **Font:** Arial, 10pt
5. **Background:** Light gray with border

### Step 12: Final Formatting
1. **Plot Title:** 
   - Text: "(B) Concentration-Dependent Prediction Accuracy"
   - Font: Arial, 16pt, Bold
   - Position: Top center

2. **Margins:** 
   - Top: 15mm
   - Bottom: 10mm  
   - Left: 12mm
   - Right: 10mm

## 📊 Alternative: CV% Subplot (Optional Enhancement)
If space allows, add a secondary Y-axis or subplot showing CV%:

1. **Right Y-Axis for CV%:**
   - Add secondary Y-axis
   - Plot CV_Percent vs Actual_Concentration_mM
   - Use different line style (dotted)
   - Label: "Coefficient of Variation (%)"

## 📏 Export Settings for Publication
1. **File > Export > Image**
2. **Format:** PNG or PDF
3. **Resolution:** 300 DPI minimum
4. **Size:** 
   - Width: 150mm (single column) or 180mm (1.5 column)
   - Height: Auto (maintain aspect ratio)

## ✅ Quality Checklist
- [ ] Both data series clearly distinguishable
- [ ] Error bars properly sized and visible
- [ ] Perfect prediction line clearly visible
- [ ] Sample sizes annotated for each point
- [ ] Legend shows all elements with correct symbols
- [ ] Axes properly labeled with units
- [ ] Error bar meaning clearly indicated
- [ ] Grid enhances readability
- [ ] Colors are colorblind-friendly
- [ ] Professional formatting suitable for publication

## 🎯 Expected Result
A professional line plot with error bars showing:
- Palmsens data as blue circles (●) with blue error bars
- STM32 data as red triangles (▲) with red error bars
- Perfect prediction reference line (orange dashed)
- Sample sizes indicated for each point
- Clear demonstration of concentration-dependent precision

## 📊 Data Interpretation Guide
- **Error bars represent ± 1 Standard Deviation**
- **Smaller error bars = better precision**
- **Points closer to orange line = better accuracy**
- **Trend shows precision improves with concentration**

## 📝 Notes
- This figure shows concentration-dependent performance trends
- Error bars indicate measurement precision at each concentration
- Sample size annotations provide statistical context
- Perfect prediction line enables accuracy assessment
