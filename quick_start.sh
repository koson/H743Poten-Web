#!/bin/bash

# H743 Potentiostat Research Platform - Quick Start
# เริ่มต้นใช้งานระบบวิจัยแบบครบครัน

echo "🔬 H743 Potentiostat Research Platform - Quick Start"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're on Pi or development machine
if [[ $(hostname) == *"raspberrypi"* ]] || [[ -f /etc/rpi-issue ]]; then
    echo -e "${BLUE}📟 Detected Raspberry Pi environment${NC}"
    IS_PI=true
else
    echo -e "${BLUE}💻 Detected development environment${NC}"
    IS_PI=false
fi

# Function to check if virtual environment exists
check_venv() {
    if [ -d "poten-env" ]; then
        echo -e "${GREEN}✅ Virtual environment found${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
        return 1
    fi
}

# Function to create virtual environment
create_venv() {
    echo -e "${BLUE}🔧 Creating virtual environment...${NC}"
    python3 -m venv poten-env
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Virtual environment created${NC}"
    else
        echo -e "${RED}❌ Failed to create virtual environment${NC}"
        exit 1
    fi
}

# Function to activate virtual environment
activate_venv() {
    echo -e "${BLUE}🔄 Activating virtual environment...${NC}"
    source poten-env/bin/activate
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Virtual environment activated${NC}"
    else
        echo -e "${RED}❌ Failed to activate virtual environment${NC}"
        exit 1
    fi
}

# Function to install dependencies
install_deps() {
    echo -e "${BLUE}📦 Installing dependencies...${NC}"
    
    if $IS_PI; then
        # Pi-specific dependencies
        pip install -r requirements-pi.txt
        pip install -r requirements-enhanced.txt
    else
        # Development dependencies
        pip install -r requirements-enhanced.txt
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Dependencies installed${NC}"
    else
        echo -e "${RED}❌ Failed to install dependencies${NC}"
        exit 1
    fi
}

# Function to check hardware connection (Pi only)
check_hardware() {
    if $IS_PI; then
        echo -e "${BLUE}🔍 Checking hardware connection...${NC}"
        
        # Check for STM32 device
        if ls /dev/ttyACM* 1> /dev/null 2>&1; then
            echo -e "${GREEN}✅ STM32 device found: $(ls /dev/ttyACM*)${NC}"
        elif ls /dev/ttyUSB* 1> /dev/null 2>&1; then
            echo -e "${GREEN}✅ USB device found: $(ls /dev/ttyUSB*)${NC}"
        else
            echo -e "${YELLOW}⚠️  No hardware device found${NC}"
            echo -e "${YELLOW}    Make sure STM32 H743 is connected via USB${NC}"
        fi
    fi
}

# Function to show startup options
show_options() {
    echo ""
    echo -e "${BLUE}🚀 Choose startup option:${NC}"
    echo "1) 🌐 Full Online Mode (SCPI Server + Web Interface)"
    echo "2) 📱 Offline Research Mode (Local Web Interface Only)"
    echo "3) 🛠️  SCPI Server Only"
    echo "4) 📊 File Browser Only"
    echo "5) 🔧 Development Mode"
    echo ""
    read -p "Enter choice (1-5): " choice
    
    case $choice in
        1)
            start_full_mode
            ;;
        2)
            start_offline_mode
            ;;
        3)
            start_scpi_only
            ;;
        4)
            start_file_browser
            ;;
        5)
            start_dev_mode
            ;;
        *)
            echo -e "${RED}❌ Invalid choice${NC}"
            show_options
            ;;
    esac
}

# Startup modes
start_full_mode() {
    echo -e "${GREEN}🌐 Starting Full Online Mode...${NC}"
    echo -e "${BLUE}   SCPI Server: http://localhost:8081${NC}"
    echo -e "${BLUE}   Web Interface: http://localhost:8082${NC}"
    
    # Start SCPI server in background
    echo "Starting SCPI server..."
    python scpi_server_standalone.py --host 0.0.0.0 --port 8081 &
    SCPI_PID=$!
    sleep 3
    
    # Start web frontend
    echo "Starting web frontend..."
    python research_platform_offline.py --host 0.0.0.0 --port 8082
    
    # Cleanup on exit
    kill $SCPI_PID 2>/dev/null
}

start_offline_mode() {
    echo -e "${GREEN}📱 Starting Offline Research Mode...${NC}"
    echo -e "${BLUE}   Web Interface: http://localhost:8080${NC}"
    echo -e "${YELLOW}   Note: Hardware measurements disabled, mock data available${NC}"
    
    python research_platform_offline.py --host 0.0.0.0 --port 8080
}

start_scpi_only() {
    echo -e "${GREEN}🛠️  Starting SCPI Server Only...${NC}"
    echo -e "${BLUE}   SCPI Server: http://localhost:8081${NC}"
    
    python scpi_server_standalone.py --host 0.0.0.0 --port 8081
}

start_file_browser() {
    echo -e "${GREEN}📊 Starting File Browser...${NC}"
    echo -e "${BLUE}   File Browser: http://localhost:8083${NC}"
    
    python -c "
from file_browser import create_app
app = create_app()
app.run(host='0.0.0.0', port=8083, debug=False)
"
}

start_dev_mode() {
    echo -e "${GREEN}🔧 Starting Development Mode...${NC}"
    
    if $IS_PI; then
        echo "Using Pi development script..."
        python main_dev.py
    else
        echo "Starting local development server..."
        python research_platform_offline.py --host 127.0.0.1 --port 8080 --debug
    fi
}

# Main execution
main() {
    # Check and setup virtual environment
    if ! check_venv; then
        create_venv
    fi
    
    activate_venv
    
    # Install/update dependencies
    echo -e "${BLUE}🔄 Checking dependencies...${NC}"
    install_deps
    
    # Check hardware (Pi only)
    check_hardware
    
    # Show startup options
    show_options
}

# Handle Ctrl+C
trap 'echo -e "\n${YELLOW}👋 Shutting down...${NC}"; exit 0' INT

# Run main function
main