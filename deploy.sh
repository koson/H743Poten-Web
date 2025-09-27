#!/bin/bash

TARGET="$1"
BRANCH="$2"

if [ -z "$TARGET" ] || [ -z "$BRANCH" ]; then
    echo "🚀 H743 Potentiostat Deployment"
    echo "Usage: $0 <target> <branch>"
    echo ""
    echo "Targets:"
    echo "  local      - Local Docker development"
    echo "  rpi-home   - Home Raspberry Pi"
    echo "  rpi-office - Office Raspberry Pi"
    echo "  cloud      - Cloud deployment"
    echo ""
    echo "Examples:"
    echo "  $0 local development"
    echo "  $0 rpi-home main"
    exit 1
fi

echo "🚀 Deploying H743 Potentiostat Web Interface"
echo "Target: $TARGET"
echo "Branch: $BRANCH"
echo "Time: $(date)"
echo "----------------------------------------"

# Safety check for production
if [[ "$TARGET" != "local" ]]; then
    read -p "Deploy to $TARGET? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Deployment cancelled"
        exit 1
    fi
fi

case $TARGET in
    "local")
        echo "📍 Local development deployment"
        git checkout $BRANCH
        
        # Check if poten-env exists, create if not
        if [ ! -d "poten-env" ]; then
            echo "📦 Creating virtual environment..."
            python3 -m venv poten-env
        fi
        
        # Activate environment and install dependencies
        echo "📥 Installing dependencies..."
        source poten-env/bin/activate
        pip install --upgrade pip --break-system-packages
        pip install -r requirements.txt
        
        # Start the application
        echo "🚀 Starting application..."
        python auto_dev.py stop 2>/dev/null || true
        python auto_dev.py start
        
        echo "🌐 Access at: http://localhost:8080"
        ;;
    "rpi-home")
        echo "🏠 Home Raspberry Pi deployment"
        ./scripts/deploy-to-rpi.sh 192.168.9.75 $BRANCH "home"
        ;;
    "rpi-office")
        echo "🏢 Office Raspberry Pi deployment"
        ./scripts/deploy-to-rpi.sh 192.168.2.100 $BRANCH "office"
        ;;
    "cloud")
        echo "☁️ Cloud deployment"
        ./scripts/deploy-to-cloud.sh $BRANCH
        ;;
    *)
        echo "❌ Unknown target: $TARGET"
        echo "Available targets: local, rpi-home, rpi-office, cloud"
        exit 1
        ;;
esac

echo "✅ Deployment complete!"
echo "📊 Run './scripts/health-check.sh' to verify"
