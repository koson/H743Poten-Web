#!/bin/bash

# H743 Potentiostat Application Installer
# Sets up the application for standalone use

echo "🛠️  H743 Potentiostat Application Installer"
echo "=" * 50

APP_DIR="/home/koson/H743Poten-Desktop"
DESKTOP_FILE="$HOME/Desktop/H743-Potentiostat.desktop"
APPLICATIONS_DIR="$HOME/.local/share/applications"

# Create applications directory if it doesn't exist
mkdir -p "$APPLICATIONS_DIR"

# Copy desktop file to applications directory
cp "$APP_DIR/H743-Potentiostat.desktop" "$APPLICATIONS_DIR/"

# Also copy to desktop if it exists
if [ -d "$HOME/Desktop" ]; then
    cp "$APP_DIR/H743-Potentiostat.desktop" "$DESKTOP_FILE"
    chmod +x "$DESKTOP_FILE"
    echo "✅ Desktop shortcut created: $DESKTOP_FILE"
fi

echo "✅ Application menu entry created: $APPLICATIONS_DIR/H743-Potentiostat.desktop"

# Create a simple wrapper script in PATH
WRAPPER_SCRIPT="$HOME/.local/bin/h743-potentiostat"
mkdir -p "$HOME/.local/bin"

cat > "$WRAPPER_SCRIPT" << 'EOF'
#!/bin/bash
# H743 Potentiostat wrapper script
exec /home/koson/H743Poten-Desktop/launch_h743_app.sh "$@"
EOF

chmod +x "$WRAPPER_SCRIPT"
echo "✅ Command-line launcher created: $WRAPPER_SCRIPT"

# Add ~/.local/bin to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "" >> "$HOME/.bashrc"
    echo "# Added by H743 Potentiostat installer" >> "$HOME/.bashrc"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo "✅ Added ~/.local/bin to PATH in ~/.bashrc"
    echo "   Please run 'source ~/.bashrc' or restart your terminal"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "You can now run the H743 Potentiostat application:"
echo "  1. Click the desktop shortcut: H743-Potentiostat"
echo "  2. Find it in your applications menu"
echo "  3. Run from terminal: h743-potentiostat"
echo "  4. Or run directly: $APP_DIR/launch_h743_app.sh"
echo ""
echo "📁 Data will be saved to: $HOME/H743_Data"
