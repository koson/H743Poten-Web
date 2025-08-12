# H743Poten Web Interface

A web-based interface for controlling the H743Poten potentiostat device. This application provides a user-friendly web interface for setting up and running electrochemical measurements, with full Docker support for easy deployment on Raspberry Pi and other platforms.

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
