#!/bin/bash

# Updated deployment script with correct IP address
# Deploy .NET application to Raspberry Pi

PI_HOST="ben@192.168.9.75"
PROJECT_DIR="/home/ben/dotnet-keysight"
LOCAL_DIR="."

echo "Building .NET application..."
dotnet build --configuration Release

echo "Publishing for ARM64 Linux..."
dotnet publish --configuration Release --runtime linux-arm64 --self-contained false --output ./bin/publish

echo "Creating project directory on Pi..."
ssh $PI_HOST "mkdir -p $PROJECT_DIR"

echo "Copying files to Pi..."
scp -r ./bin/publish/* $PI_HOST:$PROJECT_DIR/

echo "Setting execute permissions..."
ssh $PI_HOST "chmod +x $PROJECT_DIR/KeysightUSBTMCApp"

echo "Deployment complete to $PI_HOST:$PROJECT_DIR"
echo "To run: ssh $PI_HOST 'cd $PROJECT_DIR && ./KeysightUSBTMCApp'"