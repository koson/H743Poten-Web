#!/usr/bin/env python3
"""
Fixed CSV Parser that handles both Palmsens and STM32 formats correctly
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import linregress

def parse_csv_robust(file_path):
    """Robust CSV parser for different formats"""
    try:
        filename = os.path.basename(file_path)
        print(f"   📄 Parsing: {filename}")
        
        # Check if this is a Palmsens file (has header format)
        if 'Palmsens' in filename:
            # Palmsens format: 2-line header, then data
            df = pd.read_csv(file_path, skiprows=1)  # Skip the filename line
            print(f"   📊 Palmsens format detected")
        else:
            # STM32 format: regular CSV
            df = pd.read_csv(file_path)
            print(f"   📊 STM32 format detected")
        
        print(f"   📋 Shape: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"   📊 Columns: {list(df.columns)}")
        
        # Find voltage and current columns
        voltage_col, current_col = None, None
        
        # Column mapping for different formats
        voltage_patterns = ['v', 'voltage', 'potential', 'volt', 'e', 'wevolt']
        current_patterns = ['ua', 'current', 'i', 'wecurrent', 'we current']
        
        columns_lower = [col.lower().strip() for col in df.columns]
        
        # Find voltage column
        for pattern in voltage_patterns:
            for i, col in enumerate(columns_lower):
                if pattern in col:
                    voltage_col = df.columns[i]
                    break
            if voltage_col:
                break
        
        # Find current column  
        for pattern in current_patterns:
            for i, col in enumerate(columns_lower):
                if pattern in col:
                    current_col = df.columns[i]
                    break
            if current_col:
                break
        
        print(f"   🔍 Voltage column: {voltage_col}")
        print(f"   🔍 Current column: {current_col}")
        
        if voltage_col is None or current_col is None:
            return None, None, f"Could not identify columns from: {df.columns.tolist()}"
        
        # Extract and convert data
        voltage = pd.to_numeric(df[voltage_col], errors='coerce').dropna()
        current = pd.to_numeric(df[current_col], errors='coerce').dropna()
        
        # Convert uA to A if needed (Palmsens uses uA)
        if current_col.lower() == 'ua':
            current = current * 1e-6  # Convert uA to A
            print(f"   🔄 Converted uA to A")
        
        # Align lengths
        min_len = min(len(voltage), len(current))
        voltage = voltage.iloc[:min_len].values
        current = current.iloc[:min_len].values
        
        print(f"   📈 Data points: {len(voltage)}")
        print(f"   ⚡ Voltage range: [{voltage.min():.3f}, {voltage.max():.3f}] V")
        print(f"   ⚡ Current range: [{current.min():.2e}, {current.max():.2e}] A")
        
        if len(voltage) < 10:
            return None, None, "Insufficient data points"
        
        return voltage, current, None
        
    except Exception as e:
        return None, None, f"Error parsing CSV: {str(e)}"

def voltage_window_baseline_detector(voltage, current, window_size=0.05):
    """Detect baseline regions using voltage windows"""
    baseline_segments = []
    
    # Split voltage range into windows
    v_min, v_max = min(voltage), max(voltage)
    v_range = v_max - v_min
    num_windows = max(10, int(v_range / window_size))
    
    for i in range(num_windows):
        window_start = v_min + i * window_size
        window_end = window_start + window_size
        
        # Find points in this window
        mask = (voltage >= window_start) & (voltage <= window_end)
        window_current = current[mask]
        window_voltage = voltage[mask]
        
        if len(window_current) > 5:
            # Check if current is relatively stable (low std)
            current_std = np.std(window_current)
            current_mean = np.mean(window_current)
            
            # Relative stability check
            if current_std < abs(current_mean) * 0.1 + 1e-9:  # Adjusted for A units
                baseline_segments.append({
                    'voltage_range': (window_start, window_end),
                    'voltage_values': window_voltage,
                    'current_values': window_current,
                    'stability': current_std
                })
    
    return baseline_segments

def calculate_r2_for_segment(voltage, current):
    """Calculate R² for a single baseline segment"""
    if len(voltage) < 3:
        return 0.0
    
    try:
        slope, intercept, r_value, p_value, std_err = linregress(voltage, current)
        return r_value ** 2
    except:
        return 0.0

def analyze_and_plot_file(file_path, output_dir):
    """Analyze a single file and create plot"""
    
    # Parse CSV
    voltage, current, error = parse_csv_robust(file_path)
    if error:
        print(f"   ❌ Parse error: {error}")
        return None
    
    # Detect baselines
    baseline_segments = voltage_window_baseline_detector(voltage, current)
    print(f"   🔍 Found {len(baseline_segments)} baseline segments")
    
    if len(baseline_segments) == 0:
        print(f"   ⚠️ No baseline segments detected")
        return None
    
    # Calculate R² for each segment
    segment_r2 = []
    for segment in baseline_segments:
        r2 = calculate_r2_for_segment(segment['voltage_values'], segment['current_values'])
        segment_r2.append(r2)
    
    # Overall statistics
    avg_r2 = np.mean(segment_r2) if segment_r2 else 0.0
    max_r2 = max(segment_r2) if segment_r2 else 0.0
    
    # Determine quality
    if avg_r2 >= 0.9:
        quality = "EXCELLENT 🟢"
    elif avg_r2 >= 0.7:
        quality = "GOOD ✅"
    elif avg_r2 >= 0.5:
        quality = "FAIR ⚠️"
    else:
        quality = "POOR ❌"
    
    print(f"   📊 Quality: {quality} (R²={avg_r2:.3f})")
    
    # Create plot
    plt.figure(figsize=(12, 8))
    
    # Plot main CV curve
    plt.plot(voltage, current, 'b-', linewidth=0.8, alpha=0.7, label='CV Curve')
    
    # Highlight baseline segments
    colors = ['red', 'green', 'orange', 'purple', 'brown', 'pink']
    for i, (segment, r2) in enumerate(zip(baseline_segments, segment_r2)):
        color = colors[i % len(colors)]
        v_vals = segment['voltage_values']
        i_vals = segment['current_values']
        
        plt.scatter(v_vals, i_vals, c=color, s=20, alpha=0.8, 
                   label=f'Baseline {i+1} (R²={r2:.3f})')
    
    # Add overall R² annotation
    plt.text(0.02, 0.98, f"Overall R² = {avg_r2:.3f}\n{quality}", 
             transform=plt.gca().transAxes, fontsize=12, 
             verticalalignment='top', 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Labels and formatting
    plt.xlabel('Voltage (V)')
    plt.ylabel('Current (A)')
    filename = os.path.basename(file_path)
    plt.title(f'Baseline Analysis: {filename}')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save plot
    plot_filename = os.path.splitext(filename)[0] + '_baseline_analysis.png'
    plot_path = os.path.join(output_dir, plot_filename)
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"   💾 Plot saved: {plot_filename}")
    
    result = {
        'avg_r2': avg_r2,
        'max_r2': max_r2,
        'num_segments': len(baseline_segments),
        'quality': quality,
        'total_points': len(voltage)
    }
    
    return result

def main():
    """Test with first few files from each instrument"""
    
    print("🧪 CORRECTED CSV PARSER TEST")
    print("=" * 50)
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"test_corrected_parser_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"📂 Output directory: {output_dir}")
    
    # Get 2 files from each instrument type
    test_files = []
    
    # Palmsens files
    palmsens_dir = "Test_data/Palmsens/Palmsens_0.5mM"
    if os.path.exists(palmsens_dir):
        palmsens_files = [f for f in os.listdir(palmsens_dir) if f.endswith('.csv')][:2]
        for f in palmsens_files:
            test_files.append(os.path.join(palmsens_dir, f))
    
    # STM32 files  
    stm32_dir = "Test_data/Stm32/Pipot_Ferro_1_0mM"
    if os.path.exists(stm32_dir):
        stm32_files = [f for f in os.listdir(stm32_dir) if f.endswith('.csv') and not f.endswith('.backup')][:2]
        for f in stm32_files:
            test_files.append(os.path.join(stm32_dir, f))
    
    print(f"📁 Testing with {len(test_files)} files:")
    
    results = []
    for i, file_path in enumerate(test_files):
        print(f"\n--- FILE {i+1}: {os.path.basename(file_path)} ---")
        
        try:
            result = analyze_and_plot_file(file_path, output_dir)
            if result:
                results.append({'file': file_path, 'result': result})
                print(f"   ✅ Success!")
            else:
                print(f"   ❌ Analysis failed")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
    
    # Summary
    print(f"\n" + "=" * 50)
    print(f"🎉 TEST COMPLETE")
    print(f"📊 Successful: {len(results)}/{len(test_files)}")
    print(f"📂 Plots saved in: {output_dir}")
    
    if results:
        print(f"\n📈 RESULTS:")
        for r in results:
            filename = os.path.basename(r['file'])[:40]
            result = r['result']
            print(f"   {filename:40} | R²={result['avg_r2']:.3f} | {result['quality']}")

if __name__ == "__main__":
    main()