import sys
from pathlib import Path

print("🔍 Debugging Import Issues...")
print(f"Python version: {sys.version}")
print(f"Current directory: {Path.cwd()}")

# Add current directory to path
current_dir = str(Path(__file__).parent)
sys.path.insert(0, current_dir)
print(f"Added to path: {current_dir}")

# Try imports step by step
print("\n📦 Testing imports...")

try:
    import numpy as np
    print("✅ numpy imported")
except Exception as e:
    print(f"❌ numpy failed: {e}")

try:
    import pandas as pd
    print("✅ pandas imported")
except Exception as e:
    print(f"❌ pandas failed: {e}")

try:
    from scipy import signal
    print("✅ scipy imported")
except Exception as e:
    print(f"⚠️  scipy missing: {e}")

try:
    from sklearn.metrics import mean_squared_error
    print("✅ sklearn imported")
except Exception as e:
    print(f"⚠️  sklearn missing: {e}")

# Try importing our modules
print("\n🔬 Testing our modules...")

try:
    from config import PeakDetectionConfig
    print("✅ config module imported")
except Exception as e:
    print(f"❌ config failed: {e}")
    import traceback
    traceback.print_exc()

try:
    from peak_detection_framework import TraditionalCVAnalyzer
    print("✅ peak_detection_framework imported")
except Exception as e:
    print(f"❌ peak_detection_framework failed: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Debug completed!")
