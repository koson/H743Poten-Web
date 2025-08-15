#!/usr/bin/env python3
"""
Quick AI System Test
"""

import sys
import os
import numpy as np

# Add src to path
sys.path.insert(0, 'src')

def main():
    print("🧪 Quick AI System Test")
    print("=" * 30)
    
    # Test 1: Basic imports
    print("Test 1: Importing modules...")
    try:
        from ai.ml_models.signal_processor import SignalProcessor
        print("  ✅ SignalProcessor")
    except Exception as e:
        print(f"  ❌ SignalProcessor: {e}")
        return False
    
    try:
        from ai.ml_models.electrochemical_intelligence import ElectrochemicalIntelligence
        print("  ✅ ElectrochemicalIntelligence")  
    except Exception as e:
        print(f"  ❌ ElectrochemicalIntelligence: {e}")
        return False
    
    # Test 2: Create instances
    print("\nTest 2: Creating instances...")
    try:
        sp = SignalProcessor()
        print("  ✅ SignalProcessor instance created")
    except Exception as e:
        print(f"  ❌ SignalProcessor instance: {e}")
        return False
    
    try:
        ei = ElectrochemicalIntelligence()
        print("  ✅ ElectrochemicalIntelligence instance created")
    except Exception as e:
        print(f"  ❌ ElectrochemicalIntelligence instance: {e}")
        return False
    
    # Test 3: Basic functionality
    print("\nTest 3: Basic functionality...")
    try:
        # Generate test data
        voltage = np.linspace(-0.5, 0.5, 100)
        current = 1e-6 * np.exp(-((voltage - 0.1) / 0.05) ** 2) + np.random.normal(0, 1e-8, 100)
        
        # Test signal quality
        quality = sp.assess_signal_quality(voltage, current)
        print(f"  ✅ Signal quality: {quality.quality_score:.2f}")
        
        # Test filtering
        filtered = sp.apply_filtering(voltage, current, 'auto')
        print(f"  ✅ Filtering: {filtered.filter_method}")
        
    except Exception as e:
        print(f"  ❌ Basic functionality: {e}")
        return False
    
    print("\n🎉 All tests passed!")
    return True

if __name__ == "__main__":
    main()
