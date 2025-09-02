# H743Poten Raspberry Pi Deployment - Quick Start Guide

## 📦 Step 1: Prepare Files for Transfer

### From your development machine (Windows/WSL):
```bash
# Navigate to project directory
cd /mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web

# Make deployment scripts executable
chmod +x deploy/*.sh

# Create deployment package
tar -czf H743Poten-Deploy.tar.gz \
    --exclude=__pycache__ \
    --exclude=.git \
    --exclude=node_modules \
    --exclude="*.pyc" \
    .
```

## 🚀 Step 2: Transfer to Raspberry Pi

### Option A: Using SCP (Recommended)
```bash
# Copy the deployment package
scp H743Poten-Deploy.tar.gz pi@[PI_IP_ADDRESS]:/tmp/

# Or copy the entire directory
scp -r . pi@[PI_IP_ADDRESS]:/tmp/H743Poten-Web/
```

### Option B: Using rsync (Better for updates)
```bash
# Initial deployment
rsync -avz --exclude=__pycache__ --exclude=.git . pi@[PI_IP_ADDRESS]:/tmp/H743Poten-Web/

# For future updates
rsync -avz --exclude=__pycache__ --exclude=.git --delete . pi@[PI_IP_ADDRESS]:/home/potentiostat/H743Poten-Web/
```

### Option C: Using USB Drive
```bash
# Copy to USB drive
cp H743Poten-Deploy.tar.gz /media/usb/

# On Pi, copy from USB
sudo cp /media/usb/H743Poten-Deploy.tar.gz /tmp/
```

## 🔧 Step 3: Deploy on Raspberry Pi

### SSH to Raspberry Pi:
```bash
ssh pi@[PI_IP_ADDRESS]
```

### Extract and Deploy:
```bash
# If using tar package
cd /tmp
tar -xzf H743Poten-Deploy.tar.gz
sudo mv H743Poten-Web /home/

# Or if using direct copy
sudo mv /tmp/H743Poten-Web /home/

# Navigate to application directory
cd /home/H743Poten-Web

# Make scripts executable (if not already)
sudo chmod +x deploy/*.sh

# Run deployment
sudo ./deploy/simple-deploy.sh
```

## 📋 Complete Example Workflow

```bash
# === On Development Machine ===
cd /mnt/d/GitHubRepos/__Potentiostat/poten-2025/H743Poten/H743Poten-Web
chmod +x deploy/*.sh
scp -r . pi@192.168.1.100:/tmp/H743Poten-Web/

# === On Raspberry Pi ===
ssh pi@192.168.1.100
sudo mv /tmp/H743Poten-Web /home/
cd /home/H743Poten-Web
sudo ./deploy/simple-deploy.sh
```

## 🔍 Verification Steps

After deployment, verify everything is working:

```bash
# Check service status
sudo systemctl status potentiostat

# Check if application is responding
curl http://localhost:8080

# Check logs
sudo journalctl -u potentiostat -f

# Test web interface
# Open browser: http://[PI_IP]:8080
```

## ⚡ Quick Commands Reference

```bash
# Transfer files (from dev machine)
scp -r H743Poten-Web/ pi@[PI_IP]:/tmp/

# Deploy (on Pi)
sudo mv /tmp/H743Poten-Web /home/
cd /home/H743Poten-Web  
sudo ./deploy/simple-deploy.sh

# Manage service (on Pi)
sudo systemctl start|stop|restart|status potentiostat
sudo journalctl -u potentiostat -f
```

## 🛠️ Troubleshooting

### If transfer fails:
```bash
# Check SSH connection
ping [PI_IP]
ssh pi@[PI_IP] "echo 'Connection OK'"

# Check disk space on Pi
ssh pi@[PI_IP] "df -h"
```

### If deployment fails:
```bash
# Check script permissions
ls -la deploy/
chmod +x deploy/*.sh

# Run with verbose output
sudo bash -x ./deploy/simple-deploy.sh
```

### Common Issues:
- **Permission denied**: Use `sudo` for deployment script
- **No space**: Clean up Pi disk space first
- **Network issues**: Check Pi IP address and connectivity
- **Missing files**: Ensure all files transferred correctly

## 📚 What Gets Deployed

The deployment creates this structure on Pi:
```
/home/potentiostat/
├── H743Poten-Web/           # Application files
├── poten-data/              # Data storage
├── poten-backups/           # Automated backups
└── poten-env/               # Python virtual environment

/etc/systemd/system/
└── potentiostat.service     # System service

/etc/nginx/sites-enabled/
└── potentiostat             # Web proxy (optional)
```
