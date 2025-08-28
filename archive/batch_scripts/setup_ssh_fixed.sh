#!/bin/bash

# SSH Server Setup Script for WSL Remote Development (Fixed Version)
echo "🔧 Setting up SSH Server for Remote Development..."

# Create VS Code specific SSH configuration
sudo tee /etc/ssh/sshd_config.d/vscode.conf << 'EOF'
# VS Code Remote Development Configuration
PasswordAuthentication yes
PubkeyAuthentication yes
PermitRootLogin no
AllowUsers koson

# VS Code specific settings for better connection stability
ClientAliveInterval 30
ClientAliveCountMax 3
X11Forwarding yes
EOF

# Restart SSH service
echo "♻️  Restarting SSH service..."
sudo systemctl restart ssh

# Check SSH status
echo "📊 SSH Service Status:"
sudo systemctl status ssh --no-pager -l

# Display connection information
echo ""
echo "🌐 SSH Connection Information:"
echo "=================================="
WSL_IP=$(ip addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
USER=$(whoami)

echo "WSL IP Address: $WSL_IP"
echo "Username: $USER"  
echo "SSH Port: 22"
echo ""
echo "📱 VS Code Remote Connection Steps:"
echo "1. Install 'Remote - SSH' extension in VS Code"
echo "2. Press Ctrl+Shift+P → 'Remote-SSH: Connect to Host'"
echo "3. Enter: $USER@$WSL_IP"
echo "4. Enter password when prompted"
echo ""
echo "🔑 For SSH key authentication (recommended):"
echo "ssh-keygen -t rsa -b 4096"
echo "ssh-copy-id $USER@$WSL_IP"
echo ""

# Test SSH connection
echo "🧪 Testing SSH connection..."
if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no localhost 'echo "Connection successful!"' 2>/dev/null; then
    echo "✅ SSH connection test passed!"
else
    echo "⚠️  SSH test failed - checking service..."
    sudo systemctl status ssh --no-pager
fi

# Create WSL startup script
cat > ~/start_wsl_ssh.sh << EOF
#!/bin/bash
# WSL SSH Startup Script
echo "Starting SSH server..."
sudo systemctl start ssh
WSL_IP=\$(ip addr show eth0 | grep 'inet ' | awk '{print \$2}' | cut -d/ -f1)
echo "✅ SSH Server running at: \$WSL_IP:22"
echo "📱 VS Code connection: $USER@\$WSL_IP"
EOF

chmod +x ~/start_wsl_ssh.sh

echo ""
echo "✅ SSH Server setup completed!"
echo "📄 Created ~/start_wsl_ssh.sh for easy startup"
echo "💡 Run './start_wsl_ssh.sh' to start SSH server anytime"
