#!/usr/bin/env python3
"""
Demo script to understand peak enable/disable synchronization issue
Creates a simple test scenario to investigate the problem
"""

def analyze_peak_sync_issue():
    """Analyze the peak enable/disable synchronization issue"""
    print("🔍 Analyzing Peak Enable/Disable Synchronization Issue")
    print("=" * 60)
    
    print("📝 Problem Description:")
    print("   User reported: 'Red และ Ox ในฝั่ง reverse ถูก disable'")
    print("   'แต่เมื่อ enable จุด Red พบว่า Ox ตัวล่างจะถูก enable ตามด้วย'") 
    print("   'แต่ถ้า disable Red มันจะไม่ตามอีก (ตามเฉพาะ enable ครั้งแรก)'")
    
    print("\n🎯 Expected Behavior:")
    print("   - Red และ Ox peaks ควร sync กัน (enable/disable together)")
    print("   - เมื่อ enable Red → Ox ควร enable ด้วย")
    print("   - เมื่อ disable Red → Ox ควร disable ด้วย")
    print("   - ควรมี bidirectional sync (Red ↔ Ox)")
    
    print("\n🐛 Current Issue:")
    print("   - การ sync ทำงานเฉพาะ enable ครั้งแรก")
    print("   - การ disable ไม่ sync")
    print("   - อาจเป็น one-way sync แทน bidirectional")
    
    print("\n🔧 Possible Causes:")
    print("   1. Event handler ที่ไม่ครบถ้วน")
    print("   2. Logic ที่ check state ไม่ถูกต้อง") 
    print("   3. การ update UI ที่ไม่ sync")
    print("   4. Peak grouping logic ที่มีปัญหา")
    
    print("\n📂 Code Locations to Check:")
    print("   - templates/peak_analysis.html (UI logic)")
    print("   - static/js/peak_analysis_plotly.js (event handling)")
    print("   - Auto peak selection functions")
    print("   - Checkbox change event handlers")
    
    print("\n🧪 Test Scenarios:")
    print("   1. Load CV data with clear Red และ Ox peaks")
    print("   2. Enable auto-peak selection")
    print("   3. Manually toggle Red peak → check if Ox follows")
    print("   4. Disable Red peak → check if Ox disables")
    print("   5. Try reverse: toggle Ox → check if Red follows")
    
    return analyze_js_code()

def analyze_js_code():
    """Analyze JavaScript code for sync issues"""
    print("\n🔍 Analyzing JavaScript Code...")
    
    js_file = "static/js/peak_analysis_plotly.js"
    try:
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ File not found: {js_file}")
        return False
    
    # Look for event handling code
    sync_patterns = [
        "checkbox.*change",
        "dispatchEvent.*change",
        "enabled.*toggle",
        "peak.*sync",
        "Red.*Ox",
        "Ox.*Red"
    ]
    
    print("📝 Searching for sync-related code:")
    
    found_patterns = []
    for pattern in sync_patterns:
        if pattern.lower().replace(".*", "") in content.lower():
            found_patterns.append(pattern)
    
    if found_patterns:
        print("✅ Found potential sync-related code:")
        for pattern in found_patterns:
            print(f"   - {pattern}")
    else:
        print("❌ No obvious sync code found")
    
    # Look for the specific checkbox logic
    if "checkbox.checked" in content:
        print("✅ Found checkbox state management")
    
    if "dispatchEvent" in content:
        print("✅ Found event dispatching")
    
    # Check for auto-selection logic
    if "autoSelectHighestPeaks" in content:
        print("✅ Found auto-selection function")
    
    print("\n💡 Recommended Investigation:")
    print("   1. Add console.log to track peak enable/disable events")
    print("   2. Check if event handlers are properly bound")
    print("   3. Verify bidirectional sync logic")
    print("   4. Test with both manual and automatic peak selection")
    
    return True

def create_debug_instructions():
    """Create debugging instructions for the user"""
    print("\n🛠️  Debug Instructions:")
    print("=" * 30)
    
    print("1. Open Developer Tools (F12)")
    print("2. Go to Console tab")
    print("3. Load CV data and detect peaks")
    print("4. Try to manually toggle Red/Ox peaks")
    print("5. Watch console for debug messages")
    print("6. Check for any JavaScript errors")
    
    print("\n📋 Debug Checklist:")
    print("   □ Are Red and Ox peaks properly grouped?")
    print("   □ Do checkbox events fire correctly?")
    print("   □ Is the sync logic bidirectional?")
    print("   □ Are UI updates reflected in data structures?")
    print("   □ Does auto-selection interfere with manual selection?")

if __name__ == "__main__":
    success = analyze_peak_sync_issue()
    create_debug_instructions()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Analysis complete. Check browser console for detailed debugging.")
    else:
        print("❌ Analysis incomplete. Check file paths and try again.")
    
    print("\n🔗 Next Steps:")
    print("   1. Open peak_analysis page in browser")
    print("   2. Test Red/Ox peak synchronization")
    print("   3. Check console for debug messages")
    print("   4. Identify the exact sync issue")
    print("   5. Implement proper bidirectional sync")