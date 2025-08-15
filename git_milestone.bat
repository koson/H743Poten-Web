@echo off
echo ==========================================
echo H743Poten Data Logging System - Milestone
echo ==========================================

cd /d "D:\GitHubRepos\__Potentiostat\poten-2025\H743Poten\H743Poten-Web"

echo Current directory: %CD%
echo.

echo Checking git status...
git status
echo.

echo Adding all files to staging...
git add .
echo.

echo Checking staged files...
git status --porcelain
echo.

echo Creating commit...
git commit -m "feat: Complete data logging system with PNG display

- Fix DataLoggingService path resolution to use absolute paths
- Implement PNG file serving for CV measurement plots
- Complete data browser with session management
- Add real-time plot display in session modals
- Fix JavaScript image loading with proper error handling
- All CV measurement features now fully functional:
  * Port selection and connection management
  * Real-time CV measurements with live plotting
  * Data logging with CSV and PNG export
  * Session browsing with plot visualization
  * File download and session management

Milestone: Data Logging System v1.0 Complete"
echo.

echo Creating tag...
git tag -a "v1.0-data-logging" -m "Data Logging System v1.0

Complete implementation of CV measurement data logging system:
- Full CV measurement workflow
- Real-time plotting with Plotly.js
- Automatic data saving (CSV + PNG)
- Session management and browsing
- PNG plot display in web interface
- File download capabilities

This milestone represents a fully functional potentiostat web interface
with comprehensive data management capabilities."
echo.

echo Git operations completed!
echo Tag created: v1.0-data-logging
echo.

pause
