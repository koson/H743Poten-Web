#!/usr/bin/env python3
"""
STM32 Unit Converter
====================
Convert STM32 CV data files from A (ampere) units to µA (microampere) units.
- Detects files with A units automatically
- Converts current values by multiplying by 1e6
- Updates headers to show µA units
- Preserves original file structure and naming
"""

import pandas as pd
import numpy as np
import os
import shutil
import logging
from pathlib import Path
import re
from typing import List, Tuple, Dict, Optional
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

class STM32UnitConverter:
    """Convert STM32 CSV files from A to µA units"""
    
    def __init__(self, input_dir: str = "test_data/raw_stm32", 
                 output_dir: str = "test_data/converted_stm32"):
        """Initialize converter with input and output directories"""
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.conversion_log = []
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📁 Input directory: {self.input_dir}")
        logger.info(f"📁 Output directory: {self.output_dir}")
    
    def detect_file_units(self, filepath: str) -> Tuple[bool, List[str]]:
        """
        Detect if file has A (ampere) units that need conversion
        Returns: (needs_conversion, current_columns)
        """
        try:
            # Read first few lines to check headers
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                lines = [f.readline().strip() for _ in range(10)]
            
            # Look for current-related columns with A units
            current_columns = []
            needs_conversion = False
            
            for line in lines:
                if not line:
                    continue
                    
                # Check for headers with A units (but not µA, mA, etc.)
                # Common patterns: "Current (A)", "I (A)", "Current(A)", etc.
                if re.search(r'\bcurrent\s*\(\s*A\s*\)', line, re.IGNORECASE):
                    needs_conversion = True
                    current_columns.append(line)
                elif re.search(r'\bI\s*\(\s*A\s*\)', line, re.IGNORECASE):
                    needs_conversion = True
                    current_columns.append(line)
                elif re.search(r'\(A\)', line) and not re.search(r'[µμm]A\)', line):
                    needs_conversion = True
                    current_columns.append(line)
                    
            return needs_conversion, current_columns
            
        except Exception as e:
            logger.warning(f"⚠️ Error reading {filepath}: {e}")
            return False, []
    
    def convert_file(self, input_path: str, output_path: str) -> bool:
        """Convert a single file from A to µA units"""
        try:
            logger.info(f"🔄 Converting: {Path(input_path).name}")
            
            # Read the file
            df = pd.read_csv(input_path, encoding='utf-8-sig')
            
            # Identify current columns to convert
            current_columns = []
            for col in df.columns:
                # Look for columns that likely contain current data in A
                if re.search(r'\bcurrent\s*\(\s*A\s*\)', col, re.IGNORECASE):
                    current_columns.append(col)
                elif re.search(r'\bI\s*\(\s*A\s*\)', col, re.IGNORECASE):
                    current_columns.append(col)
                elif re.search(r'\(A\)', col) and not re.search(r'[µμm]A\)', col):
                    current_columns.append(col)
                elif 'current' in col.lower() and 'A' in col and 'µA' not in col:
                    current_columns.append(col)
            
            if not current_columns:
                logger.warning(f"⚠️ No A-unit columns found in {Path(input_path).name}")
                return False
            
            # Convert the data and headers
            conversion_info = {
                'original_file': str(input_path),
                'converted_file': str(output_path),
                'converted_columns': [],
                'data_range_before': {},
                'data_range_after': {}
            }
            
            for col in current_columns:
                # Store original data range
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                    original_min = df[col].min()
                    original_max = df[col].max()
                    conversion_info['data_range_before'][col] = {
                        'min': float(original_min),
                        'max': float(original_max)
                    }
                    
                    # Convert data: multiply by 1e6 to go from A to µA
                    df[col] = df[col] * 1e6
                    
                    # Store converted data range
                    conversion_info['data_range_after'][col] = {
                        'min': float(df[col].min()),
                        'max': float(df[col].max())
                    }
                    
                    logger.info(f"  ✅ {col}: {original_min:.2e}A → {df[col].min():.2f}µA")
                    conversion_info['converted_columns'].append(col)
            
            # Update column headers to show µA
            new_columns = []
            for col in df.columns:
                if col in current_columns:
                    # Replace (A) with (µA) or similar
                    new_col = re.sub(r'\(\s*A\s*\)', '(µA)', col)
                    new_col = re.sub(r'\bA\b', 'µA', new_col)
                    new_columns.append(new_col)
                else:
                    new_columns.append(col)
            
            df.columns = new_columns
            
            # Save converted file
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            # Log the conversion
            self.conversion_log.append(conversion_info)
            
            logger.info(f"  💾 Saved to: {Path(output_path).name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error converting {input_path}: {e}")
            return False
    
    def convert_batch(self, file_pattern: str = "*.csv") -> Dict:
        """Convert all matching files in the input directory"""
        logger.info(f"🚀 Starting batch conversion...")
        logger.info(f"🔍 Looking for {file_pattern} files in {self.input_dir}")
        
        # Find all CSV files
        csv_files = list(self.input_dir.glob(file_pattern))
        
        if not csv_files:
            logger.warning(f"⚠️ No {file_pattern} files found in {self.input_dir}")
            return {'total': 0, 'converted': 0, 'skipped': 0, 'errors': 0}
        
        logger.info(f"📊 Found {len(csv_files)} files to check")
        
        stats = {'total': len(csv_files), 'converted': 0, 'skipped': 0, 'errors': 0}
        
        for csv_file in csv_files:
            try:
                # Check if file needs conversion
                needs_conversion, current_cols = self.detect_file_units(str(csv_file))
                
                if not needs_conversion:
                    logger.info(f"⏭️ Skipping {csv_file.name} (no A units detected)")
                    stats['skipped'] += 1
                    continue
                
                # Create output filename
                output_file = self.output_dir / csv_file.name
                
                # Convert the file
                if self.convert_file(str(csv_file), str(output_file)):
                    stats['converted'] += 1
                else:
                    stats['errors'] += 1
                    
            except Exception as e:
                logger.error(f"❌ Error processing {csv_file}: {e}")
                stats['errors'] += 1
        
        # Save conversion log
        self.save_conversion_log()
        
        # Print summary
        logger.info(f"\n📊 Conversion Summary:")
        logger.info(f"  Total files: {stats['total']}")
        logger.info(f"  Converted: {stats['converted']}")
        logger.info(f"  Skipped: {stats['skipped']}")
        logger.info(f"  Errors: {stats['errors']}")
        
        return stats
    
    def save_conversion_log(self):
        """Save detailed conversion log"""
        if not self.conversion_log:
            return
            
        log_file = self.output_dir / "conversion_log.json"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump({
                'conversion_timestamp': pd.Timestamp.now().isoformat(),
                'total_conversions': len(self.conversion_log),
                'conversions': self.conversion_log
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📝 Conversion log saved: {log_file}")
    
    def copy_unchanged_files(self, file_pattern: str = "*.csv"):
        """Copy files that don't need conversion to output directory"""
        logger.info(f"📋 Copying unchanged files...")
        
        csv_files = list(self.input_dir.glob(file_pattern))
        copied = 0
        
        for csv_file in csv_files:
            needs_conversion, _ = self.detect_file_units(str(csv_file))
            
            if not needs_conversion:
                output_file = self.output_dir / csv_file.name
                shutil.copy2(csv_file, output_file)
                logger.info(f"📄 Copied: {csv_file.name}")
                copied += 1
        
        logger.info(f"📊 Copied {copied} unchanged files")
        return copied

def main():
    """Main conversion function"""
    converter = STM32UnitConverter()
    
    # Convert files that need it
    stats = converter.convert_batch()
    
    # Copy files that don't need conversion
    # converter.copy_unchanged_files()
    
    if stats['converted'] > 0:
        logger.info(f"\n✅ Conversion complete! {stats['converted']} files converted.")
        logger.info(f"📁 Converted files are in: {converter.output_dir}")
        logger.info(f"💡 You can now copy these files to your main data directories")
    else:
        logger.info(f"\n⏭️ No files needed conversion.")

if __name__ == "__main__":
    main()