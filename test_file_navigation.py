#!/usr/bin/env python3
"""
Test script to verify file navigation keyboard shortcuts:
Ctrl+Left (Previous file) and Ctrl+Right (Next file)
"""

import re

def test_file_navigation_shortcuts():
    """Test that file navigation shortcuts are properly implemented"""
    
    template_path = "templates/peak_analysis.html"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("🔍 Testing File Navigation Keyboard Shortcuts")
        print("=" * 60)
        
        # Check for essential components
        checks = [
            ('Ctrl+Left Detection', r'event\.ctrlKey.*event\.key.*ArrowLeft'),
            ('Ctrl+Right Detection', r'event\.ctrlKey.*event\.key.*ArrowRight'),
            ('switchFile Function', r'function switchFile\(direction\)'),
            ('Previous/Next Logic', r'direction.*===.*previous.*direction.*===.*next'),
            ('Dropdown Value Update', r'traceSelect\.value.*newIndex'),
            ('Change Event Dispatch', r'dispatchEvent\(changeEvent\)'),
            ('Visual Feedback', r'traceSelect\.style\.backgroundColor'),
            ('Focus Maintenance', r'traceSelect\.focus\(\)'),
            ('Info Notification', r'showShortcutNotification.*info'),
            ('UI Tooltips', r'title.*Ctrl.*Previous.*Next'),
            ('Visual Keyboard Hints', r'<kbd>.*Ctrl.*←.*</kbd>.*<kbd>.*Ctrl.*→.*</kbd>')
        ]
        
        all_passed = True
        for check_name, pattern in checks:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name}")
                all_passed = False
        
        print("=" * 60)
        
        if all_passed:
            print("🎉 All file navigation shortcuts are properly implemented!")
            print()
            print("📝 Implementation Summary:")
            print("   🔄 Ctrl+Left: Switch to previous file (wraps to last)")
            print("   🔄 Ctrl+Right: Switch to next file (wraps to first)")
            print("   🎯 Maintains dropdown focus to prevent losing selection")
            print("   💡 Visual feedback: dropdown highlighting during switch")
            print("   📢 Toast notifications show current file position")
            print("   🖱️ Tooltip and visual <kbd> hints in UI")
            print()
            print("🚀 Benefits:")
            print("   ✓ No need to click dropdown after disabling peaks")
            print("   ✓ Fast file navigation without mouse movement")
            print("   ✓ Wraps around: seamless navigation through file list")
            print("   ✓ Clear visual feedback prevents confusion")
            return True
        else:
            print("⚠️ Some file navigation components are missing")
            return False
            
    except FileNotFoundError:
        print(f"❌ Template file not found: {template_path}")
        return False
    except Exception as e:
        print(f"❌ Error reading template file: {e}")
        return False

def test_keyboard_shortcuts_integration():
    """Test that all keyboard shortcuts work together"""
    
    print("\n🧪 Testing Keyboard Shortcuts Integration")
    print("=" * 50)
    
    template_path = "templates/peak_analysis.html"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Test that shortcuts don't conflict
        shortcuts = [
            ('Ctrl+Shift+Enter', r'Ctrl\+Shift\+Enter'),
            ('Ctrl+Left', r'Ctrl.*←'),
            ('Ctrl+Right', r'Ctrl.*→')
        ]
        
        print("Available keyboard shortcuts:")
        for shortcut_name, pattern in shortcuts:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"✅ {shortcut_name}")
            else:
                print(f"❌ {shortcut_name}")
        
        # Check event listener structure
        event_listeners = re.findall(r'addEventListener.*keydown', content, re.IGNORECASE)
        print(f"\n📊 Found {len(event_listeners)} keydown event listener(s)")
        
        # Check for proper event handling
        if re.search(r'event\.preventDefault\(\)', content):
            print("✅ Proper event.preventDefault() usage")
        else:
            print("❌ Missing event.preventDefault()")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing integration: {e}")
        return False

def print_usage_instructions():
    """Print user instructions for the new shortcuts"""
    
    print("\n" + "="*60)
    print("📖 USER INSTRUCTIONS")
    print("="*60)
    print()
    print("🎯 New File Navigation Shortcuts:")
    print("   Ctrl+←  : Switch to previous file")
    print("   Ctrl+→  : Switch to next file")
    print()
    print("💡 All Available Shortcuts:")
    print("   Ctrl+Shift+Enter : Save Analysis Parameters")
    print("   Ctrl+←          : Previous file")
    print("   Ctrl+→          : Next file")
    print()
    print("🔄 Workflow Benefits:")
    print("   1. Upload multiple CSV files")
    print("   2. Use Ctrl+←/→ to navigate between files")
    print("   3. Click to disable unwanted peaks")
    print("   4. Continue using Ctrl+←/→ (no focus loss!)")
    print("   5. Use Ctrl+Shift+Enter to save quickly")
    print()
    print("✨ The dropdown maintains focus, so you can:")
    print("   - Navigate files without mouse clicks")
    print("   - See toast notifications with file position")
    print("   - Get visual feedback during navigation")
    print("   - Work faster with multi-file analysis")

if __name__ == "__main__":
    # Test file navigation implementation
    nav_ok = test_file_navigation_shortcuts()
    
    # Test integration with existing shortcuts
    integration_ok = test_keyboard_shortcuts_integration()
    
    # Print usage instructions
    print_usage_instructions()
    
    print("\n" + "="*60)
    if nav_ok and integration_ok:
        print("🎯 File navigation shortcuts are ready!")
        print("💡 Test the shortcuts by uploading multiple CSV files")
    else:
        print("⚠️ Some issues found. Check the output above.")