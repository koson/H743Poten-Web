#!/bin/bash

# Deploy .NET API to Pi (using source files)
PI_HOST="ben@192.168.9.75"
PROJECT_DIR="/home/ben/dotnet-keysight-api"

echo "Creating project directory on Pi..."
ssh $PI_HOST "mkdir -p $PROJECT_DIR && rm -rf $PROJECT_DIR/*"

echo "Copying C# project files to Pi..."
scp Program.cs KeysightUSBTMCApp.csproj $PI_HOST:$PROJECT_DIR/

echo "Building and running on Pi..."
ssh $PI_HOST "
cd $PROJECT_DIR
export PATH=\$PATH:\$HOME/.dotnet
dotnet restore
dotnet build
echo 'Starting .NET Keysight API on port 5001...'
nohup dotnet run > keysight-dotnet.log 2>&1 &
echo 'API started. Check log with: cat $PROJECT_DIR/keysight-dotnet.log'
echo 'Access API at: http://192.168.9.75:5001/swagger'
"