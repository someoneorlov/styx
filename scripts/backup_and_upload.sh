#!/bin/bash

cur_dir=$(dirname "$0")

# Load .env file
source "$cur_dir/../.env"
source "$cur_dir/../.env.prod"

# Network check function
check_network() {
    wget -q --spider http://google.com
    return $?
}

# Backup file name with date and time
date_time=$(date +"%Y%m%d-%H%M%S")
backup_file="$cur_dir/../data/yandex_disk_backup/backup-$date_time.backup"

# Log file
log_file="$cur_dir/../logs_prod/yandex_disk_logfile.log"

# Create a custom-format backup
PGPASSWORD=$POSTGRES_PASS pg_dump -h localhost -p 5432 -U $POSTGRES_USER -Fc $POSTGRES_DB > $backup_file

# Check network connectivity
if ! check_network; then
    echo "$(date) - Network is not available." >> $log_file
    exit 1
fi

# Get upload URL from Yandex Disk API
upload_url=$(curl -s -X GET -G 'https://cloud-api.yandex.net/v1/disk/resources/upload' \
-H "Authorization: OAuth $YANDEX_OAUTH_TOKEN" \
-d "path=/styx_backup/$(basename $backup_file)&overwrite=true" | jq -r '.href')

# Check if upload URL is received
if [ -z "$upload_url" ]; then
    echo "$(date) - Failed to get upload URL." >> $log_file
    exit 1
fi

# Upload the file to Yandex Disk
if curl -T "$backup_file" "$upload_url"; then
    echo "$(date) - Backup and upload successful." >> $log_file
else
    echo "$(date) - Backup or upload failed." >> $log_file
fi

# Local backup rotation: keep the last N backups
max_backups=7
backup_dir="$cur_dir/../data/yandex_disk_backup"
backup_files_local=($(ls -1tr $backup_dir/backup-*.backup))
if [ ${#backup_files_local[@]} -gt $max_backups ]; then
    num_files_to_delete=$((${#backup_files_local[@]} - $max_backups))
    for ((i=0; i<$num_files_to_delete; i++)); do
        echo "Deleting old local backup: ${backup_files_local[i]}" >> $log_file
        rm -f "${backup_files_local[i]}"
    done
fi

# Fetch backup file names from Yandex Disk
limit=10000
media_type="data"
fields="name"
files_json=$(curl -s -H "Authorization: OAuth $YANDEX_OAUTH_TOKEN" \
"https://cloud-api.yandex.net/v1/disk/resources/files?limit=$limit&media_type=$media_type&fields=items.$fields")
backup_fileS=$(echo $files_json | jq -r '.items[] | select(.name | startswith("backup-")) | .name' | sort | head -n -$max_backups)

# Delete old backups from Yandex Disk
for file in $backup_fileS; do
    delete_url="https://cloud-api.yandex.net/v1/disk/resources?path=/styx_backup/$file&permanently=true"
    delete_response=$(curl -s -X DELETE -H "Authorization: OAuth $YANDEX_OAUTH_TOKEN" "$delete_url")
    if [ -n "$delete_response" ]; then
        echo "Failed to delete old backup from Yandex Disk: $file"  # Debug line
        echo "$(date) - Failed to delete old backup from Yandex Disk: $file" >> $log_file
    else
        echo "Deleted old backup from Yandex Disk: $file"  # Debug line
        echo "$(date) - Deleted old backup from Yandex Disk: $file" >> $log_file
    fi
done
