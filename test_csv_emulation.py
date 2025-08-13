"""
CSV Emulation Test Script
Test the CSV data emulation functionality
"""

import sys
import os
import time

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from hardware.mock_scpi_handler import MockSCPIHandler
from hardware.csv_data_emulator import CSVDataEmulator

def test_csv_emulator_standalone():
    """Test CSV emulator as standalone component"""
    print("=== Testing CSV Data Emulator (Standalone) ===")
    
    emulator = CSVDataEmulator()
    
    # Test loading CSV file
    csv_file = os.path.join(os.path.dirname(__file__), 'sample_data', 'cv_sample.csv')
    print(f"Loading CSV file: {csv_file}")
    
    success = emulator.load_csv_file(csv_file)
    if not success:
        print("❌ Failed to load CSV file")
        return False
    
    print("✅ CSV file loaded successfully")
    
    # Get data info
    info = emulator.get_data_info()
    print(f"📊 Data info: {info['total_points']} points, duration: {info['time_range']['duration']:.3f}s")
    
    # Start emulation at 2x speed
    print("🚀 Starting emulation at 2x speed...")
    success = emulator.start_emulation(playback_speed=2.0, loop=False)
    if not success:
        print("❌ Failed to start emulation")
        return False
    
    # Monitor progress for 5 seconds
    for i in range(10):
        time.sleep(0.5)
        progress = emulator.get_progress()
        data_points = emulator.get_current_data()
        latest = emulator.get_latest_point()
        
        print(f"Progress: {progress['progress_percent']:.1f}% "
              f"({progress['current_index']}/{progress['total_points']}) "
              f"- {len(data_points)} points available")
        
        if latest:
            print(f"  Latest: t={latest['timestamp']:.3f}s, V={latest['voltage']:.3f}V, I={latest['current']:.9f}A")
    
    # Stop emulation
    emulator.stop_emulation()
    print("⏹️ Emulation stopped")
    
    return True

def test_mock_scpi_with_csv():
    """Test Mock SCPI Handler with CSV emulation"""
    print("\n=== Testing Mock SCPI Handler with CSV ===")
    
    handler = MockSCPIHandler()
    
    # Connect
    success = handler.connect()
    if not success:
        print("❌ Failed to connect")
        return False
    print("✅ Connected to mock device")
    
    # Load CSV data
    csv_file = os.path.join(os.path.dirname(__file__), 'sample_data', 'cv_sample.csv')
    csv_file = csv_file.replace('\\', '/')  # Normalize path for command
    
    result = handler.send_custom_command(f"csv:load {csv_file}")
    if not result['success']:
        print(f"❌ Failed to load CSV: {result['error']}")
        return False
    print("✅ CSV data loaded via SCPI command")
    
    # Get CSV info
    result = handler.send_custom_command("csv:info?")
    print(f"📊 CSV Info: {result['response']}")
    
    # Start CSV emulation
    result = handler.send_custom_command("csv:start 1.5 false")  # 1.5x speed, no loop
    if not result['success']:
        print(f"❌ Failed to start CSV emulation: {result['error']}")
        return False
    print("🚀 CSV emulation started at 1.5x speed")
    
    # Monitor for a few seconds
    for i in range(8):
        time.sleep(0.5)
        
        # Get progress
        result = handler.send_custom_command("csv:progress?")
        print(f"Progress: {result['response']}")
        
        # Get data
        result = handler.send_custom_command("poten:csv:data?")
        if result['success'] and result['response']:
            lines = result['response'].split('\n')
            print(f"  Data points available: {len(lines)}")
            if lines:
                last_line = lines[-1].split(',')
                if len(last_line) >= 3:
                    print(f"  Latest: t={last_line[0]}s, V={last_line[1]}V, I={last_line[2]}A")
    
    # Test seeking
    print("🎯 Testing seek functionality...")
    result = handler.send_custom_command("csv:seek 2.0")
    if result['success']:
        print("✅ Seeked to 2.0 seconds")
    else:
        print(f"❌ Seek failed: {result['error']}")
    
    # Stop emulation
    result = handler.send_custom_command("csv:stop")
    print("⏹️ CSV emulation stopped")
    
    # Disconnect
    handler.disconnect()
    print("🔌 Disconnected")
    
    return True

def test_regular_mock_simulation():
    """Test regular mock simulation (non-CSV)"""
    print("\n=== Testing Regular Mock Simulation ===")
    
    handler = MockSCPIHandler()
    handler.connect()
    
    # Setup CV measurement
    result = handler.send_custom_command("poten:cv:setup -0.5,0.5,0.05,0.01")
    print(f"Setup CV: {result['success']}")
    
    # Start measurement
    result = handler.send_custom_command("poten:cv:start")
    print(f"Start CV: {result['success']}")
    
    # Get some data
    time.sleep(2)
    result = handler.send_custom_command("poten:cv:data?")
    if result['success'] and result['response']:
        lines = result['response'].split('\n')
        print(f"Mock simulation generated {len(lines)} data points")
        if lines:
            first_line = lines[0].split(',')
            last_line = lines[-1].split(',')
            print(f"  First point: t={first_line[0]}s, V={first_line[1]}V")
            print(f"  Last point: t={last_line[0]}s, V={last_line[1]}V")
    
    # Stop measurement
    handler.send_custom_command("poten:cv:stop")
    handler.disconnect()
    print("✅ Regular mock simulation test completed")
    
    return True

def main():
    """Run all tests"""
    print("🧪 CSV Emulation System Test")
    print("=" * 50)
    
    try:
        # Test standalone emulator
        success1 = test_csv_emulator_standalone()
        
        # Test SCPI integration
        success2 = test_mock_scpi_with_csv()
        
        # Test regular simulation
        success3 = test_regular_mock_simulation()
        
        print("\n" + "=" * 50)
        print("📋 Test Results:")
        print(f"  CSV Emulator (Standalone): {'✅ PASS' if success1 else '❌ FAIL'}")
        print(f"  Mock SCPI with CSV: {'✅ PASS' if success2 else '❌ FAIL'}")
        print(f"  Regular Mock Simulation: {'✅ PASS' if success3 else '❌ FAIL'}")
        
        if all([success1, success2, success3]):
            print("\n🎉 All tests passed! CSV emulation system is working correctly.")
        else:
            print("\n⚠️ Some tests failed. Check the output above for details.")
            
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
