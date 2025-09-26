# 🚀 H743 Potentiostat Deployment Guide

เครื่องมือสำหรับการ deploy H743 Potentiostat Web Interface ไปยัง environments ต่างๆ

## 📋 Prerequisites

### Development Machine (Windows/Linux/macOS)
- Git
- Python 3.8+
- SSH client
- rsync (for Pi deployment)

### Raspberry Pi Target
- Raspberry Pi OS
- SSH enabled
- Network connectivity
- Python 3.8+

## 🛠️ Setup

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd H743Poten-Web
```

### 2. Setup Development Environment
```bash
# Create and activate virtual environment
python3 -m venv poten-env
source poten-env/bin/activate  # Linux/macOS
# or
poten-env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Deployment Commands

### Local Development
```bash
# Start local development server
./deploy.sh local development

# Access at: http://localhost:8080
```

### Raspberry Pi Deployment

#### First-time Pi Setup
```bash
# Setup Raspberry Pi (run once)
./scripts/setup-pi.sh 192.168.1.100

# Note: Replace IP with your Pi's actual IP
```

#### Deploy to Pi
```bash
# Deploy to home Pi
./deploy.sh rpi-home development

# Deploy to office Pi
./deploy.sh rpi-office main
```

### Health Monitoring
```bash
# Check all services
./scripts/health-check.sh

# Quick status check
curl http://localhost:8080/health
curl http://192.168.1.100:8080/health
```

## 📊 Monitoring & Troubleshooting

### Health Check Endpoints
- `GET /health` - Service health status
- `GET /debug` - Debug information
- `GET /api/connection/status` - Hardware connection status

### Log Access
```bash
# Local logs
tail -f logs/h743poten.log

# Pi logs (via SSH)
ssh pi@192.168.1.100 'cd h743poten-web && python auto_dev.py logs'
```

### Service Management on Pi
```bash
# Via auto_dev.py
python auto_dev.py start
python auto_dev.py stop
python auto_dev.py status
python auto_dev.py logs

# Via systemd (if enabled)
sudo systemctl start h743poten-web
sudo systemctl status h743poten-web
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Copy template and modify
cp .env.template .env

# Key variables:
FLASK_ENV=production
SERIAL_PORT=/dev/ttyUSB0
SERIAL_BAUDRATE=115200
WEB_HOST=0.0.0.0
WEB_PORT=8080
GPIO_ENABLED=true
```

### Pi-specific Settings
- Serial port: Usually `/dev/ttyUSB0` or `/dev/ttyACM0`
- GPIO access: User must be in `gpio`, `dialout` groups
- Auto-start: Systemd service configured automatically

## 🌐 Network Configuration

### Default Ports
- Web interface: 8080
- Health check: 8080/health

### Firewall (if needed)
```bash
# Allow web access
sudo ufw allow 8080/tcp
```

## 🔄 Git Workflow

### Branch Strategy
```bash
# Development
git checkout development
# ... make changes ...
git add .
git commit -m "feature: description"

# Deploy to test
./deploy.sh rpi-home development

# Production release
git checkout main
git merge development
git tag v1.0.1

# Deploy to production
./deploy.sh rpi-office main
```

## 🚨 Troubleshooting

### Common Issues

#### Connection Issues
```bash
# Check Pi network
ping 192.168.1.100

# Check SSH access
ssh pi@192.168.1.100

# Check Pi services
ssh pi@192.168.1.100 'python h743poten-web/auto_dev.py status'
```

#### Serial Port Issues
```bash
# List available ports
ls -la /dev/tty*

# Check permissions
groups pi
# Should include: dialout, gpio

# Test serial connection
python -c "import serial; print('Serial OK')"
```

#### Service Won't Start
```bash
# Check logs
python auto_dev.py logs

# Check dependencies
pip install -r requirements.txt

# Check Python environment
which python
python --version
```

### Getting Help

1. Check logs: `./scripts/health-check.sh`
2. Verify configuration: `cat .env`
3. Test manually: `python main.py`
4. Check network: `curl http://localhost:8080/health`

## 📝 File Structure

```
H743Poten-Web/
├── deploy.sh              # Main deployment script
├── scripts/
│   ├── deploy-to-rpi.sh   # Pi deployment
│   ├── setup-pi.sh        # Pi initial setup
│   ├── health-check.sh    # Health monitoring
│   └── deploy-to-cloud.sh # Cloud deployment (future)
├── src/                   # Application source
├── templates/             # Web templates
├── static/               # Static assets
├── requirements.txt      # Python dependencies
├── .env.template        # Environment template
└── DEPLOYMENT.md        # This file
```

## 🎯 Next Steps

1. **Test local deployment**: `./deploy.sh local development`
2. **Setup your Pi**: `./scripts/setup-pi.sh <pi-ip>`
3. **Deploy to Pi**: `./deploy.sh rpi-home development`
4. **Monitor health**: `./scripts/health-check.sh`
5. **Access web interface**: `http://<pi-ip>:8080`

Happy deploying! 🚀
