
# Step 4 Data Upload Instructions

## Prepared Data Location
- **PalmSens files**: `d:/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web\step4_prepared_data/palmsens/`
- **STM32 files**: `d:/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web\step4_prepared_data/stm32/`

## Upload Process

### 1. Access Step 4 Interface
- Open web browser: http://localhost:8080/step4/
- Click "Data Upload" tab

### 2. Upload PalmSens Data (Reference Instrument)
- Select "PalmSens" as instrument type
- Drag and drop files from `palmsens/` folder
- Expected files: 8 files

### 3. Upload STM32 Data (Target Instrument)  
- Select "STM32 H743" as instrument type
- Drag and drop files from `stm32/` folder
- Expected files: 4 files

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
        