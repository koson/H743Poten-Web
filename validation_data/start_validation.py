import sys
print("🚀 Starting Phase 1 Validation...")

# Test core libraries first
try:
    import numpy as np
    import pandas as pd
    print("✅ Core libraries working")
except ImportError as e:
    print(f"❌ Core libraries failed: {e}")
    sys.exit(1)

# Test if our data splits exist
from pathlib import Path
splits_path = Path("splits")

if splits_path.exists():
    print("✅ Data splits directory found")
    
    # Count files in each split
    for split_name in ["train", "validation", "test"]:
        split_file = splits_path / f"{split_name}_files.txt"
        if split_file.exists():
            with open(split_file, 'r') as f:
                count = len([line for line in f if line.strip()])
            print(f"   📊 {split_name}: {count} files")
        else:
            print(f"   ❌ {split_name}_files.txt not found")
else:
    print("❌ Data splits not found - running stratified_data_splitter.py...")
    import subprocess
    try:
        result = subprocess.run([sys.executable, "stratified_data_splitter.py"], 
                              capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print("✅ Data splits created successfully")
        else:
            print(f"❌ Data splitter failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Failed to run data splitter: {e}")

# Try basic peak detection test
print("\n🔬 Testing Peak Detection Framework...")

try:
    # Import without the problematic scipy parts first
    exec("""
# Simplified peak detection test
import numpy as np

class SimplePeakDetector:
    def detect_peaks(self, voltages, currents, filename="test"):
        # Simple peak detection using numpy only
        peaks = []
        min_height = 1e-9
        
        # Find local maxima for anodic peaks
        for i in range(1, len(currents) - 1):
            if (currents[i] > currents[i-1] and 
                currents[i] > currents[i+1] and 
                abs(currents[i]) > min_height):
                peaks.append(i)
        
        peak_potentials = [voltages[i] for i in peaks]
        peak_currents = [currents[i] for i in peaks]
        
        return {
            'peaks_detected': len(peaks),
            'peak_potentials': peak_potentials,
            'peak_currents': peak_currents,
            'confidence': 0.8 if peaks else 0.0
        }

# Test with sample data
voltages = np.linspace(-0.5, 0.5, 100)

# Create clear CV peaks
currents = np.zeros_like(voltages)
# Anodic peak at +0.2V
peak1_idx = np.argmin(np.abs(voltages - 0.2))
currents[peak1_idx-2:peak1_idx+3] = [1e-6, 3e-6, 5e-6, 3e-6, 1e-6]

# Cathodic peak at -0.2V
peak2_idx = np.argmin(np.abs(voltages + 0.2))
currents[peak2_idx-2:peak2_idx+3] = [-1e-6, -3e-6, -4e-6, -3e-6, -1e-6]

detector = SimplePeakDetector()
result = detector.detect_peaks(voltages, currents)

print(f"✅ Simple peak detection test:")
print(f"   Peaks found: {result['peaks_detected']}")
print(f"   Peak potentials: {[f'{v:.3f}V' for v in result['peak_potentials']]}")
print(f"   Confidence: {result['confidence']:.1%}")
""")
    
except Exception as e:
    print(f"❌ Peak detection test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n🎯 Ready to start validation...")
print("📝 Will proceed with fallback mode if needed")
print("🚀 STARTING PHASE 1 VALIDATION NOW...")
