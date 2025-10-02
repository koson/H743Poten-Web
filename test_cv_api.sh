#!/bin/bash

echo "🔬 STM32 CV .NET API Testing Script"
echo "=================================="

# Check if .NET is installed
if ! command -v dotnet &> /dev/null; then
    echo "❌ .NET SDK not found. Installing..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Ubuntu/Debian
        sudo apt update
        sudo apt install -y dotnet-sdk-8.0
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "Please install .NET 8.0 SDK from: https://dotnet.microsoft.com/download"
        exit 1
    fi
else
    echo "✅ .NET SDK found: $(dotnet --version)"
fi

# Build the project
echo ""
echo "🔨 Building STM32 CV Web API..."
if dotnet build STM32CVWebAPI.csproj; then
    echo "✅ Build successful"
else
    echo "❌ Build failed"
    exit 1
fi

# Check STM32 connection
echo ""
echo "🔌 Checking STM32 connection..."

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux - check for STM32 device
    if ls /dev/ttyACM* 1> /dev/null 2>&1; then
        STM32_PORT=$(ls /dev/ttyACM* | head -n1)
        echo "✅ STM32 found at: $STM32_PORT"
    else
        echo "⚠️  STM32 not found. Connect STM32 to USB port."
        STM32_PORT="/dev/ttyACM0"
    fi
else
    # Windows
    echo "⚠️  Windows: Please ensure STM32 is connected to COM port"
    STM32_PORT="COM10"
fi

# Start the API server in background
echo ""
echo "🚀 Starting STM32 CV Web API server..."
echo "Port: $STM32_PORT"

# Run in background and capture PID
dotnet run --project STM32CVWebAPI.csproj &
API_PID=$!

echo "API Server PID: $API_PID"
echo "Waiting for server to start..."
sleep 5

# Test API endpoints
echo ""
echo "🧪 Testing API endpoints..."

# Check if server is running
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✅ API server is running"
    
    # Test status endpoint
    echo ""
    echo "📊 CV Status:"
    curl -s http://localhost:5000/api/cv/status | jq . || curl -s http://localhost:5000/api/cv/status
    
    # Test STM32 connection
    echo ""
    echo "🔗 STM32 Connection:"
    curl -s http://localhost:5000/api/stm32/status | jq . || curl -s http://localhost:5000/api/stm32/status
    
    echo ""
    echo "🌐 Web interface available at: http://localhost:5000"
    echo ""
    echo "Press Enter to stop the server, or Ctrl+C to keep it running..."
    read -r
    
    # Stop the server
    kill $API_PID 2>/dev/null
    echo "🛑 API server stopped"
    
else
    echo "❌ API server failed to start"
    kill $API_PID 2>/dev/null
    exit 1
fi

echo ""
echo "✅ Testing complete!"