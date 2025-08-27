#!/usr/bin/env python3
"""
Quick Test: Notebook Environment Setup
ทดสอบ environment ก่อนรัน Notebook
"""

print("🔧 Testing Notebook Environment...")
print("="*50)

# Test basic imports
try:
    import numpy as np
    print("✅ numpy:", np.__version__)
except ImportError as e:
    print("❌ numpy:", e)

try:
    import pandas as pd  
    print("✅ pandas:", pd.__version__)
except ImportError as e:
    print("❌ pandas:", e)

try:
    import matplotlib.pyplot as plt
    print("✅ matplotlib:", plt.matplotlib.__version__)
except ImportError as e:
    print("❌ matplotlib:", e)

try:
    import seaborn as sns
    print("✅ seaborn:", sns.__version__)
except ImportError as e:
    print("❌ seaborn:", e)

try:
    from scipy import signal
    print("✅ scipy")
except ImportError as e:
    print("❌ scipy:", e)

# Test our precision analyzer
try:
    import sys
    sys.path.append('.')
    from precision_peak_baseline_analyzer import PrecisionPeakBaselineAnalyzer
    print("✅ precision_peak_baseline_analyzer")
except ImportError as e:
    print("❌ precision_peak_baseline_analyzer:", e)

# Test Jupyter kernel
try:
    import ipykernel
    print("✅ ipykernel:", ipykernel.__version__)
except ImportError as e:
    print("❌ ipykernel:", e)

print("\n" + "="*50)
print("🎯 Environment test complete!")
print("💡 If any packages are missing, install them before running notebook")
