@echo off
echo 🔬 STM32 CV .NET API Testing Script (Windows)
echo =============================================

REM Check if .NET is installed
dotnet --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ .NET SDK not found. Please install .NET 8.0 SDK from:
    echo https://dotnet.microsoft.com/download
    pause
    exit /b 1
) else (
    echo ✅ .NET SDK found
    dotnet --version
)

REM Build the project
echo.
echo 🔨 Building STM32 CV Web API...
dotnet build STM32CVWebAPI.csproj
if %errorlevel% neq 0 (
    echo ❌ Build failed
    pause
    exit /b 1
)
echo ✅ Build successful

REM Check STM32 connection
echo.
echo 🔌 Checking STM32 connection...
echo ⚠️  Please ensure STM32 is connected to COM port (e.g., COM10, COM6)

REM Start the API server
echo.
echo 🚀 Starting STM32 CV Web API server...
start /B dotnet run --project STM32CVWebAPI.csproj

echo Waiting for server to start...
timeout /t 5 /nobreak >nul

REM Test API endpoints
echo.
echo 🧪 Testing API endpoints...

REM Check if server is running
curl -s http://localhost:5000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ API server failed to start or curl not available
    echo Try opening http://localhost:5000 in your browser manually
) else (
    echo ✅ API server is running
    
    echo.
    echo 📊 CV Status:
    curl -s http://localhost:5000/api/cv/status
    
    echo.
    echo 🔗 STM32 Connection:
    curl -s http://localhost:5000/api/stm32/status
)

echo.
echo 🌐 Web interface available at: http://localhost:5000
echo.
echo Opening web browser...
start http://localhost:5000

echo.
echo Press any key to stop the server...
pause >nul

REM Stop the server (kill dotnet processes)
taskkill /F /IM dotnet.exe /T >nul 2>&1
echo 🛑 API server stopped

echo.
echo ✅ Testing complete!
pause