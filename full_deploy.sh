#!/bin/bash
# Boreas full deployment script (now in project root)
set -e


# Ensure boreas_net network exists
echo "🌐 Ensuring Docker network 'boreas_net' exists..."
docker network create boreas_net || true

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


# Build containers (main, airflow, and prometheus-stack)
echo "🔨 Building containers..."
docker compose build
docker compose -f docker-compose.yml -f docker-compose.airflow.yml build
docker compose -f prometheus-stack/docker-compose.yml build



# Start database first (main and airflow)
echo "🗄️  Starting database..."
docker compose up -d db
docker compose -f docker-compose.yml -f docker-compose.airflow.yml up -d db

# Wait for db container to be healthy
echo "⏳ Waiting for db container to be healthy..."
for i in {1..30}; do
    status=$(docker inspect --format='{{.State.Health.Status}}' boreas_db 2>/dev/null || echo "starting")
    if [ "$status" = "healthy" ]; then
        echo "DB container is healthy."
        break
    fi
    echo "Waiting for db... ($i)"
    sleep 2
done

# Start Prometheus and Grafana stack
echo "📊 Starting Prometheus and Grafana stack..."
docker compose -f prometheus-stack/docker-compose.yml up -d




# Start web service before migrations to ensure network connectivity
echo "🟢 Starting web service (for migrations)..."
docker compose up -d web

# Wait for web container to be healthy and networked
echo "⏳ Waiting for web container to be healthy and networked..."
for i in {1..30}; do
    status=$(docker inspect --format='{{.State.Health.Status}}' boreas_app 2>/dev/null || echo "starting")
    if [ "$status" = "healthy" ] || [ "$status" = "running" ]; then
        echo "Web container is $status."
        break
    fi
    echo "Waiting for web... ($i)"
    sleep 2
done

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


# Retry makemigrations and migrate until successful (max 15 attempts)
for i in {1..15}; do
    echo "Attempt $i: Running makemigrations..."
    if docker compose exec web python /app/boreas_mediacion/manage.py makemigrations; then
        echo "makemigrations succeeded."
        break
    fi
    echo "makemigrations failed, retrying in 4s..."
    sleep 4
done

for i in {1..15}; do
    echo "Attempt $i: Running migrate..."
    if docker compose exec web python /app/boreas_mediacion/manage.py migrate; then
        echo "migrate succeeded."
        break
    fi
    echo "migrate failed, retrying in 4s..."
    sleep 4
done

echo "📦 Collecting static files..."
docker compose exec web python /app/boreas_mediacion/manage.py collectstatic --noinput --clear


# Load main fixtures in a single command
echo "📦 Loading main fixtures..."
for i in {1..15}; do
    docker compose exec web python boreas_mediacion/manage.py loaddata \
        boreas_mediacion/fixtures/01_mqtt_device_families.json \
        boreas_mediacion/fixtures/02_mqtt_brokers.json \
        boreas_mediacion/fixtures/03_mqtt_topics.json \
        boreas_mediacion/fixtures/04_sensor_actuaciones.json \
        boreas_mediacion/fixtures/05_router_parameters.json \
        boreas_mediacion/fixtures/06_datadis_credentials.json \
        boreas_mediacion/fixtures/07_aemet.json && {
        echo "loaddata succeeded.";
        break;
    } || {
        echo "loaddata failed, retrying in 4s...";
        sleep 4;
    }
done



# Create superuser (automated)
echo "👤 Creating superuser (if not exists)..."
docker compose exec web python /app/boreas_mediacion/manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); username='pablo'; password='boreas2026'; email='pablo@localhost';
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
else:
    print('Superuser already exists.')"



# After migrations, start go_mqtt, go_anomaly_detector, and Airflow services
echo "🟢 Starting go_mqtt service..."
docker compose up -d go_mqtt --remove-orphans

echo "🔍 Starting go_anomaly_detector service..."
docker compose up -d go_anomaly_detector --remove-orphans

echo "🟢 Starting Airflow services..."
docker compose -f docker-compose.yml -f docker-compose.airflow.yml up -d airflow-webserver airflow-scheduler --remove-orphans
docker compose -f prometheus-stack/docker-compose.yml up -d

# Wait for Airflow webserver to be healthy
echo "⏳ Waiting for Airflow webserver to be healthy..."
for i in {1..30}; do
    status=$(docker inspect --format='{{.State.Health.Status}}' boreas_airflow_web 2>/dev/null || echo "starting")
    if [ "$status" = "healthy" ] || [ "$status" = "running" ]; then
        echo "Airflow webserver is $status."
        break
    fi
    echo "Waiting for Airflow webserver... ($i)"
    sleep 2
done

# Wait for Airflow scheduler to be healthy
echo "⏳ Waiting for Airflow scheduler to be healthy..."
for i in {1..30}; do
    status=$(docker inspect --format='{{.State.Health.Status}}' boreas_airflow_scheduler 2>/dev/null || echo "starting")
    if [ "$status" = "healthy" ] || [ "$status" = "running" ]; then
        echo "Airflow scheduler is $status."
        break
    fi
    echo "Waiting for Airflow scheduler... ($i)"
    sleep 2
done

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


echo "♻️  Reloading Airflow services..."
sh reload_airflow.sh

echo "✅ Deployment complete!"
echo "Dashboard: http://localhost/"
echo "Airflow:   http://localhost:8080/"
echo "API:       http://localhost/api/"
echo "Admin:     http://localhost/admin/"
