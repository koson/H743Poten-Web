@echo off
echo Stopping Flask Server...
taskkill /f /im python.exe 2>nul
echo Server stopped
pause
