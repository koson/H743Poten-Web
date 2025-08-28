# Mathematical Methods and Statistical Analysis: Detailed Appendix

## 📐 Mathematical Framework Overview

This appendix provides comprehensive mathematical details supporting the PLS analysis and statistical validation presented in the main article. All equations, algorithms, and statistical tests are documented for full transparency and reproducibility.

## 🧮 Partial Least Squares (PLS) Theory

### 1. PLS Regression Model

The fundamental PLS relationship establishes a linear mapping between electrochemical response matrix **X** and concentration vector **y**:

**y** = **X****β** + **ε**

**Matrix Dimensions:**
- **X**: n × p (samples × voltage points)
- **y**: n × 1 (samples × concentration)
- **β**: p × 1 (regression coefficients)
- **ε**: n × 1 (residual errors)

### 2. Bilinear Decomposition

PLS simultaneously decomposes both **X** and **y** into latent variable structures:

**X** = **T****P**^T + **E** = Σᵢ₌₁ᴬ **t**ᵢ**p**ᵢ^T + **E**

**y** = **T****q**^T + **f** = Σᵢ₌₁ᴬ **t**ᵢ**q**ᵢ^T + **f**

**Where:**
- **T** = score matrix (n × A) - latent variable coordinates
- **P** = X-loadings (p × A) - variable weights for X
- **q** = y-loadings (A × 1) - variable weights for y
- **E**, **f** = residual matrices after A components
- A = number of PLS components (optimized via cross-validation)

### 3. Inner Relationship

The core PLS relationship connects X-scores to y-scores:

**u** = **T****c** + **h**

Where:
- **u** = y-scores (n × A)
- **c** = inner weights (A × 1)
- **h** = inner residuals

## 🔢 NIPALS Algorithm Implementation

### Nonlinear Iterative Partial Least Squares (NIPALS)

**Initialization:**
```
X₀ = X_centered_scaled
Y₀ = y_centered
```

**For each component a = 1, 2, ..., A:**

**Step 1: Initialize y-score**
```
uₐ = first column of Yₐ₋₁ (or random initialization)
```

**Step 2: Iterative convergence loop**
```
Repeat until convergence:
  1. wₐ = Xₐ₋₁ᵀ uₐ / (uₐᵀ uₐ)         # X-weights
  2. wₐ = wₐ / ||wₐ||                   # Normalize to unit length
  3. tₐ = Xₐ₋₁ wₐ                       # X-scores
  4. qₐ = Yₐ₋₁ᵀ tₐ / (tₐᵀ tₐ)           # y-weights
  5. uₐ = Yₐ₋₁ qₐ / (qₐᵀ qₐ)           # y-scores
  
Convergence criterion: ||wₐ,new - wₐ,old|| < tolerance
```

**Step 3: Component extraction**
```
pₐ = Xₐ₋₁ᵀ tₐ / (tₐᵀ tₐ)               # X-loadings
bₐ = uₐᵀ tₐ / (tₐᵀ tₐ)                 # Inner weight
```

**Step 4: Deflation**
```
Xₐ = Xₐ₋₁ - tₐ pₐᵀ                     # Remove component from X
Yₐ = Yₐ₋₁ - bₐ tₐ qₐᵀ                 # Remove component from Y
```

**Convergence Parameters:**
- Tolerance: 1×10⁻⁶
- Maximum iterations: 500
- Typical convergence: 3-8 iterations per component

## 📊 Model Validation Metrics

### 1. Coefficient of Determination (R²)

**Training R²:**
```
R² = 1 - (SS_res / SS_tot)
SS_res = Σᵢ₌₁ⁿ (yᵢ - ŷᵢ)²
SS_tot = Σᵢ₌₁ⁿ (yᵢ - ȳ)²
```

**Cross-Validation R² (Q²):**
```
Q² = 1 - (PRESS / SS_tot)
PRESS = Σᵢ₌₁ⁿ (yᵢ - ŷᵢ,cv)²
```

Where ŷᵢ,cv represents predictions from cross-validation excluding sample i.

### 2. Performance Metrics

