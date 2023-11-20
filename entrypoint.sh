#!/bin/bash

# Wait for the database to be ready
/usr/local/bin/wait-for-it.sh db:5432 --timeout=30

# Execute the Python script with URL from environment variable
# python /app/src/data/load_new_data.py "$SCRAPER_URL"