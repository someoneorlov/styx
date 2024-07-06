#!/bin/bash
set -e

# Debug: List files and permissions
ls -l /docker-entrypoint-initdb.d/

# Process each SQL template file
for template in /docker-entrypoint-initdb.d/*.sql.template; do
    # Check if the template file exists and is writable
    if [ -f "$template" ] && [ -w "$template" ]; then
        # Derive the actual SQL file name from the template name
        sql_file="${template%.template}"

        # Create SQL file from template
        envsubst < "$template" > "$sql_file"

        # Execute the SQL script
        if [ -f "$sql_file" ] && [ -w "$sql_file" ]; then
            psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$sql_file"
        else
            echo "SQL file $sql_file missing or not writable"
            exit 1
        fi
    else
        echo "Template file $template missing or not writable"
        exit 1
    fi
done