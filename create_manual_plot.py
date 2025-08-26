#!/usr/bin/env python3
"""
Create a single baseline plot manually - no external dependencies
"""

import csv
import os
import sys

# Read the CSV file manually
def read_csv_manual(filename):
    """Read CSV file manually without pandas"""
    data = []
    headers = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        for row in reader:
            try:
                data.append([float(x) for x in row])
            except ValueError:
                continue  # Skip invalid rows
    
    return headers, data

def find_columns(headers):
    """Find voltage and current columns"""
    voltage_idx = -1
    current_idx = -1
    
    for i, header in enumerate(headers):
        header_lower = header.strip().lower()
        if any(keyword in header_lower for keyword in ['voltage', 'potential', 'v']):
            voltage_idx = i
        elif any(keyword in header_lower for keyword in ['current', 'i']):
            current_idx = i
    
    return voltage_idx, current_idx

def simple_baseline_detection(voltage_data, current_data):
    """
    Very simple baseline detection - find flat regions
    """
    if len(voltage_data) < 20:
        return [], []
    
    # Convert to lists for easier manipulation
    v_list = list(voltage_data)
    i_list = list(current_data)
    
    # Simple approach: find regions where current doesn't change much
    baseline_v = []
    baseline_i = []
    
    window_size = 10
    threshold = 2.0  # µA threshold for "flat" regions
    
    for i in range(0, len(i_list) - window_size, window_size // 2):
        window_current = i_list[i:i + window_size]
        window_voltage = v_list[i:i + window_size]
        
        if len(window_current) >= window_size:
            current_range = max(window_current) - min(window_current)
            
            # If current variation is small, consider as baseline
            if current_range < threshold:
                baseline_v.extend(window_voltage)
                baseline_i.extend(window_current)
    
    return baseline_v, baseline_i

def create_html_plot(voltage_data, current_data, baseline_v, baseline_i, filename, output_path):
    """Create an HTML plot using simple SVG"""
    
    # Calculate plot bounds
    v_min, v_max = min(voltage_data), max(voltage_data)
    i_min, i_max = min(current_data), max(current_data)
    
    # Add some padding
    v_range = v_max - v_min
    i_range = i_max - i_min
    v_min -= v_range * 0.1
    v_max += v_range * 0.1
    i_min -= i_range * 0.1
    i_max += i_range * 0.1
    
    # SVG dimensions
    width, height = 800, 600
    margin = 60
    plot_width = width - 2 * margin
    plot_height = height - 2 * margin
    
    # Scale functions
    def scale_x(v):
        return margin + (v - v_min) / (v_max - v_min) * plot_width
    
    def scale_y(i):
        return height - margin - (i - i_min) / (i_max - i_min) * plot_height
    
    # Generate SVG
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Baseline Detection: {filename}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .plot-container {{ text-align: center; }}
            .stats {{ margin-top: 20px; text-align: left; max-width: 800px; margin-left: auto; margin-right: auto; }}
        </style>
    </head>
    <body>
        <div class="plot-container">
            <h2>✅ Baseline Detection: {filename}</h2>
            <svg width="{width}" height="{height}" style="border: 1px solid #ccc;">
                <!-- Grid lines -->
                <defs>
                    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                        <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#f0f0f0" stroke-width="1"/>
                    </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" />
                
                <!-- Plot area -->
                <rect x="{margin}" y="{margin}" width="{plot_width}" height="{plot_height}" 
                      fill="none" stroke="black" stroke-width="2"/>
                
                <!-- CV Data -->
                <polyline points="{' '.join([f'{scale_x(v)},{scale_y(i)}' for v, i in zip(voltage_data, current_data)])}"
                          fill="none" stroke="blue" stroke-width="2" opacity="0.8"/>
                
                <!-- Baseline -->
                {f'<polyline points="{" ".join([f"{scale_x(v)},{scale_y(i)}" for v, i in zip(baseline_v, baseline_i)])}" fill="none" stroke="green" stroke-width="4"/>' if baseline_v else ''}
                
                <!-- Axes labels -->
                <text x="{width/2}" y="{height - 10}" text-anchor="middle" font-size="14">Voltage (V)</text>
                <text x="20" y="{height/2}" text-anchor="middle" font-size="14" transform="rotate(-90, 20, {height/2})">Current (µA)</text>
                
                <!-- Axis values -->
                <text x="{margin}" y="{height - margin + 20}" text-anchor="middle" font-size="12">{v_min:.2f}</text>
                <text x="{width - margin}" y="{height - margin + 20}" text-anchor="middle" font-size="12">{v_max:.2f}</text>
                <text x="{margin - 10}" y="{margin}" text-anchor="end" font-size="12">{i_max:.1f}</text>
                <text x="{margin - 10}" y="{height - margin}" text-anchor="end" font-size="12">{i_min:.1f}</text>
                
                <!-- Legend -->
                <rect x="{width - 200}" y="{margin + 20}" width="180" height="80" fill="white" stroke="gray" stroke-width="1"/>
                <line x1="{width - 190}" y1="{margin + 35}" x2="{width - 160}" y2="{margin + 35}" stroke="blue" stroke-width="3"/>
                <text x="{width - 155}" y="{margin + 40}" font-size="12">CV Data</text>
                <line x1="{width - 190}" y1="{margin + 55}" x2="{width - 160}" y2="{margin + 55}" stroke="green" stroke-width="3"/>
                <text x="{width - 155}" y="{margin + 60}" font-size="12">Baseline</text>
                <text x="{width - 155}" y="{margin + 80}" font-size="10">Baseline pts: {len(baseline_v)}</text>
            </svg>
        </div>
        
        <div class="stats">
            <h3>Statistics:</h3>
            <p><strong>Data points:</strong> {len(voltage_data)}</p>
            <p><strong>Voltage range:</strong> {v_min:.3f} to {v_max:.3f} V</p>
            <p><strong>Current range:</strong> {i_min:.3f} to {i_max:.3f} µA</p>
            <p><strong>Baseline points:</strong> {len(baseline_v)}</p>
            <p><strong>Baseline coverage:</strong> {len(baseline_v)/len(voltage_data)*100:.1f}% of data</p>
        </div>
    </body>
    </html>
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    """Test with a single file"""
    test_file = "Test_data/Stm32/Pipot_Ferro_1_0mM_20mVpS_E4_scan_05.csv"
    
    print(f"🧪 Creating baseline plot for: {test_file}")
    
    if not os.path.exists(test_file):
        print(f"❌ File not found: {test_file}")
        return
    
    try:
        # Read CSV manually
        headers, data = read_csv_manual(test_file)
        print(f"✅ Loaded {len(data)} rows with columns: {headers}")
        
        # Find columns
        voltage_idx, current_idx = find_columns(headers)
        
        if voltage_idx == -1 or current_idx == -1:
            print(f"❌ Could not find voltage/current columns")
            print(f"Available columns: {headers}")
            return
        
        print(f"✅ Found voltage column: {headers[voltage_idx]} (index {voltage_idx})")
        print(f"✅ Found current column: {headers[current_idx]} (index {current_idx})")
        
        # Extract data
        voltage_data = [row[voltage_idx] for row in data]
        current_data = [row[current_idx] for row in data]
        
        # Apply unit conversion (assume µA after conversion script)
        current_unit = headers[current_idx].strip().lower()
        if current_unit in ['ua', 'µa']:
            scale = 1.0
        elif current_unit == 'a':
            scale = 1e6
        elif current_unit == 'ma':
            scale = 1e3
        elif current_unit == 'na':
            scale = 1e-3
        else:
            scale = 1.0
        
        current_data = [i * scale for i in current_data]
        
        print(f"✅ Data loaded: {len(voltage_data)} points")
        print(f"Voltage range: {min(voltage_data):.3f} to {max(voltage_data):.3f} V")
        print(f"Current range: {min(current_data):.3f} to {max(current_data):.3f} µA")
        
        # Simple baseline detection
        baseline_v, baseline_i = simple_baseline_detection(voltage_data, current_data)
        
        print(f"✅ Baseline detected: {len(baseline_v)} points")
        
        # Create HTML plot
        filename = os.path.basename(test_file)
        output_path = f"{os.path.splitext(filename)[0]}_baseline_plot.html"
        
        create_html_plot(voltage_data, current_data, baseline_v, baseline_i, filename, output_path)
        
        print(f"✅ Plot saved: {output_path}")
        print(f"📊 Open the HTML file in a browser to view the plot")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()