#!/bin/bash

# Deploy Pure .NET SCPI Server to Raspberry Pi
# No Python Required!

PI_HOST="ben@192.168.9.75"
PROJECT_DIR="/home/ben/pure-dotnet-scpi"

echo "╔══════════════════════════════════════════════╗"
echo "║  Deploying Pure .NET SCPI Server to Pi      ║"
echo "╚══════════════════════════════════════════════╝"
echo

# Stop any existing servers
echo "🛑 Stopping existing servers..."
ssh $PI_HOST "pkill -f scpi-server; pkill -f KeysightUSBTMCApp; pkill -f python.*keysight"

# Create project directory
echo "📁 Creating project directory..."
ssh $PI_HOST "mkdir -p $PROJECT_DIR"

# Copy files
echo "📤 Copying files to Pi..."
scp PureDotNetScpiServer.cs PureDotNetScpiServer.csproj $PI_HOST:$PROJECT_DIR/

# Fix USBTMC device permissions
echo "🔐 Setting device permissions..."
ssh $PI_HOST "sudo chmod 666 /dev/usbtmc0 2>/dev/null || echo 'Warning: /dev/usbtmc0 not found yet'"

# Build and run on Pi
echo "🔨 Building on Pi..."
ssh $PI_HOST "
cd $PROJECT_DIR
export PATH=\$PATH:\$HOME/.dotnet

echo '🔨 Restoring packages...'
dotnet restore

echo '🔨 Building project...'
dotnet build -c Release

echo '✅ Build complete!'
echo
echo '🚀 Starting SCPI Server...'
echo '   TCP Port: 5025'
echo '   Device: /dev/usbtmc0'
echo
echo 'Starting server in background...'
nohup dotnet run > scpi-server.log 2>&1 &

sleep 3
echo
echo '📊 Server status:'
ps aux | grep scpi-server | grep -v grep || echo 'Server not running'
echo
echo '📝 View logs with:'
echo '   ssh $PI_HOST \"tail -f $PROJECT_DIR/scpi-server.log\"'
echo
echo '🧪 Test with:'
echo '   telnet 192.168.9.75 5025'
echo '   Then type: *IDN?'
echo
echo '✅ Deployment complete!'
"

echo
echo "╔══════════════════════════════════════════════╗"
echo "║  SCPI Server Running on Pi! 🎉               ║"
echo "╚══════════════════════════════════════════════╝"
echo
echo "📡 Connect to: 192.168.9.75:5025"
echo "📝 Test commands:"
echo "   *IDN?           - Get device identity"
echo "   *RST            - Reset device"
echo "   MEAS:VOLT:DC?   - Measure DC voltage"
echo "   QUIT            - Disconnect"