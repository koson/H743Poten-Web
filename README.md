# H743Poten Web Interface

# H743Poten Web Interface

A comprehensive web interface for controlling and monitoring the STM32H743 Potentiostat system. This interface provides real-time control, data visualization, and measurement management capabilities for electrochemical measurements.

## 🚀 Features

- **Real-time Device Control**: Connect and control STM32H743 potentiostat via UART/Serial
- **Measurement Management**: Support for Cyclic Voltammetry (CV), Chronoamperometry (CA), and other electrochemical techniques
- **Data Visualization**: Interactive plots using Plotly for real-time data display
- **Mock Hardware Mode**: Development and testing without physical hardware
- **Docker Support**: Containerized deployment for development and production
- **Responsive UI**: Bootstrap-based interface optimized for desktop and mobile
- **SCPI Protocol**: Industry-standard SCPI commands for device communication
- **Data Export**: Export measurement data in multiple formats (CSV, JSON)
- **Device Status Monitoring**: Real-time connection status and hardware diagnostics

## 📋 Prerequisites

### For Docker Deployment (Recommended)
- Docker Desktop or Docker Engine
- Docker Compose

### For Local Development
- Python 3.8+
- pip (Python package manager)

### For Hardware Connection
- STM32H743 Potentiostat device
- USB cable for UART communication
- Appropriate device drivers (usually automatic on modern systems)

## 🛠️ Quick Start

### Using Docker (Recommended)

1. **Clone or navigate to the project directory**:
   ```bash
   cd H743Poten-Web
   ```

2. **Start development environment**:
   ```bash
   # Windows
   deploy.bat dev
   
   # Linux/macOS
   ./deploy.sh dev
   ```

3. **Access the web interface**:
   - Development: http://localhost:5000
   - The interface will start with mock hardware for testing

4. **Start production environment**:
   ```bash
   # Windows
   deploy.bat prod
   
   # Linux/macOS
   ./deploy.sh prod
   ```
   - Production: http://localhost:8080

### Manual Docker Commands

```bash
# Development environment
docker-compose --profile dev up h743poten-dev -d

# Production environment
docker-compose up h743poten-web -d

# View logs
docker logs h743poten-dev -f

# Stop containers
docker-compose --profile dev down
```

### Local Python Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   python main_dev.py    # Development mode
   python main.py        # Production mode
   ```

## 📁 Project Structure

```
H743Poten-Web/
├── src/                          # Source code
│   ├── app.py                   # Main Flask application
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py          # Configuration settings
│   ├── hardware/
│   │   ├── __init__.py
│   │   ├── scpi_handler.py      # Real hardware communication
│   │   └── mock_scpi_handler.py # Mock hardware for testing
│   ├── services/
│   │   ├── __init__.py
│   │   ├── measurement_service.py # Measurement logic
│   │   └── data_service.py      # Data management
│   ├── templates/
│   │   └── index.html           # Web interface
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── run_app.py               # Production entry point
│   └── run_dev.py               # Development entry point
├── docker-compose.yml           # Docker orchestration
├── Dockerfile                   # Production Docker image
├── Dockerfile.dev              # Development Docker image
├── requirements.txt             # Python dependencies
├── main.py                      # Production launcher
├── main_dev.py                  # Development launcher
├── wsgi.py                      # WSGI entry point
├── deploy.sh                    # Linux/macOS deployment script
├── deploy.bat                   # Windows deployment script
├── test_imports.py              # Import validation script
├── setup_raspberry_pi.sh        # Raspberry Pi setup
└── README.md                    # This file
```

## 🔧 Configuration

### Environment Variables

The application supports the following environment variables:

```bash
# Flask Configuration
FLASK_ENV=development|production    # Application environment
FLASK_DEBUG=True|False             # Debug mode

# Hardware Configuration
DEVICE_PORT=/dev/ttyUSB0           # Serial port (Linux/macOS)
DEVICE_PORT=COM3                   # Serial port (Windows)
DEVICE_BAUDRATE=115200             # Serial communication speed
USE_MOCK_HARDWARE=True|False       # Enable mock hardware mode

