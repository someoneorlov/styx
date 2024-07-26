#!/bin/sh
set -e

# if [ -f /flyway/.env ]; then
#   . /flyway/.env  # Source the .env file to load variables
# fi

# Replace placeholders in flyway.conf.template with environment variables
envsubst < /flyway/conf/flyway.conf.template > /flyway/conf/flyway.conf

# Run Flyway with the substituted configuration file
flyway migrate