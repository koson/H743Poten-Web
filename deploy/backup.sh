#!/bin/bash
# H743Poten Backup Script
# Run daily via cron: 0 2 * * * /home/potentiostat/H743Poten-Web/deploy/backup.sh

set -e

# Configuration
USER_ACCOUNT="potentiostat"
BASE_DIR="/home/$USER_ACCOUNT"
BACKUP_DIR="$BASE_DIR/poten-backups"
DATA_DIR="$BASE_DIR/poten-data"
APP_DIR="$BASE_DIR/H743Poten-Web"
RETENTION_DAYS=30

# Ensure running as correct user
if [ "$(whoami)" != "$USER_ACCOUNT" ]; then
    echo "Error: This script must run as user $USER_ACCOUNT"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="poten_backup_$TIMESTAMP"

echo "🔄 Starting H743Poten backup: $BACKUP_NAME"

# Create temporary directory for backup
TEMP_DIR="/tmp/$BACKUP_NAME"
mkdir -p "$TEMP_DIR"

# Copy data directory
echo "📁 Backing up data directory..."
cp -r "$DATA_DIR" "$TEMP_DIR/poten-data"

# Copy application logs
echo "📄 Backing up application logs..."
mkdir -p "$TEMP_DIR/app-logs"
cp -r "$APP_DIR/data_logs" "$TEMP_DIR/app-logs/" 2>/dev/null || true
cp -r "$APP_DIR/logs" "$TEMP_DIR/app-logs/" 2>/dev/null || true

# Copy configuration files
echo "⚙️ Backing up configuration..."
mkdir -p "$TEMP_DIR/config"
cp "$APP_DIR/config/"*.py "$TEMP_DIR/config/" 2>/dev/null || true
cp "$APP_DIR/"*.json "$TEMP_DIR/config/" 2>/dev/null || true

# Create backup metadata
echo "📋 Creating backup metadata..."
cat > "$TEMP_DIR/backup_info.txt" << EOF
H743Poten Backup Information
===========================
Backup Date: $(date)
System: $(uname -a)
User: $(whoami)
Python Version: $(python3 --version)
Disk Usage: $(du -sh "$DATA_DIR" 2>/dev/null || echo "Unknown")

Contents:
- Data directory: $DATA_DIR
- Application logs: $APP_DIR/data_logs, $APP_DIR/logs
- Configuration files
- Service status at backup time

Service Status:
$(systemctl status potentiostat --no-pager -l 2>/dev/null || echo "Service status unavailable")
EOF

# Create compressed archive
echo "📦 Creating compressed archive..."
cd /tmp
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" "$BACKUP_NAME"

# Calculate size and checksum
BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME.tar.gz" | cut -f1)
BACKUP_CHECKSUM=$(sha256sum "$BACKUP_DIR/$BACKUP_NAME.tar.gz" | cut -d' ' -f1)

# Clean up temporary directory
rm -rf "$TEMP_DIR"

echo "✅ Backup completed: $BACKUP_NAME.tar.gz ($BACKUP_SIZE)"
echo "🔒 SHA256: $BACKUP_CHECKSUM"

# Log backup completion
echo "$(date): Backup completed - $BACKUP_NAME.tar.gz ($BACKUP_SIZE) SHA256:$BACKUP_CHECKSUM" >> "$BACKUP_DIR/backup.log"

# Clean up old backups
echo "🧹 Cleaning up old backups (keeping last $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "poten_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Count remaining backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "poten_backup_*.tar.gz" | wc -l)
echo "📊 Total backups: $BACKUP_COUNT"

# Check disk space
DISK_USAGE=$(df -h "$BACKUP_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    echo "⚠️ Warning: Disk usage is $DISK_USAGE% - consider cleaning up old backups"
fi

echo "🎉 Backup process completed successfully!"
