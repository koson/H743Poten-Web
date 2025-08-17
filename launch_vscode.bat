@echo off
REM Launch VS Code with shell integration

REM Set up environment
SET REPO_PATH=D:\GitHubRepos\__Potentiostat\poten-2025\H743Poten\H743Poten-Web
SET SHELL_SETUP=%REPO_PATH%\shell_setup.sh

REM Check if shell_setup.sh exists
IF NOT EXIST "%SHELL_SETUP%" (
    echo Error: shell_setup.sh not found!
    exit /b 1
)

REM Convert Windows path to WSL path
wsl wslpath -a "%SHELL_SETUP%" > temp_path.txt
SET /p WSL_SETUP=<temp_path.txt
del temp_path.txt

REM Source the shell setup in WSL and start VS Code
wsl bash -ic "source %WSL_SETUP% && code %REPO_PATH%"