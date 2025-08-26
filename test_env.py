print("Hello from Python!")
import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

try:
    import pandas as pd
    print(f"✅ pandas version: {pd.__version__}")
except:
    print("❌ pandas not available")

try:
    import numpy as np
    print(f"✅ numpy version: {np.__version__}")
except:
    print("❌ numpy not available")

try:
    import matplotlib
    print(f"✅ matplotlib version: {matplotlib.__version__}")
except:
    print("❌ matplotlib not available")