# Application Configuration
HOST=0.0.0.0                       # Bind address
PORT=8080                          # Application port
LOG_LEVEL=INFO|DEBUG|WARNING       # Logging level
```

### Docker Environment

Environment variables can be set in `docker-compose.yml` or passed at runtime:

```bash
# Override environment variables
docker-compose up -e DEVICE_PORT=/dev/ttyACM0 h743poten-web
```

## 🎯 Usage

### Web Interface

1. **Connect to Device**:
   - Click "Connect" button
   - Select appropriate serial port
   - Status indicator shows connection state

2. **Send SCPI Commands**:
   - Use the UART Interface section
   - Type SCPI commands (e.g., `*IDN?`, `SYST:ERR?`)
   - View responses in real-time

3. **Run Measurements**:
   - Configure measurement parameters
   - Click "Start Measurement"
   - View real-time data plots
   - Export data when complete

4. **Device Status**:
   - Monitor connection status
   - View system information
   - Check for errors

### API Endpoints

The application provides REST API endpoints:

```bash
# Device Management
GET  /api/connect                  # Connect to device
POST /api/disconnect               # Disconnect from device
GET  /api/status                   # Get device status

# Measurements
POST /api/measurements/start       # Start measurement
POST /api/measurements/stop        # Stop measurement
GET  /api/measurements/data        # Get measurement data

# SCPI Communication
POST /api/scpi/command             # Send SCPI command
GET  /api/scpi/response            # Get SCPI response

# Data Management
GET  /api/data/export              # Export data
POST /api/data/clear               # Clear data
```

## 🔧 Deployment Options

### Development Deployment

Best for development and testing:

```bash
# Start development environment
deploy.bat dev                     # Windows
./deploy.sh dev                    # Linux/macOS

# Features:
# - Hot reload on code changes
# - Debug mode enabled
# - Mock hardware by default
# - Accessible at http://localhost:5000
```

### Production Deployment

Best for production use:

```bash
# Start production environment
deploy.bat prod                    # Windows
./deploy.sh prod                   # Linux/macOS

# Features:
# - Optimized performance
# - Production WSGI server (Gunicorn)
# - Real hardware connection
# - Accessible at http://localhost:8080
```

### Raspberry Pi Deployment

For Raspberry Pi deployment:

1. **Setup script**:
   ```bash
   chmod +x setup_raspberry_pi.sh
   ./setup_raspberry_pi.sh
   ```

2. **Start service**:
   ```bash
   sudo systemctl start h743poten-web
   sudo systemctl enable h743poten-web
   ```

## 🛠️ Development

### Adding New Features

1. **Add new routes** in `src/app.py`
2. **Create services** in `src/services/`
3. **Add hardware interfaces** in `src/hardware/`
4. **Update templates** in `src/templates/`
5. **Add static assets** in `src/static/`

### Testing

```bash
# Test imports
python test_imports.py

# Run with mock hardware
FLASK_ENV=development USE_MOCK_HARDWARE=True python main_dev.py

# Test Docker builds
docker-compose build
```

### Debugging

```bash
# View container logs
docker logs h743poten-dev -f

# Debug inside container
docker exec -it h743poten-dev bash

# Check port usage
netstat -tulpn | grep :5000
```

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   # Test imports
   python test_imports.py
   
   # Check Python path
   export PYTHONPATH=/path/to/project/src
   ```

2. **Device Connection Issues**:
   ```bash
   # Check device permissions (Linux)
   sudo usermod -a -G dialout $USER
   
   # List available ports
   python -c "import serial.tools.list_ports; print([p.device for p in serial.tools.list_ports.comports()])"
   ```

3. **Docker Issues**:
   ```bash
   # Rebuild containers
   docker-compose build --no-cache
   
   # Check Docker logs
   docker logs h743poten-dev
   
   # Clean up
   docker system prune -a
   ```

4. **Port Conflicts**:
   ```bash
   # Check what's using the port
   netstat -tulpn | grep :5000
   
   # Change port in docker-compose.yml
   ports:
     - "5001:8080"  # Change 5000 to 5001
   ```

### Hardware-Specific Issues

1. **Serial Port Not Found**:
   - Check device connection
   - Verify driver installation
   - Try different USB ports
   - Check device permissions

2. **SCPI Communication Errors**:
   - Verify baud rate settings
   - Check cable integrity
   - Test with mock hardware first
   - Review SCPI command syntax

## 📚 Dependencies

### Python Packages

- **Flask**: Web framework
- **PySerial**: Serial communication
- **Plotly**: Data visualization
- **Gunicorn**: WSGI server (production)
- **python-dotenv**: Environment variable management

