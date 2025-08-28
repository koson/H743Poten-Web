#!/usr/bin/env python3
"""
Simple API test script to avoid terminal conflicts with running server
"""
import requests
import json
import time

def test_preview_data_api():
    print("Testing /api/workflow/get-preview-data endpoint...")
    
    try:
        # Give server time to fully start if needed
        time.sleep(1)
        
        # Test the API endpoint
        response = requests.get('http://127.0.0.1:8080/api/workflow/get-preview-data')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Data Source: {data.get('data_source', 'unknown')}")
            print(f"File Name: {data.get('file_name', 'unknown')}")
            print(f"Data Points: {data.get('data_points', 0)}")
            print("API call successful!")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Is it running on port 8080?")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_preview_data_api()
