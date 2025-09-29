#!/bin/bash
# Simple wrapper to run SCPI server with proper permissions

echo "🚀 Starting H743 SCPI Server with proper permissions..."

# Change serial port permissions
sudo chmod 666 /dev/ttyACM* 2>/dev/null || echo "⚠️  Could not change permissions"

# Add user to dialout group if not already
if ! groups koson | grep -q dialout; then
    echo "Adding koson to dialout group..."
    sudo usermod -a -G dialout koson
    echo "✅ Added to dialout. You may need to logout/login for full effect."
fi

# Show current permissions
echo "📋 Current serial port permissions:"
ls -la /dev/ttyACM* 2>/dev/null || echo "No ttyACM devices found"

# Start SCPI server
cd /home/koson/H743Poten/H743Poten-Web
python3 scpi_server_standalone.py