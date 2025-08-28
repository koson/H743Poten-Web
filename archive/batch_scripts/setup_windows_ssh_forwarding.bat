@echo off
echo 🔧 Windows WSL SSH Port Forwarding Setup
echo ==========================================

echo.
echo 📋 Step 1: Enable WSL Port Forwarding
echo Adding Windows Firewall rule for SSH port 22...

netsh advfirewall firewall add rule name="WSL SSH" dir=in action=allow protocol=TCP localport=22
if %errorlevel% neq 0 (
    echo ❌ Failed to add firewall rule. Run as Administrator.
    pause
    exit /b 1
)

echo ✅ Firewall rule added successfully.

echo.
echo 📋 Step 2: Setup Port Forwarding
echo Setting up port forwarding from Windows to WSL...

:: Get WSL IP address
for /f "tokens=2 delims=: " %%i in ('wsl hostname -I') do set WSL_IP=%%i

echo WSL IP detected: %WSL_IP%

:: Add port forwarding rule
netsh interface portproxy add v4tov4 listenport=22 listenaddress=0.0.0.0 connectport=22 connectaddress=%WSL_IP%
if %errorlevel% neq 0 (
    echo ❌ Failed to add port proxy. Run as Administrator.
    pause
    exit /b 1
)

echo ✅ Port forwarding configured.

echo.
echo 📋 Step 3: Display Connection Information
echo ==========================================

:: Get Windows IP address
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /i "IPv4"') do set WINDOWS_IP=%%i
set WINDOWS_IP=%WINDOWS_IP: =%

echo.
echo 🌐 Connection Information:
echo -------------------------
echo Windows Host IP: %WINDOWS_IP%
echo WSL IP: %WSL_IP%
echo SSH Port: 22
echo.
echo 📱 VS Code Remote Connection:
echo Use: koson@%WINDOWS_IP%
echo Or:  koson@%WSL_IP%
echo.

echo 🧪 Testing connections...
echo.

:: Test local connection
echo Testing Windows to WSL connection...
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no koson@%WSL_IP% "echo 'WSL SSH: OK'" 2>nul
if %errorlevel% equ 0 (
    echo ✅ Direct WSL connection: Working
) else (
    echo ❌ Direct WSL connection: Failed
)

echo.
echo 📋 Step 4: Additional Firewall Rules
echo Adding Windows Defender Firewall rules...

:: Add inbound rule for SSH
netsh advfirewall firewall add rule name="SSH Inbound" dir=in action=allow protocol=TCP localport=22
netsh advfirewall firewall add rule name="SSH Outbound" dir=out action=allow protocol=TCP localport=22

echo ✅ Additional firewall rules added.

echo.
echo 🔍 Current Port Forwarding Rules:
netsh interface portproxy show v4tov4

echo.
echo 📝 Connection Instructions:
echo ==========================
echo.
echo 1. From external computer, install VS Code Remote-SSH extension
echo 2. Connect to: koson@%WINDOWS_IP%
echo 3. If that fails, try: koson@%WSL_IP%
echo 4. Enter WSL password when prompted
echo.
echo 🛠️  Troubleshooting:
echo - Ensure Windows Firewall allows SSH (port 22)
echo - Check router port forwarding if connecting from outside network
echo - Verify WSL SSH service is running: wsl sudo systemctl status ssh
echo.
echo ✅ Setup completed! Try connecting from remote VS Code.
echo.
pause
