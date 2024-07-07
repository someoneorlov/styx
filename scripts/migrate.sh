#!/bin/bash
set -e

# Set Flyway directory
flyway_dir="/flyway/sql"

# Execute Flyway command
flyway_url="jdbc:postgresql://${DB_HOST}:${DB_PORT}/${POSTGRES_DB}"
/flyway/flyway -url=${flyway_url} -user=${DB_USER} -password=${DB_PASS} migrate