**Mean Absolute Error (MAE):**
```
MAE = (1/n) × Σᵢ₌₁ⁿ |yᵢ - ŷᵢ|
```

**Root Mean Square Error (RMSE):**
```
RMSE = √[(1/n) × Σᵢ₌₁ⁿ (yᵢ - ŷᵢ)²]
```

**Mean Absolute Percentage Error (MAPE):**
```
MAPE = (100/n) × Σᵢ₌₁ⁿ |yᵢ - ŷᵢ|/|yᵢ|
```

**Bias (Systematic Error):**
```
Bias = (1/n) × Σᵢ₌₁ⁿ (ŷᵢ - yᵢ)
```

## 🎯 Cross-Validation Strategies

### 1. Leave-One-Out Cross-Validation (LOO-CV)

**Procedure:**
```
For i = 1 to n:
  1. Remove sample i from training set
  2. Build PLS model with remaining n-1 samples
  3. Predict concentration for sample i
  4. Store prediction ŷᵢ,cv
  
Calculate Q² using all LOO predictions
```

### 2. K-Fold Cross-Validation

**Procedure:**
```
1. Randomly partition data into k equal-sized folds
2. For each fold j = 1 to k:
   - Use fold j as validation set
   - Use remaining k-1 folds as training set
   - Build PLS model and predict fold j
3. Calculate average Q² across all folds
```

**Implemented with k = 5 and 100 random partitions**

### 3. Monte Carlo Cross-Validation

**Procedure:**
```
For iteration i = 1 to n_iterations:
  1. Randomly split data 80% training / 20% validation
  2. Build PLS model on training set
  3. Predict validation set
  4. Calculate Q²ᵢ
  
Final Q² = mean(Q²ᵢ) ± std(Q²ᵢ)
```

**Implemented with 100 iterations**

## 🔍 Statistical Tests and Validation

### 1. Normality Tests

**Shapiro-Wilk Test:**
```
H₀: Residuals follow normal distribution
H₁: Residuals do not follow normal distribution
Test statistic: W = (Σᵢbᵢx₍ᵢ₎)² / Σᵢ(xᵢ - x̄)²
```

**Anderson-Darling Test:**
```
A² = -n - (1/n)Σᵢ₌₁ⁿ(2i-1)[ln F(X₍ᵢ₎) + ln(1-F(X₍ₙ₊₁₋ᵢ₎))]
```

### 2. Homoscedasticity Tests

**Breusch-Pagan Test:**
```
H₀: σ²ᵢ = σ² (constant variance)
H₁: σ²ᵢ = σ²g(αᵀzᵢ) (heteroscedasticity)
Test statistic: LM = nR² ~ χ²(p)
```

**White Test:**
```
Regress squared residuals on original predictors and cross-products
Test statistic: nR² ~ χ²(p)
```

### 3. Independence Tests

**Durbin-Watson Test:**
```
DW = Σᵢ₌₂ⁿ(eᵢ - eᵢ₋₁)² / Σᵢ₌₁ⁿeᵢ²
```

Where:
- DW ≈ 2: No autocorrelation
- DW < 2: Positive autocorrelation
- DW > 2: Negative autocorrelation

## 📈 Analytical Method Validation

### 1. Detection Limits

**Limit of Detection (LOD):**
```
LOD = 3.3 × (σ_blank / S)
```

**Limit of Quantification (LOQ):**
```
LOQ = 10 × (σ_blank / S)
```

Where:
- σ_blank = standard deviation of blank measurements
- S = calibration sensitivity (slope)

### 2. Precision Metrics

**Repeatability (Same Conditions):**
```
RSD_r = (s_r / x̄) × 100%
s_r = √[(Σᵢ₌₁ᵐΣⱼ₌₁ⁿ(xᵢⱼ - x̄ᵢ)²) / (m(n-1))]
```

**Intermediate Precision (Different Days/Operators):**
```
RSD_I = (s_I / x̄) × 100%
s_I = √[s_r² + s_L²]
```

Where s_L = between-group variance component.

**Reproducibility (Different Laboratories):**
```
RSD_R = (s_R / x̄) × 100%
s_R = √[s_I² + s_lab²]
```

### 3. Accuracy Assessment

