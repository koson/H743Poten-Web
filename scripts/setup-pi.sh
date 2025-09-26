#!/bin/bash

PI_HOST="$1"
PI_USER="pi"

if [ -z "$PI_HOST" ]; then
    echo "🥧 H743 Potentiostat - Raspberry Pi Setup"
    echo "Usage: $0 <raspberry_pi_ip>"
    echo "Example: $0 192.168.1.100"
    exit 1
fi

echo "🥧 Setting up Raspberry Pi: $PI_HOST"

# Test connection
if ! ping -c 1 -W 3 $PI_HOST > /dev/null 2>&1; then
    echo "❌ Cannot reach $PI_HOST"
    exit 1
fi

echo "✅ Connection successful"
echo "🔧 Installing prerequisites..."

ssh ${PI_USER}@${PI_HOST} << 'ENDSSH'
set -e

echo "📦 Updating packages..."
sudo apt update -y

echo "🐍 Installing Python tools..."
sudo apt install -y python3 python3-pip python3-venv git curl rsync

echo "🔌 Installing hardware tools..."
sudo apt install -y python3-serial python3-gpio i2c-tools

echo "🔄 Setting up systemd service..."
sudo tee /etc/systemd/system/h743poten-web.service > /dev/null << 'ENDSERVICE'
[Unit]
Description=H743 Potentiostat Web Interface
After=network.target

[Service]
Type=forking
User=pi
WorkingDirectory=/home/pi/h743poten-web
ExecStart=/home/pi/h743poten-web/poten-env/bin/python /home/pi/h743poten-web/auto_dev.py start
ExecStop=/home/pi/h743poten-web/poten-env/bin/python /home/pi/h743poten-web/auto_dev.py stop
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
ENDSERVICE

sudo systemctl daemon-reload
sudo systemctl enable h743poten-web.service

echo "🛡️  Setting up permissions..."
sudo usermod -a -G dialout,gpio,i2c,spi pi

echo "📁 Creating directories..."
mkdir -p /home/pi/h743poten-web/{logs,data_logs}

echo "✅ Setup complete!"
ENDSSH

echo "🎉 Raspberry Pi setup completed!"
echo "Next steps:"
echo "1. Deploy: ./deploy.sh rpi-home development"
echo "2. Check: ./scripts/health-check.sh"
