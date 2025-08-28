@echo off
REM H743Poten Development Server Manager
REM แก้ปัญหา VS Code terminal lock

REM แสดงข้อมูลเมื่อเริ่มต้น (สำหรับ auto-start)
if "%1"=="" (
    echo ==============================================
    echo  H743Poten Development Environment
    echo ==============================================
    echo Commands:
    echo   dev start             - Start development server
    echo   dev stop              - Stop development server  
    echo   dev status            - Check server status
    echo   dev logs              - Show server logs (50 lines)
    echo   dev logs 100          - Show server logs (100 lines)
    echo   dev logs 20 ERROR     - Show logs containing "ERROR"
    echo   dev auto              - Auto-start with status check
    echo.
    echo Current Status:
    python terminal_manager.py status 2>nul
    echo ==============================================
    goto :eof
)

if "%1"=="start" (
    echo Starting H743Poten Development Server...
    python terminal_manager.py start
    goto :eof
)

if "%1"=="stop" (
    echo Stopping H743Poten Development Server...
    python terminal_manager.py stop
    goto :eof
)

if "%1"=="status" (
    python terminal_manager.py status
    goto :eof
)

if "%1"=="logs" (
    if "%2"=="" (
        python terminal_manager.py logs
    ) else if "%3"=="" (
        python terminal_manager.py logs %2
    ) else (
        python terminal_manager.py logs %2 %3
    )
    goto :eof
)

if "%1"=="auto" (
    echo H743Poten Auto-Start Mode
    echo ==========================
    python terminal_manager.py status 2>nul
    if errorlevel 1 (
        echo Server not running, starting...
        python terminal_manager.py start
    ) else (
        echo Server already running!
    )
    goto :eof
)

echo Unknown command: %1
echo Use 'dev' without parameters to see help
