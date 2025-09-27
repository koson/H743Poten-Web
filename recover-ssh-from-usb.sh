#!/bin/bash

# SSH Key Recovery and Setup from USB Drive
# Usage: ./recover-ssh-from-usb.sh <pi_host> [user] [usb_mount_point]

PI_HOST="$1"
PI_USER="${2:-ben}"
USB_MOUNT="${3:-/media/*/}"  # Default USB mount points

if [ -z "$PI_HOST" ]; then
    echo "Usage: $0 <pi_host> [user] [usb_mount_point]"
    echo "Example: $0 192.168.9.75 ben"
    echo "Example: $0 192.168.9.75 ben /media/usb"
    exit 1
fi

echo "🔍 SSH Key Recovery from USB Drive"
echo "=================================="
echo "Pi Host: $PI_HOST"
echo "User: $PI_USER"
echo ""

echo "📋 Instructions for Pi Terminal:"
echo "================================"
echo ""
echo "1. 🔌 Check USB Drive:"
echo "   lsblk                    # List all drives"
echo "   ls -la /media/*/         # Check mounted USB drives"
echo "   ls -la /mnt/             # Alternative mount location"
echo ""
echo "2. 🔍 Find SSH Keys on USB:"
echo "   find /media -name '*.pub' -o -name 'id_*' 2>/dev/null"
echo "   find /mnt -name '*.pub' -o -name 'id_*' 2>/dev/null"
echo "   ls -la /media/*/ssh/     # If keys are in ssh folder"
echo "   ls -la /media/*/.ssh/    # If keys are in .ssh folder"
echo ""
echo "3. 📄 View Public Key:"
echo "   cat /media/*/id_rsa.pub  # Replace with actual path"
echo "   cat /media/*/ssh/id_rsa.pub"
echo ""
echo "4. 🔑 Setup SSH Keys:"
echo "   # Create .ssh directory if not exists"
echo "   mkdir -p ~/.ssh"
echo "   chmod 700 ~/.ssh"
echo ""
echo "   # Copy keys from USB"
echo "   cp /media/*/id_rsa ~/.ssh/"
echo "   cp /media/*/id_rsa.pub ~/.ssh/"
echo "   chmod 600 ~/.ssh/id_rsa"
echo "   chmod 644 ~/.ssh/id_rsa.pub"
echo ""
echo "   # Add public key to authorized_keys"
echo "   cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys"
echo "   chmod 600 ~/.ssh/authorized_keys"
echo ""
echo "5. 🚀 Alternative: Copy Key to This Machine"
echo "   # On Pi, show the public key:"
echo "   cat /media/*/id_rsa.pub"
echo ""
echo "   # On this machine, add to authorized_keys:"
echo "   echo 'COPIED_KEY_HERE' >> ~/.ssh/authorized_keys"
echo ""

# Test connection after setup
echo "6. ✅ Test Connection:"
echo "   # From this machine:"
echo "   ssh $PI_USER@$PI_HOST"
echo ""
echo "7. 🎯 Deploy After SSH Works:"
echo "   ./deploy.sh rpi-home development"
echo ""

echo "💡 Quick Commands to Run on Pi:"
echo "==============================="
cat << 'EOF'
# Find and list SSH keys on USB
find /media -name "*.pub" -o -name "id_*" 2>/dev/null

# Setup SSH directory
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Copy keys (adjust path as needed)
USB_KEY_PATH=$(find /media -name "id_rsa.pub" 2>/dev/null | head -1)
if [ -n "$USB_KEY_PATH" ]; then
    USB_DIR=$(dirname "$USB_KEY_PATH")
    cp "$USB_DIR/id_rsa" ~/.ssh/ 2>/dev/null
    cp "$USB_DIR/id_rsa.pub" ~/.ssh/ 2>/dev/null
    chmod 600 ~/.ssh/id_rsa
    chmod 644 ~/.ssh/id_rsa.pub
    cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
    echo "✅ SSH keys setup complete!"
    echo "📄 Your public key:"
    cat ~/.ssh/id_rsa.pub
else
    echo "❌ No SSH keys found on USB"
fi
EOF

echo ""
echo "🔄 Alternative Approaches:"
echo "========================="
echo ""
echo "A. 📤 Export Key from Pi to This Machine:"
echo "   1. On Pi: cat /media/*/id_rsa.pub"
echo "   2. Copy the output"
echo "   3. On this machine: echo 'COPIED_KEY' >> ~/.ssh/authorized_keys"
echo ""
echo "B. 📥 Import Key from Pi for Authentication:"
echo "   1. Copy private key from USB to Pi's ~/.ssh/"
echo "   2. Use that key to authenticate to this machine"
echo ""
echo "C. 🔗 Reverse SSH (Pi connects to this machine):"
echo "   1. Setup SSH server on this machine"
echo "   2. Pi initiates connection"
echo "   3. Use reverse tunnel for deployment"
echo ""

# Show current machine's SSH setup
echo "📊 Current Machine SSH Info:"
echo "============================"
echo "SSH directory: ~/.ssh/"
if [ -f ~/.ssh/id_rsa.pub ]; then
    echo "✅ SSH key exists"
    echo "Public key:"
    cat ~/.ssh/id_rsa.pub
else
    echo "❌ No SSH key found"
fi

echo ""
echo "🎯 Next Steps:"
echo "=============="
echo "1. Connect to Pi directly (keyboard/monitor/VNC)"
echo "2. Run the commands above to find and setup SSH keys"
echo "3. Test SSH connection: ssh $PI_USER@$PI_HOST"
echo "4. Deploy: ./deploy.sh rpi-home development"