@echo off
cd /d "d:\GitHubRepos\__Potentiostat\poten-2025\H743Poten\H743Poten-Web"
call .venv\Scripts\activate
echo Starting Flask Server...
echo Open browser: http://localhost:8080/step4/
start /min python main.py
echo Server started in background
pause
 