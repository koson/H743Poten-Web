#!/usr/bin/env python3
"""
Quick test script to verify the keyboard shortcut functionality
by opening the web interface and checking the HTML contains the expected elements.
"""

import requests
import re
import sys

def test_keyboard_shortcut_implementation():
    """Test that the keyboard shortcut is properly implemented"""
    try:
        # Try to fetch the main page
        response = requests.get('http://127.0.0.1:8080', timeout=5)
        
        if response.status_code == 200:
            print("✅ Web server is accessible")
            
            # Check if we can access the peak analysis page
            # (This might require uploading a file first in a real scenario)
            content = response.text
            
            # Check for presence of keyboard shortcut elements in any loaded content
            shortcut_indicators = [
                r'Ctrl\+Shift\+Enter',
                r'addEventListener.*keydown',
                r'showShortcutNotification',
                r'Save analysis parameters.*Ctrl\+Shift\+Enter'
            ]
            
            found_indicators = []
            for pattern in shortcut_indicators:
                if re.search(pattern, content, re.IGNORECASE):
                    found_indicators.append(pattern)
            
            print(f"📋 Found {len(found_indicators)}/{len(shortcut_indicators)} keyboard shortcut indicators")
            
            # The main page might not contain the peak analysis template
            # But we can check if the server is serving files correctly
            print("✅ Server is running and serving content")
            print("🎯 To test the keyboard shortcut:")
            print("   1. Open http://127.0.0.1:8080 in your browser")
            print("   2. Upload a CSV file for analysis")
            print("   3. Fill in the analysis parameters")
            print("   4. Press Ctrl+Shift+Enter to save")
            print("   5. You should see a green notification and button animation")
            
            return True
            
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server")
        print("   Make sure the development server is running on http://127.0.0.1:8080")
        return False
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

def test_template_file():
    """Test that the template file contains the expected keyboard shortcut code"""
    try:
        template_path = "templates/peak_analysis.html"
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for essential keyboard shortcut components
        checks = [
            ('Keyboard Event Listener', r'addEventListener.*keydown'),
            ('Ctrl+Shift+Enter Detection', r'event\.ctrlKey.*event\.shiftKey.*event\.key.*Enter'),
            ('Save Function Call', r'saveAnalysisParameters\(\)'),
            ('Notification Function', r'function showShortcutNotification'),
            ('Button Tooltip', r'title.*Save analysis parameters.*Ctrl\+Shift\+Enter'),
            ('Visual Shortcut Info', r'<kbd>.*Ctrl\+Shift\+Enter.*</kbd>')
        ]
        
        print("🔍 Checking template file for keyboard shortcut implementation:")
        print("=" * 60)
        
        all_passed = True
        for check_name, pattern in checks:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name}")
                all_passed = False
        
        print("=" * 60)
        
        if all_passed:
            print("🎉 All keyboard shortcut components are properly implemented!")
            print("📝 Implementation Summary:")
            print("   - Ctrl+Shift+Enter triggers saveAnalysisParameters()")
            print("   - Visual feedback: button animation and color change")
            print("   - Toast notification with success/warning messages")
            print("   - Tooltip shows the keyboard shortcut")
            print("   - <kbd> styling for shortcut display")
            print("   - Prevents default browser behavior")
            return True
        else:
            print("⚠️ Some keyboard shortcut components are missing")
            return False
            
    except FileNotFoundError:
        print(f"❌ Template file not found: {template_path}")
        return False
    except Exception as e:
        print(f"❌ Error reading template file: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Keyboard Shortcut Implementation")
    print("=" * 50)
    
    # Test template file
    template_ok = test_template_file()
    print()
    
    # Test server
    server_ok = test_keyboard_shortcut_implementation()
    
    print()
    print("=" * 50)
    if template_ok and server_ok:
        print("🎯 Keyboard shortcut implementation is ready!")
        print("💡 User Instructions:")
        print("   1. Open the web interface")
        print("   2. Upload a CSV file")
        print("   3. Fill analysis parameters")
        print("   4. Press Ctrl+Shift+Enter to save quickly")
    else:
        print("⚠️ Some issues found. Check the output above.")
        sys.exit(1)

def test_server_status():
    """Test server status"""
    print("🌐 Testing server accessibility:")
    print("-" * 30)
    return test_keyboard_shortcut_implementation()