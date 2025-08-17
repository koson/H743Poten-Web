#!/bin/bash
# Simple WSL Setup for H743Poten Development
# ใช้เมื่อ Python ยังไม่ได้ติดตั้งใน WSL

echo "=============================================="
echo " H743Poten WSL Environment Setup"
echo "=============================================="

# ตรวจสอบว่าอยู่ใน WSL หรือไม่
if grep -q microsoft /proc/version; then
    echo "✅ Running in WSL"
else
    echo "❌ This script is designed for WSL"
    exit 1
fi

# ตรวจสอบการติดตั้ง Python
if command -v python3 &> /dev/null; then
    echo "✅ Python3 is installed"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    echo "✅ Python is installed"
    PYTHON_CMD="python"
else
    echo "❌ Python not found!"
    echo ""
    echo "Installing Python..."
    echo "Run these commands:"
    echo "  sudo apt update"
    echo "  sudo apt install python3 python3-pip python3-venv"
    echo ""
    
    # ถาม user ว่าต้องการติดตั้งหรือไม่
    read -p "Do you want to install Python now? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing Python..."
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv
        
        if command -v python3 &> /dev/null; then
            echo "✅ Python3 installed successfully!"
            PYTHON_CMD="python3"
        else
            echo "❌ Failed to install Python3"
            exit 1
        fi
    else
        echo "Please install Python manually and try again."
        exit 1
    fi
fi

# ตรวจสอบ requirements
echo ""
echo "Checking Python requirements..."

if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    $PYTHON_CMD -m pip install --user -r requirements.txt
else
    echo "❌ requirements.txt not found"
fi

# ตั้งค่า alias สำหรับ dev command
echo ""
echo "Setting up dev command alias..."

# เพิ่ม alias ใน .bashrc ถ้ายังไม่มี
if ! grep -q "alias dev=" ~/.bashrc; then
    echo "alias dev='./dev.sh'" >> ~/.bashrc
    echo "✅ Added 'dev' alias to ~/.bashrc"
fi

# ทำให้ dev.sh executable
chmod +x dev.sh

echo ""
echo "=============================================="
echo " Setup Complete!"
echo "=============================================="
echo "You can now use:"
echo "  ./dev.sh          - Show help"
echo "  ./dev.sh status   - Check server status"
echo "  dev status        - Same as above (after restart)"
echo ""
echo "Note: Restart your terminal or run 'source ~/.bashrc' to use 'dev' command"
echo "=============================================="
