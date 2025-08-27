#!/usr/bin/env python3
"""
🎯 Precision Peak & Baseline Analysis - Quick Demo
ตัวอย่างการใช้งานระบบโดยไม่ต้องใช้ Jupyter Notebook

เนื่องจากมีปัญหาเรื่อง virtual environment กับ Jupyter
ไฟล์นี้จึงทำงานเหมือน notebook แต่รันผ่าน Python script
"""

print("🎯 PRECISION PEAK & BASELINE ANALYSIS - QUICK DEMO")
print("="*60)
print("📅 วันที่: 27 สิงหาคม 2025")
print("🎯 วัตถุประสงค์: ทดสอบระบบ Precision Peak Detection")
print("="*60)

# Import libraries
print("\n📦 IMPORTING LIBRARIES...")
try:
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    from scipy import signal
    import json
    from datetime import datetime
    import warnings
    warnings.filterwarnings('ignore')
    
    print("✅ Core libraries imported")
    
    # Set style
    try:
        plt.style.use('seaborn')
        print("✅ Matplotlib style set")
    except:
        plt.style.use('default')
        print("✅ Default style set")
        
    try:
        sns.set_palette("husl")
        print("✅ Seaborn palette set")
    except Exception as e:
        print(f"⚠️ Seaborn palette: {e}")
    
except Exception as e:
    print(f"❌ Import error: {e}")

# Import precision analyzer
print("\n🔬 IMPORTING PRECISION ANALYZER...")
try:
    import sys
    sys.path.append('.')
    from precision_peak_baseline_analyzer import PrecisionPeakBaselineAnalyzer
    print("✅ Precision Peak & Baseline Analyzer imported successfully")
except Exception as e:
    print(f"❌ Analyzer import error: {e}")

# Configuration
print("\n⚙️ CONFIGURATION...")
config = {
    'analyte': 'generic',
    'confidence_threshold': 40.0,
    'min_peak_height': 1.0,
    'peak_prominence_factor': 0.02,
    'quality_threshold': 50.0,
    'enable_smoothing': True,
    'outlier_removal': True
}

analyzer = PrecisionPeakBaselineAnalyzer(config)
print("✅ Analyzer configured:")
for key, value in config.items():
    print(f"   • {key}: {value}")

# Data loading
print("\n📊 DATA LOADING...")
test_file = "Test_data/Palmsens/Palmsens_0.5mM/Palmsens_0.5mM_CV_100mVpS_E1_scan_01.csv"
print(f"📁 Test file: {test_file}")

try:
    # Load data
    df = pd.read_csv(test_file, skiprows=1)
    voltage = df.iloc[:, 0].values
    current = df.iloc[:, 1].values
    
    print(f"✅ Data loaded successfully:")
    print(f"   • Data points: {len(voltage)}")
    print(f"   • Voltage range: {voltage.min():.3f} to {voltage.max():.3f} V")
    print(f"   • Current range: {current.min():.3f} to {current.max():.3f} μA")
    
    # Data statistics
    print(f"\n📊 Data Statistics:")
    print(f"   • Mean current: {current.mean():.3f} μA")
    print(f"   • Std deviation: {current.std():.3f} μA")
    print(f"   • Peak-to-peak: {current.max() - current.min():.3f} μA")
    
except Exception as e:
    print(f"❌ Data loading error: {e}")

# Run analysis
print("\n🔬 RUNNING PRECISION ANALYSIS...")
print("-"*40)

try:
    result = analyzer.analyze_cv_data(test_file)
    
    print("🎯 ANALYSIS RESULTS:")
    print(f"✅ Success: {result['success']}")
    print(f"📍 Peaks detected: {len(result['peaks'])}")
    print(f"📊 Baseline quality: {result['baseline_quality']:.1f}%")
    print(f"🎯 Overall quality: {result['overall_quality']:.1f}%")
    print(f"📐 Total area: {result['total_area']:.3f} μA⋅V")
    print(f"📈 Oxidation area: {result['oxidation_area']:.3f} μA⋅V")
    print(f"📉 Reduction area: {result['reduction_area']:.3f} μA⋅V")
    print(f"🧬 PLS readiness: {result['pls_readiness']:.1f}%")
    
    # Peak details
    if result['peaks']:
        print(f"\n📍 DETECTED PEAKS ({len(result['peaks'])} total):")
        oxidation_count = len([p for p in result['peaks'] if p['peak_type'] == 'oxidation'])
        reduction_count = len([p for p in result['peaks'] if p['peak_type'] == 'reduction'])
        
        print(f"   • Oxidation peaks: {oxidation_count}")
        print(f"   • Reduction peaks: {reduction_count}")
        
        print("\nTop 5 peaks:")
        for i, peak in enumerate(result['peaks'][:5]):
            print(f"   Peak {i+1}: {peak['peak_type']} at {peak['voltage']:.3f}V")
            print(f"            Current: {peak['current']:.2f}μA, Confidence: {peak['confidence']:.1f}%")
    
    # Generate simple visualization
    print(f"\n📊 GENERATING VISUALIZATION...")
    try:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # CV plot with peaks
        ax1.plot(voltage, current, 'b-', linewidth=1.5, alpha=0.7, label='CV Data')
        
        if result['peaks']:
            # Plot oxidation peaks
            ox_peaks = [p for p in result['peaks'] if p['peak_type'] == 'oxidation']
            if ox_peaks:
                ox_v = [p['voltage'] for p in ox_peaks]
                ox_i = [p['current'] for p in ox_peaks]
                ax1.scatter(ox_v, ox_i, c='red', s=80, zorder=5, label=f'Oxidation ({len(ox_peaks)})')
            
            # Plot reduction peaks
            red_peaks = [p for p in result['peaks'] if p['peak_type'] == 'reduction']
            if red_peaks:
                red_v = [p['voltage'] for p in red_peaks]
                red_i = [p['current'] for p in red_peaks]
                ax1.scatter(red_v, red_i, c='blue', s=80, zorder=5, label=f'Reduction ({len(red_peaks)})')
        
        ax1.set_xlabel('Voltage (V)')
        ax1.set_ylabel('Current (μA)')
        ax1.set_title('🎯 Detected Peaks on CV Data')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Quality metrics
        metrics = {
            'Baseline': result['baseline_quality'],
            'Overall': result['overall_quality'],
            'PLS Ready': result['pls_readiness']
        }
        
        bars = ax2.bar(list(metrics.keys()), list(metrics.values()), 
                      alpha=0.7, color=['green', 'blue', 'orange'])
        ax2.set_ylabel('Quality (%)')
        ax2.set_title('📊 Analysis Quality Metrics')
        ax2.set_ylim(0, 100)
        
        # Add value labels
        for bar, value in zip(bars, metrics.values()):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                     f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('precision_demo_results.png', dpi=150, bbox_inches='tight')
        print("✅ Visualization saved: precision_demo_results.png")
        
    except Exception as e:
        print(f"⚠️ Visualization error: {e}")
    
    # Save results
    print(f"\n💾 SAVING RESULTS...")
    try:
        report_filename = f"precision_demo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"✅ Results saved: {report_filename}")
    except Exception as e:
        print(f"⚠️ Save error: {e}")
        
except Exception as e:
    print(f"❌ Analysis error: {e}")
    import traceback
    traceback.print_exc()

print(f"\n" + "="*60)
print("🏆 DEMO COMPLETE!")
print("💡 สามารถใช้งานระบบ Precision Peak Detection ได้แล้ว")
print("📋 Notebook จะใช้งานได้เมื่อแก้ไข kernel environment แล้ว")
print("="*60)
