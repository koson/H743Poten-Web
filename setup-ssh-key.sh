#!/bin/bash

# SSH Key Setup Helper for Raspberry Pi Deployment
# Usage: ./setup-ssh-key.sh <pi_host> [user]

PI_HOST="$1"
PI_USER="${2:-ben}"

if [ -z "$PI_HOST" ]; then
    echo "Usage: $0 <pi_host> [user]"
    echo "Example: $0 192.168.9.75 ben"
    exit 1
fi

echo "🔑 SSH Key Setup for Raspberry Pi"
echo "=================================="
echo "Host: $PI_HOST"
echo "User: $PI_USER"
echo ""

# Check if SSH key exists
if [ ! -f ~/.ssh/id_rsa.pub ]; then
    echo "❌ No SSH key found"
    echo "Creating new SSH key..."
    ssh-keygen -t rsa -b 4096 -C "$(whoami)@$(hostname)" -f ~/.ssh/id_rsa -N ""
    echo "✅ SSH key created"
fi

echo "📋 Your SSH public key:"
echo "======================="
cat ~/.ssh/id_rsa.pub
echo ""
echo "📝 Copy the key above and run this on your Raspberry Pi:"
echo "sudo mkdir -p /home/$PI_USER/.ssh"
echo "sudo chmod 700 /home/$PI_USER/.ssh"
echo "echo 'YOUR_KEY_HERE' | sudo tee -a /home/$PI_USER/.ssh/authorized_keys"
echo "sudo chmod 600 /home/$PI_USER/.ssh/authorized_keys"
echo "sudo chown -R $PI_USER:$PI_USER /home/$PI_USER/.ssh"
echo ""

# Try copying key automatically
echo "🚀 Attempting automatic key copy..."
echo "   (You may need to enter password)"

if ssh-copy-id -i ~/.ssh/id_rsa.pub ${PI_USER}@${PI_HOST} 2>/dev/null; then
    echo "✅ SSH key copied successfully!"
    echo "Testing connection..."
    
    if ssh -o ConnectTimeout=5 ${PI_USER}@${PI_HOST} echo "SSH Test OK"; then
        echo "🎉 SSH connection working!"
        echo "You can now use: ./deploy.sh rpi-home development"
    else
        echo "❌ SSH still not working"
    fi
else
    echo "⚠️  Automatic copy failed"
    echo ""
    echo "🔧 Manual setup required:"
    echo "1. Connect to your Pi directly (keyboard/monitor or VNC)"
    echo "2. Run the commands shown above"
    echo "3. Or enable password authentication temporarily:"
    echo "   sudo nano /etc/ssh/sshd_config"
    echo "   Set: PasswordAuthentication yes"
    echo "   sudo systemctl restart ssh"
fi

echo ""
echo "💡 Alternative: Use the manual deployment script"
echo "   ./scripts/deploy-to-rpi-manual.sh $PI_HOST development home $PI_USER"