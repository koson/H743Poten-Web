@echo off
REM H743Poten Web Interface Docker Development Scripts for Windows

setlocal enabledelayedexpansion

REM Colors for output (Windows compatible)
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Function to print colored output
:print_status
echo %BLUE%[H743Poten Docker]%NC% %~1
goto :eof

:print_success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

:print_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:print_error
echo %RED%[ERROR]%NC% %~1
goto :eof

REM Check if Docker is running
:check_docker
docker info >nul 2>&1
if %errorlevel% neq 0 (
    call :print_error "Docker is not running. Please start Docker Desktop."
    exit /b 1
)
call :print_success "Docker is running"
goto :eof

REM Build Docker images
:build
call :print_status "Building H743Poten Docker images..."
docker build -t h743poten-web:latest -f Dockerfile .
docker build -t h743poten-web:dev -f Dockerfile.dev .
call :print_success "Docker images built successfully"
goto :eof

REM Start development environment
:dev
call :print_status "Starting H743Poten development environment..."
docker-compose --profile dev up -d h743poten-dev
call :print_success "Development server is running at http://localhost:5000"
call :print_status "Use 'docker-compose logs -f h743poten-dev' to view logs"
goto :eof

REM Start production environment
:start
call :print_status "Starting H743Poten production environment..."
docker-compose up -d h743poten-web
call :print_success "Production server is running at http://localhost:8080"
call :print_status "Use 'docker-compose logs -f h743poten-web' to view logs"
goto :eof

REM Stop containers
:stop
call :print_status "Stopping H743Poten containers..."
docker-compose down
call :print_success "Containers stopped"
goto :eof

REM Restart containers
:restart
call :print_status "Restarting H743Poten containers..."
docker-compose restart
call :print_success "Containers restarted"
goto :eof

REM View logs
:logs
if "%~1"=="dev" (
    docker-compose logs -f h743poten-dev
) else (
    docker-compose logs -f h743poten-web
)
goto :eof

REM Run one-off development container
:run-dev
call :print_status "Running H743Poten development container..."
docker run --rm -it -p 5000:8080 -v "%cd%:/app" h743poten-web:dev
goto :eof

REM Clean up Docker resources
:clean
call :print_warning "This will remove all H743Poten Docker containers and images"
set /p confirm="Are you sure? (y/N): "
if /i "%confirm%"=="y" (
    call :print_status "Cleaning up Docker resources..."
    docker-compose down --rmi all --volumes --remove-orphans
    docker image prune -f
    call :print_success "Cleanup completed"
) else (
    call :print_status "Cleanup cancelled"
)
goto :eof

REM Shell into running container
:shell
if "%~1"=="dev" (
    call :print_status "Opening shell in development container..."
    docker-compose exec h743poten-dev /bin/bash
) else (
    call :print_status "Opening shell in production container..."
    docker-compose exec h743poten-web /bin/bash
)
goto :eof

REM Show status
:status
call :print_status "Docker container status:"
docker-compose ps
echo.
call :print_status "Recent logs:"
docker-compose logs --tail=10
goto :eof

REM Show help
:show_help
echo H743Poten Web Interface Docker Commands
echo ======================================
echo.
echo Usage: %~nx0 [command] [options]
echo.
echo Development Commands:
echo   build         Build Docker images
echo   dev           Start development environment (mock hardware)
echo   run-dev       Run one-off development container
echo.
echo Production Commands:
echo   start         Start production environment
echo.
echo Management Commands:
echo   stop          Stop all containers
echo   restart       Restart containers
echo   logs [dev]    View container logs (add 'dev' for development logs)
echo   shell [dev]   Open shell in container (add 'dev' for development container)
echo   status        Show container status and recent logs
echo   clean         Remove all Docker resources
echo.
echo Examples:
echo   %~nx0 dev                      # Start development environment
echo   %~nx0 start                    # Start production environment
echo   %~nx0 logs dev                 # View development logs
echo   %~nx0 shell                    # Open shell in production container
echo.
goto :eof

REM Main command handling
if "%~1"=="build" (
    call :check_docker
    call :build
) else if "%~1"=="dev" (
    call :check_docker
    call :dev
) else if "%~1"=="start" (
    call :check_docker
    call :start
) else if "%~1"=="stop" (
    call :stop
) else if "%~1"=="restart" (
    call :restart
) else if "%~1"=="logs" (
    call :logs %~2
) else if "%~1"=="run-dev" (
    call :check_docker
    call :build
    call :run-dev
) else if "%~1"=="shell" (
    call :shell %~2
) else if "%~1"=="status" (
    call :status
) else if "%~1"=="clean" (
    call :clean
) else if "%~1"=="help" (
    call :show_help
) else if "%~1"=="--help" (
    call :show_help
) else if "%~1"=="-h" (
    call :show_help
) else if "%~1"=="" (
    call :print_error "No command specified"
    call :show_help
    exit /b 1
) else (
    call :print_error "Unknown command: %~1"
    call :show_help
    exit /b 1
)
