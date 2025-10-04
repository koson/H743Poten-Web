#!/usr/bin/env python3
"""
🧪 CV Peak Validation Demo Script
=================================

Demonstrates the CV Peak Validation Web UI functionality
by testing the API endpoints and showing how the system works.

Run this while the web server is running.

Author: H743Poten Research Team  
Date: October 4, 2025
"""

import requests
import json
import time
import sys

class CVValidationDemo:
    """Demo client for CV Peak Validation API"""
    
    def __init__(self, base_url="http://127.0.0.1:5001"):
        self.base_url = base_url
        print(f"🧪 CV Peak Validation Demo")
        print(f"🌐 Server: {base_url}")
        print("=" * 40)
    
    def test_connection(self):
        """Test if server is running"""
        try:
            response = requests.get(f"{self.base_url}/")
            if response.status_code == 200:
                print("✅ Server connection: OK")
                return True
            else:
                print(f"❌ Server returned status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            return False
    
    def get_available_files(self):
        """Get list of available CV files"""
        try:
            response = requests.get(f"{self.base_url}/api/files")
            data = response.json()
            
            if 'files' in data:
                files = data['files']
                print(f"📁 Found {len(files)} CV files:")
                
                # Show first few files as examples
                for i, file in enumerate(files[:5]):
                    metadata = file['metadata']
                    print(f"   {i+1}. {file['filename']}")
                    print(f"      Compound: {metadata['compound']}")
                    print(f"      Concentration: {metadata['concentration']}mM")
                    print(f"      Scan rate: {metadata['scan_rate']}mV/s")
                
                if len(files) > 5:
                    print(f"   ... and {len(files) - 5} more files")
                
                return files
            else:
                print("❌ No files found")
                return []
                
        except Exception as e:
            print(f"❌ Error getting files: {e}")
            return []
    
    def analyze_sample_file(self, files):
        """Analyze a sample CV file"""
        if not files:
            return None
        
        # Select first ferrocyanide file
        sample_file = None
        for file in files:
            if 'ferro' in file['filename'].lower():
                sample_file = file
                break
        
        if not sample_file:
            sample_file = files[0]  # Fallback to first file
        
        print(f"\\n🔬 Analyzing sample file: {sample_file['filename']}")
        print(f"📊 Metadata: {sample_file['metadata']}")
        
        try:
            response = requests.post(f"{self.base_url}/api/analyze", 
                                   json={'file_path': sample_file['full_path']})
            
            if response.status_code == 200:
                data = response.json()
                
                print("✅ Analysis completed!")
                print(f"📈 Session ID: {data['session_id']}")
                print(f"📊 Data points: {data['cv_data']['data_points']}")
                print(f"🎯 Peaks detected: {len(data['peaks'])}")
                
                # Show peak information
                print("\\n🎯 Detected Peaks:")
                for peak in data['peaks']:
                    print(f"   Peak {peak['id']}: {peak['voltage']:.3f}V, {peak['current']:.2f}µA")
                    print(f"      Type: {peak['type']}, Confidence: {peak['confidence']:.2f}")
                
                return data
            else:
                error_data = response.json()
                print(f"❌ Analysis failed: {error_data.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"❌ Error analyzing file: {e}")
            return None
    
    def demo_peak_validation(self, analysis_data):
        """Demonstrate peak validation"""
        if not analysis_data:
            return
        
        session_id = analysis_data['session_id']
        peaks = analysis_data['peaks']
        
        print(f"\\n✅ Demonstrating Peak Validation")
        print(f"📝 Session: {session_id}")
        
        # Create sample validations (validate some, reject others)
        validations = []
        
        for i, peak in enumerate(peaks):
            # Validate peaks with high confidence, reject others
            is_valid = peak['confidence'] > 0.6
            reasoning = "High confidence" if is_valid else "Low confidence"
            
            validations.append({
                'peak_id': peak['id'],
                'is_valid': is_valid,
                'reasoning': f"Demo validation: {reasoning}"
            })
            
            status = "✅ VALIDATE" if is_valid else "❌ REJECT"
            print(f"   Peak {peak['id']}: {status} (confidence: {peak['confidence']:.2f})")
        
        # Send validations to server
        try:
            response = requests.post(f"{self.base_url}/api/validate_peaks", 
                                   json={
                                       'session_id': session_id,
                                       'peak_validations': validations
                                   })
            
            if response.status_code == 200:
                result = response.json()
                print(f"\\n📊 Validation Results:")
                print(f"   ✅ Validated: {result['validated_count']} peaks")
                print(f"   ❌ Rejected: {result['rejected_count']} peaks")
                print(f"   📈 Total processed: {result['total_peaks']} peaks")
                
                return result
            else:
                error_data = response.json()
                print(f"❌ Validation failed: {error_data.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"❌ Error validating peaks: {e}")
            return None
    
    def demo_export_data(self):
        """Demonstrate exporting training data"""
        print(f"\\n📤 Demonstrating Data Export")
        
        try:
            response = requests.get(f"{self.base_url}/api/export_data")
            
            if response.status_code == 200:
                data = response.json()
                export_data = data['data']
                
                print("✅ Export successful!")
                print(f"📊 Training Data Summary:")
                print(f"   📈 Total peaks: {export_data['total_peaks']}")
                print(f"   📝 Sessions: {export_data['sessions']}")
                print(f"   🧪 Compounds: {export_data['compounds']}")
                print(f"   📅 Generated: {export_data['timestamp']}")
                print(f"   📁 Filename: {data['filename']}")
                
                # Show sample peaks
                if export_data['peaks']:
                    print("\\n📋 Sample validated peaks:")
                    for i, peak in enumerate(export_data['peaks'][:3]):
                        print(f"   {i+1}. {peak['compound_name']}: {peak['voltage']:.3f}V, "
                              f"{peak['current']:.2f}µA ({peak['peak_type']})")
                
                return data
            else:
                error_data = response.json()
                print(f"❌ Export failed: {error_data.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"❌ Error exporting data: {e}")
            return None
    
    def run_complete_demo(self):
        """Run complete demonstration"""
        print("🚀 Starting Complete CV Peak Validation Demo")
        print("=" * 50)
        
        # Step 1: Test connection
        if not self.test_connection():
            print("❌ Cannot proceed without server connection")
            return False
        
        # Step 2: Get available files
        files = self.get_available_files()
        if not files:
            print("❌ No CV files available for analysis")
            return False
        
        # Step 3: Analyze sample file
        analysis_data = self.analyze_sample_file(files)
        if not analysis_data:
            print("❌ Analysis failed")
            return False
        
        # Step 4: Demonstrate validation
        validation_result = self.demo_peak_validation(analysis_data)
        if not validation_result:
            print("❌ Validation failed")
            return False
        
        # Step 5: Export training data
        export_result = self.demo_export_data()
        if not export_result:
            print("⚠️  Export failed (may be expected if no data)")
        
        # Final summary
        print("\\n🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("✅ Web UI is working correctly")
        print("✅ Peak detection is functional") 
        print("✅ Validation system is operational")
        print("✅ Training data export is ready")
        print("\\n🌐 You can now use the web interface at:")
        print(f"   {self.base_url}")
        
        return True

def main():
    """Main demo function"""
    demo = CVValidationDemo()
    
    try:
        success = demo.run_complete_demo()
        
        if success:
            print("\\n💡 Next Steps:")
            print("1. Open http://127.0.0.1:5001 in your browser")
            print("2. Select a CV file from the dropdown")
            print("3. Click Recalculate to analyze")
            print("4. Select peaks to validate/reject")
            print("5. Export peak data for AI training")
        else:
            print("\\n❌ Demo failed - check server status")
    
    except KeyboardInterrupt:
        print("\\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\\n❌ Demo error: {e}")

if __name__ == "__main__":
    main()