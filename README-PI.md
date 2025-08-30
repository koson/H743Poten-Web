# 🍓 H743 Potentiostat - Raspberry Pi Edition

[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-4%2B-red.svg)](https://www.raspberrypi.org/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-green.svg)](https://flask.palletsprojects.com/)

**Clean, production-ready version optimized for Raspberry Pi deployment**

## 🎯 Overview

This is a streamlined version of the H743 Potentiostat system, specifically optimized for deployment on Raspberry Pi devices. All development artifacts, analysis tools, and documentation have been cleaned up, leaving only the essential production code.

## ⚡ Quick Start

### 1. 📥 Download to Raspberry Pi
```bash
git clone https://github.com/koson/H743Poten-Web.git
cd H743Poten-Web
git checkout production-raspberry-pi
```

### 2. 🚀 One-Line Installation
```bash
chmod +x install-pi.sh && ./install-pi.sh
```

### 3. ▶️ Start Server
```bash
source venv/bin/activate
python3 auto_dev.py start
```

### 4. 🌐 Access Web Interface
Open browser to: `http://your-pi-ip:8080`

## 📁 Clean File Structure

```
H743Poten-Web/
├── 🚀 Core Application
│   ├── main.py                     # Main application entry
│   ├── main_dev.py                 # Development server
│   ├── auto_dev.py                 # Auto development launcher
│   └── requirements-pi.txt         # Pi-optimized dependencies
│
├── 🧠 Peak Detection (Production)
│   ├── baseline_detector_v4.py     # Core baseline detection
│   ├── enhanced_detector_v5.py     # Latest enhanced detection
│   ├── terminal_manager.py         # Terminal management
│   └── universal_terminal_manager.py
│
├── 🌐 Web Components
│   ├── src/                        # Source code
│   ├── static/                     # Web assets
│   └── templates/                  # HTML templates
│
├── 🐳 Deployment
│   ├── docker-compose.yml          # Container deployment
│   ├── Dockerfile                  # Production container
│   └── install-pi.sh               # Pi installation script
│
├── 📚 Documentation
│   ├── README.md                   # This file
│   ├── QUICK_START.md              # Quick setup guide
│   └── RASPBERRY_PI_DEPLOYMENT_PLAN.md
│
└── 📁 Archive (Preserved)
    ├── archive/                    # Previous development files
    └── Article_Figure_Package/     # Research publication materials
```

## 🎛️ Hardware Requirements

### Minimum Specifications
- **Raspberry Pi 4** (2GB RAM minimum, 4GB recommended)
- **SD Card**: 16GB+ (Class 10 or better)
- **Python**: 3.8+ (pre-installed on Raspberry Pi OS)

### Connections
- **USB**: STM32 H743 Potentiostat device
- **Network**: Ethernet or WiFi for web interface access
- **GPIO**: Reserved for future expansion

## 🔧 Configuration

### Environment Setup
```bash
# Copy and edit configuration
cp .env.example .env
nano .env
```

### Key Settings
```env
# Server Configuration
FLASK_ENV=production
HOST=0.0.0.0
PORT=8080

# STM32 Communication
SERIAL_PORT=/dev/ttyUSB0
BAUD_RATE=115200

# Data Logging
LOG_LEVEL=INFO
DATA_DIR=/home/pi/potentiostat-data
```

## 🐳 Docker Deployment (Alternative)

### Quick Docker Start
```bash
# Using docker-compose
docker-compose up -d

# Using Docker directly
docker build -t h743-poten .
docker run -d -p 8080:8080 --device=/dev/ttyUSB0 h743-poten
```

## 🔌 STM32 Device Setup

### Serial Connection
1. Connect STM32 H743 via USB
2. Check device: `ls /dev/ttyUSB*` or `ls /dev/ttyACM*`
3. Set permissions: `sudo usermod -a -G dialout $USER`
4. Update `.env` with correct port

### Test Communication
```bash
# Test serial connection
python3 -c "
import serial
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
print('✅ STM32 connection OK' if ser.is_open else '❌ Connection failed')
ser.close()
"
```

## 🔄 Service Management

### Manual Control
```bash
# Start server
python3 auto_dev.py start

# Stop server  
python3 auto_dev.py stop

# Check status
python3 auto_dev.py status
```

### Systemd Service (Auto-start)
```bash
# If installed via install-pi.sh
sudo systemctl start h743-potentiostat     # Start
sudo systemctl stop h743-potentiostat      # Stop  
sudo systemctl status h743-potentiostat    # Status
sudo systemctl restart h743-potentiostat   # Restart
```

## 📊 Performance Optimization

### For Pi 3/4 (2GB RAM)
- Uses lightweight matplotlib instead of plotly
- Numpy with ARM optimization
- Minimal web assets
- Efficient data structures

### For Pi 4 (4GB+ RAM)
Uncomment in `requirements-pi.txt`:
```
scikit-learn>=1.0.0,<1.3.0  # ML features
plotly>=5.0.0,<6.0.0        # Interactive plots
```

## 🔍 Troubleshooting

### Common Issues

**1. Permission Denied (Serial)**
```bash
sudo usermod -a -G dialout $USER
# Logout and login again
```

**2. Port Already in Use**
```bash
sudo netstat -tlnp | grep :8080
sudo kill -9 <PID>
```

**3. Import Errors**
```bash
source venv/bin/activate
pip install -r requirements-pi.txt
```

**4. Memory Issues**
```bash
# Check memory usage
free -h
# Increase swap if needed
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## 🚀 Production Deployment

### Security Checklist
- [ ] Change default passwords
- [ ] Enable firewall (ufw)
- [ ] Set up SSL/TLS (optional)
- [ ] Configure log rotation
- [ ] Set up automated backups

### Monitoring
```bash
# Check system resources
htop

# Monitor logs
tail -f /var/log/syslog | grep h743

# Check disk space
df -h
```

## 🏷️ Version Information

- **Current Branch**: `production-raspberry-pi`
- **Based on**: `v2.1-recover-from-archive`
- **Optimized for**: Raspberry Pi 3B+, 4B, 4B+ (2GB/4GB/8GB)
- **Python**: 3.8+ (ARM compatible)

## 📞 Support

### Quick Reference
```bash
# Health check
curl http://localhost:8080/health

# Test peak detection
python3 -c "from baseline_detector_v4 import cv_baseline_detector_v4; print('✅ Detection OK')"

# View logs
journalctl -u h743-potentiostat -f
```

### Getting Help
1. Check logs first: `auto_dev.py logs` or `journalctl -u h743-potentiostat`
2. Verify hardware connections
3. Test components individually
4. Check GitHub issues for known problems

---

## 🎉 Clean Deployment Success!

This version removes **90%+ of development clutter** while preserving **100% of production functionality**.

**What's Gone**: 473 archived files, analysis scripts, test data, documentation, legacy algorithms
**What's Here**: Clean production code, Pi optimization, easy deployment, essential documentation

**Ready for Raspberry Pi! 🍓**
