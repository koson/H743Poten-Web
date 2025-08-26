#!/usr/bin/env python3
"""
Limited Test: Process only a few files to debug the batch analyzer
"""

import os
import glob
import json
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from scipy.stats import linregress

def parse_csv_robust(file_path):
    """Robust CSV parser for different formats"""
    try:
        # Try reading with different encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        print(f"   📄 CSV loaded: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"   📊 Columns: {list(df.columns)}")
        
        # Check if we have voltage and current columns
        voltage_col, current_col = None, None
        
        # Common column name patterns
        voltage_patterns = ['potential', 'voltage', 'volt', 'e', 'v', 'wevolt']
        current_patterns = ['current', 'i', 'wecurrent', 'we current']
        
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
            return None, None, "Could not identify voltage/current columns"
        
        # Extract data
        voltage = pd.to_numeric(df[voltage_col], errors='coerce').dropna()
        current = pd.to_numeric(df[current_col], errors='coerce').dropna()
        
        # Align lengths
        min_len = min(len(voltage), len(current))
        voltage = voltage.iloc[:min_len]
        current = current.iloc[:min_len]
        
        print(f"   📈 Data points: {len(voltage)}")
        print(f"   ⚡ Voltage range: [{voltage.min():.3f}, {voltage.max():.3f}]")
        print(f"   ⚡ Current range: [{current.min():.6f}, {current.max():.6f}]")
        
        if len(voltage) < 10:
            return None, None, "Insufficient data points"
        
        return voltage.values, current.values, None
        
    except Exception as e:
        return None, None, f"Error parsing CSV: {str(e)}"

def main():
    """Test with just a few files"""
    
    print("🧪 LIMITED BATCH TEST")
    print("=" * 40)
    
    # Find just first 3 CSV files
    all_files = []
    for root, dirs, files in os.walk("Test_data"):
        for file in files:
            if file.endswith('.csv') and not file.endswith('.backup'):
                all_files.append(os.path.join(root, file))
    
    test_files = sorted(all_files)[:3]  # Only first 3 files
    print(f"📁 Testing with {len(test_files)} files:")
    
    for i, file_path in enumerate(test_files):
        print(f"\n--- FILE {i+1}: {os.path.basename(file_path)} ---")
        
        try:
            voltage, current, error = parse_csv_robust(file_path)
            
            if error:
                print(f"   ❌ Error: {error}")
            else:
                print(f"   ✅ Parsed successfully!")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")

if __name__ == "__main__":
    main()