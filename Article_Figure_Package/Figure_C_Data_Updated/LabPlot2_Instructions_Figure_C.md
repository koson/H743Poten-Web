# LabPlot2 Instructions for Figure C (PLS Score Plot)

## Data Files:
- `palmsens_scores_labplot.csv` - Palmsens PC1-PC2 scores (220 points)
- `stm32_scores_labplot.csv` - STM32 PC1-PC2 scores (183 points)
- `combined_scores_labplot.csv` - All data combined (403 points)
- `device_summary_statistics.csv` - Statistical summaries
- `plot_grid_references.csv` - Grid line references

## Plot Setup:

### 1. Create Scatter Plot:
- **X-axis**: PC1_Score (range: -4 to 3)
- **Y-axis**: PC2_Score (range: -2 to 2)
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
- **Zero lines**: Add reference lines at PC1_Score=0 and PC2_Score=0
- **Legend**: Show device legend (top-right)
- **Axis labels**: "PC1_Score" and "PC2_Score"

### 4. Statistical Information:
- **Palmsens**: 220 samples
- **STM32**: 183 samples
- **Total**: 403 samples
- **Classification**: Shows device separation in PLS space

## Expected Result:
Scatter plot showing clear separation between Palmsens (right, blue circles) and STM32 
(left, red triangles) devices in the first two principal components space.
- **Palmsens cluster**: PC1 ≈ +1.3, PC2 ≈ -0.5 (right-bottom quadrant)
- **STM32 cluster**: PC1 ≈ -2.5, PC2 ≈ +0.4 (left-top quadrant)
