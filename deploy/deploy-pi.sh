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
    # Running as root - create user and setup system dependencies
    info "Running as root - setting up system and dedicated user..."
    
    # Update system packages first (as root)
    info "Updating system packages..."
    apt update
    apt upgrade -y
    
    # Install system dependencies (as root)
    info "Installing system dependencies..."
    apt install -y \
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
    
    # Enable GPIO, SPI, I2C (as root)
    info "Enabling hardware interfaces..."
    if command -v raspi-config >/dev/null; then
        raspi-config nonint do_spi 0
        raspi-config nonint do_i2c 0
        raspi-config nonint do_serial_hw 0
        raspi-config nonint do_serial_cons 1
    fi
    
    # Create potentiostat user if it doesn't exist
    if ! id "$USER_ACCOUNT" &>/dev/null; then
        info "Creating user: $USER_ACCOUNT"
        adduser --disabled-password --gecos "H743Poten Service User" $USER_ACCOUNT
        success "User $USER_ACCOUNT created successfully"
    else
        info "User $USER_ACCOUNT already exists"
    fi
    
    # Add to required groups
    usermod -aG gpio,spi,i2c,dialout $USER_ACCOUNT
    
    # Create home directory structure
    mkdir -p "/home/$USER_ACCOUNT"
    chown $USER_ACCOUNT:$USER_ACCOUNT "/home/$USER_ACCOUNT"
    
    # Set up directories and permissions (as root)
    info "Setting up directory structure..."
    mkdir -p "$DATA_DIR"/{measurements,calibrations,logs}
    mkdir -p "$BACKUP_DIR"
    mkdir -p "/home/$USER_ACCOUNT/.config/potentiostat"
    chown -R $USER_ACCOUNT:$USER_ACCOUNT "/home/$USER_ACCOUNT"
    
    # Switch to the user and continue (skip system setup)
    info "Switching to user $USER_ACCOUNT to continue application setup..."
    export SKIP_SYSTEM_SETUP=1
    exec sudo -u $USER_ACCOUNT bash "$0" "$@"
    
elif [ "$CURRENT_USER" != "$USER_ACCOUNT" ]; then
    error "Please run this script as root first"
    error "Run: sudo bash deploy/deploy-pi.sh"
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
if [ -z "$SKIP_SYSTEM_SETUP" ]; then
    info "System setup already completed by root user"
else
    info "Skipping system setup (already done by root)"
fi

# Skip system package installation when running as potentiostat user
# (Already done by root in previous step)

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
# Note: This requires root privileges, so we'll create it in /tmp first
# and provide instructions for root to install it
cp deploy/potentiostat.service /tmp/
cat > /tmp/install_service.sh << 'EOF'
#!/bin/bash
# Script to install systemd service (run as root)
cp /tmp/potentiostat.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable potentiostat.service
echo "✅ Service installed and enabled"
EOF
chmod +x /tmp/install_service.sh

info "Service file prepared. Root user needs to run: sudo /tmp/install_service.sh"

# Set up log rotation
info "Setting up log rotation..."
# Create log rotation config in /tmp for root to install
cat > /tmp/potentiostat_logrotate << EOF
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

info "Log rotation config prepared. Root user needs to run: sudo cp /tmp/potentiostat_logrotate /etc/logrotate.d/potentiostat"

# Set up nginx reverse proxy (optional)
read -p "Set up Nginx reverse proxy? (Y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    info "Setting up Nginx configuration..."
    # Create nginx config in /tmp for root to install
    cp deploy/nginx-potentiostat /tmp/
    cat > /tmp/install_nginx.sh << 'EOF'
#!/bin/bash
# Script to install nginx config (run as root)
cp /tmp/nginx-potentiostat /etc/nginx/sites-available/potentiostat
ln -sf /etc/nginx/sites-available/potentiostat /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
if [ $? -eq 0 ]; then
    systemctl enable nginx
    systemctl restart nginx
    echo "✅ Nginx configured and restarted"
else
    echo "❌ Nginx configuration error"
fi
EOF
    chmod +x /tmp/install_nginx.sh
    
    info "Nginx config prepared. Root user needs to run: sudo /tmp/install_nginx.sh"
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
info "Application setup completed!"
info "Root user needs to complete the installation by running:"
echo "  sudo /tmp/install_service.sh"
echo "  sudo cp /tmp/potentiostat_logrotate /etc/logrotate.d/potentiostat"
if [ -f /tmp/install_nginx.sh ]; then
    echo "  sudo /tmp/install_nginx.sh"
fi
echo "  sudo systemctl start potentiostat.service"

# Create a final setup script for root
cat > /tmp/finish_setup.sh << 'EOF'
#!/bin/bash
echo "🔧 Completing H743Poten setup..."

# Install service
if [ -f /tmp/install_service.sh ]; then
    /tmp/install_service.sh
fi

# Install log rotation
if [ -f /tmp/potentiostat_logrotate ]; then
    cp /tmp/potentiostat_logrotate /etc/logrotate.d/potentiostat
    echo "✅ Log rotation configured"
fi

# Install nginx if configured
if [ -f /tmp/install_nginx.sh ]; then
    /tmp/install_nginx.sh
fi

# Start the service
echo "🚀 Starting H743Poten service..."
systemctl start potentiostat.service

# Check service status
sleep 3
if systemctl is-active --quiet potentiostat.service; then
    echo "✅ H743Poten service is running!"
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "Application URLs:"
    echo "  - Direct: http://$(hostname -I | awk '{print $1}'):8080"
    if [ -f /etc/nginx/sites-enabled/potentiostat ]; then
        echo "  - Nginx:  http://$(hostname -I | awk '{print $1}')"
    fi
    echo ""
    echo "Useful commands:"
    echo "  - Check status:  systemctl status potentiostat"
    echo "  - View logs:     journalctl -u potentiostat -f"
    echo "  - Restart:       systemctl restart potentiostat"
    echo "  - Stop:          systemctl stop potentiostat"
else
    echo "❌ Failed to start H743Poten service"
    echo "Check logs: journalctl -u potentiostat -f"
    exit 1
fi
EOF

chmod +x /tmp/finish_setup.sh

success "User setup completed!"
warning "Root user must run: sudo /tmp/finish_setup.sh"
