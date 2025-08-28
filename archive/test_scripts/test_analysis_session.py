#!/usr/bin/env python3
"""
Test analysis session creation and routing
"""

import requests
import json
import sys

def test_analysis_session():
    """Test creating analysis session and accessing route"""
    
    base_url = "http://127.0.0.1:8080"
    
    # Test session creation
    session_data = {
        "peaks": [
            [
                {"voltage": 0.2, "current": 5.1, "type": "oxidation", "confidence": 85},
                {"voltage": -0.1, "current": -2.3, "type": "reduction", "confidence": 92}
            ]
        ],
        "data": [
            {
                "voltage": [-0.4, -0.2, 0.0, 0.2, 0.4],
                "current": [-2.1, -2.3, 0.5, 5.1, 3.2],
                "filename": "test_file.csv"
            }
        ],
        "method": "enhanced_v4_improved",
        "methodName": "Enhanced V4 Improved"
    }
    
    try:
        # Create session
        print("🧪 Creating analysis session...")
        response = requests.post(
            f"{base_url}/peak_detection/create_analysis_session",
            json=session_data,
            timeout=10
        )
        
        print(f"Session creation status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            session_id = result.get('session_id')
            print(f"✅ Session created: {session_id}")
            
            # Test accessing the route
            print(f"🧪 Testing route access...")
            route_response = requests.get(
                f"{base_url}/peak_detection/peak_analysis/{session_id}",
                timeout=10
            )
            
            print(f"Route access status: {route_response.status_code}")
            
            if route_response.status_code == 200:
                print("✅ Route accessible, returning HTML content")
                return True
            else:
                print(f"❌ Route failed: {route_response.text}")
                return False
                
        else:
            print(f"❌ Session creation failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Analysis Session Creation and Route Access...")
    success = test_analysis_session()
    sys.exit(0 if success else 1)
