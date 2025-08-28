#!/usr/bin/env python3
"""
Phase 2 Runner - Cross-Instrument Calibration
H743Poten Research Team
"""

import sys
import os
from pathlib import Path

# Add validation_data to path
current_dir = Path(__file__).parent
validation_dir = current_dir / "validation_data"
sys.path.insert(0, str(validation_dir))

# Change working directory to validation_data
os.chdir(validation_dir)

print("🎯 H743Poten Phase 2 Launcher")
print("🚀 Starting Cross-Instrument Calibration...")
print("=" * 50)

try:
    # Import and run the calibration
    from cross_instrument_calibration import run_phase2_calibration
    
    success = run_phase2_calibration()
    
    if success:
        print("\n🎉 PHASE 2 COMPLETED SUCCESSFULLY!")
    else:
        print("\n❌ PHASE 2 FAILED!")
        
except Exception as e:
    print(f"❌ Error running Phase 2: {e}")
    import traceback
    traceback.print_exc()
