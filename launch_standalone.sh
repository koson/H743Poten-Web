#!/bin/bash
# H743 Potentiostat Standalone Launcher
# ====================================
# Standalone launcher script for the CV measurement app

echo "🚀 H743 Potentiostat Standalone App"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "standalone_cv_app.py" ]; then
    echo "❌ Error: standalone_cv_app.py not found in current directory"
    echo "💡 Please run from the H743Poten-Desktop directory"
    exit 1
fi

# Check Python version
echo "🐍 Checking Python..."
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
    echo "✅ Found Python3: $(python3 --version)"
else
    echo "❌ Python3 not found"
    exit 1
fi

# Check display (for GUI)
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo "⚠️  Warning: No display detected"
    echo "💡 Make sure you're in a graphical environment"
fi

# Check dependencies
echo "📦 Checking basic dependencies..."

# Check tkinter
if $PYTHON_CMD -c "import tkinter" 2>/dev/null; then
    echo "✅ tkinter available"
else
    echo "❌ tkinter not available"
    echo "💡 Install with: sudo apt-get install python3-tk"
fi

# Check serial module
if $PYTHON_CMD -c "import serial" 2>/dev/null; then
    echo "✅ serial module available"
else
    echo "⚠️  serial module not available (needed for STM32 communication)"
    echo "💡 Install with: pip3 install pyserial"
fi

echo ""
echo "🎯 Starting Standalone CV App..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Launch the standalone app
exec $PYTHON_CMD standalone_cv_app.py
