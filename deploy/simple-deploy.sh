#!/bin/bash
# H743Poten Simple Deployment Script
# Two-phase deployment: Phase 1 (root), Phase 2 (user)

set -e

USER_ACCOUNT="potentiostat"
INSTALL_DIR="/home/$USER_ACCOUNT/H743Poten-Web"
DATA_DIR="/home/$USER_ACCOUNT/poten-data"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

if [ "$(whoami)" != "root" ]; then
    error "This script must be run as root"
    error "Run: sudo ./deploy/simple-deploy.sh"
    exit 1
fi

echo "🍓 H743Poten Simple Deployment (Phase 1: System Setup)"
echo "====================================================="

# Update system
info "Updating system packages..."
apt update && apt upgrade -y

# Install dependencies
info "Installing system dependencies..."
apt install -y python3 python3-pip python3-venv git nginx sqlite3

# Enable hardware interfaces
info "Enabling hardware interfaces..."
if command -v raspi-config >/dev/null; then
    raspi-config nonint do_spi 0
    raspi-config nonint do_i2c 0
fi

# Create user if needed
if ! id "$USER_ACCOUNT" &>/dev/null; then
    info "Creating user: $USER_ACCOUNT"
    adduser --disabled-password --gecos "H743Poten Service User" $USER_ACCOUNT
    success "User $USER_ACCOUNT created"
else
    info "User $USER_ACCOUNT already exists"
fi

# Add to groups
usermod -aG gpio,spi,i2c,dialout $USER_ACCOUNT

# Create directories
info "Setting up directories..."
mkdir -p "$DATA_DIR"/{measurements,calibrations,logs}
mkdir -p "/home/$USER_ACCOUNT/poten-backups"
chown -R $USER_ACCOUNT:$USER_ACCOUNT "/home/$USER_ACCOUNT"

# Install service
info "Installing systemd service..."
cp "$INSTALL_DIR/deploy/potentiostat.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable potentiostat.service

# Install log rotation
info "Setting up log rotation..."
cp "$INSTALL_DIR/deploy/potentiostat_logrotate" /etc/logrotate.d/potentiostat 2>/dev/null || cat > /etc/logrotate.d/potentiostat << EOF
$DATA_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER_ACCOUNT $USER_ACCOUNT
}
EOF

# Setup nginx
read -p "Setup Nginx reverse proxy? (Y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    info "Setting up Nginx..."
    cp "$INSTALL_DIR/deploy/nginx-potentiostat" /etc/nginx/sites-available/potentiostat
    ln -sf /etc/nginx/sites-available/potentiostat /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl restart nginx
    success "Nginx configured"
fi

success "Phase 1 completed! Now running Phase 2 as user $USER_ACCOUNT..."

# Phase 2: User setup
sudo -u $USER_ACCOUNT bash << 'USERSCRIPT'
set -e

USER_ACCOUNT="potentiostat"
INSTALL_DIR="/home/$USER_ACCOUNT/H743Poten-Web"
DATA_DIR="/home/$USER_ACCOUNT/poten-data"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }

echo "🔧 Phase 2: User Application Setup"
echo "=================================="

# Create Python virtual environment
info "Setting up Python virtual environment..."
cd "/home/$USER_ACCOUNT"
python3 -m venv poten-env
source poten-env/bin/activate

# Install Python packages
info "Installing Python packages..."
cd "$INSTALL_DIR"
pip install --upgrade pip

# Create lightweight requirements for Pi
cat > requirements-pi-simple.txt << 'EOF'
Flask==2.3.3
Flask-CORS==4.0.0
numpy==1.24.3
pandas==2.0.3
scipy==1.10.1
matplotlib==3.7.2
scikit-learn==1.3.0
RPi.GPIO==0.7.1
spidev==3.6
pyserial==3.5
gunicorn==21.2.0
EOF

pip install -r requirements-pi-simple.txt

# Create production config
info "Setting up production configuration..."
mkdir -p config
cat > config/production.py << EOF
import os

class ProductionConfig:
    SECRET_KEY = os.urandom(32)
    DATABASE_PATH = '$DATA_DIR/potentiostat.db'
    LOG_LEVEL = 'INFO'
    LOG_FILE = '$DATA_DIR/logs/potentiostat.log'
    USE_HARDWARE = True
    DATA_DIR = '$DATA_DIR'
    HOST = '0.0.0.0'
    PORT = 8080
    DEBUG = False
EOF

# Setup cron jobs
info "Setting up maintenance tasks..."
chmod +x deploy/*.sh
(crontab -l 2>/dev/null || echo "") | grep -v "H743Poten" > /tmp/cron_temp
echo "0 2 * * * $INSTALL_DIR/deploy/backup.sh" >> /tmp/cron_temp
echo "*/10 * * * * $INSTALL_DIR/deploy/health-monitor.sh" >> /tmp/cron_temp
crontab /tmp/cron_temp
rm /tmp/cron_temp

success "Phase 2 completed!"
USERSCRIPT

# Start service
info "Starting H743Poten service..."
systemctl start potentiostat.service

sleep 3
if systemctl is-active --quiet potentiostat.service; then
    success "🎉 Deployment completed successfully!"
    echo
    info "Application URLs:"
    echo "  - Direct: http://$(hostname -I | awk '{print $1}'):8080"
    if [ -f /etc/nginx/sites-enabled/potentiostat ]; then
        echo "  - Nginx:  http://$(hostname -I | awk '{print $1}')"
    fi
    echo
    info "Management commands:"
    echo "  - Status:  systemctl status potentiostat"
    echo "  - Logs:    journalctl -u potentiostat -f" 
    echo "  - Restart: systemctl restart potentiostat"
else
    error "Service failed to start"
    error "Check logs: journalctl -u potentiostat -f"
    exit 1
fi
