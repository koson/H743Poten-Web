# Article Figure Package - Complete Documentation

## 📦 **Package Overview**
Complete publication-ready figure package for PLS concentration prediction analysis, including data files, LabPlot2 instructions, and article content example.

## 📁 **Package Structure**
```
Article_Figure_Package/
├── Article_Content_Example.md              # Complete article content example
├── Mathematical_Methods_Appendix.md        # Detailed mathematical framework
├── Color_Symbol_Guidelines.md              # Standardized formatting guidelines
├── README.md                               # This file
├── Figure_A_Data/                          # Data for Figure 1A (Individual Predictions)
│   ├── palmsens_predictions.csv            # Palmsens individual prediction data (n=220)
│   ├── stm32_predictions.csv               # STM32 individual prediction data (n=183)
│   ├── perfect_prediction_line.csv         # Perfect prediction reference line (y=x)
│   └── LabPlot2_Instructions_A.md          # Detailed LabPlot2 setup for Figure A
├── Figure_B_Data/                          # Data for Figure 1B (Mean ± Error Bars)
│   ├── concentration_means_palmsens.csv    # Palmsens statistics by concentration
│   ├── concentration_means_stm32.csv       # STM32 statistics by concentration  
│   ├── concentration_statistics.csv        # Combined statistics (backup)
│   └── LabPlot2_Instructions_B.md          # Detailed LabPlot2 setup for Figure B
└── Figure_C_Data/                          # Data for Figure 1C (Instrument Classification)
    ├── pls_scores_all.csv                  # All samples PLS scores (n=403)
    ├── pls_scores_palmsens.csv             # Palmsens PLS scores (n=220)
    ├── pls_scores_stm32.csv                # STM32 PLS scores (n=183)
    ├── device_separation_summary.csv       # Statistical separation metrics
    ├── pls_score_statistics.json           # Detailed classification results
    └── LabPlot2_Instructions_C.md          # Detailed LabPlot2 setup for Figure C
```

## 🧮 **Mathematical Transparency and Reproducibility**

### **Comprehensive Mathematical Documentation**
This package includes complete mathematical framework documentation in `Mathematical_Methods_Appendix.md`:

- **PLS Theory**: Complete derivation from first principles
- **NIPALS Algorithm**: Step-by-step implementation details
- **Validation Metrics**: All statistical formulas with interpretations
- **Error Propagation**: Uncertainty quantification methodology
- **Quality Control**: Mathematical basis for method validation

### **Scientific Rigor Benefits**
- **Peer Review Confidence**: Reviewers can verify all calculations
- **Reproducibility**: Other researchers can replicate exact methodology  
- **Method Transfer**: Clear understanding enables cross-laboratory implementation
- **Regulatory Compliance**: Meets FDA/ICH guidelines for analytical validation
- **Educational Value**: Serves as reference for students and practitioners

### **Implementation Transparency**
- All algorithms documented with convergence criteria
- Statistical tests specified with assumptions and limitations
- Cross-validation strategies explained in mathematical detail
- Uncertainty sources quantified and propagated properly

## 🎯 **Target Figures**

### **Figure 1A: Individual PLS Prediction Results**
- **Type**: Scatter plot
- **Shows**: All 403 individual predictions vs actual concentrations
- **Purpose**: Demonstrate overall model accuracy and data distribution
- **Key Elements**:
  - Palmsens data: Blue circles (●)
  - STM32 data: Red triangles (▲)
  - Perfect prediction line: Orange dashed line
  - Overall statistics: R² = 0.986, MAE = 0.55 mM

### **Figure 1B: Concentration-Dependent Performance**
- **Type**: Line plot with error bars
- **Shows**: Mean predictions ± SD for each concentration level
- **Purpose**: Illustrate precision trends and device comparison
- **Key Elements**:
  - Error bars representing ± 1 Standard Deviation
  - Sample sizes annotated for each point
  - Clear concentration-dependent precision trends
  - Both devices showing similar performance patterns

