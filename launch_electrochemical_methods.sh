#!/bin/bash
"""
Complete Electrochemical Methods Launcher
==========================================
Launches the integrated CV, DPV, SWV application
"""

echo "🧪 H743 Potentiostat - Complete Electrochemical Methods"
echo "======================================================"

# Check Python version
python_version=$(python3 --version 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ $python_version"
else
    echo "❌ Python3 not found. Please install Python 3.6+"
    exit 1
fi

# Check required modules
echo "🔍 Checking dependencies..."

python3 -c "import tkinter" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ tkinter GUI support"
else
    echo "❌ tkinter not available. Install with: sudo apt-get install python3-tk"
    exit 1
fi

python3 -c "import matplotlib" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ matplotlib plotting support"  
else
    echo "❌ matplotlib not available. Install with: pip install matplotlib"
    exit 1
fi

python3 -c "import numpy" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ numpy scientific computing"
else
    echo "❌ numpy not available. Install with: pip install numpy"
    exit 1
fi

python3 -c "import serial" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ serial communication support"
else
    echo "⚠️  pyserial not available. Install with: pip install pyserial"
    echo "   (Serial communication will be simulated)"
fi

# Check display
if [ -z "$DISPLAY" ]; then
    echo "⚠️  No DISPLAY variable set - GUI may not work"
    echo "   For headless operation: export DISPLAY=:0"
else
    echo "✅ Display ready: $DISPLAY"
fi

echo ""
echo "🚀 Starting Complete Electrochemical Methods Application..."
echo "📊 Available methods: CV, DPV, SWV"
echo ""

# Launch the application
cd "$(dirname "$0")"
python3 electrochemical_methods_app.py

echo ""
echo "👋 Electrochemical Methods Application closed"
