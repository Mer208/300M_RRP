#!/usr/bin/env bash
# exit on error
set -o errexit

# Initialize the database
if [ ! -d "migrations" ]; then
    echo "Initializing database migrations..."
    flask db init
fi

# Create and apply migrations
echo "Creating database migrations..."
flask db migrate -m "Initial migration"

# Force upgrade the database to the latest version
echo "Applying database migrations..."
flask db upgrade --force

# Start the application
gunicorn app:app 
