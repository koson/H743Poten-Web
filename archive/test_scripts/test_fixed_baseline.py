#!/usr/bin/env python3
"""
Test baseline detection after fixing unit conversion issue
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import sqlite3
import json
import numpy as np
from utils.baseline_detector import BaselineDetector

def test_baseline_with_real_data():
    """Test baseline detection with real measurement data"""
    print("🧪 Testing Baseline Detection with Real Data (Fixed Units)")
    print("=" * 60)
    
    # Connect to database
    db_path = "parameter_log.db"
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get latest CV measurement
    cursor.execute("""
        SELECT id, filename, data 
        FROM measurements 
        WHERE data LIKE '%"method":"CV"%' 
        ORDER BY timestamp DESC 
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    
    if not result:
        print("❌ No CV measurements found")
        conn.close()
        return
    
    measurement_id, filename, data_json = result
    print(f"📂 Testing measurement ID: {measurement_id}")
    print(f"📄 Filename: {filename}")
    
    # Parse measurement data
    data = json.loads(data_json)
    voltage = data.get('voltage', [])
    current = data.get('current', [])
    
    if not voltage or not current:
        print("❌ No voltage/current data found")
        conn.close()
        return
    
    print(f"📊 Data points: {len(voltage)}")
    print(f"🔋 Voltage range: {min(voltage):.3f} to {max(voltage):.3f} V")
    print(f"⚡ Current range: {min(current):.3f} to {max(current):.3f} µA")
    print(f"📏 Current magnitude: {max(abs(min(current)), abs(max(current))):.3f} µA")
    
    # Check if current values are in reasonable µA range
    current_magnitude = max(abs(min(current)), abs(max(current)))
    if current_magnitude < 0.1:
        print("⚠️  WARNING: Current values are very small (< 0.1 µA)")
        print("    This suggests possible unit conversion issues")
    elif current_magnitude < 1e-3:
        print("❌ CRITICAL: Current values are extremely small (< 0.001 µA)")
        print("    Unit conversion problem detected!")
        conn.close()
        return
    
    # Test baseline detection
    print("\n🔍 Testing Enhanced Baseline Detector V2.1...")
    detector = BaselineDetector()
    
    try:
        baseline_result = detector.detect_baseline(
            np.array(voltage), 
            np.array(current),
            mode='auto',
            measurement_type='CV'
        )
        
        if baseline_result and baseline_result.get('success'):
            print("✅ Baseline detection successful!")
            print(f"   Algorithm: {baseline_result.get('algorithm', 'Unknown')}")
            print(f"   Confidence: {baseline_result.get('confidence', 0):.3f}")
            
            baseline_points = baseline_result.get('baseline_points', [])
            if baseline_points:
                baseline_voltages = [p[0] for p in baseline_points]
                baseline_currents = [p[1] for p in baseline_points]
                print(f"   Baseline range: {min(baseline_voltages):.3f} to {max(baseline_voltages):.3f} V")
                print(f"   Baseline current: {min(baseline_currents):.3f} to {max(baseline_currents):.3f} µA")
            
            # Check baseline quality
            quality = baseline_result.get('quality_metrics', {})
            if quality:
                print("📈 Quality metrics:")
                for metric, value in quality.items():
                    if isinstance(value, (int, float)):
                        print(f"   {metric}: {value:.4f}")
                    else:
                        print(f"   {metric}: {value}")
        else:
            print("❌ Baseline detection failed!")
            error_msg = baseline_result.get('error', 'Unknown error') if baseline_result else 'No result returned'
            print(f"   Error: {error_msg}")
            
    except Exception as e:
        print(f"❌ Exception during baseline detection: {str(e)}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("🏁 Test completed")

if __name__ == "__main__":
    test_baseline_with_real_data()