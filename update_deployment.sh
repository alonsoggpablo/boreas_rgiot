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
docker-compose -f docker-compose.yml -f docker-compose.airflow.yml down

# Rebuild web container
echo "🔨 Rebuilding web container..."
docker-compose build web

# Start database first
echo "🗄️  Starting database..."
docker-compose up -d db

# Wait for database to be healthy
echo "⏳ Waiting for database to be ready..."
sleep 10

# Collect static files
echo "📦 Collecting static files..."
docker-compose run --rm web python manage.py collectstatic --noinput --clear

# Start all services
echo "🚀 Starting all services..."
docker-compose -f docker-compose.yml -f docker-compose.airflow.yml up -d

# Show container status
echo ""
echo "========================================="
echo "✅ Deployment completed!"
echo "========================================="
docker-compose -f docker-compose.yml -f docker-compose.airflow.yml ps

echo ""
echo "Services:"
echo "  Dashboard: http://82.165.142.98/"
echo "  Airflow:   http://82.165.142.98:8080/"
echo "  API:       http://82.165.142.98/api/"
echo "  Admin:     http://82.165.142.98/admin/"
echo ""
