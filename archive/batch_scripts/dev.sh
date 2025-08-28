#!/bin/bash
# H743Poten Development Server Manager for Linux/WSL
# แก้ปัญหา VS Code terminal lock

# ตรวจสอบว่ามี Python หรือไม่
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found in WSL!"
    echo "💡 Please install Python in WSL:"
    echo "   sudo apt update && sudo apt install python3 python3-pip"
    exit 1
fi

show_help() {
    echo "=============================================="
    echo " H743Poten Development Environment (WSL/Linux)"
    echo "=============================================="
    echo "Commands:"
    echo "  ./dev.sh start             - Start development server"
    echo "  ./dev.sh stop              - Stop development server"
    echo "  ./dev.sh status            - Check server status"
    echo "  ./dev.sh logs              - Show server logs (50 lines)"
    echo "  ./dev.sh logs 100          - Show server logs (100 lines)"
    echo "  ./dev.sh logs 20 ERROR     - Show logs containing \"ERROR\""
    echo "  ./dev.sh auto              - Auto-start with status check"
    echo ""
    echo "Python Command: $PYTHON_CMD"
    echo ""
    echo "Current Status:"
    if [ -f "terminal_manager.py" ]; then
        $PYTHON_CMD terminal_manager.py status 2>/dev/null || echo "❌ Terminal manager not working"
    else
        echo "❌ terminal_manager.py not found"
    fi
    echo "=============================================="
}

case "$1" in
    "start")
        echo "Starting H743Poten Development Server..."
        if [ -f "terminal_manager.py" ]; then
            $PYTHON_CMD terminal_manager.py start
        else
            echo "❌ terminal_manager.py not found"
            echo "💡 Make sure you're in the correct directory"
        fi
        ;;
    "stop")
        echo "Stopping H743Poten Development Server..."
        if [ -f "terminal_manager.py" ]; then
            $PYTHON_CMD terminal_manager.py stop
        else
            echo "❌ terminal_manager.py not found"
        fi
        ;;
    "status")
        if [ -f "terminal_manager.py" ]; then
            $PYTHON_CMD terminal_manager.py status
        else
            echo "❌ terminal_manager.py not found"
        fi
        ;;
    "logs")
        if [ -f "terminal_manager.py" ]; then
            if [ -z "$2" ]; then
                $PYTHON_CMD terminal_manager.py logs
            elif [ -z "$3" ]; then
                $PYTHON_CMD terminal_manager.py logs "$2"
            else
                $PYTHON_CMD terminal_manager.py logs "$2" "$3"
            fi
        else
            echo "❌ terminal_manager.py not found"
        fi
        ;;
    "auto")
        echo "H743Poten Auto-Start Mode"
        echo "=========================="
        if [ -f "terminal_manager.py" ]; then
            if ! $PYTHON_CMD terminal_manager.py status >/dev/null 2>&1; then
                echo "Server not running, starting..."
                $PYTHON_CMD terminal_manager.py start
            else
                echo "Server already running!"
            fi
        else
            echo "❌ terminal_manager.py not found"
        fi
        ;;
    *)
        show_help
        ;;
esac
