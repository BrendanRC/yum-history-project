#!/bin/bash
# Setup script for automated yum history uploads

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_JOB="*/5 * * * * $SCRIPT_DIR/auto_upload.py >> /var/log/yum-history-upload.log 2>&1"

echo "Setting up automated yum history uploads..."

# Add environment variables to root's crontab environment
echo "Adding cron job to upload yum history every 5 minutes..."

# Create a temporary cron file
crontab -l > /tmp/current_cron 2>/dev/null || touch /tmp/current_cron

# Check if the job already exists
if ! grep -q "auto_upload.py" /tmp/current_cron; then
    echo "S3_BUCKET_NAME=package-history-3ddh4rp4" >> /tmp/current_cron
    echo "$CRON_JOB" >> /tmp/current_cron
    crontab /tmp/current_cron
    echo "Cron job added successfully"
else
    echo "Cron job already exists"
fi

rm -f /tmp/current_cron

echo "Setup complete!"
echo "Yum history will be automatically uploaded to S3 every 5 minutes after package operations."
echo "Log file: /var/log/yum-history-upload.log"
