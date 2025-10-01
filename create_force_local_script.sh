#!/bin/bash

# Create proper USBTMC disconnect script
# This ensures DMM returns to local mode

echo "🔧 Creating proper USBTMC disconnect script..."

cat > ~/H743Poten/force_local_mode.sh << 'EOF'
#!/bin/bash

# Force Keysight 34461A to exit remote mode
echo "🏠 Forcing DMM to local mode..."

# Method 1: USB device reset (most reliable)
USB_DEVICE_PATH="/sys/bus/usb/devices/3-2"

if [ -d "$USB_DEVICE_PATH" ]; then
    echo "📤 Resetting USB device..."
    echo '0' | sudo tee "$USB_DEVICE_PATH/authorized" > /dev/null
    sleep 1
    echo '1' | sudo tee "$USB_DEVICE_PATH/authorized" > /dev/null
    sleep 2
    
    # Fix permissions
    sudo chmod 666 /dev/usbtmc0 2>/dev/null || echo "USBTMC device not yet available"
    sleep 1
    sudo chmod 666 /dev/usbtmc0 2>/dev/null
    
    echo "✅ USB reset complete - DMM should be in local mode"
else
    echo "⚠️ USB device path not found, trying alternative..."
    
    # Method 2: Find and reset via lsusb
    DEVICE_ID=$(lsusb | grep "2a8d:1401" | head -1 | awk '{print $2":"$4}' | sed 's/:/\//' | sed 's/0*//')
    if [ ! -z "$DEVICE_ID" ]; then
        echo "Found device at: $DEVICE_ID"
        # Reset via usb_modeswitch or similar
    fi
fi

# Method 3: Module reload as last resort
if lsmod | grep -q usbtmc; then
    echo "🔄 Reloading USBTMC module..."
    sudo modprobe -r usbtmc
    sleep 1
    sudo modprobe usbtmc
    sleep 2
    sudo chmod 666 /dev/usbtmc0 2>/dev/null
fi

echo "🎯 Local mode sequence complete!"
EOF

chmod +x ~/H743Poten/force_local_mode.sh

echo "✅ Script created at ~/H743Poten/force_local_mode.sh"