### **Figure 1C: Instrument Classification Analysis**
- **Type**: PLS score plot
- **Shows**: PC1 vs PC2 scores revealing instrument-specific signatures
- **Purpose**: Demonstrate analytical equivalence while acknowledging instrumental differences
- **Key Elements**:
  - Palmsens data: Blue circles (●)
  - STM32 data: Red circles (●)
  - Classification accuracy: 30.8%
  - PC1 separation: 3.81, PC2 separation: 0.88

## 📊 **Data File Descriptions**

### **Figure A Data Files**
1. **palmsens_predictions.csv** (220 rows)
   - Individual prediction results from Palmsens system
   - Columns: Sample_ID, Device, Actual_Concentration_mM, Predicted_Concentration_mM, errors, voltammetric parameters

2. **stm32_predictions.csv** (183 rows)
   - Individual prediction results from STM32 system
   - Same column structure as Palmsens file

3. **perfect_prediction_line.csv** (2 rows)
   - Reference line data for perfect prediction (y=x)
   - Columns: Actual_Concentration_mM, Predicted_Concentration_mM

### **Figure B Data Files**
1. **concentration_means_palmsens.csv** (5 rows)
   - Statistical summary for Palmsens by concentration
   - Columns: Concentration, N_Samples, Mean, SD, SEM, CV%, Bias, Abs_Error

2. **concentration_means_stm32.csv** (5 rows)
   - Statistical summary for STM32 by concentration
   - Same column structure as Palmsens summary

3. **concentration_statistics.csv** (10 rows)
   - Combined statistics for both devices (backup file)

### **Figure C Data Files**
1. **pls_scores_all.csv** (403 rows)
   - PLS scores for all samples showing instrument separation
   - Columns: Sample_ID, Device, Concentration, PC1_Score, PC2_Score

2. **pls_scores_palmsens.csv** (220 rows)
   - PLS scores for Palmsens samples only
   - Same column structure as all scores file

3. **pls_scores_stm32.csv** (183 rows)
   - PLS scores for STM32 samples only
   - Same column structure as all scores file

4. **device_separation_summary.csv** (2 rows)
   - Statistical summary of device separation by PC component
   - Columns: Component, Palmsens_Mean, STM32_Mean, Separation, P_Value

5. **pls_score_statistics.json** (1 file)
   - Detailed classification statistics and model performance metrics
   - Contains separation distances, classification accuracy, and validation results

## 🎨 **Standardized Design Elements**

### **Color Scheme**
- **Palmsens**: #2E86AB (Professional Blue)
- **STM32**: #A23B72 (Deep Red/Magenta)
- **Reference Lines**: #F18F01 (Orange)
- **Grid**: #CCCCCC (Light Gray)

### **Symbols**
- **Palmsens**: ● (Circle, filled)
- **STM32**: ▲ (Triangle, filled)
- **Size**: 8-10 points
- **Border**: 1-1.5 points

### **Typography**
- **Font**: Arial (sans-serif)
- **Title**: 16pt Bold
- **Axis Labels**: 14pt Bold
- **Legends**: 11pt Regular

## 🔧 **LabPlot2 Setup**

### **Prerequisites**
- LabPlot2 software installed
- All data files downloaded to accessible location
- Basic familiarity with LabPlot2 interface

### **Setup Process**
1. **Figure A**: Follow `Figure_A_Data/LabPlot2_Instructions_A.md`
   - Import 3 CSV files
   - Create scatter plot with perfect prediction line
   - Format symbols, colors, and legend

2. **Figure B**: Follow `Figure_B_Data/LabPlot2_Instructions_B.md`
   - Import 2 statistical CSV files
   - Create line plot with error bars
   - Add sample size annotations

3. **Figure C**: Follow `Figure_C_Data/LabPlot2_Instructions_C.md`
   - Import PLS score CSV files
   - Create scatter plot showing PC1 vs PC2
   - Apply conditional formatting for device separation

