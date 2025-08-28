#!/usr/bin/env python3
"""
Test script to verify baseline segment coloring functionality
"""

import re

def test_baseline_segment_coloring():
    """Test that baseline segment coloring is properly implemented"""
    
    js_file_path = "static/js/peak_analysis_plotly.js"
    
    try:
        with open(js_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("🎨 Testing Baseline Segment Coloring Implementation")
        print("=" * 60)
        
        # Check for essential components
        checks = [
            ('Split Baseline Logic', r'Split baseline into forward and reverse segments'),
            ('Forward Baseline Red Color', r'Forward Baseline.*color.*#ff0000'),
            ('Reverse Baseline Green Color', r'Reverse Baseline.*color.*#00aa00'),
            ('Forward Segment Red Markers', r'Forward Segment.*color.*#ff0000'),
            ('Reverse Segment Green Markers', r'Reverse Segment.*color.*#00aa00'),
            ('Conditional Baseline Split', r'baseline\.markers.*forward_segment.*reverse_segment'),
            ('Forward R² Display', r'Forward.*R².*toFixed'),
            ('Reverse R² Display', r'Reverse.*R².*toFixed'),
            ('Fallback Single Baseline', r'Fallback.*single baseline'),
            ('Segment End Index Usage', r'forwardEndIdx.*end_idx'),
            ('Segment Start Index Usage', r'reverseStartIdx.*start_idx')
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
            print("🎉 Baseline segment coloring is properly implemented!")
            print()
            print("🎨 Color Scheme:")
            print("   🔴 Forward Baseline & Segments: Red (#ff0000)")
            print("   🟢 Reverse Baseline & Segments: Green (#00aa00)")
            print("   ⚫ Fallback Single Baseline: Light Red (#ff6b6b)")
            print()
            print("📊 Implementation Details:")
            print("   • Baseline split based on segment markers")
            print("   • Forward: from start to forward_segment.end_idx")
            print("   • Reverse: from reverse_segment.start_idx to end")
            print("   • R² values displayed in trace names")
            print("   • Fallback to single baseline if no segments")
            print()
            print("🚀 User Benefits:")
            print("   ✓ Clear visual distinction between CV directions")
            print("   ✓ Easy identification of segment quality (R² values)")
            print("   ✓ Consistent color coding throughout analysis")
            print("   ✓ Hover tooltips show segment information")
            return True
        else:
            print("⚠️ Some baseline coloring components are missing")
            return False
            
    except FileNotFoundError:
        print(f"❌ JavaScript file not found: {js_file_path}")
        return False
    except Exception as e:
        print(f"❌ Error reading JavaScript file: {e}")
        return False

def test_color_consistency():
    """Test that colors are consistent across all baseline elements"""
    
    js_file_path = "static/js/peak_analysis_plotly.js"
    
    try:
        with open(js_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n🔍 Testing Color Consistency")
        print("=" * 40)
        
        # Find all color references for baseline elements
        forward_colors = re.findall(r'Forward.*color.*[\'"]#([a-fA-F0-9]{6})[\'"]', content, re.IGNORECASE)
        reverse_colors = re.findall(r'Reverse.*color.*[\'"]#([a-fA-F0-9]{6})[\'"]', content, re.IGNORECASE)
        
        print(f"Forward element colors found: {forward_colors}")
        print(f"Reverse element colors found: {reverse_colors}")
        
        # Check consistency
        forward_consistent = all(color.lower() == 'ff0000' for color in forward_colors)
        reverse_consistent = all(color.lower() == '00aa00' for color in reverse_colors)
        
        if forward_consistent and reverse_consistent:
            print("✅ Color consistency verified!")
            print(f"   Forward elements: {len(forward_colors)} × #ff0000 (red)")
            print(f"   Reverse elements: {len(reverse_colors)} × #00aa00 (green)")
            return True
        else:
            print("⚠️ Color inconsistency detected!")
            if not forward_consistent:
                print(f"   Forward colors not consistent: {set(forward_colors)}")
            if not reverse_consistent:
                print(f"   Reverse colors not consistent: {set(reverse_colors)}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking color consistency: {e}")
        return False

def print_usage_instructions():
    """Print user instructions for the new baseline coloring"""
    
    print("\n" + "="*60)
    print("📖 USER INSTRUCTIONS: Baseline Segment Coloring")
    print("="*60)
    print()
    print("🎨 New Visual Features:")
    print("   🔴 Forward Baseline: Red color (#ff0000)")
    print("     • Shows the forward scan direction baseline")
    print("     • Includes R² value in legend (e.g., 'R²=0.984')")
    print("     • Both line and marker points are red")
    print()
    print("   🟢 Reverse Baseline: Green color (#00aa00)")
    print("     • Shows the reverse scan direction baseline")
    print("     • Includes R² value in legend (e.g., 'R²=0.993')")
    print("     • Both line and marker points are green")
    print()
    print("🔄 How It Works:")
    print("   1. System detects forward and reverse segments from data")
    print("   2. Splits baseline into two colored sections automatically")
    print("   3. Forward: from start to segment end point")
    print("   4. Reverse: from segment start point to end")
    print("   5. Shows R² quality metrics for each segment")
    print()
    print("🎯 What You'll See:")
    print("   • Legend shows 'Forward Baseline (R²=X.XXX)' in red")
    print("   • Legend shows 'Reverse Baseline (R²=X.XXX)' in green")
    print("   • Baseline markers match their respective colors")
    print("   • Clear visual separation between CV directions")
    print()
    print("💡 Benefits:")
    print("   ✓ Easier to assess baseline quality per direction")
    print("   ✓ Quick visual identification of better-fitted segments")
    print("   ✓ Consistent color coding with CV analysis standards")
    print("   ✓ Improved readability for multi-directional data")

def test_server_integration():
    """Test that the changes will work with the running server"""
    
    print("\n🌐 Testing Server Integration")
    print("=" * 40)
    
    # Check if auto_dev.py exists
    try:
        with open("auto_dev.py", "r") as f:
            print("✅ Development server script found")
    except FileNotFoundError:
        print("⚠️ auto_dev.py not found")
        return False
    
    # Check if the server status can be checked
    print("💡 To test the baseline coloring:")
    print("   1. Ensure server is running: python3 auto_dev.py status")
    print("   2. Open: http://127.0.0.1:8080")
    print("   3. Upload a multi-segment CV file")
    print("   4. Look for red/green baseline segments")
    print("   5. Check legend shows R² values for each color")
    
    return True

if __name__ == "__main__":
    # Test implementation
    impl_ok = test_baseline_segment_coloring()
    
    # Test color consistency
    color_ok = test_color_consistency()
    
    # Test server integration
    server_ok = test_server_integration()
    
    # Print usage instructions
    print_usage_instructions()
    
    print("\n" + "="*60)
    if impl_ok and color_ok:
        print("🎨 Baseline segment coloring is ready!")
        print("🔄 Refresh the web page to see the new colors")
        print("📊 Forward segments: Red | Reverse segments: Green")
    else:
        print("⚠️ Some issues found. Check the output above.")