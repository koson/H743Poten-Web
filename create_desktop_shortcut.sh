#!/bin/bash

# 🖥️ H743 Potentiostat Desktop Shortcut Creator
# Creates desktop shortcut for click-to-run functionality

echo "🚀 Creating H743 Potentiostat Desktop Shortcut"
echo "=============================================="

# Get current directory
CURRENT_DIR="/home/koson/H743Poten-Desktop"
DESKTOP_DIR="$HOME/Desktop"

# Create desktop entry file
cat > "$DESKTOP_DIR/H743Poten.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=H743 Potentiostat
Comment=STM32 H743 Electrochemical Measurement System - CV, DPV, SWV
Exec=$CURRENT_DIR/start_desktop.sh
Icon=$CURRENT_DIR/static/img/potentiostat.png
Path=$CURRENT_DIR
Terminal=false
Categories=Science;Chemistry;Education;
StartupNotify=true
Keywords=potentiostat;electrochemistry;CV;DPV;SWV;STM32;
EOF

# Make desktop file executable
chmod +x "$DESKTOP_DIR/H743Poten.desktop"

# Create icon if doesn't exist
if [ ! -f "$CURRENT_DIR/static/img/potentiostat.png" ]; then
    mkdir -p "$CURRENT_DIR/static/img"
    
    # Create simple SVG icon and convert to PNG (if available)
    cat > "$CURRENT_DIR/static/img/potentiostat.svg" << 'SVGEOF'
<svg width="64" height="64" xmlns="http://www.w3.org/2000/svg">
  <rect width="64" height="64" fill="#1e3a8a" rx="8"/>
  <circle cx="32" cy="20" r="8" fill="#fbbf24"/>
  <rect x="28" y="32" width="8" height="24" fill="#10b981"/>
  <text x="32" y="52" text-anchor="middle" fill="white" font-size="8">H743</text>
</svg>
SVGEOF

    # Try to convert SVG to PNG if available
    if command -v convert &> /dev/null; then
        convert "$CURRENT_DIR/static/img/potentiostat.svg" "$CURRENT_DIR/static/img/potentiostat.png"
    elif command -v rsvg-convert &> /dev/null; then
        rsvg-convert -h 64 -w 64 "$CURRENT_DIR/static/img/potentiostat.svg" > "$CURRENT_DIR/static/img/potentiostat.png"
    else
        echo "⚠️  Icon conversion tools not available - using SVG"
        sed -i 's/potentiostat.png/potentiostat.svg/' "$DESKTOP_DIR/H743Poten.desktop"
    fi
fi

# Trust desktop file (for some Linux distributions)
if command -v gio &> /dev/null; then
    gio set "$DESKTOP_DIR/H743Poten.desktop" metadata::trusted true
fi

echo "✅ Desktop shortcut created successfully!"
echo "📍 Location: $DESKTOP_DIR/H743Poten.desktop"
echo "🖱️  Double-click 'H743 Potentiostat' on desktop to launch"
echo ""
echo "🎯 Features available:"
echo "   - Cyclic Voltammetry (CV)"
echo "   - Differential Pulse Voltammetry (DPV)" 
echo "   - Square Wave Voltammetry (SWV)"
echo "   - STM32 H743 Auto-detection"
echo "   - Real-time data visualization"
echo "   - Data export (CSV, JSON, PNG)"
echo ""
echo "🎉 Ready for electrochemical analysis!"