#!/bin/bash

# H743 Potentiostat Application Launcher
# Standalone launcher for complete electrochemical methods application

echo "🚀 Starting H743 Potentiostat Application..."
echo "=" * 50

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH"
    echo "   Please install Python 3 and try again"
    exit 1
fi

# Check if STM32 device is connected
if [ ! -e "/dev/ttyACM0" ]; then
    echo "⚠️  Warning: STM32 device not found at /dev/ttyACM0"
    echo "   Please check if H743 Potentiostat is connected"
    echo "   Available serial devices:"
    ls -la /dev/tty* | grep -E "(ACM|USB)" || echo "   No USB/ACM devices found"
    echo ""
fi

# Check required Python packages
echo "🔍 Checking Python dependencies..."
MISSING_PACKAGES=()

python3 -c "import serial" 2>/dev/null || MISSING_PACKAGES+=("pyserial")
python3 -c "import matplotlib" 2>/dev/null || MISSING_PACKAGES+=("matplotlib")
python3 -c "import tkinter" 2>/dev/null || MISSING_PACKAGES+=("tkinter")
python3 -c "import numpy" 2>/dev/null || MISSING_PACKAGES+=("numpy")

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "❌ Missing required packages: ${MISSING_PACKAGES[*]}"
    echo "   Installing missing packages..."
    python3 -m pip install --user "${MISSING_PACKAGES[@]}"
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install packages. Please install manually:"
        echo "   pip3 install ${MISSING_PACKAGES[*]}"
        exit 1
    fi
fi

echo "✅ All dependencies satisfied"

# Set up data directory
DATA_DIR="$HOME/H743_Data"
if [ ! -d "$DATA_DIR" ]; then
    mkdir -p "$DATA_DIR"
    echo "📁 Created data directory: $DATA_DIR"
fi

# Export environment variables for data storage
export PYPIPO_DATA_DIR="$DATA_DIR"

# Kill any existing instances
pkill -f "electrochemical_methods_app.py" 2>/dev/null

echo ""
echo "🧪 Launching H743 Electrochemical Methods Application..."
echo "   Data will be saved to: $DATA_DIR"
echo "   Close the GUI window to exit the application"
echo ""

# Launch the main application
python3 electrochemical_methods_app.py

echo ""
echo "👋 H743 Application closed"
