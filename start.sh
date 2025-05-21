#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
#pip install -r requirements.txt

# Initialize the database
if [ ! -d "migrations" ]; then
    echo "Initializing database migrations..."
    flask db init
fi

# Create and apply migrations
echo "Creating database migrations..."
flask db migrate -m "Initial migration"
echo "Applying database migrations..."
flask db upgrade

# Start the application
gunicorn app:app 
