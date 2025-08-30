#!/bin/bash

# 🍓 Raspberry Pi Deployment Cleanup Script
# Clean repository for Raspberry Pi deployment

echo "🧹 Starting Raspberry Pi deployment cleanup..."

# Phase 1: Remove development artifacts
echo "📁 Removing development directories..."

# Remove analysis results and data directories
rm -rf comprehensive_pls_results_*
rm -rf plots/
rm -rf data_logs/
rm -rf logs/
rm -rf cv_data/
rm -rf sample_data/
rm -rf Test_data/
rm -rf test_files/
rm -rf validation_data/
rm -rf temp_data/
rm -rf docs/
rm -rf D/
rm -rf Ref_Project/

# Remove Python environments and cache
rm -rf venv/
rm -rf .venv/
rm -rf .venv_wsl/
rm -rf __pycache__/
rm -rf .pytest_cache/

# Phase 2: Remove legacy detection algorithms (keep only v4 and v5)
echo "🔬 Removing legacy detection algorithms..."
rm -f baseline_detector_simple.py
rm -f baseline_detector_voltage_windows.py
rm -f enhanced_detector_v3.py
rm -f enhanced_detector_v4.py
rm -f enhanced_detector_v4_improved.py

# Phase 3: Remove analysis and visualization scripts
echo "📊 Removing analysis scripts..."
rm -f create_figure_a_mean_errorbar.py
rm -f debug_figure_c_labplot.py
rm -f extract_errorbar_for_labplot.py
rm -f extract_figure_c_scores.py
rm -f extract_mean_errorbar_data.py
rm -f improved_pls_visualizer.py
rm -f project_cleanup.py
rm -f simple_cleanup.py

# Phase 4: Remove notebooks and test files
echo "📓 Removing notebooks and test files..."
rm -f Enhanced_Detector_V4_Testing.ipynb
rm -f Precision_Peak_Baseline_Analysis.ipynb
rm -f baseline_test.html
rm -f test_convert.csv
rm -f test_converted.csv
rm -f test_cv_data_ua.csv
rm -f test_original.csv

# Phase 5: Archive documentation (move to archive instead of delete)
echo "📚 Archiving documentation..."
mkdir -p archive/docs/
mv AI_PROGRESS_DAY1.md archive/docs/ 2>/dev/null || true
mv DEPLOYMENT_SUCCESS.md archive/docs/ 2>/dev/null || true
mv PLS_WORKFLOW_ANALYSIS.md archive/docs/ 2>/dev/null || true
mv PRECISION_PLS_SYSTEM_DOCUMENTATION.md archive/docs/ 2>/dev/null || true
mv PRODUCTION_DEPLOYMENT_PLAN.md archive/docs/ 2>/dev/null || true
mv SSH_REMOTE_SETUP.md archive/docs/ 2>/dev/null || true
mv SSH_TROUBLESHOOTING.md archive/docs/ 2>/dev/null || true
mv STM32_FIRMWARE_UNIT_ISSUE.md archive/docs/ 2>/dev/null || true
mv STM32_SCPI_Commands.md archive/docs/ 2>/dev/null || true
mv STM32_UNIT_CONVERSION_FIX_COMPLETE.md archive/docs/ 2>/dev/null || true
mv WORKFLOW_VISUALIZATION_COMPLETION.md archive/docs/ 2>/dev/null || true

echo "✅ Cleanup completed!"
echo "🍓 Repository is now ready for Raspberry Pi deployment"

# Show remaining files
echo ""
echo "📋 Remaining essential files:"
find . -maxdepth 1 -type f -name "*.py" | sort
echo ""
echo "📁 Remaining directories:"
find . -maxdepth 1 -type d -name "[^.]*" | sort
