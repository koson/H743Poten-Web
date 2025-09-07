"""
Data Preparation Script for Step 4 Cross-Instrument Calibration
Prepares PalmSens and STM32 data for upload to the web interface
"""

import os
import pandas as pd
import numpy as np
import shutil
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataPreparationManager:
    def __init__(self, base_path="d:/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web"):
        self.base_path = base_path
        self.test_data_path = os.path.join(base_path, "Test_data")
        self.output_path = os.path.join(base_path, "step4_prepared_data")
        
        # Create output directory
        os.makedirs(self.output_path, exist_ok=True)
        os.makedirs(os.path.join(self.output_path, "palmsens"), exist_ok=True)
        os.makedirs(os.path.join(self.output_path, "stm32"), exist_ok=True)
        
        self.data_summary = {
            "preparation_date": datetime.now().isoformat(),
            "palmsens_files": [],
            "stm32_files": [],
            "total_files": 0,
            "data_quality_checks": {}
        }
    
    def standardize_palmsens_data(self, input_file, output_file):
        """Standardize PalmSens data format for Step 4 upload"""
        try:
            # Read PalmSens CSV file
            df = pd.read_csv(input_file, skiprows=1)  # Skip the filename header
            
            # Check if columns exist
            if 'V' in df.columns and 'uA' in df.columns:
                # Rename columns to standard format
                df = df.rename(columns={'V': 'voltage', 'uA': 'current'})
                
                # Convert current from µA to A for consistency
                df['current'] = df['current'] * 1e-6
                
                # Add metadata columns
                df['instrument'] = 'palmsens'
                df['timestamp'] = datetime.now().isoformat()
                
                # Basic data quality checks
                voltage_range = [float(df['voltage'].min()), float(df['voltage'].max())]
                current_range = [float(df['current'].min()), float(df['current'].max())]
                data_points = len(df)
                
                # Remove any invalid data points
                df = df.dropna()
                df = df[np.isfinite(df['voltage']) & np.isfinite(df['current'])]
                
                # Save standardized file
                df[['voltage', 'current']].to_csv(output_file, index=False)
                
                # Return metadata
                return {
                    'original_file': input_file,
                    'output_file': output_file,
                    'data_points': data_points,
                    'cleaned_points': len(df),
                    'voltage_range': voltage_range,
                    'current_range': current_range,
                    'instrument': 'palmsens',
                    'status': 'success'
                }
            else:
                logger.warning(f"Invalid column format in {input_file}")
                return {'status': 'error', 'error': 'Invalid column format'}
                
        except Exception as e:
            logger.error(f"Error processing PalmSens file {input_file}: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def standardize_stm32_data(self, input_file, output_file):
        """Standardize STM32 data format for Step 4 upload"""
        try:
            # Read STM32 CSV file
            df = pd.read_csv(input_file)
            
            # Check possible column names
            voltage_col = None
            current_col = None
            
            for col in df.columns:
                if 'potential' in col.lower() or 'voltage' in col.lower() or col.lower() == 'v':
                    voltage_col = col
                elif 'current' in col.lower() or col.lower() in ['i', 'ua', 'µa']:
                    current_col = col
            
            if voltage_col and current_col:
                # Create standardized dataframe
                std_df = pd.DataFrame()
                std_df['voltage'] = df[voltage_col]
                std_df['current'] = df[current_col]
                
                # Convert current to A if it's in µA
                if df[current_col].abs().mean() > 1e-3:  # Likely in µA
                    std_df['current'] = std_df['current'] * 1e-6
                
                # Add metadata
                std_df['instrument'] = 'stm32'
                std_df['timestamp'] = datetime.now().isoformat()
                
                # Data quality checks
                voltage_range = [float(std_df['voltage'].min()), float(std_df['voltage'].max())]
                current_range = [float(std_df['current'].min()), float(std_df['current'].max())]
                data_points = len(std_df)
                
                # Clean data
                std_df = std_df.dropna()
                std_df = std_df[np.isfinite(std_df['voltage']) & np.isfinite(std_df['current'])]
                
                # Save standardized file
                std_df[['voltage', 'current']].to_csv(output_file, index=False)
                
                return {
                    'original_file': input_file,
                    'output_file': output_file,
                    'data_points': data_points,
                    'cleaned_points': len(std_df),
                    'voltage_range': voltage_range,
                    'current_range': current_range,
                    'instrument': 'stm32',
                    'status': 'success'
                }
            else:
                logger.warning(f"Could not identify voltage/current columns in {input_file}")
                return {'status': 'error', 'error': 'Could not identify voltage/current columns'}
                
        except Exception as e:
            logger.error(f"Error processing STM32 file {input_file}: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def process_palmsens_directory(self, concentration="1.0mM", scan_rate="100mVpS", max_files=10):
        """Process PalmSens files from a specific concentration directory"""
        palmsens_dir = os.path.join(self.test_data_path, "Palmsens", f"Palmsens_{concentration}")
        
        if not os.path.exists(palmsens_dir):
            logger.error(f"PalmSens directory not found: {palmsens_dir}")
            return []
        
        # Find files matching the scan rate
        matching_files = []
        for file in os.listdir(palmsens_dir):
            if file.endswith('.csv') and scan_rate in file:
                matching_files.append(os.path.join(palmsens_dir, file))
        
        # Limit number of files to process
        matching_files = matching_files[:max_files]
        
        processed_files = []
        for i, input_file in enumerate(matching_files):
            output_filename = f"palmsens_{concentration}_{scan_rate}_file_{i+1:02d}.csv"
            output_file = os.path.join(self.output_path, "palmsens", output_filename)
            
            result = self.standardize_palmsens_data(input_file, output_file)
            if result['status'] == 'success':
                processed_files.append(result)
                self.data_summary['palmsens_files'].append(result)
                logger.info(f"Processed PalmSens file: {output_filename}")
        
        return processed_files
    
    def process_stm32_directory(self, max_files=10):
        """Process STM32 files from converted directory"""
        stm32_dir = os.path.join(self.test_data_path, "converted_stm32")
        
        if not os.path.exists(stm32_dir):
            logger.error(f"STM32 directory not found: {stm32_dir}")
            return []
        
        # Find CSV files
        csv_files = [f for f in os.listdir(stm32_dir) if f.endswith('.csv')]
        csv_files = csv_files[:max_files]
        
        processed_files = []
        for i, filename in enumerate(csv_files):
            input_file = os.path.join(stm32_dir, filename)
            output_filename = f"stm32_measurement_{i+1:02d}.csv"
            output_file = os.path.join(self.output_path, "stm32", output_filename)
            
            result = self.standardize_stm32_data(input_file, output_file)
            if result['status'] == 'success':
                processed_files.append(result)
                self.data_summary['stm32_files'].append(result)
                logger.info(f"Processed STM32 file: {output_filename}")
        
        return processed_files
    
    def generate_sample_datasets(self):
        """Generate additional sample datasets for testing"""
        # Generate synthetic data for demonstration
        logger.info("Generating additional sample datasets...")
        
        # Sample concentrations and conditions
        conditions = [
            {'conc': '0.5mM', 'scan_rate': '50mV/s'},
            {'conc': '2.0mM', 'scan_rate': '200mV/s'},
            {'conc': '5.0mM', 'scan_rate': '100mV/s'}
        ]
        
        for i, condition in enumerate(conditions):
            # Generate voltage sweep
            voltage = np.linspace(-0.5, 0.5, 200)
            
            # Generate realistic CV current with some noise
            # Simplified Butler-Volmer equation
            E0 = 0.2  # Standard potential
            n = 1     # Number of electrons
            F = 96485  # Faraday constant
            R = 8.314  # Gas constant
            T = 298    # Temperature
            
            current_palmsens = []
            current_stm32 = []
            
            for v in voltage:
                # Butler-Volmer current
                eta = v - E0
                i_base = 1e-6 * (np.exp((0.5*n*F*eta)/(R*T)) - np.exp((-0.5*n*F*eta)/(R*T)))
                
                # Add concentration effect
                conc_factor = float(condition['conc'].replace('mM', '')) / 1.0
                i_base *= conc_factor
                
                # Add instrument-specific characteristics
                # PalmSens (reference) - cleaner signal
                noise_palmsens = np.random.normal(0, abs(i_base) * 0.02)
                current_palmsens.append(i_base + noise_palmsens)
                
                # STM32 - slightly more noise and systematic offset
                offset = i_base * 0.05  # 5% systematic offset
                noise_stm32 = np.random.normal(0, abs(i_base) * 0.05)
                current_stm32.append(i_base + offset + noise_stm32)
            
            # Save PalmSens sample
            palmsens_df = pd.DataFrame({
                'voltage': voltage,
                'current': current_palmsens
            })
            palmsens_file = os.path.join(self.output_path, "palmsens", f"palmsens_sample_{condition['conc']}_{i+1:02d}.csv")
            palmsens_df.to_csv(palmsens_file, index=False)
            
            # Save STM32 sample
            stm32_df = pd.DataFrame({
                'voltage': voltage,
                'current': current_stm32
            })
            stm32_file = os.path.join(self.output_path, "stm32", f"stm32_sample_{condition['conc']}_{i+1:02d}.csv")
            stm32_df.to_csv(stm32_file, index=False)
            
            # Update summary
            self.data_summary['palmsens_files'].append({
                'output_file': palmsens_file,
                'data_points': len(voltage),
                'voltage_range': [float(voltage.min()), float(voltage.max())],
                'current_range': [float(min(current_palmsens)), float(max(current_palmsens))],
                'instrument': 'palmsens',
                'type': 'synthetic',
                'condition': condition
            })
            
            self.data_summary['stm32_files'].append({
                'output_file': stm32_file,
                'data_points': len(voltage),
                'voltage_range': [float(voltage.min()), float(voltage.max())],
                'current_range': [float(min(current_stm32)), float(max(current_stm32))],
                'instrument': 'stm32',
                'type': 'synthetic',
                'condition': condition
            })
    
    def prepare_all_data(self):
        """Main function to prepare all data for Step 4 upload"""
        logger.info("Starting data preparation for Step 4...")
        
        # Process real PalmSens data
        logger.info("Processing PalmSens data...")
        palmsens_files = self.process_palmsens_directory(concentration="1.0mM", scan_rate="100mVpS", max_files=5)
        
        # Process real STM32 data  
        logger.info("Processing STM32 data...")
        stm32_files = self.process_stm32_directory(max_files=5)
        
        # Generate additional sample data
        self.generate_sample_datasets()
        
        # Update summary
        self.data_summary['total_files'] = len(self.data_summary['palmsens_files']) + len(self.data_summary['stm32_files'])
        
        # Save summary
        summary_file = os.path.join(self.output_path, "data_preparation_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(self.data_summary, f, indent=2)
        
        # Create upload instructions
        self.create_upload_instructions()
        
        logger.info(f"Data preparation completed!")
        logger.info(f"Total files prepared: {self.data_summary['total_files']}")
        logger.info(f"PalmSens files: {len(self.data_summary['palmsens_files'])}")
        logger.info(f"STM32 files: {len(self.data_summary['stm32_files'])}")
        logger.info(f"Output directory: {self.output_path}")
        
        return self.data_summary
    
    def create_upload_instructions(self):
        """Create instructions for uploading data to Step 4 interface"""
        instructions = """
# Step 4 Data Upload Instructions

## Prepared Data Location
- **PalmSens files**: `{}/palmsens/`
- **STM32 files**: `{}/stm32/`

## Upload Process

### 1. Access Step 4 Interface
- Open web browser: http://localhost:8080/step4/
- Click "Data Upload" tab

### 2. Upload PalmSens Data (Reference Instrument)
- Select "PalmSens" as instrument type
- Drag and drop files from `palmsens/` folder
- Expected files: {} files

### 3. Upload STM32 Data (Target Instrument)  
- Select "STM32 H743" as instrument type
- Drag and drop files from `stm32/` folder
- Expected files: {} files

### 4. Verify Data Upload
- Check data summary shows correct number of files
- Verify voltage and current ranges look reasonable
- Proceed to "ML Training" when ready

## Data Format
All files are standardized with columns:
- `voltage`: Voltage in Volts (V)
- `current`: Current in Amperes (A)

## Troubleshooting
- If upload fails, check file format matches CSV with voltage,current columns
- Large files (>10MB) may timeout - use smaller datasets
- Contact support if instrument type not recognized
        """.format(
            self.output_path,
            self.output_path,
            len(self.data_summary['palmsens_files']),
            len(self.data_summary['stm32_files'])
        )
        
        instructions_file = os.path.join(self.output_path, "UPLOAD_INSTRUCTIONS.md")
        with open(instructions_file, 'w') as f:
            f.write(instructions)
        
        logger.info(f"Upload instructions saved to: {instructions_file}")

def main():
    """Main execution function"""
    # Initialize data preparation manager
    manager = DataPreparationManager()
    
    # Prepare all data
    summary = manager.prepare_all_data()
    
    print("\n" + "="*60)
    print("DATA PREPARATION COMPLETED!")
    print("="*60)
    print(f"📁 Output Directory: {manager.output_path}")
    print(f"📊 Total Files: {summary['total_files']}")
    print(f"🔬 PalmSens Files: {len(summary['palmsens_files'])}")
    print(f"⚡ STM32 Files: {len(summary['stm32_files'])}")
    print("\n📋 Next Steps:")
    print("1. Open http://localhost:8080/step4/")
    print("2. Go to 'Data Upload' tab")
    print("3. Upload PalmSens files (select 'PalmSens' instrument)")
    print("4. Upload STM32 files (select 'STM32 H743' instrument)")
    print("5. Proceed to 'ML Training'")
    print("\n📖 Detailed instructions: step4_prepared_data/UPLOAD_INSTRUCTIONS.md")
    print("="*60)

if __name__ == "__main__":
    main()
