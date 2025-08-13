"""
AI Dashboard Icon Test - Direct API Test
Tests Font Awesome icons rendering in PyPiPo AI Dashboard
"""

import requests
import time
from bs4 import BeautifulSoup
import re

def test_ai_dashboard_icons():
    """Test AI Dashboard icons loading and rendering"""
    print("🧪 Testing AI Dashboard Font Awesome Icons")
    print("=" * 50)
    
    try:
        # Test main page
        print("📄 Testing main page...")
        response = requests.get("http://localhost:5000/", timeout=10)
        
        if response.status_code == 200:
            print("✅ Main page loaded successfully")
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check Font Awesome CDN
            fa_links = soup.find_all('link', {'href': re.compile(r'font-awesome')})
            print(f"📦 Font Awesome CDN links found: {len(fa_links)}")
            for link in fa_links:
                print(f"   - {link.get('href')}")
            
            # Check AI Dashboard icons
            fa_icons = soup.find_all('i', class_=re.compile(r'fas|far|fab'))
            print(f"🎨 Font Awesome icons found: {len(fa_icons)}")
            
            # Specific AI Dashboard icons
            dashboard_icons = {
                'fa-brain': 'AI Intelligence',
                'fa-mountain': 'Peak Classifier', 
                'fa-flask': 'Concentration Predictor',
                'fa-wave-square': 'Signal Processor'
            }
            
            print("\n🤖 AI Dashboard Component Icons:")
            for icon_class, description in dashboard_icons.items():
                icons = soup.find_all('i', class_=re.compile(icon_class))
                status = "✅" if len(icons) > 0 else "❌"
                print(f"   {status} {icon_class}: {len(icons)} found - {description}")
            
            # Check AI Dashboard CSS
            print("\n🎨 CSS Files:")
            css_links = soup.find_all('link', {'href': re.compile(r'\.css')})
            for link in css_links:
                href = link.get('href', '')
                if 'ai-dashboard' in href:
                    print(f"   ✅ AI Dashboard CSS: {href}")
                elif 'style' in href:
                    print(f"   📄 Style CSS: {href}")
            
            # Test CSS loading
            print("\n🔧 Testing CSS Loading:")
            css_response = requests.get("http://localhost:5000/static/css/ai-dashboard.css", timeout=5)
            if css_response.status_code == 200:
                css_content = css_response.text
                css_size = len(css_content)
                print(f"   ✅ AI Dashboard CSS loaded: {css_size} bytes")
                
                # Check for icon styles
                icon_styles = css_content.count('.ml-component-icon')
                fa_styles = css_content.count('i.fas')
                print(f"   🎯 Icon style rules: {icon_styles} component, {fa_styles} Font Awesome")
            else:
                print(f"   ❌ CSS loading failed: {css_response.status_code}")
                
        else:
            print(f"❌ Main page failed: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_ai_api_endpoints():
    """Test AI API endpoints"""
    print("\n🔗 Testing AI API Endpoints:")
    print("-" * 30)
    
    endpoints = [
        "/api/ai/demo/peaks",
        "/api/ai/demo/full-analysis", 
        "/api/ai/status"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:5000{endpoint}", timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"   {status} {endpoint}: HTTP {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'success' in data:
                        print(f"      📊 Success: {data['success']}")
                    if 'peaks_detected' in data:
                        print(f"      🏔️ Peaks: {data['peaks_detected']}")
                except:
                    print(f"      📄 Response length: {len(response.text)} chars")
                    
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {endpoint}: Request failed - {e}")

if __name__ == "__main__":
    print("🚀 PyPiPo AI Dashboard Icon Test")
    print("🕐 " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    test_ai_dashboard_icons()
    test_ai_api_endpoints()
    
    print("\n" + "=" * 50)
    print("✅ Icon test completed!")
    print("💡 If icons not showing:")
    print("   1. Clear browser cache")
    print("   2. Check browser console for errors")
    print("   3. Verify Font Awesome CDN connectivity")
    print("   4. Test with different browser")
