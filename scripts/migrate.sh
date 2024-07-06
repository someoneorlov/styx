#!/bin/bash
set -e

# Check the environment variable
if [ -z "$ENVIRONMENT" ]; then
    echo "Environment not set. Please set the ENVIRONMENT variable."
    exit 1
fi

# Set Flyway directory
flyway_dir="/flyway/sql"

# Execute Flyway command
flyway_url="jdbc:postgresql://db_${ENVIRONMENT}:${DB_PORT}/${POSTGRES_DB}"
/flyway/flyway -url=${flyway_url} -user=${DB_USER} -password=${DB_PASS} migrate
