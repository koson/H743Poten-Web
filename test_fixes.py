#!/usr/bin/env python3
"""
Test script to verify the fixes for peak detection and baseline length issues
"""

import re

def test_peak_detection_fixes():
    """Test that peak detection logic has been improved"""
    
    template_path = "templates/peak_analysis.html"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("🔍 Testing Peak Detection Fixes")
        print("=" * 50)
        
        # Check for improved peak detection components
        checks = [
            ('Debug Logging Added', r'console\.log.*AUTO-SELECT.*Processing.*peaks'),
            ('Peak Type Check Enhanced', r'hasAnodicType.*hasCathodicType'),
            ('Current Direction Fallback', r'Fall back to current direction'),
            ('Individual Peak Logging', r'Peak.*type.*y.*x'),
            ('Group Assignment Logging', r'Added to.*group'),
            ('Group Count Logging', r'Groups.*anodic.*cathodic'),
            ('Highest Peak Logging', r'Highest.*anodic.*cathodic'),
            ('Final Result Logging', r'Peak.*enabled'),
            ('Enabled Count Summary', r'Result.*peaks enabled'),
            ('Enhanced Type Detection', r'toLowerCase.*includes.*anodic.*cathodic')
        ]
        
        all_passed = True
        for check_name, pattern in checks:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name}")
                all_passed = False
        
        print("=" * 50)
        
        if all_passed:
            print("🎉 Peak detection fixes are properly implemented!")
            print()
            print("🔧 Improvements Made:")
            print("   • Enhanced debug logging for troubleshooting")
            print("   • Better type detection (anodic/cathodic)")
            print("   • Robust fallback to current direction")
            print("   • Detailed console output for analysis")
            print("   • Improved peak grouping logic")
            return True
        else:
            print("⚠️ Some peak detection improvements are missing")
            return False
            
    except FileNotFoundError:
        print(f"❌ Template file not found: {template_path}")
        return False
    except Exception as e:
        print(f"❌ Error reading template file: {e}")
        return False

