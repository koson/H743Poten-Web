#!/usr/bin/env python3
"""Test script to verify AI analysis imports"""

try:
    from src.services.ai_analysis_service import ElectrochemicalAnalyzer
    print("✓ AI Analysis Service imported successfully")
    
    from src.routes.ai_analysis_routes import ai_analysis_bp
    print("✓ AI Analysis Routes imported successfully")
    
    # Test basic functionality
    analyzer = ElectrochemicalAnalyzer()
    print("✓ ElectrochemicalAnalyzer instantiated successfully")
    
    print("\n✅ All AI analysis components imported and initialized successfully!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
