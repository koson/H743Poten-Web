# LabPlot2 Instructions for Figure 1C: Instrument Classification Analysis

## 📊 Figure Description
**PLS Score Plot** showing instrument-specific clustering and separation between Palmsens and STM32 potentiostat systems based on electrochemical response patterns.

## 📁 Data Files Required
```
Figure_C_Data/
├── pls_scores_all.csv              # All samples with PC1/PC2 scores (n=403)
├── pls_scores_palmsens.csv         # Palmsens samples only (n=220)
├── pls_scores_stm32.csv            # STM32 samples only (n=183)
├── device_separation_summary.csv   # Statistical summary by device
└── pls_score_statistics.json       # Detailed separation statistics
```

## 🎨 LabPlot2 Setup Instructions

### Step 1: Create New Project
1. Open LabPlot2
2. File > New Project
3. Name: "Figure_1C_Instrument_Classification"

### Step 2: Import Data Files
1. **Import All Scores:**
   - File > Import > CSV
   - Select `pls_scores_all.csv`
   - Name the spreadsheet: "All_Scores"

2. **Import Palmsens Scores (Optional):**
   - File > Import > CSV  
   - Select `pls_scores_palmsens.csv`
   - Name the spreadsheet: "Palmsens_Scores"

3. **Import STM32 Scores (Optional):**
   - File > Import > CSV
   - Select `pls_scores_stm32.csv`
   - Name the spreadsheet: "STM32_Scores"

### Step 3: Create Main Plot
1. **Insert Worksheet:**
   - Right-click Project > Insert > Worksheet
   - Name: "Figure_1C"

2. **Insert Cartesian Plot:**
   - Right-click Worksheet > Insert > XY-Plot
   - Name: "PLS_Score_Plot"

### Step 4: Add Palmsens Data Points
**Method A: Using Conditional Formatting (Recommended)**

1. **Right-click Plot > Insert > XY-Curve**
2. **Data Source:** All_Scores
3. **Configure:**
   - **X Column:** PC1_Score
   - **Y Column:** PC2_Score
   - **Name:** "All Samples"

4. **Enable Conditional Formatting:**
   - **Symbol Properties > Use conditional formatting**
   - **Add Condition 1:**
     - **Column:** Device
     - **Operator:** equals
     - **Value:** Palmsens
     - **Symbol:** Circle (●)
     - **Size:** 8 points
     - **Border Color:** #1F4E79 (dark blue)
     - **Fill Color:** #2E86AB (blue)
     - **Border Width:** 1 point

   - **Add Condition 2:**
     - **Column:** Device
     - **Operator:** equals
     - **Value:** STM32
     - **Symbol:** Circle (●)
     - **Size:** 8 points
     - **Border Color:** #7A1C4B (dark red)
     - **Fill Color:** #A23B72 (red)
     - **Border Width:** 1 point

**Method B: Separate Data Series (Alternative)**

1. **Palmsens Series:**
   - Data Source: Palmsens_Scores
   - X: PC1_Score, Y: PC2_Score
   - Symbol: Blue circles (●)

2. **STM32 Series:**
   - Data Source: STM32_Scores  
   - X: PC1_Score, Y: PC2_Score
   - Symbol: Red circles (●)

### Step 5: Format Axes
1. **X-Axis (PC1):**
   - **Title:** "PC1 (First Component)"
   - **Title Font:** Arial, 14pt, Bold
   - **Label Font:** Arial, 12pt
   - **Range:** -5 to +4 (adjust based on data)
   - **Major Ticks:** Every 2 units
   - **Minor Ticks:** Every 0.5 units

2. **Y-Axis (PC2):**
   - **Title:** "PC2 (Second Component)"
   - **Title Font:** Arial, 14pt, Bold
   - **Label Font:** Arial, 12pt
   - **Range:** -2.5 to +1.5 (adjust based on data)
   - **Major Ticks:** Every 1 unit
   - **Minor Ticks:** Every 0.25 units

