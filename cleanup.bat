@echo off
REM Terminal Cleanup Script for H743Poten Project
REM ใช้สำหรับแก้ปัญหา terminal lock และ process ค้าง

echo ========================================
echo   H743Poten Terminal Cleanup Utility
echo ========================================
echo.

REM ตรวจสอบว่ามี Python หรือไม่
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python or add it to PATH
    pause
    exit /b 1
)

REM ตรวจสอบ argument
if "%1"=="" (
    echo Running full cleanup...
    python cleanup_terminals.py
) else if "%1"=="check" (
    echo Checking current processes and ports...
    python cleanup_terminals.py check
) else if "%1"=="processes" (
    echo Cleaning up Python/Flask processes...
    python cleanup_terminals.py processes
) else if "%1"=="port" (
    if "%2"=="" (
        echo Cleaning up port 8080...
        python cleanup_terminals.py port 8080
    ) else (
        echo Cleaning up port %2...
        python cleanup_terminals.py port %2
    )
) else if "%1"=="help" (
    echo Usage:
    echo   cleanup.bat              - Full cleanup
    echo   cleanup.bat check        - Check processes and ports
    echo   cleanup.bat processes    - Kill Python/Flask processes
    echo   cleanup.bat port [PORT]  - Kill process using specific port
    echo   cleanup.bat help         - Show this help
) else (
    echo Unknown command: %1
    echo Use 'cleanup.bat help' for usage information
)

echo.
echo ========================================
echo   Cleanup completed!
echo ========================================
pause
