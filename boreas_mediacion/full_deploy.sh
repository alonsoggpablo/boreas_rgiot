PROJECT_ROOT_MARKER="manage.py"
if [ ! -f "$PROJECT_ROOT_MARKER" ]; then
    echo "❌ ERROR: Please run this script from the project root directory (where manage.py is located)."
    exit 1
fi
#!/bin/bash
# Boreas full deployment script
set -e

# Pull latest code

echo "📥 Pulling latest code..."
git pull origin main

# Stop all containers

echo "🛑 Stopping containers..."
docker compose down
docker compose -f docker-compose.airflow.yml down

# Build containers

echo "🔨 Building containers..."
docker compose build
docker compose -f docker-compose.airflow.yml build

# Start database first

echo "🗄️  Starting database..."
docker compose up -d db
docker compose -f docker-compose.airflow.yml up -d postgres
sleep 10


# Start web service (needed for management commands)
echo "🟢 Starting web service..."
docker compose up -d web
docker compose -f docker-compose.airflow.yml up -d airflow-webserver airflow-scheduler

# Wait for web container to be healthy
echo "⏳ Waiting for web container to be healthy..."
for i in {1..30}; do
    status=$(docker inspect --format='{{.State.Health.Status}}' boreas_app 2>/dev/null || echo "starting")
    if [ "$status" = "healthy" ] || [ "$status" = "running" ]; then
        echo "Web container is $status."
        break
    fi
    echo "Waiting... ($i)"
    sleep 2
done

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
docker compose -f docker-compose.airflow.yml up -d

# Remove old instructions file if unnecessary
if [ -f INSTRUCCIONES_DESPLIEGUE.TXT ]; then
    echo "🧹 Removing INSTRUCCIONES_DESPLIEGUE.TXT..."
    rm INSTRUCCIONES_DESPLIEGUE.TXT
fi

# Verify everything

echo "🔎 Verifying containers..."
docker compose ps
docker compose -f docker-compose.airflow.yml ps

echo "🔎 Verifying dashboard access..."
curl -I http://localhost/

echo "🔎 Verifying Airflow access..."
curl -I http://localhost:8080/

echo "✅ Deployment complete!"
echo "Dashboard: http://localhost/"
echo "Airflow:   http://localhost:8080/"
echo "API:       http://localhost/api/"
echo "Admin:     http://localhost/admin/"
