#!/bin/bash
# Terminal Cleanup Script for H743Poten Project (WSL/Linux)
# ใช้สำหรับแก้ปัญหา terminal lock และ process ค้าง

echo "========================================"
echo "   H743Poten Terminal Cleanup Utility"
echo "========================================"
echo

function check_processes() {
    echo "🔍 Checking Python/Flask processes..."
    ps aux | grep -E "(python|flask|gunicorn)" | grep -v grep | grep -E "(h743|poten|main\.py|app\.py)"
    echo
}

function check_ports() {
    echo "🔍 Checking port usage..."
    netstat -tulpn 2>/dev/null | grep -E ":8080|:5000" || echo "No Flask ports in use"
    echo
}

function kill_flask_processes() {
    echo "🛑 Killing Flask/Python processes..."
    
    # หา PIDs ของ processes ที่เกี่ยวข้อง
    PIDS=$(ps aux | grep -E "(python|flask)" | grep -E "(h743|poten|main\.py|app\.py)" | grep -v grep | awk '{print $2}')
    
    if [ -z "$PIDS" ]; then
        echo "✅ No Flask processes found"
    else
        echo "📋 Found processes: $PIDS"
        for PID in $PIDS; do
            echo "🔄 Killing PID: $PID"
            kill -TERM $PID 2>/dev/null
            sleep 1
            # ตรวจสอบว่าปิดแล้วหรือยัง
            if kill -0 $PID 2>/dev/null; then
                echo "⚠️ Force killing PID: $PID"
                kill -KILL $PID 2>/dev/null
            fi
        done
        echo "✅ Process cleanup completed"
    fi
    echo
}

function kill_port_process() {
    local PORT=${1:-8080}
    echo "🛑 Killing process using port $PORT..."
    
    local PID=$(lsof -ti:$PORT 2>/dev/null)
    if [ -z "$PID" ]; then
        echo "✅ Port $PORT is free"
    else
        echo "📍 Port $PORT is used by PID: $PID"
        kill -TERM $PID 2>/dev/null
        sleep 1
        if kill -0 $PID 2>/dev/null; then
            echo "⚠️ Force killing PID: $PID"
            kill -KILL $PID 2>/dev/null
        fi
        echo "✅ Port $PORT freed"
    fi
    echo
}

function full_cleanup() {
    echo "🧹 Starting full cleanup..."
    echo "----------------------------------------"
    check_processes
    check_ports
    kill_flask_processes
    kill_port_process 8080
    echo "----------------------------------------"
    echo "🎉 Cleanup completed!"
}

# Main logic
case "${1:-full}" in
    "check")
        check_processes
        check_ports
        ;;
    "processes")
        kill_flask_processes
        ;;
    "port")
        kill_port_process ${2:-8080}
        ;;
    "full"|"")
        full_cleanup
        ;;
    "help")
        echo "Usage:"
        echo "  $0                 - Full cleanup"
        echo "  $0 check           - Check processes and ports"
        echo "  $0 processes       - Kill Python/Flask processes"
        echo "  $0 port [PORT]     - Kill process using specific port"
        echo "  $0 help            - Show this help"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        ;;
esac
