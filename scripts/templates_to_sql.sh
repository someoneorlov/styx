#!/bin/bash
set -e

# Check the environment variable
if [ "$ENVIRONMENT" == "test" ]; then
    template_dir="/flyway/templates/test"
    flyway_dir="/flyway/sql/test"
elif [ "$ENVIRONMENT" == "prod" ]; then
    template_dir="/flyway/templates/prod"
    flyway_dir="/flyway/sql/prod"
else
    echo "Environment not set or invalid."
    exit 1
fi

# Create the Flyway directory if it doesn't exist
mkdir -p $flyway_dir

# Process each SQL template file in the template directory
for template in $template_dir/*.sql.template; do
    # Check if the template file exists and is writable
    if [ -f "$template" ] && [ -w "$template" ]; then
        # Derive the actual SQL file name from the template name
        sql_file="$flyway_dir/$(basename "${template%.template}")"

        # Create SQL file from template
        envsubst < "$template" > "$sql_file"
    else
        echo "Template file $template missing or not writable"
        exit 1
    fi
done

# Execute Flyway command
flyway_url="jdbc:postgresql://db_${ENVIRONMENT}:${DB_PORT}/${POSTGRES_DB}"
# /flyway/flyway -url=${flyway_url} -user=${DB_USER} -password=${DB_PASS} repair
/flyway/flyway -url=${flyway_url} -user=${DB_USER} -password=${DB_PASS} migrate
