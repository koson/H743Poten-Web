#!/bin/bash

# H743Poten Web Interface - Raspberry Pi Quick Start Script
# This script sets up and runs H743Poten Web Interface on Raspberry Pi

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[H743Poten RPi]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Raspberry Pi
check_raspberry_pi() {
    if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
        print_warning "This script is optimized for Raspberry Pi, but will continue anyway"
    else
        print_success "Running on Raspberry Pi"
    fi
}

# Install Docker if not present
install_docker() {
    if ! command -v docker &> /dev/null; then
        print_status "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
        print_success "Docker installed successfully"
        print_warning "Please log out and log back in to apply group changes"
    else
        print_success "Docker is already installed"
    fi
}

# Install Docker Compose if not present
install_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_status "Installing Docker Compose..."
        sudo apt-get update
        sudo apt-get install -y docker-compose
        print_success "Docker Compose installed successfully"
    else
        print_success "Docker Compose is already installed"
    fi
}

# Setup udev rules for USB devices
setup_udev_rules() {
    print_status "Setting up udev rules for USB devices..."
    
    # Create udev rule for STM32 devices
    sudo tee /etc/udev/rules.d/99-stm32.rules > /dev/null << 'EOF'
# STM32 Virtual COM Port
SUBSYSTEM=="tty", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", MODE="0666", GROUP="dialout"
# STM32 DFU Mode
SUBSYSTEM=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="df11", MODE="0666", GROUP="plugdev"
EOF
    
    # Reload udev rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    
    # Add user to dialout group
    sudo usermod -a -G dialout $USER
    
    print_success "Udev rules configured"
}

# Create application directory
setup_directory() {
    APP_DIR="$HOME/h743poten-web"
    if [ ! -d "$APP_DIR" ]; then
        print_status "Creating application directory..."
        mkdir -p "$APP_DIR"
        cd "$APP_DIR"
    else
        print_status "Using existing application directory"
        cd "$APP_DIR"
    fi
}

# Download or update application
setup_application() {
    print_status "Setting up H743Poten Web Interface..."
    
    # If this script is being run from the source directory, copy files
    if [ -f "../docker-compose.yml" ]; then
        print_status "Copying application files..."
        cp -r ../* .
    else
        print_error "Please run this script from the H743Poten-Web directory"
        exit 1
    fi
}

# Configure environment
configure_environment() {
    print_status "Configuring environment..."
    
    # Copy environment file if not exists
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_status "Environment file created. Please edit .env if needed."
    fi
    
    # Set correct serial port for Raspberry Pi
    if [ -f ".env" ]; then
        sed -i 's|SERIAL_PORT=/dev/ttyACM0|SERIAL_PORT=/dev/ttyUSB0|g' .env
    fi
}

# Build and start application
start_application() {
    print_status "Building and starting H743Poten Web Interface..."
    
    # Build the images
    docker-compose build
    
    # Start the production service
    docker-compose up -d h743poten-web
    
    # Wait a moment for the service to start
    sleep 5
    
    # Check if service is running
    if docker-compose ps | grep -q "h743poten-web.*Up"; then
        print_success "H743Poten Web Interface is running!"
        print_status "Access the web interface at:"
        echo "  Local: http://localhost:8080"
        echo "  Network: http://$(hostname -I | awk '{print $1}'):8080"
    else
        print_error "Failed to start the application"
        print_status "Check logs with: docker-compose logs h743poten-web"
        exit 1
    fi
}

# Setup systemd service for auto-start
setup_systemd_service() {
    print_status "Setting up systemd service for auto-start..."
    
    sudo tee /etc/systemd/system/h743poten-web.service > /dev/null << EOF
[Unit]
Description=H743Poten Web Interface
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$HOME/h743poten-web
ExecStart=/usr/bin/docker-compose up -d h743poten-web
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0
User=$USER
Group=$USER

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable h743poten-web.service
    
    print_success "Systemd service configured for auto-start on boot"
}

# Show status and next steps
show_status() {
    print_success "Setup completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Access the web interface at http://$(hostname -I | awk '{print $1}'):8080"
    echo "2. Connect your H743Poten device via USB"
    echo "3. Use the web interface to control your potentiostat"
    echo
    echo "Useful commands:"
    echo "  ./docker-dev.sh status    # Check application status"
    echo "  ./docker-dev.sh logs      # View application logs"
    echo "  ./docker-dev.sh restart   # Restart the application"
    echo "  ./docker-dev.sh stop      # Stop the application"
    echo
}

# Main installation process
main() {
    print_status "Starting H743Poten Web Interface setup for Raspberry Pi..."
    
    check_raspberry_pi
    install_docker
    install_docker_compose
    setup_udev_rules
    setup_directory
    setup_application
    configure_environment
    start_application
    setup_systemd_service
    show_status
    
    print_success "H743Poten Web Interface is ready to use!"
}

# Handle command line arguments
case "${1:-}" in
    "install"|"setup"|"")
        main
        ;;
    "start")
        docker-compose up -d h743poten-web
        print_success "H743Poten Web Interface started"
        ;;
    "stop")
        docker-compose down
        print_success "H743Poten Web Interface stopped"
        ;;
    "restart")
        docker-compose restart h743poten-web
        print_success "H743Poten Web Interface restarted"
        ;;
    "status")
        docker-compose ps
        ;;
    "logs")
        docker-compose logs -f h743poten-web
        ;;
    "help"|"--help"|"-h")
        echo "H743Poten Web Interface - Raspberry Pi Setup"
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  install/setup  Install and setup everything (default)"
        echo "  start          Start the application"
        echo "  stop           Stop the application"
        echo "  restart        Restart the application"
        echo "  status         Show application status"
        echo "  logs           Show application logs"
        echo "  help           Show this help"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac
