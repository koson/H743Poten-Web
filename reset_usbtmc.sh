#!/bin/bash

# Quick USB Reset Script for DMM

echo "🔄 Resetting USBTMC connection..."

# Method 1: Module reset
echo "📍 Step 1: Resetting USB TMC module..."
ssh ben@192.168.9.75 "
  sudo rmmod usbtmc
  sleep 2
  sudo modprobe usbtmc
  sleep 2
"

# Method 2: Check available devices
echo "📍 Step 2: Checking available devices..."
ssh ben@192.168.9.75 "ls -la /dev/usbtmc* 2>/dev/null || echo 'No USBTMC devices found'"

# Method 3: Set permissions
echo "📍 Step 3: Setting permissions..."
ssh ben@192.168.9.75 "
  for dev in /dev/usbtmc*; do
    if [ -e \"\$dev\" ]; then
      sudo chmod 666 \"\$dev\"
      echo \"✅ Set permissions for \$dev\"
    fi
  done
"

# Method 4: Test connection
echo "📍 Step 4: Testing connection..."
ssh ben@192.168.9.75 "
  for dev in /dev/usbtmc*; do
    if [ -e \"\$dev\" ]; then
      echo \"Testing \$dev...\"
      timeout 3 sh -c \"echo '*IDN?' > \$dev && cat \$dev\" 2>/dev/null && echo \"✅ \$dev works!\" || echo \"❌ \$dev timeout\"
    fi
  done
"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  If still not working:                       ║"
echo "║  1. Unplug USB cable from DMM                ║"
echo "║  2. Wait 10 seconds                          ║"
echo "║  3. Plug USB cable back in                   ║"
echo "║  4. Run this script again                    ║"
echo "╚══════════════════════════════════════════════╝"