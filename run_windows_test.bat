@echo off
REM H743Poten Windows COM Port Detection and Test Script
REM Run this in Windows Command Prompt (not WSL)

echo 🔍 H743Poten - Windows COM Port Scanner
echo =====================================
echo.

echo 📡 Scanning for COM ports...
powershell -Command "Get-WmiObject -Class Win32_PnPEntity | Where-Object { $_.Caption -match 'COM\d+' } | ForEach-Object { $comNumber = [regex]::Match($_.Caption, 'COM(\d+)').Groups[1].Value; Write-Host \"COM$comNumber : $($_.Caption)\" -ForegroundColor Cyan; if ($_.Caption -match 'STM32|USB|Serial') { Write-Host '  ✅ Possible STM32 device!' -ForegroundColor Green } }"

echo.
echo 🐍 Testing Python serial connection...
python find_stm32_device.py

echo.
echo 🚀 To run your CV test:
echo    python test_cv_final.py
echo.
echo 📝 Note: Make sure to update the COM port number in your Python script
echo    based on the devices found above.

pause