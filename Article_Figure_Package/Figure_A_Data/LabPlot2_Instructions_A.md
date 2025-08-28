# LabPlot2 Instructions for Figure 1A: Individual Prediction Results

## 📊 Figure Description
**Scatter plot of predicted versus actual concentrations** showing individual prediction results for all measurements with perfect prediction reference line.

## 📁 Data Files Required
```
Figure_A_Data/
├── palmsens_predictions.csv        # Palmsens individual predictions (n=220)
├── stm32_predictions.csv           # STM32 individual predictions (n=183) 
└── perfect_prediction_line.csv     # Perfect prediction reference line (y=x)
```

## 🎨 LabPlot2 Setup Instructions

### Step 1: Create New Project
1. Open LabPlot2
2. File > New Project
3. Name: "Figure_1A_PLS_Predictions"

### Step 2: Import Data Files
1. **Import Palmsens Data:**
   - File > Import > CSV
   - Select `palmsens_predictions.csv`
   - Name the spreadsheet: "Palmsens_Data"

2. **Import STM32 Data:**
   - File > Import > CSV  
   - Select `stm32_predictions.csv`
   - Name the spreadsheet: "STM32_Data"

3. **Import Perfect Line:**
   - File > Import > CSV
   - Select `perfect_prediction_line.csv`
   - Name the spreadsheet: "Perfect_Line"

### Step 3: Create Main Plot
1. **Insert Worksheet:**
   - Right-click Project > Insert > Worksheet
   - Name: "Figure_1A"

2. **Insert Cartesian Plot:**
   - Right-click Worksheet > Insert > XY-Plot
   - Name: "PLS_Prediction_Plot"

### Step 4: Add Palmsens Data Series
1. **Right-click Plot > Insert > XY-Curve**
2. **Data Source:** Palmsens_Data
3. **Configure:**
   - **X Column:** Actual_Concentration_mM
   - **Y Column:** Predicted_Concentration_mM
   - **Name:** "Palmsens (n=220)"

4. **Symbol Settings:**
   - **Type:** Circle (●)
   - **Size:** 8 points
   - **Border Color:** #1F4E79 (dark blue)
   - **Filling Color:** #2E86AB (blue)
   - **Border Width:** 1 point

5. **Line Settings:**
   - **Type:** No Line
   - **Skip gaps:** Checked

### Step 5: Add STM32 Data Series
1. **Right-click Plot > Insert > XY-Curve**
2. **Data Source:** STM32_Data
3. **Configure:**
   - **X Column:** Actual_Concentration_mM
   - **Y Column:** Predicted_Concentration_mM
   - **Name:** "STM32 (n=183)"

4. **Symbol Settings:**
   - **Type:** Triangle Up (▲)
   - **Size:** 8 points
   - **Border Color:** #7A1C4B (dark red)
   - **Filling Color:** #A23B72 (red)
   - **Border Width:** 1 point

5. **Line Settings:**
   - **Type:** No Line

### Step 6: Add Perfect Prediction Line
1. **Right-click Plot > Insert > XY-Curve**
2. **Data Source:** Perfect_Line
3. **Configure:**
   - **X Column:** Actual_Concentration_mM
   - **Y Column:** Predicted_Concentration_mM
   - **Name:** "Perfect Prediction (y=x)"

4. **Line Settings:**
   - **Type:** Solid Line
   - **Color:** #F18F01 (orange)
   - **Width:** 2 points
   - **Style:** Dashed

5. **Symbol Settings:**
   - **Type:** No Symbol

### Step 7: Format Axes
1. **X-Axis (Bottom):**
   - **Title:** "Actual Concentration (mM)"
   - **Title Font:** Arial, 14pt, Bold
   - **Label Font:** Arial, 12pt
   - **Range:** 0 to 25
   - **Major Ticks:** Every 5 mM
   - **Minor Ticks:** Every 1 mM

2. **Y-Axis (Left):**
   - **Title:** "Predicted Concentration (mM)"
   - **Title Font:** Arial, 14pt, Bold
   - **Label Font:** Arial, 12pt
   - **Range:** 0 to 25
   - **Major Ticks:** Every 5 mM
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
2. **Position:** Top Right corner
3. **Settings:**
   - **Background:** White with border
   - **Font:** Arial, 11pt
   - **Border:** Black, 0.5pt
   - **Padding:** 5pt all sides

### Step 10: Add Statistics Text Box
1. **Right-click Plot > Insert > Text Label**
2. **Content:**
   ```
   Overall Model Performance:
   R² = 0.986
   MAE = 0.55 mM
   Total n = 403
   ```
3. **Position:** Top Left corner
4. **Font:** Arial, 11pt
5. **Background:** White with light border

### Step 11: Final Formatting
1. **Plot Title:** 
   - Text: "(A) Individual PLS Prediction Results"
   - Font: Arial, 16pt, Bold
   - Position: Top center

2. **Margins:** 
   - Top: 15mm
   - Bottom: 10mm  
   - Left: 12mm
   - Right: 10mm

## 📏 Export Settings for Publication
1. **File > Export > Image**
2. **Format:** PNG or PDF
3. **Resolution:** 300 DPI minimum
4. **Size:** 
   - Width: 150mm (single column) or 180mm (1.5 column)
   - Height: Auto (maintain aspect ratio)

## ✅ Quality Checklist
- [ ] Both data series clearly visible and distinguishable
- [ ] Perfect prediction line clearly visible (orange dashed)
- [ ] Legend shows all three elements with correct symbols
- [ ] Axes properly labeled with units
- [ ] Grid enhances readability without overwhelming data
- [ ] Statistics text box positioned clearly
- [ ] All fonts consistent and readable at publication size
- [ ] Colors are colorblind-friendly
- [ ] Figure title descriptive and clear

## 🎯 Expected Result
A professional scatter plot showing:
- Palmsens data as blue circles (●)
- STM32 data as red triangles (▲)  
- Perfect prediction line as orange dashed line
- Clear correlation between actual and predicted values
- Professional formatting suitable for publication

## 📝 Notes
- This figure demonstrates overall model accuracy
- Individual data points show scatter and any outliers
- Perfect prediction line provides reference for ideal performance
- Legend and statistics provide essential information for interpretation
