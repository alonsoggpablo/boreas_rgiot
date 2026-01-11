# Alert Monitoring System with Apache Airflow

## 🎯 Overview

Complete alert monitoring system migrated from Node-RED to Django + Apache Airflow:

- **Django**: Alert models, business logic, email notifications
- **Apache Airflow**: Scheduling, orchestration, monitoring dashboard
- **Scheduled Tasks**: 
  - Disk space check: Daily at 10:00
  - Device connection check: Daily at 09:00
  - Alert cleanup: Daily at 02:00

---

## 📦 Components Created

### 1. Django Models (`models.py`)

```python
- AlertRule          # Define alert rules with thresholds
- Alert              # Alert instances when rules trigger
- AlertNotification  # Notification records (email, MQTT, etc.)
```

**Features:**
- Multiple rule types: disk_space, device_connection, custom
- Multiple notification channels: email, MQTT
- Full audit trail with timestamps
- Severity levels: info, warning, error, critical
- Status tracking: active, acknowledged, resolved

---

### 2. Alert Service Layer (`alert_service.py`)

```python
AlertService                      # Base service for alerts
├── DiskSpaceAlertService        # Monitor disk usage (10:00 daily)
└── DeviceConnectionAlertService # Monitor device connectivity (09:00 daily)
```

**Features:**
- Disk space threshold monitoring (default: 89%)
- Email notifications via SMTP (mail.rggestionyenergia.com:587)
- Device last-seen tracking for connection health
- Automatic alert deduplication (won't re-trigger same alert)
- Configurable check intervals

---

### 3. Admin Interface (`admin.py`)

**AlertRule Admin:**
- View/manage all alert rules
- Activate/deactivate rules
- Manual trigger: "Check now" action
- Display rule status, threshold, recipients

**Alert Admin:**
- View all triggered alerts with severity badges
- Filter by severity, status, type, date
- Mark as acknowledged/resolved
- Bulk actions

**AlertNotification Admin:**
- Track all notification attempts
- See delivery status (sent, failed, pending)
- View error messages if failed

---

### 4. Django Management Command

**Usage:**
```bash
# Check all rule types
python manage.py check_alerts all

# Check specific rule type
python manage.py check_alerts disk_space
python manage.py check_alerts device_connection

# Manual cleanup (from Airflow task)
python manage.py check_alerts cleanup
```

**Output:**
- Formatted status messages
- Alert details if triggered
- Notification status
- Summary report

---

### 5. Apache Airflow Setup

**Files Created:**
```
docker-compose.airflow.yml       # Airflow containers + PostgreSQL
Dockerfile.airflow               # Airflow image with Django support
airflow-requirements.txt          # Python dependencies
airflow/dags/boreas_alerts.py    # Main alert DAG
airflow/config.py                # Airflow configuration
```

**DAG: `boreas_alerts`**

Scheduled at: 02:00, 09:00, 10:00 daily

Tasks:
```
cleanup_old_alerts (02:00)
    ↓
check_device_connections (09:00)
    ↓
check_disk_space (10:00)
```

---

## 🚀 Getting Started

### Step 1: Start Django Containers (if not running)

```bash
cd C:\Users\Usuario\Documents\GitHub\boreas_rgiot
docker-compose up -d
```

### Step 2: Start Airflow

```bash
docker-compose -f docker-compose.airflow.yml up -d
```

This starts:
- `airflow-db` (PostgreSQL for Airflow metadata)
- `airflow-webserver` (UI on http://localhost:8080)
- `airflow-scheduler` (Executes DAGs on schedule)

### Step 3: Create Alert Rules in Django Admin

1. Go to http://localhost/admin/boreas_mediacion/alertrule/
2. Create "Disk Space Monitor" rule:
   - Type: Disk Space
   - Threshold: 89%
   - Recipients: tecnico@rggestionyenergia.com
   - Active: ✓

3. Create "Device Connection Monitor" rule (optional):
   - Type: Device Connection
   - Clients: Metro de Madrid, Ayuntamiento de Madrid
   - Max hours inactive: 12
   - Active: ✓

### Step 4: Monitor in Airflow Dashboard

- Go to http://localhost:8080
- Login with: `airflow` / `airflow`
- View DAG: `boreas_alerts`
- See scheduled tasks and execution history

---

## 📊 Monitoring Alerts

### Django Admin
- http://localhost/admin/boreas_mediacion/alertrule/ - Manage rules
- http://localhost/admin/boreas_mediacion/alert/ - View triggered alerts
- http://localhost/admin/boreas_mediacion/alertnotification/ - Check notifications

### Airflow Dashboard
- http://localhost:8080/dags/boreas_alerts
- See task execution status
- View logs for each task
- Track alert system health

---

## 🔧 Configuration

### Email Settings (Django)

In `settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.rggestionyenergia.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tecnico@rggestionyenergia.com'
EMAIL_HOST_PASSWORD = 'your-password'
```

### Alert Rule Configuration

In Django Admin, for each AlertRule:
```json
{
  "filesystem": "ext4",           # For disk_space rules
  "critical_threshold": 95,       # Alert if >95%
  "clients": ["client_name"],     # For device_connection rules
  "max_hours_inactive": 12        # For device_connection rules
}
```

### Airflow Schedule

Edit `airflow/dags/boreas_alerts.py`:
```python
schedule_interval='0 2,9,10 * * *'  # Cron format: minute hour * * day_of_week
```

---

## 📝 Alert Types

### 1. Disk Space Alert

**Trigger:** Disk usage ≥ threshold (default: 89%)

**Severity:**
- 89-94% → warning
- ≥95% → critical

**Action:**
- Email to configured recipients
- Message includes: current usage %, threshold %

**Example:**
```
El espacio de disco ocupado supera el 89%
Usado: 92%
```

---

### 2. Device Connection Alert

**Trigger:** Device last update > configured hours (default: 12h)

**Severity:** error

**Action:**
- Email to configured recipients
- Message includes: device list, last seen time

**Example:**
```
¡¡ALARMA!! No hay recepción de datos

Se ha detectado que los siguientes dispositivos no envían datos 
desde hace más de 12 horas:

- nanoenvi-12345 (Cliente: Metro de Madrid, última vez: 2026-01-07T22:30)
- nanoenvi-67890 (Cliente: Ayuntamiento de Madrid, última vez: 2026-01-06T16:45)
```

---

## 🛠️ Troubleshooting

### Airflow containers won't start

1. Check if required networks exist:
```bash
docker network ls
```

2. Ensure Django database is running:
```bash
docker-compose ps
```

3. View logs:
```bash
docker-compose -f docker-compose.airflow.yml logs airflow-webserver
```

### No alerts triggering

1. Check alert rules are active in Django Admin
2. Verify last_check timestamp hasn't been recently updated
3. Check Airflow task logs for errors
4. Test manually: `python manage.py check_alerts disk_space`

### Emails not sending

1. Verify SMTP settings in Django settings.py
2. Check email server connectivity: `telnet mail.rggestionyenergia.com 587`
3. Verify credentials are correct
4. Check AlertNotification status in Django Admin
5. View error_message field for SMTP errors

---

## 📈 Next Steps

### Option 1: Add Slack Notifications
```python
# In AlertService, add slack_notify method
# In AlertRule, add notification_type='slack'
```

### Option 2: Add Webhook Notifications
```python
# Send alerts to external systems
# Update AlertNotification to track webhook deliveries
```

### Option 3: Add Custom Rules
```python
# Create custom alert rule types in AlertRule
# Implement check methods in alert_service.py
```

### Option 4: Add Metrics Dashboard
```python
# Use Grafana to visualize alert history
# Track alert frequency, resolution time, etc.
```

---

## 📚 API Reference

### Check All Alerts (Django)
```bash
python manage.py check_alerts all
```

### Check Specific Type
```bash
python manage.py check_alerts disk_space
python manage.py check_alerts device_connection
```

### Cleanup Alerts
```bash
python manage.py check_alerts cleanup
```

---

## 🔐 Security Notes

- Email credentials stored in Django settings or environment variables
- Alert history retained for 30 days (configurable)
- SMTP uses TLS encryption
- All alerts logged with timestamps for audit trail
- Admin interface requires Django authentication

---

## 📞 Support

**Alert Rules Admin:**
- Path: `/admin/boreas_mediacion/alertrule/`
- Manage all monitoring rules

**View Alerts:**
- Path: `/admin/boreas_mediacion/alert/`
- Monitor triggered alerts

**Check Notifications:**
- Path: `/admin/boreas_mediacion/alertnotification/`
- Verify email delivery

**Airflow Dashboard:**
- URL: `http://localhost:8080/`
- Monitor DAG execution
- View task logs

