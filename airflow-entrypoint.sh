#!/bin/bash
set -e

# Wait a bit for the database
sleep 5

# Initialize Airflow database if not already done
if ! airflow db check 2>/dev/null; then
  echo "Initializing Airflow database..."
  airflow db init
fi

# Create admin user if it doesn't exist
if ! airflow users list 2>/dev/null | grep -q airflow; then
  echo "Creating Airflow admin user..."
  airflow users create \
    --username airflow \
    --password airflow \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com
fi

echo "Starting Airflow..."
# Execute the main command
exec "$@"
