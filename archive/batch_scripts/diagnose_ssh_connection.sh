#!/bin/bash

# WSL SSH Troubleshooting and Network Diagnostics
echo "🔍 WSL SSH Network Diagnostics"
echo "================================"

# Get network information
echo "📍 Network Information:"
echo "----------------------"
WSL_IP=$(hostname -I | tr -d ' ')
echo "WSL IP Address: $WSL_IP"
echo "WSL Hostname: $(hostname)"

# Check SSH service status
echo ""
echo "🔌 SSH Service Status:"
echo "---------------------"
if systemctl is-active --quiet ssh; then
    echo "✅ SSH Service: Running"
    echo "Port: $(ss -tlnp | grep :22 | awk '{print $4}')"
else
    echo "❌ SSH Service: Not Running"
    echo "🔧 Starting SSH service..."
    sudo systemctl start ssh
fi

# Test SSH locally
echo ""
echo "🧪 Local SSH Test:"
echo "------------------"
if timeout 5 ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no localhost 'echo "Local SSH: OK"' 2>/dev/null; then
    echo "✅ Local SSH connection: Working"
else
    echo "❌ Local SSH connection: Failed"
    echo "🔧 Checking SSH configuration..."
    sudo sshd -t
fi

# Check firewall and network
echo ""
echo "🛡️  Network Security:"
echo "--------------------"
if command -v ufw &> /dev/null; then
    echo "UFW Status: $(sudo ufw status | head -1)"
else
    echo "UFW: Not installed"
fi

# Check listening ports
echo ""
echo "👂 Listening Ports:"
echo "------------------"
echo "SSH Ports:"
ss -tlnp | grep :22

# Network connectivity test
echo ""
echo "🌐 Network Connectivity:"
echo "-----------------------"
echo "Default Gateway: $(ip route | grep default | awk '{print $3}')"
echo "DNS Servers: $(cat /etc/resolv.conf | grep nameserver | awk '{print $2}' | tr '\n' ' ')"

# Windows host detection
echo ""
echo "🖥️  Windows Host Detection:"
echo "---------------------------"
WINDOWS_HOST=$(ip route | grep default | awk '{print $3}')
echo "Windows Host IP: $WINDOWS_HOST"

if ping -c 1 -W 1 $WINDOWS_HOST >/dev/null 2>&1; then
    echo "✅ Windows Host: Reachable"
else
    echo "❌ Windows Host: Not reachable"
fi

# Generate connection scripts
echo ""
echo "📝 Creating Connection Scripts:"
echo "------------------------------"

# Create Windows batch file for port forwarding
cat > /mnt/c/temp/setup_ssh_portforward.bat << EOF
@echo off
echo Setting up SSH port forwarding from Windows to WSL...
echo WSL IP: $WSL_IP

REM Add firewall rule
netsh advfirewall firewall delete rule name="WSL SSH" >nul 2>&1
netsh advfirewall firewall add rule name="WSL SSH" dir=in action=allow protocol=TCP localport=22

REM Remove existing port proxy
netsh interface portproxy delete v4tov4 listenport=22 listenaddress=0.0.0.0 >nul 2>&1

REM Add port proxy
netsh interface portproxy add v4tov4 listenport=22 listenaddress=0.0.0.0 connectport=22 connectaddress=$WSL_IP

echo ✅ Port forwarding configured.
echo Connection: koson@%COMPUTERNAME%
echo Or try: koson@$WSL_IP
pause
EOF

# Create PowerShell script for advanced setup
cat > /mnt/c/temp/setup_ssh_advanced.ps1 << 'EOF'
# Advanced SSH setup for WSL remote development
Write-Host "🔧 Advanced WSL SSH Setup" -ForegroundColor Green

# Get WSL IP
$wslIP = (wsl hostname -I).Trim()
Write-Host "WSL IP: $wslIP" -ForegroundColor Yellow

# Remove existing rules
Write-Host "Cleaning existing rules..." -ForegroundColor Gray
netsh advfirewall firewall delete rule name="WSL SSH" 2>$null
netsh interface portproxy delete v4tov4 listenport=22 2>$null

# Add firewall rules
Write-Host "Adding firewall rules..." -ForegroundColor Gray
netsh advfirewall firewall add rule name="WSL SSH Inbound" dir=in action=allow protocol=TCP localport=22
netsh advfirewall firewall add rule name="WSL SSH Outbound" dir=out action=allow protocol=TCP localport=22

# Add port forwarding
Write-Host "Setting up port forwarding..." -ForegroundColor Gray
netsh interface portproxy add v4tov4 listenport=22 listenaddress=0.0.0.0 connectport=22 connectaddress=$wslIP

# Show current rules
Write-Host "`n📋 Current Port Forwarding Rules:" -ForegroundColor Green
netsh interface portproxy show v4tov4

# Get Windows IP
$windowsIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.PrefixOrigin -eq "Dhcp"}).IPAddress | Select-Object -First 1

Write-Host "`n🌐 Connection Information:" -ForegroundColor Green
Write-Host "Windows IP: $windowsIP" -ForegroundColor Yellow
Write-Host "WSL IP: $wslIP" -ForegroundColor Yellow
Write-Host "SSH Port: 22" -ForegroundColor Yellow
Write-Host "`nVS Code Remote Connection:" -ForegroundColor Cyan
Write-Host "Use: koson@$windowsIP" -ForegroundColor White
Write-Host "Backup: koson@$wslIP" -ForegroundColor White

Read-Host "`nPress Enter to continue"
EOF

echo "✅ Created connection scripts in /mnt/c/temp/"
echo ""

# Show final instructions
echo "🎯 Next Steps:"
echo "-------------"
echo "1. Run as Administrator in Windows:"
echo "   C:\\temp\\setup_ssh_portforward.bat"
echo ""
echo "2. Or run PowerShell as Administrator:"
echo "   PowerShell -ExecutionPolicy Bypass -File C:\\temp\\setup_ssh_advanced.ps1"
echo ""
echo "3. Test connection from remote VS Code:"
echo "   koson@$WINDOWS_HOST (Windows IP)"
echo "   koson@$WSL_IP (Direct WSL IP)"
echo ""
echo "🔧 If still not working, check:"
echo "- Windows Firewall settings"
echo "- Router/network firewall"
echo "- Antivirus software blocking SSH"

# Make scripts executable
chmod +x /mnt/c/temp/setup_ssh_portforward.bat
