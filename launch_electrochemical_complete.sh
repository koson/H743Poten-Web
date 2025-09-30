#!/bin/bash

# H743 Potentiostat - Complete Electrochemical Methods
# Launch script with full functionality

echo "🧪 H743 Potentiostat - Complete Electrochemical Methods"
echo "======================================================="
echo "Features:"
echo "  ✅ CV (Cyclic Voltammetry) - Real-time plotting"
echo "  ✅ DPV (Differential Pulse Voltammetry)"
echo "  ✅ SWV (Square Wave Voltammetry) with Preconcentration"
echo "  📊 Progress indicators for long processes"
echo "  ⚙️  User-configurable parameters"
echo "  💾 Data export capabilities"
echo ""

# Check if STM32 is connected
if [ ! -e "/dev/ttyACM0" ]; then
    echo "⚠️  Warning: STM32 not found at /dev/ttyACM0"
    echo "    Make sure your H743 Potentiostat is connected"
    echo ""
fi

# Configure Python environment
if [ -d "poten-env" ]; then
    echo "🐍 Activating Python environment..."
    source poten-env/bin/activate
fi

# Launch the application
echo "🚀 Launching Electrochemical Methods GUI..."
echo ""

python3 electrochemical_methods_app.py

echo ""
echo "✅ Electrochemical Methods session completed"
