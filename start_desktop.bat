@echo off
REM H743 Potentiostat Desktop Launcher for Windows
echo ⚡ H743 Potentiostat Desktop - Windows
echo 🕐 2-Hour Speed Build Edition
echo ================================================

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.7+
    pause
    exit /b 1
)

echo ✅ Python found
echo 📦 Installing dependencies...

REM Install dependencies
python -m pip install --quiet --disable-pip-version-check pywebview requests flask pyserial

echo ✅ Dependencies installed
echo 🚀 Starting H743 Potentiostat Desktop...

REM Launch desktop app
python desktop_app.py

echo 🛑 Desktop app closed
pause