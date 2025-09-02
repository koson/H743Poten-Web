# H743Poten Raspberry Pi Deployment Guide

## 📋 Overview
การ deploy H743Poten Web Interface บน Raspberry Pi ด้วย dedicated user สำหรับความปลอดภัย

## 🎯 System Architecture

```
/home/potentiostat/
├── H743Poten-Web/           # Main application
│   ├── src/                 # Source code
│   ├── static/              # Web assets
│   ├── templates/           # HTML templates
│   ├── data_logs/           # Application logs
│   ├── logs/                # Server logs
│   └── deploy/              # Deployment scripts
├── poten-data/              # Data storage
│   ├── measurements/        # CV measurement data
│   ├── calibrations/        # Calibration data
│   └── logs/                # System logs
├── poten-backups/           # Automated backups
└── poten-env/               # Python virtual environment
```

## 🚀 Quick Deployment (Recommended)

### Single Command Deployment
```bash
# 1. Copy application to Raspberry Pi
scp -r H743Poten-Web/ pi@[PI_IP]:/home/

# 2. SSH to Pi and run deployment
ssh pi@[PI_IP]
cd /home/H743Poten-Web
sudo chmod +x deploy/simple-deploy.sh
sudo ./deploy/simple-deploy.sh
```

### What the script does:
- ✅ Updates system packages
- ✅ Installs Python dependencies  
- ✅ Creates dedicated `potentiostat` user
- ✅ Sets up hardware permissions (GPIO, SPI, I2C)
- ✅ Configures systemd service
- ✅ Sets up Nginx reverse proxy (optional)
- ✅ Installs automated backups and monitoring
- ✅ Starts the application

### Alternative: Manual Two-Phase Deployment

## 🔧 Manual Deployment Steps

### 1. System Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv git nginx sqlite3

# Enable hardware interfaces
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0
```

### 2. Create Dedicated User
```bash
# Create user
sudo adduser --disabled-password --gecos "H743Poten Service User" potentiostat

# Add to hardware groups
sudo usermod -aG gpio,spi,i2c,dialout potentiostat

# Switch to user
sudo su - potentiostat
```

### 3. Setup Application
```bash
# Create directories
mkdir -p ~/poten-data/{measurements,calibrations,logs}
mkdir -p ~/poten-backups

# Copy application (if not already done)
# Application should be in /home/potentiostat/H743Poten-Web/

# Create virtual environment
python3 -m venv ~/poten-env
source ~/poten-env/bin/activate

# Install Python packages
cd ~/H743Poten-Web
pip install -r requirements-pi.txt
```

### 4. Configure System Service
```bash
# Install service file
sudo cp deploy/potentiostat.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable potentiostat.service
```

### 5. Setup Nginx (Optional but Recommended)
```bash
# Copy nginx config
sudo cp deploy/nginx-potentiostat /etc/nginx/sites-available/potentiostat
sudo ln -sf /etc/nginx/sites-available/potentiostat /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
```

## 🔐 Security Features

### User Isolation
- Dedicated `potentiostat` user
- Limited system access
- Hardware group membership only

### File Permissions
```bash
# Application files (read-only)
chmod 755 /home/potentiostat/H743Poten-Web
chmod 644 /home/potentiostat/H743Poten-Web/*.py

# Data directories (read-write)
chmod 755 /home/potentiostat/poten-data
chmod 644 /home/potentiostat/poten-data/*
```

### Service Security
- No new privileges
- Private tmp directory
- Protected system directories
- Limited read-write paths

## 🎛️ Service Management

### Basic Commands
```bash
# Start service
sudo systemctl start potentiostat

# Stop service
sudo systemctl stop potentiostat

# Restart service
sudo systemctl restart potentiostat

# Check status
sudo systemctl status potentiostat

# View logs
sudo journalctl -u potentiostat -f
```

### Health Monitoring
```bash
# Check if service is running
systemctl is-active potentiostat

# Check service uptime
systemctl show potentiostat --property=ActiveEnterTimestamp

# Monitor resource usage
sudo systemctl status potentiostat --no-pager -l
```

## 📊 Data Management

### Backup Strategy
```bash
# Daily backup script (cron job)
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/potentiostat/poten-backups"
tar -czf "$BACKUP_DIR/poten_backup_$DATE.tar.gz" \
    /home/potentiostat/poten-data \
    /home/potentiostat/H743Poten-Web/data_logs

# Keep only last 30 days
find "$BACKUP_DIR" -name "poten_backup_*.tar.gz" -mtime +30 -delete
```

### Log Rotation
Automatic log rotation configured via `/etc/logrotate.d/potentiostat`:
- Daily rotation
- Keep 30 days
- Compress old logs

## 🌐 Network Configuration

### Direct Access
- Application: `http://[PI_IP]:8080`
- Direct Flask server

### Nginx Proxy (Recommended)
- Web interface: `http://[PI_IP]`
- SSL/TLS termination
- Static file serving
- Load balancing ready

## 🔧 Troubleshooting

### Service Won't Start
```bash
# Check detailed logs
sudo journalctl -u potentiostat --no-pager -l

# Check Python environment
sudo -u potentiostat /home/potentiostat/poten-env/bin/python3 --version

# Test application manually
sudo -u potentiostat bash
cd ~/H743Poten-Web
source ~/poten-env/bin/activate
python3 main.py
```

### Hardware Access Issues
```bash
# Check user groups
groups potentiostat

# Test GPIO access
sudo -u potentiostat python3 -c "import RPi.GPIO as GPIO; print('GPIO OK')"

# Test SPI access
ls -la /dev/spi*
```

### Permission Issues
```bash
# Fix ownership
sudo chown -R potentiostat:potentiostat /home/potentiostat/

# Fix permissions
sudo chmod -R 755 /home/potentiostat/H743Poten-Web
sudo chmod -R 755 /home/potentiostat/poten-data
```

## 📋 Post-Deployment Checklist

- [ ] Service starts automatically
- [ ] Web interface accessible
- [ ] Hardware interfaces working
- [ ] Data logging functional
- [ ] Backup system configured
- [ ] Log rotation active
- [ ] Firewall configured (if needed)
- [ ] Monitoring setup

## 🔄 Updates and Maintenance

### Application Updates
```bash
# Stop service
sudo systemctl stop potentiostat

# Backup current version
sudo -u potentiostat tar -czf ~/poten-backups/app_backup_$(date +%Y%m%d).tar.gz ~/H743Poten-Web

# Update application files
# (copy new files)

# Restart service
sudo systemctl start potentiostat
```

### System Updates
```bash
# Regular system updates
sudo apt update && sudo apt upgrade -y

# Python package updates
sudo -u potentiostat bash
source ~/poten-env/bin/activate
pip list --outdated
pip install --upgrade [package-name]
```

## 📞 Support

### Log Locations
- Service logs: `journalctl -u potentiostat`
- Application logs: `/home/potentiostat/poten-data/logs/`
- Nginx logs: `/var/log/nginx/`

### Performance Monitoring
```bash
# CPU and memory usage
htop

# Disk usage
df -h
du -sh /home/potentiostat/*

# Network connections
netstat -tulpn | grep :8080
```
