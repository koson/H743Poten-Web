#!/bin/bash

# SSH Server Setup Script for WSL Remote Development
# Run this script to configure SSH for VS Code remote development

echo "🔧 Setting up SSH Server for Remote Development..."

# Configure SSH for password authentication and VS Code compatibility
sudo tee /etc/ssh/sshd_config.d/vscode.conf << 'EOF'
# VS Code Remote Development Configuration
Port 22
PasswordAuthentication yes
PubkeyAuthentication yes
PermitRootLogin no
AllowUsers koson

# Security settings
Protocol 2
X11Forwarding yes
X11DisplayOffset 10
PrintMotd no
AcceptEnv LANG LC_*
Subsystem sftp /usr/lib/openssh/sftp-server

# VS Code specific settings
ClientAliveInterval 30
ClientAliveCountMax 3
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
echo "WSL IP Address: $(ip addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)"
echo "Username: $(whoami)"
echo "SSH Port: 22"
echo ""
echo "📱 VS Code Remote Connection:"
echo "1. Install 'Remote - SSH' extension in VS Code"
echo "2. Press Ctrl+Shift+P and select 'Remote-SSH: Connect to Host'"
echo "3. Enter: $(whoami)@$(ip addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)"
echo "4. Enter your password when prompted"
echo ""
echo "🔑 For key-based authentication (recommended):"
echo "ssh-keygen -t rsa -b 4096 -C 'your_email@example.com'"
echo "ssh-copy-id $(whoami)@$(ip addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)"
echo ""

# Test SSH connection locally
echo "🧪 Testing SSH connection..."
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no localhost 'echo "SSH connection successful!"' 2>/dev/null || echo "⚠️  Local SSH test failed - check configuration"

echo "✅ SSH Server setup completed!"
echo "💡 Tip: Add this to your Windows firewall if connecting from external machines"

# Generate startup script for auto-starting SSH
cat > ~/start_ssh.sh << 'EOF'
#!/bin/bash
# Auto-start SSH service in WSL
sudo systemctl start ssh
echo "SSH Server started at: $(ip addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1'):22"
EOF

chmod +x ~/start_ssh.sh
echo "📄 Created ~/start_ssh.sh for easy SSH startup"
