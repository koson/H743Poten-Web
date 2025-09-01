#!/bin/bash
# H743Poten Raspberry Pi Deployment Script
# Run this script on the Raspberry Pi to deploy the application

set -e

echo "🍓 H743Poten Raspberry Pi Deployment"
echo "===================================="

# Configuration
USER_ACCOUNT="potentiostat"  # Dedicated user for security
INSTALL_DIR="/home/$USER_ACCOUNT/H743Poten-Web"
DATA_DIR="/home/$USER_ACCOUNT/poten-data"
BACKUP_DIR="/home/$USER_ACCOUNT/poten-backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as correct user
CURRENT_USER=$(whoami)
if [ "$CURRENT_USER" = "root" ]; then
    # Running as root - create user and setup
    info "Running as root - setting up dedicated user..."
    
    # Create potentiostat user if it doesn't exist
    if ! id "$USER_ACCOUNT" &>/dev/null; then
        info "Creating user: $USER_ACCOUNT"
        adduser --disabled-password --gecos "H743Poten Service User" $USER_ACCOUNT
        
        # Add to required groups
        usermod -aG gpio,spi,i2c,dialout $USER_ACCOUNT
        
        success "User $USER_ACCOUNT created successfully"
    else
        info "User $USER_ACCOUNT already exists"
        # Ensure user is in correct groups
        usermod -aG gpio,spi,i2c,dialout $USER_ACCOUNT
    fi
    
    # Create home directory structure
    mkdir -p "/home/$USER_ACCOUNT"
    chown $USER_ACCOUNT:$USER_ACCOUNT "/home/$USER_ACCOUNT"
    
    # Switch to the user and continue
    info "Switching to user $USER_ACCOUNT to continue setup..."
    exec sudo -u $USER_ACCOUNT bash "$0" "$@"
    
elif [ "$CURRENT_USER" != "$USER_ACCOUNT" ]; then
    error "Please run this script as root first, then it will switch to user '$USER_ACCOUNT'"
    error "Run: sudo bash deploy-pi.sh"
    exit 1
fi

# Check if we're on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    warning "This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
info "Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install system dependencies
info "Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    nginx \
    sqlite3 \
    build-essential \
    cmake \
    pkg-config \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libhdf5-dev \
    libatlas-base-dev \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    python3-scipy \
    python3-numpy \
    python3-matplotlib

# Enable GPIO, SPI, I2C
info "Enabling hardware interfaces..."
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_serial_hw 0
sudo raspi-config nonint do_serial_cons 1

# Add user to hardware groups
sudo usermod -aG gpio,spi,i2c,dialout $USER_ACCOUNT

# Create directories
info "Creating directory structure..."
mkdir -p "$DATA_DIR"/{measurements,calibrations,logs}
mkdir -p "$BACKUP_DIR"
mkdir -p "/home/$USER_ACCOUNT/.config/potentiostat"

# Create Python virtual environment
info "Setting up Python virtual environment..."
cd "/home/$USER_ACCOUNT"
python3 -m venv poten-env
source poten-env/bin/activate

# Upgrade pip
pip install --upgrade pip

# Create requirements.txt for Pi
info "Creating Raspberry Pi requirements..."
cat > requirements-pi.txt << EOF
# Core Flask and web dependencies
Flask==2.3.3
Flask-CORS==4.0.0
Werkzeug==2.3.7

# Scientific computing (use system packages for better performance)
# numpy==1.24.3  # Use system package
# scipy==1.10.1  # Use system package
# matplotlib==3.7.2  # Use system package

# Data handling
pandas==2.0.3
h5py==3.9.0

# Hardware interfaces
RPi.GPIO==0.7.1
spidev==3.6
smbus2==0.4.2
pyserial==3.5

# Logging and utilities
colorama==0.4.6
psutil==5.9.5

# Additional scientific libraries (lightweight versions)
scikit-learn==1.3.0
statsmodels==0.14.0

# Web and API
requests==2.31.0
gunicorn==21.2.0

