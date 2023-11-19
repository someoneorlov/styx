#!/bin/bash
set -e

# Debug: List files and permissions
ls -l /docker-entrypoint-initdb.d/

# Check if the template file exists and is writable
if [ -f "/docker-entrypoint-initdb.d/01_create_user.sql.template" ] && [ -w "/docker-entrypoint-initdb.d/01_create_user.sql.template" ]; then
    # Create SQL file directly in /docker-entrypoint-initdb.d/
    envsubst < "/docker-entrypoint-initdb.d/01_create_user.sql.template" > "/docker-entrypoint-initdb.d/01_create_user.sql"
else
    echo "Template file missing or not writable"
    exit 1
fi

# Execute the SQL script
if [ -f "/docker-entrypoint-initdb.d/01_create_user.sql" ] && [ -w "/docker-entrypoint-initdb.d/01_create_user.sql" ]; then
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "/docker-entrypoint-initdb.d/01_create_user.sql"
else
    echo "SQL file missing or not writable"
    exit 1
fi