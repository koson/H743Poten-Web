#!/bin/bash

echo "🔧 Quick SSH Remote Access Fix"
echo "=============================="

# Get network info
WSL_IP=$(hostname -I | tr -d ' ')
GATEWAY=$(ip route | grep default | awk '{print $3}')

echo "WSL IP: $WSL_IP"
echo "Gateway (Windows): $GATEWAY"

# Test SSH locally first
echo ""
echo "Testing local SSH..."
if echo "exit" | timeout 3 ssh -o ConnectTimeout=2 localhost 2>/dev/null; then
    echo "✅ Local SSH: Working"
else
    echo "❌ Local SSH: Failed"
fi

# Create Windows batch file for port forwarding
echo ""
echo "Creating Windows setup script..."

cat > /mnt/c/temp/fix_ssh_access.bat << EOF
@echo off
echo 🔧 Fixing WSL SSH Remote Access
echo ===============================

echo Adding Windows Firewall rules...
netsh advfirewall firewall delete rule name="WSL SSH" >nul 2>&1
netsh advfirewall firewall add rule name="WSL SSH" dir=in action=allow protocol=TCP localport=22

echo Setting up port forwarding...
netsh interface portproxy delete v4tov4 listenport=22 >nul 2>&1
netsh interface portproxy add v4tov4 listenport=22 listenaddress=0.0.0.0 connectport=22 connectaddress=$WSL_IP

echo.
echo ✅ Setup completed!
echo.
echo 🌐 Connection Information:
echo WSL IP: $WSL_IP
echo Windows Gateway: $GATEWAY
echo.
echo 📱 VS Code Remote Connection:
echo Try: koson@$GATEWAY
echo Or:  koson@$WSL_IP
echo.
echo 🔍 Current port forwarding:
netsh interface portproxy show v4tov4
echo.
pause
EOF

echo "✅ Created: C:\\temp\\fix_ssh_access.bat"

# Create PowerShell alternative
cat > /mnt/c/temp/fix_ssh_access.ps1 << 'EOF'
Write-Host "🔧 WSL SSH Remote Access Setup" -ForegroundColor Green

$wslIP = (wsl hostname -I).Trim()
Write-Host "WSL IP: $wslIP" -ForegroundColor Yellow

# Clean old rules
netsh advfirewall firewall delete rule name="WSL SSH" 2>$null
netsh interface portproxy delete v4tov4 listenport=22 2>$null

# Add new rules
Write-Host "Adding firewall rules..." -ForegroundColor Gray
netsh advfirewall firewall add rule name="WSL SSH" dir=in action=allow protocol=TCP localport=22

Write-Host "Setting up port forwarding..." -ForegroundColor Gray
netsh interface portproxy add v4tov4 listenport=22 listenaddress=0.0.0.0 connectport=22 connectaddress=$wslIP

$windowsIP = (Get-NetIPAddress -AddressFamily IPv4 -Type Unicast | Where-Object {$_.InterfaceAlias -notlike "*Loopback*" -and $_.InterfaceAlias -notlike "*WSL*"}).IPAddress | Select-Object -First 1

Write-Host "`n✅ Setup completed!" -ForegroundColor Green
Write-Host "`n🌐 Connection Info:" -ForegroundColor Cyan
Write-Host "Windows IP: $windowsIP" -ForegroundColor Yellow
Write-Host "WSL IP: $wslIP" -ForegroundColor Yellow
Write-Host "`nVS Code connection: koson@$windowsIP" -ForegroundColor White

Read-Host "`nPress Enter to exit"
EOF

echo "✅ Created: C:\\temp\\fix_ssh_access.ps1"

# Simple test script
cat > /mnt/c/temp/test_ssh.bat << EOF
@echo off
echo Testing SSH connection to WSL...
ssh -o ConnectTimeout=5 koson@$WSL_IP "echo 'SSH connection successful!'"
pause
EOF

echo "✅ Created: C:\\temp\\test_ssh.bat"

echo ""
echo "🎯 Next Steps:"
echo "=============="
echo "1. Run as Administrator in Windows Command Prompt:"
echo "   C:\\temp\\fix_ssh_access.bat"
echo ""
echo "2. Or run PowerShell as Administrator:"
echo "   PowerShell -ExecutionPolicy Bypass -File C:\\temp\\fix_ssh_access.ps1"
echo ""
echo "3. Test with:"
echo "   C:\\temp\\test_ssh.bat"
echo ""
echo "4. VS Code Remote SSH connection:"
echo "   koson@$GATEWAY (Windows IP)"
echo "   koson@$WSL_IP (Direct WSL)"
echo ""
echo "🔧 If still having issues:"
echo "- Check Windows Firewall is not blocking SSH"
echo "- Verify antivirus is not blocking connections"
echo "- Make sure VS Code Remote-SSH extension is installed"
echo ""
echo "📞 Current SSH status:"
sudo systemctl status ssh --no-pager -l | grep -E "(Active|Listen)"

echo ""
echo "Ready for remote connection! 🚀"
