@echo off
REM Environment Switcher for H743Poten Development

echo ==============================================
echo  H743Poten Environment Switcher
echo ==============================================
echo.
echo Choose your development environment:
echo.
echo 1. Windows CMD (Recommended for beginners)
echo    - Uses Python directly on Windows
echo    - Full compatibility with dev.bat commands
echo.
echo 2. WSL (Linux environment)
echo    - Uses Python in Linux subsystem
echo    - Better for Docker and Linux development
echo.
echo 3. Auto-detect best environment
echo.

set /p choice="Enter your choice (1/2/3): "

if "%choice%"=="1" goto :cmd_env
if "%choice%"=="2" goto :wsl_env  
if "%choice%"=="3" goto :auto_env

echo Invalid choice. Using Windows CMD environment.
goto :cmd_env

:cmd_env
echo.
echo 🪟 Using Windows CMD Environment
echo ================================
dev
goto :eof

:wsl_env
echo.
echo 🐧 Using WSL Environment
echo ========================
simple_wsl.bat
goto :eof

:auto_env
echo.
echo 🔍 Auto-detecting best environment...
echo ====================================

REM ตรวจสอบ WSL
wsl --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ WSL detected, using WSL environment
    simple_wsl.bat
) else (
    echo ✅ WSL not available, using Windows CMD environment
    dev
)
goto :eof
