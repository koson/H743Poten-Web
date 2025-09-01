#!/bin/bash
# Setup cron jobs for H743Poten maintenance tasks

USER_ACCOUNT="potentiostat"
APP_DIR="/home/$USER_ACCOUNT/H743Poten-Web"

echo "⏰ Setting up cron jobs for H743Poten maintenance..."

# Create cron jobs for the potentiostat user
sudo -u $USER_ACCOUNT crontab -l > /tmp/potentiostat_crontab 2>/dev/null || echo "# H743Poten Crontab" > /tmp/potentiostat_crontab

# Add backup job (daily at 2 AM)
if ! grep -q "backup.sh" /tmp/potentiostat_crontab; then
    echo "0 2 * * * $APP_DIR/deploy/backup.sh >> /home/$USER_ACCOUNT/poten-data/logs/backup.log 2>&1" >> /tmp/potentiostat_crontab
    echo "✅ Added daily backup job"
fi

# Add health monitoring (every 5 minutes)
if ! grep -q "health-monitor.sh" /tmp/potentiostat_crontab; then
    echo "*/5 * * * * $APP_DIR/deploy/health-monitor.sh >> /home/$USER_ACCOUNT/poten-data/logs/health.log 2>&1" >> /tmp/potentiostat_crontab
    echo "✅ Added health monitoring job"
fi

# Add weekly health report (Sundays at 8 AM)
if ! grep -q "health-monitor.sh --report" /tmp/potentiostat_crontab; then
    echo "0 8 * * 0 $APP_DIR/deploy/health-monitor.sh --report" >> /tmp/potentiostat_crontab
    echo "✅ Added weekly health report job"
fi

# Add log cleanup (daily at 3 AM)
if ! grep -q "log cleanup" /tmp/potentiostat_crontab; then
    echo "0 3 * * * find /home/$USER_ACCOUNT/poten-data/logs -name '*.log' -mtime +30 -delete # log cleanup" >> /tmp/potentiostat_crontab
    echo "✅ Added log cleanup job"
fi

# Install the crontab
sudo -u $USER_ACCOUNT crontab /tmp/potentiostat_crontab
rm /tmp/potentiostat_crontab

echo "📋 Current cron jobs for $USER_ACCOUNT:"
sudo -u $USER_ACCOUNT crontab -l

echo "✅ Cron jobs setup completed!"
echo ""
echo "Scheduled tasks:"
echo "  - Daily backup: 2:00 AM"
echo "  - Health monitoring: Every 5 minutes"
echo "  - Weekly health report: Sunday 8:00 AM"
echo "  - Log cleanup: Daily 3:00 AM"