### Step 6: Add Grid and Format
1. **Grid Settings:**
   - **Major Grid:** Light gray (#CCCCCC), 0.5pt width
   - **Minor Grid:** Very light gray (#EEEEEE), 0.25pt width
   - **Style:** Solid lines

2. **Plot Area:**
   - **Background:** White
   - **Border:** Black, 1pt width

### Step 7: Insert Legend
1. **Right-click Plot > Insert > Legend**
2. **Position:** Top Right corner
3. **Settings:**
   - **Background:** White with border
   - **Font:** Arial, 11pt
   - **Border:** Black, 0.5pt
   - **Padding:** 5pt all sides

4. **Legend Content:**
   - Palmsens (n=220) ●
   - STM32 (n=183) ●

### Step 8: Add Statistical Information Box
1. **Right-click Plot > Insert > Text Label**
2. **Content:**
   ```
   Model Performance:
   Classification Score: 30.8%
   PC1 Separation: 3.81
   PC2 Separation: 0.88
   
   Total Samples: n = 403
   ```
3. **Position:** Top Left corner
4. **Font:** Arial, 10pt
5. **Background:** Light gray (#F5F5F5) with border

### Step 9: Add Separation Indicators (Optional)
1. **Add vertical line at x=0:**
   - Right-click Plot > Insert > Custom Line
   - Vertical line at PC1 = 0
   - Style: Dashed, gray, thin
   - Label: "Separation Line"

### Step 10: Final Formatting
1. **Plot Title:** 
   - Text: "(C) Instrument Classification Analysis"
   - Font: Arial, 16pt, Bold
   - Position: Top center

2. **Margins:** 
   - Top: 15mm
   - Bottom: 10mm  
   - Left: 12mm
   - Right: 10mm

## 📊 Data Interpretation Guidelines

### **What the Plot Shows:**
- **X-axis (PC1)**: Primary component separating the instruments
- **Y-axis (PC2)**: Secondary component providing additional discrimination
- **Blue points**: Palmsens measurements
- **Red points**: STM32 measurements

### **Expected Patterns:**
- **Partial separation** between blue and red clusters
- **Some overlap** in the central region
- **Distinct clustering** indicating instrument-specific signatures
- **No perfect separation** (realistic for real-world instruments)

### **Statistical Interpretation:**
- **30.8% Classification Score**: Moderate separation (not perfect)
- **PC1 Separation = 3.81**: Strong separation along primary component
- **PC2 Separation = 0.88**: Weaker separation along secondary component

## 📏 Export Settings for Publication
1. **File > Export > Image**
2. **Format:** PNG or PDF
3. **Resolution:** 300 DPI minimum
4. **Size:** 
   - Width: 120mm (smaller than main prediction plots)
   - Height: 100mm (square-ish aspect ratio works well for score plots)

## ✅ Quality Checklist
- [ ] Both device clusters clearly visible
- [ ] Appropriate axis ranges showing all data points
- [ ] Legend identifies both devices with sample sizes
- [ ] Grid enhances readability without overwhelming data
- [ ] Statistical information box positioned clearly
- [ ] Colors consistent with other figures (blue/red scheme)
- [ ] Fonts consistent and readable at publication size
- [ ] Axis titles descriptive and clear

## 🎯 Expected Result
A professional scatter plot showing:
- Clear but partial separation between instruments
- Palmsens cluster (blue) generally on positive PC1 side
- STM32 cluster (red) generally on negative PC1 side
- Some overlap demonstrating realistic instrument similarity
- Statistical information confirming moderate classification performance

## 📝 Scientific Interpretation Notes
This figure demonstrates:
1. **Instrument Specificity**: Each device has measurable electrochemical signatures
2. **Realistic Performance**: Not claiming perfect separation (scientific honesty)
3. **Method Validation**: Understanding instrument-to-instrument variation
4. **Quality Control**: Basis for identifying data source in mixed datasets

## 💡 Key Message
The plot supports the conclusion that while both instruments provide comparable analytical performance for concentration prediction, they possess distinct electrochemical response characteristics that can be statistically distinguished, representing appropriate scientific transparency about instrumental differences.

## 🔍 Troubleshooting
- **If points overlap too much**: Adjust symbol transparency (80-90%)
- **If axis ranges are too tight**: Expand by 10-20% beyond data limits
- **If separation not clear**: Verify PC1/PC2 data are correctly imported
- **If colors don't match**: Use exact hex codes specified in Color Guidelines
