@echo off
REM H743Poten Web Interface - Easy Deployment Script for Windows

echo H743Poten Web Interface - Deployment Script

set command=%1
if "%command%"=="" set command=help

if "%command%"=="dev" goto start_dev
if "%command%"=="prod" goto start_prod
if "%command%"=="build" goto build_images
if "%command%"=="stop" goto stop_containers
if "%command%"=="logs" goto show_logs
if "%command%"=="status" goto show_status
if "%command%"=="test" goto run_tests
if "%command%"=="help" goto show_help
goto show_help

:start_dev
echo [INFO] Starting development environment...
docker-compose --profile dev up h743poten-dev -d
echo [SUCCESS] Development server started!
echo [INFO] Web interface available at: http://localhost:5000
echo [INFO] Use 'docker logs h743poten-dev -f' to view live logs
goto end

:start_prod
echo [INFO] Starting production environment...
docker-compose up h743poten-web -d
echo [SUCCESS] Production server started!
echo [INFO] Web interface available at: http://localhost:8080
echo [INFO] Use 'docker logs h743poten-web -f' to view live logs
goto end

:build_images
echo [INFO] Building Docker images...
docker-compose build h743poten-web
docker-compose --profile dev build h743poten-dev
echo [SUCCESS] Docker images built successfully!
goto end

:stop_containers
echo [INFO] Stopping all containers...
docker-compose --profile dev down
docker-compose down
echo [SUCCESS] All containers stopped!
goto end

:show_logs
echo [INFO] Container logs:
docker ps --filter "name=h743poten" | findstr "h743poten-dev" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Development container logs:
    docker logs h743poten-dev --tail 50
)
docker ps --filter "name=h743poten" | findstr "h743poten-web" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Production container logs:
    docker logs h743poten-web --tail 50
)
goto end

:show_status
echo [INFO] Container status:
docker ps --filter "name=h743poten"
docker ps --filter "name=h743poten" | findstr "h743poten-dev" >nul 2>&1
if not errorlevel 1 (
    echo [SUCCESS] Development server is running at http://localhost:5000
)
docker ps --filter "name=h743poten" | findstr "h743poten-web" >nul 2>&1
if not errorlevel 1 (
    echo [SUCCESS] Production server is running at http://localhost:8080
)
goto end

:run_tests
echo [INFO] Running import tests...
python test_imports.py
goto end

:show_help
echo.
echo Usage: %~nx0 [COMMAND]
echo.
echo Commands:
echo   dev         Start development environment
echo   prod        Start production environment
echo   build       Build all Docker images
echo   stop        Stop all containers
echo   logs        Show container logs
echo   status      Show container status
echo   test        Run import tests
echo   help        Show this help message
echo.
echo Examples:
echo   %~nx0 dev      # Start development server on http://localhost:5000
echo   %~nx0 prod     # Start production server on http://localhost:8080
echo   %~nx0 logs     # View application logs
echo.
goto end

:end
