"""
Airflow DAG: Daily System Report
Sends a summary email every day at 9am with last reading time for each MQTT family, all active alerts, and disk/RAM usage.
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import django
import psutil


# Setup Django environment for Airflow
import sys
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
import django
django.setup()

from boreas_mediacion.models import MQTT_device_family, mqtt_msg, Alert
from django.utils import timezone
from django.conf import settings
from boreas_mediacion.alert_service import AlertService

EMAIL_TO = 'alonsogpablo@rggestionyenergia.com'


def gather_report():
    # Last reading time for each family
    family_lines = []
    for family in MQTT_device_family.objects.all():
        last_msg = mqtt_msg.objects.filter(device_family=family).order_by('-report_time').first()
        last_time = last_msg.report_time.strftime('%Y-%m-%d %H:%M:%S') if last_msg else 'Never'
        family_lines.append(f"{family.name}: {last_time}")
    family_report = '\n'.join(family_lines)

    # All active alerts
    alerts = Alert.objects.filter(status='active')
    alert_lines = [f"[{a.severity.upper()}] {a.message}" for a in alerts]
    alerts_report = '\n'.join(alert_lines) if alert_lines else 'No active alerts.'

    # Disk and RAM usage
    disk = psutil.disk_usage('/')
    ram = psutil.virtual_memory()
    disk_report = f"Disk usage: {disk.percent:.1f}%"
    ram_report = f"RAM usage: {ram.percent:.1f}%"

    # Compose email
    subject = "[boreas] Daily System Report"
    body = f"""
Daily System Report
===================

Last reading time for each MQTT family:
{family_report}

Active alerts:
{alerts_report}

System usage:
{disk_report}\n{ram_report}
"""
    # Send email
    service = AlertService()
    service.send_email_notification(EMAIL_TO, subject, body)


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 19),
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
}

dag = DAG(
    'daily_system_report',
    default_args=default_args,
    description='Send daily system report email',
    schedule_interval='0 9 * * *',
    catchup=False,
)

report_task = PythonOperator(
    task_id='send_daily_report',
    python_callable=gather_report,
    dag=dag,
)
