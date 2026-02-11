#!/bin/bash
# Script to update Boreas deployment on remote host

set -e  # Exit on error

echo "========================================="
echo "Updating Boreas deployment..."
echo "========================================="

# Pull latest changes
echo "📥 Pulling latest changes from git..."
git pull origin main

# Stop containers
echo "🛑 Stopping containers..."
docker compose -f docker-compose.yml -f docker-compose.airflow.yml down

# Rebuild web container
echo "🔨 Rebuilding web container..."
docker compose build web

# Start database first
echo "🗄️  Starting database..."
docker compose up -d db

# Wait for database to be healthy
echo "⏳ Waiting for database to be ready..."
sleep 10

# Collect static files
echo "📦 Collecting static files..."
# First remove old staticfiles to ensure fresh collection
docker compose exec -T web rm -rf /app/staticfiles/*
# Now collect all static files including DRF
docker compose exec -T web python manage.py collectstatic --noinput --clear --verbosity=2

# Verify static files were collected
echo "✓ Verifying static files..."
docker compose exec -T web ls -la /app/staticfiles/ | head -20

echo "📦 Running migrations..."
docker compose exec web python manage.py migrate
# Make migrations and run migrations
echo "📦 Making migrations..."
docker compose exec web python manage.py makemigrations --noinput
echo "📦 Running migrations..."
docker compose exec web python manage.py migrate

# Load fixtures

echo "📦 Loading fixtures..."
for fixture in boreas_mediacion/fixtures/*.json; do
    echo "   → $fixture"
    docker compose exec web python manage.py loaddata $fixture
    sleep 1
done

# Create superuser (interactive)
echo "👤 Creating superuser (if not exists)..."
docker compose exec web python manage.py createsuperuser || true

# Start all services
echo "🚀 Starting all services..."
docker compose -f docker-compose.yml -f docker-compose.airflow.yml up -d

# Restart nginx to pick up config changes
echo "🔄 Restarting nginx..."
docker compose restart nginx

# Show container status
echo ""
echo "========================================="
echo "✅ Deployment completed!"
echo "========================================="
docker compose -f docker-compose.yml -f docker-compose.airflow.yml ps

echo ""
echo "Services:"
echo "  Dashboard: http://82.165.142.98/"
echo "  Airflow:   http://82.165.142.98:8080/"
echo "  API:       http://82.165.142.98/api/"
echo "  Admin:     http://82.165.142.98/admin/"
echo ""
