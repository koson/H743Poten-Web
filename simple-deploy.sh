#!/bin/bash

# Simple deployment script with password authentication
PI_HOST="192.168.9.75"
PI_USER="ben"
PROJECT_DIR="h743poten-web"

echo "🚀 Simple Pi Deployment"
echo "======================="
echo "Host: $PI_HOST"
echo "User: $PI_USER"
echo ""

# Test basic connection
echo "🔌 Testing connection..."
if ! ping -c 1 -W 3 $PI_HOST > /dev/null 2>&1; then
    echo "❌ Cannot reach $PI_HOST"
    exit 1
fi
echo "✅ Pi is reachable"

# Check if Pi directory exists and has files
echo "📁 Checking Pi directory..."
ssh ${PI_USER}@${PI_HOST} "ls -la ~/${PROJECT_DIR}/ 2>/dev/null | head -5 || echo 'Directory does not exist'"

echo ""
echo "📋 Manual Steps (run on Pi terminal):"
echo "====================================="
echo "1. 📁 Navigate to project:"
echo "   cd ~/${PROJECT_DIR}"
echo ""
echo "2. 🐍 Setup Python environment:"
echo "   python3 -m venv poten-env"
echo "   source poten-env/bin/activate"
echo "   pip install --upgrade pip"
echo "   pip install -r requirements.txt"
echo ""
echo "3. 🚀 Start the application:"
echo "   python auto_dev.py stop 2>/dev/null || true"
echo "   python auto_dev.py start"
echo ""
echo "4. 🌐 Check if running:"
echo "   curl http://localhost:8080"
echo "   # Or visit: http://$PI_HOST:8080"
echo ""

# Try to run basic command on Pi
echo "🔧 Testing SSH command execution..."
if ssh ${PI_USER}@${PI_HOST} "cd ~/${PROJECT_DIR} && pwd && ls -la | head -5"; then
    echo "✅ SSH command execution works"
    echo ""
    echo "🚀 Would you like to run the setup commands automatically? (y/N)"
    read -p "Enter choice: " choice
    
    if [[ "$choice" =~ ^[Yy]$ ]]; then
        echo "🔄 Running automatic setup..."
        
        ssh ${PI_USER}@${PI_HOST} << 'DEPLOY_SCRIPT'
set -e
cd ~/h743poten-web

echo "📦 Setting up Python environment..."
if [ ! -d "poten-env" ]; then
    python3 -m venv poten-env
fi

source poten-env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "🚀 Starting application..."
python auto_dev.py stop 2>/dev/null || true
python auto_dev.py start

echo "⏳ Waiting for startup..."
sleep 10

if curl -s http://localhost:8080 > /dev/null; then
    echo "✅ Application is running!"
    echo "🌐 Access at: http://192.168.9.75:8080"
else
    echo "⚠️  Application may still be starting..."
    echo "📊 Check logs: python auto_dev.py logs"
fi
DEPLOY_SCRIPT
        
        if [ $? -eq 0 ]; then
            echo "🎉 Deployment successful!"
        else
            echo "❌ Deployment had issues"
        fi
    else
        echo "💡 Follow the manual steps above"
    fi
else
    echo "❌ SSH command execution failed"
    echo "💡 Use manual deployment steps above"
fi