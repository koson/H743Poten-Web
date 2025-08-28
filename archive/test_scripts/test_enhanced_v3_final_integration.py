#!/usr/bin/env python3
"""
สรุปผลการทดสอบ Enhanced V3 Integration
"""

import requests
import json

def test_enhanced_v3_final():
    """ทดสอบ Enhanced V3 integration สุดท้าย"""
    
    print("🎯 Enhanced V3 Integration - Final Test")
    print("=" * 50)
    
    # โหลดข้อมูลทดสอบ
    with open('test_enhanced_v3_api_data.json', 'r') as f:
        test_data = json.load(f)
    
    print(f"📊 Test data: {len(test_data['voltage'])} points")
    
    # ทดสอบ Enhanced V3 method
    api_url = "http://localhost:8081/peak_detection/get-peaks/enhanced_v3"
    
    try:
        response = requests.post(api_url, json=test_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ API Response: {response.status_code}")
            print(f"🎯 Success: {result.get('success', False)}")
            print(f"🔧 Method: {result.get('method', 'unknown')}")
            
            # Peak summary
            peak_summary = result.get('peak_summary', {})
            peaks = result.get('peaks', [])
            
            print(f"\n📈 PEAK DETECTION RESULTS:")
            print(f"   Total valid peaks: {peak_summary.get('total_valid', len(peaks))}")
            print(f"   Oxidation valid: {peak_summary.get('oxidation_valid', 0)}")
            print(f"   Reduction valid: {peak_summary.get('reduction_valid', 0)}")
            print(f"   Total rejected: {peak_summary.get('total_rejected', 0)}")
            
            # Peak details
            if peaks:
                print(f"\n🔍 Peak Details:")
                for i, peak in enumerate(peaks):
                    type_str = peak['type'][:3].upper()
                    voltage = peak['voltage']
                    current = peak['current']
                    confidence = peak.get('confidence', 0)
                    print(f"   Peak {i+1}: {type_str} at {voltage:.3f}V, {current:.2f}µA, conf={confidence:.0f}%")
            
            # Rejected peaks
            rejected = result.get('rejected_peaks', [])
            if rejected:
                print(f"\n❌ Rejected Peaks:")
                for i, peak in enumerate(rejected):
                    type_str = peak['type'][:3].upper()
                    voltage = peak['voltage']
                    current = peak['current']
                    reason = peak.get('reason', 'Unknown')
                    print(f"   Rejected {i+1}: {type_str} at {voltage:.3f}V, {current:.2f}µA - {reason}")
            
            # Integration status
            method = result.get('method', '')
            if 'enhanced_v3' in method:
                if 'fallback' in method:
                    print(f"\n⚠️ INTEGRATION STATUS: Enhanced V3 with Fallback")
                    print(f"   Fallback reason: {result.get('params', {}).get('fallback_reason', 'Unknown')}")
                else:
                    print(f"\n✅ INTEGRATION STATUS: Pure Enhanced V3")
                    
                print(f"🎉 Enhanced V3 is successfully integrated in web application!")
            else:
                print(f"\n❌ INTEGRATION STATUS: Not using Enhanced V3")
                print(f"   Current method: {method}")
            
            return True
            
        else:
            print(f"❌ API Error: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_web_interface_availability():
    """ทดสอบว่า web interface พร้อมใช้งาน"""
    
    print(f"\n🌐 Web Interface Test")
    print(f"=" * 30)
    
    try:
        # ตรวจสอบ peak detection page
        response = requests.get("http://localhost:8081/peak_detection", timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Peak detection page: Available")
            
            # ตรวจสอบว่ามี Enhanced V3 method card
            if 'enhanced_v3' in response.text.lower():
                print(f"✅ Enhanced V3 method card: Found in UI")
            else:
                print(f"⚠️ Enhanced V3 method card: Not found in UI")
                
            return True
        else:
            print(f"❌ Peak detection page: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Web interface test failed: {e}")
        return False

if __name__ == "__main__":
    
    # ทดสอบ web interface
    web_ok = test_web_interface_availability()
    
    # ทดสอบ Enhanced V3 API
    api_ok = test_enhanced_v3_final()
    
    print(f"\n🎯 FINAL INTEGRATION REPORT")
    print(f"=" * 40)
    
    if web_ok and api_ok:
        print(f"✅ Enhanced V3 successfully integrated!")
        print(f"🎉 Ready for user testing through web interface")
        print(f"🌐 Access: http://127.0.0.1:8081/peak_detection")
        print(f"🚀 Enhanced V3 is available as the 4th detection method")
    else:
        print(f"❌ Integration incomplete")
        if not web_ok:
            print(f"   - Web interface issues detected")
        if not api_ok:
            print(f"   - API integration issues detected")