# Development tools
pytest==7.4.0
EOF

# Install Python packages
info "Installing Python packages..."
pip install -r requirements-pi.txt

# Clone/copy application if needed
if [ ! -d "$INSTALL_DIR" ]; then
    info "Application directory not found. Please copy your application files to $INSTALL_DIR"
    warning "After copying files, run this script again to complete setup"
    exit 1
fi

# Set up application configuration
info "Setting up application configuration..."
cd "$INSTALL_DIR"

# Create production config
cat > config/production.py << EOF
# Production configuration for Raspberry Pi
import os

class ProductionConfig:
    # Security
    SECRET_KEY = os.urandom(32)
    
    # Database
    DATABASE_PATH = '$DATA_DIR/potentiostat.db'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = '$DATA_DIR/logs/potentiostat.log'
    
    # Hardware
    USE_HARDWARE = True  # Enable real hardware on Pi
    SPI_BUS = 0
    SPI_DEVICE = 0
    
    # Data storage
    DATA_DIR = '$DATA_DIR'
    MEASUREMENT_DIR = '$DATA_DIR/measurements'
    CALIBRATION_DIR = '$DATA_DIR/calibrations'
    
    # Web server
    HOST = '0.0.0.0'
    PORT = 8080
    DEBUG = False
    
    # Security headers
    SESSION_COOKIE_SECURE = False  # Set to True if using HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
EOF

# Create systemd service
info "Setting up systemd service..."
sudo cp deploy/potentiostat.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable potentiostat.service

# Set up log rotation
info "Setting up log rotation..."
sudo tee /etc/logrotate.d/potentiostat << EOF
$DATA_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER_ACCOUNT $USER_ACCOUNT
    postrotate
        systemctl reload potentiostat.service || true
    endscript
}
EOF

# Set up nginx reverse proxy (optional)
read -p "Set up Nginx reverse proxy? (Y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    info "Setting up Nginx..."
    sudo tee /etc/nginx/sites-available/potentiostat << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Static files
    location /static {
        alias $INSTALL_DIR/static;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    sudo ln -sf /etc/nginx/sites-available/potentiostat /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t
    sudo systemctl enable nginx
    sudo systemctl restart nginx
    
    success "Nginx configured. Application will be available on port 80"
fi

# Set file permissions
info "Setting file permissions..."
chmod +x "$INSTALL_DIR"/*.py
chmod +x "$INSTALL_DIR"/deploy/*.sh
chown -R $USER_ACCOUNT:$USER_ACCOUNT "$INSTALL_DIR"
chown -R $USER_ACCOUNT:$USER_ACCOUNT "$DATA_DIR"

# Setup cron jobs for maintenance
info "Setting up automated maintenance tasks..."
chmod +x "$INSTALL_DIR/deploy/setup-cron.sh"
"$INSTALL_DIR/deploy/setup-cron.sh"

# Start the service
info "Starting H743Poten service..."
sudo systemctl start potentiostat.service

# Check service status
sleep 3
if sudo systemctl is-active --quiet potentiostat.service; then
    success "H743Poten service is running!"
    info "Service status:"
    sudo systemctl status potentiostat.service --no-pager -l
    
    echo
    success "🎉 Deployment completed successfully!"
    echo
    info "Application URLs:"
    echo "  - Direct: http://$(hostname -I | awk '{print $1}'):8080"
    if [ -f /etc/nginx/sites-enabled/potentiostat ]; then
        echo "  - Nginx:  http://$(hostname -I | awk '{print $1}')"
    fi
    echo
    info "Useful commands:"
    echo "  - Check status:  sudo systemctl status potentiostat"
    echo "  - View logs:     sudo journalctl -u potentiostat -f"
    echo "  - Restart:       sudo systemctl restart potentiostat"
    echo "  - Stop:          sudo systemctl stop potentiostat"
    
else
    error "Failed to start H743Poten service"
    error "Check logs: sudo journalctl -u potentiostat -f"
    exit 1
fi
