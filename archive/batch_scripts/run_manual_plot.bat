@echo off
echo Starting manual plot creation...
cd /d "D:\GitHubRepos\__Potentiostat\poten-2025\H743Poten\H743Poten-Web"

REM Try different Python executables
echo Trying system Python...
python create_manual_plot.py

echo.
echo Trying Python3...
python3 create_manual_plot.py

echo.
echo Trying venv Python...
".venv\Scripts\python.exe" create_manual_plot.py

echo.
echo Done. Check for output files.
pause