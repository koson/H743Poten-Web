#!/usr/bin/env python3
"""
Test script to verify imports work correctly
"""

import os
import sys

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

def test_imports():
    """Test that all imports work correctly"""
    try:
        print("Testing imports...")
        
        # Test config import
        from config.settings import Config
        print("✓ Config imported successfully")
        
        # Test hardware imports
        from hardware.scpi_handler import SCPIHandler
        print("✓ SCPIHandler imported successfully")
        
        from hardware.mock_scpi_handler import MockSCPIHandler
        print("✓ MockSCPIHandler imported successfully")
        
        # Test services imports
        from services.measurement_service import MeasurementService
        print("✓ MeasurementService imported successfully")
        
        from services.data_service import DataService
        print("✓ DataService imported successfully")
        
        # Test main app import
        from app import create_app
        print("✓ create_app imported successfully")
        
        # Test creating app
        app = create_app()
        print("✓ App created successfully")
        
        print("\n🎉 All imports working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

if __name__ == "__main__":
    test_imports()
