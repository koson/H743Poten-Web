#!/usr/bin/env python3
"""
Test STM32 Unit Converter
=========================
Create sample test files and validate the conversion process
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from stm32_unit_converter import STM32UnitConverter

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def create_test_files():
    """Create sample test files with different unit formats"""
    test_dir = Path("test_data/raw_stm32")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("🧪 Creating test files...")
    
    # Test file 1: File with A units (needs conversion)
    voltage = np.linspace(-0.5, 0.5, 100)
    current_a = np.sin(voltage * 4) * 1e-6 + np.random.normal(0, 1e-7, 100)  # µA range but in A units
    
    df1 = pd.DataFrame({
        'Voltage (V)': voltage,
        'Current (A)': current_a,
        'Time (s)': np.linspace(0, 10, 100)
    })
    
    test_file1 = test_dir / "test_stm32_A_units.csv"
    df1.to_csv(test_file1, index=False)
    logger.info(f"📄 Created: {test_file1.name}")
    logger.info(f"   Current range: {current_a.min():.2e} to {current_a.max():.2e} A")
    
    # Test file 2: File with µA units (no conversion needed)
    current_ua = current_a * 1e6  # Convert to µA for comparison
    
    df2 = pd.DataFrame({
        'Voltage (V)': voltage,
        'Current (µA)': current_ua,
        'Time (s)': np.linspace(0, 10, 100)
    })
    
    test_file2 = test_dir / "test_stm32_uA_units.csv"
    df2.to_csv(test_file2, index=False)
    logger.info(f"📄 Created: {test_file2.name}")
    logger.info(f"   Current range: {current_ua.min():.2f} to {current_ua.max():.2f} µA")
    
    # Test file 3: More complex header format
    df3 = pd.DataFrame({
        'Potential(V)': voltage,
        'I (A)': current_a * 0.8,  # Different current pattern
        'Scan Rate': 50
    })
    
    test_file3 = test_dir / "test_stm32_I_A_format.csv"
    df3.to_csv(test_file3, index=False)
    logger.info(f"📄 Created: {test_file3.name}")
    
    return [test_file1, test_file2, test_file3]

def validate_conversion(test_files):
    """Test the conversion process and validate results"""
    logger.info("\n🔬 Testing conversion process...")
    
    # Run the converter
    converter = STM32UnitConverter()
    stats = converter.convert_batch()
    
    logger.info(f"\n📊 Conversion Results: {stats}")
    
    # Validate specific files
    output_dir = Path("test_data/converted_stm32")
    
    for test_file in test_files:
        output_file = output_dir / test_file.name
        
        if output_file.exists():
            logger.info(f"\n🔍 Validating: {test_file.name}")
            
            # Read original and converted files
            original = pd.read_csv(test_file)
            converted = pd.read_csv(output_file)
            
            logger.info(f"   Original columns: {list(original.columns)}")
            logger.info(f"   Converted columns: {list(converted.columns)}")
            
            # Check if conversion happened correctly
            for col in original.columns:
                if 'A)' in col and 'µA)' not in col:
                    # Find corresponding converted column
                    converted_col = None
                    for conv_col in converted.columns:
                        if col.replace('(A)', '').strip() in conv_col:
                            converted_col = conv_col
                            break
                    
                    if converted_col:
                        ratio = converted[converted_col].mean() / original[col].mean()
                        logger.info(f"   Conversion ratio for {col}: {ratio:.0f} (should be ~1e6)")
                        
                        if abs(ratio - 1e6) < 1e3:  # Allow small floating point errors
                            logger.info(f"   ✅ Conversion successful!")
                        else:
                            logger.warning(f"   ⚠️ Unexpected conversion ratio!")
        else:
            logger.info(f"   ⏭️ {test_file.name} not converted (likely no A units)")

def main():
    """Main test function"""
    logger.info("🧪 STM32 Unit Converter Test Suite")
    logger.info("=" * 50)
    
    # Create test files
    test_files = create_test_files()
    
    # Test conversion
    validate_conversion(test_files)
    
    logger.info("\n✅ Test complete!")
    logger.info("💡 You can now copy your real STM32 files to test_data/raw_stm32/")
    logger.info("💡 Then run: python3 stm32_unit_converter.py")

if __name__ == "__main__":
    main()