#!/bin/bash

# SSH Key Setup for Pi using found public key
# This script helps setup SSH access using the Pi's public key

PI_HOST="192.168.9.75"
PI_USER="ben"
PI_PUBLIC_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMRi1JQDvjSpC1ZeqLoV4kpo7hQx9S4Sp14FdjfGlPML rpi-20250926"

echo "🔑 SSH Key Setup with Found Pi Key"
echo "=================================="
echo "Pi Host: $PI_HOST"
echo "Pi User: $PI_USER"
echo "Found Key: ED25519 (rpi-20250926)"
echo ""

echo "📋 The key you found is the Pi's PUBLIC key"
echo "This means Pi has the PRIVATE key pair for this public key"
echo ""

echo "🔄 Two ways to proceed:"
echo ""
echo "1. 📤 Copy OUR public key TO the Pi (Normal approach)"
echo "   - This allows us to connect TO the Pi"
echo "   - We need to add our key to Pi's authorized_keys"
echo ""
echo "2. 📥 Use Pi's private key to connect FROM Pi (Reverse)"
echo "   - Pi connects to us using its private key"
echo "   - We add Pi's public key to our authorized_keys"
echo ""

echo "🎯 Method 1: Normal SSH Connection (Recommended)"
echo "==============================================="
echo ""
echo "Commands to run on Pi terminal:"
echo "mkdir -p ~/.ssh"
echo "chmod 700 ~/.ssh"
echo "echo '$(cat ~/.ssh/id_rsa.pub)' >> ~/.ssh/authorized_keys"
echo "chmod 600 ~/.ssh/authorized_keys"
echo ""

echo "📄 Our public key to add to Pi:"
if [ -f ~/.ssh/id_rsa.pub ]; then
    cat ~/.ssh/id_rsa.pub
else
    echo "❌ No public key found. Creating one..."
    ssh-keygen -t rsa -b 4096 -C "$(whoami)@$(hostname)" -f ~/.ssh/id_rsa -N ""
    echo "✅ New key created:"
    cat ~/.ssh/id_rsa.pub
fi

echo ""
echo "🎯 Method 2: Reverse Connection (Alternative)"
echo "==========================================="
echo "Add Pi's public key to our authorized_keys:"
echo "echo '$PI_PUBLIC_KEY' >> ~/.ssh/authorized_keys"
echo "chmod 600 ~/.ssh/authorized_keys"
echo ""
echo "Then Pi can connect to us, and we can use reverse tunneling"
echo ""

echo "💡 Quick Manual Setup on Pi:"
echo "============================"
echo "# On Pi terminal, copy our public key:"
cat << EOF
mkdir -p ~/.ssh
chmod 700 ~/.ssh
cat >> ~/.ssh/authorized_keys << 'PUBKEY'
$(cat ~/.ssh/id_rsa.pub 2>/dev/null || echo "# Add your public key here")
PUBKEY
chmod 600 ~/.ssh/authorized_keys
EOF

echo ""
echo "🚀 After SSH is working:"
echo "======================="
echo "ssh $PI_USER@$PI_HOST"
echo "./deploy.sh rpi-home development"
echo ""

echo "🔧 Alternative: Use password authentication temporarily"
echo "On Pi: sudo nano /etc/ssh/sshd_config"
echo "Set: PasswordAuthentication yes"
echo "Then: sudo systemctl restart ssh"