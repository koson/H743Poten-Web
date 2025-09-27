#!/bin/bash

PI_HOST="$1"
BRANCH="$2"
ENVIRONMENT="$3"
PI_USER="${4:-ben}"  # Default to 'ben' instead of 'pi'
PROJECT_DIR="h743poten-web"

if [ -z "$PI_HOST" ] || [ -z "$BRANCH" ]; then
    echo "Usage: $0 <pi_host> <branch> [environment] [user]"
    echo "Example: $0 192.168.9.75 development home ben"
    exit 1
fi

echo "🔄 Deploying H743 Potentiostat to Raspberry Pi"
echo "Host: $PI_HOST"
echo "Branch: $BRANCH"
echo "Environment: $ENVIRONMENT"
echo "User: $PI_USER"
echo "Project Dir: $PROJECT_DIR"

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

# Alternative deployment methods
echo "🚀 Choose deployment method:"
echo "1. SSH with key (requires key setup)"
echo "2. Manual deployment guide"
echo ""

# Try SSH first
echo "📡 Testing SSH connection..."
if ssh -o ConnectTimeout=5 -o BatchMode=yes ${PI_USER}@${PI_HOST} echo "SSH OK" 2>/dev/null; then
    echo "✅ SSH connection successful!"
    USE_SSH=true
else
    echo "❌ SSH connection failed"
    echo "💡 Manual deployment required"
    USE_SSH=false
fi

if [ "$USE_SSH" = true ]; then
    echo "🔄 Deploying via SSH..."
    
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
EOF

    if [ $? -eq 0 ]; then
        echo "🎉 Successfully deployed to $PI_HOST"
        echo "🌐 Web interface: http://$PI_HOST:8080"
        echo "📊 Check status: ssh ${PI_USER}@${PI_HOST} 'cd ${PROJECT_DIR} && python auto_dev.py status'"
    else
        echo "❌ Deployment failed"
        exit 1
    fi

else
    # Manual deployment guide
    echo ""
    echo "📋 Manual Deployment Guide"
    echo "=========================="
    echo ""
    echo "Since SSH is not working, please follow these steps:"
    echo ""
    echo "1. 🔑 Fix SSH Access (Choose one):"
    echo "   a) Copy SSH key to Pi:"
    echo "      cat ~/.ssh/id_rsa.pub"
    echo "      # Then on Pi: echo 'YOUR_KEY_HERE' >> ~/.ssh/authorized_keys"
    echo ""
    echo "   b) Enable password authentication on Pi:"
    echo "      # On Pi: sudo nano /etc/ssh/sshd_config"
    echo "      # Set: PasswordAuthentication yes"
    echo "      # Then: sudo systemctl restart ssh"
    echo ""
    echo "2. 📁 Transfer Files:"
    echo "   You can use SCP, SFTP, or USB drive to copy this project to:"
    echo "   /home/${PI_USER}/${PROJECT_DIR}/"
    echo ""
    echo "3. 🚀 Setup on Pi (run these on Pi terminal):"
    echo "   cd ~/${PROJECT_DIR}"
    echo "   python3 -m venv poten-env"
    echo "   source poten-env/bin/activate"
    echo "   pip install -r requirements.txt"
    echo "   python auto_dev.py start"
    echo ""
    echo "4. 🌐 Access Web Interface:"
    echo "   http://$PI_HOST:8080"
    echo ""
    echo "After fixing SSH, you can use: ./deploy.sh rpi-home $BRANCH"
    echo ""
    
    # Create a deployment package
    echo "📦 Creating deployment package..."
    PACKAGE_NAME="h743poten-deploy-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    tar -czf "$PACKAGE_NAME" \
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
        .
    
    echo "✅ Created deployment package: $PACKAGE_NAME"
    echo "💡 Transfer this file to your Pi and extract it"
    
fi