@echo off
REM Simple WSL Launcher for H743Poten

echo Starting WSL for H743Poten Development...
echo.

REM วิธีที่ 1: ลอง default WSL
echo Method 1: Trying default WSL...
wsl bash -l -c "cd /mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web && pwd && ./dev.sh" 2>nul
if %errorlevel% equ 0 goto :success

REM วิธีที่ 2: ลอง Ubuntu
echo Method 2: Trying Ubuntu distribution...
wsl -d Ubuntu bash -l -c "cd /mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web && pwd && ./dev.sh" 2>nul
if %errorlevel% equ 0 goto :success

REM วิธีที่ 3: เปิด WSL ธรรมดาแล้วให้ user รันเอง
echo Method 3: Opening WSL manually...
echo.
echo Please run these commands in WSL:
echo   cd /mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web
echo   ./dev.sh
echo.
wsl
goto :eof

:success
echo ✅ WSL started successfully!
goto :eof
