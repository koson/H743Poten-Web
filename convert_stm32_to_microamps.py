#!/usr/bin/env python3
"""
STM32 Unit Converter: A to µA
=============================
Convert STM32 data from Amperes (A) to microamperes (µA) 
to match Palmsens framework units
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import shutil
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class STM32UnitConverter:
    """Convert STM32 files from A to µA units"""
    
    def __init__(self):
        self.conversion_factor = 1e6  # A to µA
        self.processed_files = 0
        self.failed_files = 0
        
    def backup_original_files(self, source_dir: Path, backup_dir: Path):
        """Create backup of original files before conversion"""
        logger.info("📁 Creating backup of original files...")
        
        if backup_dir.exists():
            # Remove existing backup
            shutil.rmtree(backup_dir)
        
        # Copy entire directory
        shutil.copytree(source_dir, backup_dir)
        logger.info(f"✅ Backup created: {backup_dir}")
        
    def convert_file(self, file_path: Path) -> bool:
        """Convert a single CSV file from A to µA"""
        try:
            # Read file to check structure
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                first_line = f.readline().strip()
            
            # Check if has metadata line
            skiprows = 1 if first_line.startswith('FileName:') else 0
            
            # Read the CSV
            df = pd.read_csv(file_path, encoding='utf-8-sig', skiprows=skiprows)
            
            # Check if it has the expected columns
            if 'V' not in df.columns or 'A' not in df.columns:
                logger.debug(f"⚠️ Skipping {file_path.name} - no V,A columns")
                return False
            
            # Convert current from A to µA
            df['A'] = df['A'] * self.conversion_factor
            
            # Rename column from A to uA
            df = df.rename(columns={'A': 'uA'})
            
            # Prepare the file content
            content_lines = []
            
            # Add metadata line if it existed
            if skiprows == 1:
                content_lines.append(first_line)
            
            # Convert DataFrame to CSV string
            csv_content = df.to_csv(index=False)
            content_lines.append(csv_content)
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                if skiprows == 1:
                    f.write(content_lines[0] + '\n')
                    f.write(content_lines[1])
                else:
                    f.write(content_lines[0])
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to convert {file_path.name}: {e}")
            return False
    
    def convert_all_files(self, data_dir: Path):
        """Convert all STM32 files in directory"""
        logger.info(f"🔄 Converting files in {data_dir}")
        
        csv_files = list(data_dir.glob("*.csv"))
        total_files = len(csv_files)
        
        logger.info(f"📂 Found {total_files} CSV files to convert")
        
        # Process each file
        for i, file_path in enumerate(csv_files, 1):
            if i % 100 == 0:
                logger.info(f"   Processing file {i}/{total_files}...")
            
            if self.convert_file(file_path):
                self.processed_files += 1
            else:
                self.failed_files += 1
        
        logger.info(f"✅ Conversion completed:")
        logger.info(f"   - Successfully converted: {self.processed_files} files")
        logger.info(f"   - Failed conversions: {self.failed_files} files")
    
    def verify_conversion(self, data_dir: Path, sample_size: int = 5):
        """Verify that conversion was successful"""
        logger.info(f"🔍 Verifying conversion (checking {sample_size} random files)...")
        
        csv_files = list(data_dir.glob("*.csv"))
        
        if len(csv_files) == 0:
            logger.warning("⚠️ No CSV files found for verification")
            return
        
        # Sample random files for verification
        import random
        sample_files = random.sample(csv_files, min(sample_size, len(csv_files)))
        
        verification_results = []
        
        for file_path in sample_files:
            try:
                # Check first line for metadata
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    first_line = f.readline().strip()
                
                skiprows = 1 if first_line.startswith('FileName:') else 0
                df = pd.read_csv(file_path, encoding='utf-8-sig', skiprows=skiprows)
                
                # Check columns
                has_v = 'V' in df.columns
                has_ua = 'uA' in df.columns
                has_a = 'A' in df.columns
                
                # Check current values (should be in µA range now)
                if has_ua:
                    current_values = df['uA'].dropna()
                    current_min = current_values.min()
                    current_max = current_values.max()
                    current_range = f"{current_min:.2e} to {current_max:.2e}"
                else:
                    current_range = "N/A"
                
                verification_results.append({
                    'file': file_path.name,
                    'has_V': has_v,
                    'has_uA': has_ua,
                    'has_A': has_a,
                    'current_range': current_range,
                    'success': has_v and has_ua and not has_a
                })
                
            except Exception as e:
                verification_results.append({
                    'file': file_path.name,
                    'error': str(e),
                    'success': False
                })
        
        # Report verification results
        successful = sum(1 for r in verification_results if r.get('success', False))
        
        logger.info(f"📊 Verification Results:")
        logger.info(f"   - {successful}/{len(sample_files)} files verified successfully")
        
        for result in verification_results:
            if result.get('success', False):
                logger.info(f"   ✅ {result['file']}: V,uA columns, range {result['current_range']}")
            else:
                if 'error' in result:
                    logger.warning(f"   ❌ {result['file']}: {result['error']}")
                else:
                    logger.warning(f"   ❌ {result['file']}: Missing V,uA or still has A column")
        
        if successful == len(sample_files):
            logger.info("🎉 All sampled files converted successfully!")
        else:
            logger.warning("⚠️ Some files may not have converted correctly")
    
    def run_conversion(self):
        """Run complete conversion process"""
        logger.info("🚀 Starting STM32 A to µA Unit Conversion")
        logger.info("=" * 50)
        
        # Define directories
        data_dir = Path("test_data/raw_stm32")
        backup_dir = Path("test_data/backup_stm32_amperes")
        
        if not data_dir.exists():
            logger.error(f"❌ Data directory not found: {data_dir}")
            return
        
        # Create backup
        self.backup_original_files(data_dir, backup_dir)
        
        # Convert all files
        self.convert_all_files(data_dir)
        
        # Verify conversion
        self.verify_conversion(data_dir)
        
        logger.info("\n✅ Unit conversion completed!")
        logger.info(f"   Original files backed up to: {backup_dir}")
        logger.info("   STM32 files now use µA units compatible with Palmsens framework")

def main():
    """Main execution"""
    converter = STM32UnitConverter()
    converter.run_conversion()

if __name__ == "__main__":
    main()