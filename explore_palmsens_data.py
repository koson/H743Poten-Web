#!/usr/bin/env python3
"""
Palmsens Data Explorer
====================
Explore Palmsens data structure to understand available concentrations and scan rates
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
from collections import defaultdict

def extract_palmsens_metadata(filename: str) -> dict:
    """Extract concentration and scan rate from Palmsens filename"""
    filename_lower = filename.lower()
    
    # Concentration from directory or filename
    concentration = None
    
    # Try different patterns
    patterns = [
        r'palmsens_(\d+\.?\d*)mm',  # palmsens_1.0mM
        r'(\d+\.?\d*)mm',           # 1.0mM
        r'(\d+)_(\d+)mm',           # 1_0mM format
        r'ferro.*?(\d+\.?\d*)mm'    # ferro...1.0mM
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename_lower)
        if match:
            try:
                if len(match.groups()) == 2:  # Handle 1_0mM format
                    concentration = float(f"{match.group(1)}.{match.group(2)}")
                else:
                    concentration = float(match.group(1))
                break
            except ValueError:
                continue
    
    # Scan rate
    scan_rate = None
    sr_patterns = [
        r'(\d+\.?\d*)\s*mv[\/\-_]?s',
        r'cv[_\-](\d+\.?\d*)mvps'
    ]
    
    for pattern in sr_patterns:
        match = re.search(pattern, filename_lower)
        if match:
            try:
                scan_rate = float(match.group(1))
                break
            except ValueError:
                continue
    
    return {
        'concentration': concentration,
        'scan_rate': scan_rate,
        'filename': filename
    }

def explore_palmsens_data():
    """Explore Palmsens data structure"""
    print("🔍 Exploring Palmsens Data Structure")
    print("=" * 40)
    
    data_dir = Path("Test_data/Palmsens")
    all_files = list(data_dir.rglob("*.csv"))
    
    print(f"📂 Total files found: {len(all_files)}")
    
    # Analyze file structure
    concentration_groups = defaultdict(list)
    scan_rate_groups = defaultdict(list)
    condition_combinations = defaultdict(list)
    
    for file_path in all_files:
        metadata = extract_palmsens_metadata(str(file_path))
        
        if metadata['concentration'] is not None:
            concentration_groups[metadata['concentration']].append(file_path)
        if metadata['scan_rate'] is not None:
            scan_rate_groups[metadata['scan_rate']].append(file_path)
        
        if metadata['concentration'] is not None and metadata['scan_rate'] is not None:
            key = (metadata['concentration'], metadata['scan_rate'])
            condition_combinations[key].append(file_path)
    
    print(f"\n📊 Concentrations found:")
    for conc in sorted(concentration_groups.keys()):
        print(f"   {conc} mM: {len(concentration_groups[conc])} files")
    
    print(f"\n⚡ Scan rates found:")
    for sr in sorted(scan_rate_groups.keys()):
        print(f"   {sr} mV/s: {len(scan_rate_groups[sr])} files")
    
    print(f"\n🎯 Condition combinations:")
    for (conc, sr), files in sorted(condition_combinations.items()):
        print(f"   {conc} mM @ {sr} mV/s: {len(files)} files")
    
    # Show some example filenames for each concentration
    print(f"\n📁 Example filenames by concentration:")
    for conc in sorted(concentration_groups.keys())[:5]:  # Show first 5
        files = concentration_groups[conc]
        print(f"   {conc} mM:")
        for file_path in files[:3]:  # Show first 3 examples
            print(f"      {file_path.name}")
        if len(files) > 3:
            print(f"      ... and {len(files) - 3} more")
    
    # Look at directory structure
    print(f"\n🗂️ Directory structure:")
    dirs = set()
    for file_path in all_files:
        dirs.add(file_path.parent)
    
    for dir_path in sorted(dirs):
        file_count = len(list(dir_path.glob("*.csv")))
        print(f"   {dir_path.relative_to(data_dir)}: {file_count} files")
        
        # Check if directory name contains concentration info
        dir_name = dir_path.name.lower()
        if 'mm' in dir_name:
            conc_match = re.search(r'(\d+\.?\d*)mm', dir_name)
            if conc_match:
                print(f"      → Likely concentration: {conc_match.group(1)} mM")

if __name__ == "__main__":
    explore_palmsens_data()