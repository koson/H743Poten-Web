#!/usr/bin/env python3
"""
Advanced CV Scan Test Suite
ทดสอบ CV Scan หลายแบบเพื่อ validate functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cv_scan_test import SimpleSTM32CVTester
import time
import json

def test_scan_rates():
    """ทดสอบ scan rate ต่างๆ"""
    print("\n🧪 Test 1: Different Scan Rates")
    print("=" * 40)
    
    tester = SimpleSTM32CVTester("/dev/ttyACM0")
    if not tester.connect():
        return False
    
    if not tester.clear_stm32_state():
        return False
    
    scan_rates = [0.05, 0.1, 0.2, 0.5]  # V/s
    results = {}
    
    for rate in scan_rates:
        print(f"\n📊 Testing scan rate: {rate}V/s")
        
        # Short test scan
        success = tester.test_cv_scan(
            begin_v=-0.2,
            upper_v=0.2,
            lower_v=-0.2,
            scan_rate=rate,
            cycles=1,
            duration=20
        )
        
        results[f"scan_rate_{rate}"] = success
        time.sleep(2)  # Brief pause between tests
    
    tester.disconnect()
    
    print(f"\n📋 Scan Rate Test Results:")
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test}: {status}")
    
    return all(results.values())

def test_voltage_ranges():
    """ทดสอบ voltage range ต่างๆ"""
    print("\n🧪 Test 2: Different Voltage Ranges")
    print("=" * 40)
    
    tester = SimpleSTM32CVTester("/dev/ttyACM0")
    if not tester.connect():
        return False
    
    if not tester.clear_stm32_state():
        return False
    
    voltage_ranges = [
        (-0.5, 0.5),   # ±0.5V
        (-1.0, 1.0),   # ±1.0V
        (-0.2, 0.8),   # Asymmetric
        (0.0, 0.5),    # Positive only
    ]
    
    results = {}
    
    for i, (lower, upper) in enumerate(voltage_ranges, 1):
        print(f"\n📊 Testing range {i}: {lower}V to {upper}V")
        
        success = tester.test_cv_scan(
            begin_v=lower,
            upper_v=upper,
            lower_v=lower,
            scan_rate=0.2,
            cycles=1,
            duration=15
        )
        
        results[f"range_{lower}_{upper}"] = success
        time.sleep(2)
    
    tester.disconnect()
    
    print(f"\n📋 Voltage Range Test Results:")
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test}: {status}")
    
    return all(results.values())

def test_multiple_cycles():
    """ทดสอบ multiple cycles"""
    print("\n🧪 Test 3: Multiple Cycles")
    print("=" * 40)
    
    tester = SimpleSTM32CVTester("/dev/ttyACM0")
    if not tester.connect():
        return False
    
    if not tester.clear_stm32_state():
        return False
    
    cycles_to_test = [1, 2, 3]
    results = {}
    
    for cycles in cycles_to_test:
        print(f"\n📊 Testing {cycles} cycles")
        
        success = tester.test_cv_scan(
            begin_v=-0.3,
            upper_v=0.3,
            lower_v=-0.3,
            scan_rate=0.3,
            cycles=cycles,
            duration=cycles * 10 + 5  # More time for more cycles
        )
        
        results[f"cycles_{cycles}"] = success
        time.sleep(2)
    
    tester.disconnect()
    
    print(f"\n📋 Multiple Cycles Test Results:")
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test}: {status}")
    
    return all(results.values())

def test_stress_scan():
    """ทดสอบ stress test - long duration scan"""
    print("\n🧪 Test 4: Stress Test (Long Duration)")
    print("=" * 40)
    
    tester = SimpleSTM32CVTester("/dev/ttyACM0")
    if not tester.connect():
        return False
    
    if not tester.clear_stm32_state():
        return False
    
    print("📊 Running 60-second stress test...")
    
    success = tester.test_cv_scan(
        begin_v=-0.8,
        upper_v=0.8,
        lower_v=-0.8,
        scan_rate=0.05,  # Slow scan for long test
        cycles=2,
        duration=60  # 1 minute test
    )
    
    tester.disconnect()
    
    print(f"\n📋 Stress Test Result: {'✅ PASS' if success else '❌ FAIL'}")
    return success

def run_full_test_suite():
    """รัน test suite ทั้งหมด"""
    print("🔬 STM32 CV Advanced Test Suite")
    print("=" * 50)
    
    test_results = {}
    
    # Test 1: Scan Rates
    try:
        test_results['scan_rates'] = test_scan_rates()
    except Exception as e:
        print(f"❌ Scan rates test failed: {e}")
        test_results['scan_rates'] = False
    
    time.sleep(3)
    
    # Test 2: Voltage Ranges
    try:
        test_results['voltage_ranges'] = test_voltage_ranges()
    except Exception as e:
        print(f"❌ Voltage ranges test failed: {e}")
        test_results['voltage_ranges'] = False
    
    time.sleep(3)
    
    # Test 3: Multiple Cycles
    try:
        test_results['multiple_cycles'] = test_multiple_cycles()
    except Exception as e:
        print(f"❌ Multiple cycles test failed: {e}")
        test_results['multiple_cycles'] = False
    
    time.sleep(3)
    
    # Test 4: Stress Test
    try:
        test_results['stress_test'] = test_stress_scan()
    except Exception as e:
        print(f"❌ Stress test failed: {e}")
        test_results['stress_test'] = False
    
    # Final Results
    print("\n" + "="*50)
    print("🏆 FINAL TEST RESULTS")
    print("="*50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
        if result:
            passed += 1
    
    success_rate = (passed / total) * 100
    print(f"\n📊 Overall Success Rate: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate >= 75:
        print("🎉 CV Test Suite: PASSED!")
        return True
    else:
        print("❌ CV Test Suite: FAILED!")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        exit(0 if run_full_test_suite() else 1)
    else:
        print("🔬 STM32 CV Quick Validation Test")
        print("=" * 40)
        
        # Quick single test
        tester = SimpleSTM32CVTester("/dev/ttyACM0")
        if tester.connect() and tester.clear_stm32_state():
            success = tester.test_cv_scan(
                begin_v=-0.3, upper_v=0.3, lower_v=-0.3,
                scan_rate=0.2, cycles=1, duration=15
            )
            tester.disconnect()
            
            if success:
                print("🎉 Quick CV test: PASSED!")
                print("Run with --full flag for complete test suite")
                exit(0)
            else:
                print("❌ Quick CV test: FAILED!")
                exit(1)
        else:
            print("❌ Could not connect to STM32")
            exit(1)