**Bias Calculation:**
```
Bias = (x̄_measured - x_true) / x_true × 100%
```

**Recovery:**
```
Recovery% = (C_found / C_added) × 100%
```

**Trueness (ISO 5725):**
```
Trueness = |μ - μ_true|
```

Where μ = long-term mean of measurements.

## 🎭 Device Classification Mathematics

### 1. Principal Component Analysis for Classification

**Covariance Matrix:**
```
C = (1/(n-1)) × Xᵀcentered × Xcentered
```

**Eigendecomposition:**
```
C = VΛVᵀ
```

Where:
- V = eigenvector matrix (principal component directions)
- Λ = diagonal eigenvalue matrix (variance explained)

**PC Scores:**
```
T = Xcentered × V
```

### 2. Linear Discriminant Analysis (LDA)

**Between-Class Scatter Matrix:**
```
S_B = Σᵢ₌₁ᶜ nᵢ(μᵢ - μ)(μᵢ - μ)ᵀ
```

**Within-Class Scatter Matrix:**
```
S_W = Σᵢ₌₁ᶜ Σⱼ₌₁ⁿⁱ (xⱼ - μᵢ)(xⱼ - μᵢ)ᵀ
```

**Fisher's Linear Discriminant:**
```
w = S_W⁻¹(μ₁ - μ₂)
```

**Classification Boundary:**
```
w·x + w₀ = 0
w₀ = -½wᵀ(μ₁ + μ₂)
```

### 3. Separation Metrics

**Mahalanobis Distance:**
```
D²ᵢⱼ = (μᵢ - μⱼ)ᵀ Σ⁻¹ (μᵢ - μⱼ)
```

**Separation Power:**
```
SP = √[d² / (σ₁² + σ₂²)]
```

Where d = distance between group means.

**Classification Accuracy:**
```
Accuracy = (TP + TN) / (TP + TN + FP + FN) × 100%
```

## 📏 Uncertainty Quantification

### 1. Error Propagation

**General Propagation Formula:**
```
σ_f² = Σᵢ₌₁ⁿ (∂f/∂xᵢ)² σ_xᵢ² + 2ΣᵢΣⱼ₌ᵢ₊₁ⁿ (∂f/∂xᵢ)(∂f/∂xⱼ)σ_xᵢⱼ
```

**For PLS Prediction:**
```
σ_pred² = σ_model² + σ_instrumental² + σ_environmental²
```

### 2. Measurement Uncertainty (GUM Approach)

**Combined Standard Uncertainty:**
```
u_c²(y) = Σᵢ₌₁ᴺ cᵢ²u²(xᵢ) + 2ΣᵢΣⱼ₌ᵢ₊₁ᴺ cᵢcⱼu(xᵢ,xⱼ)
```

**Expanded Uncertainty (k=2, 95% confidence):**
```
U = k × u_c(y)
```

### 3. Bootstrap Confidence Intervals

**Bootstrap Procedure:**
```
For b = 1 to B bootstrap samples:
  1. Resample training data with replacement
  2. Build PLS model on bootstrap sample
  3. Calculate performance metric θ̂_b
  
95% CI = [θ̂_(0.025), θ̂_(0.975)]
```

## 🔬 Electrochemical Signal Processing

### 1. Baseline Correction

**Polynomial Detrending:**
```
I_corrected(V) = I_raw(V) - Σᵢ₌₀ᵖ aᵢVᵢ
```

Where polynomial coefficients aᵢ are fitted by least squares:
```
a = (VᵀV)⁻¹VᵀI_raw
```

**Asymmetric Least Squares (ALS):**
```
Minimize: Σᵢwᵢ(yᵢ - zᵢ)² + λΣᵢ(Δ²zᵢ)²
```

Where:
- wᵢ = asymmetric weights (higher for baseline points)
- λ = smoothness parameter
- Δ²zᵢ = second-order differences

### 2. Noise Filtering

**Savitzky-Golay Filter:**
```
ŷᵢ = Σⱼ₌₋ₘᵐ cⱼyᵢ₊ⱼ
```

Where cⱼ are convolution coefficients from least-squares polynomial fitting.

