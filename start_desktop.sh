#!/bin/bash
# H743 Potentiostat Desktop Launcher for Linux
echo "⚡ H743 Potentiostat Desktop - Linux"
echo "🕐 2-Hour Speed Build Edition"
echo "================================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found! Please install Python 3.7+"
    exit 1
fi

echo "✅ Python3 found"
echo "📦 Installing dependencies..."

# Install dependencies
python3 -m pip install --quiet --disable-pip-version-check pywebview requests flask pyserial

echo "✅ Dependencies installed"
echo "🚀 Starting H743 Potentiostat Desktop..."

# Launch desktop app
python3 desktop_app.py

echo "🛑 Desktop app closed"