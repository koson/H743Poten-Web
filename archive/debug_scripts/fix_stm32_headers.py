#!/usr/bin/env python3
"""
Fix STM32 Headers - Correct unit mislabeling in raw STM32 files
==============================================================
Problem: Files in test_data/raw_stm32 have header "V,uA" but values are in A units
Solution: Convert headers from "V,uA" to "V,A" without changing data values
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
import shutil
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class STM32HeaderFixer:
    """Fix mislabeled headers in STM32 files"""
    
    def __init__(self, input_dir: str = "test_data/raw_stm32", 
                 backup_dir: str = "test_data/backup_raw_stm32"):
        """
        Initialize header fixer
        
        Args:
            input_dir: Directory with files to fix
            backup_dir: Directory for backups
        """
        self.input_dir = Path(input_dir)
        self.backup_dir = Path(backup_dir)
        
        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'fixed_files': 0,
            'skipped_files': 0,
            'errors': 0
        }
        
        logger.info(f"🔧 STM32 Header Fixer initialized")
        logger.info(f"📁 Input directory: {self.input_dir}")
        logger.info(f"💾 Backup directory: {self.backup_dir}")
    
    def analyze_file_headers(self):
        """Analyze all CSV files to understand the header situation"""
        logger.info("🔍 Analyzing file headers...")
        
        csv_files = list(self.input_dir.glob("*.csv"))
        header_patterns = {}
        
        for csv_file in csv_files[:10]:  # Sample first 10 files
            try:
                with open(csv_file, 'r') as f:
                    lines = f.readlines()
                    if len(lines) >= 2:
                        # Get first two lines (header + first data line)
                        header = lines[1].strip() if lines[0].startswith('FileName:') else lines[0].strip()
                        first_data = lines[2].strip() if lines[0].startswith('FileName:') else lines[1].strip()
                        
                        pattern = f"{header} | Example: {first_data}"
                        header_patterns[pattern] = header_patterns.get(pattern, 0) + 1
            except Exception as e:
                logger.warning(f"Could not analyze {csv_file.name}: {e}")
        
        logger.info("📊 Header patterns found:")
        for pattern, count in header_patterns.items():
            logger.info(f"  {pattern} (Count: {count})")
    
    def needs_header_fix(self, filepath: Path) -> bool:
        """Check if file needs header correction"""
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
                
                if len(lines) < 2:
                    return False
                
                # Check if first line is FileName metadata
                start_idx = 1 if lines[0].startswith('FileName:') else 0
                header_line = lines[start_idx].strip()
                
                # Check if header has "uA" but values suggest they're in A
                if "uA" in header_line:
                    # Look at first few data lines
                    for i in range(start_idx + 1, min(start_idx + 6, len(lines))):
                        data_line = lines[i].strip()
                        if ',' in data_line:
                            try:
                                voltage_str, current_str = data_line.split(',')
                                current_val = float(current_str)
                                
                                # If current value is very small (< 1e-3), likely in A not µA
                                if abs(current_val) < 1e-3 and abs(current_val) > 0:
                                    return True
                            except ValueError:
                                continue
                
                return False
                
        except Exception as e:
            logger.warning(f"Could not check {filepath.name}: {e}")
            return False
    
    def fix_file_header(self, filepath: Path) -> bool:
        """Fix header in a single file"""
        try:
            # Read original file
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            if len(lines) < 2:
                return False
            
            # Backup original file
            backup_path = self.backup_dir / filepath.name
            shutil.copy2(filepath, backup_path)
            
            # Determine header line index
            start_idx = 1 if lines[0].startswith('FileName:') else 0
            header_line = lines[start_idx].strip()
            
            # Fix header: replace "uA" with "A"
            if "uA" in header_line:
                fixed_header = header_line.replace("uA", "A")
                lines[start_idx] = fixed_header + '\n'
                
                # Write fixed file
                with open(filepath, 'w') as f:
                    f.writelines(lines)
                
                logger.info(f"✅ Fixed: {filepath.name}")
                logger.info(f"   Before: {header_line}")
                logger.info(f"   After:  {fixed_header}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error fixing {filepath.name}: {e}")
            return False
    
    def fix_all_headers(self):
        """Fix headers in all STM32 files"""
        logger.info("🚀 Starting header fix process...")
        
        # First, analyze current situation
        self.analyze_file_headers()
        
        csv_files = list(self.input_dir.glob("*.csv"))
        self.stats['total_files'] = len(csv_files)
        
        logger.info(f"📂 Found {len(csv_files)} CSV files to process")
        
        for csv_file in csv_files:
            if self.needs_header_fix(csv_file):
                if self.fix_file_header(csv_file):
                    self.stats['fixed_files'] += 1
                else:
                    self.stats['errors'] += 1
            else:
                self.stats['skipped_files'] += 1
                logger.debug(f"⏭️ Skipping {csv_file.name} (no fix needed)")
        
        # Report results
        self.report_results()
    
    def report_results(self):
        """Generate summary report"""
        logger.info("📊 Header Fix Summary:")
        logger.info(f"   Total files: {self.stats['total_files']}")
        logger.info(f"   Fixed files: {self.stats['fixed_files']}")
        logger.info(f"   Skipped files: {self.stats['skipped_files']}")
        logger.info(f"   Errors: {self.stats['errors']}")
        
        if self.stats['fixed_files'] > 0:
            logger.info(f"💾 Original files backed up to: {self.backup_dir}")
            logger.info("✅ Header correction completed!")
        else:
            logger.info("ℹ️ No files needed header correction")

def main():
    """Main execution function"""
    fixer = STM32HeaderFixer()
    fixer.fix_all_headers()

if __name__ == "__main__":
    main()