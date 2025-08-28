@echo off
REM WSL Environment Checker for H743Poten

echo ==============================================
echo  WSL Environment Check
echo ==============================================

REM ตรวจสอบว่า WSL ติดตั้งหรือไม่
wsl --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ WSL is not installed or not working
    echo.
    echo 💡 To install WSL:
    echo    1. Open PowerShell as Administrator
    echo    2. Run: wsl --install
    echo    3. Restart your computer
    echo    4. Set up Ubuntu or your preferred distribution
    echo.
    goto :fallback
)

echo ✅ WSL is available
echo.

REM แสดงรายการ WSL distributions
echo WSL Distributions:
wsl --list --verbose

REM ตรวจสอบ default distribution
echo.
echo Checking available distributions...

REM ลองหา distribution ที่ใช้งานได้
set WSL_FOUND=0

REM ลอง Ubuntu ก่อน
wsl -d Ubuntu echo "Ubuntu test" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Ubuntu is available
    set WSL_DISTRO=Ubuntu
    set WSL_FOUND=1
    goto :use_wsl
)

REM ลอง default distribution
wsl echo "Default WSL test" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Default WSL distribution is working
    set WSL_DISTRO=
    set WSL_FOUND=1
    goto :use_wsl
)

REM ลอง docker-desktop ถ้ามี
wsl -d docker-desktop echo "Docker Desktop test" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Docker Desktop WSL is available
    set WSL_DISTRO=docker-desktop
    set WSL_FOUND=1
    goto :use_wsl
)

if %WSL_FOUND%==0 (
    echo ❌ No working WSL distribution found
    goto :fallback
)

:use_wsl
echo.
echo 🚀 Starting WSL environment...
echo Using distribution: %WSL_DISTRO%
echo Switching to WSL directory...

REM ใช้ distribution ที่เหมาะสม
if "%WSL_DISTRO%"=="" (
    wsl bash -c "cd '/mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web' && pwd && ls -la dev.sh 2>/dev/null && ./dev.sh || echo 'dev.sh not found or not executable'"
) else (
    wsl -d %WSL_DISTRO% bash -c "cd '/mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web' && pwd && ls -la dev.sh 2>/dev/null && ./dev.sh || echo 'dev.sh not found or not executable'"
)
goto :eof

:fallback
echo.
echo 🔄 Falling back to Windows environment...
echo Use 'dev' command instead
dev
goto :eof
