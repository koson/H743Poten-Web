#!/bin/bash

# 🍓 Raspberry Pi Installation Script
# Quick setup for H743 Potentiostat on Raspberry Pi

set -e  # Exit on any error

echo "🍓 H743 Potentiostat - Raspberry Pi Installation"
echo "=============================================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This script is designed for Raspberry Pi"
    echo "🤔 Continue anyway? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "❌ Installation cancelled"
        exit 1
    fi
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install Python and dependencies
echo "🐍 Installing Python dependencies..."
sudo apt install -y python3 python3-pip python3-venv git

# Install system libraries for scientific computing
echo "🔬 Installing scientific computing libraries..."
sudo apt install -y python3-numpy python3-scipy python3-matplotlib
sudo apt install -y libatlas-base-dev libopenblas-dev  # BLAS libraries for NumPy

# Create virtual environment
echo "🌐 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python packages (Pi optimized)
echo "📦 Installing Python packages..."
pip install -r requirements-pi.txt

# Make scripts executable
chmod +x auto_dev.py

# Create systemd service (optional)
echo "🔧 Do you want to create a systemd service for auto-start? (y/N)"
read -r service_response
if [[ "$service_response" =~ ^[Yy]$ ]]; then
    # Create service file
    sudo tee /etc/systemd/system/h743-potentiostat.service > /dev/null << EOF
[Unit]
Description=H743 Potentiostat Web Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python auto_dev.py start
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    # Enable service
    sudo systemctl daemon-reload
    sudo systemctl enable h743-potentiostat.service
    echo "✅ Systemd service created and enabled"
    echo "🚀 Use: sudo systemctl start h743-potentiostat to start service"
fi

# Setup GPIO permissions (if needed)
echo "🔌 Setting up GPIO permissions..."
sudo usermod -a -G gpio,i2c,spi $USER

# Test installation
echo "🧪 Testing installation..."
python3 -c "import flask, serial, numpy; print('✅ Core dependencies OK')"

echo ""
echo "🎉 Installation Complete!"
echo "========================"
echo ""
echo "🚀 Quick Start:"
echo "   source venv/bin/activate    # Activate environment"
echo "   python3 auto_dev.py start   # Start server"
echo ""
echo "🌐 Server will be available at: http://raspberry-pi-ip:8080"
echo ""
echo "📝 Configuration:"
echo "   - Copy .env.example to .env and configure settings"
echo "   - Connect STM32 device via USB/Serial"
echo "   - Ensure GPIO permissions are set"
echo ""
echo "🔧 Systemd Service (if enabled):"
echo "   sudo systemctl start h743-potentiostat    # Start"
echo "   sudo systemctl stop h743-potentiostat     # Stop"
echo "   sudo systemctl status h743-potentiostat   # Check status"
