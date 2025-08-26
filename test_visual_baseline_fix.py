#!/usr/bin/env python3
"""
Simple test script to verify baseline separation fix visually
Opens the peak analysis page to check if baseline segments are properly separated
"""

import webbrowser
import time
import subprocess
import sys

def test_visual_baseline_separation():
    """Open browser to test baseline separation visually"""
    print("🧪 Testing Baseline Separation Fix - Visual Test")
    print("=" * 50)
    
    url = "http://127.0.0.1:8083/peak_analysis"
    
    print("🌐 Opening peak analysis page in browser...")
    print(f"   URL: {url}")
    
    try:
        webbrowser.open(url)
        print("✅ Browser opened")
    except Exception as e:
        print(f"❌ Failed to open browser: {e}")
        return False
    
    print("\n📋 Manual Test Instructions:")
    print("1. โหลดไฟล์ CV data ใดก็ได้")
    print("2. เลือก peak detection method และ detect peaks")
    print("3. ดูเส้น baseline ที่แสดงผล:")
    print("   - เส้นสีแดง (Forward) ควรไม่เชื่อมกับเส้นสีเขียว (Reverse)")
    print("   - แต่ละเส้นควรแยกออกจากกันชัดเจน")
    print("   - R² values ควรแสดงใน legend")
    
    print("\n✅ Baseline Separation Fix Applied:")
    print("   - ใช้ forwardEndIdx + 1 สำหรับ forward segment")  
    print("   - ใช้ reverseStartIdx สำหรับ reverse segment")
    print("   - ไม่ใช้ splitPoint ที่ทำให้ overlap")
    
    print("\n🔍 Visual Check List:")
    print("   □ เส้นสีแดง (Forward) ยาวไปถึงจุดสิ้นสุดที่เหมาะสม")
    print("   □ เส้นสีเขียว (Reverse) เริ่มจากจุดเริ่มต้นที่เหมาะสม")
    print("   □ ไม่มีการเชื่อมต่อระหว่างเส้นสองสี")
    print("   □ มีช่องว่างหรือแยกชัดเจนระหว่าง forward และ reverse")
    
    return True

if __name__ == "__main__":
    test_visual_baseline_separation()
    
    print("\n💡 Note: This is a visual test.")
    print("   Check the browser to confirm baseline segments are properly separated.")
    print("   If segments still appear connected, additional debugging may be needed.")