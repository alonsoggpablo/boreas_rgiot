# Boreas IoT Deployment Guide

Complete guide for deploying Boreas IoT system with Django, PostgreSQL, MQTT, and Airflow.

## Table of Contents

1. [Local Development](#local-development)
2. [Remote Production Deployment](#remote-production-deployment)
3. [Services Overview](#services-overview)
4. [Troubleshooting](#troubleshooting)
5. [Useful Commands](#useful-commands)

---

## Local Development

### Prerequisites

- Docker Desktop
- Docker Compose v2.x
- Git

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/alonsoggpablo/boreas_rgiot.git
   cd boreas_rgiot
   ```

2. **Build and start all services**
   ```bash
   docker-compose build
   docker-compose -f docker-compose.yml -f docker-compose.airflow.yml up -d
   ```

3. **Verify services are running**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.airflow.yml ps
   ```

4. **Collect static files**
   ```bash
   docker-compose exec web python manage.py collectstatic --noinput
   ```

5. **Create superuser**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. **Access the dashboard**
   - Dashboard: http://localhost/dashboard/family-messages/
   - Admin: http://localhost/admin/
   - API: http://localhost/api/
   - Airflow: http://localhost:8080/

7. **Load initial fixtures (optional, recommended for first setup)**
   ```bash
   # Load all fixtures in order
   docker compose exec web python manage.py loaddata boreas_mediacion/fixtures/01_mqtt_device_families.json
   docker compose exec web python manage.py loaddata boreas_mediacion/fixtures/02_mqtt_brokers.json
   docker compose exec web python manage.py loaddata boreas_mediacion/fixtures/03_mqtt_topics.json
   docker compose exec web python manage.py loaddata boreas_mediacion/fixtures/04_sensor_actuaciones.json
   docker compose exec web python manage.py loaddata boreas_mediacion/fixtures/05_router_parameters.json
   ```

   This will populate the database with initial MQTT families, brokers, topics, sensor actions, and router parameters.

---

## Remote Production Deployment

### Prerequisites

- Remote server with Docker installed
- Docker Compose V2
- SSH access to remote server
- Git access

### Step 1: SSH into Remote Server

```bash
ssh user@82.165.142.98
cd /path/to/boreas_rgiot
```

### Step 2: Run Automated Deployment Script

The repository includes an automated deployment script that handles everything:

```bash
git pull origin main
chmod +x update_deployment.sh
./update_deployment.sh
```

**What the script does:**
- ✅ Pulls latest code from GitHub
- ✅ Stops all containers cleanly
- ✅ Rebuilds the web container
- ✅ Starts the database
- ✅ **Collects static files** (crucial for favicon and DRF UI)
- ✅ Starts all services (web, MQTT, Airflow, nginx)
- ✅ Restarts nginx to apply configuration changes
- ✅ Displays deployment status and service URLs

### Step 3: Verify Deployment

```bash
docker compose -f docker-compose.yml -f docker-compose.airflow.yml ps
```

All services should show "Up" status.

### Step 4: Test Services

- **Dashboard**: http://82.165.142.98/
- **Airflow**: http://82.165.142.98:8080/
- **API**: http://82.165.142.98/api/
- **Admin**: http://82.165.142.98/admin/

---

## Services Overview

### Web Application (Django)
- **Container**: boreas_app
- **Port**: 8000 (internal), exposed via nginx on port 80
- **Features**:
  - REST API with Django REST Framework
  - Dashboard for monitoring IoT data
  - Admin interface
  - Alert management system

### Database (PostgreSQL)
- **Container**: boreas_db
- **Port**: 5432
- **Volume**: `postgres_data`
- **Initialization**: Automatic on first run
- **Data**: 12 MQTT families, Sigfox, DATADIS, WirelessLogic devices

### MQTT Service
- **Container**: boreas_mqtt
- **Functionality**: 
  - Receives messages from MQTT broker
  - Stores data in database
  - Triggers alert checks
- **Connection**: Configured in environment variables

### Nginx (Reverse Proxy)
- **Container**: boreas_nginx
- **Port**: 80
- **Features**:
  - Proxies requests to Django
  - Serves static files (CSS, JS, favicon)
  - Serves media files (uploads)
  - Forwards headers for hostname detection
  - MIME type handling for favicon (webp, ico)

### Airflow (Scheduler)
- **Containers**: boreas_airflow_web, boreas_airflow_scheduler
- **Port**: 8080
- **DAGs**:
  - `aemet_monitor` - AEMET data monitoring
  - `boreas_alerts` - Alert checking
  - `boreas_family_alerts` - Family timeout alerts (runs every 10 minutes)
- **Database**: Shares PostgreSQL with Django

---

## Key Features

### Dashboard (`/dashboard/family-messages/`)
Displays data from 5 sources:
1. **MQTT Families** - 12 device families (aemet, shellies, gadget, router, etc.)
2. **Sigfox** - CO2, temperature, humidity readings
3. **DATADIS** - Energy consumption data
4. **DATADIS Power** - Max power readings
5. **WirelessLogic** - SIM card usage and status

Auto-refreshes every 5 seconds. Alphabetically sorted by family/source name.

### Alert System
- **16 Active Alert Rules**:
  - 12 MQTT family timeout rules (1-hour threshold)
  - 4 API source timeout rules (1-hour threshold)
- **Automatic Checking**: Every 10 minutes via Airflow DAG
- **Notifications**: Email alerts when timeout detected
- **Configuration**: [ALERT_SYSTEM.md](ALERT_SYSTEM.md)

### Static Files & Favicon
- **Location**: `boreas_mediacion/boreas_mediacion/static/`
- **Collected to**: `staticfiles/` (Docker volume)
- **Served by**: Nginx at `/static/`
- **Favicon**: `favicon.webp` with MIME type `image/webp`
- **Auto-refresh on Deploy**: Deployment script runs `collectstatic`

### Hostname Detection
- **Dashboard URL**: Automatically detects actual hostname
- **Airflow Link**: Uses `X-Forwarded-Host` header from nginx
- **Fallback**: Uses `HTTP_HOST` if header not available
- **Construction**: `{hostname}:8080` for Airflow link

---

## Troubleshooting

### Static Files Not Working (Favicon, DRF UI)

**Symptoms**: 404 errors for `/static/` files, favicon not visible

**Solutions**:
1. Run deployment script: `./update_deployment.sh`
2. Or manually collect statics:
   ```bash
   docker compose exec web python manage.py collectstatic --noinput --clear
   docker compose restart nginx
   ```

### Airflow Link Goes to Wrong Host

**Symptoms**: Link shows `0.0.0.0:8080` instead of actual IP

**Solutions**:
1. Ensure nginx is forwarding `X-Forwarded-Host` header
2. Check `nginx.conf` contains `proxy_set_header X-Forwarded-Host $host;`
3. Run deployment script to update config

### DRF API Not Working

**Symptoms**: `/api/` returns 404 or missing styling

**Solutions**:
1. Static files not collected - see "Static Files Not Working" above
2. Restart containers: `docker compose restart`
3. Check logs: `docker compose logs web`

### MQTT Messages Not Received

**Symptoms**: Dashboard shows no MQTT data

**Solutions**:
1. Check MQTT service is running:
   ```bash
   docker compose ps | grep mqtt
   ```
2. Check MQTT credentials in environment:
   ```bash
   docker compose exec web env | grep MQTT
   ```
3. Verify MQTT broker connectivity:
   ```bash
   docker compose logs mqtt
   ```

### Airflow Not Running

**Symptoms**: Port 8080 not accessible

**Solutions**:
1. Start Airflow services:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.airflow.yml up -d
   ```
2. Check status:
   ```bash
   docker compose ps | grep airflow
   ```
3. View logs:
   ```bash
   docker compose logs boreas_airflow_web
   ```

---

## Useful Commands

### Docker Compose (V2 Syntax)

```bash
# Start all services
docker compose -f docker-compose.yml -f docker-compose.airflow.yml up -d

# Stop all services
docker compose -f docker-compose.yml -f docker-compose.airflow.yml down

# View service status
docker compose ps
docker compose -f docker-compose.yml -f docker-compose.airflow.yml ps

# View logs
docker compose logs -f web          # Django logs
docker compose logs -f nginx        # Nginx logs
docker compose logs -f mqtt         # MQTT logs
docker compose logs boreas_airflow_web  # Airflow web logs

# Execute command in container
docker compose exec web python manage.py <command>

# Access shell
docker compose exec web bash
docker compose exec db bash

# Connect to PostgreSQL
docker compose exec db psql -U boreas_user -d boreas_db
```

### Django Management Commands

```bash
# Collect static files
docker compose exec web python manage.py collectstatic --noinput --clear

# Run migrations
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser

# Check family alerts
docker compose exec web python manage.py check_family_alerts

# Setup family alert rules
docker compose exec web python manage.py setup_family_alerts

# Setup API alert rules
docker compose exec web python manage.py setup_api_alerts
```

### Database Commands

```bash
# PostgreSQL shell
docker compose exec db psql -U boreas_user -d boreas_db

# Backup database
docker compose exec db pg_dump -U boreas_user -d boreas_db > backup.sql

# Restore from backup
docker compose exec -T db psql -U boreas_user -d boreas_db < backup.sql
```

### Cleaning Up

```bash
# Remove stopped containers
docker compose down

# Remove all containers and volumes (⚠️ WARNING: Deletes data!)
docker compose down -v

# Clean up unused Docker resources
docker system prune -a
```

---

## Environment Variables

Key environment variables in `docker-compose.yml`:

```bash
# Django Configuration
DEBUG=True/False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,82.165.142.98,*

# Database
DATABASE_URL=postgresql://boreas_user:boreas_password@db:5432/boreas_db

# Email (for alerts)
EMAIL_HOST=mail.rggestionyenergia.com
EMAIL_PORT=587
EMAIL_HOST_USER=alonsogpablo@rggestionyenergia.com
EMAIL_USE_TLS=True

# MQTT
MQTT_SERVER=mqtt.rg-iotsolutions.com
MQTT_PORT=1883
MQTT_USER=pablo
MQTT_PASSWORD=pabloDev1234
```

---

## File Structure

```
boreas_rgiot/
├── docker-compose.yml           # Main compose file
├── docker-compose.airflow.yml   # Airflow services
├── Dockerfile                   # Web app container
├── Dockerfile.airflow          # Airflow container
├── nginx.conf                  # Nginx configuration
├── update_deployment.sh        # Automated deployment script
├── requirements.txt            # Python dependencies
├── DEPLOYMENT_GUIDE.md        # This file
├── ALERT_SYSTEM.md           # Alert configuration
├── airflow/
│   └── dags/
│       ├── aemet_monitor.py
│       ├── boreas_alerts.py
│       └── boreas_family_alerts.py
└── boreas_mediacion/
    ├── boreas_mediacion/
    │   ├── settings.py
    │   ├── urls.py
    │   └── views.py
    ├── templates/
    │   └── family_messages.html
    ├── static/
    │   └── favicon.webp
    └── manage.py
```

---

## Version Information

- **Django**: 4.2
- **PostgreSQL**: 15 (Alpine)
- **Docker Compose**: V2.x
- **Airflow**: Latest
- **Nginx**: Alpine

---

## Support & Documentation

- [ALERT_SYSTEM.md](ALERT_SYSTEM.md) - Alert configuration details
- [README.md](README.md) - Project overview
- [DOCUMENTACION.md](DOCUMENTACION.md) - Spanish documentation

---

## Last Updated

January 15, 2026

**Recent Changes:**
- ✅ Fixed favicon handling with proper MIME types
- ✅ Fixed Airflow link hostname detection
- ✅ Added automatic static file collection to deployment script
- ✅ Added nginx configuration for X-Forwarded-Host header
