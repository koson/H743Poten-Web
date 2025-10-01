#!/bin/bash

echo "═══════════════════════════════════════════════════════════"
echo "🚀 Deploying CV Web API to Raspberry Pi"
echo "═══════════════════════════════════════════════════════════"

PI_USER="ben"
PI_HOST="192.168.9.75"
DEPLOY_DIR="/home/$PI_USER/cv-web-api"

echo ""
echo "📦 Step 1: Building CV Web API..."
cd "$(dirname "$0")/CVWebApi"
dotnet restore
dotnet build -c Release

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "🛑 Step 2: Stopping existing CV Web API..."
ssh $PI_USER@$PI_HOST "pkill -f CVWebApi || true"
sleep 2

echo ""
echo "📁 Step 3: Creating deployment directory..."
ssh $PI_USER@$PI_HOST "mkdir -p $DEPLOY_DIR"

echo ""
echo "📤 Step 4: Copying files to Pi..."
scp -r bin/Release/net8.0/* $PI_USER@$PI_HOST:$DEPLOY_DIR/

echo ""
echo "🔧 Step 5: Setting permissions..."
ssh $PI_USER@$PI_HOST "chmod +x $DEPLOY_DIR/CVWebApi && sudo chmod 666 /dev/usbtmc* 2>/dev/null || true"

echo ""
echo "🚀 Step 6: Starting CV Web API..."
ssh $PI_USER@$PI_HOST "cd $DEPLOY_DIR && nohup ./CVWebApi > cv-api.log 2>&1 & echo \$! > cv-api.pid"

sleep 3

echo ""
echo "✅ Step 7: Checking service status..."
PID=$(ssh $PI_USER@$PI_HOST "cat $DEPLOY_DIR/cv-api.pid 2>/dev/null")
if [ ! -z "$PID" ]; then
    echo "✅ CV Web API is running (PID: $PID)"
    echo ""
    echo "�� Service URLs:"
    echo "   API: http://192.168.9.75:5000"
    echo "   Web: http://192.168.9.75:5000"
    echo ""
    echo "📝 Useful commands:"
    echo "   View logs: ssh $PI_USER@$PI_HOST 'tail -f $DEPLOY_DIR/cv-api.log'"
    echo "   Stop API:  ssh $PI_USER@$PI_HOST 'kill \$(cat $DEPLOY_DIR/cv-api.pid)'"
else
    echo "❌ Failed to start CV Web API"
    echo "📝 Check logs: ssh $PI_USER@$PI_HOST 'cat $DEPLOY_DIR/cv-api.log'"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "🎉 CV Web API Deployment Complete!"
echo "═══════════════════════════════════════════════════════════"
