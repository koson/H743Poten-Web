#!/bin/bash
# H743Poten System Health Monitor
# Check system health and send alerts if needed

set -e

# Configuration
USER_ACCOUNT="potentiostat"
SERVICE_NAME="potentiostat"
LOG_FILE="/home/$USER_ACCOUNT/poten-data/logs/health_monitor.log"
ALERT_EMAIL=""  # Set email for alerts (optional)

# Thresholds
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90
TEMP_THRESHOLD=70

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
    log "INFO: $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
    log "SUCCESS: $1"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    log "WARNING: $1"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    log "ERROR: $1"
}

# Check if service is running
check_service() {
    info "Checking $SERVICE_NAME service..."
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        success "Service is running"
        
        # Check service uptime
        UPTIME=$(systemctl show $SERVICE_NAME --property=ActiveEnterTimestamp --value)
        if [ -n "$UPTIME" ]; then
            info "Service uptime: Started at $UPTIME"
        fi
        
        return 0
    else
        error "Service is not running"
        
        # Try to restart service
        warning "Attempting to restart service..."
        if sudo systemctl restart $SERVICE_NAME; then
            sleep 5
            if systemctl is-active --quiet $SERVICE_NAME; then
                success "Service restarted successfully"
                return 0
            else
                error "Failed to restart service"
                return 1
            fi
        else
            error "Failed to restart service"
            return 1
        fi
    fi
}

# Check system resources
check_resources() {
    info "Checking system resources..."
    
    # CPU usage
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    CPU_USAGE=${CPU_USAGE%.*}  # Remove decimal
    
    if [ "$CPU_USAGE" -gt "$CPU_THRESHOLD" ]; then
        warning "High CPU usage: ${CPU_USAGE}%"
    else
        success "CPU usage: ${CPU_USAGE}%"
    fi
    
    # Memory usage
    MEMORY_INFO=$(free | grep Mem)
    MEMORY_TOTAL=$(echo $MEMORY_INFO | awk '{print $2}')
    MEMORY_USED=$(echo $MEMORY_INFO | awk '{print $3}')
    MEMORY_USAGE=$((MEMORY_USED * 100 / MEMORY_TOTAL))
    
    if [ "$MEMORY_USAGE" -gt "$MEMORY_THRESHOLD" ]; then
        warning "High memory usage: ${MEMORY_USAGE}%"
    else
        success "Memory usage: ${MEMORY_USAGE}%"
    fi
    
    # Disk usage
    DISK_USAGE=$(df -h /home | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [ "$DISK_USAGE" -gt "$DISK_THRESHOLD" ]; then
        warning "High disk usage: ${DISK_USAGE}%"
    else
        success "Disk usage: ${DISK_USAGE}%"
    fi
}

# Check temperature (Raspberry Pi specific)
check_temperature() {
    if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
        info "Checking system temperature..."
        
        TEMP_RAW=$(cat /sys/class/thermal/thermal_zone0/temp)
        TEMP_C=$((TEMP_RAW / 1000))
        
        if [ "$TEMP_C" -gt "$TEMP_THRESHOLD" ]; then
            warning "High temperature: ${TEMP_C}°C"
        else
            success "Temperature: ${TEMP_C}°C"
        fi
    fi
}

# Check network connectivity
check_network() {
    info "Checking network connectivity..."
    
    # Check if port 8080 is listening
    if netstat -tulpn | grep -q ":8080"; then
        success "Application port 8080 is listening"
    else
        warning "Application port 8080 is not listening"
    fi
    
    # Check internet connectivity (optional)
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        success "Internet connectivity OK"
    else
        warning "No internet connectivity"
    fi
}

# Check application health
check_application() {
    info "Checking application health..."
    
    # Check if application responds
    if curl -s http://localhost:8080/health >/dev/null 2>&1; then
        success "Application health endpoint responding"
    else
        warning "Application health endpoint not responding"
    fi
    
    # Check recent logs for errors
    LOG_ERRORS=$(journalctl -u $SERVICE_NAME --since "5 minutes ago" | grep -i error | wc -l)
    if [ "$LOG_ERRORS" -gt 0 ]; then
        warning "Found $LOG_ERRORS error(s) in recent logs"
    else
        success "No recent errors in logs"
    fi
}

# Check file system
check_filesystem() {
    info "Checking file system..."
    
    # Check if critical directories exist and are writable
    CRITICAL_DIRS=(
        "/home/$USER_ACCOUNT/poten-data"
        "/home/$USER_ACCOUNT/poten-data/measurements"
        "/home/$USER_ACCOUNT/poten-data/logs"
        "/home/$USER_ACCOUNT/H743Poten-Web/data_logs"
    )
    
    for dir in "${CRITICAL_DIRS[@]}"; do
        if [ -d "$dir" ] && [ -w "$dir" ]; then
            success "Directory OK: $dir"
        else
            error "Directory issue: $dir"
        fi
    done
}

# Generate health report
generate_report() {
    REPORT_FILE="/tmp/health_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$REPORT_FILE" << EOF
H743Poten System Health Report
=============================
Generated: $(date)
Hostname: $(hostname)
Uptime: $(uptime)

System Resources:
- CPU Usage: ${CPU_USAGE}%
- Memory Usage: ${MEMORY_USAGE}%
- Disk Usage: ${DISK_USAGE}%
$([ -n "$TEMP_C" ] && echo "- Temperature: ${TEMP_C}°C")

Service Status:
$(systemctl status $SERVICE_NAME --no-pager -l)

Recent Logs (last 20 lines):
$(journalctl -u $SERVICE_NAME --no-pager -n 20)

Process Information:
$(ps aux | grep -E "(python|potentiostat)" | grep -v grep)

Network Status:
$(netstat -tulpn | grep :8080)

Disk Space:
$(df -h)
EOF

    info "Health report generated: $REPORT_FILE"
    
    # If email is configured, send report
    if [ -n "$ALERT_EMAIL" ] && command -v mail >/dev/null; then
        mail -s "H743Poten Health Report - $(hostname)" "$ALERT_EMAIL" < "$REPORT_FILE"
        info "Health report sent to $ALERT_EMAIL"
    fi
}

# Main health check
main() {
    echo "🏥 H743Poten System Health Monitor"
    echo "================================="
    
    # Ensure log directory exists
    mkdir -p "$(dirname "$LOG_FILE")"
    
    log "Starting health check"
    
    # Run all checks
    check_service
    check_resources
    check_temperature
    check_network
    check_application
    check_filesystem
    
    # Generate report if requested
    if [ "$1" = "--report" ]; then
        generate_report
    fi
    
    log "Health check completed"
    success "Health check completed successfully!"
}

# Run health check
main "$@"
