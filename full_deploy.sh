#!/bin/bash
# Boreas full deployment script
set -e

# Pull latest code

echo "📥 Pulling latest code..."
git pull origin main

# Stop all containers

echo "🛑 Stopping containers..."
docker compose down

# Build containers

echo "🔨 Building containers..."
docker compose build

# Start database first

echo "🗄️  Starting database..."
docker compose up -d db
sleep 10

# Start web service (needed for management commands)
echo "🟢 Starting web service..."
docker compose up -d web
sleep 5

# Run migrations

echo "📦 Running migrations..."
docker compose exec web python manage.py migrate

# Collect static files

echo "📦 Collecting static files..."
docker compose exec web python manage.py collectstatic --noinput --clear

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
docker compose up -d

# Remove old instructions file if unnecessary
if [ -f INSTRUCCIONES_DESPLIEGUE.TXT ]; then
    echo "🧹 Removing INSTRUCCIONES_DESPLIEGUE.TXT..."
    rm INSTRUCCIONES_DESPLIEGUE.TXT
fi

# Verify everything

echo "🔎 Verifying containers..."
docker compose ps

echo "🔎 Verifying dashboard access..."
curl -I http://localhost/

echo "🔎 Verifying Airflow access..."
curl -I http://localhost:8080/

echo "✅ Deployment complete!"
echo "Dashboard: http://localhost/"
echo "Airflow:   http://localhost:8080/"
echo "API:       http://localhost/api/"
echo "Admin:     http://localhost/admin/"