### **Quality Assurance**
- Each instruction file includes detailed checklist
- Color codes specified for consistency
- Export settings provided for publication quality

## 📝 **Article Integration**

### **Content Structure**
The `Article_Content_Example.md` provides:
- **Abstract excerpt** with key findings
- **Results section** with detailed figure descriptions
- **Statistical interpretation** of both figures
- **Publication-ready figure captions**
- **Method validation discussion**

### **Figure Captions**
Complete, publication-ready captions including:
- Detailed descriptions of what each panel shows
- Sample sizes and statistical metrics
- Color/symbol coding explanations
- Key findings and interpretations

## 🎯 **Publication Guidelines**

### **Journal Targets**
- Analytical Chemistry
- Electrochimica Acta  
- Sensors and Actuators B
- Talanta
- Analytica Chimica Acta

### **Technical Requirements**
- **Resolution**: 300 DPI minimum
- **Format**: PNG or PDF (vector preferred)
- **Size**: Single column (85mm) or 1.5 column (130mm)
- **Color Space**: RGB for digital, CMYK for print

### **Style Compliance**
- Follows ACS (American Chemical Society) guidelines
- Colorblind-friendly palette
- Professional typography
- Clear statistical reporting

## ✅ **Quality Control Checklist**

### **Data Integrity**
- [ ] All data files contain expected number of rows
- [ ] No missing values in critical columns
- [ ] Statistical calculations verified
- [ ] Sample sizes match reported values

### **Figure Quality**
- [ ] Colors consistent with guidelines
- [ ] Symbols clearly distinguishable
- [ ] Text readable at publication size
- [ ] Legend complete and accurate
- [ ] Error bars properly implemented

### **Documentation**
- [ ] All instruction files complete
- [ ] Color codes documented
- [ ] File structure clear
- [ ] Example content comprehensive

## 🚀 **Usage Instructions**

### **For Figure Creation**
1. Download entire Article_Figure_Package
2. Open LabPlot2
3. Follow instructions in respective subfolder
4. Use provided data files exactly as structured
5. Apply color/symbol guidelines consistently

### **For Article Writing**
1. Reference Article_Content_Example.md for structure
2. Use Mathematical_Methods_Appendix.md for detailed methodology
3. Use provided figure captions as templates
4. Adapt statistical interpretations as needed
5. Ensure consistency with your journal's style

### **For Mathematical Transparency**
1. Consult Mathematical_Methods_Appendix.md for all equations
2. Include relevant formulas in your methodology section
3. Reference specific algorithms and validation procedures
4. Maintain statistical rigor in results interpretation

### **For Consistency**
1. Use Color_Symbol_Guidelines.md for all related figures
2. Maintain same font choices throughout manuscript
3. Apply same statistical reporting format
4. Use same abbreviations and terminology

## 📞 **Support Information**

### **File Issues**
- Check data file formats (CSV with comma separators)
- Verify LabPlot2 version compatibility
- Ensure proper file encoding (UTF-8)

### **Quality Issues**
- Refer to quality control checklists
- Cross-reference with color guidelines
- Validate against example content

### **Customization**
- Colors can be adjusted while maintaining contrast
- Symbols should remain consistent for device identification
- Text sizes may need adjustment for specific journals

## 🎉 **Expected Outcomes**

Upon completion, you will have:
- **Three publication-ready figures** (1A, 1B, and 1C)
- **Consistent visual design** across all figures
- **Complete data transparency** with source files
- **Professional formatting** meeting journal standards
- **Comprehensive documentation** for reproducibility
- **Scientific integrity** showing both similarities and differences between instruments

This package provides everything needed to create high-quality, publication-ready figures that effectively communicate your PLS analysis results while maintaining scientific rigor and visual excellence. The three-panel approach demonstrates analytical equivalence (Figures A & B) while acknowledging instrumental differences (Figure C) for complete transparency.
