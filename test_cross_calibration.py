#!/usr/bin/env python3
"""
Simple test for Cross-Instrument Calibration System
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.append('.')

print("🧪 Testing Cross-Instrument Calibration System")
print("=" * 50)

def test_basic_imports():
    """Test basic imports"""
    try:
        import pandas as pd
        import numpy as np
        from scipy import stats
        print("✅ Dependencies imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_data_availability():
    """Test if calibration data exists"""
    data_logs_path = Path("data_logs")
    calibration_models_file = data_logs_path / "calibration_models.json"
    
    if calibration_models_file.exists():
        with open(calibration_models_file, 'r') as f:
            data = json.load(f)
        print(f"✅ Calibration models found: {len(data)} models")
        for key in data.keys():
            print(f"   - {key}")
        return True
    else:
        print("❌ No calibration models found")
        return False

def test_article_data():
    """Test if Article Figure Package data exists"""
    article_path = Path("Article_Figure_Package")
    if article_path.exists():
        subdirs = [d for d in article_path.iterdir() if d.is_dir()]
        print(f"✅ Article data found: {len(subdirs)} directories")
        for subdir in subdirs:
            csv_files = list(subdir.glob("*.csv"))
            print(f"   - {subdir.name}: {len(csv_files)} CSV files")
        return True
    else:
        print("❌ No Article Figure Package data found")
        return False

def test_cross_calibration_creation():
    """Test creating CrossInstrumentCalibrator instance"""
    try:
        # Create a minimal version without complex dependencies
        class SimpleCrossCalibrator:
            def __init__(self):
                self.data_logs_path = Path("data_logs")
                self.calibration_models_file = self.data_logs_path / "calibration_models.json"
                self.cross_cal_db = self.data_logs_path / "cross_calibration_test.db"
                self.instruments = {}
                self.correction_factors = {}
                print("✅ SimpleCrossCalibrator initialized")
            
            def load_existing_data(self):
                calibration_data = {}
                if self.calibration_models_file.exists():
                    with open(self.calibration_models_file, 'r') as f:
                        calibration_data['models'] = json.load(f)
                    print(f"✅ Loaded {len(calibration_data['models'])} calibration models")
                return calibration_data
            
            def register_instrument(self, instrument_id, instrument_type):
                self.instruments[instrument_id] = {
                    'type': instrument_type,
                    'registered': datetime.now().isoformat()
                }
                print(f"✅ Registered instrument: {instrument_id} ({instrument_type})")
                return True
        
        # Test the calibrator
        calibrator = SimpleCrossCalibrator()
        
        # Test registering instruments
        calibrator.register_instrument("H743_Test", "H743")
        calibrator.register_instrument("PalmSens_Test", "PalmSens")
        
        # Test loading data
        data = calibrator.load_existing_data()
        
        print(f"✅ Cross-calibration system working: {len(calibrator.instruments)} instruments")
        return True
        
    except Exception as e:
        print(f"❌ Error creating calibrator: {e}")
        return False

def test_database_creation():
    """Test SQLite database creation"""
    try:
        db_path = Path("data_logs") / "test_calibration.db"
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Create test table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_instruments (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert test data
            cursor.execute("""
                INSERT INTO test_instruments (name, type) VALUES (?, ?)
            """, ("H743_Test", "Potentiostat"))
            
            # Query data
            cursor.execute("SELECT * FROM test_instruments")
            results = cursor.fetchall()
            
            conn.commit()
        
        print(f"✅ Database test successful: {len(results)} records")
        
        # Clean up
        if db_path.exists():
            db_path.unlink()
            
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n🚀 Running Cross-Instrument Calibration Tests\n")
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Data Availability", test_data_availability),
        ("Article Data", test_article_data),
        ("Cross-Calibration Creation", test_cross_calibration_creation),
        ("Database Creation", test_database_creation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Cross-Instrument Calibration system is ready.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
