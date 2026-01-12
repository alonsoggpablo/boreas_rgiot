"""
Airflow Configuration
Links Airflow with Django for alert management
"""

import os
from airflow.models import Variable

# Get Django database settings from environment
DJANGO_DB_URL = os.getenv(
    'DJANGO_DATABASE_URL',
    'postgresql://boreas_user:boreas_password@db:5432/boreas_db'
)

# Airflow configuration
AIRFLOW_HOME = os.getenv('AIRFLOW_HOME', '/opt/airflow')

# Email configuration (matches Django settings)
SMTP_MAIL_FROM = os.getenv('EMAIL_HOST_USER', 'tecnico@rggestionyenergia.com')
SMTP_HOST = os.getenv('EMAIL_HOST', 'mail.rggestionyenergia.com')
SMTP_PORT = int(os.getenv('EMAIL_PORT', 587))
SMTP_USER = os.getenv('EMAIL_HOST_USER', 'tecnico@rggestionyenergia.com')
SMTP_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# Alert rule variables (can be overridden via Airflow UI)
default_alert_variables = {
    'disk_space_threshold': 89,
    'device_check_timeout': 12,  # hours
    'alert_cleanup_days': 30,
    'email_recipients': 'tecnico@rggestionyenergia.com',
}

# Set default variables if not already set
for key, value in default_alert_variables.items():
    try:
        Variable.get(key)
    except:
        Variable.set(key, value)

print("✓ Airflow configuration loaded")
print(f"  SMTP Server: {SMTP_HOST}:{SMTP_PORT}")
print(f"  Django Database: {DJANGO_DB_URL[:50]}...")