### System Dependencies

- **Docker**: Containerization
- **Docker Compose**: Container orchestration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test thoroughly
4. Update documentation
5. Submit a pull request

## 📄 License

This project is part of the H743Poten potentiostat system.

## 🆘 Support

For issues and questions:

1. Check the troubleshooting section
2. Review container logs
3. Test with mock hardware
4. Verify Docker installation

## 🔄 Version History

- **v1.0.0**: Initial release with basic web interface
- **v1.1.0**: Added Docker support and deployment scripts
- **v1.2.0**: Enhanced SCPI communication and mock hardware
- **v1.3.0**: Added measurement management and data visualization

---

**Note**: This web interface is designed to work with the STM32H743 Potentiostat firmware. Ensure your device firmware is compatible with the SCPI commands used by this interface. This application provides a user-friendly web interface for setting up and running electrochemical measurements, with full Docker support for easy deployment on Raspberry Pi and other platforms.

## Features

- 🔬 Real-time data visualization with Plotly
- 📊 Support for multiple measurement modes (CV, DPV, SWV, CA)
- 🖥️ UART/SCPI command interface
- 📁 Data export functionality (CSV)
- 🔌 Device connection management
- 📱 Responsive web interface (mobile-friendly)
- 🐳 Full Docker support for easy deployment
- 🍓 Optimized for Raspberry Pi deployment

## Quick Start with Docker

### Prerequisites

- Docker and Docker Compose installed
- For Raspberry Pi: Use the automated setup script

### Raspberry Pi Quick Setup

```bash
# Clone or copy the project to your Raspberry Pi
# Run the automated setup script
chmod +x setup_raspberry_pi.sh
./setup_raspberry_pi.sh
```

This script will:
- Install Docker and Docker Compose
- Configure USB device permissions
- Build and start the application
- Set up auto-start on boot
- Configure the web interface at http://your-rpi-ip:8080

### Development Environment

Start development environment with mock hardware:

```bash
# Linux/Mac
chmod +x docker-dev.sh
./docker-dev.sh dev

# Windows
docker-dev.bat dev
```

Access at: http://localhost:5000

### Production Environment

Start production environment:

```bash
# Linux/Mac
./docker-dev.sh start

# Windows
docker-dev.bat start
```

Access at: http://localhost:8080

## Manual Installation

### Requirements

- Python 3.8 or higher
- Flask
- pyserial
- Modern web browser

### Installation Steps

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Linux/Mac
   venv\Scripts\activate     # On Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env file as needed
   ```

### Manual Usage

#### Development Mode (No Hardware Required)

```bash
python main_dev.py
```

#### Production Mode

```bash
python main.py
```

## Docker Commands Reference

### Using Docker Scripts

The project includes convenient scripts for Docker management:

#### Linux/Mac (`docker-dev.sh`)

```bash
./docker-dev.sh build         # Build Docker images
./docker-dev.sh dev           # Start development environment
./docker-dev.sh start         # Start production environment
./docker-dev.sh stop          # Stop all containers
./docker-dev.sh restart       # Restart containers
./docker-dev.sh logs [dev]    # View logs
./docker-dev.sh shell [dev]   # Open shell in container
./docker-dev.sh status        # Show container status
./docker-dev.sh clean         # Remove all Docker resources
./docker-dev.sh deploy-rpi <ip> # Deploy to Raspberry Pi
```

#### Windows (`docker-dev.bat`)

```batch
docker-dev.bat build         # Build Docker images
docker-dev.bat dev           # Start development environment
docker-dev.bat start         # Start production environment
docker-dev.bat stop          # Stop all containers
docker-dev.bat logs          # View logs
docker-dev.bat status        # Show container status
```

### Direct Docker Compose Commands

```bash
# Development environment
docker-compose --profile dev up -d h743poten-dev

# Production environment
docker-compose up -d h743poten-web

# View logs
docker-compose logs -f h743poten-web

# Stop services
docker-compose down
```

## Configuration

### Environment Variables

Create a `.env` file from `.env.example` and configure:

```bash
# Flask Configuration
FLASK_ENV=production
WEB_HOST=0.0.0.0
WEB_PORT=8080

# Serial Communication
SERIAL_PORT=/dev/ttyACM0
BAUD_RATE=115200

