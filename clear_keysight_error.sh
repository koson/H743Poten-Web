#!/bin/bash

# Script to clear Keysight 34461A DMM error status
# Usage: ./clear_keysight_error.sh

echo "Clearing Keysight 34461A Error Status..."

# Check if USBTMC device exists
if [ ! -e "/dev/usbtmc0" ]; then
    echo "Error: /dev/usbtmc0 not found. Please check USB connection."
    exit 1
fi

# Set permissions
sudo chmod 666 /dev/usbtmc0

# Clear error queue and reset DMM
echo "Clearing error queue..."
echo "*CLS" > /dev/usbtmc0

# Wait a moment
sleep 0.5

# Send reset command
echo "Resetting DMM..."
echo "*RST" > /dev/usbtmc0

# Wait for reset to complete
sleep 2

# Clear any remaining errors
echo "Final error queue clear..."
echo "*CLS" > /dev/usbtmc0

# Wait
sleep 0.5

# Check error queue
echo "Checking error queue..."
echo "SYST:ERR?" > /dev/usbtmc0
ERROR_RESPONSE=$(timeout 3 cat /dev/usbtmc0)

echo "Error Queue Response: $ERROR_RESPONSE"

# Check DMM status
echo "Checking DMM status..."
echo "*IDN?" > /dev/usbtmc0
IDN_RESPONSE=$(timeout 3 cat /dev/usbtmc0)

echo "DMM Identity: $IDN_RESPONSE"

# Set DMM to a known good state
echo "Setting DMM to voltage measurement mode..."
echo "CONF:VOLT:DC AUTO" > /dev/usbtmc0

sleep 0.5

# Enable display
echo "Enabling display..."
echo "DISP ON" > /dev/usbtmc0

sleep 0.5

# Set display text to confirm operation
echo "Setting display text..."
echo "DISP:TEXT 'READY'" > /dev/usbtmc0

sleep 1

# Clear display text
echo "Clearing display text..."
echo "DISP:TEXT:CLE" > /dev/usbtmc0

echo "Error clearing complete. Check DMM display for any remaining errors."