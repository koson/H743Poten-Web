#!/bin/bash

PI_HOST="$1"
BRANCH="$2"
ENVIRONMENT="$3"
PI_USER="pi"
PROJECT_DIR="h743poten-web"

if [ -z "$PI_HOST" ] || [ -z "$BRANCH" ]; then
    echo "Usage: $0 <pi_host> <branch> [environment]"
    exit 1
fi

echo "🔄 Deploying to Raspberry Pi"
echo "Host: $PI_HOST"
echo "Branch: $BRANCH"
echo "Environment: $ENVIRONMENT"

# Test connection
echo "🔌 Testing connection to $PI_HOST..."
if ! ping -c 1 -W 3 $PI_HOST > /dev/null 2>&1; then
    echo "❌ Cannot reach $PI_HOST"
    echo "Please check:"
    echo "  - Pi is powered on"
    echo "  - Network connection"
    echo "  - IP address is correct"
    exit 1
fi

echo "✅ Connection OK"

# Sync code (exclude unnecessary files)
echo "📁 Syncing code to Pi..."
rsync -av --progress --delete \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='node_modules' \
    --exclude='.env' \
    --exclude='*.log' \
    --exclude='temp_data' \
    --exclude='data_logs' \
    --exclude='poten-env' \
    --exclude='test_env' \
    --exclude='wsl_venv' \
    --exclude='.venv' \
    . ${PI_USER}@${PI_HOST}:~/${PROJECT_DIR}/

if [ $? -ne 0 ]; then
    echo "❌ Failed to sync code"
    exit 1
fi

echo "✅ Code synced successfully"

# Deploy on Pi
echo "🚀 Setting up on Raspberry Pi..."
ssh ${PI_USER}@${PI_HOST} << EOF
set -e

cd ~/${PROJECT_DIR}

echo "📦 Setting up environment..."

# Create .env file for Pi
cat > .env << EOL
# H743 Potentiostat - Raspberry Pi Configuration
NODE_ENV=production
FLASK_ENV=production

# Database
DATABASE_URL=postgresql://postgres:potentiostat@localhost:5432/potentiostat

# Serial Communication (adjust as needed)
SERIAL_PORT=/dev/ttyUSB0
SERIAL_BAUDRATE=115200

# Web Server
WEB_HOST=0.0.0.0
WEB_PORT=8080

# GPIO
GPIO_ENABLED=true

# Environment specific
DEPLOYMENT_ENV=$ENVIRONMENT
EOL

echo "🐍 Setting up Python environment..."

# Create virtual environment if not exists
if [ ! -d "poten-env" ]; then
    python3 -m venv poten-env
fi

# Activate and install dependencies
source poten-env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "🚀 Starting application..."

# Make scripts executable
chmod +x *.sh scripts/*.sh 2>/dev/null || true

# Stop existing services
python auto_dev.py stop 2>/dev/null || true
pkill -f "python.*main" 2>/dev/null || true

# Start the application
python auto_dev.py start

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 15

# Health check
if curl -s http://localhost:8080 > /dev/null; then
    echo "✅ Web service is running"
    echo "🌐 Access at: http://$PI_HOST:8080"
else
    echo "⚠️  Web service may not be ready yet"
    echo "📊 Check logs with: python auto_dev.py logs"
fi

echo "✅ Deployment complete on Raspberry Pi!"
