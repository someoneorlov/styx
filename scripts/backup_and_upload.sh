#!/bin/bash

# Load .env file
source "$(dirname "$0")/../.env"

# Network check function
check_network() {
    wget -q --spider http://google.com
    return $?
}

# Backup file name with date and time
DATE_TIME=$(date +"%Y%m%d-%H%M%S")
BACKUP_FILE="/home/ec2-user/yandex_disk/backup-$DATE_TIME.backup"

# Log file
LOG_FILE="$(dirname "$0")/../logs/yandex_disk_logfile.log"

# Create a custom-format backup
PGPASSWORD=$POSTGRES_PASS pg_dump -h localhost -p 5432 -U $POSTGRES_USER -Fc $POSTGRES_DB > $BACKUP_FILE

# Check network connectivity
if ! check_network; then
    echo "$(date) - Network is not available." >> $LOG_FILE
    exit 1
fi

# Get upload URL from Yandex Disk API
UPLOAD_URL=$(curl -s -X GET -G 'https://cloud-api.yandex.net/v1/disk/resources/upload' \
-H "Authorization: OAuth $YANDEX_OAUTH_TOKEN" \
-d "path=/styx_backup/$(basename $BACKUP_FILE)&overwrite=true" | jq -r '.href')

# Check if upload URL is received
if [ -z "$UPLOAD_URL" ]; then
    echo "$(date) - Failed to get upload URL." >> $LOG_FILE
    exit 1
fi

# Upload the file to Yandex Disk
if curl -T "$BACKUP_FILE" "$UPLOAD_URL"; then
    echo "$(date) - Backup and upload successful." >> $LOG_FILE
else
    echo "$(date) - Backup or upload failed." >> $LOG_FILE
fi

# Local backup rotation: keep the last N backups
MAX_BACKUPS=7
BACKUP_DIR="/home/ec2-user/yandex_disk"
BACKUP_FILES_LOCAL=($(ls -1tr $BACKUP_DIR/backup-*.backup))
if [ ${#BACKUP_FILES_LOCAL[@]} -gt $MAX_BACKUPS ]; then
    NUM_FILES_TO_DELETE=$((${#BACKUP_FILES_LOCAL[@]} - $MAX_BACKUPS))
    for ((i=0; i<$NUM_FILES_TO_DELETE; i++)); do
        echo "Deleting old local backup: ${BACKUP_FILES_LOCAL[i]}" >> $LOG_FILE
        rm -f "${BACKUP_FILES_LOCAL[i]}"
    done
fi

# Fetch backup file names from Yandex Disk
LIMIT=10000
MEDIA_TYPE="data"
FIELDS="name"
FILES_JSON=$(curl -s -H "Authorization: OAuth $YANDEX_OAUTH_TOKEN" \
"https://cloud-api.yandex.net/v1/disk/resources/files?limit=$LIMIT&media_type=$MEDIA_TYPE&fields=items.$FIELDS")
BACKUP_FILES=$(echo $FILES_JSON | jq -r '.items[] | select(.name | startswith("backup-")) | .name' | sort | head -n -$MAX_BACKUPS)

# Delete old backups from Yandex Disk
for file in $BACKUP_FILES; do
    DELETE_URL="https://cloud-api.yandex.net/v1/disk/resources?path=/styx_backup/$file&permanently=true"
    DELETE_RESPONSE=$(curl -s -X DELETE -H "Authorization: OAuth $YANDEX_OAUTH_TOKEN" "$DELETE_URL")
    if [ -n "$DELETE_RESPONSE" ]; then
        echo "Failed to delete old backup from Yandex Disk: $file"  # Debug line
        echo "$(date) - Failed to delete old backup from Yandex Disk: $file" >> $LOG_FILE
    else
        echo "Deleted old backup from Yandex Disk: $file"  # Debug line
        echo "$(date) - Deleted old backup from Yandex Disk: $file" >> $LOG_FILE
    fi
done