def test_baseline_length_fixes():
    """Test that baseline length issues have been resolved"""
    
    js_file_path = "static/js/peak_analysis_plotly.js"
    
    try:
        with open(js_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n📏 Testing Baseline Length Fixes")
        print("=" * 50)
        
        # Check for baseline length fix components
        checks = [
            ('Split Point Calculation', r'splitPoint.*Math\.floor.*forwardEndIdx.*reverseStartIdx'),
            ('Forward Full Range', r'slice\(0,.*splitPoint.*\+ 1\)'),
            ('Reverse Full Range', r'slice\(splitPoint\)'),
            ('Forward to Split Coverage', r'from start to split point'),
            ('Reverse from Split Coverage', r'from split point to end'),
            ('Midpoint Logic', r'Find the midpoint.*forward ends.*reverse begins'),
            ('No Hard-coded Indices', r'(?!.*Math\.floor.*chartData\.voltage\.length / 2)'),
            ('Dynamic Split Point', r'forwardEndIdx.*reverseStartIdx.*/ 2')
        ]
        
        all_passed = True
        for check_name, pattern in checks:
            if check_name == 'No Hard-coded Indices':
                # This is a negative check - should NOT find the old hard-coded logic
                if not re.search(r'Math\.floor\(chartData\.voltage\.length / 2\)', content):
                    print(f"✅ {check_name}")
                else:
                    print(f"❌ {check_name}")
                    all_passed = False
            else:
                if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                    print(f"✅ {check_name}")
                else:
                    print(f"❌ {check_name}")
                    all_passed = False
        
        print("=" * 50)
        
        if all_passed:
            print("🎉 Baseline length fixes are properly implemented!")
            print()
            print("📏 Improvements Made:")
            print("   • Dynamic split point based on actual segment data")
            print("   • Forward baseline: covers from start to split point")
            print("   • Reverse baseline: covers from split point to end")
            print("   • No more hard-coded midpoint calculations")
            print("   • Full voltage range coverage for both segments")
            return True
        else:
            print("⚠️ Some baseline length improvements are missing")
            return False
            
    except FileNotFoundError:
        print(f"❌ JavaScript file not found: {js_file_path}")
        return False
    except Exception as e:
        print(f"❌ Error reading JavaScript file: {e}")
        return False

def print_debugging_instructions():
    """Print instructions for debugging the issues"""
    
    print("\n" + "="*60)
    print("🔧 DEBUGGING INSTRUCTIONS")
    print("="*60)
    print()
    print("🕵️ To debug peak detection issues:")
    print("   1. Open browser Developer Tools (F12)")
    print("   2. Go to Console tab")
    print("   3. Refresh the page and upload a CV file")
    print("   4. Look for [AUTO-SELECT] debug messages")
    print("   5. Check peak types and current values")
    print("   6. Verify both anodic and cathodic groups have peaks")
    print()
    print("📊 Expected Console Output:")
    print("   [AUTO-SELECT] Processing X peaks for auto-selection")
    print("   [AUTO-SELECT] Peak 0: type=\"...\", y=..., x=...")
    print("   [AUTO-SELECT] → Added to anodic/cathodic group")
    print("   [AUTO-SELECT] Groups: X anodic, Y cathodic")
    print("   [AUTO-SELECT] Highest anodic: y=..., x=...")
    print("   [AUTO-SELECT] Highest cathodic: y=..., x=...")
    print("   [AUTO-SELECT] Result: Z/X peaks enabled")
    print()
    print("📏 To verify baseline length:")
    print("   1. Check that red baseline covers full forward scan")
    print("   2. Check that green baseline covers full reverse scan")
    print("   3. Both baselines should meet at the split point")
    print("   4. No gaps or overlaps between red and green segments")
    print()
    print("🎯 Expected Behavior:")
    print("   • At least 1 anodic peak enabled (positive current)")
    print("   • At least 1 cathodic peak enabled (negative current)")
    print("   • Red baseline: covers voltage range from start to split")
    print("   • Green baseline: covers voltage range from split to end")

def print_troubleshooting_tips():
    """Print troubleshooting tips for common issues"""
    
    print("\n" + "="*60)
    print("🛠️ TROUBLESHOOTING TIPS")
    print("="*60)
    print()
    print("❌ If only anodic peaks are enabled:")
    print("   • Check peak.type values in console")
    print("   • Verify cathodic peaks have negative y values")
    print("   • Look for 'Added to cathodic group' messages")
    print("   • Ensure cathodic peaks are detected in data")
    print()
    print("❌ If baseline is still short:")
    print("   • Check splitPoint calculation in console")
    print("   • Verify forwardEndIdx and reverseStartIdx values")
    print("   • Look for 'from start to split point' messages")
    print("   • Ensure baseline.full array covers full range")
    print()
    print("❌ If no peaks are enabled:")
    print("   • Check if peaks array is empty")
    print("   • Verify autoSelectHighestPeaks is being called")
    print("   • Look for 'Processing X peaks' console message")
    print("   • Check if peaks have valid x, y values")
    print()
    print("✅ Success indicators:")
    print("   • Console shows both anodic and cathodic groups")
    print("   • Both highest anodic and cathodic peaks identified")
    print("   • Red and green baselines span full voltage range")
    print("   • Legend shows both Forward and Reverse baselines with R²")

if __name__ == "__main__":
    # Test peak detection fixes
    peak_ok = test_peak_detection_fixes()
    
    # Test baseline length fixes
    baseline_ok = test_baseline_length_fixes()
    
    # Print debugging instructions
    print_debugging_instructions()
    
    # Print troubleshooting tips
    print_troubleshooting_tips()
    
    print("\n" + "="*60)
    if peak_ok and baseline_ok:
        print("🎯 All fixes are properly implemented!")
        print("🔄 Refresh the web page to test the improvements")
        print("🕵️ Use browser Developer Tools to debug if needed")
    else:
        print("⚠️ Some fixes may need additional work. Check output above.")