# Security
SECRET_KEY=your-secret-key-here
```

### Serial Port Configuration

Common serial ports:
- Raspberry Pi: `/dev/ttyUSB0` or `/dev/ttyACM0`
- Linux: `/dev/ttyUSB0` or `/dev/ttyACM0`
- Windows: `COM1`, `COM2`, etc.

## API Endpoints

### Device Control
- `GET /api/connection/status` - Get device connection status
- `POST /api/connection/connect` - Connect to device
- `POST /api/connection/disconnect` - Disconnect from device
- `GET /api/device/info` - Get device information

### Measurement Control
- `GET /api/measurement/modes` - List available measurement modes
- `POST /api/measurement/setup` - Setup measurement parameters
- `POST /api/measurement/start` - Start measurement
- `POST /api/measurement/stop` - Stop measurement
- `GET /api/measurement/status` - Get measurement status

### Data Management
- `GET /api/data/current` - Get current measurement data
- `GET /api/data/export` - Export data as CSV

### UART/SCPI Interface
- `POST /api/uart/send` - Send custom SCPI commands

## Project Structure

```
H743Poten-Web/
├── src/
│   ├── config/         # Configuration settings
│   ├── hardware/       # Hardware interface code
│   ├── services/       # Business logic services
│   ├── static/         # Static web assets (CSS, JS)
│   ├── templates/      # HTML templates
│   └── app.py         # Main Flask application
├── logs/              # Application logs
├── main.py            # Production entry point
├── main_dev.py        # Development entry point
├── wsgi.py           # WSGI entry point for Gunicorn
├── requirements.txt   # Python dependencies
├── Dockerfile        # Production Docker image
├── Dockerfile.dev    # Development Docker image
├── docker-compose.yml # Docker Compose configuration
├── docker-dev.sh     # Linux/Mac Docker management script
├── docker-dev.bat    # Windows Docker management script
├── setup_raspberry_pi.sh # Raspberry Pi automated setup
├── .env.example      # Environment configuration template
└── .env.development  # Development environment settings
```

## Deployment

### Raspberry Pi Deployment

1. **Automated Setup** (Recommended):
   ```bash
   ./setup_raspberry_pi.sh
   ```

2. **Manual Deployment**:
   ```bash
   # On your development machine
   ./docker-dev.sh deploy-rpi 192.168.1.100
   ```

3. **SSH Deployment**:
   ```bash
   # Copy files to Raspberry Pi
   scp -r . pi@192.168.1.100:~/h743poten-web/
   
   # SSH to Raspberry Pi and start
   ssh pi@192.168.1.100
   cd ~/h743poten-web
   ./docker-dev.sh start
   ```

### Production Server Deployment

1. Build production image:
   ```bash
   docker build -t h743poten-web:latest .
   ```

2. Run with proper device access:
   ```bash
   docker run -d \
     --name h743poten-web \
     -p 8080:8080 \
     --privileged \
     -v /dev:/dev \
     h743poten-web:latest
   ```

## Troubleshooting

### Common Issues

1. **Permission Denied on Serial Port**:
   ```bash
   sudo usermod -a -G dialout $USER
   # Logout and login again
   ```

2. **Docker Permission Issues**:
   ```bash
   sudo usermod -a -G docker $USER
   # Logout and login again
   ```

3. **Port Already in Use**:
   ```bash
   # Check what's using the port
   sudo lsof -i :8080
   # Or change port in .env file
   ```

4. **USB Device Not Detected**:
   ```bash
   # Check connected devices
   lsusb
   # Check serial devices
   ls -la /dev/tty*
   ```

### Logs and Debugging

View application logs:
```bash
# Docker logs
./docker-dev.sh logs

# Direct logs
tail -f logs/h743poten.log
```

Debug mode:
```bash
# Start development server with debug
./docker-dev.sh dev
```

## Hardware Support

### Supported Devices
- STM32H743 based potentiostat
- USB CDC (Virtual COM Port) interface
- Standard SCPI command set

### SCPI Commands
- `*IDN?` - Device identification
- `POTEn:INFO?` - Potentiostat information
- `POTEn:STAT?` - Device status
- `POTEn:CV:START` - Start CV measurement
- `POTEn:DPV:START` - Start DPV measurement
- `POTEn:SWV:START` - Start SWV measurement
- `POTEn:CA:START` - Start CA measurement

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with both development and production Docker environments
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the troubleshooting section
- Review the logs for error messages
- Create an issue in the project repository 
