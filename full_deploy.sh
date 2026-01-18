#!/bin/bash
# Boreas full deployment script (now in project root)
set -e

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Stop all containers (main and airflow)
echo "🛑 Stopping containers..."
docker compose down
docker compose -f docker-compose.yml -f docker-compose.airflow.yml down

# Remove Postgres data volume for a clean DB reset
echo "🗑️ Removing Postgres data volume..."
docker volume rm boreas_rgiot_postgres_data || true

# Remove all Django migration files for a clean migration history
echo "🗑️ Removing all Django migration files..."
find boreas_mediacion/boreas_mediacion/migrations -type f ! -name '__init__.py' -delete

# Build containers (main and airflow)
echo "🔨 Building containers..."
docker compose build
docker compose -f docker-compose.yml -f docker-compose.airflow.yml build

# Start database first (main and airflow)
echo "🗄️  Starting database..."
docker compose up -d db
docker compose -f docker-compose.yml -f docker-compose.airflow.yml up -d db
sleep 10

# Start web service (needed for management commands)
echo "🟢 Starting web service..."
docker compose up -d web --remove-orphans
docker compose -f docker-compose.yml -f docker-compose.airflow.yml up -d airflow-webserver airflow-scheduler --remove-orphans

# Start nginx proxy
echo "🟢 Starting nginx proxy..."
docker compose up -d nginx

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

echo "📦 Resetting and running migrations..."
echo "🔧 Fixing permissions for migrations directory (host, UID/GID 1000 for container)..."
sudo chown -R 1000:1000 boreas_mediacion/boreas_mediacion/migrations
sudo chmod -R 775 boreas_mediacion/boreas_mediacion/migrations

# Run makemigrations before migrate using correct path
docker compose exec web python /app/boreas_mediacion/manage.py makemigrations
docker compose exec web python /app/boreas_mediacion/manage.py migrate

echo "📦 Collecting static files..."
docker compose exec web python /app/boreas_mediacion/manage.py collectstatic --noinput --clear


# Load main fixtures in a single command
echo "📦 Loading main fixtures..."
docker compose exec web python boreas_mediacion/manage.py loaddata \
    boreas_mediacion/fixtures/01_mqtt_device_families.json \
    boreas_mediacion/fixtures/02_mqtt_brokers.json \
    boreas_mediacion/fixtures/03_mqtt_topics.json \
    boreas_mediacion/fixtures/04_sensor_actuaciones.json \
    boreas_mediacion/fixtures/05_router_parameters.json \
    boreas_mediacion/fixtures/06_datadis_credentials.json

# Create superuser (automated)
echo "👤 Creating superuser (if not exists)..."
docker compose exec web python /app/boreas_mediacion/manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); username='pablo'; password='boreas2026'; email='pablo@localhost';
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
else:
    print('Superuser already exists.')"

# Start all services (main and airflow)
echo "🚀 Starting all services..."
docker compose up -d
docker compose -f docker-compose.yml -f docker-compose.airflow.yml up -d

# Remove old instructions file if unnecessary
if [ -f INSTRUCCIONES_DESPLIEGUE.TXT ]; then
    echo "🧹 Removing INSTRUCCIONES_DESPLIEGUE.TXT..."
    rm INSTRUCCIONES_DESPLIEGUE.TXT
fi

# Verify everything (main and airflow)
echo "🔎 Verifying containers..."
docker compose ps
docker compose -f docker-compose.yml -f docker-compose.airflow.yml ps

echo "🔎 Verifying dashboard access..."
curl -I http://localhost/

echo "🔎 Verifying Airflow access..."
curl -I http://localhost:8080/

echo "✅ Deployment complete!"
echo "Dashboard: http://localhost/"
echo "Airflow:   http://localhost:8080/"
echo "API:       http://localhost/api/"
echo "Admin:     http://localhost/admin/"