**Moving Average Filter:**
```
ŷᵢ = (1/(2m+1)) × Σⱼ₌₋ₘᵐ yᵢ₊ⱼ
```

### 3. Feature Selection

**Variance Threshold:**
```
Keep features where: Var(Xⱼ) > threshold
```

**Correlation Filter:**
```
Remove features where: |corr(Xᵢ,Xⱼ)| > threshold, i ≠ j
```

**Variable Importance in Projection (VIP):**
```
VIPⱼ = √[p × Σₕ₌₁ᴴ SS(bₕqₕ) × wⱼₕ² / Σₕ₌₁ᴴ SS(bₕqₕ)]
```

Where:
- SS(bₕqₕ) = sum of squares explained by component h
- wⱼₕ = weight of variable j in component h

## 📋 Quality Control Parameters

### 1. Control Chart Limits

**Shewhart Control Charts:**
```
UCL = μ + 3σ/√n
LCL = μ - 3σ/√n
```

**CUSUM Control Charts:**
```
C⁺ᵢ = max[0, C⁺ᵢ₋₁ + (xᵢ - μ₀ - K)]
C⁻ᵢ = max[0, C⁻ᵢ₋₁ - (xᵢ - μ₀ - K)]
```

Where K = allowable slack parameter.

### 2. Capability Indices

**Process Capability:**
```
Cp = (USL - LSL)/(6σ)
Cpk = min[(USL - μ)/(3σ), (μ - LSL)/(3σ)]
```

**Method Capability:**
```
Cm = (specification range)/(analytical range)
```

## 🎯 Optimization Algorithms

### 1. Component Number Selection

**Cross-Validation PRESS Minimization:**
```
PRESS(A) = Σᵢ₌₁ⁿ (yᵢ - ŷᵢ,cv(A))²
A_optimal = argmin(PRESS(A))
```

**Akaike Information Criterion (AIC):**
```
AIC = n × ln(RSS/n) + 2k
```

Where k = number of parameters (components).

**Bayesian Information Criterion (BIC):**
```
BIC = n × ln(RSS/n) + k × ln(n)
```

### 2. Hyperparameter Optimization

**Grid Search:**
```
For each parameter combination (α₁, α₂, ..., αₖ):
  1. Perform cross-validation
  2. Calculate performance metric
  3. Store best parameters
```

**Random Search:**
```
For i = 1 to n_iterations:
  1. Sample random parameter values
  2. Evaluate model performance
  3. Update best parameters if improved
```

## 🎨 Visualization Mathematics

### 1. Principal Component Biplots

**Sample Scores:**
```
T = XVₐ
```

**Variable Loadings:**
```
P = XᵀT(TᵀT)⁻¹
```

**Biplot Approximation:**
```
X ≈ TPᵀ
```

### 2. Confidence Ellipses

**Hotelling's T² Ellipse:**
```
(x - μ)ᵀS⁻¹(x - μ) = (p(n-1)/(n-p)) × F_p,n-p,α
```

**Normal Probability Ellipse:**
```
(x - μ)ᵀΣ⁻¹(x - μ) = χ²_p,α
```

## 📚 References and Standards

### Analytical Chemistry Standards
- **ICH Q2(R1)**: Validation of Analytical Procedures
- **AOAC Guidelines**: Statistical Manual
- **ISO 5725**: Accuracy and Precision of Measurement Methods
- **IUPAC Recommendations**: Analytical Method Validation

### Statistical Methods
- **Wold, S. et al.**: PLS Regression: A Basic Tool
- **Martens, H. & Naes, T.**: Multivariate Calibration
- **Hastie, T. et al.**: Elements of Statistical Learning
- **ISO/IEC Guide 98**: Uncertainty of Measurement (GUM)

### Software Implementation
- **scikit-learn**: Python machine learning library
- **NumPy/SciPy**: Numerical computing foundation
- **Pandas**: Data manipulation and analysis
- **Matplotlib/Seaborn**: Statistical visualization

---

**Note**: All mathematical procedures were implemented with numerical stability considerations, including regularization for matrix inversions and convergence monitoring for iterative algorithms. Code availability and detailed implementation notes are provided in the accompanying software repository.
