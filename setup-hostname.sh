#!/bin/bash

# Hostname Resolution Setup for H743Poten Raspberry Pi
echo "🔧 Setting up hostname resolution for Raspberry Pi"
echo "=================================================="

# Pi connection details
PI_IP="192.168.9.75"
PI_HOSTNAME="rpi-home"
PI_USER="ben"

echo "Pi IP: $PI_IP"
echo "Hostname: $PI_HOSTNAME"
echo "User: $PI_USER"
echo ""

# Option 1: SSH Config setup (Recommended)
echo "🔑 Option 1: SSH Config Setup (Recommended)"
echo "============================================"

SSH_CONFIG="$HOME/.ssh/config"
mkdir -p ~/.ssh

# Check if SSH config already has rpi-home
if grep -q "Host $PI_HOSTNAME" "$SSH_CONFIG" 2>/dev/null; then
    echo "✅ SSH config already has $PI_HOSTNAME configured"
else
    echo "📝 Adding $PI_HOSTNAME to SSH config..."
    cat >> "$SSH_CONFIG" << EOF

# H743Poten Raspberry Pi
Host $PI_HOSTNAME
    HostName $PI_IP
    User $PI_USER
    Port 22
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ServerAliveInterval 30
    ServerAliveCountMax 3
EOF
    
    chmod 600 "$SSH_CONFIG"
    echo "✅ SSH config updated: $SSH_CONFIG"
fi

echo ""
echo "🌐 Now you can use these commands:"
echo "================================="
echo "ssh $PI_HOSTNAME                           # Instead of: ssh $PI_USER@$PI_IP"
echo "scp file.txt $PI_HOSTNAME:~/               # Instead of: scp file.txt $PI_USER@$PI_IP:~/"
echo "./deploy.sh $PI_HOSTNAME development       # Deploy using hostname"
echo ""

# Option 2: System hosts file (Alternative)
echo "🖥️  Option 2: System Hosts File (Alternative)"
echo "=============================================="
echo "To add to Windows hosts file manually:"
echo "1. Run as Administrator: notepad C:\\Windows\\System32\\drivers\\etc\\hosts"
echo "2. Add line: $PI_IP $PI_HOSTNAME"
echo "3. Save and close"
echo ""

# Test connection
echo "🔌 Testing connection..."
if ping -c 1 -W 3 $PI_IP > /dev/null 2>&1; then
    echo "✅ Pi is reachable at $PI_IP"
    
    # Test SSH with hostname (if config was created)
    if grep -q "Host $PI_HOSTNAME" "$SSH_CONFIG" 2>/dev/null; then
        echo "🔑 Testing SSH with hostname..."
        if ssh -o ConnectTimeout=5 $PI_HOSTNAME "echo 'SSH connection successful!'" 2>/dev/null; then
            echo "✅ SSH hostname resolution working!"
        else
            echo "⚠️  SSH hostname test failed - check SSH key setup"
            echo "Run: ssh-copy-id $PI_HOSTNAME"
        fi
    fi
else
    echo "❌ Cannot reach Pi at $PI_IP"
    echo "Please check network connection"
fi

echo ""
echo "🎯 Quick Commands Reference:"
echo "============================"
echo "SSH to Pi:        ssh $PI_HOSTNAME"
echo "Check status:     ssh $PI_HOSTNAME 'cd ~/h743poten-web && python auto_dev.py status'"
echo "View logs:        ssh $PI_HOSTNAME 'cd ~/h743poten-web && python auto_dev.py logs'"
echo "Deploy code:      ./deploy.sh $PI_HOSTNAME development"
echo "Web interface:    http://$PI_IP:8080"
echo ""
echo "✅ Hostname resolution setup complete!"