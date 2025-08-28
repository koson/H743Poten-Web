# Color and Symbol Guidelines for Publication Figures

## 🎨 **Standardized Color Palette**

### **Primary Device Colors**
```
Palmsens:
- Primary Color: #2E86AB (RGB: 46, 134, 171) - Professional Blue
- Border Color: #1F4E79 (RGB: 31, 78, 121) - Dark Blue
- Usage: Main data points, lines, error bars

STM32:
- Primary Color: #A23B72 (RGB: 162, 59, 114) - Deep Red/Magenta  
- Border Color: #7A1C4B (RGB: 122, 28, 75) - Dark Red
- Usage: Main data points, lines, error bars
```

### **Reference and Accent Colors**
```
Perfect Prediction Line:
- Color: #F18F01 (RGB: 241, 143, 1) - Orange
- Usage: Perfect prediction lines, reference lines

Statistical Elements:
- Grid Major: #CCCCCC (RGB: 204, 204, 204) - Light Gray
- Grid Minor: #EEEEEE (RGB: 238, 238, 238) - Very Light Gray
- Text/Borders: #000000 (RGB: 0, 0, 0) - Black
- Background: #FFFFFF (RGB: 255, 255, 255) - White
```

### **Additional Reference Colors**
```
Limits/Thresholds:
- Upper Limit: #C73E1D (RGB: 199, 62, 29) - Red
- Lower Limit: #2A9D8F (RGB: 42, 157, 143) - Teal
- Neutral Zone: #E9C46A (RGB: 233, 196, 106) - Yellow

Quality Indicators:
- Excellent: #2A9D8F (RGB: 42, 157, 143) - Green
- Good: #E9C46A (RGB: 233, 196, 106) - Yellow  
- Acceptable: #F4A261 (RGB: 244, 162, 97) - Orange
- Poor: #E76F51 (RGB: 231, 111, 81) - Red
```

## 📊 **Symbol Standards**

### **Primary Symbols**
```
Palmsens:
- Symbol: ● (Circle, filled)
- Size: 8-10 points
- Border: 1-1.5 points
- Usage: All scatter plots, individual data points

STM32:
- Symbol: ▲ (Triangle Up, filled)  
- Size: 8-10 points
- Border: 1-1.5 points
- Usage: All scatter plots, individual data points
```

### **Line Styles**
```
Data Connections:
- Palmsens: Solid line, 2pt width
- STM32: Solid line, 2pt width

Reference Lines:
- Perfect Prediction: Dashed line, 2pt width, Orange
- Bias Line: Dashed line, 1.5pt width, Red
- Limits of Agreement: Dotted line, 1pt width, Red

Trend Lines:
- Linear Fit: Solid line, 1.5pt width, matching device color
- Confidence Intervals: Dotted line, 1pt width, matching device color
```

### **Error Bar Specifications**
```
Standard Error Bars:
- Width: 1.5pt
- Cap Style: Perpendicular caps
- Cap Size: 6-8pt
- Color: Match parent data series

Error Bar Types:
- Standard Deviation: ± 1 SD (default)
- Standard Error: ± 1 SEM (when specified)
- Confidence Interval: ± 95% CI (when specified)
```

## 📏 **Typography Standards**

### **Font Specifications**
```
Primary Font: Arial (sans-serif)
- Available on all systems
- Clear at small sizes
- Professional appearance

Font Sizes:
- Figure Titles: 16pt, Bold
- Axis Titles: 14pt, Bold  
- Axis Labels: 12pt, Regular
- Legend Text: 11pt, Regular
- Annotations: 10pt, Regular
- Small Text: 9pt, Regular
```

### **Text Formatting**
```
Axis Titles:
- Include units in parentheses
- Example: "Concentration (mM)"
- Example: "Predicted Concentration (mM)"

Legend Entries:
- Include sample sizes
- Example: "Palmsens (n=220)"
- Example: "STM32 (n=183)"

Statistical Annotations:
- Use standard notation
- Example: "R² = 0.986"
- Example: "MAE = 0.55 mM"
- Example: "n = 403"
```

## 🔧 **Technical Specifications**

### **Figure Dimensions**
```
Single Column: 85mm width
1.5 Column: 130mm width  
Double Column: 180mm width

Aspect Ratios:
- Square plots: 1:1
- Landscape plots: 4:3 or 3:2
- Portrait plots: 3:4

Margins:
- Top: 15mm (for title)
- Bottom: 10mm  
- Left: 12mm (for Y-axis)
- Right: 10mm
```

### **Export Settings**
```
Format: PNG or PDF (vector preferred)
Resolution: 300 DPI minimum
Color Space: RGB for digital, CMYK for print
Compression: Lossless
Background: White (opaque)
```

### **Grid and Axis Settings**
```
Grid Lines:
- Major: Light gray (#CCCCCC), 0.5pt
- Minor: Very light gray (#EEEEEE), 0.25pt
- Style: Solid lines
- Transparency: 50%

Tick Marks:
- Major: 3pt length, inward
- Minor: 1.5pt length, inward
- Color: Black
- Width: 0.5pt

Axis Lines:
- Color: Black
- Width: 1pt
- Style: Solid
```

## 🔍 **Quality Control Checklist**

### **Color Accessibility**
- [ ] Colorblind-friendly palette (avoid red-green combinations)
- [ ] Sufficient contrast ratios (minimum 3:1)
- [ ] Symbols distinguishable without color
- [ ] Patterns work in grayscale

### **Consistency Checks**
- [ ] Same colors used across all related figures
- [ ] Same symbols used for same devices/conditions
- [ ] Same font and sizes throughout
- [ ] Same line weights and styles

### **Publication Readiness**
- [ ] All text readable at publication size
- [ ] High resolution (300 DPI minimum)
- [ ] Proper margins and spacing
- [ ] Legend includes all necessary information
- [ ] Axes properly labeled with units

## 📋 **Application Examples**

### **Figure 1A: Scatter Plot**
```
- Palmsens: Blue circles (●), #2E86AB
- STM32: Red triangles (▲), #A23B72  
- Perfect Line: Orange dashed, #F18F01
- Grid: Light gray (#CCCCCC)
- Background: White
```

### **Figure 1B: Error Bar Plot**
```
- Palmsens: Blue circles with blue error bars
- STM32: Red triangles with red error bars
- Error bars: ± 1 SD, cap style with whiskers
- Sample size annotations: Small black text
```

### **Legend Format**
```
Palmsens (n=220) ● ——
STM32 (n=183) ▲ ——  
Perfect Prediction (y=x) - - -
```

## 💡 **Best Practices**

1. **Consistency First**: Use same colors/symbols across all figures
2. **Accessibility**: Ensure colorblind accessibility  
3. **Clarity**: Symbols must be distinguishable at publication size
4. **Professional**: Follow journal style guidelines
5. **Documentation**: Include color codes in figure files
6. **Testing**: Print in grayscale to test readability

## 🎯 **Color Rationale**

- **Blue (Palmsens)**: Associated with reliability, professionalism
- **Red/Magenta (STM32)**: Contrasts well with blue, modern feel
- **Orange (Reference)**: High visibility, neutral association
- **Gray (Grid)**: Subtle, doesn't compete with data
- **Black (Text)**: Maximum readability and contrast

These guidelines ensure consistency, accessibility, and professional appearance across all publication figures.
