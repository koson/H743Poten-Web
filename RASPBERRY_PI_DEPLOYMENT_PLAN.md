# 🍓 Raspberry Pi Deployment Plan

## 📊 Current Repository Status
- **Branch**: `feature/Baseline-detect-algo-2`
- **Tags**: `v2.1-recover-from-archive`, `v2.0-article-figures`
- **Status**: Repository cluttered with development files, archives, and documentation
- **Goal**: Create clean deployment-ready version for Raspberry Pi

## 🎯 Deployment Objectives
1. **Clean Production Code**: Only essential files for running the potentiostat
2. **Raspberry Pi Optimization**: Lightweight, efficient deployment
3. **Easy Installation**: Simple setup process on Pi
4. **Documentation**: Clear deployment instructions

## 📁 File Categories Analysis

### ✅ **ESSENTIAL FOR RASPBERRY PI**
```
Core Application:
├── main.py                          # Main application entry
├── main_dev.py                      # Development server
├── auto_dev.py                      # Auto development script
├── requirements.txt                 # Python dependencies
├── src/                            # Core source code
├── static/                         # Web assets
├── templates/                      # HTML templates
├── docker-compose.yml              # Container deployment
├── Dockerfile                      # Production container
└── .env.example                    # Environment template

Peak Detection Algorithms:
├── baseline_detector_v4.py         # Primary baseline detector
├── enhanced_detector_v5.py         # Latest enhanced detector
├── terminal_manager.py             # Terminal management
└── universal_terminal_manager.py   # Cross-platform terminal

Configuration:
├── .gitignore                      # Git configuration
├── README.md                       # Project documentation
└── QUICK_START.md                  # Quick setup guide
```

### 🗑️ **TO REMOVE/ARCHIVE**
```
Development Files:
├── archive/                        # Already archived files (473 files)
├── Article_Figure_Package/         # Research publication materials
├── comprehensive_pls_results_*/    # Analysis results
├── plots/                          # Generated plots
├── data_logs/                      # Log files
├── logs/                          # More log files
├── cv_data/                       # CV test data
├── sample_data/                   # Sample datasets
├── Test_data/                     # Test datasets
├── test_files/                    # Test files
├── validation_data/               # Validation datasets
├── temp_data/                     # Temporary data
├── venv/                          # Virtual environment
├── .venv/                         # Another virtual environment
├── .venv_wsl/                     # WSL virtual environment
├── __pycache__/                   # Python cache
├── .pytest_cache/                 # Pytest cache
├── docs/                          # Documentation files
├── D/                             # Unknown directory
└── Ref_Project/                   # Reference project

Legacy/Development Scripts:
├── create_figure_a_mean_errorbar.py
├── debug_figure_c_labplot.py
├── extract_errorbar_for_labplot.py
├── extract_figure_c_scores.py
├── extract_mean_errorbar_data.py
├── improved_pls_visualizer.py
├── project_cleanup.py
├── simple_cleanup.py
├── baseline_detector_simple.py
├── baseline_detector_voltage_windows.py
├── enhanced_detector_v3.py
├── enhanced_detector_v4.py
├── enhanced_detector_v4_improved.py
├── Enhanced_Detector_V4_Testing.ipynb
├── Precision_Peak_Baseline_Analysis.ipynb
└── Various test CSV files

Documentation (Archive):
├── AI_PROGRESS_DAY1.md
├── DEPLOYMENT_SUCCESS.md
├── PLS_WORKFLOW_ANALYSIS.md
├── PRECISION_PLS_SYSTEM_DOCUMENTATION.md
├── PRODUCTION_DEPLOYMENT_PLAN.md
├── SSH_REMOTE_SETUP.md
├── SSH_TROUBLESHOOTING.md
├── STM32_FIRMWARE_UNIT_ISSUE.md
├── STM32_SCPI_Commands.md
├── STM32_UNIT_CONVERSION_FIX_COMPLETE.md
└── WORKFLOW_VISUALIZATION_COMPLETION.md
```

## 🚀 Deployment Strategy Options

### Option 1: 🎯 **Create Clean Production Branch** (Recommended)
```bash
# Create new clean branch from current state
git checkout -b production-raspberry-pi

# Remove unnecessary files and directories
# Keep only essential production files
# Commit clean version
# Tag as v3.0-raspberry-pi-ready
```

### Option 2: 📦 **Create Deployment Package**
```bash
# Create deployment directory
mkdir ../H743Poten-Pi-Deploy

# Copy only essential files
# Create deployment script
# Package for easy transfer to Pi
```

### Option 3: 🐳 **Docker-Only Deployment**
```bash
# Use existing Dockerfile
# Create Pi-optimized docker-compose
# Deploy as containers only
```

## 📋 Cleanup Actions Required

### Phase 1: Remove Development Artifacts
- [ ] Delete all analysis results directories
- [ ] Remove test data directories  
- [ ] Clean Python cache files
- [ ] Remove virtual environments
- [ ] Archive documentation files

### Phase 2: Optimize for Pi
- [ ] Update requirements.txt for Pi dependencies
- [ ] Create Pi-specific configuration
- [ ] Add ARM compatibility checks
- [ ] Optimize Docker for ARM architecture

### Phase 3: Create Deployment Package
- [ ] Create installation script
- [ ] Add Pi deployment documentation
- [ ] Test on Pi environment
- [ ] Create backup/restore procedures

## 🎛️ Raspberry Pi Specific Considerations

### Hardware Requirements
- **RAM**: Minimum 2GB (4GB recommended)
- **Storage**: 16GB+ SD card
- **Python**: Python 3.8+
- **GPIO**: Access for STM32 communication

### Dependencies to Consider
- **Serial Communication**: pyserial for STM32
- **Web Framework**: Flask/FastAPI (lightweight)
- **Data Processing**: NumPy (ARM optimized)
- **Plotting**: Matplotlib (may need optimization)

### Performance Optimizations
- **Reduce memory usage**: Optimize data structures
- **Minimize CPU load**: Efficient algorithms only
- **Storage optimization**: Compress static assets
- **Network efficiency**: Minimize web assets

## 🛠️ Next Steps
1. **Choose deployment strategy**
2. **Create clean production branch**
3. **Test locally before Pi deployment**
4. **Document Pi-specific setup**
5. **Create automated deployment script**

---
*Generated on August 29, 2025 - Preparing for Raspberry Pi deployment*
